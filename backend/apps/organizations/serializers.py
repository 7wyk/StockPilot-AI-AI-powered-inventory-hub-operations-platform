from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Membership, Organization, OrganizationInvite
from .permissions import ROLE_PERMISSIONS

User = get_user_model()


class OrganizationSummarySerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "timezone", "currency", "role"]

    def get_role(self, obj):
        user = self.context["request"].user
        return Membership.objects.filter(user=user, organization=obj, is_active=True).values_list("role", flat=True).first()


class MemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user_id", "email", "first_name", "last_name", "role", "role_label", "is_active", "joined_at", "last_seen_at"]
        read_only_fields = ["id", "user_id", "email", "first_name", "last_name", "role_label", "joined_at", "last_seen_at"]

    def validate_role(self, value):
        if value == Membership.Role.OWNER:
            raise serializers.ValidationError("Owner transfer is not available through member administration.")
        return value


class InvitationSerializer(serializers.ModelSerializer):
    invited_by_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = OrganizationInvite
        fields = ["id", "email", "role", "role_label", "status", "expires_at", "accepted_at", "created_at", "invited_by_name"]
        read_only_fields = fields

    def get_invited_by_name(self, obj):
        return obj.invited_by.get_full_name() or obj.invited_by.email

    def get_status(self, obj):
        if obj.accepted_at:
            return "accepted"
        if obj.canceled_at:
            return "canceled"
        if obj.expires_at <= timezone.now():
            return "expired"
        return "pending"


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Membership.Role.choices, default=Membership.Role.VIEWER)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_role(self, value):
        if value == Membership.Role.OWNER:
            raise serializers.ValidationError("Owner invitations are not supported; assign a member role instead.")
        return value


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=32, max_length=128, write_only=True)


class PermissionMatrixSerializer(serializers.Serializer):
    role = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())


def permission_matrix():
    return [{"role": role, "permissions": sorted(permissions)} for role, permissions in ROLE_PERMISSIONS.items()]
