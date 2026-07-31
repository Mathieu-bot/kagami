"""Dashboard 8 — Alerts History (public).

Past alert episodes (AQI >= 3): counts per city, worst episodes, and a
detailed log of recent alerts.
"""

import streamlit as st
import plotly.express as px

from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import alert_episodes, alert_summary
from utils.charts import style_plotly_chart

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Alerts History",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title("🚨 Alerts History")
st.caption("_Past episodes where AQI reached alert level (≥ 3)_")

try:
    days = st.selectbox("Period", [30, 90, 180, 365], index=1,
                        format_func=lambda d: f"Last {d} days",
                        key="alerts_days")

    df_episodes = alert_episodes(days)
    df_summary = alert_summary(days)

    if df_episodes.empty:
        st.success("✅ No alert episodes in this period — great air quality!")
        st.stop()

    # ─── Key metrics ───
    c1, c2, c3 = st.columns(3)
    c1.metric("🚨 Total Alerts", len(df_episodes))
    worst = df_episodes.iloc[0]
    c2.metric("🔥 Worst Episode", f"AQI {worst['aqi']}", f"{worst['city_name']} · {worst['full_date']}")
    c3.metric("🏙️ Cities Affected", df_episodes["city_name"].nunique())

    # ─── Alerts per city ───
    if not df_summary.empty:
        with st.container(border=True):
            st.subheader("📊 Alerts per City")
            fig = px.bar(
                df_summary, x="city_name", y="alert_count",
                color="max_aqi", color_continuous_scale=["yellow", "orange", "red"],
                labels={"city_name": "", "alert_count": "Alerts", "max_aqi": "Worst AQI"},
                text="alert_count", height=380,
            )
            fig.update_traces(textposition="outside")
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Recent episodes table ───
    with st.container(border=True):
        st.subheader("🗒️ Recent Episodes")
        recent = df_episodes.head(100).copy()
        st.dataframe(recent, use_container_width=True, hide_index=True)
except DatabaseError as e:
    st.error(f"❌ Database error: {e}")
