from rest_framework import viewsets

from apps.organizations.permissions import OrganizationPermission, get_active_membership, organization_permission_class

from .models import Supplier
from .serializers import SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return Supplier.objects.filter(organization=membership.organization).prefetch_related("products") if membership else Supplier.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=get_active_membership(self.request.user).organization)

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [organization_permission_class(OrganizationPermission.VIEW_SUPPLIERS)()]
        return [organization_permission_class(OrganizationPermission.MANAGE_SUPPLIERS)()]
