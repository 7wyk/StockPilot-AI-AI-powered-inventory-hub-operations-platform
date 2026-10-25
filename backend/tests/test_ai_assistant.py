"""
Tests for Phase 7: Groq AI Operations Assistant backend.

Verifies:
- Conversation tenant isolation
- Conversation permissions (USE_AI requirement)
- Read tool deterministic query correctness
- AI write tool confirmation requirement (never mutates directly)
- Confirmed mutation execution via transactional services
- Cancellation / no mutation without explicit confirmation
- Security: cross-tenant ID rejection and action authorization
- Scoped user preferences memory
"""

from decimal import Decimal
import json

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.ai.models import Conversation, Message, UserPreference
from apps.ai import services as ai_services
from apps.ai.tools import execute_confirmed_write_action, execute_tool
from apps.audit.models import AuditLog
from apps.hubs.models import Hub
from apps.inventory.models import Category, InventoryBalance, Product
from apps.movements.models import StockMovement
from apps.organizations.models import Membership, Organization

User = get_user_model()


@pytest.fixture
def setup_ai_environment(db):
    """Set up two organizations with users, products, hubs, and balances."""
    # Organization 1 (Alpha Corp)
    user_owner = User.objects.create_user(
        username="owner@alphacorp.com", email="owner@alphacorp.com", password="password123"
    )
    user_viewer = User.objects.create_user(
        username="viewer@alphacorp.com", email="viewer@alphacorp.com", password="password123"
    )
    user_manager = User.objects.create_user(
        username="manager@alphacorp.com", email="manager@alphacorp.com", password="password123"
    )
    org_alpha = Organization.objects.create(name="Alpha Corp", slug="alpha-corp")

    Membership.objects.create(user=user_owner, organization=org_alpha, role=Membership.Role.OWNER, is_active=True)
    Membership.objects.create(user=user_viewer, organization=org_alpha, role=Membership.Role.VIEWER, is_active=True)
    Membership.objects.create(user=user_manager, organization=org_alpha, role=Membership.Role.INVENTORY_MANAGER, is_active=True)

    for u in (user_owner, user_viewer, user_manager):
        profile = getattr(u, "profile", None)
        if profile:
            profile.active_organization = org_alpha
            profile.save()

    hub_alpha_main = Hub.objects.create(organization=org_alpha, name="Alpha Central", code="ALP-1")
    hub_alpha_sec = Hub.objects.create(organization=org_alpha, name="Alpha Secondary", code="ALP-2")

    cat_alpha = Category.objects.create(organization=org_alpha, name="Industrial", slug="industrial")
    product_alpha_1 = Product.objects.create(
        organization=org_alpha,
        name="Precision Sensor",
        sku="SEN-001",
        cost_price=Decimal("45.00"),
        reorder_threshold=Decimal("15"),
        target_stock_level=Decimal("50"),
        category=cat_alpha,
    )
    InventoryBalance.objects.create(
        organization=org_alpha,
        product=product_alpha_1,
        hub=hub_alpha_main,
        on_hand=Decimal("10"),  # Low stock (10 <= 15)
        reserved=Decimal("0"),
    )

    product_alpha_stockout = Product.objects.create(
        organization=org_alpha,
        name="Titanium Bearing",
        sku="TBR-002",
        cost_price=Decimal("120.00"),
        reorder_threshold=Decimal("5"),
        target_stock_level=Decimal("20"),
        category=cat_alpha,
    )
    InventoryBalance.objects.create(
        organization=org_alpha,
        product=product_alpha_stockout,
        hub=hub_alpha_main,
        on_hand=Decimal("0"),
        reserved=Decimal("0"),
    )

    # Organization 2 (Beta Corp - Tenant boundary verification)
    user_beta = User.objects.create_user(
        username="user@betacorp.com", email="user@betacorp.com", password="password123"
    )
    org_beta = Organization.objects.create(name="Beta Corp", slug="beta-corp")
    Membership.objects.create(user=user_beta, organization=org_beta, role=Membership.Role.OWNER, is_active=True)
    profile_beta = getattr(user_beta, "profile", None)
    if profile_beta:
        profile_beta.active_organization = org_beta
        profile_beta.save()

    hub_beta = Hub.objects.create(organization=org_beta, name="Beta Warehouse", code="BET-1")
    product_beta = Product.objects.create(
        organization=org_beta,
        name="Secret Beta Product",
        sku="SEC-999",
        cost_price=Decimal("999.00"),
        reorder_threshold=Decimal("10"),
        target_stock_level=Decimal("100"),
    )

    return {
        "org_alpha": org_alpha,
        "user_owner": user_owner,
        "user_viewer": user_viewer,
        "user_manager": user_manager,
        "hub_alpha_main": hub_alpha_main,
        "hub_alpha_sec": hub_alpha_sec,
        "product_alpha_1": product_alpha_1,
        "product_alpha_stockout": product_alpha_stockout,
        "org_beta": org_beta,
        "user_beta": user_beta,
        "hub_beta": hub_beta,
        "product_beta": product_beta,
    }


def test_conversation_tenant_isolation(setup_ai_environment):
    """Conversations in Org A cannot be read or modified by users in Org B."""
    env = setup_ai_environment
    client_alpha = APIClient()
    client_alpha.force_authenticate(user=env["user_owner"])

    client_beta = APIClient()
    client_beta.force_authenticate(user=env["user_beta"])

    # Create conversation in Alpha
    resp = client_alpha.post("/api/v1/ai/conversations/", {"title": "Alpha Operations"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED
    conv_id = resp.data["id"]

    # Beta user listing conversations does not see Alpha's conversation
    beta_list = client_beta.get("/api/v1/ai/conversations/")
    assert beta_list.status_code == status.HTTP_200_OK
    assert not any(c["id"] == conv_id for c in beta_list.data)

    # Beta user direct access to Alpha's conversation is 404
    beta_detail = client_beta.get(f"/api/v1/ai/conversations/{conv_id}/")
    assert beta_detail.status_code == status.HTTP_404_NOT_FOUND


def test_conversation_permissions_enforced(setup_ai_environment):
    """Users with roles lacking USE_AI (e.g. VIEWER) receive 403 Forbidden."""
    env = setup_ai_environment
    client_viewer = APIClient()
    client_viewer.force_authenticate(user=env["user_viewer"])

    # Attempting to chat or view conversations should be 403
    resp = client_viewer.post("/api/v1/ai/chat/", {"message": "Hello"}, format="json")
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    resp = client_viewer.get("/api/v1/ai/conversations/")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_ai_read_tools_deterministic_correctness(setup_ai_environment):
    """Read tools return accurate database metrics without hallucination."""
    env = setup_ai_environment
    org = env["org_alpha"]
    user = env["user_owner"]

    # 1. Inventory Summary
    summary = execute_tool("get_inventory_summary", {}, org, user)
    assert summary["active_products"] == 2
    assert summary["low_stock_products"] == 1
    assert summary["out_of_stock_products"] == 1

    # 2. Low Stock Products
    low_stock = execute_tool("get_low_stock_products", {}, org, user)
    assert len(low_stock) == 1
    assert low_stock[0]["sku"] == "SEN-001"
    assert Decimal(low_stock[0]["on_hand"]) == Decimal("10")

    # 3. Stockouts
    stockouts = execute_tool("get_stockouts", {}, org, user)
    assert len(stockouts) == 1
    assert stockouts[0]["sku"] == "TBR-002"

    # 4. Hub Inventory
    hubs = execute_tool("get_hub_inventory", {}, org, user)
    assert len(hubs) == 2

    # 5. Restock Recommendations
    restock = execute_tool("get_restock_recommendations", {}, org, user)
    assert len(restock) >= 1
    sensor_rec = next(r for r in restock if r["sku"] == "SEN-001")
    assert Decimal(sensor_rec["recommended_quantity"]) == Decimal("40")  # target 50 - on_hand 10

    # 6. Product Details
    prod_details = execute_tool("get_product_details", {"sku": "SEN-001"}, org, user)
    assert prod_details["name"] == "Precision Sensor"
    assert Decimal(prod_details["total_on_hand"]) == Decimal("10")

    # 7. Generate Report
    rep = execute_tool("generate_report", {"report_type": "inventory_health", "format": "csv"}, org, user)
    assert rep["status"] == "report_ready"


def test_ai_write_tools_require_confirmation_no_direct_mutation(setup_ai_environment):
    """
    Critical Requirement: AI write tools MUST return a confirmation proposal
    and NEVER mutate inventory directly during tool execution.
    """
    env = setup_ai_environment
    org = env["org_alpha"]
    user = env["user_owner"]
    product = env["product_alpha_1"]
    hub = env["hub_alpha_main"]

    initial_balance = InventoryBalance.objects.get(product=product, hub=hub).on_hand
    initial_movements = StockMovement.objects.filter(product=product).count()

    # Tool invocation proposing stock receipt
    proposal = execute_tool(
        "receive_stock",
        {"product_id": product.id, "hub_id": hub.id, "quantity": "25", "reason": "Restock arrival"},
        org,
        user,
    )

    # 1. Proposal is structured and requires confirmation
    assert proposal.get("requires_confirmation") is True
    assert proposal["action"] == "receive_stock"
    assert proposal["parameters"]["product_id"] == product.id
    assert proposal["parameters"]["quantity"] == "25"
    assert Decimal(proposal["current_state"]["on_hand"]) == initial_balance

    # 2. Database state is completely untouched!
    current_balance = InventoryBalance.objects.get(product=product, hub=hub).on_hand
    assert current_balance == initial_balance
    assert StockMovement.objects.filter(product=product).count() == initial_movements


def test_confirmed_mutation_execution(setup_ai_environment):
    """
    When the user confirms the proposed write action via the API,
    Django executes the transactional service and records an audit log.
    """
    env = setup_ai_environment
    client = APIClient()
    client.force_authenticate(user=env["user_owner"])
    product = env["product_alpha_1"]
    hub = env["hub_alpha_main"]

    initial_on_hand = InventoryBalance.objects.get(product=product, hub=hub).on_hand

    # User confirms the write action
    confirm_payload = {
        "action": "receive_stock",
        "parameters": {
            "product_id": product.id,
            "hub_id": hub.id,
            "quantity": "20",
            "reason": "Air freight delivery verified",
        },
    }
    resp = client.post("/api/v1/ai/confirm-action/", confirm_payload, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["status"] == "success"
    assert Decimal(resp.data["new_on_hand"]) == initial_on_hand + Decimal("20")

    # Verify inventory was updated transactionally
    updated_balance = InventoryBalance.objects.get(product=product, hub=hub)
    assert updated_balance.on_hand == initial_on_hand + Decimal("20")

    # Verify stock movement record created
    movement = StockMovement.objects.filter(product=product, movement_type="receipt").latest("created_at")
    assert movement.quantity_delta == Decimal("20")
    assert movement.actor == env["user_owner"]

    # Verify audit event recorded
    audit = AuditLog.objects.filter(resource_type="stock_movement", resource_id=movement.pk).first()
    assert audit is not None


def test_confirmed_transfer_execution(setup_ai_environment):
    """Confirming a proposed transfer creates a transfer record."""
    env = setup_ai_environment
    client = APIClient()
    client.force_authenticate(user=env["user_owner"])
    product = env["product_alpha_1"]
    src_hub = env["hub_alpha_main"]
    dst_hub = env["hub_alpha_sec"]

    confirm_payload = {
        "action": "create_transfer",
        "parameters": {
            "product_id": product.id,
            "source_hub_id": src_hub.id,
            "destination_hub_id": dst_hub.id,
            "quantity": "5",
            "reason": "Balance stock across hubs",
        },
    }
    resp = client.post("/api/v1/ai/confirm-action/", confirm_payload, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["status"] == "success"
    assert "transfer_id" in resp.data


def test_cross_tenant_object_id_rejected(setup_ai_environment):
    """Passing a product or hub ID from another organization is strictly rejected."""
    env = setup_ai_environment
    client = APIClient()
    client.force_authenticate(user=env["user_owner"])  # Belongs to Alpha

    # Attempt to confirm action targeting Beta's product
    payload = {
        "action": "receive_stock",
        "parameters": {
            "product_id": env["product_beta"].id,  # From Org Beta!
            "hub_id": env["hub_alpha_main"].id,
            "quantity": "10",
        },
    }
    resp = client.post("/api/v1/ai/confirm-action/", payload, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "not found" in resp.data["detail"].lower()


def test_invalid_write_proposal_arguments_rejected(setup_ai_environment):
    """Excess issue quantity or invalid parameters return errors."""
    env = setup_ai_environment
    org = env["org_alpha"]
    user = env["user_owner"]
    product = env["product_alpha_1"]
    hub = env["hub_alpha_main"]

    # Available is 10; trying to issue 50
    proposal = execute_tool(
        "issue_stock",
        {"product_id": product.id, "hub_id": hub.id, "quantity": "50"},
        org,
        user,
    )
    assert "error" in proposal
    assert "available" in proposal["error"].lower()


def test_user_preferences_memory_scoped(setup_ai_environment):
    """User preferences memory is org-scoped, user-scoped, and validated."""
    env = setup_ai_environment
    client = APIClient()
    client.force_authenticate(user=env["user_owner"])

    # 1. Set valid preference
    put_resp = client.put(
        "/api/v1/ai/preferences/",
        {"key": "preferred_hub", "value": "Alpha Central"},
        format="json",
    )
    assert put_resp.status_code == status.HTTP_200_OK
    assert put_resp.data["key"] == "preferred_hub"

    # 2. Get preferences
    get_resp = client.get("/api/v1/ai/preferences/")
    assert get_resp.status_code == status.HTTP_200_OK
    assert len(get_resp.data) == 1
    assert get_resp.data[0]["key"] == "preferred_hub"

    # 3. Reject invalid unwhitelisted preference key
    bad_resp = client.put(
        "/api/v1/ai/preferences/",
        {"key": "unrestricted_private_notes", "value": "secret"},
        format="json",
    )
    assert bad_resp.status_code == status.HTTP_400_BAD_REQUEST

    # 4. Delete preference
    del_resp = client.delete("/api/v1/ai/preferences/preferred_hub/")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT
    assert client.get("/api/v1/ai/preferences/").data == []


def test_chat_flow_end_to_end(setup_ai_environment):
    """Chat endpoint processes query, creates conversation, and saves message history."""
    env = setup_ai_environment
    client = APIClient()
    client.force_authenticate(user=env["user_owner"])

    resp = client.post(
        "/api/v1/ai/chat/",
        {"message": "What is my current inventory summary?"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "conversation_id" in resp.data
    assert "message" in resp.data
    conv_id = resp.data["conversation_id"]

    # Verify conversation and message persisted in DB
    conv = Conversation.objects.get(id=conv_id)
    assert conv.organization == env["org_alpha"]
    assert conv.user == env["user_owner"]
    assert conv.messages.count() >= 2  # user message + assistant reply

    # Fetch conversation history via detail endpoint
    detail_resp = client.get(f"/api/v1/ai/conversations/{conv_id}/")
    assert detail_resp.status_code == status.HTTP_200_OK
    assert len(detail_resp.data["messages"]) >= 2
