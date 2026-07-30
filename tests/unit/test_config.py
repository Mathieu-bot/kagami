"""Unit tests for the config module — NeonDB connection."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


class TestGetEngine:
    """Verify engine creation."""

    def test_engine_created_with_url(self):
        """get_engine() should return a SQLAlchemy engine."""
        with patch("config.st") as mock_st:
            mock_st.secrets = {"neon_url": "postgresql://test:test@localhost/test"}
            from config import get_engine
            engine = get_engine()
            assert engine is not None
            rendered = engine.url.render_as_string(hide_password=False)
            assert rendered.startswith("postgresql://test:test@localhost/")

    def test_engine_raises_without_url(self):
        """get_engine() should raise DatabaseError when no URL is configured."""
        with patch("config.st") as mock_st:
            mock_st.secrets = {}
            from config import get_engine, DatabaseError
            with pytest.raises(DatabaseError, match="NeonDB URL not found"):
                get_engine()


class TestQuery:
    """Verify the query helper function."""

    def test_query_returns_dataframe(self):
        """query() should return a DataFrame on success."""
        mock_df = pd.DataFrame({"col": [1, 2, 3]})
        with patch("config.st"), \
             patch("config.create_engine") as mock_engine:
            mock_conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
            with patch("pandas.read_sql", return_value=mock_df):
                from config import query
                result = query("SELECT 1")
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 3

    def test_query_handles_errors(self):
        """query() should raise DatabaseError on failure."""
        with patch("config.st") as mock_st, \
             patch("config.create_engine") as mock_engine:
            mock_engine.return_value.connect.side_effect = Exception("DB down")
            from config import query, DatabaseError
            with pytest.raises(DatabaseError, match="Query failed"):
                query("SELECT 1")
