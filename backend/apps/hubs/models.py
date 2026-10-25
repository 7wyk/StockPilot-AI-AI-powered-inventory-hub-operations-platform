from django.db import models


class Hub(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, related_name="hubs")
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=32)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["organization", "code"], name="unique_hub_code_per_organization")]
        indexes = [models.Index(fields=["organization", "is_active", "name"])]

    def __str__(self):
        return f"{self.name} ({self.code})"
