"""Dashboard 5 — Inter-city comparison (public).

Side-by-side view of current AQI and the 7-day trend for all cities.
"""

import streamlit as st
import plotly.express as px

from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import comparison_current, comparison_trend_7d
from utils.charts import style_plotly_chart

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — City Comparison",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title("⚖️ City Comparison")
st.caption("_How do cities compare right now and over the last week?_")

try:
    df_current = comparison_current()
    df_trend = comparison_trend_7d()

    if df_current.empty and df_trend.empty:
        st.info("No data available yet.")
        st.stop()

    # ─── Key metrics ───
    if not df_current.empty:
        best = df_current.iloc[-1]
        worst = df_current.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("🟢 Best Air", f"{best['city_name']}", f"AQI {best['current_aqi']}")
        c2.metric("🔴 Worst Air", f"{worst['city_name']}", f"AQI {worst['current_aqi']}")
        c3.metric("🏙️ Cities", len(df_current))

    # ─── Current AQI bar chart ───
    if not df_current.empty:
        with st.container(border=True):
            st.subheader("📊 Current AQI by City")
            fig = px.bar(
                df_current, x="city_name", y="current_aqi",
                color="current_aqi", color_continuous_scale=["green", "yellow", "orange", "red"],
                labels={"city_name": "", "current_aqi": "Current AQI"},
                text="current_aqi", height=380,
            )
            fig.update_traces(texttemplate="%{text}", textposition="outside")
            fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.6,
                          annotation_text="Alert Threshold (AQI ≥ 3)")
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── 7-day trend multi-line ───
    if not df_trend.empty:
        with st.container(border=True):
            st.subheader("📈 7-Day AQI Trend")
            fig = px.line(
                df_trend, x="full_date", y="avg_aqi", color="city_name",
                markers=True,
                labels={"full_date": "Date", "avg_aqi": "Average AQI", "city_name": ""},
                height=420,
            )
            fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.6,
                          annotation_text="Alert Threshold")
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Ranking table ───
    if not df_current.empty:
        with st.container(border=True):
            st.subheader("🏆 Ranking")
            st.dataframe(
                df_current.reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )
except DatabaseError as e:
    st.error(f"❌ Database error: {e}")
