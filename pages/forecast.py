"""Dashboard 11 — AQI Forecast (public).

7-day AQI forecast per city using ARIMA (with a moving-average fallback).
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import list_cities, city_daily_aqi
from utils.charts import style_plotly_chart
from utils.forecast import forecast_aqi

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — AQI Forecast",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title("🔮 AQI Forecast")
st.caption("_7-day AQI forecast per city (ARIMA, with moving-average fallback)_")

try:
    cities = list_cities()
    if cities.empty:
        st.info("No cities available.")
        st.stop()

    city = st.selectbox("City", cities["city_name"].tolist(), key="forecast_city")

    history = city_daily_aqi(city, days=60)

    if len(history) < 3:
        st.info("Not enough history to forecast yet — data is still accumulating.")
        st.stop()

    forecast = forecast_aqi(history, horizon=7)

    if forecast.empty:
        st.info("Not enough history to forecast yet.")
        st.stop()

    # ─── Forecast metrics ───
    trend = forecast["forecast"].tolist()
    direction = trend[-1] - trend[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("🔮 Next 7d Avg", f"{sum(trend) / len(trend):.2f}")
    c2.metric("📅 Day 7", f"{trend[-1]:.2f}")
    c3.metric(
        "📈 Trend",
        "Improving 📉" if direction < -0.2 else
        "Worsening 📈" if direction > 0.2 else "Stable ➡️",
    )

    # ─── Chart: history + forecast ───
    with st.container(border=True):
        st.subheader(f"📈 History + Forecast — {city}")
        hist = history.copy()
        hist["full_date"] = pd.to_datetime(hist["full_date"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist["full_date"], y=hist["daily_avg"],
            mode="lines", name="History", line=dict(color="#1E88E5", width=2),
        ))
        fc_dates = pd.to_datetime(forecast["forecast_date"])
        fig.add_trace(go.Scatter(
            x=fc_dates, y=forecast["forecast"],
            mode="lines+markers", name="Forecast", line=dict(color="#D81B60", width=2, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=fc_dates.tolist() + fc_dates[::-1].tolist(),
            y=forecast["upper"].tolist() + forecast["lower"][::-1],
            fill="toself", fillcolor="rgba(216,27,96,0.12)",
            line=dict(color="rgba(255,255,255,0)"), name="80% CI", showlegend=True,
        ))
        fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.6,
                      annotation_text="Alert Threshold (AQI ≥ 3)")
        fig = style_plotly_chart(fig)
        st.plotly_chart(fig, use_container_width=True)

    # ─── Forecast table ───
    with st.container(border=True):
        st.subheader("🗓️ Forecast Details")
        st.dataframe(forecast, use_container_width=True, hide_index=True)
except DatabaseError as e:
    st.error(f"❌ Database error: {e}")
