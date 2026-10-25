from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class AuthenticationRateThrottle(SimpleRateThrottle):
    scope = "authentication"

    def get_rate(self):
        return getattr(settings, "AUTH_RATE_LIMIT", "10/minute")

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class SensitiveEndpointRateThrottle(SimpleRateThrottle):
    scope = "sensitive"

    def get_rate(self):
        return getattr(settings, "SENSITIVE_RATE_LIMIT", "60/minute")

    def get_cache_key(self, request, view):
        user_part = str(request.user.pk) if getattr(request.user, "is_authenticated", False) else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": user_part}
