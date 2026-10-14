from datetime import date, timedelta
import pytest
from fastapi import status


def test_low_stock_and_expiry_alerts_generation(client, owner_headers):
    today = date.today()

    # 1. Product with reorder_threshold=10, 0 stock initially -> triggers low_stock alert (Test 11)
    prod1 = client.post("/api/v1/products", json={
        "name": "Organic Honey",
        "sku": "HNY-001",
        "purchase_cost": 150.00,
        "selling_price": 220.00,
        "reorder_threshold": 10
    }, headers=owner_headers).json()

    # Reconcile alerts
    rec_res = client.post("/api/v1/alerts/reconcile", headers=owner_headers)
    assert rec_res.status_code == status.HTTP_200_OK

    alerts_res = client.get("/api/v1/alerts?product_id=" + str(prod1["id"]), headers=owner_headers)
    alerts = alerts_res.json()
    low_alert = next((a for a in alerts if a["alert_type"] == "low_stock"), None)
    assert low_alert is not None
    assert "at or below reorder threshold" in low_alert["message"]

    # 2. Near-expiry batch (Test 12): expiry in 15 days (<= 30 days default warning window)
    prod2 = client.post("/api/v1/products", json={
        "name": "Soy Milk",
        "sku": "SOY-001",
        "purchase_cost": 40.00,
        "selling_price": 60.00,
        "reorder_threshold": 5
    }, headers=owner_headers).json()

    client.post("/api/v1/inventory/batches", json={
        "product_id": prod2["id"],
        "batch_number": "B-SOY-EXP15",
        "quantity_received": 25,
        "received_date": str(today - timedelta(days=5)),
        "expiry_date": str(today + timedelta(days=15)),
        "unit_cost": 40.00
    }, headers=owner_headers)

    client.post("/api/v1/alerts/reconcile", headers=owner_headers)
    alerts2 = client.get("/api/v1/alerts?product_id=" + str(prod2["id"]), headers=owner_headers).json()
    near_alert = next((a for a in alerts2 if a["alert_type"] == "near_expiry"), None)
    assert near_alert is not None
    assert "expires in 15 day(s)" in near_alert["message"]

    # 3. Expired batch with remaining stock (Test 13)
    client.post("/api/v1/inventory/batches", json={
        "product_id": prod2["id"],
        "batch_number": "B-SOY-EXPD",
        "quantity_received": 10,
        "received_date": str(today - timedelta(days=40)),
        "expiry_date": str(today - timedelta(days=3)),  # Expired 3 days ago!
        "unit_cost": 40.00
    }, headers=owner_headers)

    client.post("/api/v1/alerts/reconcile", headers=owner_headers)
    alerts3 = client.get("/api/v1/alerts?product_id=" + str(prod2["id"]), headers=owner_headers).json()
    exp_alert = next((a for a in alerts3 if a["alert_type"] == "expired"), None)
    assert exp_alert is not None
    assert "expired on" in exp_alert["message"]
    assert exp_alert["severity"] == "critical"
