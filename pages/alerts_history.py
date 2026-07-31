"""Dashboard 8 — Alerts History + Control Room (public).

Live per-city status with auto-refresh (control room), plus the history
of past alert episodes (AQI >= 3): counts per city, worst episodes, and
a detailed log of recent alerts.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import alert_episodes, alert_summary, control_room_status, list_cities
from utils.charts import style_plotly_chart, render_city_badges, rename_traces, set_hover_template
from utils import filters
from i18n import t, col, translate_df
from ui import page_icon

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Alerts History",
    page_icon=page_icon("alerts_history"),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title(t("alerts.title"))
st.caption(t("alerts.caption"))


@st.fragment(run_every=30)
def control_room():
    """Live per-city status badges, auto-refreshed every 30 seconds."""
    st.subheader(t("alerts.control_title"))
    st.caption(t("alerts.control_caption"))
    try:
        df_live = control_room_status()
    except DatabaseError as e:
        st.error(t("common.db_error", msg=e))
        return
    if df_live.empty:
        st.info(t("alerts.no_control_data"))
        return
    render_city_badges(df_live, show_freshness=True)


try:
    control_room()

    # ─── Local filters: days + severity + cities ───
    with st.expander(t("common.filters"), expanded=False):
        days = st.selectbox(t("common.period"), [30, 90, 180, 365], index=1,
                            format_func=lambda d: t("alerts.last_days", d=d),
                            key="alerts_days")
        severity = st.selectbox(
            t("alerts.severity"),
            ["all", "Alert", "Severe"],
            index=0,
            key="alerts_severity",
            format_func=lambda s: t("alerts.severity_all") if s == "all"
            else (t("alerts.level_alert") if s == "Alert" else t("alerts.level_severe")),
        )
        df_city_opt = list_cities()
        city_options = df_city_opt["city_name"].tolist() if not df_city_opt.empty else []
        filters.cities_multiselect(city_options, key="alerts_cities")
    selected_cities = filters.selected("alerts_cities")

    df_episodes = alert_episodes(days)
    df_summary = alert_summary(days)

    # Apply page-local filters
    if isinstance(severity, str) and severity != "all" and not df_episodes.empty and "level" in df_episodes.columns:
        df_episodes = df_episodes[df_episodes["level"] == severity]
    if selected_cities and not df_episodes.empty and "city_name" in df_episodes.columns:
        df_episodes = df_episodes[df_episodes["city_name"].isin(selected_cities)]
    if selected_cities and not df_summary.empty and "city_name" in df_summary.columns:
        df_summary = df_summary[df_summary["city_name"].isin(selected_cities)]

    if df_episodes.empty:
        st.success(t("alerts.no_alerts"))
        st.stop()

    # ─── Key metrics ───
    c1, c2, c3 = st.columns(3)
    c1.metric(t("alerts.total_alerts"), len(df_episodes))
    worst = df_episodes.iloc[0]
    c2.metric(t("alerts.worst_episode"), f"AQI {worst['aqi']}", f"{worst['city_name']} · {worst['full_date']}")
    c3.metric(t("alerts.cities_affected"), df_episodes["city_name"].nunique())

    # ─── Alerts per city ───
    if not df_summary.empty:
        with st.container(border=True):
            st.subheader(t("alerts.alerts_per_city"))
            st.caption(t("alerts.alerts_per_city_caption"))
            fig = px.bar(
                df_summary, x="city_name", y="alert_count",
                color="max_aqi", color_continuous_scale=["yellow", "orange", "red"],
                labels={"city_name": col("city_name"), "alert_count": t("alerts.alerts"),
                        "max_aqi": t("alerts.worst_aqi")},
                text="alert_count", height=380,
            )
            fig.update_traces(textposition="outside")
            fig = style_plotly_chart(fig)
            set_hover_template(fig, fmt=".0f")
            st.plotly_chart(fig, use_container_width=True)

    # ─── Recent episodes table ───
    with st.container(border=True):
        st.subheader(t("alerts.recent_episodes"))
        st.caption(t("alerts.recent_episodes_caption"))
        recent = df_episodes.head(100).copy()
        st.dataframe(translate_df(recent), use_container_width=True, hide_index=True)
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
