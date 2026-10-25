from rest_framework import viewsets

from apps.organizations.permissions import OrganizationPermission, get_active_membership, organization_permission_class

from .models import Hub
from .serializers import HubSerializer


class HubViewSet(viewsets.ModelViewSet):
    serializer_class = HubSerializer

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return Hub.objects.filter(organization=membership.organization) if membership else Hub.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=get_active_membership(self.request.user).organization)

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [organization_permission_class(OrganizationPermission.VIEW_HUB_INVENTORY)()]
        return [organization_permission_class(OrganizationPermission.MANAGE_HUBS)()]
