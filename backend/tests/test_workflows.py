from decimal import Decimal

import pytest
from django.urls import reverse

from apps.hubs.models import Hub
from apps.inventory.models import InventoryBalance
from apps.restocking.models import RestockRequest
from apps.transfers.models import Transfer

from .test_inventory import context


@pytest.mark.django_db
def test_restock_lifecycle_receives_stock_once():
    client, organization, hub, product = context("restock-org")
    create = client.post(
        reverse("restock-request-list"),
        {"product": product.pk, "hub": hub.pk, "quantity": "8", "notes": "Low stock"},
        format="json",
    )
    assert create.status_code == 201
    restock_id = create.data["id"]

    for action in ("submit", "approve", "order", "receive"):
        response = client.post(reverse(f"restock-request-{action}", kwargs={"pk": restock_id}), {}, format="json")
        assert response.status_code == 200, response.data

    restock = RestockRequest.objects.get(pk=restock_id)
    balance = InventoryBalance.objects.get(organization=organization, hub=hub, product=product)
    assert restock.status == RestockRequest.Status.RECEIVED
    assert balance.on_hand == Decimal("8.00")

    repeated = client.post(reverse("restock-request-receive", kwargs={"pk": restock_id}), {}, format="json")
    assert repeated.status_code == 400
    assert InventoryBalance.objects.get(pk=balance.pk).on_hand == Decimal("8.00")


@pytest.mark.django_db
def test_transfer_dispatch_and_receive_move_stock_between_hubs():
    client, organization, source, product = context("transfer-org")
    destination = Hub.objects.create(organization=organization, name="Overflow Hub", code="OVERFLOW")
    stock_url = reverse("product-stock", kwargs={"pk": product.pk})
    receipt = client.post(stock_url, {"hub_id": source.pk, "movement_type": "receipt", "quantity": "10", "idempotency_key": "transfer-seed"}, format="json")
    assert receipt.status_code == 201

    create = client.post(
        reverse("transfer-list"),
        {"product": product.pk, "source_hub": source.pk, "destination_hub": destination.pk, "quantity": "4"},
        format="json",
    )
    assert create.status_code == 201
    transfer_id = create.data["id"]

    for action in ("submit", "approve", "dispatch", "receive"):
        response = client.post(reverse(f"transfer-{action}", kwargs={"pk": transfer_id}), {}, format="json")
        assert response.status_code == 200, response.data

    transfer = Transfer.objects.get(pk=transfer_id)
    assert transfer.status == Transfer.Status.RECEIVED
    assert InventoryBalance.objects.get(organization=organization, hub=source, product=product).on_hand == Decimal("6.00")
    assert InventoryBalance.objects.get(organization=organization, hub=destination, product=product).on_hand == Decimal("4.00")


@pytest.mark.django_db
def test_transfer_dispatch_rejects_insufficient_source_stock_without_state_change():
    client, organization, source, product = context("short-transfer-org")
    destination = Hub.objects.create(organization=organization, name="Overflow Hub", code="OVERFLOW")
    create = client.post(
        reverse("transfer-list"),
        {"product": product.pk, "source_hub": source.pk, "destination_hub": destination.pk, "quantity": "4"},
        format="json",
    )
    assert create.status_code == 201
    transfer_id = create.data["id"]
    for action in ("submit", "approve"):
        assert client.post(reverse(f"transfer-{action}", kwargs={"pk": transfer_id}), {}, format="json").status_code == 200

    dispatch = client.post(reverse("transfer-dispatch", kwargs={"pk": transfer_id}), {}, format="json")

    assert dispatch.status_code == 400
    assert Transfer.objects.get(pk=transfer_id).status == Transfer.Status.APPROVED
