import math
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Sale, SaleItem, Product, ForecastRecord


class ForecastingPipeline:

    @staticmethod
    def get_product_daily_sales(
        db: Session,
        product_id: int,
        lookback_days: int = 90,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Aggregates daily sales quantity for a specific product over the lookback window.
        Includes zero-sales days by reindexing across the complete continuous date range.
        """
        if end_date is None:
            end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        # Query sales for product
        query = (
            db.query(
                func.date(Sale.created_at).label("sale_date"),
                func.sum(SaleItem.quantity).label("daily_qty")
            )
            .join(SaleItem, SaleItem.sale_id == Sale.id)
            .filter(
                SaleItem.product_id == product_id,
                Sale.status == "completed",
                func.date(Sale.created_at) >= start_date,
                func.date(Sale.created_at) <= end_date
            )
            .group_by(func.date(Sale.created_at))
            .all()
        )

        # Build full date range
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        sales_map = {row.sale_date: float(row.daily_qty) for row in query}

        df = pd.DataFrame(index=date_range)
        df["date"] = df.index.date
        df["quantity"] = df["date"].map(lambda d: sales_map.get(d, 0.0))
        df["day_of_week"] = df.index.dayofweek
        return df

    @staticmethod
    def run_moving_average_forecast(
        df: pd.DataFrame,
        window: int = 7,
        horizon_days: int = 7
    ) -> Dict[str, Any]:
        """
        Computes Moving Average baseline with out-of-sample backtesting validation.
        Enforces non-negative demand constraints.
        """
        n_obs = len(df)
        if n_obs == 0:
            return {
                "model_name": "Moving Average (Baseline)",
                "historical_observations": 0,
                "daily_average": 0.0,
                "predicted_daily": 0.0,
                "predictions": [0.0] * horizon_days,
                "mae": 0.0,
                "rmse": 0.0,
                "status": "no_data"
            }

        daily_quantities = df["quantity"].values
        overall_mean = float(np.mean(daily_quantities))

        # Backtesting evaluation using last horizon_days if sufficient history exists
        mae = None
        rmse = None
        if n_obs >= (window + horizon_days):
            train_series = daily_quantities[:-horizon_days]
            actual_test = daily_quantities[-horizon_days:]

            # Roll moving average
            val_preds = []
            cur_history = list(train_series)
            for _ in range(horizon_days):
                pred_val = float(np.mean(cur_history[-window:]))
                val_preds.append(max(0.0, pred_val))
                cur_history.append(pred_val)

            mae = float(np.mean(np.abs(np.array(actual_test) - np.array(val_preds))))
            rmse = float(np.sqrt(np.mean((np.array(actual_test) - np.array(val_preds)) ** 2)))

        # Future forecast
        recent_window = daily_quantities[-window:] if n_obs >= window else daily_quantities
        predicted_daily = max(0.0, float(np.mean(recent_window)))
        predictions = [round(predicted_daily, 2) for _ in range(horizon_days)]

        return {
            "model_name": f"Moving Average ({min(window, n_obs)}-day window)",
            "historical_observations": n_obs,
            "daily_average": round(overall_mean, 2),
            "predicted_daily": round(predicted_daily, 2),
            "predictions": predictions,
            "mae": round(mae, 3) if mae is not None else None,
            "rmse": round(rmse, 3) if rmse is not None else None,
            "status": "success"
        }

    @staticmethod
    def run_random_forest_forecast(
        df: pd.DataFrame,
        horizon_days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        Advanced ML Regressor leveraging lag features and rolling statistics.
        Employs strict time-ordered train/test splits to prevent future data leakage.
        """
        n_obs = len(df)
        # Require at least 21 days for meaningful feature generation and time-split
        if n_obs < 21:
            return None

        # Feature Engineering
        feat_df = df.copy()
        feat_df["lag_1"] = feat_df["quantity"].shift(1)
        feat_df["lag_2"] = feat_df["quantity"].shift(2)
        feat_df["lag_7"] = feat_df["quantity"].shift(7)
        feat_df["rolling_mean_7"] = feat_df["quantity"].shift(1).rolling(7, min_periods=1).mean()
        feat_df["rolling_std_7"] = feat_df["quantity"].shift(1).rolling(7, min_periods=1).std().fillna(0)
        feat_df = feat_df.dropna()

        if len(feat_df) < 14:
            return None

        feature_cols = ["day_of_week", "lag_1", "lag_2", "lag_7", "rolling_mean_7", "rolling_std_7"]
        X = feat_df[feature_cols]
        y = feat_df["quantity"]

        # Time-ordered split (80% train, 20% test)
        split_idx = int(len(feat_df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        if len(X_test) == 0:
            return None

        rf = RandomForestRegressor(n_estimators=60, max_depth=6, random_state=42)
        rf.fit(X_train, y_train)

        # Evaluate on test set
        test_preds = rf.predict(X_test)
        test_preds = np.clip(test_preds, a_min=0, a_max=None)
        mae = float(mean_absolute_error(y_test, test_preds))
        rmse = float(root_mean_squared_error(y_test, test_preds))

        # Iterative recursive forecast for horizon_days
        recent_quantities = list(df["quantity"].values)
        future_preds = []
        last_date = df.index[-1]

        for step in range(1, horizon_days + 1):
            next_date = last_date + timedelta(days=step)
            dow = next_date.dayofweek
            l1 = recent_quantities[-1]
            l2 = recent_quantities[-2] if len(recent_quantities) >= 2 else l1
            l7 = recent_quantities[-7] if len(recent_quantities) >= 7 else l1
            r_mean = float(np.mean(recent_quantities[-7:]))
            r_std = float(np.std(recent_quantities[-7:]))

            step_features = pd.DataFrame([{
                "day_of_week": dow,
                "lag_1": l1,
                "lag_2": l2,
                "lag_7": l7,
                "rolling_mean_7": r_mean,
                "rolling_std_7": r_std
            }])

            p = max(0.0, float(rf.predict(step_features)[0]))
            future_preds.append(round(p, 2))
            recent_quantities.append(p)

        return {
            "model_name": "Random Forest Regressor",
            "historical_observations": n_obs,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "predicted_daily": round(float(np.mean(future_preds)), 2),
            "predictions": future_preds,
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "status": "success"
        }
