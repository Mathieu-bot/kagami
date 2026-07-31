"""Unit tests for utils/sql_guard.py — Data Explorer read-only hardening."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from utils.sql_guard import is_read_only_sql, enforce_limit


class TestIsReadOnlySql:
    """Verify single read-only statement detection."""

    def test_plain_select(self):
        assert is_read_only_sql("SELECT * FROM dim_city")

    def test_select_with_leading_whitespace_and_newline(self):
        assert is_read_only_sql("  \n SELECT city_name FROM dim_city")

    def test_with_cte(self):
        assert is_read_only_sql("WITH x AS (SELECT 1) SELECT * FROM x")

    def test_explain(self):
        assert is_read_only_sql("EXPLAIN SELECT * FROM fact_aqi")

    def test_empty_string_rejected(self):
        assert not is_read_only_sql("")
        assert not is_read_only_sql("   ")

    def test_insert_rejected(self):
        assert not is_read_only_sql("INSERT INTO x VALUES (1)")

    def test_delete_rejected(self):
        assert not is_read_only_sql("DELETE FROM fact_aqi")

    def test_update_rejected(self):
        assert not is_read_only_sql("UPDATE fact_aqi SET aqi = 1")

    def test_drop_rejected(self):
        assert not is_read_only_sql("DROP TABLE fact_aqi")

    def test_multi_statement_smuggling_rejected(self):
        # The historical C2 bypass: SELECT starts valid, then a second
        # statement is appended after a semicolon.
        assert not is_read_only_sql("SELECT 1; DROP TABLE fact_aqi")
        assert not is_read_only_sql("SELECT 1; DELETE FROM fact_aqi")
        assert not is_read_only_sql("SELECT 1; TRUNCATE fact_aqi")

    def test_leading_comment_rejected(self):
        assert not is_read_only_sql("-- comment\nSELECT 1")


class TestEnforceLimit:
    """Verify LIMIT capping."""

    def test_appends_limit(self):
        assert enforce_limit("SELECT * FROM dim_city") == "SELECT * FROM dim_city LIMIT 1000"

    def test_respects_custom_max(self):
        assert enforce_limit("SELECT * FROM dim_city", max_rows=100) == \
            "SELECT * FROM dim_city LIMIT 100"

    def test_keeps_existing_limit(self):
        sql = "SELECT * FROM fact_aqi LIMIT 50"
        assert enforce_limit(sql) == sql

    def test_keeps_existing_limit_with_offset(self):
        sql = "SELECT * FROM fact_aqi LIMIT 50 OFFSET 10"
        assert enforce_limit(sql) == sql

    def test_explain_unchanged(self):
        sql = "EXPLAIN SELECT * FROM fact_aqi"
        assert enforce_limit(sql) == sql

    def test_case_insensitive_limit_detection(self):
        sql = "SELECT * FROM fact_aqi limit 25"
        assert enforce_limit(sql) == sql
