"""Dashboard 6 — User Management (admin only).

Manage the local app users (SQLite): create users, reset passwords,
change roles, enable/disable, and delete accounts.
"""

import streamlit as st

from auth import init_session_state, require_role
from sidebar import render_sidebar
from users import (
    list_users,
    create_user,
    update_password,
    update_role,
    toggle_active,
    delete_user,
)

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — User Management",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
require_role("admin")
render_sidebar()

st.title("👥 User Management")
st.caption("_Manage admin access — users are stored locally, NeonDB stays untouched._")

# ─── Create user ───
with st.expander("➕ Create user", expanded=True):
    with st.form("create_user_form"):
        c1, c2 = st.columns(2)
        new_username = c1.text_input("Username", key="um_username")
        new_email = c2.text_input("Email (optional, for Google login)", key="um_email")
        c3, c4 = st.columns(2)
        new_password = c3.text_input("Password", type="password", key="um_password")
        new_role = c4.selectbox("Role", ["viewer", "admin"], key="um_role")
        if st.form_submit_button("Create user"):
            if not new_username or not new_password:
                st.error("Username and password are required.")
            else:
                try:
                    create_user(new_username, new_email or None, new_password, new_role)
                    st.success(f"User '{new_username}' created.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

# ─── Users table ───
st.subheader("Existing users")
users = list_users()
if not users:
    st.info("No users yet — create the first one above.")
else:
    st.dataframe(
        [{"username": u["username"], "email": u["email"] or "-",
          "role": u["role"], "active": "✅" if u["active"] else "❌",
          "created_at": u["created_at"]} for u in users],
        use_container_width=True,
        hide_index=True,
    )

    for user in users:
        with st.expander(f"{user['username']} — {user['role']}"):
            c1, c2 = st.columns(2)
            with c1:
                new_role = st.selectbox(
                    "Role", ["viewer", "admin"],
                    index=0 if user["role"] == "viewer" else 1,
                    key=f"role_{user['username']}",
                )
                if st.button("Update role", key=f"btn_role_{user['username']}"):
                    update_role(user["username"], new_role)
                    st.success(f"Role of '{user['username']}' set to {new_role}.")
                    st.rerun()
            with c2:
                new_active = st.checkbox(
                    "Active", value=bool(user["active"]),
                    key=f"active_{user['username']}",
                )
                if st.button("Toggle active", key=f"btn_active_{user['username']}"):
                    toggle_active(user["username"], new_active)
                    st.success(f"'{user['username']}' active = {new_active}.")
                    st.rerun()

            pwd = st.text_input(
                "New password", type="password", key=f"pwd_{user['username']}",
            )
            c3, c4 = st.columns(2)
            with c3:
                if st.button("Reset password", key=f"btn_pwd_{user['username']}"):
                    if pwd:
                        update_password(user["username"], pwd)
                        st.success(f"Password of '{user['username']}' updated.")
                    else:
                        st.warning("Enter a new password first.")
            with c4:
                if st.button("🗑 Delete", key=f"btn_del_{user['username']}"):
                    delete_user(user["username"])
                    st.success(f"User '{user['username']}' deleted.")
                    st.rerun()
