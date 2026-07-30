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


def get_engine():
    """Return a SQLAlchemy engine connected to NeonDB.

    Reads the connection URL from st.secrets (Streamlit cloud) or
    NEON_URL environment variable (local / CI).

    Raises
    ------
    DatabaseError
        If no database URL is configured.
    """
    try:
        url = st.secrets.get("neon_url") or os.environ.get("NEON_URL")
    except Exception:
        url = os.environ.get("NEON_URL")
    if not url:
        raise DatabaseError(
            "NeonDB URL not found. Set NEON_URL env var or "
            "add neon_url to .streamlit/secrets.toml"
        )
    return create_engine(url, pool_size=5, max_overflow=2)


def query(sql: str, params: dict = None) -> pd.DataFrame:
    """Execute a SQL query and return a DataFrame.

    Parameters
    ----------
    sql : str
        SQL statement with optional :param placeholders.
    params : dict, optional
        Bind parameter values (e.g. {"city_name": "Antananarivo"}).

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
            if params:
                result = pd.read_sql(text(sql), conn, params=params)
            else:
                result = pd.read_sql(sql, conn)
        return result
    except Exception as e:
        raise DatabaseError(f"Query failed: {e}") from e
