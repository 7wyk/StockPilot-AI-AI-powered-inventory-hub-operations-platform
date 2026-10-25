"""
AI tool definitions and execution for StockPilot AI.

All tools call deterministic backend analytics services.
The AI never invents numbers — it reads from the database.

Read-only tools execute automatically.
Write operations produce confirmation proposals that require user approval.
"""

import json
from decimal import Decimal

from apps.analytics import services as analytics
from apps.inventory.models import Product, InventoryBalance
from apps.hubs.models import Hub
from apps.movements.models import StockMovement

# Tool definitions for Groq function calling
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
            "description": "Get deterministic restock recommendations based on target_stock_level − on_hand. Not an AI prediction.",
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
            "description": "Trigger generation of a specific report type. Returns a confirmation that the report is being generated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["inventory_health", "low_stock", "stockout", "inventory_valuation",
                                 "slow_moving", "hub_performance", "stock_movements", "transfers", "restocking"],
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
]

# Tools that require user confirmation (write operations)
WRITE_TOOLS = frozenset({
    "receive_stock", "issue_stock", "adjust_stock",
    "create_transfer", "create_restock_request",
})

# Read-only tools that execute automatically
READ_TOOLS = frozenset({
    "get_inventory_summary", "get_low_stock_products", "get_stockouts",
    "get_hub_inventory", "get_movement_summary", "get_restock_recommendations",
    "get_product_details", "get_stock_health", "generate_report",
})


def execute_tool(tool_name, arguments, organization, user):
    """
    Execute a tool and return the result.
    Only read-only tools are executed here.
    Write tools return confirmation proposals.
    """
    args = arguments if isinstance(arguments, dict) else json.loads(arguments)

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
        return [
            item for item in health["items"]
            if item["status"] == "out_of_stock"
        ]

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
            "status": "report_available",
            "message": f"A {report_type.replace('_', ' ')} report in {fmt.upper()} format is available. "
                       f"The user can download it from the Reports page.",
            "report_type": report_type,
            "format": fmt,
        }

    return {"error": f"Unknown tool: {tool_name}"}


def _get_product_details(organization, args):
    """Look up product by ID, SKU, or name search."""
    product = None

    if args.get("product_id"):
        product = Product.objects.filter(
            organization=organization, id=args["product_id"], is_active=True,
        ).first()
    elif args.get("sku"):
        product = Product.objects.filter(
            organization=organization, sku__iexact=args["sku"], is_active=True,
        ).first()
    elif args.get("name"):
        product = Product.objects.filter(
            organization=organization, name__icontains=args["name"], is_active=True,
        ).first()

    if not product:
        return {"error": "Product not found."}

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
