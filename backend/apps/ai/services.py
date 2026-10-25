"""
Groq AI service for StockPilot AI operations assistant.

Uses Groq server-side — API key never exposed to the browser.
The assistant answers from verified records via deterministic tools.
"""

import json
import os

from django.utils import timezone

from .models import Conversation, Message, UserPreference
from .tools import TOOL_DEFINITIONS, READ_TOOLS, execute_tool

SYSTEM_PROMPT = """You are the StockPilot AI operations assistant. You help inventory teams understand their stock positions, identify risks, and take the right next action.

IMPORTANT RULES:
1. You MUST use the provided tools to get data. NEVER invent numbers, metrics, or inventory data.
2. When asked about inventory, stock levels, movements, or any quantitative question, ALWAYS call the appropriate tool first.
3. Present tool results clearly with specific numbers from the data.
4. If data is empty or insufficient, say so honestly — don't guess.
5. For write operations (receiving stock, creating transfers, etc.), present a confirmation proposal — never execute directly.
6. You are scoped to the user's active organization. You cannot access other organizations' data.
7. Distinguish between verified measurements (from the database) and your suggestions/recommendations.
8. Be concise but thorough. Use bullet points and tables when helpful.
9. If asked to generate a report, use the generate_report tool and tell the user they can download it from the Reports page.
"""


def get_groq_client():
    """Get configured Groq client. Raises if API key is missing."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except Exception:
        return None


def get_or_create_conversation(organization, user, conversation_id=None):
    """Get existing or create new conversation."""
    if conversation_id:
        conv = Conversation.objects.filter(
            id=conversation_id,
            organization=organization,
            user=user,
        ).first()
        if conv:
            return conv

    return Conversation.objects.create(
        organization=organization,
        user=user,
        title="New conversation",
    )


def get_conversation_history(conversation, limit=20):
    """Get recent messages for context window."""
    messages = conversation.messages.order_by("-created_at")[:limit]
    result = []
    for msg in reversed(messages):
        entry = {"role": msg.role, "content": msg.content}
        if msg.tool_calls:
            entry["tool_calls"] = msg.tool_calls
        result.append(entry)
    return result


def chat(*, organization, user, message, conversation_id=None):
    """
    Process a user message and return the AI response.

    Flow:
    1. Get or create conversation
    2. Build message history with system prompt
    3. Call Groq with tool definitions
    4. If Groq requests tool calls, execute read tools and feed results back
    5. Return final response

    Never lets the LLM mutate data directly.
    """
    conversation = get_or_create_conversation(organization, user, conversation_id)

    # Save user message
    user_msg = Message.objects.create(
        conversation=conversation,
        role=Message.Role.USER,
        content=message,
    )

    # Update conversation title from first message
    if conversation.messages.count() <= 1:
        conversation.title = message[:100]
        conversation.save(update_fields=["title", "updated_at"])

    client = get_groq_client()
    if not client:
        # Graceful fallback when Groq is not configured
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content="I'm currently unable to process your request because the AI service is not configured. "
                    "Please ask your administrator to set the GROQ_API_KEY environment variable. "
                    "In the meantime, you can use the Reports page for analytics and data exports.",
            metadata={"error": "groq_not_configured"},
        )
        return _format_response(conversation, assistant_msg)

    # Build messages for Groq
    history = get_conversation_history(conversation)
    groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    try:
        # First Groq call — may include tool calls
        response = client.chat.completions.create(
            model=model,
            messages=groq_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=2048,
            temperature=0.3,
        )

        assistant_message = response.choices[0].message
        tool_calls_data = []
        tool_results = []

        # Process tool calls
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                tool_calls_data.append({
                    "id": tool_call.id,
                    "name": tool_name,
                    "arguments": tool_args,
                })

                if tool_name in READ_TOOLS:
                    result = execute_tool(tool_name, tool_args, organization, user)
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "result": result,
                    })
                else:
                    # Write tool — return confirmation proposal
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "result": {
                            "requires_confirmation": True,
                            "action": tool_name,
                            "parameters": tool_args,
                            "message": "This action requires your confirmation before it can be executed.",
                        },
                    })

            # Save assistant message with tool calls
            Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=assistant_message.content or "",
                tool_calls=tool_calls_data,
            )

            # Feed tool results back to Groq
            tool_response_messages = groq_messages + [
                {
                    "role": "assistant",
                    "content": assistant_message.content or "",
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
                },
            ]

            for tr in tool_results:
                tool_response_messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": json.dumps(tr["result"], default=str),
                })

            # Second Groq call with tool results
            final_response = client.chat.completions.create(
                model=model,
                messages=tool_response_messages,
                max_tokens=2048,
                temperature=0.3,
            )

            final_content = final_response.choices[0].message.content or ""
        else:
            final_content = assistant_message.content or ""
            tool_calls_data = []
            tool_results = []

        # Save final assistant response
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=final_content,
            tool_calls=tool_calls_data,
            tool_results=tool_results,
        )

        return _format_response(conversation, assistant_msg, tool_calls_data, tool_results)

    except Exception as exc:
        error_content = f"I encountered an error while processing your request: {str(exc)}. Please try again."
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=error_content,
            metadata={"error": str(exc)},
        )
        return _format_response(conversation, assistant_msg)


def _format_response(conversation, message, tool_calls=None, tool_results=None):
    """Format the response for the API."""
    return {
        "conversation_id": conversation.id,
        "message": {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "tool_calls": tool_calls or [],
            "tool_results": tool_results or [],
            "created_at": message.created_at.isoformat(),
        },
        "conversation_title": conversation.title,
    }


def get_user_conversations(organization, user):
    """List user's conversations."""
    convs = Conversation.objects.filter(
        organization=organization,
        user=user,
    ).order_by("-updated_at")[:50]

    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
            "message_count": c.messages.count(),
        }
        for c in convs
    ]


def get_conversation_messages(organization, user, conversation_id):
    """Get all messages for a conversation."""
    conv = Conversation.objects.filter(
        id=conversation_id,
        organization=organization,
        user=user,
    ).first()
    if not conv:
        return None

    messages = conv.messages.order_by("created_at")
    return {
        "conversation_id": conv.id,
        "title": conv.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "tool_results": m.tool_results,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }
