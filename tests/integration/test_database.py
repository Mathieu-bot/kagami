"""Integration tests — real connection to NeonDB (requires secrets)."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pandas as pd


@pytest.mark.integration
class TestNeonDBConnection:
    """Verify we can connect to the real NeonDB.
    
    These tests require:
      - A valid .streamlit/secrets.toml with neon_url
      - Network access to NeonDB
    
    They are skipped automatically when no connection is available.
    """

    @pytest.fixture(autouse=True)
    def check_connection(self):
        """Skip if we can't connect to NeonDB."""
        try:
            from config import get_engine
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(
                    "SELECT 1"
                )
        except Exception:
            pytest.skip("NeonDB not available — skipping integration tests")

    def test_connection_succeeds(self):
        """Should connect and run a simple query."""
        from config import query
        df = query("SELECT 1 AS test")
        assert df["test"].iloc[0] == 1

    def test_dim_city_exists(self):
        """dim_city table should exist with the right columns."""
        from config import query
        df = query("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'dim_city' ORDER BY ordinal_position")
        columns = df["column_name"].tolist()
        assert "city_key" in columns
        assert "city_name" in columns
        assert "latitude" in columns
        assert "longitude" in columns

    def test_dim_date_exists(self):
        """dim_date table should exist with the right columns."""
        from config import query
        df = query("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'dim_date' ORDER BY ordinal_position")
        columns = df["column_name"].tolist()
        assert "date_key" in columns
        assert "full_date" in columns
        assert "hour" in columns
        assert "day_of_week" in columns
        assert "month" in columns
        assert "year" in columns

    def test_fact_aqi_exists(self):
        """fact_aqi table should exist with the right columns."""
        from config import query
        df = query("SELECT column_name FROM information_schema.columns "
                   "WHERE table_name = 'fact_aqi' ORDER BY ordinal_position")
        columns = df["column_name"].tolist()
        assert "city_key" in columns
        assert "date_key" in columns
        assert "aqi" in columns
        for col in ["pm2_5", "pm10", "no2", "o3", "so2", "co", "nh3"]:
            assert col in columns, f"Column {col} not found in fact_aqi"

    def test_fact_aqi_has_data(self):
        """fact_aqi should contain at least one row."""
        from config import query
        df = query("SELECT COUNT(*) AS cnt FROM fact_aqi")
        assert df["cnt"].iloc[0] > 0, "fact_aqi is empty!"

    def test_all_six_cities_present(self):
        """There should be exactly 6 cities in Madagascar."""
        from config import query
        df = query("SELECT city_name FROM dim_city ORDER BY city_name")
        cities = df["city_name"].tolist()
        assert len(cities) == 6, f"Expected 6 cities, got {len(cities)}"
        assert "Antananarivo" in cities
        assert "Toamasina" in cities
        assert "Mahajanga" in cities
        assert "Fianarantsoa" in cities
        assert "Toliara" in cities
        assert "Antsiranana" in cities

    def test_referential_integrity(self):
        """All city_key and date_key in fact_aqi should reference existing rows."""
        from config import query
        df = query("""
            SELECT COUNT(*) AS orphans FROM fact_aqi f
            LEFT JOIN dim_city c ON f.city_key = c.city_key
            LEFT JOIN dim_date d ON f.date_key = d.date_key
            WHERE c.city_key IS NULL OR d.date_key IS NULL
        """)
        assert df["orphans"].iloc[0] == 0, "Orphan records found in fact_aqi!"
