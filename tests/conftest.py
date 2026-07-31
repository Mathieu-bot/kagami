"""Shared fixtures and mocks for all tests."""

import os
import sys
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from contextlib import ExitStack

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def reset_engine_cache():
    """Reset the cached SQLAlchemy engine so tests stay isolated."""
    import config
    config._engine = None
    yield
    config._engine = None


@pytest.fixture
def mock_query():
    """Patch the `query` function so no real DB calls happen in unit tests."""
    with patch("queries.query") as mock:
        yield mock


@pytest.fixture
def mock_streamlit():
    """Mock streamlit functions that would otherwise crash outside the runtime."""
    targets = [
        "streamlit.error", "streamlit.info", "streamlit.warning",
        "streamlit.success", "streamlit.stop", "streamlit.progress",
        "streamlit.metric", "streamlit.subheader", "streamlit.markdown",
        "streamlit.caption", "streamlit.divider", "streamlit.selectbox",
        "streamlit.multiselect", "streamlit.radio", "streamlit.dataframe",
        "streamlit.plotly_chart", "streamlit.expander", "streamlit.container",
        "streamlit.columns", "streamlit.sidebar", "streamlit.spinner",
        "streamlit.cache_data", "streamlit.cache_resource",
        "streamlit.page_link", "streamlit.title", "streamlit.set_page_config",
    ]
    with ExitStack() as stack:
        for target in targets:
            stack.enter_context(patch(target))

        def _make_columns(n):
            """Return n context-manager column mocks."""
            count = n if isinstance(n, int) else len(n)
            return [MagicMock() for _ in range(count)]

        with patch("streamlit.session_state", {}), \
             patch("streamlit.context", create=True), \
             patch("streamlit.columns", side_effect=_make_columns):
            yield


@pytest.fixture
def sample_aqi_df():
    """Sample DataFrame mimicking a query result."""
    return pd.DataFrame({
        "avg_aqi": [1.25],
        "city_name": ["Antananarivo"],
    })


@pytest.fixture
def sample_monthly_stats():
    """Sample monthly statistics DataFrame."""
    return pd.DataFrame([{
        "month": "2025-01", "count": 4320,
        "min": 1.0, "p25": 1.0, "median": 1.0,
        "avg": 1.12, "std": 0.33, "p75": 1.0, "max": 3.0,
    }])
