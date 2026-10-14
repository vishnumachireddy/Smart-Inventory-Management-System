from datetime import date, datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Alert, Product, InventoryBatch, AppSetting
from app.core.config import settings


class AlertService:

    @staticmethod
    def get_configured_near_expiry_days(db: Session) -> int:
        setting = db.query(AppSetting).filter(AppSetting.key == "near_expiry_days").first()
        if setting and setting.value.isdigit():
            return int(setting.value)
        return settings.DEFAULT_NEAR_EXPIRY_DAYS

    @staticmethod
    def reconcile_all_alerts(db: Session, current_date: Optional[date] = None) -> Dict[str, int]:
        """
        Reconciles the entire alert state against database inventory realities:
        - Creates missing alerts.
        - Resolves obsolete alerts whose triggering conditions no longer exist.
        - Deduplicates repeated alerts.
        Returns a dictionary of counts.
        """
        if current_date is None:
            current_date = date.today()

        near_expiry_days = AlertService.get_configured_near_expiry_days(db)
        
        low_stock_generated = 0
        near_expiry_generated = 0
        expired_generated = 0
        resolved_count = 0

        # --- 1. Low Stock Alerts ---
        products = db.query(Product).filter(Product.is_active == True).all()
        for prod in products:
            # Calculate total eligible stock
            eligible_batches = db.query(InventoryBatch).filter(
                InventoryBatch.product_id == prod.id,
                InventoryBatch.current_quantity > 0,
                InventoryBatch.status == "active",
                (InventoryBatch.expiry_date == None) | (InventoryBatch.expiry_date >= current_date)
            ).all()

            total_stock = sum(b.current_quantity for b in eligible_batches)

            existing_alert = db.query(Alert).filter(
                Alert.product_id == prod.id,
                Alert.alert_type == "low_stock",
                Alert.is_resolved == False
            ).first()

            if total_stock <= prod.reorder_threshold:
                severity = "critical" if total_stock == 0 else "warning"
                msg = (
                    f"Product '{prod.name}' (SKU: {prod.sku}) is at or below reorder threshold: "
                    f"{total_stock} {prod.unit} available (Threshold: {prod.reorder_threshold})."
                )
                if not existing_alert:
                    alert = Alert(
                        product_id=prod.id,
                        alert_type="low_stock",
                        severity=severity,
                        message=msg,
                        is_read=False,
                        is_resolved=False,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(alert)
                    low_stock_generated += 1
                else:
                    # Update message and severity if stock changed
                    existing_alert.message = msg
                    existing_alert.severity = severity
            else:
                # Resolved condition
                if existing_alert:
                    existing_alert.is_resolved = True
                    existing_alert.resolved_at = datetime.now(timezone.utc)
                    resolved_count += 1

        # --- 2. Near-Expiry & Expired Batch Alerts ---
        batches = db.query(InventoryBatch).filter(
            InventoryBatch.current_quantity > 0,
            InventoryBatch.expiry_date != None
        ).all()

        for batch in batches:
            days_left = (batch.expiry_date - current_date).days
            prod = batch.product

            if days_left < 0:
                # Expired Batch Alert
                batch.status = "expired"
                existing_expired = db.query(Alert).filter(
                    Alert.batch_id == batch.id,
                    Alert.alert_type == "expired",
                    Alert.is_resolved == False
                ).first()

                if not existing_expired:
                    msg = (
                        f"Batch {batch.batch_number} of '{prod.name}' expired on {batch.expiry_date}! "
                        f"{batch.current_quantity} {prod.unit} remaining must be quarantined or discarded."
                    )
                    alert = Alert(
                        product_id=batch.product_id,
                        batch_id=batch.id,
                        alert_type="expired",
                        severity="critical",
                        message=msg,
                        is_read=False,
                        is_resolved=False,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(alert)
                    expired_generated += 1

                # If it had a near_expiry alert, resolve it
                old_near = db.query(Alert).filter(
                    Alert.batch_id == batch.id,
                    Alert.alert_type == "near_expiry",
                    Alert.is_resolved == False
                ).first()
                if old_near:
                    old_near.is_resolved = True
                    old_near.resolved_at = datetime.now(timezone.utc)
                    resolved_count += 1

            elif 0 <= days_left <= near_expiry_days:
                # Near Expiry Batch Alert
                existing_near = db.query(Alert).filter(
                    Alert.batch_id == batch.id,
                    Alert.alert_type == "near_expiry",
                    Alert.is_resolved == False
                ).first()

                severity = "critical" if days_left <= 7 else "warning"
                msg = (
                    f"Batch {batch.batch_number} of '{prod.name}' expires in {days_left} day(s) on {batch.expiry_date}. "
                    f"Available stock: {batch.current_quantity} {prod.unit}."
                )

                if not existing_near:
                    alert = Alert(
                        product_id=batch.product_id,
                        batch_id=batch.id,
                        alert_type="near_expiry",
                        severity=severity,
                        message=msg,
                        is_read=False,
                        is_resolved=False,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(alert)
                    near_expiry_generated += 1
                else:
                    existing_near.message = msg
                    existing_near.severity = severity

            else:
                # Stock is healthy and far from expiry; resolve any stale near_expiry alerts
                stale_alert = db.query(Alert).filter(
                    Alert.batch_id == batch.id,
                    Alert.alert_type == "near_expiry",
                    Alert.is_resolved == False
                ).first()
                if stale_alert:
                    stale_alert.is_resolved = True
                    stale_alert.resolved_at = datetime.now(timezone.utc)
                    resolved_count += 1

        db.flush()
        return {
            "low_stock_generated": low_stock_generated,
            "near_expiry_generated": near_expiry_generated,
            "expired_generated": expired_generated,
            "resolved_count": resolved_count
        }
