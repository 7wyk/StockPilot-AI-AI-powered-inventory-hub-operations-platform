"""
Deterministic analytics calculations for StockPilot AI.

All calculations are database-backed using Django ORM aggregation.
No values are fabricated or estimated. Every rule is documented.

Calculation Rules
=================
- Inventory value: sum(cost_price × on_hand) across all InventoryBalance rows
- Low stock: on_hand > 0 AND on_hand <= product.reorder_threshold (aggregated across all hubs)
- Out of stock: total on_hand == 0 for a product
- Restock recommendation: target_stock_level - total_on_hand where total_on_hand < target_stock_level
- Slow-moving inventory: products with zero stock movements in the configured lookback period
  (default 30 days). This is a transparent, configurable rule — not an AI prediction.
- Excess inventory: on_hand > target_stock_level (when target_stock_level > 0)
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Case,
    Count,
    DecimalField,
    F,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.hubs.models import Hub
from apps.inventory.models import Category, InventoryBalance, Product
from apps.movements.models import StockMovement
from apps.restocking.models import RestockRequest
from apps.transfers.models import Transfer


def get_overview(organization):
    """Return top-level KPI metrics for the organization."""
    products = Product.objects.filter(organization=organization, is_active=True)
    balances = InventoryBalance.objects.filter(organization=organization).select_related("product")

    total_units = balances.aggregate(
        total=Coalesce(Sum("on_hand"), Value(Decimal("0")))
    )["total"]

    inventory_value = sum(
        (b.product.cost_price * b.on_hand for b in balances), Decimal("0")
    )

    # Annotate each active product with total on_hand across all hubs
    annotated = products.annotate(
        total_on_hand=Coalesce(Sum("balances__on_hand"), Value(Decimal("0")))
    )

    low_stock = annotated.filter(
        total_on_hand__gt=0,
        total_on_hand__lte=F("reorder_threshold"),
        reorder_threshold__gt=0,
    ).count()

    out_of_stock = annotated.filter(total_on_hand=0).count()

    active_hubs = Hub.objects.filter(organization=organization, is_active=True).count()

    # Movement volume in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    movement_volume = StockMovement.objects.filter(
        organization=organization,
        created_at__gte=thirty_days_ago,
    ).count()

    return {
        "active_products": products.count(),
        "total_units": str(total_units),
        "inventory_value": str(inventory_value),
        "low_stock_products": low_stock,
        "out_of_stock_products": out_of_stock,
        "active_hubs": active_hubs,
        "movement_volume_30d": movement_volume,
        "data_status": "live" if products.exists() else "empty",
    }


def get_movement_trends(organization, days=30):
    """
    Return daily movement counts and value changes for the given period.
    If insufficient data exists, returns an empty list with a data_status indicator.
    """
    since = timezone.now() - timedelta(days=days)
    movements = (
        StockMovement.objects.filter(
            organization=organization,
            created_at__gte=since,
        )
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(
            count=Count("id"),
            receipts=Count("id", filter=Q(movement_type="receipt")),
            issues=Count("id", filter=Q(movement_type="issue")),
            adjustments=Count("id", filter=Q(movement_type="adjustment")),
            transfers_in=Count("id", filter=Q(movement_type="transfer_in")),
            transfers_out=Count("id", filter=Q(movement_type="transfer_out")),
        )
        .order_by("date")
    )
    results = list(movements)
    return {
        "period_days": days,
        "data_status": "live" if results else "insufficient_history",
        "trends": [
            {
                "date": str(row["date"]),
                "total": row["count"],
                "receipts": row["receipts"],
                "issues": row["issues"],
                "adjustments": row["adjustments"],
                "transfers_in": row["transfers_in"],
                "transfers_out": row["transfers_out"],
            }
            for row in results
        ],
    }


def get_hub_analytics(organization):
    """Return inventory metrics grouped by hub."""
    hubs = Hub.objects.filter(organization=organization, is_active=True)
    results = []
    for hub in hubs:
        balances = InventoryBalance.objects.filter(
            organization=organization, hub=hub
        ).select_related("product")
        total_units = sum((b.on_hand for b in balances), Decimal("0"))
        total_value = sum((b.product.cost_price * b.on_hand for b in balances), Decimal("0"))
        product_count = balances.values("product").distinct().count()
        low_stock_count = 0
        out_of_stock_count = 0
        for b in balances:
            if b.on_hand == 0:
                out_of_stock_count += 1
            elif b.product.reorder_threshold > 0 and b.on_hand <= b.product.reorder_threshold:
                low_stock_count += 1

        results.append({
            "hub_id": hub.id,
            "hub_name": hub.name,
            "hub_code": hub.code,
            "total_units": str(total_units),
            "total_value": str(total_value),
            "product_count": product_count,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
        })
    return results


def get_stock_health(organization, lookback_days=30):
    """
    Return stock health breakdown: healthy, low stock, out of stock,
    excess, and slow-moving inventory.

    Slow-moving rule: products with zero stock movements in the last
    `lookback_days` days. This is a transparent, configurable threshold.
    """
    products = Product.objects.filter(
        organization=organization, is_active=True
    ).annotate(
        total_on_hand=Coalesce(Sum("balances__on_hand"), Value(Decimal("0")))
    )

    since = timezone.now() - timedelta(days=lookback_days)
    products_with_movements = set(
        StockMovement.objects.filter(
            organization=organization,
            created_at__gte=since,
        )
        .values_list("product_id", flat=True)
        .distinct()
    )

    healthy = 0
    low_stock = 0
    out_of_stock = 0
    excess = 0
    slow_moving = 0
    items = []

    for p in products:
        on_hand = p.total_on_hand
        status = "healthy"
        if on_hand == 0:
            out_of_stock += 1
            status = "out_of_stock"
        elif p.reorder_threshold > 0 and on_hand <= p.reorder_threshold:
            low_stock += 1
            status = "low_stock"
        elif p.target_stock_level > 0 and on_hand > p.target_stock_level:
            excess += 1
            status = "excess"
        else:
            healthy += 1

        has_movement = p.id in products_with_movements
        if on_hand > 0 and not has_movement:
            slow_moving += 1
            if status == "healthy":
                status = "slow_moving"

        items.append({
            "product_id": p.id,
            "product_name": p.name,
            "sku": p.sku,
            "on_hand": str(on_hand),
            "reorder_threshold": str(p.reorder_threshold),
            "target_stock_level": str(p.target_stock_level),
            "status": status,
            "has_recent_movement": has_movement,
        })

    return {
        "lookback_days": lookback_days,
        "summary": {
            "total_products": len(items),
            "healthy": healthy,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "excess": excess,
            "slow_moving": slow_moving,
        },
        "items": items,
    }


def get_low_stock_products(organization, hub_id=None, category_id=None):
    """
    Return products where total on_hand > 0 and on_hand <= reorder_threshold.
    Low stock rule: on_hand is positive but at or below reorder_threshold.
    """
    products = Product.objects.filter(
        organization=organization,
        is_active=True,
        reorder_threshold__gt=0,
    )
    if category_id:
        products = products.filter(category_id=category_id)

    balance_filter = Q(balances__organization=organization)
    if hub_id:
        balance_filter &= Q(balances__hub_id=hub_id)

    annotated = products.annotate(
        total_on_hand=Coalesce(Sum("balances__on_hand", filter=balance_filter), Value(Decimal("0")))
    ).filter(
        total_on_hand__gt=0,
        total_on_hand__lte=F("reorder_threshold"),
    ).order_by("total_on_hand")

    return [
        {
            "product_id": p.id,
            "product_name": p.name,
            "sku": p.sku,
            "on_hand": str(p.total_on_hand),
            "reorder_threshold": str(p.reorder_threshold),
            "target_stock_level": str(p.target_stock_level),
            "deficit": str(max(p.target_stock_level - p.total_on_hand, Decimal("0"))),
            "category": p.category.name if p.category else None,
        }
        for p in annotated.select_related("category")
    ]


def get_restock_recommendations(organization):
    """
    Return products that need restocking: on_hand < target_stock_level.
    Recommendation = target_stock_level - total_on_hand.
    This is a deterministic calculation, not an AI prediction.
    """
    products = Product.objects.filter(
        organization=organization,
        is_active=True,
        target_stock_level__gt=0,
    ).annotate(
        total_on_hand=Coalesce(Sum("balances__on_hand"), Value(Decimal("0")))
    ).filter(
        total_on_hand__lt=F("target_stock_level"),
    ).order_by(
        Case(
            When(total_on_hand=0, then=Value(0)),
            default=Value(1),
        ),
        "total_on_hand",
    )

    return [
        {
            "product_id": p.id,
            "product_name": p.name,
            "sku": p.sku,
            "on_hand": str(p.total_on_hand),
            "target_stock_level": str(p.target_stock_level),
            "recommended_quantity": str(p.target_stock_level - p.total_on_hand),
            "cost_price": str(p.cost_price),
            "estimated_cost": str(p.cost_price * (p.target_stock_level - p.total_on_hand)),
            "category": p.category.name if p.category else None,
            "priority": "critical" if p.total_on_hand == 0 else "low" if p.total_on_hand > p.reorder_threshold else "high",
        }
        for p in products.select_related("category")
    ]


def get_inventory_valuation(organization, hub_id=None, category_id=None):
    """
    Return detailed inventory valuation: cost_price × on_hand per balance row.
    """
    balances = InventoryBalance.objects.filter(
        organization=organization,
    ).select_related("product", "product__category", "hub")

    if hub_id:
        balances = balances.filter(hub_id=hub_id)
    if category_id:
        balances = balances.filter(product__category_id=category_id)

    items = []
    total_value = Decimal("0")
    total_units = Decimal("0")

    for b in balances.filter(on_hand__gt=0):
        line_value = b.product.cost_price * b.on_hand
        total_value += line_value
        total_units += b.on_hand
        items.append({
            "product_id": b.product.id,
            "product_name": b.product.name,
            "sku": b.product.sku,
            "hub_name": b.hub.name,
            "on_hand": str(b.on_hand),
            "cost_price": str(b.product.cost_price),
            "line_value": str(line_value),
            "category": b.product.category.name if b.product.category else None,
        })

    return {
        "total_value": str(total_value),
        "total_units": str(total_units),
        "line_count": len(items),
        "items": items,
    }


def get_movement_report(organization, days=30, hub_id=None, product_id=None, movement_type=None):
    """Return filtered stock movement records."""
    since = timezone.now() - timedelta(days=days)
    qs = StockMovement.objects.filter(
        organization=organization,
        created_at__gte=since,
    ).select_related("product", "hub", "actor").order_by("-created_at")

    if hub_id:
        qs = qs.filter(hub_id=hub_id)
    if product_id:
        qs = qs.filter(product_id=product_id)
    if movement_type:
        qs = qs.filter(movement_type=movement_type)

    return [
        {
            "id": m.id,
            "product_name": m.product.name,
            "product_sku": m.product.sku,
            "hub_name": m.hub.name,
            "movement_type": m.movement_type,
            "quantity_delta": str(m.quantity_delta),
            "quantity_before": str(m.quantity_before),
            "quantity_after": str(m.quantity_after),
            "reason": m.reason,
            "actor": m.actor.email if m.actor else None,
            "created_at": m.created_at.isoformat(),
        }
        for m in qs[:500]  # Bounded query
    ]


def get_transfer_report(organization, days=30, status=None):
    """Return transfer records for reporting."""
    since = timezone.now() - timedelta(days=days)
    qs = Transfer.objects.filter(
        organization=organization,
        created_at__gte=since,
    ).select_related("product", "source_hub", "destination_hub", "requested_by").order_by("-created_at")

    if status:
        qs = qs.filter(status=status)

    return [
        {
            "id": t.id,
            "product_name": t.product.name,
            "source_hub": t.source_hub.name,
            "destination_hub": t.destination_hub.name,
            "quantity": str(t.quantity),
            "status": t.status,
            "requested_by": t.requested_by.email if t.requested_by else None,
            "created_at": t.created_at.isoformat(),
            "dispatched_at": t.dispatched_at.isoformat() if t.dispatched_at else None,
            "received_at": t.received_at.isoformat() if t.received_at else None,
        }
        for t in qs[:500]
    ]


def get_restock_report(organization, days=30, status=None):
    """Return restock request records for reporting."""
    since = timezone.now() - timedelta(days=days)
    qs = RestockRequest.objects.filter(
        organization=organization,
        created_at__gte=since,
    ).select_related("product", "hub", "supplier", "requested_by").order_by("-created_at")

    if status:
        qs = qs.filter(status=status)

    return [
        {
            "id": r.id,
            "product_name": r.product.name,
            "hub_name": r.hub.name,
            "supplier_name": r.supplier.name if r.supplier else None,
            "quantity": str(r.quantity),
            "status": r.status,
            "requested_by": r.requested_by.email if r.requested_by else None,
            "created_at": r.created_at.isoformat(),
            "received_at": r.received_at.isoformat() if r.received_at else None,
        }
        for r in qs[:500]
    ]
