"""Local SQLite user store — app users live outside NeonDB.

Only the "admin" role gates the admin pages; everyone else is a public
viewer with open access to the (public) air quality data. Passwords are
hashed with bcrypt. The database file path can be overridden with the
KAGAMI_USERS_DB environment variable (used by tests).
"""

import os
import sqlite3
from contextlib import closing

import bcrypt


def db_path() -> str:
    """Return the SQLite database file path."""
    default = os.path.join(os.path.expanduser("~"), ".kagami", "users.db")
    return os.environ.get("KAGAMI_USERS_DB", default)


def _connect() -> sqlite3.Connection:
    path = db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _fetchone(query: str, params=()):
    with closing(_connect()) as conn:
        row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def _fetchall(query: str, params=()):
    with closing(_connect()) as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def _execute(query: str, params=()):
    with closing(_connect()) as conn:
        with conn:
            conn.execute(query, params)


def init_db():
    """Create the users table if it does not exist."""
    _execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Return True if the password matches the stored hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def get_user(username: str):
    """Return the user dict or None."""
    return _fetchone("SELECT * FROM users WHERE username = ?", (username,))


def get_user_by_email(email: str):
    """Return the user dict for an email address (used by Google login)."""
    if not email:
        return None
    return _fetchone("SELECT * FROM users WHERE email = ?", (email,))


def list_users():
    """Return all users (without password hashes)."""
    return _fetchall(
        "SELECT username, email, role, active, created_at FROM users ORDER BY username"
    )


def create_user(username: str, email: str, password: str, role: str = "viewer"):
    """Create a new user. Raises ValueError on duplicates or empty username."""
    username = (username or "").strip()
    if not username:
        raise ValueError("Username is required")
    if get_user(username):
        raise ValueError(f"Username '{username}' already exists")
    if email:
        existing = get_user_by_email(email)
        if existing:
            raise ValueError(f"Email '{email}' already used by '{existing['username']}'")
    _execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (username, email or None, hash_password(password), role),
    )


def update_password(username: str, password: str):
    """Reset a user's password."""
    _execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (hash_password(password), username),
    )


def update_role(username: str, role: str):
    """Change a user's role."""
    _execute("UPDATE users SET role = ? WHERE username = ?", (role, username))


def toggle_active(username: str, active: bool):
    """Enable or disable a user account."""
    _execute(
        "UPDATE users SET active = ? WHERE username = ?",
        (int(bool(active)), username),
    )


def delete_user(username: str):
    """Delete a user."""
    _execute("DELETE FROM users WHERE username = ?", (username,))


init_db()
