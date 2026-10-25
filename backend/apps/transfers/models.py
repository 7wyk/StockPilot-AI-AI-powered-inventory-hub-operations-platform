from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Transfer(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        DISPATCHED = "dispatched", "Dispatched"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="transfers")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="transfers")
    source_hub = models.ForeignKey("hubs.Hub", on_delete=models.PROTECT, related_name="outgoing_transfers")
    destination_hub = models.ForeignKey("hubs.Hub", on_delete=models.PROTECT, related_name="incoming_transfers")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transfers_created")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="transfers_approved")
    dispatched_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="transfers_dispatched")
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="transfers_received")
    quantity = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "status", "created_at"])]

    def __str__(self):
        return f"Transfer {self.product} {self.source_hub} → {self.destination_hub} ({self.status})"
