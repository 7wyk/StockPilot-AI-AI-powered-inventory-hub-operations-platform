import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserProfile
from apps.audit.services import record_audit

from .models import Membership, Organization, OrganizationInvite
from .permissions import (
    CanManageOrganization,
    HasOrganizationMembership,
    HasOrganizationPermission,
    OrganizationPermission,
    get_active_membership,
)
from .serializers import (
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    MemberSerializer,
    OrganizationSummarySerializer,
    PermissionMatrixSerializer,
    permission_matrix,
)

User = get_user_model()
INVITATION_TTL = timedelta(days=7)


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _request_id(request):
    return request.headers.get("X-Request-ID", "")[:128]


class OrganizationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationSummarySerializer

    def get_queryset(self):
        return Organization.objects.filter(memberships__user=self.request.user, memberships__is_active=True).distinct()


class ActiveOrganizationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        organization_id = request.data.get("organization_id")
        membership = Membership.objects.filter(user=request.user, organization_id=organization_id, is_active=True).select_related("organization").first()
        if not membership:
            return Response({"detail": "You do not have an active membership in that organization."}, status=status.HTTP_400_BAD_REQUEST)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.active_organization = membership.organization
        profile.save(update_fields=["active_organization", "updated_at"])
        record_audit(
            organization=membership.organization,
            actor=request.user,
            action="account.organization_switched",
            resource_type="organization",
            resource_id=membership.organization_id,
            metadata={"role": membership.role},
            request_id=_request_id(request),
        )
        return Response(OrganizationSummarySerializer(membership.organization, context={"request": request}).data)


class MemberListView(generics.ListAPIView):
    permission_classes = [HasOrganizationMembership]
    serializer_class = MemberSerializer

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return Membership.objects.filter(organization=membership.organization, is_active=True).select_related("user") if membership else Membership.objects.none()


class MemberDetailView(generics.UpdateAPIView, generics.DestroyAPIView):
    serializer_class = MemberSerializer
    http_method_names = ["patch", "delete", "head", "options"]

    def get_permissions(self):
        permission = OrganizationPermission.MANAGE_ROLES if self.request.method == "PATCH" else OrganizationPermission.MANAGE_MEMBERS
        permission_checker = type("MemberPermission", (HasOrganizationPermission,), {"required_permission": permission})
        return [permission_checker()]

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return Membership.objects.filter(organization=membership.organization, is_active=True).select_related("user") if membership else Membership.objects.none()

    def _authorize_target(self, target):
        actor = get_active_membership(self.request.user)
        if target.role == Membership.Role.OWNER:
            return Response({"detail": "The owner membership cannot be changed here."}, status=status.HTTP_403_FORBIDDEN)
        if target.user_id == self.request.user.id:
            return Response({"detail": "You cannot remove or change your own membership here."}, status=status.HTTP_400_BAD_REQUEST)
        if actor.role != Membership.Role.OWNER and target.role == Membership.Role.ADMIN:
            return Response({"detail": "Only the owner can manage an administrator."}, status=status.HTTP_403_FORBIDDEN)
        return None

    def patch(self, request, *args, **kwargs):
        target = self.get_object()
        denial = self._authorize_target(target)
        if denial:
            return denial
        serializer = self.get_serializer(target, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_role = target.role
        target = serializer.save()
        if old_role != target.role:
            record_audit(
                organization=target.organization,
                actor=request.user,
                action="organization.member_role_changed",
                resource_type="membership",
                resource_id=target.pk,
                metadata={"user_id": target.user_id, "from_role": old_role, "to_role": target.role},
                request_id=_request_id(request),
            )
        return Response(self.get_serializer(target).data)

    def delete(self, request, *args, **kwargs):
        self.required_permission = OrganizationPermission.MANAGE_MEMBERS
        target = self.get_object()
        denial = self._authorize_target(target)
        if denial:
            return denial
        target.is_active = False
        target.save(update_fields=["is_active"])
        record_audit(
            organization=target.organization,
            actor=request.user,
            action="organization.member_removed",
            resource_type="membership",
            resource_id=target.pk,
            metadata={"user_id": target.user_id, "email": target.user.email},
            request_id=_request_id(request),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationListCreateView(generics.ListCreateAPIView):
    permission_classes = [HasOrganizationPermission]
    serializer_class = InvitationSerializer
    required_permission = OrganizationPermission.MANAGE_MEMBERS

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        queryset = OrganizationInvite.objects.filter(organization=membership.organization).select_related("invited_by") if membership else OrganizationInvite.objects.none()
        requested_status = self.request.query_params.get("status", "")
        if requested_status == "pending":
            queryset = queryset.filter(accepted_at__isnull=True, canceled_at__isnull=True, expires_at__gt=timezone.now())
        elif requested_status == "accepted":
            queryset = queryset.filter(accepted_at__isnull=False)
        elif requested_status == "canceled":
            queryset = queryset.filter(canceled_at__isnull=False)
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor_membership = get_active_membership(request.user)
        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]
        if Membership.objects.filter(organization=actor_membership.organization, user__email__iexact=email, is_active=True).exists():
            return Response({"detail": "That user is already an active member of this organization."}, status=status.HTTP_400_BAD_REQUEST)

        token = secrets.token_urlsafe(32)
        now = timezone.now()
        invite = OrganizationInvite.objects.filter(organization=actor_membership.organization, email=email).first()
        if invite and invite.accepted_at and invite.accepted_at > now - timedelta(minutes=1):
            return Response({"detail": "That invitation was already accepted."}, status=status.HTTP_400_BAD_REQUEST)
        if invite:
            invite.role = role
            invite.token_hash = _token_hash(token)
            invite.invited_by = request.user
            invite.expires_at = now + INVITATION_TTL
            invite.accepted_at = None
            invite.canceled_at = None
            invite.save(update_fields=["role", "token_hash", "invited_by", "expires_at", "accepted_at", "canceled_at"])
        else:
            invite = OrganizationInvite.objects.create(
                organization=actor_membership.organization,
                email=email,
                role=role,
                token_hash=_token_hash(token),
                invited_by=request.user,
                expires_at=now + INVITATION_TTL,
            )
        record_audit(
            organization=actor_membership.organization,
            actor=request.user,
            action="organization.invitation_created",
            resource_type="invitation",
            resource_id=invite.pk,
            metadata={"email": email, "role": role},
            request_id=_request_id(request),
        )
        response = InvitationSerializer(invite).data
        response["invitation_token"] = token
        return Response(response, status=status.HTTP_201_CREATED)


class InvitationDetailView(APIView):
    permission_classes = [HasOrganizationPermission]
    required_permission = OrganizationPermission.MANAGE_MEMBERS

    def get_object(self, request, pk):
        membership = get_active_membership(request.user)
        return OrganizationInvite.objects.filter(pk=pk, organization=membership.organization).select_related("invited_by").first() if membership else None

    def post(self, request, pk, action):
        invite = self.get_object(request, pk)
        if not invite:
            return Response({"detail": "Invitation not found."}, status=status.HTTP_404_NOT_FOUND)
        if invite.accepted_at:
            return Response({"detail": "An accepted invitation cannot be changed."}, status=status.HTTP_400_BAD_REQUEST)
        if action == "cancel":
            if invite.canceled_at:
                return Response(InvitationSerializer(invite).data)
            invite.canceled_at = timezone.now()
            invite.save(update_fields=["canceled_at"])
            record_audit(organization=invite.organization, actor=request.user, action="organization.invitation_canceled", resource_type="invitation", resource_id=invite.pk, request_id=_request_id(request))
            return Response(InvitationSerializer(invite).data)
        if action == "resend":
            token = secrets.token_urlsafe(32)
            invite.token_hash = _token_hash(token)
            invite.expires_at = timezone.now() + INVITATION_TTL
            invite.canceled_at = None
            invite.save(update_fields=["token_hash", "expires_at", "canceled_at"])
            record_audit(organization=invite.organization, actor=request.user, action="organization.invitation_resent", resource_type="invitation", resource_id=invite.pk, request_id=_request_id(request))
            response = InvitationSerializer(invite).data
            response["invitation_token"] = token
            return Response(response)
        return Response({"detail": "Unsupported invitation action."}, status=status.HTTP_400_BAD_REQUEST)


class InvitationAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite = OrganizationInvite.objects.select_for_update().select_related("organization").filter(token_hash=_token_hash(serializer.validated_data["token"])).first()
        if not invite:
            return Response({"detail": "Invitation token is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        if invite.accepted_at or invite.canceled_at or invite.expires_at <= timezone.now():
            return Response({"detail": "This invitation is no longer active."}, status=status.HTTP_400_BAD_REQUEST)
        if invite.email.lower() != request.user.email.lower():
            return Response({"detail": "Sign in with the invited email address to accept this invitation."}, status=status.HTTP_403_FORBIDDEN)
        membership, created = Membership.objects.get_or_create(user=request.user, organization=invite.organization, defaults={"role": invite.role, "is_active": True})
        if not created:
            if membership.is_active:
                return Response({"detail": "You are already an active member of this organization."}, status=status.HTTP_400_BAD_REQUEST)
            membership.role = invite.role
            membership.is_active = True
            membership.save(update_fields=["role", "is_active"])
        invite.accepted_at = timezone.now()
        invite.save(update_fields=["accepted_at"])
        record_audit(organization=invite.organization, actor=request.user, action="organization.invitation_accepted", resource_type="invitation", resource_id=invite.pk, metadata={"role": invite.role}, request_id=_request_id(request))
        return Response(MemberSerializer(membership).data, status=status.HTTP_200_OK)


class PermissionMatrixView(APIView):
    permission_classes = [HasOrganizationMembership]

    def get(self, request):
        serializer = PermissionMatrixSerializer(permission_matrix(), many=True)
        return Response(serializer.data)
