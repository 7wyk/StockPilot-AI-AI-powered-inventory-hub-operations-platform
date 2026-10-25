import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import UserProfile
from apps.organizations.models import Membership, Organization

User = get_user_model()


@pytest.mark.django_db
def test_organization_list_only_returns_authenticated_users_memberships():
    first = User.objects.create_user(username="first@example.com", email="first@example.com", password="SafePassw0rd!")
    second = User.objects.create_user(username="second@example.com", email="second@example.com", password="SafePassw0rd!")
    first_org = Organization.objects.create(name="First Org", slug="first-org")
    second_org = Organization.objects.create(name="Second Org", slug="second-org")
    Membership.objects.create(user=first, organization=first_org, role=Membership.Role.OWNER)
    Membership.objects.create(user=second, organization=second_org, role=Membership.Role.OWNER)
    UserProfile.objects.create(user=first, active_organization=first_org)
    UserProfile.objects.create(user=second, active_organization=second_org)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(first)}")
    response = client.get(reverse("organization-list"))

    assert response.status_code == 200
    payload = response.data["results"] if isinstance(response.data, dict) else response.data
    assert [item["slug"] for item in payload] == ["first-org"]
