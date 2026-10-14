from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi import status


def test_batch_receipt_and_stock_movements(client, owner_headers):
    # 1. Create product
    prod_res = client.post("/api/v1/products", json={
        "name": "Greek Yogurt",
        "sku": "YGT-001",
        "unit": "cup",
        "purchase_cost": 40.00,
        "selling_price": 60.00,
        "reorder_threshold": 10
    }, headers=owner_headers)
    prod_id = prod_res.json()["id"]

    # 2. Receive stock into batch (Test 3)
    batch_payload = {
        "product_id": prod_id,
        "batch_number": "B-YGT-101",
        "quantity_received": 50,
        "received_date": str(date.today()),
        "expiry_date": str(date.today() + timedelta(days=20)),
        "unit_cost": 40.00
    }
    b_res = client.post("/api/v1/inventory/batches", json=batch_payload, headers=owner_headers)
    assert b_res.status_code == status.HTTP_200_OK
    b_data = b_res.json()
    assert b_data["current_quantity"] == 50
    assert b_data["days_until_expiry"] == 20

    # 3. Verify stock movement was created (Test 4)
    mov_res = client.get(f"/api/v1/inventory/movements?product_id={prod_id}", headers=owner_headers)
    assert mov_res.status_code == status.HTTP_200_OK
    movements = mov_res.json()
    assert len(movements) >= 1
    assert movements[0]["movement_type"] == "purchase_receipt"
    assert movements[0]["quantity"] == 50


def test_fefo_order_and_multi_batch_sale_allocation(client, owner_headers, staff_headers):
    # Create product
    prod_res = client.post("/api/v1/products", json={
        "name": "Butter Cookies",
        "sku": "CKI-001",
        "purchase_cost": 30.00,
        "selling_price": 50.00,
        "reorder_threshold": 5
    }, headers=owner_headers)
    prod_id = prod_res.json()["id"]

    today = date.today()
    # Batch 1: Expiry in 30 days, 10 units, cost 30.00
    client.post("/api/v1/inventory/batches", json={
        "product_id": prod_id,
        "batch_number": "B-CKI-LATER",
        "quantity_received": 10,
        "received_date": str(today - timedelta(days=5)),
        "expiry_date": str(today + timedelta(days=30)),
        "unit_cost": 30.00
    }, headers=owner_headers)

    # Batch 2: Expiry in 5 days (Earlier Expiry!), 10 units, cost 28.00
    client.post("/api/v1/inventory/batches", json={
        "product_id": prod_id,
        "batch_number": "B-CKI-SOON",
        "quantity_received": 10,
        "received_date": str(today - timedelta(days=2)),
        "expiry_date": str(today + timedelta(days=5)),
        "unit_cost": 28.00
    }, headers=owner_headers)

    # Total stock is 20 units.
    # Sale for 15 units (Test 6: fulfilled across multiple batches)
    sale_payload = {
        "items": [{"product_id": prod_id, "quantity": 15}],
        "discount_amount": 0.0,
        "payment_method": "cash"
    }
    sale_res = client.post("/api/v1/sales", json=sale_payload, headers=staff_headers)
    assert sale_res.status_code == status.HTTP_200_OK
    sale_data = sale_res.json()

    # FEFO Verification (Test 5):
    # Earlier expiring batch (B-CKI-SOON) must be exhausted FIRST (10 units),
    # and remaining 5 units deducted from B-CKI-LATER.
    items = sale_data["items"]
    assert len(items) == 2

    soon_item = next(it for it in items if it["batch_number"] == "B-CKI-SOON")
    later_item = next(it for it in items if it["batch_number"] == "B-CKI-LATER")
    assert soon_item["quantity"] == 10
    assert later_item["quantity"] == 5

    # Financial calculation verification (Test 10):
    # Revenue = 15 * 50 = 750
    # Cost = (10 * 28) + (5 * 30) = 280 + 150 = 430
    # Gross Profit = 750 - 430 = 320
    assert Decimal(str(sale_data["total_amount"])) == Decimal("750.00")
    assert Decimal(str(sale_data["total_cost"])) == Decimal("430.00")
    assert Decimal(str(sale_data["gross_profit"])) == Decimal("320.00")

    # Check batch current_quantity
    batches_res = client.get(f"/api/v1/inventory/batches?product_id={prod_id}", headers=owner_headers)
    b_dict = {b["batch_number"]: b["current_quantity"] for b in batches_res.json()}
    assert b_dict["B-CKI-SOON"] == 0
    assert b_dict["B-CKI-LATER"] == 5


def test_rejection_of_sales_exceeding_stock(client, owner_headers, staff_headers):
    # Test 7: Rejection of sales exceeding eligible stock
    prod_res = client.post("/api/v1/products", json={
        "name": "Almonds",
        "sku": "ALM-001",
        "purchase_cost": 100.00,
        "selling_price": 150.00,
        "reorder_threshold": 5
    }, headers=owner_headers)
    prod_id = prod_res.json()["id"]

    # Add 5 units
    client.post("/api/v1/inventory/batches", json={
        "product_id": prod_id,
        "batch_number": "B-ALM-1",
        "quantity_received": 5,
        "received_date": str(date.today()),
        "expiry_date": str(date.today() + timedelta(days=60)),
        "unit_cost": 100.00
    }, headers=owner_headers)

    # Attempt to sell 10 units (Exceeds available 5)
    sale_payload = {
        "items": [{"product_id": prod_id, "quantity": 10}],
        "payment_method": "cash"
    }
    sale_res = client.post("/api/v1/sales", json=sale_payload, headers=staff_headers)
    assert sale_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "insufficient eligible stock" in sale_res.json()["detail"].lower()


def test_prevention_of_sales_from_expired_batches(client, owner_headers, staff_headers):
    # Test 8: Prevention of sales from expired batches
    prod_res = client.post("/api/v1/products", json={
        "name": "Expired Bread",
        "sku": "EX-BRD-001",
        "purchase_cost": 20.00,
        "selling_price": 30.00,
        "reorder_threshold": 2
    }, headers=owner_headers)
    prod_id = prod_res.json()["id"]

    # Add batch with expiry date in the PAST
    client.post("/api/v1/inventory/batches", json={
        "product_id": prod_id,
        "batch_number": "B-EXPIRED",
        "quantity_received": 20,
        "received_date": str(date.today() - timedelta(days=10)),
        "expiry_date": str(date.today() - timedelta(days=2)),  # Expired 2 days ago!
        "unit_cost": 20.00
    }, headers=owner_headers)

    # Attempt to sell 1 unit
    sale_res = client.post("/api/v1/sales", json={
        "items": [{"product_id": prod_id, "quantity": 1}]
    }, headers=staff_headers)

    # Must be rejected because expired stock is excluded from sale fulfillment
    assert sale_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "insufficient eligible stock" in sale_res.json()["detail"].lower()


def test_sale_cancellation_and_stock_restoration(client, owner_headers, staff_headers):
    # Test 19: Sales cancellation and stock restoration through reversal entries
    prod_res = client.post("/api/v1/products", json={
        "name": "Energy Drink",
        "sku": "ENG-001",
        "purchase_cost": 50.00,
        "selling_price": 80.00,
        "reorder_threshold": 5
    }, headers=owner_headers)
    prod_id = prod_res.json()["id"]

    client.post("/api/v1/inventory/batches", json={
        "product_id": prod_id,
        "batch_number": "B-ENG-10",
        "quantity_received": 20,
        "received_date": str(date.today()),
        "expiry_date": str(date.today() + timedelta(days=90)),
        "unit_cost": 50.00
    }, headers=owner_headers)

    # 1. Make sale of 8 units
    sale_res = client.post("/api/v1/sales", json={
        "items": [{"product_id": prod_id, "quantity": 8}],
        "payment_method": "card"
    }, headers=staff_headers)
    sale_id = sale_res.json()["id"]

    # Verify remaining stock is 12
    p_check = client.get(f"/api/v1/products/{prod_id}", headers=staff_headers)
    assert p_check.json()["total_stock"] == 12

    # 2. Cancel sale
    cancel_res = client.post(f"/api/v1/sales/{sale_id}/cancel", json={
        "cancellation_reason": "Customer changed mind at register"
    }, headers=owner_headers)
    assert cancel_res.status_code == status.HTTP_200_OK
    assert cancel_res.json()["status"] == "cancelled"

    # 3. Verify stock restored back to 20
    p_restored = client.get(f"/api/v1/products/{prod_id}", headers=staff_headers)
    assert p_restored.json()["total_stock"] == 20

    # 4. Verify customer_return movement ledger was logged
    mov_res = client.get(f"/api/v1/inventory/movements?product_id={prod_id}", headers=owner_headers)
    movements = mov_res.json()
    return_mov = next((m for m in movements if m["movement_type"] == "customer_return"), None)
    assert return_mov is not None
    assert return_mov["quantity"] == 8
