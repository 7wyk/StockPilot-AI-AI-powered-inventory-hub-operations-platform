from django.urls import path

from .views import ActiveOrganizationView, OrganizationListView

urlpatterns = [
    path("organizations/", OrganizationListView.as_view(), name="organization-list"),
    path("organizations/active/", ActiveOrganizationView.as_view(), name="organization-active"),
]
