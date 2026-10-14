from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.core.database import get_db
from app.core.deps import require_staff_or_owner, require_shop_owner
from app.models import Alert, User, DailyInventorySnapshot, ScheduledJobRun
from app.schemas import (
    AlertResponse,
    InventoryAlertSummaryResponse,
    DailySnapshotResponse,
    ScheduledJobRunResponse,
)
from app.services.inventory_alert_service import InventoryAlertService
from app.services.daily_scheduler_service import DailySchedulerService

router = APIRouter()
KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


def enrich_alert_response(alert: Alert) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        product_id=alert.product_id,
        batch_id=alert.batch_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        is_read=alert.is_read,
        is_resolved=alert.is_resolved,
        created_at=alert.created_at,
        resolved_at=alert.resolved_at,
        product_name=alert.product.name if alert.product else None,
        sku=alert.product.sku if alert.product else None,
        batch_number=alert.batch.batch_number if alert.batch else None,
        current_stock=int(alert.relevant_stock_quantity) if alert.relevant_stock_quantity is not None else (alert.batch.current_quantity if alert.batch else None),
        expiry_date=alert.relevant_expiry_date if alert.relevant_expiry_date else (alert.batch.expiry_date if alert.batch else None)
    )


@router.get("/inventory-summary", response_model=InventoryAlertSummaryResponse)
def get_inventory_alert_summary(
    near_expiry_days: Optional[int] = Query(None, ge=1, le=90, description="Override warning threshold window in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """
    Returns the real-time calculated inventory alert summary for login-time
    modal dialogs and dedicated alert screens.
    """
    summary = InventoryAlertService.get_inventory_summary(db, near_expiry_days=near_expiry_days)
    return summary


@router.get("", response_model=List[AlertResponse])
def list_alerts(
    alert_type: Optional[str] = Query(None, description="Filter by: low_stock, out_of_stock, near_expiry, expired"),
    severity: Optional[str] = Query(None, description="Filter by: info, warning, critical"),
    is_resolved: Optional[bool] = Query(False, description="Filter by resolution state"),
    is_read: Optional[bool] = Query(None, description="Filter by read state"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves alerts with filtering and resolution status."""
    query = db.query(Alert).options(
        joinedload(Alert.product),
        joinedload(Alert.batch)
    )

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)
    if is_read is not None:
        query = query.filter(Alert.is_read == is_read)

    alerts = query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
    return [enrich_alert_response(a) for a in alerts]


@router.post("/reconcile")
def trigger_alert_reconciliation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """
    Triggers complete reconciliation of active alerts and updates the daily snapshot.
    """
    summary = InventoryAlertService.reconcile_and_snapshot(db)
    db.commit()
    return {
        "status": "success",
        "message": "Alert reconciliation completed successfully",
        "summary": summary["summary"],
        "generated_at": summary["generated_at"]
    }


@router.post("/run-daily-check")
def trigger_daily_check(
    force: bool = Query(True, description="Force execution even if already executed today"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """
    Manually triggers the daily automated inventory check, snapshotting, and email notifications.
    """
    result = DailySchedulerService.execute_daily_inventory_check(db=db, force_run=force)
    return result


@router.patch("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Marks an alert as read."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    alert.read_at = datetime.now(KOLKATA_TZ)
    db.commit()
    db.refresh(alert)
    return enrich_alert_response(alert)


@router.post("/mark-all-read")
def mark_all_alerts_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Marks all unread alerts as read."""
    now_dt = datetime.now(KOLKATA_TZ)
    count = db.query(Alert).filter(Alert.is_read == False).update({
        "is_read": True,
        "read_at": now_dt
    })
    db.commit()
    return {"status": "success", "marked_read_count": count}


@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
def mark_alert_resolved(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Manually marks an alert as resolved."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    alert.status = "resolved"
    alert.resolved_at = datetime.now(KOLKATA_TZ)
    db.commit()
    db.refresh(alert)
    return enrich_alert_response(alert)


@router.get("/snapshots", response_model=List[DailySnapshotResponse])
def list_daily_snapshots(
    limit: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves persisted daily inventory snapshots."""
    snapshots = (
        db.query(DailyInventorySnapshot)
        .order_by(desc(DailyInventorySnapshot.reporting_date))
        .limit(limit)
        .all()
    )
    return snapshots


@router.get("/job-runs", response_model=List[ScheduledJobRunResponse])
def list_job_runs(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Retrieves history of scheduled job executions."""
    runs = (
        db.query(ScheduledJobRun)
        .order_by(desc(ScheduledJobRun.started_at))
        .limit(limit)
        .all()
    )
    return runs
