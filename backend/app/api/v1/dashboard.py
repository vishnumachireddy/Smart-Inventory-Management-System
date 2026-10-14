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


@router.get("/bundle")
def get_dashboard_bundle(
    trend_days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """
    Returns full precomputed dashboard data bundle in a single network round-trip.
    Drastically reduces WAN latency across remote serverless databases.
    """
    kpis = AnalyticsService.get_dashboard_summary(db)
    trends = AnalyticsService.get_sales_trends(db, days=trend_days)
    categories = AnalyticsService.get_category_distribution(db)
    top_products = AnalyticsService.get_top_selling_products(db, limit=5, days=30)
    expiry_risk = AnalyticsService.get_expiry_risk_summary(db)

    return {
        "kpis": kpis,
        "trends": trends,
        "categories": categories,
        "top_products": top_products,
        "expiry_risk": expiry_risk
    }
