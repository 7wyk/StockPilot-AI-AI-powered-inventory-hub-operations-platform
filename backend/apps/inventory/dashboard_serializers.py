from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    active_products = serializers.IntegerField()
    stock_units = serializers.DecimalField(max_digits=18, decimal_places=2)
    inventory_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    low_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    active_hubs = serializers.IntegerField()
    data_status = serializers.ChoiceField(choices=["empty", "live"])
