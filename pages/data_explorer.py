"""Dashboard 12 — Data Explorer (admin only).

Read-only SQL explorer against NeonDB. Only a single SELECT / WITH /
EXPLAIN statement is accepted (see utils/sql_guard.py); results are
capped to protect the small VM, and every query runs in a READ ONLY
transaction at the database layer.
"""

import streamlit as st
import pandas as pd

from auth import init_session_state, require_role
from sidebar import render_sidebar
from config import DatabaseError, query
from utils.sql_guard import is_read_only_sql, enforce_limit
from i18n import t, translate_df

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Data Explorer",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()
require_role("admin")  # Admin pages only

st.title(t("explorer.title"))
st.caption(t("explorer.caption"))

MAX_ROWS = 1000

QUICK_QUERIES = {
    "dim_city": "SELECT * FROM dim_city ORDER BY city_name",
    "dim_date (last 7 days)": (
        "SELECT * FROM dim_date "
        "WHERE full_date >= CURRENT_DATE - INTERVAL '7 days' ORDER BY full_date, hour"
    ),
    "fact_aqi (last 48h sample)": (
        "SELECT * FROM fact_aqi f "
        "JOIN dim_date d ON d.date_key = f.date_key "
        "JOIN dim_city c ON c.city_key = f.city_key "
        "WHERE d.full_date >= CURRENT_DATE - INTERVAL '48 hours' "
        "ORDER BY d.full_date DESC, d.hour DESC LIMIT 100"
    ),
    "row counts per table": (
        "SELECT 'dim_city' AS table_name, COUNT(*) AS rows FROM dim_city "
        "UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date "
        "UNION ALL SELECT 'fact_aqi', COUNT(*) FROM fact_aqi"
    ),
}

try:
    # ─── Quick browse ───
    with st.container(border=True):
        st.subheader(t("explorer.quick"))
        quick = st.selectbox(t("explorer.pick"), list(QUICK_QUERIES) + [t("explorer.custom")],
                             key="explorer_quick")
        if isinstance(quick, str) and quick in QUICK_QUERIES:
            sql = QUICK_QUERIES[quick]
        else:
            sql = st.text_area(
                t("explorer.sql_label"),
                value="SELECT city_name FROM dim_city ORDER BY city_name",
                height=140, key="explorer_sql",
            )

        col_run, col_hint = st.columns([1, 4])
        with col_run:
            run = st.button(t("explorer.run"), key="explorer_run")
        with col_hint:
            st.caption(t("explorer.hint", max=MAX_ROWS))
            st.caption(t("explorer.single_statement"))

        if run:
            sql = sql.strip().rstrip(";")
            if not sql:
                st.error(t("explorer.write_query"))
            elif not is_read_only_sql(sql):
                st.error(t("explorer.read_only"))
            else:
                sql = enforce_limit(sql, max_rows=MAX_ROWS)
                try:
                    with st.spinner(t("explorer.running")):
                        df = query(sql)
                    st.success(t("explorer.rows", n=len(df)))
                    st.dataframe(translate_df(df), use_container_width=True, hide_index=True)
                    if not df.empty:
                        st.download_button(
                            t("common.download_csv"),
                            df.to_csv(index=False).encode("utf-8"),
                            file_name="explorer_result.csv",
                            mime="text/csv",
                            key="explorer_download",
                        )
                except DatabaseError as e:
                    st.error(f"❌ {e}")
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
