"""Shared fixtures and mocks for all tests."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from contextlib import ExitStack


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
    ]
    with ExitStack() as stack:
        for target in targets:
            stack.enter_context(patch(target))
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=None)
        mock_col.__exit__ = MagicMock(return_value=None)
        with patch("streamlit.session_state", {}), \
             patch("streamlit.context", create=True), \
             patch("streamlit.columns", return_value=[mock_col, mock_col]):
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
