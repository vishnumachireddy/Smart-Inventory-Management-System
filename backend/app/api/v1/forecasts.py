from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_owner
from app.models import Product, User
from app.schemas import ForecastResponse, ForecastDataPoint, ModelEvaluationResponse
from app.forecasting.pipeline import ForecastingPipeline

router = APIRouter()


@router.get("/evaluation", response_model=ModelEvaluationResponse)
def evaluate_models(
    product_id: Optional[int] = Query(None, description="Optional product to evaluate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """
    Evaluates forecasting algorithms comparing Moving Average against Random Forest
    using out-of-sample MAE and RMSE metrics.
    """
    # Pick a product with most sales history if not specified
    if not product_id:
        prod = db.query(Product).filter(Product.is_active == True).first()
        if not prod:
            raise HTTPException(status_code=404, detail="No active products found to evaluate")
        product_id = prod.id

    df = ForecastingPipeline.get_product_daily_sales(db, product_id, lookback_days=90)
    baseline_eval = ForecastingPipeline.run_moving_average_forecast(df, window=7, horizon_days=7)
    rf_eval = ForecastingPipeline.run_random_forest_forecast(df, horizon_days=7)

    summary = (
        f"Evaluated on {len(df)} daily observations. "
        f"Baseline Moving Average MAE: {baseline_eval.get('mae', 'N/A')}. "
    )
    if rf_eval:
        summary += f"Random Forest Regressor MAE: {rf_eval.get('mae')}, RMSE: {rf_eval.get('rmse')}."
    else:
        summary += "Random Forest not eligible due to limited training data (<21 observations)."

    return ModelEvaluationResponse(
        baseline_moving_average=baseline_eval,
        advanced_random_forest=rf_eval,
        comparison_summary=summary
    )


@router.get("/{product_id}", response_model=ForecastResponse)
def get_product_forecast(
    product_id: int,
    horizon_days: int = Query(7, ge=1, le=30, description="Forecast horizon in days"),
    model_type: str = Query("auto", description="Model: auto, moving_average, random_forest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """
    Generates dynamic future demand estimates for a specific product.
    Returns historical trend points, future predictions, and validation error metrics.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    df = ForecastingPipeline.get_product_daily_sales(db, product_id, lookback_days=90)
    n_obs = len(df)

    # Determine model
    rf_result = None
    if model_type in ("auto", "random_forest"):
        rf_result = ForecastingPipeline.run_random_forest_forecast(df, horizon_days=horizon_days)

    if model_type == "random_forest" and not rf_result:
        # Fallback explanation
        chosen_result = ForecastingPipeline.run_moving_average_forecast(df, window=7, horizon_days=horizon_days)
        active_model = f"Moving Average Fallback (RF insufficient data: {n_obs} records)"
    elif rf_result and (model_type == "random_forest" or (rf_result.get("mae") is not None and rf_result.get("mae") < (ForecastingPipeline.run_moving_average_forecast(df, 7, horizon_days).get("mae") or 999))):
        chosen_result = rf_result
        active_model = "Random Forest Regressor"
    else:
        chosen_result = ForecastingPipeline.run_moving_average_forecast(df, window=7, horizon_days=horizon_days)
        active_model = chosen_result["model_name"]

    # Assemble timeline
    timeline: List[ForecastDataPoint] = []
    
    # 1. Recent actual history (last 14 days)
    history_slice = df.tail(14)
    for row_date, row in history_slice.iterrows():
        timeline.append(
            ForecastDataPoint(
                date=str(row_date.date()),
                predicted_demand=float(row["quantity"]),
                is_forecast=False,
                actual_demand=float(row["quantity"])
            )
        )

    # 2. Future predictions
    predictions = chosen_result.get("predictions", [0.0] * horizon_days)
    last_date = df.index[-1].date() if n_obs > 0 else date.today()
    for i, p_val in enumerate(predictions):
        f_date = last_date + timedelta(days=i + 1)
        timeline.append(
            ForecastDataPoint(
                date=str(f_date),
                predicted_demand=p_val,
                is_forecast=True,
                actual_demand=None
            )
        )

    insights = (
        f"Based on {n_obs} days of historical records. Average daily velocity is "
        f"{chosen_result.get('daily_average', chosen_result.get('predicted_daily', 0.0))} {product.unit}. "
        f"Model: {active_model}. MAE: {chosen_result.get('mae', 'N/A')}."
    )

    return ForecastResponse(
        product_id=product.id,
        product_name=product.name,
        sku=product.sku,
        model_type=active_model,
        horizon_days=horizon_days,
        historical_periods=n_obs,
        daily_average_demand=chosen_result.get("daily_average", chosen_result.get("predicted_daily", 0.0)),
        mae=chosen_result.get("mae"),
        rmse=chosen_result.get("rmse"),
        forecast=timeline,
        insights=insights
    )


@router.get("", response_model=List[ForecastResponse])
def list_forecasts(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Returns demand forecasts across multiple active products."""
    products = db.query(Product).filter(Product.is_active == True).limit(limit).all()
    results = []
    for prod in products:
        f = get_product_forecast(
            product_id=prod.id,
            horizon_days=7,
            model_type="auto",
            db=db,
            current_user=current_user
        )
        results.append(f)
    return results
