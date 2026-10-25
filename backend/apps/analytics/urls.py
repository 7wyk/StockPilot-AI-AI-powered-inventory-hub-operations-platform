from django.urls import path

from . import views

urlpatterns = [
    path("analytics/overview/", views.AnalyticsOverviewView.as_view(), name="analytics-overview"),
    path("analytics/movements/", views.AnalyticsMovementsView.as_view(), name="analytics-movements"),
    path("analytics/hubs/", views.AnalyticsHubsView.as_view(), name="analytics-hubs"),
    path("analytics/stock-health/", views.AnalyticsStockHealthView.as_view(), name="analytics-stock-health"),
    path("analytics/low-stock/", views.AnalyticsLowStockView.as_view(), name="analytics-low-stock"),
    path("analytics/restock-recommendations/", views.AnalyticsRestockView.as_view(), name="analytics-restock-recommendations"),
    path("reports/", views.ReportListView.as_view(), name="report-list"),
    path("reports/generate/", views.ReportGenerateView.as_view(), name="report-generate"),
]
