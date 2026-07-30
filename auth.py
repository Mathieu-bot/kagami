"""Authentication and role management via Caddy Basic Auth / OAuth."""

import streamlit as st
import base64

# Role mapping
USER_ROLES = {
    "admin": "admin",
    "analyst": "analyst",
    "viewer": "viewer",
}

ROLE_HIERARCHY = {
    "viewer": 0,
    "analyst": 1,
    "admin": 2,
}

PAGE_ACCESS = {
    "hq_overview": "viewer",
    "city_drilldown": "viewer",
    "deep_analysis": "analyst",
    "pipeline_monitor": "admin",
}

PAGE_LABELS = {
    "hq_overview": "📊 HQ Overview",
    "city_drilldown": "🏙️ City Drill-down",
    "deep_analysis": "🔬 Deep Analysis",
    "pipeline_monitor": "⚙️ Pipeline Monitor",
}


def get_authenticated_user() -> str:
    """Extract username from basic auth or OAuth headers."""
    # Try OAuth headers first (from Caddy forward_auth)
    try:
        headers = st.context.headers
        user_email = headers.get("x-user-email", "")
        if user_email and "@" in user_email:
            return headers.get("x-user-role", "viewer"), user_email
    except Exception:
        pass

    # Fallback to basic auth
    try:
        headers = st.context.headers
        auth = headers.get("authorization", "")
        if auth.startswith("Basic "):
            decoded = base64.b64decode(auth[6:]).decode()
            username = decoded.split(":")[0]
            return username, f"{username}@kagami.mg"
    except Exception:
        pass

    return "viewer", "viewer@kagami.mg"


def init_session_state():
    """Initialize session with user info from auth headers."""
    if "authenticated" not in st.session_state:
        username, email = get_authenticated_user()
        role = USER_ROLES.get(username, "viewer")
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["email"] = email
        st.session_state["name"] = username.capitalize()
        st.session_state["role"] = role
        st.session_state["page"] = "hq_overview"


def get_available_pages(role: str) -> list:
    """Return pages accessible to the given role."""
    return [
        key for key, required in PAGE_ACCESS.items()
        if ROLE_HIERARCHY.get(role, -1) >= ROLE_HIERARCHY.get(required, 99)
    ]


def require_role(min_role: str):
    """Stop execution if user role is insufficient."""
    user_role = st.session_state.get("role", "viewer")
    if ROLE_HIERARCHY.get(user_role, -1) < ROLE_HIERARCHY.get(min_role, 99):
        st.error(f"⛔ Access denied — {min_role} role or higher required.")
        st.info(f"Your role: **{user_role}**")
        st.stop()
