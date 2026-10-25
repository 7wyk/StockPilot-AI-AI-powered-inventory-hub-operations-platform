from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from apps.audit.services import record_audit
from apps.movements.models import StockMovement

from .models import InventoryBalance, Product


class InventoryOperationError(ValueError):
    """Raised when a stock mutation fails a business rule."""


@dataclass(frozen=True)
class StockChangeResult:
    balance: InventoryBalance
    movement: StockMovement


@transaction.atomic
def change_stock(*, organization, product: Product, hub, actor, movement_type: str, quantity: Decimal, reason: str = "", idempotency_key: str | None = None, reference_type: str = "", reference_id: str = "") -> StockChangeResult:
    if product.organization_id != organization.id or hub.organization_id != organization.id:
        raise InventoryOperationError("Product and hub must belong to the active organization.")
    if idempotency_key:
        existing = StockMovement.objects.filter(organization=organization, idempotency_key=idempotency_key).select_related("product", "hub").first()
        if existing:
            balance = InventoryBalance.objects.get(organization=organization, product=existing.product, hub=existing.hub)
            return StockChangeResult(balance=balance, movement=existing)

    try:
        requested = Decimal(str(quantity))
    except Exception as exc:
        raise InventoryOperationError("Quantity must be a valid decimal number.") from exc

    if movement_type in {StockMovement.MovementType.RECEIPT, StockMovement.MovementType.ISSUE, StockMovement.MovementType.TRANSFER_IN, StockMovement.MovementType.TRANSFER_OUT}:
        if requested <= 0:
            raise InventoryOperationError("Receipt, issue, and transfer quantities must be greater than zero.")
        delta = requested if movement_type in {StockMovement.MovementType.RECEIPT, StockMovement.MovementType.TRANSFER_IN} else -requested
    elif movement_type == StockMovement.MovementType.ADJUSTMENT:
        if requested == 0:
            raise InventoryOperationError("An adjustment cannot have a zero delta.")
        delta = requested
    else:
        raise InventoryOperationError("Unsupported movement type.")

    balance, _ = InventoryBalance.objects.get_or_create(organization=organization, product=product, hub=hub)
    balance = InventoryBalance.objects.select_for_update().get(pk=balance.pk)
    if delta < 0 and abs(delta) > balance.available:
        raise InventoryOperationError("The requested quantity exceeds available stock.")

    before = balance.on_hand
    after = before + delta
    if after < 0:
        raise InventoryOperationError("Stock cannot become negative.")
    if balance.reserved > after:
        raise InventoryOperationError("On-hand stock cannot fall below reserved stock.")

    balance.on_hand = after
    balance.save(update_fields=["on_hand", "updated_at"])
    movement = StockMovement.objects.create(
        organization=organization,
        product=product,
        hub=hub,
        actor=actor,
        movement_type=movement_type,
        quantity_delta=delta,
        quantity_before=before,
        quantity_after=after,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
    )
    record_audit(
        organization=organization,
        actor=actor,
        action=f"inventory.{movement_type}",
        resource_type="stock_movement",
        resource_id=movement.pk,
        metadata={"product_id": product.pk, "hub_id": hub.pk, "quantity_delta": str(delta)},
    )
    return StockChangeResult(balance=balance, movement=movement)
