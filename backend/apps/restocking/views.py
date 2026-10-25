from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.organizations.permissions import OrganizationPermission, get_active_membership, organization_permission_class

from .models import RestockRequest
from .serializers import RestockRequestSerializer
from .services import RestockStateError, transition_restock


class RestockRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RestockRequestSerializer
    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return RestockRequest.objects.filter(organization=membership.organization).select_related("product", "supplier", "hub", "requested_by", "approved_by") if membership else RestockRequest.objects.none()

    def perform_create(self, serializer):
        membership = get_active_membership(self.request.user)
        data = serializer.validated_data
        if data["product"].organization_id != membership.organization_id or data["hub"].organization_id != membership.organization_id:
            raise serializers.ValidationError("Product and hub must belong to the active organization.")
        if data.get("supplier") and data["supplier"].organization_id != membership.organization_id:
            raise serializers.ValidationError("Supplier must belong to the active organization.")
        serializer.save(organization=membership.organization, requested_by=self.request.user)

    def get_permissions(self):
        permissions_by_action = {
            "list": OrganizationPermission.VIEW_RESTOCK,
            "retrieve": OrganizationPermission.VIEW_RESTOCK,
            "create": OrganizationPermission.CREATE_RESTOCK,
            "submit": OrganizationPermission.CREATE_RESTOCK,
            "approve": OrganizationPermission.APPROVE_RESTOCK,
            "order": OrganizationPermission.APPROVE_RESTOCK,
            "receive": OrganizationPermission.ADJUST_STOCK,
            "cancel": OrganizationPermission.CREATE_RESTOCK,
            "update": OrganizationPermission.CREATE_RESTOCK,
            "partial_update": OrganizationPermission.CREATE_RESTOCK,
            "destroy": OrganizationPermission.CREATE_RESTOCK,
        }
        return [organization_permission_class(permissions_by_action.get(self.action, OrganizationPermission.VIEW_RESTOCK))()]

    def _transition(self, request, pk, action):
        try:
            item = transition_restock(request_id=pk, actor=request.user, action=action)
        except RestockRequest.DoesNotExist:
            return Response({"detail": "Restock request not found."}, status=status.HTTP_404_NOT_FOUND)
        except RestockStateError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(item).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self._transition(request, pk, "submit")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._transition(request, pk, "approve")

    @action(detail=True, methods=["post"])
    def order(self, request, pk=None):
        return self._transition(request, pk, "order")

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        return self._transition(request, pk, "receive")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(request, pk, "cancel")
