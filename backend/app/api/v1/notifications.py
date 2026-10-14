from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.deps import require_shop_owner
from app.models import NotificationSettings, EmailDeliveryLog, User
from app.schemas import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    TestEmailRequest,
    EmailDeliveryLogResponse,
)
from app.services.email_service import EmailNotificationService

router = APIRouter()
KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


@router.get("/settings", response_model=NotificationSettingsResponse)
def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Retrieves the store's email notification and scheduling settings."""
    notif = db.query(NotificationSettings).filter(NotificationSettings.shop_id == "default_shop").first()
    if not notif:
        notif = NotificationSettings(
            user_id=current_user.id,
            shop_id="default_shop",
            recipient_emails="",
            enabled=False,
            report_frequency="daily",
            scheduled_time="08:00",
            timezone="Asia/Kolkata",
            categories="near_expiry,low_stock,out_of_stock,sales_summary",
            include_empty_reports=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
    return notif


@router.put("/settings", response_model=NotificationSettingsResponse)
def update_notification_settings(
    payload: NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Updates notification recipients, frequency, schedule time, and categories."""
    notif = db.query(NotificationSettings).filter(NotificationSettings.shop_id == "default_shop").first()
    if not notif:
        notif = NotificationSettings(
            user_id=current_user.id,
            shop_id="default_shop"
        )
        db.add(notif)

    if payload.recipient_emails is not None:
        # Validate recipient emails format
        emails = [e.strip() for e in payload.recipient_emails.split(",") if e.strip()]
        for em in emails:
            if "@" not in em or "." not in em:
                raise HTTPException(status_code=400, detail=f"Invalid email address: {em}")
        notif.recipient_emails = payload.recipient_emails

    if payload.enabled is not None:
        notif.enabled = payload.enabled
    if payload.report_frequency is not None:
        if payload.report_frequency not in ("daily", "weekly", "both"):
            raise HTTPException(status_code=400, detail="report_frequency must be 'daily', 'weekly', or 'both'")
        notif.report_frequency = payload.report_frequency
    if payload.scheduled_time is not None:
        notif.scheduled_time = payload.scheduled_time
    if payload.timezone is not None:
        notif.timezone = payload.timezone
    if payload.categories is not None:
        notif.categories = payload.categories
    if payload.include_empty_reports is not None:
        notif.include_empty_reports = payload.include_empty_reports

    notif.user_id = current_user.id
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/test-email")
def trigger_test_email(
    payload: TestEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Dispatches a test email to verify SMTP configuration and logs the attempt."""
    result = EmailNotificationService.send_test_email(db=db, recipient_email=payload.recipient_email)
    return result


@router.get("/delivery-logs", response_model=List[EmailDeliveryLogResponse])
def list_email_delivery_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Retrieves delivery audit logs for dispatched inventory emails."""
    logs = (
        db.query(EmailDeliveryLog)
        .order_by(desc(EmailDeliveryLog.created_at))
        .limit(limit)
        .all()
    )
    return logs
