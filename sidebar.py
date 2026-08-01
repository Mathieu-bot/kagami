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


_GLOBAL_CSS = """
<style>
[data-testid="stHorizontalBlock"] {
    align-items: stretch;
}
[data-testid="stColumn"] {
    display: flex;
    flex-direction: column;
}
[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
    display: flex;
    flex-direction: column;
    flex: 1;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    display: flex;
    flex-direction: column;
    flex: 1;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, .06);
}
[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
    flex: 1;
}
[data-testid="stSidebarContent"] {
    display: flex;
    flex-direction: column;
}
.sidebar-footer {
    margin-top: auto;
    position: sticky;
    bottom: 0;
    background: #f6f8fa;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(0, 0, 0, .08);
}
[data-testid="stSidebar"] button[kind="primary"] {
    background-color: #1a1a1a !important;
    border-color: #1a1a1a !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover {
    background-color: #3a3a3a !important;
    border-color: #3a3a3a !important;
}
</style>
"""


def _inject_global_css():
    """Inject app-wide styles once per page render."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


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
    _inject_global_css()
    with st.sidebar:
        st.markdown(f"## {icon(BRAND_ICON)} Kagami")
        st.caption(t("sidebar.subtitle"))
        st.divider()

        role = st.session_state.get("role", "viewer")
        for section_key, page_ids in NAV_SECTIONS.items():
            _nav_section(section_key, page_ids, role)

        st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
        lang_selector()
        st.divider()
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
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption(f"{icon(FOOTER_ICON)} {t('sidebar.footer')}")
