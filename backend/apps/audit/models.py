from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="audit_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events")
    action = models.CharField(max_length=120)
    resource_type = models.CharField(max_length=120, blank=True)
    resource_id = models.CharField(max_length=120, blank=True)
    outcome = models.CharField(max_length=24, default="success")
    request_id = models.CharField(max_length=120, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "created_at"]), models.Index(fields=["actor", "created_at"])]

    def __str__(self):
        return f"{self.action} ({self.outcome})"
