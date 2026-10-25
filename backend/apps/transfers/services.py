from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit
from apps.inventory.services import InventoryOperationError, change_stock

from .models import Transfer


class TransferStateError(ValueError):
    pass


@transaction.atomic
def transition_transfer(*, transfer_id, actor, action):
    transfer = Transfer.objects.select_for_update().select_related("organization", "product", "source_hub", "destination_hub").get(pk=transfer_id)
    if transfer.organization.memberships.filter(user=actor, is_active=True).exists() is False:
        raise TransferStateError("The actor is not a member of this organization.")

    if action == "submit" and transfer.status == Transfer.Status.DRAFT:
        if transfer.source_hub_id == transfer.destination_hub_id:
            raise TransferStateError("Source and destination hubs must be different.")
        transfer.status = Transfer.Status.PENDING
    elif action == "approve" and transfer.status == Transfer.Status.PENDING:
        transfer.status = Transfer.Status.APPROVED
        transfer.approved_by = actor
    elif action == "dispatch" and transfer.status == Transfer.Status.APPROVED:
        change_stock(
            organization=transfer.organization,
            product=transfer.product,
            hub=transfer.source_hub,
            actor=actor,
            movement_type="transfer_out",
            quantity=transfer.quantity,
            reason=f"Transfer {transfer.pk} dispatched",
            idempotency_key=f"transfer:{transfer.pk}:dispatch",
            reference_type="transfer",
            reference_id=str(transfer.pk),
        )
        transfer.status = Transfer.Status.DISPATCHED
        transfer.dispatched_by = actor
        transfer.dispatched_at = timezone.now()
    elif action == "receive" and transfer.status == Transfer.Status.DISPATCHED:
        change_stock(
            organization=transfer.organization,
            product=transfer.product,
            hub=transfer.destination_hub,
            actor=actor,
            movement_type="transfer_in",
            quantity=transfer.quantity,
            reason=f"Transfer {transfer.pk} received",
            idempotency_key=f"transfer:{transfer.pk}:receive",
            reference_type="transfer",
            reference_id=str(transfer.pk),
        )
        transfer.status = Transfer.Status.RECEIVED
        transfer.received_by = actor
        transfer.received_at = timezone.now()
    elif action == "cancel" and transfer.status in {Transfer.Status.DRAFT, Transfer.Status.PENDING, Transfer.Status.APPROVED}:
        transfer.status = Transfer.Status.CANCELLED
    else:
        raise TransferStateError(f"Cannot {action} a transfer in {transfer.status} state.")

    transfer.save(update_fields=["status", "approved_by", "dispatched_by", "dispatched_at", "received_by", "received_at", "updated_at"])
    record_audit(
        organization=transfer.organization,
        actor=actor,
        action=f"transfer.{action}",
        resource_type="transfer",
        resource_id=transfer.pk,
        metadata={"status": transfer.status, "quantity": str(transfer.quantity)},
    )
    return transfer
