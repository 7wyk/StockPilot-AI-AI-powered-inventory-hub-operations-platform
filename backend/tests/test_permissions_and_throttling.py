from decimal import Decimal

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import UserProfile
from apps.hubs.models import Hub
from apps.inventory.models import Product
from apps.organizations.models import Membership, Organization


def authenticated_client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


def member(email, organization, role):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.create_user(username=email, email=email, password="SafePassw0rd!")
    Membership.objects.create(user=user, organization=organization, role=role)
    UserProfile.objects.create(user=user, active_organization=organization)
    return user


@pytest.mark.django_db
def test_role_permissions_are_enforced_per_action():
    organization = Organization.objects.create(name="Permission Ops", slug="permission-ops")
    owner = member("owner@permission.test", organization, Membership.Role.OWNER)
    manager = member("manager@permission.test", organization, Membership.Role.INVENTORY_MANAGER)
    hub_operator = member("operator@permission.test", organization, Membership.Role.HUB_OPERATOR)
    viewer = member("viewer@permission.test", organization, Membership.Role.VIEWER)
    hub = Hub.objects.create(organization=organization, name="Main Hub", code="PERM-MAIN")
    product = Product.objects.create(organization=organization, name="Permission Widget", sku="PERM-001", cost_price=Decimal("5.00"))

    assert authenticated_client(viewer).get(reverse("product-list")).status_code == 200
    assert authenticated_client(viewer).post(reverse("product-list"), {"name": "Blocked", "sku": "BLOCK-001", "cost_price": "2.00"}, format="json").status_code == 403
    assert authenticated_client(manager).post(reverse("hub-list"), {"name": "Blocked Hub", "code": "BLOCKED"}, format="json").status_code == 403
    assert authenticated_client(hub_operator).post(
        reverse("product-stock", kwargs={"pk": product.pk}),
        {"hub_id": hub.pk, "movement_type": "receipt", "quantity": "2", "idempotency_key": "blocked-adjustment"},
        format="json",
    ).status_code == 403
    assert authenticated_client(manager).post(
        reverse("product-stock", kwargs={"pk": product.pk}),
        {"hub_id": hub.pk, "movement_type": "receipt", "quantity": "2", "idempotency_key": "allowed-adjustment"},
        format="json",
    ).status_code == 201
    assert authenticated_client(owner).get(reverse("organization-permissions")).status_code == 200


@pytest.mark.django_db
def test_object_access_is_isolated_even_when_ids_are_known():
    first_org = Organization.objects.create(name="First", slug="first-object")
    second_org = Organization.objects.create(name="Second", slug="second-object")
    first_user = member("first@object.test", first_org, Membership.Role.OWNER)
    second_user = member("second@object.test", second_org, Membership.Role.OWNER)
    foreign_product = Product.objects.create(organization=second_org, name="Foreign", sku="FOREIGN-001", cost_price=Decimal("4.00"))

    response = authenticated_client(first_user).get(reverse("product-detail", kwargs={"pk": foreign_product.pk}))
    assert response.status_code == 404
    response = authenticated_client(first_user).patch(
        reverse("product-detail", kwargs={"pk": foreign_product.pk}),
        {"name": "Should not change"},
        format="json",
    )
    assert response.status_code == 404
    assert authenticated_client(second_user).get(reverse("product-detail", kwargs={"pk": foreign_product.pk})).status_code == 200


@pytest.mark.django_db
def test_registration_is_rate_limited_by_client_ip():
    cache.clear()
    with override_settings(AUTH_RATE_LIMIT="2/minute", SENSITIVE_RATE_LIMIT="2/minute"):
        client = APIClient(REMOTE_ADDR="198.51.100.44")
        payload = {"password": "SafePassw0rd!", "first_name": "Rate"}
        first = client.post(reverse("register"), {**payload, "email": "rate-one@test.com", "organization_name": "Rate One Ops"}, format="json")
        second = client.post(reverse("register"), {**payload, "email": "rate-two@test.com", "organization_name": "Rate Two Ops"}, format="json")
        third = client.post(reverse("register"), {**payload, "email": "rate-three@test.com", "organization_name": "Rate Three Ops"}, format="json")

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 429
    cache.clear()
