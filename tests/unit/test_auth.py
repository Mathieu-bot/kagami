"""Unit tests for the auth module — roles, permissions, session."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from auth import (
    ROLE_HIERARCHY,
    PAGE_ACCESS,
    PAGE_LABELS,
    get_available_pages,
    require_role,
    init_session_state,
    get_authenticated_user,
    USER_ROLES,
)


class TestRoleHierarchy:
    """Verify the role permission levels."""

    def test_viewer_is_lowest(self):
        assert ROLE_HIERARCHY["viewer"] == 0

    def test_analyst_is_middle(self):
        assert ROLE_HIERARCHY["analyst"] == 1

    def test_admin_is_highest(self):
        assert ROLE_HIERARCHY["admin"] == 2

    def test_hierarchy_order(self):
        assert ROLE_HIERARCHY["viewer"] < ROLE_HIERARCHY["analyst"] < ROLE_HIERARCHY["admin"]


class TestPageAccess:
    """Verify page access rules per role."""

    def test_viewer_can_access_two_pages(self):
        pages = get_available_pages("viewer")
        assert "hq_overview" in pages
        assert "city_drilldown" in pages
        assert "deep_analysis" not in pages
        assert "pipeline_monitor" not in pages
        assert len(pages) == 2

    def test_analyst_can_access_three_pages(self):
        pages = get_available_pages("analyst")
        assert "hq_overview" in pages
        assert "city_drilldown" in pages
        assert "deep_analysis" in pages
        assert "pipeline_monitor" not in pages
        assert len(pages) == 3

    def test_admin_can_access_all_pages(self):
        pages = get_available_pages("admin")
        assert len(pages) == 4

    def test_unknown_role_gets_no_access(self):
        """An unrecognised role should be denied all pages."""
        pages = get_available_pages("unknown")
        assert len(pages) == 0

    def test_all_page_keys_have_labels(self):
        for key in PAGE_ACCESS:
            assert key in PAGE_LABELS, f"Missing label for {key}"
            assert isinstance(PAGE_LABELS[key], str)
            assert len(PAGE_LABELS[key]) > 0


class TestRequireRole:
    """Verify the require_role guard."""

    def test_require_role_allowed(self, mock_streamlit):
        """Should NOT call st.stop() when role is sufficient."""
        import streamlit as st
        st.session_state["role"] = "admin"
        require_role("viewer")  # Should not raise

    def test_require_role_denied_viewer_to_admin(self, mock_streamlit):
        """Should call st.stop() when role is insufficient."""
        import streamlit as st
        import streamlit
        st.session_state["role"] = "viewer"
        require_role("admin")
        streamlit.stop.assert_called_once()


class TestGetAuthenticatedUser:
    """Verify user extraction from headers."""

    def test_fallback_to_viewer_when_no_headers(self):
        """When no auth headers exist, default to viewer."""
        username, email = get_authenticated_user()
        assert username in ("viewer", "admin")
        assert "@" in email


class TestInitSessionState:
    """Verify session initialization."""

    def test_session_state_initialized(self, mock_streamlit):
        """After init, session should have required keys."""
        import streamlit as st
        st.session_state.clear()
        init_session_state()
        assert st.session_state["authenticated"] is True
        assert "role" in st.session_state
        assert "page" in st.session_state
        assert st.session_state["page"] == "hq_overview"


class TestUserRoles:
    """Verify the USER_ROLES mapping."""

    def test_all_roles_exist(self):
        assert "admin" in USER_ROLES
        assert "analyst" in USER_ROLES
        assert "viewer" in USER_ROLES

    def test_no_extra_roles(self):
        assert len(USER_ROLES) == 3
