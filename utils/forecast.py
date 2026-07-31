"""AQI forecasting helpers.

Primary: statsmodels ARIMA (if available). Fallback: a simple moving-average
trend model so the page never breaks when statsmodels is missing.
"""

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.arima.model import ARIMA
    _HAS_STATSMODELS = True
except ImportError:  # pragma: no cover - exercised only on minimal installs
    _HAS_STATSMODELS = False


def _moving_average_forecast(values, horizon, window=7):
    """Simple fallback: last-window mean with growing uncertainty."""
    if len(values) == 0:
        return [], [], []
    base = float(np.mean(values[-window:]))
    sd = float(np.std(values[-window:])) if len(values) >= window else max(base * 0.2, 0.1)
    forecasts, lowers, uppers = [], [], []
    for step in range(1, horizon + 1):
        forecasts.append(base)
        # Uncertainty widens with the forecast horizon.
        spread = sd * (1 + 0.25 * step)
        lowers.append(max(base - spread, 0.0))
        uppers.append(base + spread)
    return forecasts, lowers, uppers


def _arima_forecast(values, horizon):
    """ARIMA(2,1,2) fit + prediction with confidence intervals."""
    model = ARIMA(values, order=(2, 1, 2))
    fitted = model.fit()
    fc = fitted.get_forecast(steps=horizon)
    mean = np.asarray(fc.predicted_mean).ravel()
    ci = fc.conf_int(alpha=0.2)
    lowers = np.maximum(np.asarray(ci[:, 0]).ravel(), 0.0)
    uppers = np.asarray(ci[:, 1]).ravel()
    return mean.tolist(), lowers.tolist(), uppers.tolist()


def forecast_aqi(history, horizon=7):
    """Forecast the next `horizon` days.

    Parameters
    ----------
    history : pd.DataFrame with 'full_date' (date-like) and 'daily_avg'.
    horizon : int, number of days to forecast ahead.

    Returns
    -------
    pd.DataFrame with columns forecast_date, forecast, lower, upper.
    """
    if history is None or history.empty:
        return pd.DataFrame(columns=["forecast_date", "forecast", "lower", "upper"])

    data = history.sort_values("full_date").copy()
    values = data["daily_avg"].astype(float).tolist()
    last_date = pd.to_datetime(data["full_date"].iloc[-1])

    if len(values) < 3:
        return pd.DataFrame(columns=["forecast_date", "forecast", "lower", "upper"])

    if _HAS_STATSMODELS and len(values) >= 7:
        try:
            forecasts, lowers, uppers = _arima_forecast(values, horizon)
        except Exception:
            # Convergence or rank issues → graceful fallback.
            forecasts, lowers, uppers = _moving_average_forecast(values, horizon)
    else:
        forecasts, lowers, uppers = _moving_average_forecast(values, horizon)

    dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon)
    return pd.DataFrame({
        "forecast_date": dates.date,
        "forecast": [round(v, 2) for v in forecasts],
        "lower": [round(v, 2) for v in lowers],
        "upper": [round(v, 2) for v in uppers],
    })
