from django.conf import settings
from django.db import models


class Report(models.Model):
    """Persisted report record with optional file storage reference."""

    class ReportType(models.TextChoices):
        INVENTORY_HEALTH = "inventory_health", "Inventory Health"
        LOW_STOCK = "low_stock", "Low Stock"
        STOCKOUT = "stockout", "Stockout"
        INVENTORY_VALUATION = "inventory_valuation", "Inventory Valuation"
        SLOW_MOVING = "slow_moving", "Slow Moving"
        HUB_PERFORMANCE = "hub_performance", "Hub Performance"
        STOCK_MOVEMENTS = "stock_movements", "Stock Movements"
        TRANSFERS = "transfers", "Transfers"
        RESTOCKING = "restocking", "Restocking"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class Format(models.TextChoices):
        CSV = "csv", "CSV"
        PDF = "pdf", "PDF"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports",
    )
    report_type = models.CharField(max_length=32, choices=ReportType.choices)
    format = models.CharField(max_length=8, choices=Format.choices, default=Format.CSV)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    filters = models.JSONField(default=dict, blank=True)
    storage_path = models.CharField(max_length=512, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "report_type", "created_at"]),
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} ({self.status})"
