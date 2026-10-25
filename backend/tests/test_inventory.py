from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import UserProfile
from apps.hubs.models import Hub
from apps.inventory.models import InventoryBalance, Product
from apps.organizations.models import Membership, Organization
from apps.movements.models import StockMovement

User = get_user_model()


def context(slug="inventory-org"):
    user = User.objects.create_user(username=f"{slug}@example.com", email=f"{slug}@example.com", password="SafePassw0rd!")
    organization = Organization.objects.create(name=slug.title(), slug=slug)
    Membership.objects.create(user=user, organization=organization, role=Membership.Role.OWNER)
    UserProfile.objects.create(user=user, active_organization=organization)
    hub = Hub.objects.create(organization=organization, name="Main Hub", code=f"{slug[:4].upper()}-MAIN")
    product = Product.objects.create(organization=organization, name="Blue Widget", sku=f"{slug[:4].upper()}-001", cost_price=Decimal("12.50"), reorder_threshold=Decimal("5"))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client, organization, hub, product


@pytest.mark.django_db
def test_stock_receipt_is_transactional_audited_and_idempotent():
    client, organization, hub, product = context()
    url = reverse("product-stock", kwargs={"pk": product.pk})
    payload = {"hub_id": hub.pk, "movement_type": "receipt", "quantity": "10", "reason": "Opening count", "idempotency_key": "opening-1"}

    first = client.post(url, payload, format="json")
    second = client.post(url, payload, format="json")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.data["movement_id"] == second.data["movement_id"]
    balance = InventoryBalance.objects.get(organization=organization, hub=hub, product=product)
    assert balance.on_hand == Decimal("10.00")
    assert StockMovement.objects.filter(organization=organization, product=product).count() == 1


@pytest.mark.django_db
def test_issue_cannot_exceed_available_stock_and_dashboard_uses_real_records():
    client, organization, hub, product = context("risk-org")
    url = reverse("product-stock", kwargs={"pk": product.pk})
    client.post(url, {"hub_id": hub.pk, "movement_type": "receipt", "quantity": "3", "idempotency_key": "receipt-1"}, format="json")

    issue = client.post(url, {"hub_id": hub.pk, "movement_type": "issue", "quantity": "4", "idempotency_key": "issue-1"}, format="json")
    summary = client.get(reverse("dashboard-summary"))

    assert issue.status_code == 400
    assert "available stock" in issue.data["detail"]
    assert summary.status_code == 200
    assert summary.data["active_products"] == 1
    assert summary.data["stock_units"] == "3.00"
    assert summary.data["inventory_value"] == "37.50"
    assert summary.data["low_stock_products"] == 1


@pytest.mark.django_db
def test_product_list_is_tenant_scoped():
    first_client, first_org, first_hub, first_product = context("first-inventory")
    second_client, second_org, second_hub, second_product = context("second-inventory")

    response = first_client.get(reverse("product-list"))

    assert response.status_code == 200
    payload = response.data["results"] if isinstance(response.data, dict) else response.data
    assert [item["sku"] for item in payload] == [first_product.sku]
    assert second_product.sku not in [item["sku"] for item in payload]
