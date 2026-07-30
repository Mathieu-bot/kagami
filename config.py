"""Database configuration — NeonDB connection."""

import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text


def get_engine():
    """Return a SQLAlchemy engine connected to NeonDB."""
    url = st.secrets.get("neon_url") or os.environ.get("NEON_URL")
    if not url:
        st.error("❌ NeonDB URL not found. Set NEON_URL or .streamlit/secrets.toml")
        st.stop()
    return create_engine(url, pool_size=5, max_overflow=2)


def query(sql: str, params: dict = None) -> pd.DataFrame:
    """Execute a SQL query and return a DataFrame."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            if params:
                result = pd.read_sql(text(sql), conn, params=params)
            else:
                result = pd.read_sql(sql, conn)
        return result
    except Exception as e:
        st.error(f"❌ Query failed: {e}")
        st.code(sql, language="sql")
        st.stop()
