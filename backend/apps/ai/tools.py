"""
AI tool definitions, validation, and execution for StockPilot AI.

All tools call deterministic backend services.
The AI never invents numbers — it reads directly from verified database records.

Read-only tools execute automatically during conversational reasoning.
Write operations NEVER directly mutate inventory. They produce a structured
confirmation proposal that must be reviewed and explicitly confirmed by the user.
"""

from decimal import Decimal, InvalidOperation
import json

from apps.analytics import services as analytics
from apps.audit.services import record_audit
from apps.hubs.models import Hub
from apps.inventory.models import InventoryBalance, Product
from apps.inventory.services import InventoryOperationError, change_stock
from apps.movements.models import StockMovement
from apps.organizations.permissions import (
    OrganizationPermission,
    get_active_membership,
    has_organization_permission,
)
from apps.restocking.models import RestockRequest
from apps.suppliers.models import Supplier
from apps.transfers.models import Transfer


# Tool definitions conforming to OpenAI / Groq function-calling schema
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_inventory_summary",
            "description": "Get a high-level overview of inventory: active products, total units, inventory value, low/out-of-stock counts, movement volume.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_low_stock_products",
            "description": "List products where on_hand is positive but at or below the reorder threshold. Returns product name, SKU, on_hand, threshold, and deficit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hub_id": {"type": "integer", "description": "Optional hub ID to filter by."},
                    "category_id": {"type": "integer", "description": "Optional category ID to filter by."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stockouts",
            "description": "List products with zero inventory across all hubs.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hub_inventory",
            "description": "Get inventory metrics broken down by hub: total units, value, product count, and alert counts per hub.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_movement_summary",
            "description": "Get stock movement trends over a period: daily counts of receipts, issues, adjustments, and transfers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days to look back. Default 30, max 365."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_restock_recommendations",
            "description": "Get deterministic restock recommendations based on target_stock_level − on_hand. Calculated directly from balances.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get detailed information about a specific product including balances across all hubs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Product ID to look up."},
                    "sku": {"type": "string", "description": "Product SKU to search for."},
                    "name": {"type": "string", "description": "Product name to search for (partial match)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_health",
            "description": "Get stock health breakdown: healthy, low stock, out of stock, excess, and slow-moving products with configurable lookback period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lookback_days": {"type": "integer", "description": "Days to check for movement. Default 30."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Trigger generation of a deterministic report type. Returns availability info and metrics summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": [
                            "inventory_health",
                            "low_stock",
                            "stockout",
                            "inventory_valuation",
                            "slow_moving",
                            "hub_performance",
                            "stock_movements",
                            "transfers",
                            "restocking",
                        ],
                        "description": "Type of report to generate.",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["csv", "pdf"],
                        "description": "Report format. Default csv.",
                    },
                },
                "required": ["report_type"],
            },
        },
    },
    # Write Operation Tools — LLM calls these to prepare confirmation proposals
    {
        "type": "function",
        "function": {
            "name": "receive_stock",
            "description": "Propose receiving incoming inventory for a product into a specific hub. Does NOT execute directly; generates a confirmation proposal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Product ID to receive."},
                    "product_sku": {"type": "string", "description": "Product SKU (alternative to product_id)."},
                    "product_name": {"type": "string", "description": "Product name (alternative to product_id)."},
                    "hub_id": {"type": "integer", "description": "Hub ID where stock is received."},
                    "hub_name": {"type": "string", "description": "Hub name or code (alternative to hub_id)."},
                    "quantity": {"type": "string", "description": "Number of units to receive (positive decimal)."},
                    "reason": {"type": "string", "description": "Operational reason or note."},
                },
                "required": ["quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_stock",
            "description": "Propose issuing (removing/shipping) inventory for a product from a hub. Does NOT execute directly; generates a confirmation proposal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Product ID to issue."},
                    "product_sku": {"type": "string", "description": "Product SKU."},
                    "product_name": {"type": "string", "description": "Product name."},
                    "hub_id": {"type": "integer", "description": "Hub ID from which stock is issued."},
                    "hub_name": {"type": "string", "description": "Hub name or code."},
                    "quantity": {"type": "string", "description": "Number of units to issue (positive decimal)."},
                    "reason": {"type": "string", "description": "Operational reason for issuing stock."},
                },
                "required": ["quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_stock",
            "description": "Propose adjusting inventory balance for a product at a hub (e.g. audit discrepancy, damage). Does NOT execute directly; generates a confirmation proposal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Product ID to adjust."},
                    "product_sku": {"type": "string", "description": "Product SKU."},
                    "product_name": {"type": "string", "description": "Product name."},
                    "hub_id": {"type": "integer", "description": "Hub ID where adjustment applies."},
                    "hub_name": {"type": "string", "description": "Hub name or code."},
                    "quantity": {"type": "string", "description": "Adjustment delta (positive or negative decimal, non-zero)."},
                    "reason": {"type": "string", "description": "Reason for adjustment (e.g. cycle count, shrinkage)."},
                },
                "required": ["quantity", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_transfer",
            "description": "Propose transferring inventory between two distinct hubs. Does NOT execute directly; generates a confirmation proposal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Product ID to transfer."},
                    "product_sku": {"type": "string", "description": "Product SKU."},
                    "product_name": {"type": "string", "description": "Product name."},
                    "source_hub_id": {"type": "integer", "description": "Origin hub ID."},
                    "source_hub_name": {"type": "string", "description": "Origin hub name or code."},
                    "destination_hub_id": {"type": "integer", "description": "Destination hub ID."},
                    "destination_hub_name": {"type": "string", "description": "Destination hub name or code."},
                    "quantity": {"type": "string", "description": "Units to transfer (positive decimal)."},
                    "reason": {"type": "string", "description": "Transfer note or justification."},
                },
                "required": ["quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_restock_request",
            "description": "Propose creating a replenishment restock request. Does NOT execute directly; generates a confirmation proposal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "Product ID to restock."},
                    "product_sku": {"type": "string", "description": "Product SKU."},
                    "product_name": {"type": "string", "description": "Product name."},
                    "hub_id": {"type": "integer", "description": "Target hub ID."},
                    "hub_name": {"type": "string", "description": "Target hub name."},
                    "supplier_id": {"type": "integer", "description": "Optional supplier ID."},
                    "quantity": {"type": "string", "description": "Quantity to reorder (positive decimal)."},
                    "reason": {"type": "string", "description": "Reason or notes for restock request."},
                },
                "required": ["quantity"],
            },
        },
    },
]

READ_TOOLS = frozenset({
    "get_inventory_summary",
    "get_low_stock_products",
    "get_stockouts",
    "get_hub_inventory",
    "get_movement_summary",
    "get_restock_recommendations",
    "get_product_details",
    "get_stock_health",
    "generate_report",
})

WRITE_TOOLS = frozenset({
    "receive_stock",
    "issue_stock",
    "adjust_stock",
    "create_transfer",
    "create_restock_request",
})


def execute_tool(tool_name: str, arguments, organization, user):
    """
    Execute a tool call from the AI assistant.
    Read-only tools execute deterministic queries directly.
    Write tools validate inputs and return a confirmation proposal without mutating data.
    """
    args = arguments if isinstance(arguments, dict) else json.loads(arguments or "{}")

    # Handle write operations -> Always return confirmation proposal
    if tool_name in WRITE_TOOLS:
        return prepare_write_proposal(tool_name, args, organization, user)

    # Read-only operations
    if tool_name == "get_inventory_summary":
        return analytics.get_overview(organization)

    elif tool_name == "get_low_stock_products":
        return analytics.get_low_stock_products(
            organization,
            hub_id=args.get("hub_id"),
            category_id=args.get("category_id"),
        )

    elif tool_name == "get_stockouts":
        health = analytics.get_stock_health(organization)
        return [item for item in health["items"] if item["status"] == "out_of_stock"]

    elif tool_name == "get_hub_inventory":
        return analytics.get_hub_analytics(organization)

    elif tool_name == "get_movement_summary":
        days = min(int(args.get("days", 30)), 365)
        return analytics.get_movement_trends(organization, days=days)

    elif tool_name == "get_restock_recommendations":
        return analytics.get_restock_recommendations(organization)

    elif tool_name == "get_product_details":
        return _get_product_details(organization, args)

    elif tool_name == "get_stock_health":
        lookback = min(int(args.get("lookback_days", 30)), 365)
        return analytics.get_stock_health(organization, lookback_days=lookback)

    elif tool_name == "generate_report":
        report_type = args.get("report_type", "inventory_health")
        fmt = args.get("format", "csv")
        return {
            "status": "report_ready",
            "report_type": report_type,
            "format": fmt,
            "message": f"Deterministic {report_type.replace('_', ' ')} data generated. "
                       f"The complete {fmt.upper()} report file can be viewed and downloaded on the Reports page.",
        }

    return {"error": f"Unknown tool: {tool_name}"}


def _get_product_details(organization, args: dict):
    """Look up product by ID, SKU, or name search strictly within tenant."""
    product = None
    if args.get("product_id"):
        product = Product.objects.filter(
            organization=organization, id=args["product_id"], is_active=True,
        ).first()
    elif args.get("sku"):
        product = Product.objects.filter(
            organization=organization, sku__iexact=str(args["sku"]).strip(), is_active=True,
        ).first()
    elif args.get("name"):
        product = Product.objects.filter(
            organization=organization, name__icontains=str(args["name"]).strip(), is_active=True,
        ).first()

    if not product:
        return {"error": "Product not found in this organization."}

    balances = InventoryBalance.objects.filter(
        organization=organization, product=product,
    ).select_related("hub")

    return {
        "product_id": product.id,
        "name": product.name,
        "sku": product.sku,
        "cost_price": str(product.cost_price),
        "selling_price": str(product.selling_price) if product.selling_price else None,
        "reorder_threshold": str(product.reorder_threshold),
        "target_stock_level": str(product.target_stock_level),
        "category": product.category.name if product.category else None,
        "unit_of_measure": product.unit_of_measure,
        "is_active": product.is_active,
        "balances": [
            {
                "hub_id": b.hub.id,
                "hub_name": b.hub.name,
                "hub_code": b.hub.code,
                "on_hand": str(b.on_hand),
                "reserved": str(b.reserved),
                "available": str(b.available),
            }
            for b in balances
        ],
        "total_on_hand": str(sum(b.on_hand for b in balances)),
    }


def _resolve_product(organization, args: dict):
    """Resolve product strictly within active organization."""
    if args.get("product_id"):
        return Product.objects.filter(organization=organization, id=args["product_id"]).first()
    sku = args.get("product_sku") or args.get("sku")
    if sku:
        return Product.objects.filter(organization=organization, sku__iexact=str(sku).strip()).first()
    name = args.get("product_name") or args.get("name")
    if name:
        return Product.objects.filter(organization=organization, name__icontains=str(name).strip()).first()
    return None


def _resolve_hub(organization, hub_id=None, hub_identifier=None):
    """Resolve hub strictly within active organization."""
    if hub_id:
        return Hub.objects.filter(organization=organization, id=hub_id).first()
    if hub_identifier:
        s = str(hub_identifier).strip()
        return (
            Hub.objects.filter(organization=organization, code__iexact=s).first()
            or Hub.objects.filter(organization=organization, name__icontains=s).first()
        )
    return Hub.objects.filter(organization=organization, is_active=True).first()


def prepare_write_proposal(tool_name: str, args: dict, organization, user):
    """
    Validate permissions, inputs, and database state for a proposed write operation.
    NEVER mutates inventory. Returns a structured confirmation proposal.
    """
    membership = get_active_membership(user)
    if not membership:
        return {"error": "User does not have an active organization membership."}

    # Verify action-level permissions
    perm_map = {
        "receive_stock": OrganizationPermission.ADJUST_STOCK,
        "issue_stock": OrganizationPermission.ADJUST_STOCK,
        "adjust_stock": OrganizationPermission.ADJUST_STOCK,
        "create_transfer": OrganizationPermission.INITIATE_TRANSFERS,
        "create_restock_request": OrganizationPermission.CREATE_RESTOCK,
    }
    required_perm = perm_map.get(tool_name)
    if required_perm and not (
        has_organization_permission(membership, required_perm)
        or has_organization_permission(membership, OrganizationPermission.APPROVE_AI_WRITES)
    ):
        return {
            "error": f"Permission denied: you do not have permission to execute {tool_name} in this organization."
        }

    # Resolve product
    product = _resolve_product(organization, args)
    if not product:
        return {"error": "Product could not be identified or does not belong to this organization."}

    # Parse and validate quantity
    try:
        qty_str = str(args.get("quantity", "")).strip()
        qty = Decimal(qty_str)
    except (InvalidOperation, ValueError, TypeError):
        return {"error": "Invalid quantity provided. Must be a numeric value."}

    reason = str(args.get("reason", "Requested via AI Operations Assistant")).strip()

    # Process specific actions
    if tool_name in {"receive_stock", "issue_stock", "adjust_stock"}:
        hub = _resolve_hub(organization, args.get("hub_id"), args.get("hub_name"))
        if not hub:
            return {"error": "Hub could not be identified or does not belong to this organization."}

        balance = InventoryBalance.objects.filter(
            organization=organization, product=product, hub=hub,
        ).first()
        current_on_hand = balance.on_hand if balance else Decimal("0")
        current_available = balance.available if balance else Decimal("0")

        if tool_name == "receive_stock":
            if qty <= 0:
                return {"error": "Received quantity must be greater than zero."}
            proposed_action = f"Receive {qty} units of {product.name} ({product.sku}) into hub {hub.name}."
            label = "Receive Stock"

        elif tool_name == "issue_stock":
            if qty <= 0:
                return {"error": "Issued quantity must be greater than zero."}
            if qty > current_available:
                return {
                    "error": f"Cannot issue {qty} units: only {current_available} units available at {hub.name}."
                }
            proposed_action = f"Issue {qty} units of {product.name} ({product.sku}) from hub {hub.name}."
            label = "Issue Stock"

        else:  # adjust_stock
            if qty == 0:
                return {"error": "Adjustment quantity cannot be zero."}
            if qty < 0 and abs(qty) > current_available:
                return {
                    "error": f"Adjustment of {qty} exceeds available stock ({current_available}) at {hub.name}."
                }
            delta_sign = f"+{qty}" if qty > 0 else str(qty)
            proposed_action = f"Adjust stock of {product.name} by {delta_sign} at hub {hub.name}."
            label = "Adjust Stock"

        return {
            "requires_confirmation": True,
            "action": tool_name,
            "operation_label": label,
            "parameters": {
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "hub_id": hub.id,
                "hub_name": hub.name,
                "hub_code": hub.code,
                "quantity": str(qty),
                "reason": reason,
            },
            "current_state": {
                "on_hand": str(current_on_hand),
                "available": str(current_available),
            },
            "proposed_action": proposed_action,
            "message": f"Action proposal prepared for {product.name}. User confirmation is required before execution.",
        }

    elif tool_name == "create_transfer":
        src_hub = _resolve_hub(organization, args.get("source_hub_id"), args.get("source_hub_name"))
        dst_hub = _resolve_hub(organization, args.get("destination_hub_id"), args.get("destination_hub_name"))

        if not src_hub or not dst_hub:
            return {"error": "Both source and destination hubs must be specified and belong to this organization."}
        if src_hub.id == dst_hub.id:
            return {"error": "Source and destination hubs must be different."}
        if qty <= 0:
            return {"error": "Transfer quantity must be greater than zero."}

        balance = InventoryBalance.objects.filter(
            organization=organization, product=product, hub=src_hub,
        ).first()
        current_available = balance.available if balance else Decimal("0")
        if qty > current_available:
            return {
                "error": f"Cannot transfer {qty} units: only {current_available} units available at origin {src_hub.name}."
            }

        return {
            "requires_confirmation": True,
            "action": "create_transfer",
            "operation_label": "Inter-Hub Transfer",
            "parameters": {
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "source_hub_id": src_hub.id,
                "source_hub_name": src_hub.name,
                "destination_hub_id": dst_hub.id,
                "destination_hub_name": dst_hub.name,
                "quantity": str(qty),
                "reason": reason,
            },
            "current_state": {
                "source_on_hand": str(balance.on_hand if balance else "0"),
                "source_available": str(current_available),
            },
            "proposed_action": f"Transfer {qty} units of {product.name} from {src_hub.name} to {dst_hub.name}.",
            "message": f"Transfer proposal prepared. User confirmation is required before creation.",
        }

    elif tool_name == "create_restock_request":
        hub = _resolve_hub(organization, args.get("hub_id"), args.get("hub_name"))
        if not hub:
            return {"error": "Target hub could not be identified or does not belong to this organization."}
        if qty <= 0:
            return {"error": "Restock quantity must be greater than zero."}

        supplier = None
        if args.get("supplier_id"):
            supplier = Supplier.objects.filter(organization=organization, id=args["supplier_id"]).first()

        balance = InventoryBalance.objects.filter(
            organization=organization, product=product, hub=hub,
        ).first()

        return {
            "requires_confirmation": True,
            "action": "create_restock_request",
            "operation_label": "Create Restock Request",
            "parameters": {
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "hub_id": hub.id,
                "hub_name": hub.name,
                "supplier_id": supplier.id if supplier else None,
                "supplier_name": supplier.name if supplier else None,
                "quantity": str(qty),
                "reason": reason,
            },
            "current_state": {
                "on_hand": str(balance.on_hand if balance else "0"),
                "reorder_threshold": str(product.reorder_threshold),
                "target_stock_level": str(product.target_stock_level),
            },
            "proposed_action": f"Create restock request for {qty} units of {product.name} at {hub.name}.",
            "message": f"Restock request proposal prepared. User confirmation is required before creation.",
        }

    return {"error": f"Unsupported write operation: {tool_name}"}


def execute_confirmed_write_action(action: str, parameters: dict, organization, user):
    """
    Execute a previously proposed write operation after the user explicitly confirmed it.
    Re-validates tenant boundaries, permissions, and database constraints.
    Reuses existing transactional services and records an audit log.
    """
    membership = get_active_membership(user)
    if not membership:
        raise ValueError("User does not have an active organization membership.")

    # Re-verify permissions
    perm_map = {
        "receive_stock": OrganizationPermission.ADJUST_STOCK,
        "issue_stock": OrganizationPermission.ADJUST_STOCK,
        "adjust_stock": OrganizationPermission.ADJUST_STOCK,
        "create_transfer": OrganizationPermission.INITIATE_TRANSFERS,
        "create_restock_request": OrganizationPermission.CREATE_RESTOCK,
    }
    required_perm = perm_map.get(action)
    if required_perm and not (
        has_organization_permission(membership, required_perm)
        or has_organization_permission(membership, OrganizationPermission.APPROVE_AI_WRITES)
    ):
        raise PermissionError(f"Permission denied for action: {action}")

    # Re-verify product belongs to tenant
    product_id = parameters.get("product_id")
    product = Product.objects.filter(organization=organization, id=product_id).first()
    if not product:
        raise ValueError("Product not found or does not belong to active organization.")

    qty = Decimal(str(parameters["quantity"]))
    reason = parameters.get("reason", "Confirmed via AI Operations Assistant")

    if action in {"receive_stock", "issue_stock", "adjust_stock"}:
        hub_id = parameters.get("hub_id")
        hub = Hub.objects.filter(organization=organization, id=hub_id).first()
        if not hub:
            raise ValueError("Hub not found or does not belong to active organization.")

        movement_type_map = {
            "receive_stock": StockMovement.MovementType.RECEIPT,
            "issue_stock": StockMovement.MovementType.ISSUE,
            "adjust_stock": StockMovement.MovementType.ADJUSTMENT,
        }
        movement_type = movement_type_map[action]

        # Call existing transactional service
        res = change_stock(
            organization=organization,
            product=product,
            hub=hub,
            actor=user,
            movement_type=movement_type,
            quantity=qty,
            reason=f"[AI Assistant Confirmed] {reason}",
            reference_type="ai_assistant",
            reference_id=str(user.id),
        )

        return {
            "status": "success",
            "action": action,
            "product_id": product.id,
            "product_name": product.name,
            "hub_id": hub.id,
            "hub_name": hub.name,
            "movement_id": res.movement.id,
            "new_on_hand": str(res.balance.on_hand),
            "new_available": str(res.balance.available),
            "message": f"Successfully executed {action.replace('_', ' ')} for {product.name}.",
        }

    elif action == "create_transfer":
        src_hub = Hub.objects.filter(organization=organization, id=parameters.get("source_hub_id")).first()
        dst_hub = Hub.objects.filter(organization=organization, id=parameters.get("destination_hub_id")).first()
        if not src_hub or not dst_hub:
            raise ValueError("Source or destination hub not found in active organization.")

        transfer = Transfer.objects.create(
            organization=organization,
            product=product,
            source_hub=src_hub,
            destination_hub=dst_hub,
            quantity=qty,
            requested_by=user,
            status=Transfer.Status.DRAFT,
            notes=f"[AI Assistant Confirmed] {reason}",
        )
        record_audit(
            organization=organization,
            actor=user,
            action="transfer.create",
            resource_type="transfer",
            resource_id=transfer.pk,
            metadata={"source": "ai_assistant", "product_id": product.pk, "quantity": str(qty)},
        )
        return {
            "status": "success",
            "action": action,
            "transfer_id": transfer.id,
            "product_name": product.name,
            "quantity": str(transfer.quantity),
            "message": f"Successfully created transfer #{transfer.id} for {product.name}.",
        }

    elif action == "create_restock_request":
        hub = Hub.objects.filter(organization=organization, id=parameters.get("hub_id")).first()
        if not hub:
            raise ValueError("Target hub not found in active organization.")

        supplier = None
        if parameters.get("supplier_id"):
            supplier = Supplier.objects.filter(organization=organization, id=parameters["supplier_id"]).first()

        restock = RestockRequest.objects.create(
            organization=organization,
            product=product,
            hub=hub,
            supplier=supplier,
            quantity=qty,
            requested_by=user,
            status=RestockRequest.Status.DRAFT,
            notes=f"[AI Assistant Confirmed] {reason}",
        )
        record_audit(
            organization=organization,
            actor=user,
            action="restock.create",
            resource_type="restock_request",
            resource_id=restock.pk,
            metadata={"source": "ai_assistant", "product_id": product.pk, "quantity": str(qty)},
        )
        return {
            "status": "success",
            "action": action,
            "restock_id": restock.id,
            "product_name": product.name,
            "quantity": str(restock.quantity),
            "message": f"Successfully created restock request #{restock.id} for {product.name}.",
        }

    raise ValueError(f"Unknown action: {action}")
