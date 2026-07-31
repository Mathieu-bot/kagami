"""Dashboard 4 — Pipeline Monitoring: 3 panels for admin (standalone page)."""

import streamlit as st
import plotly.express as px
from auth import init_session_state, require_role
from sidebar import render_sidebar
from config import DatabaseError
from queries import (
    pipeline_status,
    last_ingestion,
    data_completeness,
    records_per_day,
    data_gaps,
    list_cities,
)
from utils.charts import style_plotly_chart, pipeline_status_label
from utils import filters
from i18n import t, col, translate_df
from ui import page_icon

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Pipeline Monitor",
    page_icon=page_icon("pipeline_monitor"),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
require_role("admin")
render_sidebar()

st.title(t("pipeline.title"))
st.caption(t("pipeline.caption"))

try:
    # ─── Local filter: cities (applies to the data-gaps table) ───
    with st.expander(t("common.filters"), expanded=False):
        df_city_opt = list_cities()
        city_options = df_city_opt["city_name"].tolist() if not df_city_opt.empty else []
        filters.cities_multiselect(city_options, key="pipeline_cities")
    selected_cities = filters.selected("pipeline_cities")

    # ─── Row 1: Status + Last Ingestion ───
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.subheader(t("pipeline.status"))
            st.caption(t("pipeline.status_caption"))
            df_status = pipeline_status()
            if not df_status.empty:
                row = df_status.iloc[0]
                emoji, label = pipeline_status_label(row["status"])
                st.metric(col("status"), f"{emoji} {label}")

    with col2:
        with st.container(border=True):
            st.subheader(t("pipeline.last_ingestion"))
            st.caption(t("pipeline.last_ingestion_caption"))
            df_last = last_ingestion()
            if not df_last.empty:
                st.metric(t("pipeline.last_record"), df_last["last_record"].iloc[0])

    with col3:
        with st.container(border=True):
            st.subheader(t("pipeline.data_completeness"))
            st.caption(t("pipeline.data_completeness_caption"))
            df_comp = data_completeness()
            if not df_comp.empty:
                comp = float(df_comp["completeness"].iloc[0])
                st.metric(t("pipeline.today"), f"{comp}%")
                st.progress(min(comp, 100) / 100)

    # ─── Panel 4.2 — Records per Day ───
    with st.container(border=True):
        st.subheader(t("pipeline.records_per_day"))
        st.caption(t("pipeline.records_per_day_caption"))
        df_records = records_per_day()
        if not df_records.empty:
            fig = px.bar(df_records, x="full_date", y="records",
                         labels={"full_date": col("full_date"), "records": t("pipeline.records")},
                         color="records", color_continuous_scale="Greens")
            fig.update_traces(texttemplate="%{y}", textposition="outside")
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Panel 4.3 — Data Gaps ───
    with st.container(border=True):
        st.subheader(t("pipeline.missing_data"))
        st.caption(t("pipeline.missing_data_caption"))
        df_gaps = data_gaps()
        if selected_cities and not df_gaps.empty and "city_name" in df_gaps.columns:
            df_gaps = df_gaps[df_gaps["city_name"].isin(selected_cities)]
        if not df_gaps.empty:
            missing = df_gaps[df_gaps["status"] == "Missing"]
            total = len(df_gaps)
            missing_count = len(missing)
            ok_count = total - missing_count

            col1, col2 = st.columns(2)
            col1.metric(t("pipeline.complete_records"), ok_count)
            col2.metric(t("pipeline.missing_records"), missing_count)

            if missing_count > 0:
                st.warning(t("pipeline.missing_warning", n=missing_count, total=total))
                st.dataframe(
                    translate_df(missing[["full_date", "hour", "city_name"]]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success(t("pipeline.no_missing"))

            fig = px.pie(
                values=[ok_count, missing_count],
                names=[t("pipeline.complete"), t("pipeline.missing")],
                color=[t("pipeline.complete"), t("pipeline.missing")],
                color_discrete_map={t("pipeline.complete"): "#00E400",
                                    t("pipeline.missing"): "#FF0000"},
                hole=0.6,
            )
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
