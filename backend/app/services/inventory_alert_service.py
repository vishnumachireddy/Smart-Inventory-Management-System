import os
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app.core.config import settings
from app.models import (
    Product,
    InventoryBatch,
    StockMovement,
    Alert,
    SaleItem,
    DailyInventorySnapshot,
    AppSetting,
)
from app.services.cache_service import data_cache

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


class InventoryAlertService:
    """
    Comprehensive business logic for calculating, reconciling, and snapshotting
    inventory alerts with strict FEFO segregation, Asia/Kolkata timezone support,
    and mutual exclusivity between low-stock and out-of-stock classifications.
    """

    @classmethod
    def get_kolkata_now(cls) -> datetime:
        return datetime.now(KOLKATA_TZ)

    @classmethod
    def get_kolkata_today(cls) -> date:
        return datetime.now(KOLKATA_TZ).date()

    @classmethod
    def get_configured_near_expiry_days(cls, db: Session) -> int:
        setting = db.query(AppSetting).filter(AppSetting.key == "near_expiry_warning_days").first()
        if setting and setting.value.isdigit():
            return int(setting.value)
        return settings.DEFAULT_NEAR_EXPIRY_DAYS  # Default 7 days

    @classmethod
    def get_inventory_summary(cls, db: Session, near_expiry_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Derives the current inventory alert state directly from the database.
        Returns the structured summary for login-time modal and dedicated alerts views.
        """
        kolkata_now = cls.get_kolkata_now()
        today = kolkata_now.date()
        warning_days = near_expiry_days or cls.get_configured_near_expiry_days(db)
        cache_key = f"inventory_summary_{warning_days}"
        cached = data_cache.get(cache_key)
        if cached:
            return cached

        near_expiry_cutoff = today + timedelta(days=warning_days)

        products = db.query(Product).filter(Product.is_active == True).all()

        near_expiry_items: List[Dict[str, Any]] = []
        low_stock_items: List[Dict[str, Any]] = []
        out_of_stock_items: List[Dict[str, Any]] = []
        expired_items: List[Dict[str, Any]] = []

        from app.models import Sale
        thirty_days_ago = today - timedelta(days=30)
        sales_demand_query = (
            db.query(SaleItem.product_id, func.sum(SaleItem.quantity).label("total_sold"))
            .join(Sale, Sale.id == SaleItem.sale_id)
            .filter(Sale.created_at >= datetime.combine(thirty_days_ago, datetime.min.time(), tzinfo=KOLKATA_TZ))
            .group_by(SaleItem.product_id)
            .all()
        )
        sales_demand_map = {row.product_id: float(row.total_sold or 0) / 30.0 for row in sales_demand_query}

        # Pre-load all positive quantity batches in one single query
        all_active_batches = (
            db.query(InventoryBatch)
            .filter(InventoryBatch.current_quantity > 0)
            .all()
        )
        batch_map: Dict[int, List[InventoryBatch]] = {}
        for b in all_active_batches:
            batch_map.setdefault(b.product_id, []).append(b)

        # Pre-load recent stock movements in one query for out-of-stock lookup
        recent_movements = (
            db.query(StockMovement)
            .order_by(desc(StockMovement.created_at))
            .limit(100)
            .all()
        )
        movement_map: Dict[int, StockMovement] = {}
        for m in recent_movements:
            if m.product_id not in movement_map:
                movement_map[m.product_id] = m

        for prod in products:
            all_batches = batch_map.get(prod.id, [])

            # Segregate batches: expired batches must NEVER count towards eligible sellable stock
            eligible_batches = []
            for b in all_batches:
                if b.status != "active":
                    continue
                if b.expiry_date is not None and b.expiry_date < today:
                    # Expired batch
                    expired_items.append({
                        "id": f"expired:{b.id}",
                        "product_id": prod.id,
                        "product_name": prod.name,
                        "sku": prod.sku,
                        "batch_id": b.id,
                        "batch_number": b.batch_number,
                        "remaining_quantity": b.current_quantity,
                        "expiry_date": b.expiry_date.isoformat(),
                        "days_overdue": (today - b.expiry_date).days,
                        "severity": "critical",
                        "recommended_action": "Quarantine and remove expired units immediately from store shelves.",
                    })
                else:
                    eligible_batches.append(b)
                    # Check if near expiry
                    if b.expiry_date is not None and today <= b.expiry_date <= near_expiry_cutoff:
                        days_left = (b.expiry_date - today).days
                        is_urgent = days_left <= 3
                        near_expiry_items.append({
                            "id": f"near_expiry:{b.id}",
                            "product_id": prod.id,
                            "product_name": prod.name,
                            "sku": prod.sku,
                            "batch_id": b.id,
                            "batch_number": b.batch_number,
                            "remaining_quantity": b.current_quantity,
                            "expiry_date": b.expiry_date.isoformat(),
                            "days_until_expiry": days_left,
                            "severity": "critical" if is_urgent else "warning",
                            "recommended_action": (
                                "Apply 30-50% markdown or bundle immediately."
                                if is_urgent
                                else "Prioritize FEFO sale order; place on promotional shelf."
                            ),
                        })

            # Calculate total eligible sellable quantity
            eligible_stock = sum(b.current_quantity for b in eligible_batches)
            avg_demand = round(sales_demand_map.get(prod.id, 0.5), 1)

            # MUTUALLY EXCLUSIVE CLASSIFICATION:
            # 1. Out of stock: eligible_stock == 0
            # 2. Low stock: eligible_stock > 0 and eligible_stock <= reorder_threshold
            if eligible_stock == 0:
                last_movement = movement_map.get(prod.id)
                last_mov_str = (
                    f"{last_movement.created_at.astimezone(KOLKATA_TZ).strftime('%d %b %Y')} ({last_movement.movement_type.replace('_', ' ').title()})"
                    if last_movement
                    else "No prior movements recorded"
                )

                lead_time = prod.supplier.lead_time_days if prod.supplier else 5
                out_of_stock_items.append({
                    "id": f"out_of_stock:{prod.id}",
                    "product_id": prod.id,
                    "product_name": prod.name,
                    "sku": prod.sku,
                    "available_quantity": 0,
                    "reorder_threshold": prod.reorder_threshold,
                    "last_stock_movement": last_mov_str,
                    "severity": "critical",
                    "recommended_action": f"Urgent replenishment required. Supplier lead time is {lead_time} days.",
                })
            elif eligible_stock <= prod.reorder_threshold:
                target_reorder = max(prod.reorder_threshold * 2, int(avg_demand * 14))
                suggested_qty = max(1, target_reorder - eligible_stock)

                low_stock_items.append({
                    "id": f"low_stock:{prod.id}",
                    "product_id": prod.id,
                    "product_name": prod.name,
                    "sku": prod.sku,
                    "current_stock": eligible_stock,
                    "reorder_threshold": prod.reorder_threshold,
                    "avg_daily_demand": avg_demand,
                    "suggested_reorder_qty": suggested_qty,
                    "severity": "critical" if eligible_stock <= (prod.reorder_threshold // 2) else "warning",
                    "recommended_action": f"Order {suggested_qty} {prod.unit}s to prevent complete stockout.",
                })

        # Sort items by severity and urgency
        near_expiry_items.sort(key=lambda x: (x["days_until_expiry"], x["remaining_quantity"]))
        low_stock_items.sort(key=lambda x: (x["current_stock"] / max(1, x["reorder_threshold"])))
        out_of_stock_items.sort(key=lambda x: x["product_name"])

        result = {
            "generated_at": kolkata_now.isoformat(),
            "timezone": "Asia/Kolkata",
            "warning_window_days": warning_days,
            "summary": {
                "near_expiry_count": len(near_expiry_items),
                "low_stock_count": len(low_stock_items),
                "out_of_stock_count": len(out_of_stock_items),
                "expired_count": len(expired_items),
            },
            "near_expiry": near_expiry_items,
            "low_stock": low_stock_items,
            "out_of_stock": out_of_stock_items,
            "expired": expired_items,
        }
        data_cache.set(cache_key, result, ttl_seconds=30)
        return result

    @classmethod
    def reconcile_and_snapshot(
        cls,
        db: Session,
        reporting_date: Optional[date] = None,
        job_run_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Reconciles the alerts table in PostgreSQL, marking resolved alerts,
        upserting active alerts with stable deduplication keys, and storing
        a dated DailyInventorySnapshot.
        """
        data_cache.invalidate("inventory_summary")
        summary_data = cls.get_inventory_summary(db)
        kolkata_now = cls.get_kolkata_now()
        rep_date = reporting_date or kolkata_now.date()

        active_dedup_keys = set()

        # 1. Process Near-Expiry Alerts
        for it in summary_data["near_expiry"]:
            key = it["id"]
            active_dedup_keys.add(key)
            alert = db.query(Alert).filter(Alert.deduplication_key == key).first()
            if not alert:
                alert = Alert(
                    product_id=it["product_id"],
                    batch_id=it["batch_id"],
                    alert_type="near_expiry",
                    severity=it["severity"],
                    message=f"Batch {it['batch_number']} expires in {it['days_until_expiry']} days. {it['remaining_quantity']} units remaining. {it['recommended_action']}",
                    relevant_stock_quantity=float(it["remaining_quantity"]),
                    relevant_expiry_date=datetime.strptime(it["expiry_date"], "%Y-%m-%d").date(),
                    status="active",
                    is_read=False,
                    is_resolved=False,
                    first_detected_at=kolkata_now,
                    last_checked_at=kolkata_now,
                    deduplication_key=key,
                )
                db.add(alert)
            else:
                alert.last_checked_at = kolkata_now
                alert.relevant_stock_quantity = float(it["remaining_quantity"])
                alert.status = "active"
                alert.is_resolved = False
                alert.resolved_at = None

        # 2. Process Low-Stock Alerts
        for it in summary_data["low_stock"]:
            key = it["id"]
            active_dedup_keys.add(key)
            alert = db.query(Alert).filter(Alert.deduplication_key == key).first()
            if not alert:
                alert = Alert(
                    product_id=it["product_id"],
                    batch_id=None,
                    alert_type="low_stock",
                    severity=it["severity"],
                    message=f"Stock at {it['current_stock']} units (Threshold: {it['reorder_threshold']}). {it['recommended_action']}",
                    relevant_stock_quantity=float(it["current_stock"]),
                    relevant_expiry_date=None,
                    status="active",
                    is_read=False,
                    is_resolved=False,
                    first_detected_at=kolkata_now,
                    last_checked_at=kolkata_now,
                    deduplication_key=key,
                )
                db.add(alert)
            else:
                alert.last_checked_at = kolkata_now
                alert.relevant_stock_quantity = float(it["current_stock"])
                alert.status = "active"
                alert.is_resolved = False
                alert.resolved_at = None

        # 3. Process Out-Of-Stock Alerts
        for it in summary_data["out_of_stock"]:
            key = it["id"]
            active_dedup_keys.add(key)
            alert = db.query(Alert).filter(Alert.deduplication_key == key).first()
            if not alert:
                alert = Alert(
                    product_id=it["product_id"],
                    batch_id=None,
                    alert_type="out_of_stock",
                    severity="critical",
                    message=f"Product is completely OUT OF STOCK. Last movement: {it['last_stock_movement']}. {it['recommended_action']}",
                    relevant_stock_quantity=0.0,
                    relevant_expiry_date=None,
                    status="active",
                    is_read=False,
                    is_resolved=False,
                    first_detected_at=kolkata_now,
                    last_checked_at=kolkata_now,
                    deduplication_key=key,
                )
                db.add(alert)
            else:
                alert.last_checked_at = kolkata_now
                alert.relevant_stock_quantity = 0.0
                alert.status = "active"
                alert.is_resolved = False
                alert.resolved_at = None

        # 4. Resolve alerts that are no longer active
        unresolved_alerts = db.query(Alert).filter(
            Alert.is_resolved == False,
            Alert.deduplication_key.isnot(None)
        ).all()

        for a in unresolved_alerts:
            if a.deduplication_key not in active_dedup_keys:
                a.is_resolved = True
                a.status = "resolved"
                a.resolved_at = kolkata_now

        # 5. Snapshot computation
        # Compute stock valuation
        all_active_batches = db.query(InventoryBatch).filter(
            InventoryBatch.current_quantity > 0,
            InventoryBatch.status == "active"
        ).all()
        total_val = sum(Decimal(str(b.current_quantity)) * b.unit_cost for b in all_active_batches)

        # Sales for reporting date
        start_day = datetime.combine(rep_date, datetime.min.time(), tzinfo=KOLKATA_TZ)
        end_day = datetime.combine(rep_date, datetime.max.time(), tzinfo=KOLKATA_TZ)

        from app.models import Sale
        sales_today = db.query(Sale).filter(
            Sale.created_at >= start_day,
            Sale.created_at <= end_day,
            Sale.status == "completed"
        ).all()

        sales_cnt = len(sales_today)
        revenue_val = sum(s.total_amount for s in sales_today) if sales_today else Decimal("0.00")
        profit_val = sum(s.gross_profit for s in sales_today) if sales_today else Decimal("0.00")

        summary_text = (
            f"Daily inventory snapshot for {rep_date.isoformat()}: "
            f"{summary_data['summary']['near_expiry_count']} products nearing expiry, "
            f"{summary_data['summary']['low_stock_count']} low-stock items, "
            f"{summary_data['summary']['out_of_stock_count']} out-of-stock items. "
            f"Total Inventory Value: {settings.CURRENCY_SYMBOL}{total_val:,.2f}."
        )

        snapshot = db.query(DailyInventorySnapshot).filter(DailyInventorySnapshot.reporting_date == rep_date).first()
        if not snapshot:
            snapshot = DailyInventorySnapshot(
                reporting_date=rep_date,
                near_expiry_count=summary_data["summary"]["near_expiry_count"],
                low_stock_count=summary_data["summary"]["low_stock_count"],
                out_of_stock_count=summary_data["summary"]["out_of_stock_count"],
                total_stock_value=total_val,
                sales_count=sales_cnt,
                revenue=revenue_val,
                gross_profit=profit_val,
                summary_text=summary_text,
                generation_timestamp=kolkata_now,
            )
            db.add(snapshot)
        else:
            snapshot.near_expiry_count = summary_data["summary"]["near_expiry_count"]
            snapshot.low_stock_count = summary_data["summary"]["low_stock_count"]
            snapshot.out_of_stock_count = summary_data["summary"]["out_of_stock_count"]
            snapshot.total_stock_value = total_val
            snapshot.sales_count = sales_cnt
            snapshot.revenue = revenue_val
            snapshot.gross_profit = profit_val
            snapshot.summary_text = summary_text
            snapshot.generation_timestamp = kolkata_now

        db.flush()
        return summary_data
