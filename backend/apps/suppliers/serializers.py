from rest_framework import serializers

from .models import Supplier, SupplierProduct


class SupplierProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierProduct
        fields = ["id", "product", "supplier_sku", "lead_time_days", "last_cost", "is_preferred"]
        read_only_fields = ["id"]


class SupplierSerializer(serializers.ModelSerializer):
    products = SupplierProductSerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = ["id", "name", "email", "phone", "website", "notes", "is_active", "products", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at", "products"]
