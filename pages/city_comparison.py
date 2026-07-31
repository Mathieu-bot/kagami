"""Dashboard 5 — Inter-city comparison (public).

Two modes:
  - All cities: side-by-side view of current AQI and the 7-day trend.
  - 2 cities: head-to-head (A vs B) current AQI, 7-day trend and
    average pollutant comparison.
"""

import streamlit as st
import plotly.express as px

from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import list_cities, comparison_current, comparison_trend_7d, comparison_pollutants
from utils.charts import style_plotly_chart, rename_traces
from i18n import t, col, translate_df
from ui import page_icon

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — City Comparison",
    page_icon=page_icon("city_comparison"),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title(t("compare.title"))
st.caption(t("compare.caption"))

try:
    df_current = comparison_current()
    df_trend = comparison_trend_7d()

    if df_current.empty and df_trend.empty:
        st.info(t("common.no_data_yet"))
        st.stop()

    mode = st.radio(
        t("compare.mode"),
        ["all", "2cities"],
        index=0,
        horizontal=True,
        key="compare_mode",
        format_func=lambda m: t("compare.mode_all") if m == "all" else t("compare.mode_2cities"),
    )

    if mode == "2cities":
        # ─── A/B head-to-head ───
        df_cities = list_cities()
        cities = df_cities["city_name"].tolist() if not df_cities.empty else []
        if len(cities) < 2:
            st.info(t("common.no_cities"))
        else:
            c1, c2 = st.columns(2)
            city_a = c1.selectbox(t("compare.city_a"), cities, key="compare_city_a")
            city_b = c2.selectbox(
                t("compare.city_b"), cities, index=min(1, len(cities) - 1),
                key="compare_city_b",
            )

            if city_a == city_b:
                st.warning(t("compare.same_city"))
            else:
                st.subheader(t("compare.versus", a=city_a, b=city_b))

                # Current AQI head-to-head
                row_a = df_current[df_current["city_name"] == city_a]
                row_b = df_current[df_current["city_name"] == city_b]
                aqi_a = row_a["current_aqi"].iloc[0] if not row_a.empty else None
                aqi_b = row_b["current_aqi"].iloc[0] if not row_b.empty else None

                m1, m2 = st.columns(2)
                m1.metric(f":material/sunny: {city_a}", aqi_a)
                m2.metric(f":material/sunny: {city_b}", aqi_b)
                if aqi_a is not None and aqi_b is not None and aqi_a != aqi_b:
                    winner = city_a if aqi_a < aqi_b else city_b
                    st.markdown(t("compare.winner", city=winner))

                # 7-day trend for the two cities
                if not df_trend.empty:
                    with st.container(border=True):
                        st.subheader(t("compare.trend_7d_title"))
                        st.caption(t("compare.trend_7d_caption"))
                        trend_ab = df_trend[df_trend["city_name"].isin([city_a, city_b])]
                        if not trend_ab.empty:
                            fig = px.line(
                                trend_ab, x="full_date", y="avg_aqi", color="city_name",
                                markers=True,
                                labels={"full_date": col("full_date"),
                                        "avg_aqi": col("avg_aqi"),
                                        "city_name": col("city_name")},
                                height=400,
                            )
                            fig.add_hline(
                                y=3, line_dash="dash", line_color="red", opacity=0.6,
                                annotation_text=t("common.alert_threshold_short"),
                            )
                            fig = style_plotly_chart(fig)
                            st.plotly_chart(fig, use_container_width=True)

                # Average pollutants (7 days)
                with st.container(border=True):
                    st.subheader(t("compare.pollutant_compare"))
                    st.caption(t("compare.avg_this_week"))
                    df_poll = comparison_pollutants(city_a, city_b)
                    if not df_poll.empty:
                        poll_cols = ["pm2_5", "pm10", "no2", "o3"]
                        labels = {c: col(c) for c in poll_cols}
                        labels["city_name"] = col("city_name")
                        fig = px.bar(
                            df_poll, x="city_name", y=poll_cols,
                            barmode="group", labels=labels, height=400,
                        )
                        fig = style_plotly_chart(fig)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(t("common.no_data"))
    else:
        # ─── All cities ───
        if not df_current.empty:
            best = df_current.iloc[-1]
            worst = df_current.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric(t("compare.best_air"), f"{best['city_name']}", f"AQI {best['current_aqi']}")
            c2.metric(t("compare.worst_air"), f"{worst['city_name']}", f"AQI {worst['current_aqi']}")
            c3.metric(t("compare.cities_count"), len(df_current))

        # ─── Current AQI bar chart ───
        if not df_current.empty:
            with st.container(border=True):
                st.subheader(t("compare.current_aqi_by_city"))
                st.caption(t("compare.current_aqi_caption"))
                fig = px.bar(
                    df_current, x="city_name", y="current_aqi",
                    color="current_aqi", color_continuous_scale=["green", "yellow", "orange", "red"],
                    labels={"city_name": col("city_name"), "current_aqi": col("current_aqi")},
                    text="current_aqi", height=380,
                )
                fig.update_traces(texttemplate="%{text}", textposition="outside")
                fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.6,
                              annotation_text=t("common.alert_threshold"))
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

        # ─── 7-day trend multi-line ───
        if not df_trend.empty:
            with st.container(border=True):
                st.subheader(t("compare.trend_7d_title"))
                st.caption(t("compare.trend_7d_caption"))
                fig = px.line(
                    df_trend, x="full_date", y="avg_aqi", color="city_name",
                    markers=True,
                    labels={"full_date": col("full_date"), "avg_aqi": col("avg_aqi"),
                            "city_name": col("city_name")},
                    height=420,
                )
                fig.add_hline(y=3, line_dash="dash", line_color="red", opacity=0.6,
                              annotation_text=t("common.alert_threshold_short"))
                fig = style_plotly_chart(fig)
                st.plotly_chart(fig, use_container_width=True)

        # ─── Ranking table ───
        if not df_current.empty:
            with st.container(border=True):
                st.subheader(t("compare.ranking"))
                st.caption(t("compare.ranking_caption"))
                st.dataframe(
                    translate_df(df_current.reset_index(drop=True)),
                    use_container_width=True,
                    hide_index=True,
                )
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))