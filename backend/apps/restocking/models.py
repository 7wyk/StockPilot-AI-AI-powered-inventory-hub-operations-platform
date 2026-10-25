from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class RestockRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        ORDERED = "ordered", "Ordered"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="restock_requests")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="restock_requests")
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.SET_NULL, null=True, blank=True, related_name="restock_requests")
    hub = models.ForeignKey("hubs.Hub", on_delete=models.PROTECT, related_name="restock_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="restock_requests_created")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="restock_requests_approved")
    quantity = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    external_reference = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "status", "created_at"])]

    def __str__(self):
        return f"Restock {self.product} x {self.quantity} ({self.status})"
