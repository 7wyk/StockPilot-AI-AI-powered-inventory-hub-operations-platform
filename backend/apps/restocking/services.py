from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.inventory.services import InventoryOperationError, change_stock

from .models import RestockRequest


class RestockStateError(ValueError):
    pass


@transaction.atomic
def transition_restock(*, request_id, actor, action):
    restock = RestockRequest.objects.select_for_update().select_related("organization", "product", "supplier", "hub").get(pk=request_id)
    if restock.organization.memberships.filter(user=actor, is_active=True).exists() is False:
        raise RestockStateError("The actor is not a member of this organization.")

    if action == "submit" and restock.status == RestockRequest.Status.DRAFT:
        restock.status = RestockRequest.Status.PENDING
    elif action == "approve" and restock.status == RestockRequest.Status.PENDING:
        restock.status = RestockRequest.Status.APPROVED
        restock.approved_by = actor
    elif action == "order" and restock.status == RestockRequest.Status.APPROVED:
        restock.status = RestockRequest.Status.ORDERED
    elif action == "receive" and restock.status == RestockRequest.Status.ORDERED:
        change_stock(
            organization=restock.organization,
            product=restock.product,
            hub=restock.hub,
            actor=actor,
            movement_type="receipt",
            quantity=restock.quantity,
            reason=f"Restock request {restock.pk} received",
            idempotency_key=f"restock:{restock.pk}:receive",
            reference_type="restock_request",
            reference_id=str(restock.pk),
        )
        restock.status = RestockRequest.Status.RECEIVED
        restock.received_at = timezone.now()
    elif action == "cancel" and restock.status in {RestockRequest.Status.DRAFT, RestockRequest.Status.PENDING, RestockRequest.Status.APPROVED, RestockRequest.Status.ORDERED}:
        restock.status = RestockRequest.Status.CANCELLED
    else:
        raise RestockStateError(f"Cannot {action} a restock request in {restock.status} state.")

    restock.save(update_fields=["status", "approved_by", "received_at", "updated_at"])
    record_audit(
        organization=restock.organization,
        actor=actor,
        action=f"restock.{action}",
        resource_type="restock_request",
        resource_id=restock.pk,
        metadata={"status": restock.status},
    )
    return restock
