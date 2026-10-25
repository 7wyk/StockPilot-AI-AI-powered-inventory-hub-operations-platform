"""
Analytics API views.

All views use the authenticated user's active organization — never a
client-supplied organization ID — as the tenant boundary.
"""

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.permissions import (
    OrganizationPermission,
    get_active_membership,
    organization_permission_class,
)

from . import services
from .exports import generate_csv, generate_pdf, report_data_to_table
from .models import Report
from .serializers import ReportGenerateSerializer, ReportSerializer


class AnalyticsOverviewView(APIView):
    """GET /api/v1/analytics/overview/ — top-level KPIs."""
    permission_classes = [organization_permission_class(OrganizationPermission.VIEW_REPORTS)]

    def get(self, request):
        org = get_active_membership(request.user).organization
        return Response(services.get_overview(org))


class AnalyticsMovementsView(APIView):
    """GET /api/v1/analytics/movements/ — movement trends."""
    permission_classes = [organization_permission_class(OrganizationPermission.VIEW_REPORTS)]

    def get(self, request):
        org = get_active_membership(request.user).organization
        days = min(int(request.query_params.get("days", 30)), 365)
        return Response(services.get_movement_trends(org, days=days))


class AnalyticsHubsView(APIView):
    """GET /api/v1/analytics/hubs/ — inventory by hub."""
    permission_classes = [organization_permission_class(OrganizationPermission.VIEW_REPORTS)]

    def get(self, request):
        org = get_active_membership(request.user).organization
        return Response(services.get_hub_analytics(org))


class AnalyticsStockHealthView(APIView):
    """GET /api/v1/analytics/stock-health/ — stock health breakdown."""
    permission_classes = [organization_permission_class(OrganizationPermission.VIEW_REPORTS)]

    def get(self, request):
        org = get_active_membership(request.user).organization
        lookback = min(int(request.query_params.get("lookback_days", 30)), 365)
        return Response(services.get_stock_health(org, lookback_days=lookback))


class AnalyticsLowStockView(APIView):
    """GET /api/v1/analytics/low-stock/ — low stock products."""
    permission_classes = [organization_permission_class(OrganizationPermission.VIEW_REPORTS)]

    def get(self, request):
        org = get_active_membership(request.user).organization
        hub_id = request.query_params.get("hub_id")
        category_id = request.query_params.get("category_id")
        return Response(services.get_low_stock_products(
            org,
            hub_id=int(hub_id) if hub_id else None,
            category_id=int(category_id) if category_id else None,
        ))


class AnalyticsRestockView(APIView):
    """GET /api/v1/analytics/restock-recommendations/ — restock recommendations."""
    permission_classes = [organization_permission_class(OrganizationPermission.VIEW_REPORTS)]

    def get(self, request):
        org = get_active_membership(request.user).organization
        return Response(services.get_restock_recommendations(org))


class ReportListView(APIView):
    """GET /api/v1/reports/ — list generated reports for the organization."""
    permission_classes = [organization_permission_class(OrganizationPermission.VIEW_REPORTS)]

    def get(self, request):
        org = get_active_membership(request.user).organization
        reports = Report.objects.filter(organization=org).order_by("-created_at")[:50]
        return Response(ReportSerializer(reports, many=True).data)


class ReportGenerateView(APIView):
    """
    POST /api/v1/reports/generate/ — generate and download a report.

    For CSV/PDF reports, this generates the file synchronously and returns
    it directly as a download. The report record is also persisted.
    """
    permission_classes = [organization_permission_class(OrganizationPermission.GENERATE_REPORTS)]

    def post(self, request):
        serializer = ReportGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = get_active_membership(request.user)
        org = membership.organization
        report_type = serializer.validated_data["report_type"]
        fmt = serializer.validated_data["format"]
        filters = serializer.validated_data.get("filters", {})

        # Create report record
        report = Report.objects.create(
            organization=org,
            requested_by=request.user,
            report_type=report_type,
            format=fmt,
            filters=filters,
            status=Report.Status.PROCESSING,
        )

        try:
            data = self._get_report_data(org, report_type, filters)
            headers, rows = report_data_to_table(report_type, data)
            summary = self._get_summary(report_type, data)
            title = Report.ReportType(report_type).label
            period = filters.get("period", "Last 30 days")
            filters_text = ", ".join(f"{k}: {v}" for k, v in filters.items() if k != "period")

            if fmt == "csv":
                content = generate_csv(title=title, headers=headers, rows=rows)
                content_type = "text/csv"
                extension = "csv"
            else:
                content = generate_pdf(
                    title=title,
                    organization_name=org.name,
                    report_type=title,
                    period=period,
                    filters_text=filters_text,
                    summary=summary,
                    headers=headers,
                    rows=rows,
                )
                content_type = "application/pdf"
                extension = "pdf"

            report.status = Report.Status.COMPLETED
            report.completed_at = timezone.now()
            report.save(update_fields=["status", "completed_at"])

            filename = f"stockpilot_{report_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
            response = HttpResponse(content, content_type=content_type)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        except Exception as exc:
            report.status = Report.Status.FAILED
            report.error = str(exc)
            report.save(update_fields=["status", "error"])
            return Response(
                {"detail": f"Report generation failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_report_data(self, org, report_type, filters):
        """Dispatch to the appropriate analytics service."""
        days = int(filters.get("days", 30))
        hub_id = filters.get("hub_id")
        category_id = filters.get("category_id")

        if report_type == "inventory_health":
            return services.get_stock_health(org, lookback_days=days)
        elif report_type == "low_stock":
            return services.get_low_stock_products(
                org,
                hub_id=int(hub_id) if hub_id else None,
                category_id=int(category_id) if category_id else None,
            )
        elif report_type == "stockout":
            return services.get_stock_health(org, lookback_days=days)
        elif report_type == "inventory_valuation":
            return services.get_inventory_valuation(
                org,
                hub_id=int(hub_id) if hub_id else None,
                category_id=int(category_id) if category_id else None,
            )
        elif report_type == "slow_moving":
            return services.get_stock_health(org, lookback_days=days)
        elif report_type == "hub_performance":
            return services.get_hub_analytics(org)
        elif report_type == "stock_movements":
            return services.get_movement_report(
                org, days=days,
                hub_id=int(hub_id) if hub_id else None,
                product_id=int(filters.get("product_id")) if filters.get("product_id") else None,
                movement_type=filters.get("movement_type"),
            )
        elif report_type == "transfers":
            return services.get_transfer_report(
                org, days=days,
                status=filters.get("status"),
            )
        elif report_type == "restocking":
            return services.get_restock_report(
                org, days=days,
                status=filters.get("status"),
            )
        return {}

    def _get_summary(self, report_type, data):
        """Extract summary dict from analytics data for PDF header."""
        if report_type in ("inventory_health", "stockout", "slow_moving"):
            return data.get("summary", {})
        if report_type == "inventory_valuation":
            return {
                "total_value": data.get("total_value", "0"),
                "total_units": data.get("total_units", "0"),
                "line_count": data.get("line_count", 0),
            }
        if isinstance(data, list):
            return {"total_records": len(data)}
        return {}
