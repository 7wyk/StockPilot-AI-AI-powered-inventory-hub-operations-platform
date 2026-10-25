from rest_framework import serializers

from apps.hubs.models import Hub
from apps.movements.models import StockMovement

from .models import Category, InventoryBalance, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class InventoryBalanceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    hub_name = serializers.CharField(source="hub.name", read_only=True)
    available = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = InventoryBalance
        fields = ["id", "product", "product_name", "sku", "hub", "hub_name", "on_hand", "reserved", "available", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    balances = InventoryBalanceSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "sku", "description", "category", "category_name", "unit_of_measure", "image_path",
            "cost_price", "selling_price", "reorder_threshold", "target_stock_level", "is_active", "balances",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "balances"]

    def validate_sku(self, value):
        return value.strip().upper()


class StockMutationSerializer(serializers.Serializer):
    hub_id = serializers.PrimaryKeyRelatedField(queryset=Hub.objects.all(), source="hub")
    movement_type = serializers.ChoiceField(choices=[
        StockMovement.MovementType.RECEIPT,
        StockMovement.MovementType.ISSUE,
        StockMovement.MovementType.ADJUSTMENT,
    ])
    quantity = serializers.DecimalField(max_digits=14, decimal_places=2)
    reason = serializers.CharField(max_length=240, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=160, required=False, allow_blank=False)
