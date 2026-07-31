"""Air Quality Madagascar — HQ Overview (home page).

Navigation via sidebar page links (st.page_link) — URL-based, no radio buttons.
Protected by Caddy reverse proxy with Basic Auth / OAuth.
Roles: viewer (default), analyst, admin.
"""

import streamlit as st
import plotly.express as px
from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import (
    aqi_today,
    aqi_yesterday,
    aqi_today_sparkline,
    cities_in_alert,
    data_completeness,
    days_without_alert,
    aqi_evolution,
    air_quality_map,
    aqi_distribution,
    worst_pollutant,
    who_exceedance_rate,
    pipeline_status,
    last_ingestion,
)
from utils.charts import style_plotly_chart, aqi_level_label
from utils.exports import csv_download
from i18n import t, col, export_label

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Air Quality Madagascar",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Auth + Sidebar ───
init_session_state()
render_sidebar()

exports = {}

try:
    # ─── Page content ───
    st.title(t("hq.title"))
    st.caption(t("hq.caption"))

    period = st.session_state.get("period", "7d")

    # ─── Row 1: Key Metrics ───
    col1, col2, col3, col4 = st.columns(4)

    # Panel 1.1 — AQI Today
    with col1:
        df_aqi = aqi_today()
        df_yest = aqi_yesterday()
        df_spark = aqi_today_sparkline()
        aqi_val = round(df_aqi["avg_aqi"].iloc[0], 2) if not df_aqi.empty else 0
        yest_val = round(df_yest["yesterday_avg"].iloc[0], 2) if not df_yest.empty else 0
        delta = round(aqi_val - yest_val, 2)
        with st.container(border=True):
            st.metric(t("hq.aqi_today"), aqi_val, delta=delta)
            if not df_spark.empty:
                fig = px.line(df_spark, x="time", y="avg_aqi", height=60)
                fig.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                    xaxis_visible=False, yaxis_visible=False,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                )
                fig.update_traces(line=dict(color="#1E88E5", width=2))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Panel 1.2 — Cities in Alert
    with col2:
        df_alert = cities_in_alert()
        alert_count = int(df_alert["alert_count"].iloc[0]) if not df_alert.empty else 0
        st.metric(t("hq.cities_in_alert"), alert_count)

    # Panel 1.4 — Data Completeness
    with col3:
        df_comp = data_completeness()
        comp = df_comp["completeness"].iloc[0] if not df_comp.empty else 0
        st.metric(t("hq.data_completeness"), f"{comp}%")

    # Panel 1.5 — Days Without Alert
    with col4:
        df_days = days_without_alert()
        days = int(df_days["days_without_alert"].iloc[0]) if not df_days.empty else 0
        st.metric(t("hq.days_without_alert"), days)

    # ─── Row 2: Time Series + Map ───
    col1, col2 = st.columns([3, 2])

    # Panel 1.7 — AQI Evolution
    with col1:
        with st.container(border=True):
            st.subheader(t("hq.aqi_evolution"))
            df_ts = aqi_evolution(period)
            exports["aqi_evolution"] = df_ts
            if not df_ts.empty:
                fig = px.line(df_ts, x="full_date", y=["daily_avg", "trend"],
                              labels={"value": col("aqi"), "variable": t("hq.measure"),
                                      "full_date": col("full_date"),
                                      "daily_avg": col("daily_avg"), "trend": col("trend")})
                fig.data[1].update(line=dict(color="orange", width=3))
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    # Panel 1.8 — Air Quality Map
    with col2:
        with st.container(border=True):
            st.subheader(t("hq.aqi_map"))
            df_map = air_quality_map()
            exports["air_quality_map"] = df_map
            if not df_map.empty:
                fig = px.scatter_map(
                    df_map, lat="latitude", lon="longitude",
                    size="aqi", color="aqi", hover_name="city_name",
                    hover_data={"status": True, "latitude": False, "longitude": False},
                    labels={"city_name": col("city_name"), "status": col("status"),
                            "aqi": col("aqi")},
                    color_continuous_scale=["green", "yellow", "orange", "red"],
                    zoom=5, center={"lat": -18.9, "lon": 47.5},
                    map_style="open-street-map", height=350,
                )
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)

    # ─── Row 3: Distribution + WHO ───
    col1, col2 = st.columns(2)

    # Panel 1.9 — AQI Distribution
    with col1:
        with st.container(border=True):
            st.subheader(t("hq.aqi_distribution"))
            df_dist = aqi_distribution(period)
            exports["aqi_distribution"] = df_dist
            if not df_dist.empty:
                df_dist["level"] = df_dist["aqi"].apply(aqi_level_label)
                colors = ["#00E400", "#FFFF00", "#FF7E00", "#FF0000", "#7E0023"]
                fig = px.bar(df_dist, x="level", y="count", color="aqi",
                             color_continuous_scale=colors, text="percentage",
                             labels={"count": t("hq.measurements"), "level": t("hq.aqi_level")})
                fig.update_traces(texttemplate="%{text}%", textposition="outside")
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    # Panel 1.3 — Worst Pollutant
    with col2:
        with st.container(border=True):
            st.subheader(t("hq.worst_pollutant"))
            df_who = worst_pollutant(period)
            if not df_who.empty:
                row = df_who.iloc[0]
                st.metric(
                    f"⚠️ {row['pollutant']}",
                    f"{row['value']} µg/m³",
                    delta=t("hq.pct_of_who", pct=row["pct"], thr=row["who_threshold"]),
                )
                pct = min(float(row["pct"]), 100)
                st.progress(pct / 100, text=t("hq.pct_of_who_threshold", pct=pct))
            else:
                st.info(t("common.no_data"))

    # ─── Row 4: WHO Exceedance + Pipeline ───
    col1, col2 = st.columns(2)

    # Panel 1.6 — WHO Exceedance Rate
    with col1:
        with st.container(border=True):
            st.subheader(t("hq.who_exceedance"))
            df_exc = who_exceedance_rate(period)
            if not df_exc.empty:
                rate = df_exc["exceedance_rate"].iloc[0]
                color = "green" if rate < 5 else ("yellow" if rate < 10 else "red")
                st.metric(t("hq.readings_exceeding"), f"{rate}%")
                st.progress(min(rate, 100) / 100)

    # Panel 1.10 — Pipeline Health
    with col2:
        with st.container(border=True):
            st.subheader(t("hq.pipeline_health"))
            df_status = pipeline_status()
            df_last = last_ingestion()
            if not df_status.empty:
                status_emoji = {"Up to date": "🟢", "Delayed": "🟡", "Critical": "🔴"}
                status_label = {
                    "Up to date": t("hq.status_up_to_date"),
                    "Delayed": t("hq.status_delayed"),
                    "Critical": t("hq.status_critical"),
                }
                row = df_status.iloc[0]
                st.metric(col("status"),
                          f"{status_emoji.get(row['status'], '❓')} {status_label.get(row['status'], row['status'])}")
            if not df_last.empty:
                st.caption(t("common.last_record", ts=df_last["last_record"].iloc[0]))

    # ─── Exports ───
    with st.expander(t("common.export_csv"), expanded=False):
        for key, df in exports.items():
            csv_download(df, export_label(key), f"{key}.csv")
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
