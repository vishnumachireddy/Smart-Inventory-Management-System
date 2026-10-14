import pytest
from fastapi import status


def test_user_registration_and_login(client):
    # 1. Register first user (automatically assigned 'shop_owner')
    reg_payload = {
        "email": "first_owner@example.com",
        "password": "Password123!",
        "full_name": "First Owner",
        "role": "shop_owner"
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["email"] == "first_owner@example.com"
    assert data["role"] == "shop_owner"

    # 2. Login with valid credentials
    login_payload = {
        "email": "first_owner@example.com",
        "password": "Password123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == status.HTTP_200_OK
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["role"] == "shop_owner"

    # 3. Access protected /me route
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.json()["email"] == "first_owner@example.com"


def test_unauthorized_access_rejected(client):
    # Attempting to access protected endpoints without token must return 401
    res = client.get("/api/v1/products")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # Invalid token must return 401
    res_bad = client.get("/api/v1/products", headers={"Authorization": "Bearer bad-token-xyz"})
    assert res_bad.status_code == status.HTTP_401_UNAUTHORIZED


def test_role_based_authorization(client, owner_headers, staff_headers):
    # Staff can view products
    staff_view = client.get("/api/v1/products", headers=staff_headers)
    assert staff_view.status_code == status.HTTP_200_OK

    # Staff is FORBIDDEN (403) from creating categories or accessing user management
    category_payload = {"name": "Admin Only Cat", "description": "Restricted"}
    staff_create = client.post("/api/v1/categories", json=category_payload, headers=staff_headers)
    assert staff_create.status_code == status.HTTP_403_FORBIDDEN

    # Shop Owner is ALLOWED to create categories
    owner_create = client.post("/api/v1/categories", json=category_payload, headers=owner_headers)
    assert owner_create.status_code == status.HTTP_200_OK
    assert owner_create.json()["name"] == "Admin Only Cat"
