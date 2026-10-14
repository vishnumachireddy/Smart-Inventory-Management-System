from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_owner
from app.models import User
from app.schemas import DashboardKPISummary
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary", response_model=DashboardKPISummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """
    Returns high-level business KPI metrics:
    - Active product counts
    - Total eligible units on hand
    - Low-stock and near-expiry batch counts
    - Today's revenue & sales volume
    - Estimated gross profit and total inventory valuation
    """
    return AnalyticsService.get_dashboard_summary(db)
