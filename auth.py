"""Authentication and role management via Caddy OAuth headers."""

import streamlit as st
from config import query

# Role hierarchy for page access
ROLE_HIERARCHY = {
    "viewer": 0,
    "analyst": 1,
    "admin": 2,
}

# Page access rules: {page_key: min_role}
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


def get_user_info() -> dict:
    """Extract user info from Caddy OAuth headers or simulate for dev."""
    user_email = st.query_params.get("X-User-Email", [None])
    user_name = st.query_params.get("X-User-Name", [None])
    user_role = st.query_params.get("X-User-Role", [None])

    # Extract from request headers (when behind Caddy)
    try:
        headers = st.context.headers if hasattr(st, 'context') else {}
        user_email = headers.get("X-User-Email", user_email)
        user_name = headers.get("X-User-Name", user_name)
        user_role = headers.get("X-User-Role", user_role)
    except Exception:
        pass

    return {
        "email": user_email or "dev@local",
        "name": user_name or "Developer",
        "role": user_role or "admin",  # Default to admin in dev
    }


def get_user_role(email: str) -> str:
    """Fetch user role from NeonDB users table."""
    try:
        df = query("SELECT role FROM users WHERE email = :email", {"email": email})
        if not df.empty:
            return df["role"].iloc[0]
    except Exception:
        pass
    return "viewer"  # Default role


def check_page_access(page_key: str, role: str) -> bool:
    """Check if a role has access to a specific page."""
    required_role = PAGE_ACCESS.get(page_key, "admin")
    required_level = ROLE_HIERARCHY.get(required_role, 99)
    user_level = ROLE_HIERARCHY.get(role, -1)
    return user_level >= required_level


def get_available_pages(role: str) -> list:
    """Return list of page keys accessible to this role."""
    return [
        key for key, required in PAGE_ACCESS.items()
        if ROLE_HIERARCHY.get(role, -1) >= ROLE_HIERARCHY.get(required, 99)
    ]


def init_session_state():
    """Initialize session state with user info."""
    if "authenticated" not in st.session_state:
        user = get_user_info()
        st.session_state["authenticated"] = True
        st.session_state["email"] = user["email"]
        st.session_state["name"] = user["name"]
        st.session_state["role"] = get_user_role(user["email"])
        st.session_state["page"] = "hq_overview"


def require_role(min_role: str):
    """Decorator-style check — stop if user role is insufficient."""
    user_role = st.session_state.get("role", "viewer")
    if ROLE_HIERARCHY.get(user_role, -1) < ROLE_HIERARCHY.get(min_role, 99):
        st.error(f"⛔ Access denied — {min_role} role or higher required.")
        st.info(f"Your role: **{user_role}**")
        st.stop()
