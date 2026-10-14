from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi import status


def test_reorder_recommendation_and_dashboard_aggregation(client, owner_headers, staff_headers):
    # Test 16: Reorder recommendation calculations
    # Test 17: Dashboard aggregation consistency
    
    # 1. Create Product
    prod_res = client.post("/api/v1/products", json={
        "name": "Basmati Rice 5kg",
        "sku": "RCE-005",
        "purchase_cost": 400.00,
        "selling_price": 550.00,
        "reorder_threshold": 20
    }, headers=owner_headers)
    prod_id = prod_res.json()["id"]

    # 2. Add batch with 15 units (<= threshold 20)
    today = date.today()
    client.post("/api/v1/inventory/batches", json={
        "product_id": prod_id,
        "batch_number": "B-RCE-01",
        "quantity_received": 15,
        "received_date": str(today - timedelta(days=5)),
        "expiry_date": str(today + timedelta(days=180)),
        "unit_cost": 400.00
    }, headers=owner_headers)

    # 3. Check Reorder Recommendations (Test 16)
    rec_res = client.get("/api/v1/recommendations/reorder", headers=staff_headers)
    assert rec_res.status_code == status.HTTP_200_OK
    recs = rec_res.json()
    rce_rec = next((r for r in recs if r["product_id"] == prod_id), None)
    assert rce_rec is not None
    assert rce_rec["current_stock"] == 15
    assert rce_rec["reorder_point"] >= 20
    assert rce_rec["urgency"] in ("critical", "moderate")
    assert rce_rec["suggested_order_quantity"] > 0
    assert "reorder point" in rce_rec["reason"].lower() or "stock" in rce_rec["reason"].lower()

    # 4. Check Dashboard Aggregations (Test 17)
    dash_res = client.get("/api/v1/dashboard/summary", headers=staff_headers)
    assert dash_res.status_code == status.HTTP_200_OK
    dash = dash_res.json()
    assert dash["total_active_products"] >= 1
    assert dash["total_eligible_units"] == 15
    assert dash["low_stock_products_count"] >= 1
    # Valuation = 15 units * 400.00 = 6000.00
    assert Decimal(str(dash["inventory_valuation"])) == Decimal("6000.00")
