"""Dashboard 2 — City Drill-down: 5 panels per city (standalone page)."""

import streamlit as st
import plotly.express as px
from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import (
    list_cities,
    city_current_aqi,
    city_weekly_aqi,
    city_hourly_profile,
    city_all_pollutants,
    city_vs_national,
    city_worst_episodes,
)
from utils.charts import style_plotly_chart

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — City Drill-down",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title("🏙️ City Drill-down")
st.caption("_Detailed analysis for a specific city_")

try:
    # City selector
    df_cities = list_cities()
    cities = df_cities["city_name"].tolist() if not df_cities.empty else []
    if not cities:
        st.warning("No cities found in database")
        st.stop()

    city = st.selectbox("Select City", cities, key="city_dd_city")
    period = st.session_state.get("period", "30d")

    # ─── Row 1: Current AQI + City vs National ───
    col1, col2 = st.columns(2)

    # Panel 2.1 — Current AQI + Sparkline
    with col1:
        with st.container(border=True):
            st.subheader(f"🌤️ Current AQI — {city}")
            df_current = city_current_aqi(city)
            df_weekly = city_weekly_aqi(city)

            aqi_val = int(df_current["aqi"].iloc[0]) if not df_current.empty else 0
            st.metric("Right Now", aqi_val)

            if not df_weekly.empty:
                fig = px.line(df_weekly, x="time", y="aqi", height=120,
                              title="7-day Trend")
                fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
                fig.update_traces(line=dict(color="#1E88E5", width=2))
                fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.5)
                st.plotly_chart(fig, use_container_width=True)

    # Panel 2.4 — City vs National
    with col2:
        with st.container(border=True):
            st.subheader(f"⚖️ {city} vs National Average")
            df_comp = city_vs_national(city)
            if not df_comp.empty:
                fig = px.bar(df_comp, x="metric", y=["city_val", "national_val"],
                             barmode="group",
                             labels={"value": "Value", "metric": "Metric"},
                             color_discrete_map={
                                 "city_val": "#1E88E5", "national_val": "#FF7043",
                             })
                fig.update_layout(legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    # ─── Row 2: Hourly Profile ───
    with st.container(border=True):
        st.subheader(f"🕐 Hourly Profile — {city}")
        df_hourly = city_hourly_profile(city, period)
        if not df_hourly.empty:
            fig = px.bar(df_hourly, x="hour", y=["avg_aqi", "avg_pm25", "avg_o3"],
                         barmode="group",
                         labels={"value": "Average", "hour": "Hour of Day"},
                         title=f"Average pollutant levels by hour (last {period})")
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Row 3: All Pollutants Time Series ───
    with st.expander("📈 All Pollutants — Time Series", expanded=False):
        df_poll = city_all_pollutants(city, period)
        if not df_poll.empty:
            cols = ["pm2_5", "pm10", "no2", "o3", "so2", "co", "nh3"]
            fig = px.line(df_poll, x="time", y=cols, title=f"All Pollutants — {city}")
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Row 4: Worst Episodes ───
    with st.expander("⚠️ Worst Episodes", expanded=False):
        df_worst = city_worst_episodes(city, period)
        if not df_worst.empty:
            styled = df_worst.style.map(
                lambda v: "color: red; font-weight: bold" if v == "Alert"
                else ("color: orange" if v == "WHO PM2.5" else ""),
                subset=["status"],
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No bad episodes in this period!")
except DatabaseError as e:
    st.error(f"❌ Database error: {e}")
