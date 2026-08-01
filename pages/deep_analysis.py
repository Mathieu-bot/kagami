"""Dashboard 3 — Deep Analysis: Boxplot, Scatter, Heatmap, Correlation (standalone page)."""

import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np
from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import (
    list_cities,
    boxplot_data,
    scatter_data,
    heatmap_data,
    correlation_matrix,
    monthly_statistics,
    seasonal_analysis,
    weekday_weekend,
)
from utils.charts import style_plotly_chart
from utils.exports import csv_download
from utils import filters
from i18n import t, col, export_label
from ui import page_icon

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Deep Analysis",
    page_icon=page_icon("deep_analysis"),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title(t("deep.title"))
st.caption(t("deep.caption"))

exports = {}

try:
    # ─── Local filters: period + cities + pollutants ───
    with st.popover(t("common.filters")):
        period = filters.period_selector(key="deep_period", default="30d")
        df_city_opt = list_cities()
        city_options = df_city_opt["city_name"].tolist() if not df_city_opt.empty else []
        filters.cities_multiselect(city_options, key="deep_cities")
        filters.pollutants_multiselect(key="deep_pollutants")
    selected_cities = filters.selected("deep_cities")
    selected_pollutants = filters.selected("deep_pollutants")

    # ─── Panel 3.5 — BOXPLOT by Month ───
    with st.container(border=True, key="panel_deep_boxplot"):
        st.subheader(t("deep.boxplot"))
        st.caption(t("deep.boxplot_caption"))
        df_box = boxplot_data()
        exports["boxplot_data"] = df_box
        if not df_box.empty:
            fig = px.box(df_box, x="month", y="aqi", color="month",
                         title=t("deep.boxplot_title"), height=450,
                         labels={"month": col("month"), "aqi": col("aqi")})
            fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.6,
                          annotation_text=t("common.alert_threshold"))
            fig.update_layout(showlegend=False)
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Panel 3.6 — SCATTER PM2.5 vs AQI ───
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True, key="panel_deep_scatter"):
            st.subheader(t("deep.scatter"))
            st.caption(t("deep.scatter_caption"))
            df_scatter = scatter_data(period)
            if selected_cities and not df_scatter.empty and "city_name" in df_scatter.columns:
                df_scatter = df_scatter[df_scatter["city_name"].isin(selected_cities)]
            if not df_scatter.empty:
                labels = {"pm2_5": "PM2.5 (µg/m³)", "aqi": "AQI",
                          "city_name": col("city_name")}
                try:
                    fig = px.scatter(
                        df_scatter, x="pm2_5", y="aqi", color="city_name",
                        trendline="ols", labels=labels, height=400,
                    )
                except ImportError:
                    st.warning(t("deep.ols_warning"))
                    fig = px.scatter(
                        df_scatter, x="pm2_5", y="aqi", color="city_name",
                        labels=labels, height=400,
                    )
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    # ─── Panel 3.7 — HEATMAP Hour × Day ───
    with col2:
        with st.container(border=True, key="panel_deep_heatmap"):
            st.subheader(t("deep.heatmap"))
            st.caption(t("deep.heatmap_caption"))
            df_heat = heatmap_data()
            if not df_heat.empty:
                pivot = df_heat.pivot_table(
                    values="avg_aqi", index="day_of_week", columns="hour", aggfunc="mean",
                )
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                             "Friday", "Saturday", "Sunday"]
                pivot = pivot.reindex([d for d in day_order if d in pivot.index])

                fig = ff.create_annotated_heatmap(
                    z=pivot.values,
                    x=list(pivot.columns),
                    y=list(pivot.index),
                    colorscale="YlOrRd",
                    annotation_text=pivot.round(2).values,
                    font_colors=["black", "white"],
                    hovertemplate=f"{t('deep.hour')}: %{{x}}<br>{t('deep.day')}: %{{y}}<br>{col('avg_aqi')}: %{{z}}<extra></extra>",
                )
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)

    # ─── Panel 3.1 — Correlation Matrix ───
    with st.container(border=True, key="panel_deep_corr"):
        st.subheader(t("deep.corr_matrix"))
        st.caption(t("deep.corr_caption"))
        df_corr = correlation_matrix(period)
        if not df_corr.empty:
            corr_data = df_corr.iloc[0].to_dict()
            pollutants = ["PM2.5", "PM10", "NO₂", "O₃"]
            matrix = np.array([
                [1.0, corr_data.get("PM2.5_x_PM10", 0),
                 corr_data.get("PM2.5_x_NO2", 0), corr_data.get("PM2.5_x_O3", 0)],
                [corr_data.get("PM2.5_x_PM10", 0), 1.0,
                 corr_data.get("PM10_x_NO2", 0), corr_data.get("PM10_x_O3", 0)],
                [corr_data.get("PM2.5_x_NO2", 0), corr_data.get("PM10_x_NO2", 0),
                 1.0, corr_data.get("NO2_x_O3", 0)],
                [corr_data.get("PM2.5_x_O3", 0), corr_data.get("PM10_x_O3", 0),
                 corr_data.get("NO2_x_O3", 0), 1.0],
            ])

            fig = px.imshow(
                matrix, x=pollutants, y=pollutants,
                text_auto=".2f", color_continuous_scale="RdBu_r",
                range_color=[-1, 1], aspect="auto", height=400,
                labels={"x": "", "y": "", "color": t("deep.correlation")},
            )
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

            aqi_pm25 = corr_data.get("AQI_x_PM25", 0)
            aqi_pm10 = corr_data.get("AQI_x_PM10", 0)
            st.info(t("deep.key_insight", pm25=aqi_pm25, pm10=aqi_pm10))

    # ─── Panel 3.2 — Monthly Statistics ───
    with st.expander(t("deep.monthly_stats"), expanded=False):
        st.caption(t("deep.monthly_stats_caption"))
        df_stats = monthly_statistics()
        exports["monthly_statistics"] = df_stats
        if not df_stats.empty:
            fmt_cols = ["avg", "median", "std", "min", "max", "p25", "p75"]
            display = df_stats.rename(columns=lambda c: col(str(c)) if isinstance(c, str) else c)
            styled = display.style.background_gradient(
                subset=[col("avg"), col("median"), col("max"), col("std")], cmap="RdYlGn_r"
            ).format({
                col("avg"): "{:.2f}", col("median"): "{:.2f}", col("std"): "{:.2f}",
                col("min"): "{:.2f}", col("max"): "{:.2f}", col("p25"): "{:.2f}", col("p75"): "{:.2f}",
            })
            st.dataframe(styled, use_container_width=True, hide_index=True)

    # ─── Panel 3.3 — Seasonal Analysis + Panel 3.4 — Weekday vs Weekend ───
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True, key="panel_deep_seasonal"):
            st.subheader(t("deep.seasonal"))
            st.caption(t("deep.seasonal_caption"))
            df_season = seasonal_analysis()
            if not df_season.empty:
                season_cols = ["avg_aqi"] + filters.active_columns(
                    selected_pollutants, ["avg_pm25", "avg_pm10", "avg_o3"],
                    df=df_season)
                fig = px.bar(df_season, x="season", y=season_cols,
                             barmode="group", title=t("deep.seasonal_title"),
                             labels={"value": col("value"), "season": "",
                                     "avg_aqi": col("avg_aqi"), "avg_pm25": col("avg_pm25"),
                                     "avg_pm10": col("avg_pm10"), "avg_o3": col("avg_o3")})
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    with col2:
        with st.container(border=True, key="panel_deep_weekday"):
            st.subheader(t("deep.weekday_weekend"))
            st.caption(t("deep.weekday_weekend_caption"))
            df_we = weekday_weekend()
            if not df_we.empty:
                we_cols = ["avg_aqi"] + filters.active_columns(
                    selected_pollutants, ["avg_pm25", "avg_no2"], df=df_we)
                fig = px.bar(df_we, x="day_type", y=we_cols,
                             barmode="group", title=t("deep.weekday_weekend_title"),
                             labels={"value": col("value"), "day_type": "",
                                     "avg_aqi": col("avg_aqi"), "avg_pm25": col("avg_pm25"),
                                     "avg_no2": col("avg_no2")})
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    # ─── Exports ───
    with st.expander(t("common.export_csv"), expanded=False):
        for key, df in exports.items():
            csv_download(df, export_label(key), f"{key}.csv")
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
