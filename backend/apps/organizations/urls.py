from django.urls import path

from .views import (
    ActiveOrganizationView,
    InvitationAcceptView,
    InvitationDetailView,
    InvitationListCreateView,
    MemberDetailView,
    MemberListView,
    OrganizationListView,
    PermissionMatrixView,
)

urlpatterns = [
    path("organizations/", OrganizationListView.as_view(), name="organization-list"),
    path("organizations/active/", ActiveOrganizationView.as_view(), name="organization-active"),
    path("organizations/members/", MemberListView.as_view(), name="organization-members"),
    path("organizations/members/<int:pk>/", MemberDetailView.as_view(), name="organization-member-detail"),
    path("organizations/invitations/", InvitationListCreateView.as_view(), name="organization-invitations"),
    path("organizations/invitations/<int:pk>/<str:action>/", InvitationDetailView.as_view(), name="organization-invitation-action"),
    path("organizations/invitations/accept/", InvitationAcceptView.as_view(), name="organization-invitation-accept"),
    path("organizations/permissions/", PermissionMatrixView.as_view(), name="organization-permissions"),
]
