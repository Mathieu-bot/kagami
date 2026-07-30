"""Dashboard 3 — Deep Analysis: Boxplot, Scatter, Heatmap, Correlation."""

import streamlit as st
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np
import pandas as pd
from queries import *
from utils.charts import style_plotly_chart


def show():
    st.title("🔬 Deep Analysis")
    st.caption("_EDA-compliant: statistics, outliers, correlations, multi-dimensional_")

    period = st.session_state.get("period", "30d")

    # ─── Panel 3.5 — BOXPLOT by Month ───
    with st.container(border=True):
        st.subheader("📦 Boxplot — AQI by Month")
        st.caption("_Outlier detection: dots beyond whiskers are unusual readings_")
        df_box = boxplot_data()
        if not df_box.empty:
            fig = px.box(df_box, x="month", y="aqi", color="month",
                         title="AQI Distribution by Month", height=450)
            fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.6,
                          annotation_text="Alert Threshold (AQI ≥ 3)")
            fig.update_layout(showlegend=False)
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Panel 3.6 — SCATTER PM2.5 vs AQI ───
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("🔵 PM2.5 vs AQI")
            st.caption("_With linear regression trendline_")
            df_scatter = scatter_data(period)
            if not df_scatter.empty:
                fig = px.scatter(
                    df_scatter, x="pm2_5", y="aqi", color="city_name",
                    trendline="ols",  # Linear regression built-in
                    labels={"pm2_5": "PM2.5 (µg/m³)", "aqi": "AQI"},
                    height=400,
                )
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    # ─── Panel 3.7 — HEATMAP Hour × Day ───
    with col2:
        with st.container(border=True):
            st.subheader("🟥 Heatmap — AQI by Hour × Day")
            st.caption("_Multi-dimensional view: darker = worse air quality_")
            df_heat = heatmap_data()
            if not df_heat.empty:
                pivot = df_heat.pivot_table(
                    values="avg_aqi", index="day_of_week", columns="hour", aggfunc="mean"
                )
                # Order days correctly
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
                    hovertemplate="Hour: %{x}<br>Day: %{y}<br>Avg AQI: %{z}<extra></extra>",
                )
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)

    # ─── Panel 3.1 — Correlation Matrix ───
    with st.container(border=True):
        st.subheader("🔗 Pollutant Correlation Matrix")
        st.caption("_1.0 = perfect correlation, 0 = none, -1 = inverse_")
        df_corr = correlation_matrix(period)
        if not df_corr.empty:
            # Reshape for heatmap display
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
                labels={"x": "", "y": "", "color": "Correlation"},
            )
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

            # Key insights
            aqi_pm25 = corr_data.get("AQI_x_PM25", 0)
            aqi_pm10 = corr_data.get("AQI_x_PM10", 0)
            st.info(f"💡 **Key insight:** AQI is most correlated with "
                    f"PM2.5 ({aqi_pm25}) and PM10 ({aqi_pm10})")

    # ─── Panel 3.2 — Monthly Statistics ───
    with st.expander("📊 Monthly Statistical Distribution", expanded=False):
        df_stats = monthly_statistics()
        if not df_stats.empty:
            styled = df_stats.style.background_gradient(
                subset=["avg", "median", "max", "std"], cmap="RdYlGn_r"
            ).format({
                "avg": "{:.2f}", "median": "{:.2f}", "std": "{:.2f}",
                "min": "{:.2f}", "max": "{:.2f}", "p25": "{:.2f}", "p75": "{:.2f}"
            })
            st.dataframe(styled, use_container_width=True, hide_index=True)

    # ─── Panel 3.3 — Seasonal Analysis + Panel 3.4 — Weekday vs Weekend ───
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("🏜️ Seasonal Analysis")
            df_season = seasonal_analysis()
            if not df_season.empty:
                fig = px.bar(df_season, x="season", y=["avg_aqi", "avg_pm25", "avg_o3"],
                             barmode="group", title="Dry Season vs Wet Season",
                             labels={"value": "Average", "season": ""})
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.subheader("💼 Weekday vs Weekend")
            df_we = weekday_weekend()
            if not df_we.empty:
                fig = px.bar(df_we, x="day_type", y=["avg_aqi", "avg_pm25", "avg_no2"],
                             barmode="group", title="Weekday vs Weekend Effect",
                             labels={"value": "Average", "day_type": ""})
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
