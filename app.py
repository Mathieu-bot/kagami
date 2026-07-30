"""Air Quality Madagascar — Streamlit Multi-Role Dashboard.

Protected by Caddy reverse proxy with Google OAuth.
Roles: viewer (default), analyst, admin.
"""

import streamlit as st
from auth import init_session_state, get_available_pages, PAGE_LABELS, PAGE_ACCESS
from queries import list_cities

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Air Quality Madagascar",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Initialize auth ───
init_session_state()

# ─── Sidebar ───
with st.sidebar:
    # Brand
    st.markdown("## 🌍 Kagami")
    st.caption(f"Signed in as **{st.session_state.get('name', 'User')}**")
    st.caption(f"Role: **{st.session_state.get('role', 'viewer')}**")
    st.divider()

    # Navigation — only show available pages for this role
    st.subheader("Navigation")
    available_pages = get_available_pages(st.session_state.get("role", "viewer"))

    if not available_pages:
        st.error("No pages available for your role.")
        st.stop()

    page = st.radio(
        "Go to",
        options=available_pages,
        format_func=lambda p: PAGE_LABELS.get(p, p),
        key="nav",
        label_visibility="collapsed",
    )
    st.session_state["page"] = page

    st.divider()

    # ─── Global filters ───
    st.subheader("Filters")

    # Cities
    df_cities = list_cities()
    all_cities = df_cities["city_name"].tolist() if not df_cities.empty else []
    selected_cities = st.multiselect(
        "Cities", all_cities, default=all_cities,
        key="sidebar_cities",
    )

    # Period
    period = st.selectbox(
        "Period",
        options=["24h", "7d", "30d", "90d", "1y"],
        index=2,
        key="sidebar_period",
    )

    # Store in session state for pages to access
    st.session_state["selected_cities"] = selected_cities
    st.session_state["period"] = period

    st.divider()

    # Logout hint
    st.caption("ℹ️ Managed by Google OAuth via Caddy")

# ─── Route to the selected page ───
page_routes = {
    "hq_overview": "pages.hq_overview",
    "city_drilldown": "pages.city_drilldown",
    "deep_analysis": "pages.deep_analysis",
    "pipeline_monitor": "pages.pipeline_monitor",
}

current_page = st.session_state.get("page", "hq_overview")

if current_page in page_routes:
    module_path = page_routes[current_page]
    module = __import__(module_path, fromlist=["show"])
    module.show()
else:
    st.error(f"Page '{current_page}' not found.")
