import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import UserProfile
from apps.organizations.models import Membership, Organization, OrganizationInvite

User = get_user_model()


def auth_client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def user_with_org(email, organization, role):
    user = User.objects.create_user(username=email, email=email, password="SafePassw0rd!", first_name=email.split("@")[0])
    Membership.objects.create(user=user, organization=organization, role=role)
    UserProfile.objects.create(user=user, active_organization=organization)
    return user


@pytest.mark.django_db
def test_owner_can_invite_and_invited_user_can_accept():
    organization = Organization.objects.create(name="Operations", slug="operations")
    owner = user_with_org("owner@ops.test", organization, Membership.Role.OWNER)
    invited = User.objects.create_user(username="operator@ops.test", email="operator@ops.test", password="SafePassw0rd!")

    create = auth_client(owner).post(
        reverse("organization-invitations"),
        {"email": invited.email, "role": Membership.Role.HUB_OPERATOR},
        format="json",
    )

    assert create.status_code == 201
    assert create.data["status"] == "pending"
    assert create.data["role"] == Membership.Role.HUB_OPERATOR
    assert create.data["invitation_token"]
    invite = OrganizationInvite.objects.get(pk=create.data["id"])
    assert invite.token_hash != create.data["invitation_token"]

    accepted = auth_client(invited).post(
        reverse("organization-invitation-accept"),
        {"token": create.data["invitation_token"]},
        format="json",
    )
    assert accepted.status_code == 200
    assert accepted.data["role"] == Membership.Role.HUB_OPERATOR
    assert Membership.objects.get(user=invited, organization=organization).is_active is True
    assert invite.__class__.objects.get(pk=invite.pk).accepted_at is not None


@pytest.mark.django_db
def test_invitation_can_be_canceled_and_resend_rotates_token():
    organization = Organization.objects.create(name="Operations", slug="operations-resend")
    owner = user_with_org("owner@resend.test", organization, Membership.Role.OWNER)
    client = auth_client(owner)
    created = client.post(reverse("organization-invitations"), {"email": "new@resend.test"}, format="json")
    assert created.status_code == 201

    canceled = client.post(reverse("organization-invitation-action", args=[created.data["id"], "cancel"]), format="json")
    assert canceled.status_code == 200
    assert canceled.data["status"] == "canceled"

    resent = client.post(reverse("organization-invitation-action", args=[created.data["id"], "resend"]), format="json")
    assert resent.status_code == 200
    assert resent.data["status"] == "pending"
    assert resent.data["invitation_token"] != created.data["invitation_token"]


@pytest.mark.django_db
def test_only_authorized_roles_can_change_or_remove_members():
    organization = Organization.objects.create(name="Operations", slug="operations-members")
    owner = user_with_org("owner@members.test", organization, Membership.Role.OWNER)
    manager = user_with_org("manager@members.test", organization, Membership.Role.INVENTORY_MANAGER)
    viewer = user_with_org("viewer@members.test", organization, Membership.Role.VIEWER)

    forbidden = auth_client(manager).patch(
        reverse("organization-member-detail", args=[viewer.memberships.get(organization=organization).pk]),
        {"role": Membership.Role.ANALYST},
        format="json",
    )
    assert forbidden.status_code == 403

    changed = auth_client(owner).patch(
        reverse("organization-member-detail", args=[viewer.memberships.get(organization=organization).pk]),
        {"role": Membership.Role.ANALYST},
        format="json",
    )
    assert changed.status_code == 200
    assert changed.data["role"] == Membership.Role.ANALYST

    removed = auth_client(owner).delete(reverse("organization-member-detail", args=[manager.memberships.get(organization=organization).pk]))
    assert removed.status_code == 204
    assert Membership.objects.get(user=manager, organization=organization).is_active is False


@pytest.mark.django_db
def test_members_and_invitations_are_tenant_scoped():
    first_org = Organization.objects.create(name="First", slug="first-admin")
    second_org = Organization.objects.create(name="Second", slug="second-admin")
    owner = user_with_org("owner@first.test", first_org, Membership.Role.OWNER)
    other = user_with_org("other@second.test", second_org, Membership.Role.OWNER)
    invitation = auth_client(other).post(reverse("organization-invitations"), {"email": "someone@test.com"}, format="json")
    assert invitation.status_code == 201

    members = auth_client(owner).get(reverse("organization-members"))
    assert members.status_code == 200
    payload = members.data["results"] if isinstance(members.data, dict) else members.data
    assert [member["email"] for member in payload] == [owner.email]
    pending = auth_client(owner).get(reverse("organization-invitations"), {"status": "pending"}).data
    assert pending == []
