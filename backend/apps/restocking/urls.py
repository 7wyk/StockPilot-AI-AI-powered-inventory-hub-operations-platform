from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RestockRequestViewSet

router = DefaultRouter()
router.register("restock-requests", RestockRequestViewSet, basename="restock-request")

urlpatterns = [path("", include(router.urls))]
