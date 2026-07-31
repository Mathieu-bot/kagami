"""Unit tests for the auth module — roles, permissions, session, login."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit
import streamlit as st

import pytest

from tests.conftest import StopPage

from auth import (
    ROLE_HIERARCHY,
    PAGE_ACCESS,
    get_available_pages,
    require_role,
    init_session_state,
    handle_google_callback,
    render_login_form,
)


class TestRoleHierarchy:
    """Verify the role permission levels."""

    def test_viewer_is_lowest(self):
        assert ROLE_HIERARCHY["viewer"] == 0

    def test_admin_is_highest(self):
        assert ROLE_HIERARCHY["admin"] == 1

    def test_hierarchy_order(self):
        assert ROLE_HIERARCHY["viewer"] < ROLE_HIERARCHY["admin"]


class TestPageAccess:
    """Verify page access rules per role (data public, admin gated)."""

    def test_viewer_gets_all_public_pages(self):
        pages = get_available_pages("viewer")
        for p in ("hq_overview", "city_drilldown", "deep_analysis",
                  "city_comparison", "alerts_history"):
            assert p in pages
        assert "pipeline_monitor" not in pages
        assert "user_management" not in pages
        assert "data_explorer" not in pages

    def test_admin_gets_all_pages(self):
        pages = get_available_pages("admin")
        assert len(pages) == len(PAGE_ACCESS)

    def test_unknown_role_gets_no_access(self):
        """An unrecognised role should be denied all pages."""
        pages = get_available_pages("unknown")
        assert len(pages) == 0


class TestRequireRole:
    """Verify the require_role guard."""

    def test_require_role_allowed_admin(self, mock_streamlit):
        """Should NOT call st.stop() when the role is sufficient."""
        st.session_state["role"] = "admin"
        require_role("admin")  # Should not raise

    def test_require_role_denied_viewer(self, mock_streamlit):
        """Should call st.stop() and show the login form when denied."""
        st.session_state["role"] = "viewer"
        with pytest.raises(StopPage):
            require_role("admin")
        streamlit.stop.assert_called_once()
        # The login form should be shown on denial.
        streamlit.tabs.assert_called()


class TestInitSessionState:
    """Verify anonymous session initialization (public viewer)."""

    def test_anonymous_session_initialized(self, mock_streamlit):
        st.session_state.clear()
        init_session_state()
        assert st.session_state["authenticated"] is False
        assert st.session_state["role"] == "viewer"
        assert st.session_state["name"] == "Guest"

    def test_existing_session_not_overwritten(self, mock_streamlit):
        st.session_state.clear()
        st.session_state["authenticated"] = True
        st.session_state["role"] = "admin"
        init_session_state()
        assert st.session_state["authenticated"] is True
        assert st.session_state["role"] == "admin"


class TestGoogleCallback:
    """Verify the OAuth callback guard."""

    def test_callback_noop_without_code(self, mock_streamlit):
        """With no callback params, the handler should do nothing."""
        assert handle_google_callback() is False

    def test_callback_noop_without_config(self, mock_streamlit):
        """Without google_oauth secrets, even a code should be ignored."""
        st.query_params["oauth"] = "callback"
        st.query_params["code"] = "abc"
        assert handle_google_callback() is False


class TestLoginForm:
    """Verify the login form renders without crashing."""

    def test_login_form_renders(self, mock_streamlit):
        render_login_form()
        # Username + password inputs rendered, and the form submitted lazily.
        assert streamlit.text_input.call_count >= 2
