import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_registration_creates_user_organization_membership_and_profile():
    client = APIClient()
    response = client.post(
        reverse("register"),
        {
            "email": "owner@example.com",
            "password": "SafePassw0rd!",
            "first_name": "Owner",
            "organization_name": "Northwind Ops",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["user"]["email"] == "owner@example.com"
    assert response.data["user"]["memberships"][0]["role"] == "owner"
    assert response.data["user"]["active_organization"]["name"] == "Northwind Ops"


@pytest.mark.django_db
def test_login_me_and_logout_refresh_token():
    client = APIClient()
    client.post(
        reverse("register"),
        {
            "email": "login@example.com",
            "password": "SafePassw0rd!",
            "first_name": "Login",
            "organization_name": "Login Ops",
        },
        format="json",
    )

    login = client.post(reverse("login"), {"email": "login@example.com", "password": "SafePassw0rd!"}, format="json")
    assert login.status_code == 200
    assert login.data["user"]["email"] == "login@example.com"

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    me = client.get(reverse("me"))
    assert me.status_code == 200
    assert me.data["email"] == "login@example.com"

    logout = client.post(reverse("logout"), {"refresh": login.data["refresh"]}, format="json")
    assert logout.status_code == 204

    refresh = client.post(reverse("token_refresh"), {"refresh": login.data["refresh"]}, format="json")
    assert refresh.status_code == 401
