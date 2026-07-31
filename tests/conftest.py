"""Shared fixtures and mocks for all tests."""

import os
import sys
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from contextlib import ExitStack


class StopPage(BaseException):
    """Mimics streamlit.StopException: halts a page run without failing it."""

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Point the local user store at a throwaway file for the whole test session.
os.environ.setdefault("KAGAMI_USERS_DB", os.path.join(tempfile.mkdtemp(), "users.db"))


@pytest.fixture(autouse=True)
def reset_engine_cache(request):
    """Reset the cached SQLAlchemy engine so unit tests stay isolated.

    Integration tests reuse a single engine across the session (faster).
    """
    if "integration" in request.keywords:
        yield
        return
    import config
    config._engine = None
    yield
    config._engine = None


@pytest.fixture
def users_db(tmp_path):
    """Point the user store at a fresh temp DB per test."""
    old = os.environ.get("KAGAMI_USERS_DB")
    os.environ["KAGAMI_USERS_DB"] = str(tmp_path / "users.db")
    import users
    users.init_db()
    yield users
    if old is None:
        os.environ.pop("KAGAMI_USERS_DB", None)
    else:
        os.environ["KAGAMI_USERS_DB"] = old


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
        "streamlit.success", "streamlit.progress",
        "streamlit.metric", "streamlit.subheader", "streamlit.markdown",
        "streamlit.caption", "streamlit.divider", "streamlit.selectbox",
        "streamlit.multiselect", "streamlit.radio", "streamlit.dataframe",
        "streamlit.plotly_chart", "streamlit.expander", "streamlit.container",
        "streamlit.columns", "streamlit.sidebar", "streamlit.spinner",
        "streamlit.page_link", "streamlit.title", "streamlit.set_page_config",
        "streamlit.rerun", "streamlit.link_button", "streamlit.form",
        "streamlit.text_input", "streamlit.download_button", "streamlit.date_input",
        "streamlit.number_input", "streamlit.slider", "streamlit.text_area",
    ]
    with ExitStack() as stack:
        for target in targets:
            stack.enter_context(patch(target))
        # Widgets that would trigger real actions if truthy stay False by default.
        stack.enter_context(patch("streamlit.button", return_value=False))
        stack.enter_context(patch("streamlit.form_submit_button", return_value=False))
        stack.enter_context(patch("streamlit.checkbox", return_value=False))
        # st.stop() halts the page, exactly like the real runtime.
        stack.enter_context(patch("streamlit.stop", side_effect=StopPage))

        def _cache_pass(*args, **kwargs):
            """Mimic @st.cache_data/@st.cache_resource: return the function
            unchanged so tests exercise the real code path (no caching)."""
            if args and callable(args[0]):
                return args[0]

            def _decorator(func):
                return func
            return _decorator

        stack.enter_context(patch("streamlit.cache_data", side_effect=_cache_pass))
        stack.enter_context(patch("streamlit.cache_resource", side_effect=_cache_pass))

        def _fragment(*args, **kwargs):
            """Mimic @st.fragment: return the wrapped function unchanged."""
            if args and callable(args[0]):
                return args[0]
            def _decorator(func):
                return func
            return _decorator

        stack.enter_context(patch("streamlit.fragment", side_effect=_fragment))

        def _make_columns(n):
            """Return n context-manager column mocks."""
            count = n if isinstance(n, int) else len(n)
            return [MagicMock() for _ in range(count)]

        def _make_tabs(names):
            """Return one context-manager mock per tab."""
            return [MagicMock() for _ in names]

        stack.enter_context(patch("streamlit.columns", side_effect=_make_columns))
        stack.enter_context(patch("streamlit.tabs", side_effect=_make_tabs))

        with patch("streamlit.session_state", {}), \
             patch("streamlit.context", create=True), \
             patch("streamlit.query_params", {}):
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
