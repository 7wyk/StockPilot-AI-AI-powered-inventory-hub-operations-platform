from rest_framework import serializers

from .models import StockMovement


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    hub_name = serializers.CharField(source="hub.name", read_only=True)
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_name", "sku", "hub", "hub_name", "actor_name", "movement_type",
            "quantity_delta", "quantity_before", "quantity_after", "reason", "reference_type", "reference_id", "created_at",
        ]

    def get_actor_name(self, obj):
        return obj.actor.get_full_name() or obj.actor.email if obj.actor else None
