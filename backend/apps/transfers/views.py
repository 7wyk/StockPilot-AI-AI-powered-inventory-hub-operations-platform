from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.organizations.permissions import CanEditInventory, CanOperateHub, HasOrganizationMembership, get_active_membership

from .models import Transfer
from .serializers import TransferSerializer
from .services import TransferStateError, transition_transfer


class TransferViewSet(viewsets.ModelViewSet):
    serializer_class = TransferSerializer
    permission_classes = [HasOrganizationMembership]

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return Transfer.objects.filter(organization=membership.organization).select_related("product", "source_hub", "destination_hub", "requested_by", "approved_by", "dispatched_by", "received_by") if membership else Transfer.objects.none()

    def perform_create(self, serializer):
        membership = get_active_membership(self.request.user)
        data = serializer.validated_data
        if data["product"].organization_id != membership.organization_id or data["source_hub"].organization_id != membership.organization_id or data["destination_hub"].organization_id != membership.organization_id:
            raise serializers.ValidationError("Product and hubs must belong to the active organization.")
        if data["source_hub"].id == data["destination_hub"].id:
            raise serializers.ValidationError({"destination_hub": "Source and destination hubs must be different."})
        serializer.save(organization=membership.organization, requested_by=self.request.user)

    def get_permissions(self):
        if self.action in {"approve"}:
            return [CanEditInventory()]
        return [CanOperateHub() if self.action in {"create", "submit", "dispatch_transfer", "receive"} else HasOrganizationMembership()]

    def _transition(self, request, pk, action):
        try:
            item = transition_transfer(transfer_id=pk, actor=request.user, action=action)
        except Transfer.DoesNotExist:
            return Response({"detail": "Transfer not found."}, status=status.HTTP_404_NOT_FOUND)
        except (TransferStateError, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(item).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self._transition(request, pk, "submit")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._transition(request, pk, "approve")

    @action(detail=True, methods=["post"], url_path="dispatch", url_name="dispatch")
    def dispatch_transfer(self, request, pk=None):
        return self._transition(request, pk, "dispatch")

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        return self._transition(request, pk, "receive")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(request, pk, "cancel")
