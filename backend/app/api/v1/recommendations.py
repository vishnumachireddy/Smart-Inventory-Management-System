from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_owner
from app.models import User
from app.schemas import ReorderRecommendation
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get("/reorder", response_model=List[ReorderRecommendation])
def get_reorder_recommendations(
    horizon_days: int = Query(14, ge=7, le=60, description="Planning horizon in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """
    Computes replenishment recommendations based on lead times, forecast velocity,
    safety stock formulas, and current eligible stock levels.
    """
    return RecommendationService.generate_reorder_recommendations(
        db=db,
        planning_horizon_days=horizon_days
    )
