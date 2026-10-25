from rest_framework import serializers

from .models import Membership, Organization


class OrganizationSummarySerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "timezone", "currency", "role"]

    def get_role(self, obj):
        user = self.context["request"].user
        return Membership.objects.filter(user=user, organization=obj, is_active=True).values_list("role", flat=True).first()
