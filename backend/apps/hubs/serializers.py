from rest_framework import serializers

from .models import Hub


class HubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hub
        fields = ["id", "name", "code", "address", "city", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        return value.strip().upper()
