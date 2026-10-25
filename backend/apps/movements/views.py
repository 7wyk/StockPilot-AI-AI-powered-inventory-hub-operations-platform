from rest_framework import viewsets

from apps.organizations.permissions import OrganizationPermission, get_active_membership, organization_permission_class

from .models import StockMovement
from .serializers import StockMovementSerializer


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [organization_permission_class(OrganizationPermission.VIEW_MOVEMENTS)]

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return StockMovement.objects.filter(organization=membership.organization).select_related("product", "hub", "actor") if membership else StockMovement.objects.none()
