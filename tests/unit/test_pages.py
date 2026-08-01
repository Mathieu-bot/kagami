"""Smoke tests — execute the real code path of every page.

Each page module is loaded fresh (importlib) so its top-level body runs:
auth, sidebar, DB queries (mocked), chart building, and rendering (mocked).
This catches missing dependencies, layout errors, and bad column access.
"""

import os
import sys
import importlib.util

import pandas as pd
import pytest

from tests.conftest import StopPage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

PAGES = {
    "app": os.path.join(os.path.dirname(__file__), "..", "..", "app.py"),
    "city_drilldown": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "city_drilldown.py"),
    "deep_analysis": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "deep_analysis.py"),
    "pipeline_monitor": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "pipeline_monitor.py"),
    "user_management": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "user_management.py"),
    "city_comparison": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "city_comparison.py"),
    "alerts_history": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "alerts_history.py"),
    "forecast": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "forecast.py"),
    "data_explorer": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "data_explorer.py"),
    "citizens": os.path.join(
        os.path.dirname(__file__), "..", "..", "pages", "citizens.py"),
}


@pytest.fixture
def mega_dataframe():
    """A 2-row DataFrame with every column any page accesses.

    Returning it for every mocked query function exercises the real page
    code paths (trendlines, pivots, gradients, metrics) without a DB.
    """
    return pd.DataFrame({
        "city_name": ["Antananarivo", "Toamasina"],
        "current_aqi": [1.8, 2.6],
        "avg_aqi": [1.5, 2.1],
        "yesterday_avg": [1.2, 2.0],
        "time": ["2026-07-31 08:00:00", "2026-07-31 09:00:00"],
        "alert_count": [0, 1],
        "completeness": [96.5, 96.5],
        "days_without_alert": [12, 12],
        "full_date": ["2026-07-30", "2026-07-31"],
        "daily_avg": [1.4, 1.6],
        "trend": [1.5, 1.55],
        "latitude": [-18.91, -18.15],
        "longitude": [47.52, 49.3],
        "aqi": [1, 2],
        "status": ["Good", "Moderate"],
        "count": [100, 120],
        "percentage": [45.0, 55.0],
        "pollutant": ["PM2.5", "PM2.5"],
        "value": [14.2, 14.2],
        "who_threshold": [15.0, 15.0],
        "pct": [94.7, 94.7],
        "exceedance_rate": [3.5, 3.5],
        "last_record": ["2026-07-31 09:30:00", "2026-07-31 09:30:00"],
        "month": ["2026-07", "2026-07"],
        "hour": [8, 9],
        "day_of_week": ["Monday", "Tuesday"],
        "max_aqi": [3, 4],
        "affected_days": [1, 2],
        "level": ["Alert", "Severe"],
        "pm2_5": [12.0, 20.0],
        "pm10": [20.0, 30.0],
        "no2": [8.0, 9.0],
        "o3": [30.0, 32.0],
        "so2": [1.0, 1.2],
        "co": [0.4, 0.5],
        "nh3": [2.0, 2.1],
        "metric": ["PM2.5", "AQI"],
        "city_val": [14.2, 1.5],
        "national_val": [16.0, 1.8],
        "season": ["Dry", "Dry"],
        "day_type": ["Weekday", "Weekday"],
        "avg_pm25": [12.5, 13.0],
        "avg_pm10": [22.0, 24.0],
        "avg_o3": [31.0, 32.0],
        "avg_no2": [8.5, 9.0],
        "records": [140, 142],
        "min": [1.0, 1.0],
        "p25": [1.0, 1.0],
        "median": [1.5, 1.5],
        "avg": [1.5, 1.6],
        "std": [0.3, 0.3],
        "p75": [2.0, 2.0],
        "max": [3.0, 3.0],
        "PM2.5_x_PM10": [0.85, 0.85],
        "AQI_x_PM25": [0.9, 0.9],
    })


def _load_page(module_name: str, path: str):
    """Execute a page module body via a fresh import."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def run_page(mock_streamlit, mock_query, mega_dataframe):
    """Return a helper that runs a page with admin session + mocked queries."""
    import streamlit as st

    st.session_state["authenticated"] = True
    st.session_state["role"] = "admin"
    st.session_state["name"] = "Admin"

    mock_query.return_value = mega_dataframe

    def _run(name: str):
        try:
            return _load_page(f"smoke_{name}", PAGES[name])
        except StopPage:
            # Page deliberately halted (e.g. empty-data guard) — valid render.
            return None

    return _run


@pytest.mark.parametrize("page_name", list(PAGES.keys()))
def test_page_renders_with_data(page_name, run_page):
    """Every page should render end-to-end with mocked non-empty data."""
    run_page(page_name)  # Raises if any page code path crashes


def test_hq_overview_handles_db_error(run_page, mock_query):
    """A DatabaseError should surface as st.error, not a raw traceback."""
    from config import DatabaseError
    import streamlit as st

    mock_query.side_effect = DatabaseError("connection refused")
    run_page("app")
    st.error.assert_called_once()


def test_last_active_admin_guard(run_page):
    """A sole active admin cannot be demoted/deactivated/deleted."""
    import sys

    run_page("user_management")
    last_admin = sys.modules["smoke_user_management"]._last_active_admin

    sole_admin = [{"username": "root", "role": "admin", "active": True}]
    assert last_admin(sole_admin[0], sole_admin) is True

    admin_plus_viewer = [
        {"username": "root", "role": "admin", "active": True},
        {"username": "bob", "role": "viewer", "active": True},
    ]
    assert last_admin(admin_plus_viewer[0], admin_plus_viewer) is True

    two_admins = [
        {"username": "root", "role": "admin", "active": True},
        {"username": "carol", "role": "admin", "active": True},
    ]
    assert last_admin(two_admins[0], two_admins) is False

    inactive_sole_admin = [{"username": "root", "role": "admin", "active": False}]
    assert last_admin(inactive_sole_admin[0], inactive_sole_admin) is False


def test_city_comparison_ab_mode_renders(run_page):
    """C1: the A/B head-to-head branch (radio '2cities') must render.

    The default smoke test only exercises the "all cities" branch because
    the mocked radio returns a non-string value. Force the radio to
    "2cities" AND make the column selectboxes return real city names
    (a MagicMock would crash pandas comparisons in the page).
    """
    from unittest.mock import patch

    class _CityCol:
        def __init__(self, city):
            self._city = city

        def selectbox(self, *args, **kwargs):
            return self._city

        def metric(self, *args, **kwargs):
            return None

    cols = [_CityCol("Antananarivo"), _CityCol("Toamasina")]
    with patch("streamlit.radio", return_value="2cities"), \
         patch("streamlit.columns", return_value=cols):
        run_page("city_comparison")  # Raises if the A/B path crashes
