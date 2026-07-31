"""Dashboard 8 — Alerts History + Control Room (public).

Live per-city status with auto-refresh (control room), plus the history
of past alert episodes (AQI >= 3): counts per city, worst episodes, and
a detailed log of recent alerts.
"""

from datetime import datetime, timezone

import streamlit as st
import plotly.express as px
import pandas as pd

from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import alert_episodes, alert_summary, control_room_status
from utils.charts import style_plotly_chart, aqi_badge_color
from i18n import t, col, translate_df

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Alerts History",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title(t("alerts.title"))
st.caption(t("alerts.caption"))


def _freshness_label(ts) -> str:
    """Human-readable freshness of a reading timestamp."""
    if ts is None or (isinstance(ts, float) and pd.isna(ts)):
        return t("alerts.offline")
    parsed = pd.to_datetime(ts)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    minutes = int((datetime.now(timezone.utc) - parsed).total_seconds() / 60)
    if minutes < 2:
        return t("alerts.now")
    if minutes <= 120:
        return t("alerts.fresh_min", m=minutes)
    return t("alerts.offline")


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
    cols = st.columns(len(df_live))
    for badge, (_, row) in zip(cols, df_live.iterrows()):
        aqi = int(row["aqi"])
        color = aqi_badge_color(aqi)
        with badge:
            with st.container(border=True):
                st.markdown(f"**{row['city_name']}**")
                st.markdown(f":{color}[**AQI {aqi}**]")
                st.caption(_freshness_label(row["last_record"]))


try:
    control_room()
    days = st.selectbox(t("common.period"), [30, 90, 180, 365], index=1,
                        format_func=lambda d: t("alerts.last_days", d=d),
                        key="alerts_days")

    df_episodes = alert_episodes(days)
    df_summary = alert_summary(days)

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
            fig = px.bar(
                df_summary, x="city_name", y="alert_count",
                color="max_aqi", color_continuous_scale=["yellow", "orange", "red"],
                labels={"city_name": col("city_name"), "alert_count": t("alerts.alerts"),
                        "max_aqi": t("alerts.worst_aqi")},
                text="alert_count", height=380,
            )
            fig.update_traces(textposition="outside")
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Recent episodes table ───
    with st.container(border=True):
        st.subheader(t("alerts.recent_episodes"))
        recent = df_episodes.head(100).copy()
        st.dataframe(translate_df(recent), use_container_width=True, hide_index=True)
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
