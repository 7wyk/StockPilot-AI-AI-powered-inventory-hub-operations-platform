from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar_path = models.CharField(max_length=512, blank=True)
    job_title = models.CharField(max_length=120, blank=True)
    preferred_timezone = models.CharField(max_length=64, default="UTC")
    response_style = models.CharField(max_length=32, default="concise")
    active_organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="active_profiles"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.get_username()}"
