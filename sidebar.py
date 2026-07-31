"""Shared sidebar — brand, navigation links, and global filters for all pages."""

import os
import streamlit as st
from auth import get_available_pages, logout
from config import DatabaseError
from i18n import t, init_lang, lang_selector
from queries import list_cities

# Project root directory (where sidebar.py lives)
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def _page_path(page_id: str) -> str:
    """Return an absolute path to the page file."""
    if page_id == "hq_overview":
        return os.path.join(_PROJECT_ROOT, "app.py")
    return os.path.join(_PROJECT_ROOT, "pages", f"{page_id}.py")


def render_sidebar():
    """Render the sidebar with brand, navigation links, and global filters.

    Must be called at the top of each page *after* init_session_state().
    Reads/writes st.session_state for role, selected_cities, and period.
    """
    init_lang()
    with st.sidebar:
        # ─── Brand ───
        st.markdown("## 🌍 Kagami")
        lang_selector()
        if st.session_state.get("authenticated"):
            st.caption(t("sidebar.signed_in_as", name=st.session_state.get("name", "User")))
            role = st.session_state.get("role", "viewer")
            role_label = t("auth.role_admin") if role == "admin" else t("auth.role_viewer")
            st.caption(t("sidebar.role", role=role_label))
            if st.button(t("sidebar.sign_out"), key="sidebar_signout", use_container_width=True):
                logout()
        else:
            st.caption(t("sidebar.public_viewer"))
        st.divider()

        # ─── Navigation (URL-based page links with absolute paths) ───
        st.subheader(t("sidebar.navigation"))
        available_pages = get_available_pages(st.session_state.get("role", "viewer"))
        for pid in available_pages:
            st.page_link(_page_path(pid), label=t(f"nav.{pid}"))

        st.divider()

        # ─── Global filters ───
        st.subheader(t("sidebar.filters"))

        # Cities
        try:
            df_cities = list_cities()
            all_cities = df_cities["city_name"].tolist() if not df_cities.empty else []
        except DatabaseError:
            st.warning(t("sidebar.cities_error"))
            all_cities = []
        selected_cities = st.multiselect(
            t("common.cities"),
            all_cities,
            default=all_cities,
            key="sidebar_cities",
        )

        # Period
        period = st.selectbox(
            t("common.period"),
            options=["24h", "7d", "30d", "90d", "1y"],
            index=2,
            key="sidebar_period",
        )

        # Persist in session state for pages to read
        st.session_state["selected_cities"] = selected_cities
        st.session_state["period"] = period

        st.divider()
        st.caption(t("sidebar.footer"))
