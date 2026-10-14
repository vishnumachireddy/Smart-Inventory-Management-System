from datetime import date, timedelta
import pandas as pd
import pytest
from app.forecasting.pipeline import ForecastingPipeline


def test_moving_average_forecast_calculations():
    # Test 14: Verify moving average calculations
    # Synthetic daily sales: 14 days of data
    daily_values = [10.0, 12.0, 11.0, 15.0, 14.0, 16.0, 13.0, 12.0, 14.0, 15.0, 17.0, 16.0, 18.0, 15.0]
    dates = pd.date_range(end=date.today(), periods=14, freq="D")
    df = pd.DataFrame({"quantity": daily_values, "date": dates.date, "day_of_week": dates.dayofweek}, index=dates)

    # 7-day window forecast
    res = ForecastingPipeline.run_moving_average_forecast(df, window=7, horizon_days=7)
    assert res["status"] == "success"
    assert res["historical_observations"] == 14
    
    # Expected last 7 days: [12, 14, 15, 17, 16, 18, 15] -> sum = 107 / 7 = ~15.29
    assert abs(res["predicted_daily"] - 15.29) < 0.1
    assert len(res["predictions"]) == 7
    # Non-negative demand constraint
    assert all(p >= 0 for p in res["predictions"])


def test_forecast_insufficient_history():
    # Test 15: Forecast behavior with insufficient or zero history
    # Empty DataFrame
    empty_df = pd.DataFrame(columns=["quantity", "date", "day_of_week"])
    empty_res = ForecastingPipeline.run_moving_average_forecast(empty_df, window=7, horizon_days=7)
    assert empty_res["historical_observations"] == 0
    assert empty_res["predicted_daily"] == 0.0
    assert empty_res["predictions"] == [0.0] * 7

    # Minimal observations (2 days: [5.0, 10.0]) -> average is 7.5
    dates = pd.date_range(end=date.today(), periods=2, freq="D")
    small_df = pd.DataFrame({"quantity": [5.0, 10.0], "date": dates.date, "day_of_week": dates.dayofweek}, index=dates)
    small_res = ForecastingPipeline.run_moving_average_forecast(small_df, window=7, horizon_days=7)
    assert small_res["historical_observations"] == 2
    assert abs(small_res["predicted_daily"] - 7.5) < 0.01
