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
from i18n import t, col, translate_df

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — City Comparison",
    page_icon="⚖️",
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

    # ─── Key metrics ───
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
            st.dataframe(
                translate_df(df_current.reset_index(drop=True)),
                use_container_width=True,
                hide_index=True,
            )
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
