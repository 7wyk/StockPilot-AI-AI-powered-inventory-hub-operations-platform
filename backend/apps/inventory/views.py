from decimal import Decimal

from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.hubs.models import Hub
from apps.organizations.permissions import CanEditInventory, CanOperateHub, HasOrganizationMembership, get_active_membership

from .dashboard_serializers import DashboardSummarySerializer
from .models import Category, InventoryBalance, Product
from .serializers import CategorySerializer, ProductSerializer, StockMutationSerializer
from .services import InventoryOperationError, change_stock


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [HasOrganizationMembership]

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        return Category.objects.filter(organization=membership.organization) if membership else Category.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=get_active_membership(self.request.user).organization)

    def get_permissions(self):
        return [CanEditInventory() if self.request.method not in permissions.SAFE_METHODS else HasOrganizationMembership()]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [HasOrganizationMembership]

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        queryset = Product.objects.filter(organization=membership.organization).select_related("category").prefetch_related("balances__hub") if membership else Product.objects.none()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(sku__icontains=search)
        return queryset.distinct()

    def perform_create(self, serializer):
        membership = get_active_membership(self.request.user)
        category = serializer.validated_data.get("category")
        if category and category.organization_id != membership.organization_id:
            raise serializers.ValidationError({"category": "Category is outside the active organization."})
        serializer.save(organization=membership.organization)

    def get_permissions(self):
        return [CanEditInventory() if self.request.method not in permissions.SAFE_METHODS else HasOrganizationMembership()]


class ProductStockView(APIView):
    permission_classes = [CanOperateHub]

    def post(self, request, pk):
        membership = get_active_membership(request.user)
        product = Product.objects.filter(pk=pk, organization=membership.organization, is_active=True).first()
        if not product:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = StockMutationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hub = serializer.validated_data["hub"]
        if hub.organization_id != membership.organization_id:
            return Response({"detail": "Hub is outside the active organization."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = change_stock(
                organization=membership.organization,
                product=product,
                hub=hub,
                actor=request.user,
                movement_type=serializer.validated_data["movement_type"],
                quantity=serializer.validated_data["quantity"],
                reason=serializer.validated_data.get("reason", ""),
                idempotency_key=serializer.validated_data.get("idempotency_key"),
            )
        except InventoryOperationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"movement_id": result.movement.id, "on_hand": result.balance.on_hand, "available": result.balance.available}, status=status.HTTP_201_CREATED)


class DashboardSummaryView(APIView):
    permission_classes = [HasOrganizationMembership]

    def get(self, request):
        organization = get_active_membership(request.user).organization
        products = Product.objects.filter(organization=organization, is_active=True).annotate(
            total_on_hand=Coalesce(Sum("balances__on_hand"), Value(Decimal("0")))
        )
        balances = InventoryBalance.objects.filter(organization=organization).select_related("product")
        stock_units = balances.aggregate(total=Coalesce(Sum("on_hand"), Value(Decimal("0")))).get("total") or Decimal("0")
        inventory_value = sum((balance.product.cost_price * balance.on_hand for balance in balances), Decimal("0"))
        payload = {
            "active_products": products.count(),
            "stock_units": stock_units,
            "inventory_value": inventory_value,
            "low_stock_products": products.filter(total_on_hand__gt=0, total_on_hand__lte=F("reorder_threshold")).count(),
            "out_of_stock_products": products.filter(total_on_hand=0).count(),
            "active_hubs": Hub.objects.filter(organization=organization, is_active=True).count(),
            "data_status": "live" if products.exists() else "empty",
        }
        return Response(DashboardSummarySerializer(payload).data)
