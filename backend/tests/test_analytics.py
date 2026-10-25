"""Tests for the analytics app — services, views, and exports."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.analytics import services
from apps.analytics.exports import generate_csv, report_data_to_table
from apps.analytics.models import Report
from apps.hubs.models import Hub
from apps.inventory.models import Category, InventoryBalance, Product
from apps.movements.models import StockMovement
from apps.organizations.models import Membership, Organization
from apps.restocking.models import RestockRequest
from apps.transfers.models import Transfer

User = get_user_model()


@pytest.fixture
def org_and_user(db):
    """Create an organization with an owner user and active membership."""
    user = User.objects.create_user(
        username="analyst@test.com",
        email="analyst@test.com",
        password="test1234!",
    )
    org = Organization.objects.create(name="Analytics Org", slug="analytics-org")
    membership = Membership.objects.create(
        user=user, organization=org, role=Membership.Role.OWNER, is_active=True,
    )
    # Set active organization via profile if it exists
    profile = getattr(user, "profile", None)
    if profile:
        profile.active_organization = org
        profile.save()
    return org, user, membership


@pytest.fixture
def populated_org(org_and_user):
    """Create products, hubs, balances, and movements for analytics testing."""
    org, user, membership = org_and_user
    cat = Category.objects.create(organization=org, name="Electronics", slug="electronics")
    hub_a = Hub.objects.create(organization=org, name="Hub Alpha", code="HUB-A")
    hub_b = Hub.objects.create(organization=org, name="Hub Beta", code="HUB-B")

    # Product with stock — healthy
    p1 = Product.objects.create(
        organization=org, name="Widget A", sku="WA-001",
        cost_price=Decimal("25.00"), reorder_threshold=Decimal("10"),
        target_stock_level=Decimal("100"), category=cat,
    )
    InventoryBalance.objects.create(
        organization=org, product=p1, hub=hub_a,
        on_hand=Decimal("50"),
    )

    # Product with low stock
    p2 = Product.objects.create(
        organization=org, name="Widget B", sku="WB-002",
        cost_price=Decimal("15.00"), reorder_threshold=Decimal("20"),
        target_stock_level=Decimal("80"),
    )
    InventoryBalance.objects.create(
        organization=org, product=p2, hub=hub_a,
        on_hand=Decimal("8"),
    )

    # Product out of stock
    p3 = Product.objects.create(
        organization=org, name="Widget C", sku="WC-003",
        cost_price=Decimal("50.00"), reorder_threshold=Decimal("5"),
        target_stock_level=Decimal("30"),
    )

    # Create a movement for p1 (so it's not slow-moving)
    StockMovement.objects.create(
        organization=org, product=p1, hub=hub_a, actor=user,
        movement_type="receipt", quantity_delta=Decimal("50"),
        quantity_before=Decimal("0"), quantity_after=Decimal("50"),
    )

    return org, user, membership, hub_a, hub_b, p1, p2, p3, cat


class AnalyticsServicesTest(TestCase):
    """Test deterministic analytics calculations."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="svc@test.com", email="svc@test.com", password="test1234!",
        )
        self.org = Organization.objects.create(name="Svc Org", slug="svc-org")
        Membership.objects.create(
            user=self.user, organization=self.org,
            role=Membership.Role.OWNER, is_active=True,
        )

    def test_overview_empty_org(self):
        result = services.get_overview(self.org)
        assert result["active_products"] == 0
        assert result["data_status"] == "empty"
        assert result["inventory_value"] == "0"

    def test_overview_with_stock(self):
        hub = Hub.objects.create(organization=self.org, name="H1", code="H1")
        p = Product.objects.create(
            organization=self.org, name="P1", sku="P1",
            cost_price=Decimal("10.00"), reorder_threshold=Decimal("5"),
        )
        InventoryBalance.objects.create(
            organization=self.org, product=p, hub=hub,
            on_hand=Decimal("20"),
        )
        result = services.get_overview(self.org)
        assert result["active_products"] == 1
        assert Decimal(result["inventory_value"]) == Decimal("200.00")
        assert Decimal(result["total_units"]) == Decimal("20.00")
        assert result["data_status"] == "live"

    def test_low_stock_detection(self):
        hub = Hub.objects.create(organization=self.org, name="H2", code="H2")
        p = Product.objects.create(
            organization=self.org, name="LowP", sku="LP1",
            cost_price=Decimal("5.00"), reorder_threshold=Decimal("20"),
            target_stock_level=Decimal("50"),
        )
        InventoryBalance.objects.create(
            organization=self.org, product=p, hub=hub,
            on_hand=Decimal("10"),
        )
        result = services.get_low_stock_products(self.org)
        assert len(result) == 1
        assert result[0]["sku"] == "LP1"
        assert result[0]["deficit"] == "40.00"

    def test_restock_recommendations(self):
        hub = Hub.objects.create(organization=self.org, name="H3", code="H3")
        p = Product.objects.create(
            organization=self.org, name="RestockP", sku="RP1",
            cost_price=Decimal("10.00"), reorder_threshold=Decimal("5"),
            target_stock_level=Decimal("30"),
        )
        InventoryBalance.objects.create(
            organization=self.org, product=p, hub=hub,
            on_hand=Decimal("10"),
        )
        result = services.get_restock_recommendations(self.org)
        assert len(result) == 1
        assert Decimal(result[0]["recommended_quantity"]) == Decimal("20.00")
        assert Decimal(result[0]["estimated_cost"]) == Decimal("200.00")


@pytest.mark.django_db
def test_csv_export_basic():
    """Test CSV generation produces valid output."""
    content = generate_csv(
        title="Test Report",
        headers=["Name", "Value"],
        rows=[["Widget", "100"], ["Gadget", "200"]],
    )
    assert isinstance(content, bytes)
    text = content.decode("utf-8-sig")
    lines = text.strip().split("\n")
    assert len(lines) == 3
    assert "Name" in lines[0]
    assert "Widget" in lines[1]


@pytest.mark.django_db
def test_csv_export_empty():
    """Test CSV generation with no data rows."""
    content = generate_csv(title="Empty", headers=["Col1", "Col2"], rows=[])
    text = content.decode("utf-8-sig")
    lines = text.strip().split("\n")
    assert len(lines) == 1  # headers only


@pytest.mark.django_db
def test_report_data_to_table_low_stock():
    """Test table conversion for low stock data."""
    data = [
        {
            "product_name": "Widget", "sku": "W1", "on_hand": "5",
            "reorder_threshold": "10", "target_stock_level": "50",
            "deficit": "45", "category": "Parts",
        }
    ]
    headers, rows = report_data_to_table("low_stock", data)
    assert len(headers) == 7
    assert len(rows) == 1
    assert rows[0][0] == "Widget"


@pytest.mark.django_db
def test_movement_trends_empty(org_and_user):
    """Test movement trends with no movements returns insufficient_history."""
    org, user, _ = org_and_user
    result = services.get_movement_trends(org, days=30)
    assert result["data_status"] == "insufficient_history"
    assert result["trends"] == []


@pytest.mark.django_db
def test_hub_analytics(populated_org):
    """Test hub analytics returns per-hub breakdown."""
    org, user, _, hub_a, hub_b, p1, p2, p3, _ = populated_org
    result = services.get_hub_analytics(org)
    assert len(result) >= 1
    hub_a_data = next((h for h in result if h["hub_code"] == "HUB-A"), None)
    assert hub_a_data is not None
    assert Decimal(hub_a_data["total_units"]) > 0


@pytest.mark.django_db
def test_stock_health(populated_org):
    """Test stock health breakdown categories correctly."""
    org, user, _, hub_a, hub_b, p1, p2, p3, _ = populated_org
    result = services.get_stock_health(org)
    summary = result["summary"]
    assert summary["total_products"] == 3
    assert summary["out_of_stock"] >= 1
    assert summary["low_stock"] >= 1


class AnalyticsAPITest(TestCase):
    """Test analytics API endpoints including tenant isolation."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="api@test.com", email="api@test.com", password="test1234!",
        )
        self.org = Organization.objects.create(name="API Org", slug="api-org")
        Membership.objects.create(
            user=self.user, organization=self.org,
            role=Membership.Role.OWNER, is_active=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_overview_endpoint(self):
        resp = self.client.get("/api/v1/analytics/overview/")
        assert resp.status_code == 200
        assert "active_products" in resp.data
        assert "inventory_value" in resp.data

    def test_movements_endpoint(self):
        resp = self.client.get("/api/v1/analytics/movements/")
        assert resp.status_code == 200
        assert "trends" in resp.data

    def test_hubs_endpoint(self):
        resp = self.client.get("/api/v1/analytics/hubs/")
        assert resp.status_code == 200
        assert isinstance(resp.data, list)

    def test_stock_health_endpoint(self):
        resp = self.client.get("/api/v1/analytics/stock-health/")
        assert resp.status_code == 200
        assert "summary" in resp.data

    def test_low_stock_endpoint(self):
        resp = self.client.get("/api/v1/analytics/low-stock/")
        assert resp.status_code == 200

    def test_restock_recommendations_endpoint(self):
        resp = self.client.get("/api/v1/analytics/restock-recommendations/")
        assert resp.status_code == 200

    def test_reports_list_endpoint(self):
        resp = self.client.get("/api/v1/reports/")
        assert resp.status_code == 200

    def test_report_generate_csv(self):
        resp = self.client.post("/api/v1/reports/generate/", {
            "report_type": "inventory_health",
            "format": "csv",
        }, format="json")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"

    def test_tenant_isolation(self):
        """Reports from another org should not be visible."""
        other_user = User.objects.create_user(
            username="other@test.com", email="other@test.com", password="test1234!",
        )
        other_org = Organization.objects.create(name="Other Org", slug="other-org")
        Membership.objects.create(
            user=other_user, organization=other_org,
            role=Membership.Role.OWNER, is_active=True,
        )
        Report.objects.create(
            organization=other_org, requested_by=other_user,
            report_type="low_stock", status="completed",
        )
        resp = self.client.get("/api/v1/reports/")
        assert resp.status_code == 200
        assert len(resp.data) == 0  # Should not see other org's reports

    def test_unauthenticated_access_denied(self):
        client = APIClient()
        resp = client.get("/api/v1/analytics/overview/")
        assert resp.status_code == 401
