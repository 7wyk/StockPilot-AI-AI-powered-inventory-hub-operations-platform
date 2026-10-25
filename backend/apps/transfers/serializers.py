from rest_framework import serializers

from .models import Transfer


class TransferSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    source_hub_name = serializers.CharField(source="source_hub.name", read_only=True)
    destination_hub_name = serializers.CharField(source="destination_hub.name", read_only=True)

    class Meta:
        model = Transfer
        fields = [
            "id", "product", "product_name", "source_hub", "source_hub_name", "destination_hub", "destination_hub_name",
            "requested_by", "approved_by", "dispatched_by", "received_by", "quantity", "status", "notes",
            "created_at", "updated_at", "dispatched_at", "received_at",
        ]
        read_only_fields = ["id", "requested_by", "approved_by", "dispatched_by", "received_by", "status", "created_at", "updated_at", "dispatched_at", "received_at"]
