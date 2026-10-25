from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.hubs.views import HubViewSet
from apps.movements.views import StockMovementViewSet
from apps.suppliers.views import SupplierViewSet

from .views import CategoryViewSet, DashboardSummaryView, ProductStockView, ProductViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("hubs", HubViewSet, basename="hub")
router.register("suppliers", SupplierViewSet, basename="supplier")
router.register("movements", StockMovementViewSet, basename="movement")

urlpatterns = [
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("products/<int:pk>/stock/", ProductStockView.as_view(), name="product-stock"),
    path("", include(router.urls)),
]
