"""Unit tests for the AQI forecasting helper."""

import pandas as pd
import pytest

from utils.forecast import forecast_aqi, _moving_average_forecast


def _history(n=30, base=1.5):
    dates = pd.date_range("2026-07-01", periods=n).date
    return pd.DataFrame({
        "full_date": dates,
        "daily_avg": [base + 0.02 * i for i in range(n)],
    })


def test_forecast_returns_horizon_rows():
    df = forecast_aqi(_history(), horizon=7)
    assert len(df) == 7
    assert list(df.columns) == ["forecast_date", "forecast", "lower", "upper"]


def test_forecast_dates_follow_history():
    df = forecast_aqi(_history(n=30), horizon=3)
    assert pd.to_datetime(df["forecast_date"].iloc[0]) == pd.Timestamp("2026-07-31")
    assert pd.to_datetime(df["forecast_date"].iloc[-1]) == pd.Timestamp("2026-08-02")


def test_forecast_empty_history():
    assert forecast_aqi(pd.DataFrame()).empty
    assert forecast_aqi(None).empty


def test_forecast_too_short_history():
    assert forecast_aqi(_history(n=2)).empty


def test_lower_upper_bounds_sane():
    df = forecast_aqi(_history(n=30), horizon=5)
    assert (df["lower"] <= df["forecast"]).all()
    assert (df["forecast"] <= df["upper"]).all()


def test_moving_average_fallback():
    values = list(range(10, 20, 2))
    fc, lo, hi = _moving_average_forecast(values, horizon=3, window=5)
    assert len(fc) == len(lo) == len(hi) == 3
    assert all(lo[i] <= fc[i] <= hi[i] for i in range(3))
