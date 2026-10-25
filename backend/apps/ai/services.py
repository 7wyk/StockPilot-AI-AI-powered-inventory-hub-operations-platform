"""
Groq AI service for StockPilot AI operations assistant.

Uses Groq server-side — API key never exposed to the browser.
The assistant answers from verified records via deterministic tools.
Write actions produce confirmation proposals; mutations only happen after
the user explicitly confirms them.
"""

from decimal import Decimal
import json
import logging
import os
import re

from django.conf import settings
from django.utils import timezone

from .models import Conversation, Message, UserPreference
from .tools import (
    READ_TOOLS,
    TOOL_DEFINITIONS,
    WRITE_TOOLS,
    execute_tool,
)

logger = logging.getLogger(__name__)

BASE_SYSTEM_PROMPT = """You are StockPilot AI, the intelligent operations assistant for StockPilot AI.
You help inventory managers, hub operators, and logistics teams monitor stock positions, identify operational risks, and execute verified workflows.

CRITICAL OPERATIONAL RULES:
1. Grounded Truth: You MUST use the provided tools to fetch real data. NEVER invent numbers, SKU counts, currency amounts, or inventory balances.
2. Tool Execution: When the user asks about inventory, stock levels, movements, low stock, hubs, or restock needs, call the appropriate tool.
3. Clarity: Present tool results clearly with exact numbers and concise bullet points. Distinguish between verified database measurements and operational advice.
4. Write Operations (CRITICAL): You NEVER mutate inventory directly. If a user asks to receive stock, issue stock, adjust stock, create a transfer, or create a restock request, call the corresponding write tool to generate a confirmation proposal. Tell the user to review and confirm the action in the confirmation card.
5. Organization Scope: You are strictly isolated to the user's active organization. You have no knowledge of or access to other organizations.
6. Reports: If asked for a report, call generate_report to provide verified metrics and direct the user to the Reports page for downloads.
"""


def get_groq_client():
    """Get configured Groq client, or None if credentials are not configured."""
    api_key = getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except Exception as exc:
        logger.warning(f"Could not initialize Groq client: {exc}")
        return None


def get_or_create_conversation(organization, user, conversation_id=None):
    """Get existing or create a new conversation strictly scoped to org + user."""
    if conversation_id:
        conv = Conversation.objects.filter(
            id=conversation_id,
            organization=organization,
            user=user,
            is_active=True,
        ).first()
        if conv:
            return conv

    return Conversation.objects.create(
        organization=organization,
        user=user,
        title="New conversation",
    )


def get_conversation_history(conversation, limit=16):
    """Get recent conversation history formatted for model completions."""
    messages = conversation.messages.order_by("-created_at")[:limit]
    result = []
    for msg in reversed(messages):
        entry = {"role": msg.role, "content": msg.content or ""}
        if msg.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": tc.get("id", f"call_{i}"),
                    "type": "function",
                    "function": {
                        "name": tc.get("name"),
                        "arguments": json.dumps(tc.get("arguments", {})),
                    },
                }
                for i, tc in enumerate(msg.tool_calls)
            ]
        result.append(entry)
    return result


def _build_system_prompt(organization, user):
    """Build system prompt incorporating organization context and explicit preferences."""
    preferences = UserPreference.objects.filter(organization=organization, user=user)
    pref_lines = []
    for p in preferences:
        pref_lines.append(f"- {p.key}: {json.dumps(p.value)}")

    prompt = BASE_SYSTEM_PROMPT
    if pref_lines:
        prompt += "\nUser Operational Preferences (scoped to this workspace):\n" + "\n".join(pref_lines)
    return prompt


def _rule_based_fallback(user_text: str, organization, user):
    """
    Deterministic rule-based fallback when Groq credentials are unavailable locally.
    Enables local development, offline demos, and test suites to function smoothly.
    """
    lower = user_text.lower().strip()
    tool_name = None
    args = {}

    if any(q in lower for q in ["inventory summary", "current inventory", "inventory value", "total units", "overview"]):
        tool_name = "get_inventory_summary"
    elif any(q in lower for q in ["low in stock", "low stock", "below threshold"]):
        tool_name = "get_low_stock_products"
    elif any(q in lower for q in ["out of stock", "stockout", "zero inventory"]):
        tool_name = "get_stockouts"
    elif any(q in lower for q in ["hub inventory", "hubs", "most inventory", "by hub"]):
        tool_name = "get_hub_inventory"
    elif any(q in lower for q in ["recent movement", "movement summary", "movements", "movement trends"]):
        tool_name = "get_movement_summary"
    elif any(q in lower for q in ["restock", "replenish", "recommendations"]):
        tool_name = "get_restock_recommendations"
    elif any(q in lower for q in ["health report", "inventory health", "stock health"]):
        tool_name = "get_stock_health"
    elif "report" in lower:
        tool_name = "generate_report"
        args = {"report_type": "inventory_health", "format": "csv"}

    # Pattern matching for write proposals
    receive_match = re.search(r"receive\s+(\d+(?:\.\d+)?)\s+(?:units?\s+of\s+)?([A-Za-z0-9_\-\s]+?)(?:\s+(?:at|into|in)\s+([A-Za-z0-9_\-\s]+))?$", lower)
    adjust_match = re.search(r"adjust\s+([A-Za-z0-9_\-\s]+?)\s+by\s+([+\-]?\d+(?:\.\d+)?)", lower)
    transfer_match = re.search(r"transfer\s+(\d+(?:\.\d+)?)\s+(?:units?\s+of\s+)?([A-Za-z0-9_\-\s]+?)\s+from\s+([A-Za-z0-9_\-\s]+?)\s+to\s+([A-Za-z0-9_\-\s]+)", lower)

    if receive_match:
        qty, prod, hub = receive_match.groups()
        tool_name = "receive_stock"
        args = {"product_name": prod.strip(), "quantity": qty, "hub_name": (hub or "").strip()}
    elif adjust_match:
        prod, qty = adjust_match.groups()
        tool_name = "adjust_stock"
        args = {"product_name": prod.strip(), "quantity": qty, "reason": "Inventory adjustment via assistant"}
    elif transfer_match:
        qty, prod, src, dst = transfer_match.groups()
        tool_name = "create_transfer"
        args = {"product_name": prod.strip(), "quantity": qty, "source_hub_name": src.strip(), "destination_hub_name": dst.strip()}

    if tool_name:
        result = execute_tool(tool_name, args, organization, user)
        tool_calls = [{"id": f"call_local_{tool_name}", "name": tool_name, "arguments": args}]
        tool_results = [{"tool_call_id": f"call_local_{tool_name}", "name": tool_name, "result": result}]

        if isinstance(result, dict) and result.get("requires_confirmation"):
            content = f"I have prepared a confirmation proposal for {result.get('proposed_action', 'this action')}. Please review the details in the confirmation card and click Confirm to execute."
        elif isinstance(result, dict) and "error" in result:
            content = f"Could not complete request: {result['error']}"
        else:
            content = f"Here is the verified data from your operations records for {tool_name.replace('_', ' ')}:\n\n```json\n{json.dumps(result, indent=2, default=str)}\n```"

        return content, tool_calls, tool_results

    return (
        "I'm operating in verified local mode because GROQ_API_KEY is not configured on this server. "
        "I can answer deterministic queries like 'What is my current inventory value?', 'Which products are low in stock?', "
        "'Which products are out of stock?', 'Which hub has the most inventory?', or prepare stock operations. "
        "Set GROQ_API_KEY to enable full conversational LLM reasoning.",
        [],
        [],
    )


def chat(*, organization, user, message: str, conversation_id: int | None = None):
    """
    Process a user message and return the AI response.

    Security & Architectural Invariants:
    1. User and organization are always server-authenticated; never client-spoofed.
    2. Conversations and messages are strictly tenant-isolated.
    3. LLM executes deterministic backend tools; never mutates data directly.
    4. Write operations return confirmation proposals requiring explicit user confirmation.
    """
    conversation = get_or_create_conversation(organization, user, conversation_id)

    # Persist user message
    user_msg = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=message,
    )

    # Set title if initial message
    if conversation.messages.count() <= 1:
        first_line = message.strip().split("\n")[0][:80]
        conversation.title = first_line or "New conversation"
        conversation.save(update_fields=["title", "updated_at"])

    client = get_groq_client()
    system_prompt = _build_system_prompt(organization, user)

    if not client:
        # Graceful fallback without crashing
        content, tool_calls, tool_results = _rule_based_fallback(message, organization, user)
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results,
            metadata={"groq_configured": False},
        )
        conversation.save(update_fields=["updated_at"])
        return _format_response(conversation, assistant_msg, tool_calls, tool_results)

    # Client exists -> Groq tool-calling flow
    history = get_conversation_history(conversation)
    groq_messages = [{"role": "system", "content": system_prompt}] + history
    model = getattr(settings, "GROQ_MODEL", "") or os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=groq_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=2048,
            temperature=0.2,
        )

        choice = response.choices[0]
        assistant_reply = choice.message
        tool_calls_data = []
        tool_results_data = []

        if assistant_reply.tool_calls:
            for tc in assistant_reply.tool_calls:
                t_name = tc.function.name
                try:
                    t_args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    t_args = {}

                tool_calls_data.append({
                    "id": tc.id,
                    "name": t_name,
                    "arguments": t_args,
                })

                # Execute tool strictly with active org and user context
                result = execute_tool(t_name, t_args, organization, user)
                tool_results_data.append({
                    "tool_call_id": tc.id,
                    "name": t_name,
                    "result": result,
                })

            # Record assistant tool-calling step
            Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=assistant_reply.content or "",
                tool_calls=tool_calls_data,
            )

            # Build continuation messages with tool results
            second_round_messages = list(groq_messages)
            second_round_messages.append({
                "role": "assistant",
                "content": assistant_reply.content or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"]),
                        },
                    }
                    for tc in tool_calls_data
                ],
            })

            for tr in tool_results_data:
                second_round_messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": json.dumps(tr["result"], default=str),
                })

            final_completion = client.chat.completions.create(
                model=model,
                messages=second_round_messages,
                max_tokens=2048,
                temperature=0.2,
            )
            final_content = final_completion.choices[0].message.content or ""
        else:
            final_content = assistant_reply.content or ""

        assistant_msg = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=final_content,
            tool_calls=tool_calls_data,
            tool_results=tool_results_data,
            metadata={"groq_configured": True},
        )
        conversation.save(update_fields=["updated_at"])
        return _format_response(conversation, assistant_msg, tool_calls_data, tool_results_data)

    except Exception as exc:
        logger.error(f"Groq API call failed: {exc}", exc_info=True)
        # Attempt fallback to rule-based execution
        content, tool_calls, tool_results = _rule_based_fallback(message, organization, user)
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results,
            metadata={"error": str(exc), "fallback": True},
        )
        conversation.save(update_fields=["updated_at"])
        return _format_response(conversation, assistant_msg, tool_calls, tool_results)


def _format_response(conversation, message, tool_calls=None, tool_results=None):
    """Format standard API response."""
    return {
        "conversation_id": conversation.id,
        "conversation_title": conversation.title,
        "message": {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "tool_calls": tool_calls or message.tool_calls or [],
            "tool_results": tool_results or message.tool_results or [],
            "created_at": message.created_at.isoformat(),
        },
    }
