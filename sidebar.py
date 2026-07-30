"""Shared sidebar — brand, navigation links, and global filters for all pages."""

import streamlit as st
from auth import get_available_pages, PAGE_LABELS
from queries import list_cities


def render_sidebar():
    """Render the sidebar with brand, navigation links, and global filters.

    Must be called at the top of each page *after* init_session_state().
    Reads/writes st.session_state for role, selected_cities, and period.
    """
    with st.sidebar:
        # ─── Brand ───
        st.markdown("## 🌍 Kagami")
        st.caption(f"Signed in as **{st.session_state.get('name', 'User')}**")
        st.caption(f"Role: **{st.session_state.get('role', 'viewer')}**")
        st.divider()

        # ─── Navigation (URL-based page links) ───
        st.subheader("Navigation")
        available_pages = get_available_pages(st.session_state.get("role", "viewer"))
        for pid in available_pages:
            # HQ Overview is the home page (app.py), others live in pages/
            path = "app.py" if pid == "hq_overview" else f"pages/{pid}.py"
            st.page_link(path, label=PAGE_LABELS.get(pid, pid))

        st.divider()

        # ─── Global filters ───
        st.subheader("Filters")

        # Cities
        df_cities = list_cities()
        all_cities = df_cities["city_name"].tolist() if not df_cities.empty else []
        selected_cities = st.multiselect(
            "Cities",
            all_cities,
            default=all_cities,
            key="sidebar_cities",
        )

        # Period
        period = st.selectbox(
            "Period",
            options=["24h", "7d", "30d", "90d", "1y"],
            index=2,
            key="sidebar_period",
        )

        # Persist in session state for pages to read
        st.session_state["selected_cities"] = selected_cities
        st.session_state["period"] = period

        st.divider()
        st.caption("ℹ️ Managed by Google OAuth via Caddy")
