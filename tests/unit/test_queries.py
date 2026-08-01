"""Unit tests for the queries module — all SQL functions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pandas as pd
from unittest.mock import patch


# ─── All query functions to test ───
QUERY_FUNCTIONS = [
    ("aqi_today", ["avg_aqi"]),
    ("aqi_yesterday", ["yesterday_avg"]),
    ("cities_in_alert", ["alert_count"]),
    ("data_completeness", ["completeness"]),
    ("days_without_alert", ["days_without_alert"]),
    ("last_ingestion", ["last_record"]),
    ("pipeline_status", ["last_record", "status"]),
    ("control_room_status", ["city_name", "aqi", "last_record"]),
    ("citizen_who_exceedance", ["city_name", "exceedance_rate"]),
    ("list_cities", ["city_name"]),
    ("get_all_cities", ["city_key", "city_name", "latitude", "longitude"]),
    ("records_per_day", ["full_date", "records"]),
    ("seasonal_analysis", ["season", "avg_aqi", "avg_pm25", "avg_pm10", "avg_no2", "avg_o3"]),
    ("weekday_weekend", ["day_type", "avg_aqi", "avg_pm25", "avg_pm10", "avg_no2", "avg_o3"]),
    ("boxplot_data", ["month", "aqi"]),
    ("monthly_statistics", ["month", "median", "avg", "std"]),
    # Newer comparison / alert / forecast queries (C1 coverage)
    ("comparison_current", ["city_name", "current_aqi"]),
    ("comparison_trend_7d", ["city_name", "full_date", "avg_aqi"]),
    ("alert_episodes", ["city_name", "full_date", "hour", "aqi", "level"]),
    ("alert_summary", ["city_name", "alert_count", "max_aqi", "affected_days"]),
]


class TestQueryFunctionsReturnDataFrame:
    """Verify every query function returns a proper DataFrame."""

    @pytest.mark.parametrize("func_name,expected_cols", QUERY_FUNCTIONS)
    def test_function_returns_dataframe(self, func_name, expected_cols, mock_query):
        """Each query function should return a DataFrame with expected columns."""
        import queries as q

        # Build a mock return matching the function's expected columns
        mock_data = {col: [f"dummy_{col}"] for col in expected_cols}
        mock_query.return_value = pd.DataFrame(mock_data)

        func = getattr(q, func_name)
        result = func()

        assert isinstance(result, pd.DataFrame), f"{func_name} did not return a DataFrame"
        for col in expected_cols:
            assert col in result.columns, f"{func_name} missing column {col}"


class TestFunctionsWithPeriod:
    """Functions that take a period parameter."""

    @pytest.mark.parametrize("func_name,period,expected_cols", [
        ("aqi_evolution", "30d", ["full_date", "daily_avg", "trend"]),
        ("best_hour_per_city", "30d", ["city_name", "best_hour", "avg_aqi"]),
        ("aqi_distribution", "7d", ["aqi", "count", "percentage"]),
        ("correlation_matrix", "30d", ["PM2.5_x_PM10", "PM2.5_x_SO2", "CO_x_NH3",
                                       "AQI_x_PM25", "AQI_x_O3"]),
        ("scatter_data", "30d", ["pm2_5", "aqi", "city_name"]),
        ("who_exceedance_rate", "7d", ["exceedance_rate"]),
        ("worst_pollutant", "7d", ["pollutant", "value", "who_threshold", "pct"]),
    ])
    def test_with_period(self, func_name, period, expected_cols, mock_query):
        """Functions with period should still return correct columns."""
        import queries as q

        mock_data = {col: [f"dummy"] for col in expected_cols}
        mock_query.return_value = pd.DataFrame(mock_data)

        func = getattr(q, func_name)
        result = func(period)

        assert isinstance(result, pd.DataFrame)
        for col in expected_cols:
            assert col in result.columns, f"{func_name} missing {col}"


class TestFunctionsWithCity:
    """Functions that take a city_name parameter."""

    @pytest.mark.parametrize("func_name,expected_cols", [
        ("city_current_aqi", ["aqi"]),
        ("city_weekly_aqi", ["time", "aqi"]),
        ("city_vs_national", ["metric", "city_val", "national_val"]),
        ("city_worst_episodes", ["full_date", "hour", "aqi", "pm2_5", "pm10", "no2", "o3", "so2", "status"]),
        ("city_daily_aqi", ["full_date", "daily_avg"]),
        ("city_pollutant_timeseries", ["full_date", "pm2_5", "pm10", "no2", "o3", "so2", "co", "nh3"]),
    ])
    def test_with_city(self, func_name, expected_cols, mock_query):
        """Functions with city parameter should work correctly."""
        import queries as q

        mock_data = {col: [f"dummy"] for col in expected_cols}
        mock_query.return_value = pd.DataFrame(mock_data)

        func = getattr(q, func_name)
        result = func("Antananarivo")

        assert isinstance(result, pd.DataFrame)
        for col in expected_cols:
            assert col in result.columns

    @pytest.mark.parametrize("func_name,expected_cols", [
        ("comparison_pollutants", ["city_name", "pm2_5", "pm10", "no2", "o3"]),
    ])
    def test_with_two_cities(self, func_name, expected_cols, mock_query):
        """Functions taking two city parameters should work correctly."""
        import queries as q

        mock_data = {col: [f"dummy"] for col in expected_cols}
        mock_query.return_value = pd.DataFrame(mock_data)

        func = getattr(q, func_name)
        result = func("Antananarivo", "Toamasina")

        assert isinstance(result, pd.DataFrame)
        for col in expected_cols:
            assert col in result.columns


class TestFunctionsWithCityAndPeriod:
    """Functions that take both city_name and period parameters."""

    @pytest.mark.parametrize("func_name,period,expected_cols", [
        ("city_hourly_profile", "30d", ["hour", "avg_aqi", "avg_pm25"]),
        ("city_all_pollutants", "7d", ["time", "pm2_5", "pm10"]),
    ])
    def test_with_city_and_period(self, func_name, period, expected_cols, mock_query):
        """Functions with city + period should work correctly."""
        import queries as q

        mock_data = {col: [f"dummy"] for col in expected_cols}
        mock_query.return_value = pd.DataFrame(mock_data)

        func = getattr(q, func_name)
        result = func("Antananarivo", period)

        assert isinstance(result, pd.DataFrame)
        for col in expected_cols:
            assert col in result.columns


class TestPeriodToInterval:
    """Verify the period mapping helper."""

    def test_24h_maps_correctly(self):
        from queries import period_to_interval
        assert period_to_interval("24h") == "1 day"

    def test_7d_maps_correctly(self):
        from queries import period_to_interval
        assert period_to_interval("7d") == "7 days"

    def test_30d_maps_correctly(self):
        from queries import period_to_interval
        assert period_to_interval("30d") == "30 days"

    def test_90d_maps_correctly(self):
        from queries import period_to_interval
        assert period_to_interval("90d") == "90 days"

    def test_1y_maps_correctly(self):
        from queries import period_to_interval
        assert period_to_interval("1y") == "1 year"

    def test_unknown_period_defaults_to_7days(self):
        from queries import period_to_interval
        assert period_to_interval("invalid") == "7 days"


class TestHeatmapData:
    """Test heatmap_data which takes no parameters."""

    def test_heatmap_data_returns_expected_columns(self, mock_query):
        """heatmap_data() should return hour, day_of_week, avg_aqi."""
        mock_query.return_value = pd.DataFrame({
            "hour": [0], "day_of_week": ["Monday"], "avg_aqi": [1.2],
        })
        from queries import heatmap_data
        df = heatmap_data()
        assert "hour" in df.columns
        assert "day_of_week" in df.columns
        assert "avg_aqi" in df.columns


class TestAirQualityMap:
    """Specific test for the map query."""

    def test_map_returns_coordinates(self, mock_query):
        """air_quality_map() should include lat, lon, aqi, city_name."""
        mock_query.return_value = pd.DataFrame({
            "latitude": [-18.91],
            "longitude": [47.52],
            "aqi": [1],
            "city_name": ["Antananarivo"],
            "status": ["Good"],
        })
        from queries import air_quality_map
        df = air_quality_map()
        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert "aqi" in df.columns
        assert "city_name" in df.columns


class TestDataGaps:
    """Specific test for data gap detection."""

    def test_data_gaps_returns_status(self, mock_query):
        """data_gaps() should include status column."""
        mock_query.return_value = pd.DataFrame({
            "full_date": ["2025-01-01"],
            "hour": [0],
            "city_name": ["Antananarivo"],
            "status": ["OK"],
        })
        from queries import data_gaps
        df = data_gaps()
        assert "status" in df.columns
        assert df["status"].iloc[0] == "OK"
