"""Reusable, page-local filter components.

Every filter renders its own widget inside the page that owns it (no
more dead global sidebar filters). Widgets are stored in session_state
under a unique key per page and read back through ``selected()``, which
is defensive: it never crashes on mocked/non-list values, so page smoke
tests keep exercising the real rendering paths.
"""

import streamlit as st

from i18n import t, period_label

PERIOD_OPTIONS = ["24h", "7d", "30d", "90d", "1y"]

# Canonical pollutant columns (DB column name → display label via col()).
POLLUTANT_COLUMNS = ["pm2_5", "pm10", "no2", "o3", "so2", "co", "nh3"]

# Pollutants that actually have WHO daily thresholds (drill-down panel).
WHO_POLLUTANT_COLUMNS = ["pm2_5", "pm10", "no2", "o3"]


def selected(key, default=None):
    """Return the session value for ``key``, or ``default`` when absent.

    ``default`` is returned whenever the stored value is not a list/tuple
    (e.g. a mocked widget result in tests), so callers can safely iterate.
    """
    value = st.session_state.get(key)
    if isinstance(value, (list, tuple, set)) and len(value):
        return list(value)
    return default


def period_selector(key: str = "period", default: str = "30d"):
    """A period segmented control (24h / 7d / 30d / 90d / 1y), labelled in the current language."""
    options = PERIOD_OPTIONS
    return st.segmented_control(
        t("common.period"), options,
        default=default if default in options else "30d",
        key=key, format_func=period_label,
    )


def cities_multiselect(options, key: str, default_all: bool = True):
    """A city multiselect returning the chosen city names.

    Returns ``None`` when nothing is selected (meaning "all cities"),
    which is what callers should pass to filtering logic.
    """
    if not options:
        return None
    selected_now = st.pills(
        t("common.cities"), options, selection_mode="multi",
        default=options if default_all else [],
        key=key,
    )
    return selected_now or None


def pollutants_multiselect(key: str, columns=None, default_all: bool = True):
    """A pollutant multiselect over the given DB columns."""
    cols = columns or POLLUTANT_COLUMNS
    options = list(cols)
    selected_now = st.pills(
        t("common.pollutants"), options, selection_mode="multi",
        default=options if default_all else [],
        key=key,
    )
    return selected_now or None


def active_columns(selected_list, available, df=None):
    """Intersect a user selection with the available columns.

    ``None``/empty selection means "keep everything". When ``df`` is
    given, the result is also intersected with the columns actually
    present in the DataFrame, so a column that a query did not return
    can never leak into a plotly call.
    """
    if df is not None:
        present = list(df.columns)
        available = [c for c in available if c in present]
    if not selected_list:
        return list(available)
    return [c for c in available if c in selected_list]


def horizon_selector(key: str = "forecast_horizon", default: int = 7):
    """Forecast horizon in days (7 / 14 / 30)."""
    options = [7, 14, 30]
    index = options.index(default) if default in options else 0
    return st.selectbox(
        t("forecast.horizon"),
        options,
        index=index,
        key=key,
        format_func=lambda d: t("forecast.days", d=d),
    )
