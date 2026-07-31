"""Tests for the shared sidebar.

The sidebar hides Streamlit's auto-generated page nav (it lists every
page with no role filtering) and provides an admin login entry point for
anonymous visitors, so the admin pages stay reachable once the native
nav is hidden.
"""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from i18n import t


def _render_sidebar(session_state, login_clicked=False):
    """Render the sidebar in an isolated mocked environment."""
    from sidebar import render_sidebar

    with patch("streamlit.session_state", session_state), \
         patch("streamlit.sidebar"), \
         patch("streamlit.markdown"), \
         patch("streamlit.caption"), \
         patch("streamlit.divider"), \
         patch("streamlit.selectbox", return_value="fr"), \
         patch("streamlit.page_link"), \
         patch("streamlit.button", return_value=login_clicked) as mock_btn, \
         patch("sidebar.render_login_form") as mock_login:
        render_sidebar()
    return mock_btn, mock_login


def _button_labels(btn):
    return [c.args[0] for c in btn.call_args_list if c.args]


def test_public_visitor_gets_login_button_but_no_form():
    """Anonymous visitors see a 'Sign in' button; the form stays hidden."""
    btn, login = _render_sidebar({})
    assert t("auth.sign_in") in _button_labels(btn)
    assert "sidebar_login_btn" in [c.kwargs.get("key") for c in btn.call_args_list]
    login.assert_not_called()


def test_clicking_login_shows_form():
    """After the visitor clicks the button, the login form renders inline."""
    _, login = _render_sidebar({}, login_clicked=True)
    login.assert_called_once()


def test_authenticated_user_gets_sign_out_not_login():
    """Logged-in users see 'Sign out' and no login button."""
    btn, login = _render_sidebar({"authenticated": True, "role": "admin", "name": "Admin"})
    assert t("auth.sign_in") not in _button_labels(btn)
    assert t("sidebar.sign_out") in _button_labels(btn)
    login.assert_not_called()


def test_native_page_nav_is_hidden():
    """Streamlit's auto-generated page menu is hidden via CSS."""
    from sidebar import render_sidebar

    with patch("streamlit.session_state", {}), \
         patch("streamlit.sidebar"), \
         patch("streamlit.caption"), \
         patch("streamlit.divider"), \
         patch("streamlit.selectbox", return_value="fr"), \
         patch("streamlit.page_link"), \
         patch("streamlit.button", return_value=False), \
         patch("streamlit.markdown") as mock_md, \
         patch("sidebar.render_login_form"):
        render_sidebar()

    css = [c.args[0] for c in mock_md.call_args_list
           if c.args and isinstance(c.args[0], str) and "stSidebarNav" in c.args[0]]
    assert css, "expected CSS hiding the native page navigation"
