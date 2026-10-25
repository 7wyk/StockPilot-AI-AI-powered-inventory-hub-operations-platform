from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Persistent AI conversation scoped to organization + user."""
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="ai_conversations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_conversations",
    )
    title = models.CharField(max_length=200, default="New conversation")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["organization", "user", "-updated_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.user})"


class Message(models.Model):
    """Individual message in a conversation."""
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"
        TOOL = "tool", "Tool"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    tool_calls = models.JSONField(default=list, blank=True)
    tool_results = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:80]}"


class UserPreference(models.Model):
    """
    Long-term user preferences scoped to organization + user.
    Only stores operational preferences, not personal information.
    """
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="ai_preferences",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_preferences",
    )
    key = models.CharField(max_length=64)
    value = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user", "key"],
                name="unique_ai_preference_per_user_org",
            ),
        ]

    # Allowed preference keys — prevents creepy unrestricted memory
    ALLOWED_KEYS = frozenset({
        "preferred_hub",
        "preferred_report_format",
        "preferred_dashboard_view",
        "preferred_currency_display",
        "default_lookback_days",
    })

    def __str__(self):
        return f"{self.key}: {self.value}"
