from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.deps import require_staff_or_owner
from app.models import Alert, User, Product, InventoryBatch
from app.schemas import AlertResponse
from app.services.alert_service import AlertService

router = APIRouter()


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
        current_stock=alert.batch.current_quantity if alert.batch else None,
        expiry_date=alert.batch.expiry_date if alert.batch else None
    )


@router.get("", response_model=List[AlertResponse])
def list_alerts(
    alert_type: Optional[str] = Query(None, description="Filter by: low_stock, near_expiry, expired"),
    severity: Optional[str] = Query(None, description="Filter by: info, warning, critical"),
    is_resolved: Optional[bool] = Query(False, description="Filter by resolution state"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves alerts with filtering and resolution status."""
    query = db.query(Alert)

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)

    alerts = query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
    return [enrich_alert_response(a) for a in alerts]


@router.post("/reconcile")
def trigger_alert_reconciliation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Triggers complete reconciliation of active alerts against current inventory realities."""
    result = AlertService.reconcile_all_alerts(db)
    db.commit()
    return {
        "status": "success",
        "message": "Alert reconciliation completed successfully",
        "details": result
    }


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
    db.commit()
    db.refresh(alert)
    return enrich_alert_response(alert)


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
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return enrich_alert_response(alert)
