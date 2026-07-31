"""Integration tests against the real NeonDB (read-only SELECTs only).

These tests are skipped unless the NEON_URL environment variable is set.
They validate the actual schema and that every dashboard query returns
the expected columns with real data — catching regressions like the
data_completeness magic-number bug.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("NEON_URL"), reason="NEON_URL not set"
    ),
]

import queries as q  # noqa: E402


def test_required_tables_exist():
    df = q.query(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public'"
    )
    names = set(df["table_name"])
    for table in ("fact_aqi", "dim_city", "dim_date"):
        assert table in names, f"Missing table: {table}"


def test_list_cities_returns_data():
    df = q.list_cities()
    assert not df.empty, "dim_city is empty"
    assert "city_name" in df.columns


def test_data_completeness_within_bounds():
    df = q.data_completeness()
    assert not df.empty
    value = float(df["completeness"].iloc[0])
    assert 0 <= value <= 100, f"Completeness out of bounds: {value}"


def test_fact_aqi_schema():
    df = q.query("SELECT * FROM fact_aqi LIMIT 5")
    assert not df.empty, "fact_aqi is empty"
    for col in ("city_key", "date_key", "aqi", "pm2_5", "pm10"):
        assert col in df.columns, f"fact_aqi missing column: {col}"


def test_dashboard_queries_return_expected_columns():
    checks = [
        (q.aqi_today, ["avg_aqi"]),
        (q.aqi_yesterday, ["yesterday_avg"]),
        (q.cities_in_alert, ["alert_count"]),
        (q.data_completeness, ["completeness"]),
        (q.days_without_alert, ["days_without_alert"]),
        (q.last_ingestion, ["last_record"]),
        (q.pipeline_status, ["last_record", "status"]),
        (q.records_per_day, ["full_date", "records"]),
        (q.air_quality_map, ["latitude", "longitude", "aqi", "city_name"]),
        (q.heatmap_data, ["hour", "day_of_week", "avg_aqi"]),
        (q.boxplot_data, ["month", "aqi"]),
        (q.monthly_statistics, ["month", "median", "avg", "std"]),
        (q.seasonal_analysis, ["season", "avg_aqi", "avg_pm25"]),
        (q.weekday_weekend, ["day_type", "avg_aqi"]),
        (q.comparison_current, ["city_name", "current_aqi"]),
        (q.comparison_trend_7d, ["city_name", "full_date", "avg_aqi"]),
        (q.alert_episodes, ["city_name", "full_date", "hour", "aqi", "level"]),
        (q.alert_summary, ["city_name", "alert_count", "max_aqi", "affected_days"]),
    ]
    for func, expected_cols in checks:
        df = func()
        assert not df.empty, f"{func.__name__} returned no data"
        for col in expected_cols:
            assert col in df.columns, f"{func.__name__} missing {col}"


def test_period_queries_return_expected_columns():
    checks = [
        (q.aqi_evolution, "30d", ["full_date", "daily_avg", "trend"]),
        (q.aqi_distribution, "7d", ["aqi", "count", "percentage"]),
        (q.correlation_matrix, "30d", ["PM2.5_x_PM10", "AQI_x_PM25"]),
        (q.scatter_data, "30d", ["pm2_5", "aqi", "city_name"]),
        (q.who_exceedance_rate, "7d", ["exceedance_rate"]),
        (q.worst_pollutant, "7d", ["pollutant", "value", "who_threshold", "pct"]),
    ]
    for func, period, expected_cols in checks:
        df = func(period)
        assert not df.empty, f"{func.__name__} returned no data"
        for col in expected_cols:
            assert col in df.columns, f"{func.__name__} missing {col}"


def test_city_queries_return_expected_columns():
    city = q.list_cities()["city_name"].iloc[0]
    checks = [
        (q.city_current_aqi, [city], ["aqi"]),
        (q.city_weekly_aqi, [city], ["time", "aqi"]),
        (q.city_vs_national, [city], ["metric", "city_val", "national_val"]),
        (q.city_worst_episodes, [city, "30d"], ["full_date", "hour", "aqi", "status"]),
        (q.city_hourly_profile, [city, "30d"], ["hour", "avg_aqi", "avg_pm25"]),
        (q.city_all_pollutants, [city, "7d"], ["time", "pm2_5", "pm10"]),
        (q.city_daily_aqi, [city], ["full_date", "daily_avg"]),
        (q.city_pollutant_timeseries, [city, "30d"], ["full_date", "pm2_5", "pm10", "no2", "o3"]),
    ]
    for func, args, expected_cols in checks:
        df = func(*args)
        assert not df.empty, f"{func.__name__} returned no data"
        for col in expected_cols:
            assert col in df.columns, f"{func.__name__} missing {col}"


def test_comparison_pollutants_with_two_cities():
    cities = q.list_cities()["city_name"].tolist()
    assert len(cities) >= 2, "need at least 2 cities for A/B comparison"
    df = q.comparison_pollutants(cities[0], cities[1])
    assert not df.empty
    for col in ("city_name", "pm2_5", "pm10", "no2", "o3"):
        assert col in df.columns


def test_control_room_last_record_is_timezone_aware():
    """The W1 fix must return tz-aware UTC timestamps (no naive compare)."""
    df = q.control_room_status()
    assert not df.empty
    ts = df["last_record"].iloc[0]
    assert ts.tzinfo is not None, "last_record must be timezone-aware (UTC)"
