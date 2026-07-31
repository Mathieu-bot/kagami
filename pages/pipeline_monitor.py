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
)
from utils.charts import style_plotly_chart

init_session_state()
require_role("admin")
render_sidebar()

st.title("⚙️ Pipeline Monitor")
st.caption("_Admin panel — data pipeline health and quality_")

try:
    # ─── Row 1: Status + Last Ingestion ───
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.subheader("🔄 Pipeline Status")
            df_status = pipeline_status()
            if not df_status.empty:
                row = df_status.iloc[0]
                emoji = {"Up to date": "🟢", "Delayed": "🟡", "Critical": "🔴"}
                st.metric("Status", f"{emoji.get(row['status'], '❓')} {row['status']}")

    with col2:
        with st.container(border=True):
            st.subheader("🕐 Last Ingestion")
            df_last = last_ingestion()
            if not df_last.empty:
                st.metric("Last Record", df_last["last_record"].iloc[0])

    with col3:
        with st.container(border=True):
            st.subheader("📡 Data Completeness")
            df_comp = data_completeness()
            if not df_comp.empty:
                comp = df_comp["completeness"].iloc[0]
                st.metric("Today", f"{comp}%")
                st.progress(min(comp, 100) / 100)

    # ─── Panel 4.2 — Records per Day ───
    with st.container(border=True):
        st.subheader("📊 Records per Day (Last 7 Days)")
        df_records = records_per_day()
        if not df_records.empty:
            fig = px.bar(df_records, x="full_date", y="records",
                         labels={"full_date": "Date", "records": "Records"},
                         color="records", color_continuous_scale="Greens")
            fig.update_traces(texttemplate="%{y}", textposition="outside")
            fig = style_plotly_chart(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ─── Panel 4.3 — Data Gaps ───
    with st.container(border=True):
        st.subheader("🔍 Missing Data Detection (Last 24h)")
        df_gaps = data_gaps()
        if not df_gaps.empty:
            missing = df_gaps[df_gaps["status"] == "Missing"]
            total = len(df_gaps)
            missing_count = len(missing)
            ok_count = total - missing_count

            col1, col2 = st.columns(2)
            col1.metric("✅ Complete Records", ok_count)
            col2.metric("❌ Missing Records", missing_count)

            if missing_count > 0:
                st.warning(f"⚠️ {missing_count} missing records detected out of {total}")
                st.dataframe(
                    missing[["full_date", "hour", "city_name"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.success("✅ No missing data in the last 24 hours")

            fig = px.pie(
                values=[ok_count, missing_count],
                names=["Complete", "Missing"],
                color=["Complete", "Missing"],
                color_discrete_map={"Complete": "#00E400", "Missing": "#FF0000"},
                hole=0.6,
            )
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
except DatabaseError as e:
    st.error(f"❌ Database error: {e}")
