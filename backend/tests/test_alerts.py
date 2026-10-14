from datetime import date, timedelta
import pytest
from fastapi import status


def test_low_stock_and_expiry_alerts_generation(client, owner_headers):
    today = date.today()

    # 1. Product with reorder_threshold=10, 0 stock initially -> triggers out_of_stock alert
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

    alerts_res = client.get("/api/v1/alerts", headers=owner_headers)
    alerts = alerts_res.json()
    oos_alert = next((a for a in alerts if a["alert_type"] == "out_of_stock" and a["sku"] == "HNY-001"), None)
    assert oos_alert is not None
    assert "OUT OF STOCK" in oos_alert["message"]

    # Now add 5 units (threshold 10) -> transitions to low_stock
    client.post("/api/v1/inventory/batches", json={
        "product_id": prod1["id"],
        "batch_number": "B-HNY-01",
        "quantity_received": 5,
        "received_date": str(today - timedelta(days=2)),
        "expiry_date": str(today + timedelta(days=60)),
        "unit_cost": 150.00
    }, headers=owner_headers)

    client.post("/api/v1/alerts/reconcile", headers=owner_headers)
    alerts_low = client.get("/api/v1/alerts", headers=owner_headers).json()
    low_alert = next((a for a in alerts_low if a["alert_type"] == "low_stock" and a["sku"] == "HNY-001"), None)
    assert low_alert is not None
    assert "Threshold" in low_alert["message"]

    # 2. Near-expiry batch: expiry in 4 days (<= 7 days default window)
    prod2 = client.post("/api/v1/products", json={
        "name": "Soy Milk",
        "sku": "SOY-001",
        "purchase_cost": 40.00,
        "selling_price": 60.00,
        "reorder_threshold": 5
    }, headers=owner_headers).json()

    client.post("/api/v1/inventory/batches", json={
        "product_id": prod2["id"],
        "batch_number": "B-SOY-EXP04",
        "quantity_received": 25,
        "received_date": str(today - timedelta(days=5)),
        "expiry_date": str(today + timedelta(days=4)),
        "unit_cost": 40.00
    }, headers=owner_headers)

    client.post("/api/v1/alerts/reconcile", headers=owner_headers)
    alerts2 = client.get("/api/v1/alerts", headers=owner_headers).json()
    near_alert = next((a for a in alerts2 if a["alert_type"] == "near_expiry" and a["sku"] == "SOY-001"), None)
    assert near_alert is not None
    assert "expires in 4 day" in near_alert["message"]
