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
    city_pollutant_timeseries,
)
from utils.charts import style_plotly_chart
from utils.exports import csv_download
from utils import filters
from i18n import t, col, export_label, translate_df
from ui import page_icon

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — City Drill-down",
    page_icon=page_icon("city_drilldown"),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title(t("drill.title"))
st.caption(t("drill.caption"))

exports = {}

try:
    # City selector
    df_cities = list_cities()
    cities = df_cities["city_name"].tolist() if not df_cities.empty else []
    if not cities:
        st.warning(t("common.no_cities"))
        st.stop()

    city = st.selectbox(t("common.select_city"), cities, key="city_dd_city")

    # ─── Local filters: period + pollutants ───
    with st.expander(t("common.filters"), expanded=False):
        period = filters.period_selector(key="dd_period", default="30d")
        filters.pollutants_multiselect(key="dd_pollutants")
    selected_pollutants = filters.selected("dd_pollutants")

    # ─── Row 1: Current AQI + City vs National ───
    col1, col2 = st.columns(2)

    # Panel 2.1 — Current AQI + Sparkline
    with col1:
        with st.container(border=True):
            st.subheader(t("drill.current_aqi_city", city=city))
            st.caption(t("drill.current_aqi_city_caption"))
            df_current = city_current_aqi(city)
            df_weekly = city_weekly_aqi(city)

            aqi_val = int(round(df_current["aqi"].iloc[0])) if not df_current.empty else 0
            st.metric(t("drill.right_now"), aqi_val)

            if not df_weekly.empty:
                fig = px.line(df_weekly, x="time", y="aqi", height=120,
                              title=t("common.trend_7d"),
                              labels={"time": col("time"), "aqi": col("aqi")})
                fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
                fig.update_traces(line=dict(color="#1E88E5", width=2))
                fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.5)
                st.plotly_chart(fig, use_container_width=True)

    # Panel 2.4 — City vs National
    with col2:
        with st.container(border=True):
            st.subheader(t("drill.vs_national", city=city))
            st.caption(t("drill.vs_national_caption"))
            df_comp = city_vs_national(city)
            if not df_comp.empty:
                fig = px.bar(df_comp, x="metric", y=["city_val", "national_val"],
                             barmode="group",
                             labels={"value": col("value"), "metric": col("metric"),
                                     "city_val": col("city_val"), "national_val": col("national_val")},
                             color_discrete_map={
                                 "city_val": "#1E88E5", "national_val": "#FF7043",
                             })
                fig.update_layout(legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    # ─── Row 2: Hourly Profile ───
    with st.container(border=True):
        st.subheader(t("drill.hourly_profile", city=city))
        st.caption(t("drill.hourly_profile_caption"))
        df_hourly = city_hourly_profile(city, period)
        exports["hourly_profile"] = df_hourly
        if not df_hourly.empty:
            fig = px.bar(df_hourly, x="hour", y=["avg_aqi", "avg_pm25", "avg_o3"],
                         barmode="group",
                         labels={"value": col("value"), "hour": t("common.hour_of_day"),
                                 "avg_aqi": col("avg_aqi"), "avg_pm25": col("avg_pm25"),
                                 "avg_o3": col("avg_o3")},
                         title=t("drill.avg_by_hour", period=period))
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Row 3: All Pollutants Time Series ───
    with st.expander(t("drill.all_pollutants"), expanded=False):
        st.caption(t("drill.all_pollutants_caption"))
        df_poll = city_all_pollutants(city, period)
        exports["all_pollutants"] = df_poll
        if not df_poll.empty:
            cols = filters.active_columns(selected_pollutants,
                                          ["pm2_5", "pm10", "no2", "o3", "so2", "co", "nh3"])
            labels = {c: col(c) for c in cols}
            labels["time"] = col("time")
            fig = px.line(df_poll, x="time", y=cols,
                          title=t("drill.all_pollutants_title", city=city), labels=labels)
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Pollutants vs WHO thresholds ───
    with st.container(border=True):
        st.subheader(t("drill.who_thresholds_city", city=city))
        st.caption(t("drill.who_thresholds_city_caption"))
        df_who = city_pollutant_timeseries(city, period)
        exports["pollutants_vs_who"] = df_who
        if not df_who.empty:
            poll_cols = filters.active_columns(
                selected_pollutants, ["pm2_5", "pm10", "no2", "o3"])
            labels = {"value": "µg/m³", "full_date": col("full_date"),
                      "variable": t("common.pollutant")}
            for c in poll_cols:
                labels[c] = col(c)
            fig = px.line(
                df_who, x="full_date", y=poll_cols,
                labels=labels,
                height=420,
            )
            thresholds = {"pm2_5": 15, "pm10": 45, "no2": 25, "o3": 100}
            colors = {"pm2_5": "#D81B60", "pm10": "#8E24AA", "no2": "#F4511E", "o3": "#1E88E5"}
            for c in poll_cols:
                thr = thresholds[c]
                fig.add_hline(
                    y=thr, line_dash="dash", line_color=colors[c], opacity=0.7,
                    annotation_text=t("drill.who_hline", pollutant=c.upper(), threshold=thr),
                )
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t("common.no_pollutant_data"))

    # ─── Row 4: Worst Episodes ───
    with st.expander(t("drill.worst_episodes"), expanded=False):
        st.caption(t("drill.worst_episodes_caption"))
        df_worst = city_worst_episodes(city, period)
        exports["worst_episodes"] = df_worst
        if not df_worst.empty:
            status_map = {"Alert": t("drill.status_alert"), "WHO PM2.5": t("drill.status_who_pm25")}
            display = df_worst.copy()
            display["status"] = df_worst["status"].map(lambda v: status_map.get(v, v))
            styled = display.style.map(
                lambda v: "color: red; font-weight: bold" if v == t("drill.status_alert")
                else ("color: orange" if v == t("drill.status_who_pm25") else ""),
                subset=["status"],
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)
        else:
            st.success(t("drill.no_bad_episodes"))

    # ─── Exports ───
    with st.expander(t("common.export_csv"), expanded=False):
        for key, df in exports.items():
            csv_download(df, export_label(key), f"{key}.csv")
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
