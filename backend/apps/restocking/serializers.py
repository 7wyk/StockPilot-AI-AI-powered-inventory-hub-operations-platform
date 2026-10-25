from rest_framework import serializers

from .models import RestockRequest


class RestockRequestSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    hub_name = serializers.CharField(source="hub.name", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = RestockRequest
        fields = [
            "id", "product", "product_name", "supplier", "supplier_name", "hub", "hub_name", "requested_by",
            "approved_by", "quantity", "status", "notes", "external_reference", "created_at", "updated_at", "received_at",
        ]
        read_only_fields = ["id", "requested_by", "approved_by", "status", "created_at", "updated_at", "received_at"]
