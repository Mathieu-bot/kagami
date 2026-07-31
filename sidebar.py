"""Shared sidebar — brand and grouped navigation with Material icons.

Global filters were removed: every page now owns its own, contextual
filters (see utils.filters), so nothing in this sidebar is dead weight.
"""

import os
import streamlit as st
from auth import get_available_pages, logout, render_login_form
from i18n import t, init_lang, lang_selector
from ui import BRAND_ICON, FOOTER_ICON, NAV_SECTIONS, PAGE_ICONS, icon

# Project root directory (where sidebar.py lives)
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def _hide_native_nav():
    """Hide Streamlit's auto-generated page menu.

    Streamlit builds a native nav from the ``pages/`` folder and renders it
    at the top of the sidebar, listing *every* page (including admin ones)
    with no role filtering. We render our own grouped, role-filtered nav,
    so the native one must be hidden.
    """
    st.markdown(
        '<style>[data-testid="stSidebarNav"] {display: none;}</style>',
        unsafe_allow_html=True,
    )


def _page_path(page_id: str) -> str:
    """Return an absolute path to the page file."""
    if page_id == "hq_overview":
        return os.path.join(_PROJECT_ROOT, "app.py")
    return os.path.join(_PROJECT_ROOT, "pages", f"{page_id}.py")


def _nav_section(section_key: str, page_ids: list, role: str):
    """Render one navigation section (label + iconed page links)."""
    available = get_available_pages(role)
    visible = [pid for pid in page_ids if pid in available]
    if not visible:
        return
    st.markdown(f"**{t(section_key)}**")
    for pid in visible:
        st.page_link(
            _page_path(pid),
            label=t(f"nav.{pid}"),
            icon=icon(PAGE_ICONS[pid]),
        )


def render_sidebar():
    """Render the sidebar with brand, user info and grouped navigation.

    Must be called at the top of each page *after* init_session_state().
    """
    init_lang()
    _hide_native_nav()
    with st.sidebar:
        # ─── Brand ───
        st.markdown(f"## {icon(BRAND_ICON)} Kagami")
        st.caption(t("sidebar.subtitle"))
        lang_selector()
        if st.session_state.get("authenticated"):
            st.session_state.pop("show_login", None)
            st.caption(t("sidebar.signed_in_as", name=st.session_state.get("name", "User")))
            role = st.session_state.get("role", "viewer")
            role_label = t("auth.role_admin") if role == "admin" else t("auth.role_viewer")
            st.caption(t("sidebar.role", role=role_label))
            if st.button(t("sidebar.sign_out"), key="sidebar_signout", use_container_width=True):
                logout()
        else:
            st.caption(t("sidebar.public_viewer"))
            if st.button(t("auth.sign_in"), key="sidebar_login_btn",
                         use_container_width=True, type="primary"):
                st.session_state["show_login"] = True
            if st.session_state.get("show_login"):
                render_login_form()
        st.divider()

        # ─── Navigation (grouped by section, Material icons) ───
        role = st.session_state.get("role", "viewer")
        for section_key, page_ids in NAV_SECTIONS.items():
            _nav_section(section_key, page_ids, role)

        st.divider()
        st.caption(f"{icon(FOOTER_ICON)} {t('sidebar.footer')}")
