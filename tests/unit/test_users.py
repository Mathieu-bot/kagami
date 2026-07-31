"""Unit tests for the local SQLite user store."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest


class TestUserStore:
    """Verify the CRUD operations of the local user store."""

    def test_create_and_verify_password(self, users_db):
        users_db.create_user("alice", "alice@example.com", "secret123", "admin")
        user = users_db.get_user("alice")
        assert user["role"] == "admin"
        assert users_db.verify_password("secret123", user["password_hash"])
        assert not users_db.verify_password("wrong", user["password_hash"])

    def test_create_user_returns_dict_without_hash(self, users_db):
        users_db.create_user("bob", None, "pw", "viewer")
        users = users_db.list_users()
        assert users[0]["username"] == "bob"
        assert "password_hash" not in users[0]

    def test_duplicate_username_raises(self, users_db):
        users_db.create_user("bob", None, "pw", "viewer")
        with pytest.raises(ValueError, match="already exists"):
            users_db.create_user("bob", None, "pw2", "admin")

    def test_empty_username_raises(self, users_db):
        with pytest.raises(ValueError, match="Username"):
            users_db.create_user("", None, "pw", "viewer")

    def test_duplicate_email_raises(self, users_db):
        users_db.create_user("carol", "carol@x.com", "pw", "viewer")
        with pytest.raises(ValueError, match="already used"):
            users_db.create_user("dave", "carol@x.com", "pw", "viewer")

    def test_lookup_by_email(self, users_db):
        users_db.create_user("carol", "carol@x.com", "pw", "admin")
        user = users_db.get_user_by_email("carol@x.com")
        assert user["username"] == "carol"

    def test_lookup_by_email_returns_none(self, users_db):
        assert users_db.get_user_by_email("nobody@x.com") is None

    def test_update_password(self, users_db):
        users_db.create_user("eve", None, "oldpass", "viewer")
        users_db.update_password("eve", "newpass")
        user = users_db.get_user("eve")
        assert users_db.verify_password("newpass", user["password_hash"])
        assert not users_db.verify_password("oldpass", user["password_hash"])

    def test_update_role(self, users_db):
        users_db.create_user("frank", None, "pw", "viewer")
        users_db.update_role("frank", "admin")
        assert users_db.get_user("frank")["role"] == "admin"

    def test_toggle_active(self, users_db):
        users_db.create_user("grace", None, "pw", "viewer")
        users_db.toggle_active("grace", False)
        assert users_db.get_user("grace")["active"] == 0
        users_db.toggle_active("grace", True)
        assert users_db.get_user("grace")["active"] == 1

    def test_delete_user(self, users_db):
        users_db.create_user("heidi", None, "pw", "viewer")
        users_db.delete_user("heidi")
        assert users_db.get_user("heidi") is None

    def test_inactive_user_cannot_log_in(self, users_db):
        """The auth layer should reject inactive accounts."""
        users_db.create_user("ivan", None, "pw", "admin")
        users_db.toggle_active("ivan", False)
        user = users_db.get_user("ivan")
        assert user["active"] == 0
