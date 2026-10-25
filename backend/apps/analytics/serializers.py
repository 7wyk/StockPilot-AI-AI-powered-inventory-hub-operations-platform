from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    requested_by_email = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id", "report_type", "format", "status", "filters",
            "storage_path", "error", "created_at", "completed_at",
            "requested_by_email",
        ]
        read_only_fields = fields

    def get_requested_by_email(self, obj):
        return obj.requested_by.email if obj.requested_by else None


class ReportGenerateSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=Report.ReportType.choices)
    format = serializers.ChoiceField(choices=Report.Format.choices, default="csv")
    filters = serializers.DictField(required=False, default=dict)
