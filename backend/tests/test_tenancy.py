import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import UserProfile
from apps.organizations.models import Membership, Organization

User = get_user_model()


def auth_client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


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

    response = auth_client(first).get(reverse("organization-list"))

    assert response.status_code == 200
    payload = response.data["results"] if isinstance(response.data, dict) else response.data
    assert [item["slug"] for item in payload] == ["first-org"]


@pytest.mark.django_db
def test_member_can_switch_active_organization_but_not_to_a_foreign_org():
    user = User.objects.create_user(username="switcher@example.com", email="switcher@example.com", password="SafePassw0rd!")
    first_org = Organization.objects.create(name="First Org", slug="switch-first")
    second_org = Organization.objects.create(name="Second Org", slug="switch-second")
    foreign_org = Organization.objects.create(name="Foreign Org", slug="switch-foreign")
    Membership.objects.create(user=user, organization=first_org, role=Membership.Role.OWNER)
    Membership.objects.create(user=user, organization=second_org, role=Membership.Role.ANALYST)
    UserProfile.objects.create(user=user, active_organization=first_org)
    other = User.objects.create_user(username="other@example.com", email="other@example.com", password="SafePassw0rd!")
    Membership.objects.create(user=other, organization=foreign_org, role=Membership.Role.OWNER)

    client = auth_client(user)
    switched = client.post(reverse("organization-active"), {"organization_id": second_org.pk}, format="json")
    rejected = client.post(reverse("organization-active"), {"organization_id": foreign_org.pk}, format="json")

    assert switched.status_code == 200
    assert switched.data["slug"] == "switch-second"
    assert rejected.status_code == 400
    assert UserProfile.objects.get(user=user).active_organization_id == second_org.pk
