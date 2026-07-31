"""Database configuration — NeonDB connection.

Raises exceptions on failure so callers (pages, scripts) can handle errors
gracefully instead of calling st.stop() at the data layer.
"""

import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text


class DatabaseError(Exception):
    """Raised when a database operation fails."""

# Cached engine (module-level singleton) so the connection pool
# is created once and reused across queries instead of per-call.
_engine = None


def get_engine():
    """Return a cached SQLAlchemy engine connected to NeonDB.

    Reads the connection URL from st.secrets (Streamlit cloud) or
    NEON_URL environment variable (local / CI). The engine is created
    once and reused, keeping the connection pool alive.

    Raises
    ------
    DatabaseError
        If no database URL is configured.
    """
    global _engine
    if _engine is not None:
        return _engine
    try:
        url = st.secrets.get("neon_url") or os.environ.get("NEON_URL")
    except Exception:
        url = os.environ.get("NEON_URL")
    if not url:
        raise DatabaseError(
            "NeonDB URL not found. Set NEON_URL env var or "
            "add neon_url to .streamlit/secrets.toml"
        )
    # pool_pre_ping: drop stale pooled connections on the small VM where
    # idle connections may be killed by the server / network middleboxes.
    _engine = create_engine(url, pool_size=5, max_overflow=2, pool_pre_ping=True)
    return _engine


def query(sql: str, params: dict = None, read_only: bool = True) -> pd.DataFrame:
    """Execute a SQL query and return a DataFrame.

    Parameters
    ----------
    sql : str
        SQL statement with optional :param placeholders.
    params : dict, optional
        Bind parameter values (e.g. {"city_name": "Antananarivo"}).
    read_only : bool, default True
        Run the statement inside a ``READ ONLY`` transaction so any
        accidental write (INSERT/UPDATE/DELETE/DDL) fails at the
        database level. The dashboard only reads data, so the default
        is always read-only.

    Returns
    -------
    pd.DataFrame
        Query results.

    Raises
    ------
    DatabaseError
        If the query fails.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            if read_only:
                conn.execute(text("SET TRANSACTION READ ONLY"))
            if params:
                result = pd.read_sql(text(sql), conn, params=params)
            else:
                result = pd.read_sql(sql, conn)
        return result
    except Exception as e:
        raise DatabaseError(f"Query failed: {e}") from e
