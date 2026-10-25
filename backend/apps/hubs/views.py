from rest_framework import permissions, viewsets

from apps.organizations.permissions import CanEditInventory, HasOrganizationMembership, get_active_membership

from .models import Hub
from .serializers import HubSerializer


class HubViewSet(viewsets.ModelViewSet):
    serializer_class = HubSerializer
    permission_classes = [HasOrganizationMembership]

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return Hub.objects.filter(organization=membership.organization) if membership else Hub.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=get_active_membership(self.request.user).organization)

    def get_permissions(self):
        return [CanEditInventory() if self.request.method not in permissions.SAFE_METHODS else HasOrganizationMembership()]
