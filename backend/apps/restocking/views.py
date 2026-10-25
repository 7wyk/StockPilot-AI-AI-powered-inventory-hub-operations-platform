from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.organizations.permissions import CanEditInventory, CanOperateHub, HasOrganizationMembership, get_active_membership

from .models import RestockRequest
from .serializers import RestockRequestSerializer
from .services import RestockStateError, transition_restock


class RestockRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RestockRequestSerializer
    permission_classes = [HasOrganizationMembership]

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
        if self.action in {"approve", "order"}:
            return [CanEditInventory()]
        return [CanOperateHub() if self.action in {"create", "submit", "receive"} else HasOrganizationMembership()]

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
