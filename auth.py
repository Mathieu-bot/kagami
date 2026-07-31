"""Authentication — Public + Admin model.

Air quality data is public for everyone (no login required). Only the
admin pages (pipeline monitor, user management, data explorer) require
login with the "admin" role. Users are stored in a local SQLite file
(users.py) with bcrypt hashed passwords. Login methods:
  - Google OAuth (email matched against the local user store)
  - Username & password
"""

import json
import urllib.parse
import urllib.request

import streamlit as st

from i18n import t, init_lang
from users import get_user, get_user_by_email, verify_password

# Role model: everyone is a viewer (public); only admin gates pages.
ROLE_HIERARCHY = {
    "viewer": 0,
    "admin": 1,
}

PAGE_ACCESS = {
    # Public pages — open air quality data
    "hq_overview": "viewer",
    "city_drilldown": "viewer",
    "deep_analysis": "viewer",
    "city_comparison": "viewer",
    "alerts_history": "viewer",
    "forecast": "viewer",
    # Admin pages
    "pipeline_monitor": "admin",
    "user_management": "admin",
    "data_explorer": "admin",
}

PAGE_LABELS = {
    "hq_overview": "📊 HQ Overview",
    "city_drilldown": "🏙️ City Drill-down",
    "deep_analysis": "🔬 Deep Analysis",
    "city_comparison": "⚖️ City Comparison",
    "alerts_history": "🚨 Alerts History",
    "forecast": "🔮 AQI Forecast",
    "pipeline_monitor": "⚙️ Pipeline Monitor",
    "user_management": "👥 User Management",
    "data_explorer": "🗄️ Data Explorer",
}
# Legacy label map kept for tests; the sidebar renders `nav.*` i18n keys instead.


def get_available_pages(role: str) -> list:
    """Return pages accessible to the given role."""
    return [
        key for key, required in PAGE_ACCESS.items()
        if ROLE_HIERARCHY.get(role, -1) >= ROLE_HIERARCHY.get(required, 99)
    ]


def _google_oauth_config():
    """Return the google_oauth secrets dict or None."""
    try:
        cfg = st.secrets["google_oauth"]
        return cfg if cfg.get("client_id") and cfg.get("client_secret") else None
    except Exception:
        return None


def _google_auth_url() -> str:
    """Build the Google authorization URL (or None if not configured)."""
    cfg = _google_oauth_config()
    if not cfg:
        return None
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": "openid email profile",
        "state": "kagami",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)


def _exchange_code(code: str, cfg: dict):
    """Exchange the authorization code for the user's email address."""
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "redirect_uri": cfg["redirect_uri"],
        "grant_type": "authorization_code",
    }).encode("utf-8")
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))
    access_token = tokens["access_token"]
    req = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        info = json.loads(resp.read().decode("utf-8"))
    return info.get("email")


def handle_google_callback() -> bool:
    """Process a Google OAuth callback if one is pending in the query params."""
    try:
        params = st.query_params
        if not params.get("oauth") or str(params.get("oauth")) != "callback":
            return False
        code = params.get("code")
        cfg = _google_oauth_config()
        if not cfg or not code:
            return False
        email = _exchange_code(str(code), cfg)
        if email:
            user = get_user_by_email(email)
            if user and user["active"] and user["role"] == "admin":
                _set_session(user)
            else:
                st.session_state["authenticated"] = False
                st.session_state["email"] = email
                st.session_state["role"] = "viewer"
            try:
                params.clear()
            except Exception:
                pass
            return True
    except Exception:
        return False
    return False


def _set_session(user: dict):
    """Store an authenticated session for the given user."""
    st.session_state["authenticated"] = True
    st.session_state["username"] = user["username"]
    st.session_state["email"] = user["email"]
    st.session_state["name"] = user["username"].capitalize()
    st.session_state["role"] = user.get("role", "viewer")


def init_session_state():
    """Ensure session keys exist. Anonymous users are public viewers."""
    init_lang()
    handle_google_callback()
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.session_state["email"] = None
        st.session_state["name"] = "Guest"
        st.session_state["role"] = "viewer"
        st.session_state["page"] = "hq_overview"


def _handle_password_login(username: str, password: str):
    """Validate username/password and set the session on success."""
    user = get_user(username) if username else None
    if user and user["active"] and verify_password(password, user["password_hash"]):
        _set_session(user)
        st.rerun()
    else:
        st.error(t("auth.invalid_credentials"))


def render_login_form():
    """Render the admin login form (Google + username/password)."""
    st.markdown(t("auth.login_title"))
    st.caption(t("auth.login_caption"))
    tab_google, tab_password = st.tabs([t("auth.tab_google"), t("auth.tab_password")])

    with tab_google:
        url = _google_auth_url()
        if url:
            st.link_button(t("auth.tab_google"), url)
        else:
            st.info(t("auth.google_unconfigured"))

    with tab_password:
        with st.form("login_form"):
            username = st.text_input(t("auth.username"))
            password = st.text_input(t("auth.password"), type="password")
            submitted = st.form_submit_button(t("auth.sign_in"), type="primary")
            if submitted:
                _handle_password_login(username, password)


def require_role(min_role: str):
    """Stop execution if the user's role is insufficient; show login instead."""
    role = st.session_state.get("role", "viewer")
    if ROLE_HIERARCHY.get(role, -1) >= ROLE_HIERARCHY.get(min_role, 99):
        return
    role_label = t("auth.role_admin") if min_role == "admin" else t("auth.role_viewer")
    st.error(t("auth.access_denied", role=role_label))
    render_login_form()
    st.stop()


def logout():
    """Clear the session and redirect to the current page."""
    for key in ("authenticated", "username", "email", "name", "role"):
        st.session_state.pop(key, None)
    st.rerun()
