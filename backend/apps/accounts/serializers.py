from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.audit.models import AuditLog
from apps.organizations.models import Membership, Organization

from .models import UserProfile

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    organization_name = serializers.CharField(max_length=160)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        organization_name = validated_data.pop("organization_name")
        email = validated_data["email"]
        user_fields = {key: value for key, value in validated_data.items() if key != "email"}
        user = User.objects.create_user(username=email, email=email, **user_fields)
        organization = Organization.objects.create(name=organization_name)
        Membership.objects.create(user=user, organization=organization, role=Membership.Role.OWNER)
        UserProfile.objects.create(user=user, active_organization=organization)
        AuditLog.objects.create(
            organization=organization,
            actor=user,
            action="account.organization_created",
            resource_type="organization",
            resource_id=str(organization.pk),
            metadata={"email": email},
        )
        return user


class MembershipSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    organization_slug = serializers.CharField(source="organization.slug", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "organization", "organization_name", "organization_slug", "role", "is_active", "joined_at"]


class UserIdentitySerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)
    active_organization = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "memberships", "active_organization"]

    def get_active_organization(self, obj):
        profile = getattr(obj, "profile", None)
        organization = getattr(profile, "active_organization", None)
        if not organization:
            return None
        return {"id": organization.id, "name": organization.name, "slug": organization.slug}


class StockPilotTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.CharField(required=False, write_only=True)
    email = serializers.EmailField(required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].required = False
        self.fields["email"] = serializers.EmailField(required=False, write_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = user.id
        return token

    def validate(self, attrs):
        if attrs.get("email") and not attrs.get("username"):
            attrs["username"] = attrs["email"].strip().lower()
        if not attrs.get("username"):
            raise serializers.ValidationError({"email": "Email is required."})
        data = super().validate(attrs)
        data["user"] = UserIdentitySerializer(self.user).data
        return data
