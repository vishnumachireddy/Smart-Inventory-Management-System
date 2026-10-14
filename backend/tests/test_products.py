import pytest
from fastapi import status


def test_product_creation_and_duplicate_sku_validation(client, owner_headers):
    # 1. Create category
    cat_res = client.post("/api/v1/categories", json={"name": "Dairy"}, headers=owner_headers)
    cat_id = cat_res.json()["id"]

    # 2. Create product
    payload = {
        "name": "Fresh Milk 1L",
        "sku": "MLK-001",
        "barcode": "1234567890",
        "category_id": cat_id,
        "unit": "litre",
        "purchase_cost": 50.00,
        "selling_price": 65.00,
        "reorder_threshold": 10
    }
    res = client.post("/api/v1/products", json=payload, headers=owner_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["name"] == "Fresh Milk 1L"
    assert data["sku"] == "MLK-001"
    assert data["total_stock"] == 0
    assert data["stock_status"] == "out_of_stock"

    # 3. Attempt to create another product with the same SKU
    dup_payload = {
        "name": "Duplicate SKU Milk",
        "sku": "MLK-001",
        "category_id": cat_id,
        "purchase_cost": 45.00,
        "selling_price": 60.00,
        "reorder_threshold": 5
    }
    dup_res = client.post("/api/v1/products", json=dup_payload, headers=owner_headers)
    assert dup_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in dup_res.json()["detail"].lower()
