from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        RECEIPT = "receipt", "Receipt"
        ISSUE = "issue", "Issue"
        ADJUSTMENT = "adjustment", "Adjustment"
        TRANSFER_IN = "transfer_in", "Transfer in"
        TRANSFER_OUT = "transfer_out", "Transfer out"

    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="stock_movements")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="movements")
    hub = models.ForeignKey("hubs.Hub", on_delete=models.PROTECT, related_name="stock_movements")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements")
    movement_type = models.CharField(max_length=24, choices=MovementType.choices)
    quantity_delta = models.DecimalField(max_digits=14, decimal_places=2)
    quantity_before = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_after = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    reason = models.CharField(max_length=240, blank=True)
    reference_type = models.CharField(max_length=80, blank=True)
    reference_id = models.CharField(max_length=120, blank=True)
    idempotency_key = models.CharField(max_length=160, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity_delta__gt=0) | Q(quantity_delta__lt=0), name="movement_delta_not_zero"),
            models.CheckConstraint(condition=Q(quantity_after__gte=0), name="movement_after_non_negative"),
            models.UniqueConstraint(fields=["organization", "idempotency_key"], name="unique_movement_idempotency_per_organization"),
        ]
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["organization", "product", "created_at"]),
            models.Index(fields=["organization", "hub", "created_at"]),
        ]

    def __str__(self):
        return f"{self.movement_type}: {self.product} {self.quantity_delta}"
