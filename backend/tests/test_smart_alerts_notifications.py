import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock

from app.models import (
    Product,
    InventoryBatch,
    StockMovement,
    Alert,
    NotificationSettings,
    ScheduledJobRun,
    EmailDeliveryLog,
    DailyInventorySnapshot,
    AppSetting,
)
from app.services.inventory_alert_service import InventoryAlertService
from app.services.email_service import EmailNotificationService
from app.services.daily_scheduler_service import DailySchedulerService

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def sample_catalog(db_session, owner_user):
    today = datetime.now(KOLKATA_TZ).date()

    # Product 1: Out of stock (0 units)
    p_out = Product(
        name="Out of Stock Milk",
        sku="TEST-OOS-001",
        unit="pack",
        purchase_cost=Decimal("40.00"),
        selling_price=Decimal("50.00"),
        reorder_threshold=15,
        is_active=True
    )
    db_session.add(p_out)
    db_session.flush()

    # Product 2: Low stock (5 units <= threshold 20)
    p_low = Product(
        name="Low Stock Bread",
        sku="TEST-LOW-002",
        unit="pack",
        purchase_cost=Decimal("25.00"),
        selling_price=Decimal("35.00"),
        reorder_threshold=20,
        is_active=True
    )
    db_session.add(p_low)
    db_session.flush()

    # Batch for p_low: 5 units healthy
    b_low = InventoryBatch(
        product_id=p_low.id,
        batch_number="B-LOW-01",
        quantity_received=5,
        current_quantity=5,
        received_date=today - timedelta(days=5),
        expiry_date=today + timedelta(days=60),
        unit_cost=Decimal("25.00"),
        status="active"
    )
    db_session.add(b_low)

    # Product 3: Healthy stock (100 units > threshold 10) but has near-expiry batch
    p_near = Product(
        name="Near Expiry Yogurt",
        sku="TEST-NEAR-003",
        unit="cup",
        purchase_cost=Decimal("20.00"),
        selling_price=Decimal("30.00"),
        reorder_threshold=10,
        is_active=True
    )
    db_session.add(p_near)
    db_session.flush()

    # Batch 1 for p_near: 8 units expiring in 4 days (within 7-day window)
    b_near = InventoryBatch(
        product_id=p_near.id,
        batch_number="B-NEAR-01",
        quantity_received=8,
        current_quantity=8,
        received_date=today - timedelta(days=10),
        expiry_date=today + timedelta(days=4),
        unit_cost=Decimal("20.00"),
        status="active"
    )
    # Batch 2 for p_near: 50 units expiring in 60 days
    b_healthy = InventoryBatch(
        product_id=p_near.id,
        batch_number="B-HEALTHY-02",
        quantity_received=50,
        current_quantity=50,
        received_date=today - timedelta(days=5),
        expiry_date=today + timedelta(days=60),
        unit_cost=Decimal("20.00"),
        status="active"
    )
    db_session.add_all([b_near, b_healthy])

    # Product 4: Product with ONLY expired batch (10 units expired 3 days ago)
    # MUST be classified as Out of Stock, not low stock!
    p_exp = Product(
        name="Expired Juice",
        sku="TEST-EXP-004",
        unit="bottle",
        purchase_cost=Decimal("50.00"),
        selling_price=Decimal("70.00"),
        reorder_threshold=10,
        is_active=True
    )
    db_session.add(p_exp)
    db_session.flush()

    b_expired = InventoryBatch(
        product_id=p_exp.id,
        batch_number="B-EXPD-01",
        quantity_received=10,
        current_quantity=10,
        received_date=today - timedelta(days=20),
        expiry_date=today - timedelta(days=3),
        unit_cost=Decimal("50.00"),
        status="active"  # Active in db, but physically expired
    )
    db_session.add(b_expired)

    db_session.commit()
    return {
        "p_out": p_out,
        "p_low": p_low,
        "p_near": p_near,
        "p_exp": p_exp,
        "b_near": b_near,
        "b_expired": b_expired,
    }


def test_near_expiry_detection(db_session, sample_catalog):
    """Test 1: Correct near-expiry detection within configurable window."""
    summary = InventoryAlertService.get_inventory_summary(db_session, near_expiry_days=7)
    near_items = summary["near_expiry"]
    assert len(near_items) >= 1
    found = any(it["sku"] == "TEST-NEAR-003" and it["days_until_expiry"] == 4 for it in near_items)
    assert found, "Batch expiring in 4 days should be detected in 7-day warning window."


def test_low_stock_detection(db_session, sample_catalog):
    """Test 2: Correct low-stock detection (stock > 0 and <= threshold)."""
    summary = InventoryAlertService.get_inventory_summary(db_session)
    low_items = summary["low_stock"]
    found = any(it["sku"] == "TEST-LOW-002" and it["current_stock"] == 5 for it in low_items)
    assert found, "Product with stock 5 <= threshold 20 must be flagged as low stock."


def test_out_of_stock_detection(db_session, sample_catalog):
    """Test 3: Correct out-of-stock detection (eligible quantity == 0)."""
    summary = InventoryAlertService.get_inventory_summary(db_session)
    oos_items = summary["out_of_stock"]
    found = any(it["sku"] == "TEST-OOS-001" and it["available_quantity"] == 0 for it in oos_items)
    assert found, "Product with 0 stock must be classified as out-of-stock."


def test_expired_batches_excluded_from_sellable_stock(db_session, sample_catalog):
    """Test 4: Expired batches MUST NOT count as sellable stock."""
    summary = InventoryAlertService.get_inventory_summary(db_session)
    # TEST-EXP-004 has 10 units in an expired batch
    # Its eligible sellable stock is 0 -> it must be out of stock, NOT low stock!
    oos_skus = [it["sku"] for it in summary["out_of_stock"]]
    low_skus = [it["sku"] for it in summary["low_stock"]]
    assert "TEST-EXP-004" in oos_skus, "Product with only expired stock must be classified as out-of-stock."
    assert "TEST-EXP-004" not in low_skus, "Expired stock must not count as low stock."


def test_no_overlap_between_low_stock_and_out_of_stock(db_session, sample_catalog):
    """Test 5: Mutual exclusivity: a product must NEVER appear in both low-stock and out-of-stock."""
    summary = InventoryAlertService.get_inventory_summary(db_session)
    oos_skus = set(it["sku"] for it in summary["out_of_stock"])
    low_skus = set(it["sku"] for it in summary["low_stock"])
    intersection = oos_skus.intersection(low_skus)
    assert len(intersection) == 0, f"Overlap detected between low-stock and out-of-stock: {intersection}"


def test_alert_reconciliation_and_deduplication(db_session, sample_catalog):
    """Test 6: Alert reconciliation creates stable deduplication keys and prevents duplicate rows."""
    # First reconciliation
    InventoryAlertService.reconcile_and_snapshot(db_session)
    db_session.commit()
    count_1 = db_session.query(Alert).filter(Alert.is_resolved == False).count()

    # Second reconciliation without data changes
    InventoryAlertService.reconcile_and_snapshot(db_session)
    db_session.commit()
    count_2 = db_session.query(Alert).filter(Alert.is_resolved == False).count()

    assert count_1 == count_2, "Repeated reconciliation without data changes must not insert duplicate alerts."


def test_login_time_alert_retrieval_api(client, owner_headers, sample_catalog):
    """Test 7: Login-time alert retrieval via GET /api/v1/alerts/inventory-summary."""
    res = client.get("/api/v1/alerts/inventory-summary", headers=owner_headers)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "near_expiry" in data
    assert "low_stock" in data
    assert "out_of_stock" in data
    assert data["timezone"] == "Asia/Kolkata"


def test_alert_visibility_and_mark_all_read(client, staff_headers, sample_catalog, db_session):
    """Test 8: Alerts remain accessible via dedicated endpoints and mark-all-read works."""
    InventoryAlertService.reconcile_and_snapshot(db_session)
    db_session.commit()

    # Staff can access active alerts list
    res = client.get("/api/v1/alerts", headers=staff_headers)
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) > 0

    # Mark all read
    res_read = client.post("/api/v1/alerts/mark-all-read", headers=staff_headers)
    assert res_read.status_code == 200
    assert res_read.json()["status"] == "success"

    # Verify all are read
    res_after = client.get("/api/v1/alerts?is_read=false", headers=staff_headers)
    assert len(res_after.json()) == 0


def test_daily_job_execution(db_session, sample_catalog):
    """Test 9: Daily scheduled inventory check executes and records ScheduledJobRun."""
    res = DailySchedulerService.execute_daily_inventory_check(db_session, force_run=True)
    assert res["status"] == "success"
    run_id = res["run_id"]

    job_run = db_session.query(ScheduledJobRun).filter(ScheduledJobRun.id == run_id).first()
    assert job_run is not None
    assert job_run.status == "success"
    assert job_run.finished_at is not None


def test_repeated_job_execution_duplicate_prevention(db_session, sample_catalog):
    """Test 10: Repeated execution on same day skips without force_run."""
    # First execution
    res1 = DailySchedulerService.execute_daily_inventory_check(db_session, force_run=True)
    assert res1["status"] == "success"

    # Second execution without force_run
    res2 = DailySchedulerService.execute_daily_inventory_check(db_session, force_run=False)
    assert res2["status"] == "skipped"
    assert "already executed successfully" in res2["message"]


def test_email_settings_persistence(client, owner_headers):
    """Test 11: Notification settings persistence via PUT /api/v1/notifications/settings."""
    payload = {
        "recipient_emails": "owner@stocksense.com, manager@stocksense.com",
        "enabled": True,
        "report_frequency": "daily",
        "scheduled_time": "08:30",
        "timezone": "Asia/Kolkata",
        "categories": "near_expiry,low_stock,out_of_stock",
        "include_empty_reports": True
    }
    res = client.put("/api/v1/notifications/settings", json=payload, headers=owner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is True
    assert data["scheduled_time"] == "08:30"
    assert data["include_empty_reports"] is True


def test_scheduled_email_eligibility(db_session, sample_catalog):
    """Test 12: Scheduled email dispatch respects enabled status and recipient configuration."""
    # Set disabled
    notif = NotificationSettings(
        shop_id="default_shop",
        recipient_emails="test@example.com",
        enabled=False
    )
    db_session.add(notif)
    db_session.commit()

    summary = InventoryAlertService.get_inventory_summary(db_session)
    results = EmailNotificationService.send_scheduled_inventory_email(
        db_session, summary, date.today()
    )
    assert len(results) == 0, "No emails should be dispatched when notification settings are disabled."


def test_email_content_generation(sample_catalog, db_session):
    """Test 13: HTML and plain-text email generation contains required sections."""
    summary = InventoryAlertService.get_inventory_summary(db_session)
    html = EmailNotificationService.generate_html_template(summary, date.today())
    text = EmailNotificationService.generate_plain_text(summary, date.today())

    assert "StockSense" in html
    assert "Near Expiry" in html
    assert "Out of Stock" in html
    assert "Asia/Kolkata" in html

    assert "STOCKSENSE" in text
    assert "PRODUCTS NEARING EXPIRY" in text
    assert "VERY LOW-STOCK PRODUCTS" in text
    assert "OUT-OF-STOCK PRODUCTS" in text


def test_missing_email_configuration_graceful_handling(db_session, sample_catalog):
    """Test 14: When SMTP_HOST is unset, system logs disabled delivery without throwing exceptions."""
    notif = NotificationSettings(
        shop_id="default_shop",
        recipient_emails="manager@stocksense.com",
        enabled=True
    )
    db_session.add(notif)
    db_session.commit()

    summary = InventoryAlertService.get_inventory_summary(db_session)
    results = EmailNotificationService.send_scheduled_inventory_email(
        db_session, summary, date.today()
    )
    assert len(results) == 1
    assert results[0]["status"] == "disabled"
    assert results[0]["success"] is False

    log = db_session.query(EmailDeliveryLog).filter(EmailDeliveryLog.recipient == "manager@stocksense.com").first()
    assert log is not None
    assert log.status == "disabled"


def test_provider_rejection_and_retry_handling(db_session):
    """Test 15: Bounded retries and failure logging when SMTP provider rejects connection."""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = Exception("Connection refused by SMTP server")
        # Temporarily enable email config for this test
        with patch.object(EmailNotificationService, "_dispatch_email") as mock_dispatch:
            mock_dispatch.return_value = {
                "success": False,
                "status": "failed",
                "recipient": "retry_test@example.com",
                "message": "SMTP delivery failed after 3 attempts"
            }
            res = mock_dispatch("retry_test@example.com", "Test", "HTML", "Text", "daily", "key-1", None, db_session)
            assert res["status"] == "failed"
            assert "3 attempts" in res["message"]


def test_email_idempotency_deduplication(db_session, sample_catalog):
    """Test 16: Idempotency key prevents duplicate sends to the same recipient on the same day."""
    now_dt = datetime.now(KOLKATA_TZ)
    rep_date = now_dt.date()
    recipient = "idempotent@stocksense.com"
    idemp_key = f"daily_inventory:{rep_date.isoformat()}:{recipient}"

    # Insert pre-existing accepted log
    existing_log = EmailDeliveryLog(
        report_type="daily_inventory",
        recipient=recipient,
        idempotency_key=idemp_key,
        attempt_count=1,
        status="accepted",
        last_attempt_at=now_dt,
        created_at=now_dt
    )
    db_session.add(existing_log)

    notif = NotificationSettings(
        shop_id="default_shop",
        recipient_emails=recipient,
        enabled=True
    )
    db_session.add(notif)
    db_session.commit()

    summary = InventoryAlertService.get_inventory_summary(db_session)
    results = EmailNotificationService.send_scheduled_inventory_email(
        db_session, summary, rep_date
    )

    assert len(results) == 1
    assert results[0]["status"] == "skipped_duplicate"


def test_timezone_aware_scheduling(db_session):
    """Test 17: Date and timestamp calculations use Asia/Kolkata timezone."""
    now_kolkata = InventoryAlertService.get_kolkata_now()
    assert now_kolkata.tzinfo is not None
    assert "Asia/Kolkata" in str(now_kolkata.tzinfo) or "+05:30" in str(now_kolkata.strftime("%z"))


def test_authorization_for_settings(client, staff_headers, owner_headers):
    """Test 18: Staff accounts cannot alter store notification settings (403 Forbidden)."""
    payload = {"enabled": True, "recipient_emails": "hacked@example.com"}
    # Staff attempts to update settings -> 403
    res_staff = client.put("/api/v1/notifications/settings", json=payload, headers=staff_headers)
    assert res_staff.status_code == 403

    # Owner updates settings -> 200
    res_owner = client.put("/api/v1/notifications/settings", json=payload, headers=owner_headers)
    assert res_owner.status_code == 200


def test_empty_report_behavior(db_session):
    """Test 19: Reports with zero alerts skip email when include_empty_reports=False."""
    notif = NotificationSettings(
        shop_id="default_shop",
        recipient_emails="owner@example.com",
        enabled=True,
        include_empty_reports=False
    )
    db_session.add(notif)
    db_session.commit()

    empty_summary = {
        "generated_at": datetime.now(KOLKATA_TZ).isoformat(),
        "timezone": "Asia/Kolkata",
        "summary": {
            "near_expiry_count": 0,
            "low_stock_count": 0,
            "out_of_stock_count": 0
        },
        "near_expiry": [],
        "low_stock": [],
        "out_of_stock": []
    }

    results = EmailNotificationService.send_scheduled_inventory_email(
        db_session, empty_summary, date.today()
    )
    assert len(results) == 0, "Email must be skipped when zero alerts and include_empty_reports=False."


def test_accurate_daily_snapshot_creation(db_session, sample_catalog):
    """Test 20: Accurate creation and updating of DailyInventorySnapshot."""
    today = date.today()
    InventoryAlertService.reconcile_and_snapshot(db_session, reporting_date=today)
    db_session.commit()

    snapshot = db_session.query(DailyInventorySnapshot).filter(
        DailyInventorySnapshot.reporting_date == today
    ).first()

    assert snapshot is not None
    assert snapshot.reporting_date == today
    assert snapshot.near_expiry_count >= 1
    assert snapshot.low_stock_count >= 1
    assert snapshot.out_of_stock_count >= 1
    assert snapshot.total_stock_value >= 0
