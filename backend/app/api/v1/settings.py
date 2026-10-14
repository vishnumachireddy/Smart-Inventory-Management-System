from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_owner, require_shop_owner
from app.models import AppSetting, User
from app.schemas import AppSettingResponse, AppSettingUpdate
from app.services.alert_service import AlertService

router = APIRouter()


@router.get("", response_model=List[AppSettingResponse])
def get_app_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves all application configuration parameters."""
    defaults = [
        ("near_expiry_days", "30", "Days before expiry date to trigger near-expiry warnings"),
        ("currency_code", "INR", "Display currency code"),
        ("currency_symbol", "₹", "Display currency symbol"),
        ("default_lead_time_days", "7", "Default supplier replenishment lead time"),
        ("shop_name", "StockSense Demo Store", "Display name of the retail store"),
    ]

    for key, default_val, desc in defaults:
        existing = db.query(AppSetting).filter(AppSetting.key == key).first()
        if not existing:
            setting = AppSetting(key=key, value=default_val, description=desc)
            db.add(setting)

    db.commit()
    return db.query(AppSetting).order_by(AppSetting.key.asc()).all()


@router.put("/{key}", response_model=AppSettingResponse)
def update_app_setting(
    key: str,
    setting_in: AppSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Updates an application setting (Shop Owner only)."""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        setting = AppSetting(key=key, value=setting_in.value, description=setting_in.description)
        db.add(setting)
    else:
        setting.value = setting_in.value
        if setting_in.description:
            setting.description = setting_in.description

    db.commit()
    db.refresh(setting)

    if key == "near_expiry_days":
        AlertService.reconcile_all_alerts(db)

    return setting
