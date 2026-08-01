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
from utils import filters
from utils.forecast import forecast_aqi
from i18n import t, col, translate_df
from ui import page_icon

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — AQI Forecast",
    page_icon=page_icon("forecast"),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title(t("forecast.title"))
st.caption(t("forecast.caption"))

try:
    cities = list_cities()
    if cities.empty:
        st.info(t("common.no_cities_avail"))
        st.stop()

    city = st.selectbox(t("common.select_city"), cities["city_name"].tolist(), key="forecast_city")
    horizon = filters.horizon_selector(key="forecast_horizon", default=7)

    history = city_daily_aqi(city, days=60)

    if len(history) < 3:
        st.info(t("forecast.no_history"))
        st.stop()

    forecast = forecast_aqi(history, horizon=horizon)

    if forecast.empty:
        st.info(t("forecast.no_history2"))
        st.stop()

    # ─── Forecast metrics ───
    trend = forecast["forecast"].tolist()
    direction = trend[-1] - trend[0]
    c1, c2, c3 = st.columns(3)
    c1.metric(t("forecast.next_days_avg", h=horizon), f"{sum(trend) / len(trend):.2f}")
    c2.metric(t("forecast.day_h", h=horizon), f"{trend[-1]:.2f}")
    c3.metric(
        t("forecast.trend_metric"),
        t("forecast.improving") if direction < -0.2 else
        t("forecast.worsening") if direction > 0.2 else t("forecast.stable"),
    )

    # ─── Chart: history + forecast ───
    with st.container(border=True, key="panel_forecast_chart"):
        st.subheader(t("forecast.history_forecast", city=city))
        st.caption(t("forecast.history_forecast_caption", h=horizon))
        hist = history.copy()
        hist["full_date"] = pd.to_datetime(hist["full_date"])
        hist = hist.dropna(subset=["daily_avg"])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist["full_date"], y=hist["daily_avg"],
            mode="lines", name=t("forecast.history"), line=dict(color="#1E88E5", width=2),
        ))
        fc_dates = pd.to_datetime(forecast["forecast_date"])
        fig.add_trace(go.Scatter(
            x=fc_dates, y=forecast["forecast"],
            mode="lines+markers", name=t("forecast.forecast_series"),
            line=dict(color="#D81B60", width=2, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=fc_dates.tolist() + fc_dates[::-1].tolist(),
            y=forecast["upper"].tolist() + forecast["lower"][::-1],
            fill="toself", fillcolor="rgba(216,27,96,0.12)",
            line=dict(color="rgba(255,255,255,0)"), name=t("forecast.ci"), showlegend=True,
        ))
        fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.6,
                      annotation_text=t("common.alert_threshold"))
        fig = style_plotly_chart(fig)
        st.plotly_chart(fig, use_container_width=True)

    # ─── Forecast table ───
    with st.container(border=True, key="panel_forecast_table"):
        st.subheader(t("forecast.details"))
        st.dataframe(translate_df(forecast), use_container_width=True, hide_index=True)
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
