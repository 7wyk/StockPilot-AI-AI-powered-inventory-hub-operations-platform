from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserProfile
from apps.audit.services import record_audit

from .models import Membership, Organization
from .serializers import OrganizationSummarySerializer


class OrganizationListView(ListAPIView):
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
        )
        return Response(OrganizationSummarySerializer(membership.organization, context={"request": request}).data)
