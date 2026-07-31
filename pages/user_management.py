"""Dashboard 6 — User Management (admin only).

Manage the local app users (SQLite): create users, reset passwords,
change roles, enable/disable, and delete accounts.
"""

import streamlit as st

from auth import init_session_state, require_role
from sidebar import render_sidebar
from i18n import t, col
from users import (
    list_users,
    create_user,
    update_password,
    update_role,
    toggle_active,
    delete_user,
)
from ui import page_icon

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — User Management",
    page_icon=page_icon("user_management"),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
require_role("admin")
render_sidebar()

st.title(t("users.title"))
st.caption(t("users.caption"))


def _role_display(role: str) -> str:
    """Translate a role id for display (values stay English in the store)."""
    return t("auth.role_admin") if role == "admin" else t("auth.role_viewer")


# ─── Create user ───
with st.expander(t("users.create"), expanded=True):
    with st.form("create_user_form"):
        c1, c2 = st.columns(2)
        new_username = c1.text_input(t("auth.username"), key="um_username")
        new_email = c2.text_input(t("users.email_optional"), key="um_email")
        c3, c4 = st.columns(2)
        new_password = c3.text_input(t("auth.password"), type="password", key="um_password")
        new_role = c4.selectbox(col("role"), ["viewer", "admin"], key="um_role",
                                format_func=_role_display)
        if st.form_submit_button(t("users.create_btn")):
            if not new_username or not new_password:
                st.error(t("users.required"))
            else:
                try:
                    create_user(new_username, new_email or None, new_password, new_role)
                    st.success(t("users.created", name=new_username))
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

# ─── Users table ───
st.subheader(t("users.existing"))
users = list_users()
if not users:
    st.info(t("users.none"))
else:
    # ─── Filters: search + role + active only ───
    with st.expander(t("common.filters"), expanded=False):
        search = st.text_input(t("users.search"), key="um_search")
        role_filter = st.selectbox(
            t("users.role_filter"), ["all", "viewer", "admin"], index=0,
            key="um_role_filter", format_func=lambda r: _role_display(r) if r != "all"
            else t("users.role_all"),
        )
        active_only = st.checkbox(t("users.active_only"), key="um_active_only")

    filtered = users
    if isinstance(search, str) and search.strip():
        needle = search.strip().lower()
        filtered = [u for u in filtered
                    if needle in (u["username"] or "").lower()
                    or needle in (u["email"] or "").lower()]
    if role_filter != "all":
        filtered = [u for u in filtered if u["role"] == role_filter]
    if active_only:
        filtered = [u for u in filtered if u["active"]]

    if not filtered:
        st.info(t("users.none"))
    else:
        st.dataframe(
            [{"username": u["username"], "email": u["email"] or "-",
              "role": _role_display(u["role"]),
              "active": ":material/check_circle:" if u["active"] else ":material/cancel:",
              "created_at": u["created_at"]} for u in filtered],
            use_container_width=True,
            hide_index=True,
            column_config={"username": col("username"), "email": col("email"),
                           "role": col("role"), "active": col("active"),
                           "created_at": col("created_at")},
        )

    for user in users:
        with st.expander(f"{user['username']} — {_role_display(user['role'])}"):
            c1, c2 = st.columns(2)
            with c1:
                new_role = st.selectbox(
                    col("role"), ["viewer", "admin"],
                    index=0 if user["role"] == "viewer" else 1,
                    key=f"role_{user['username']}",
                    format_func=_role_display,
                )
                if st.button(t("users.update_role"), key=f"btn_role_{user['username']}"):
                    update_role(user["username"], new_role)
                    st.success(t("users.role_updated", name=user["username"], role=_role_display(new_role)))
                    st.rerun()
            with c2:
                new_active = st.checkbox(
                    t("users.active"), value=bool(user["active"]),
                    key=f"active_{user['username']}",
                )
                if st.button(t("users.toggle_active"), key=f"btn_active_{user['username']}"):
                    toggle_active(user["username"], new_active)
                    st.success(t("users.toggled", name=user["username"], active=new_active))
                    st.rerun()

            pwd = st.text_input(
                t("users.new_password"), type="password", key=f"pwd_{user['username']}",
            )
            c3, c4 = st.columns(2)
            with c3:
                if st.button(t("users.reset_password"), key=f"btn_pwd_{user['username']}"):
                    if pwd:
                        update_password(user["username"], pwd)
                        st.success(t("users.password_updated", name=user["username"]))
                    else:
                        st.warning(t("users.enter_password"))
            with c4:
                if st.button(t("users.delete"), key=f"btn_del_{user['username']}"):
                    delete_user(user["username"])
                    st.success(t("users.deleted", name=user["username"]))
                    st.rerun()
