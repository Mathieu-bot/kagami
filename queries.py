"""All SQL queries from the Air Quality Madagascar dashboard.

All queries use parameterized bind variables (:param) to prevent SQL injection.
Aggregates are wrapped in COALESCE so that empty periods return 0 instead
of NULL rows that render as "nan" in the UI.
"""

from config import query


def _cached_30s(func):
    """Apply ``@st.cache_data(ttl=30)`` only inside a running Streamlit
    runtime. Outside (unit tests) the function is returned unchanged so
    tests keep exercising the real code path."""
    try:
        from streamlit import runtime
        if runtime.exists():
            import streamlit as st
            return st.cache_data(ttl=30)(func)
    except Exception:
        pass
    return func


# ─── Helpers ───

def period_to_interval(period: str) -> str:
    """Convert period selector to SQL interval string."""
    mapping = {
        "24h": "1 day",
        "7d": "7 days",
        "30d": "30 days",
        "90d": "90 days",
        "1y": "1 year",
    }
    return mapping.get(period, "7 days")


# ─── Dashboard 1: HQ Overview ───

@_cached_30s
def aqi_today():
    """Panel 1.1 — AQI average for today."""
    return query("""
        SELECT COALESCE(ROUND(AVG(f.aqi)::numeric, 2), 0) AS avg_aqi
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date = CURRENT_DATE
    """)


@_cached_30s
def aqi_yesterday():
    """Panel 1.1 — Yesterday's AQI average for comparison."""
    return query("""
        SELECT COALESCE(ROUND(AVG(f.aqi)::numeric, 2), 0) AS yesterday_avg
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date = CURRENT_DATE - INTERVAL '1 day'
    """)


@_cached_30s
def aqi_today_sparkline():
    """Panel 1.1 — Hourly AQI sparkline for today."""
    return query("""
        SELECT
            (d.full_date::text || 'T' || LPAD(d.hour::text, 2, '0') || ':00:00')::timestamp AS time,
            ROUND(AVG(f.aqi)::numeric, 2) AS avg_aqi
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date = CURRENT_DATE
        GROUP BY d.full_date, d.hour
        ORDER BY time
    """)


@_cached_30s
def cities_in_alert():
    """Panel 1.2 — Number of cities currently in alert (AQI >= 3)."""
    return query("""
        SELECT COUNT(DISTINCT f.city_key) AS alert_count
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date = CURRENT_DATE AND f.aqi >= 3
    """)


@_cached_30s
def worst_pollutant(period: str = "7d"):
    """Panel 1.3 — Pollutant closest to WHO threshold."""
    interval = period_to_interval(period)
    return query("""
        WITH ratios AS (
            SELECT 'PM2.5' AS pollutant,
                   COALESCE(ROUND(AVG(f.pm2_5)::numeric, 2), 0) AS value,
                   15.0 AS who_threshold,
                   COALESCE(ROUND((AVG(f.pm2_5) / 15.0 * 100)::numeric, 1), 0) AS pct
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
            UNION ALL
            SELECT 'PM10',
                   COALESCE(ROUND(AVG(f.pm10)::numeric, 2), 0), 45.0,
                   COALESCE(ROUND((AVG(f.pm10) / 45.0 * 100)::numeric, 1), 0)
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
            UNION ALL
            SELECT 'NO₂',
                   COALESCE(ROUND(AVG(f.no2)::numeric, 2), 0), 25.0,
                   COALESCE(ROUND((AVG(f.no2) / 25.0 * 100)::numeric, 1), 0)
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
            UNION ALL
            SELECT 'O₃',
                   COALESCE(ROUND(AVG(f.o3)::numeric, 2), 0), 100.0,
                   COALESCE(ROUND((AVG(f.o3) / 100.0 * 100)::numeric, 1), 0)
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
            UNION ALL
            SELECT 'SO₂',
                   COALESCE(ROUND(AVG(f.so2)::numeric, 2), 0), 40.0,
                   COALESCE(ROUND((AVG(f.so2) / 40.0 * 100)::numeric, 1), 0)
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
        )
        SELECT * FROM ratios ORDER BY pct DESC LIMIT 1
    """, {"interval": interval})


@_cached_30s
def data_completeness():
    """Panel 1.4 — Data completeness percentage for today.

    Expected readings = 24 hours per day × number of cities
    (one reading per city per hour).
    """
    return query("""
        SELECT ROUND(COUNT(*) * 100.0 / (24 * (SELECT COUNT(*) FROM dim_city)), 1)
               AS completeness
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date = CURRENT_DATE
    """)


@_cached_30s
def days_without_alert():
    """Panel 1.5 — Consecutive days without any AQI >= 3."""
    return query("""
        WITH daily_alerts AS (
            SELECT d.full_date, BOOL_OR(f.aqi >= 3) AS has_alert
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY d.full_date
        ),
        alert_groups AS (
            SELECT full_date, has_alert,
                SUM(CASE WHEN has_alert THEN 1 ELSE 0 END)
                    OVER (ORDER BY full_date DESC ROWS UNBOUNDED PRECEDING) AS alert_group
            FROM daily_alerts
        )
        SELECT COUNT(*) AS days_without_alert
        FROM alert_groups
        WHERE alert_group = 0 AND NOT has_alert
    """)


@_cached_30s
def who_exceedance_rate(period: str = "7d"):
    """Panel 1.6 — % of readings exceeding any WHO threshold."""
    interval = period_to_interval(period)
    return query("""
        SELECT COALESCE(ROUND(
            COUNT(*) FILTER (
                WHERE f.pm2_5 > 15 OR f.pm10 > 45 OR f.no2 > 25
                   OR f.o3 > 100 OR f.so2 > 40
            ) * 100.0 / NULLIF(COUNT(*), 0), 2
        ), 0) AS exceedance_rate
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
    """, {"interval": interval})


@_cached_30s
def aqi_evolution(period: str = "30d"):
    """Panel 1.7 — Daily AQI time series with 7-day moving average."""
    interval = period_to_interval(period)
    return query("""
        WITH daily_aqi AS (
            SELECT d.full_date,
                   COALESCE(ROUND(AVG(f.aqi)::numeric, 2), 0) AS daily_avg
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
            GROUP BY d.full_date
        )
        SELECT full_date, daily_avg,
            ROUND(AVG(daily_avg) OVER (ORDER BY full_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS trend
        FROM daily_aqi
        ORDER BY full_date
    """, {"interval": interval})


@_cached_30s
def air_quality_map():
    """Panel 1.8 — Latest AQI by city with coordinates.

    The ``status`` label is intentionally NOT computed in SQL: it is derived
    client-side from ``aqi`` via ``charts.aqi_level_label`` so the map shows
    the same 5-level AQI scale as the rest of the app, translated into the
    current language. ``dim_date.hour`` is stored in UTC, so the current-hour
    filter compares against UTC (matches ``pipeline_status``/``last_ingestion``).
    """
    return query("""
        SELECT c.latitude, c.longitude, f.aqi, c.city_name
        FROM fact_aqi f
        JOIN dim_city c ON f.city_key = c.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date = CURRENT_DATE
          AND d.hour = EXTRACT(HOUR FROM NOW() AT TIME ZONE 'UTC')
        ORDER BY c.city_name
    """)


@_cached_30s
def aqi_distribution(period: str = "7d"):
    """Panel 1.9 — Distribution of AQI levels."""
    interval = period_to_interval(period)
    return query("""
        SELECT f.aqi, COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
        GROUP BY f.aqi ORDER BY f.aqi
    """, {"interval": interval})


@_cached_30s
def last_ingestion():
    """Panel 1.10 — Timestamp of the latest record (UTC)."""
    return query("""
        SELECT MAX((d.full_date::text || 'T' || LPAD(d.hour::text, 2, '0') || ':00:00')::timestamp AT TIME ZONE 'UTC') AS last_record
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
    """)


@_cached_30s
def pipeline_status():
    """Panel 1.10 — Pipeline health status.

    The stored timestamps are UTC; making that explicit avoids ambiguous
    naive-timestamp comparisons against NOW() (W1 timezone fix).
    """
    return query("""
        WITH latest AS (
            SELECT MAX((d.full_date::text || 'T' || LPAD(d.hour::text, 2, '0') || ':00:00')::timestamp
                       AT TIME ZONE 'UTC') AS last_record
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        )
        SELECT last_record,
            CASE
                WHEN last_record >= NOW() - INTERVAL '2 hours' THEN 'Up to date'
                WHEN last_record >= NOW() - INTERVAL '6 hours' THEN 'Delayed'
                ELSE 'Critical'
            END AS status
        FROM latest
    """)


# ─── Dashboard 2: City Drill-down ───

@_cached_30s
def city_current_aqi(city_name: str):
    """Panel 2.1 — Current AQI for a specific city."""
    return query("""
        SELECT f.aqi
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_city c ON f.city_key = c.city_key
        WHERE c.city_name = :city_name AND d.full_date = CURRENT_DATE
        ORDER BY d.hour DESC LIMIT 1
    """, {"city_name": city_name})


@_cached_30s
def city_weekly_aqi(city_name: str):
    """Panel 2.1 — 7-day AQI sparkline for a city."""
    return query("""
        SELECT
            (d.full_date::text || 'T' || LPAD(d.hour::text, 2, '0') || ':00:00')::timestamp AS time,
            f.aqi
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_city c ON f.city_key = c.city_key
        WHERE c.city_name = :city_name
          AND d.full_date >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY time
    """, {"city_name": city_name})


@_cached_30s
def city_hourly_profile(city_name: str, period: str = "30d"):
    """Panel 2.2 — Average pollutant levels per hour."""
    interval = period_to_interval(period)
    return query("""
        SELECT d.hour,
            COALESCE(ROUND(AVG(f.aqi)::numeric, 2), 0) AS avg_aqi,
            COALESCE(ROUND(AVG(f.pm2_5)::numeric, 2), 0) AS avg_pm25,
            COALESCE(ROUND(AVG(f.pm10)::numeric, 2), 0) AS avg_pm10,
            COALESCE(ROUND(AVG(f.no2)::numeric, 2), 0) AS avg_no2,
            COALESCE(ROUND(AVG(f.o3)::numeric, 2), 0) AS avg_o3
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_city c ON f.city_key = c.city_key
        WHERE c.city_name = :city_name
          AND d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
        GROUP BY d.hour ORDER BY d.hour
    """, {"city_name": city_name, "interval": interval})


@_cached_30s
def city_all_pollutants(city_name: str, period: str = "7d"):
    """Panel 2.3 — Time series for all pollutants."""
    interval = period_to_interval(period)
    return query("""
        SELECT
            (d.full_date::text || 'T' || LPAD(d.hour::text, 2, '0') || ':00:00')::timestamp AS time,
            f.pm2_5, f.pm10, f.no2, f.o3, f.so2, f.co, f.nh3
        FROM fact_aqi f
        JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_city c ON f.city_key = c.city_key
        WHERE c.city_name = :city_name
          AND d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
        ORDER BY time
    """, {"city_name": city_name, "interval": interval})


@_cached_30s
def city_vs_national(city_name: str):
    """Panel 2.4 — City averages vs national averages."""
    return query("""
        WITH city_avg AS (
            SELECT AVG(f.aqi) AS aqi, AVG(f.pm2_5) AS pm25, AVG(f.pm10) AS pm10,
                   AVG(f.no2) AS no2, AVG(f.o3) AS o3
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            JOIN dim_city c ON f.city_key = c.city_key
            WHERE c.city_name = :city_name
              AND d.full_date >= CURRENT_DATE - INTERVAL '30 days'
        ),
        national_avg AS (
            SELECT AVG(f.aqi) AS aqi, AVG(f.pm2_5) AS pm25, AVG(f.pm10) AS pm10,
                   AVG(f.no2) AS no2, AVG(f.o3) AS o3
            FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.full_date >= CURRENT_DATE - INTERVAL '30 days'
        )
        SELECT 'AQI' AS metric,
               COALESCE(ROUND(city.aqi::numeric, 2), 0) AS city_val,
               COALESCE(ROUND(nat.aqi::numeric, 2), 0) AS national_val
        FROM city_avg city, national_avg nat
        UNION ALL SELECT 'PM2.5',
               COALESCE(ROUND(city.pm25::numeric, 2), 0),
               COALESCE(ROUND(nat.pm25::numeric, 2), 0)
        FROM city_avg city, national_avg nat
        UNION ALL SELECT 'PM10',
               COALESCE(ROUND(city.pm10::numeric, 2), 0),
               COALESCE(ROUND(nat.pm10::numeric, 2), 0)
        FROM city_avg city, national_avg nat
        UNION ALL SELECT 'NO₂',
               COALESCE(ROUND(city.no2::numeric, 2), 0),
               COALESCE(ROUND(nat.no2::numeric, 2), 0)
        FROM city_avg city, national_avg nat
        UNION ALL SELECT 'O₃',
               COALESCE(ROUND(city.o3::numeric, 2), 0),
               COALESCE(ROUND(nat.o3::numeric, 2), 0)
        FROM city_avg city, national_avg nat
    """, {"city_name": city_name})


@_cached_30s
def city_worst_episodes(city_name: str, period: str = "30d"):
    """Panel 2.5 — Top 20 worst episodes for a city."""
    interval = period_to_interval(period)
    return query("""
        SELECT d.full_date, d.hour, f.aqi, f.pm2_5, f.pm10, f.no2, f.o3, f.so2,
            CASE
                WHEN f.aqi >= 3 THEN 'Alert'
                WHEN f.pm2_5 > 15 THEN 'WHO PM2.5'
                WHEN f.pm10 > 45 THEN 'WHO PM10'
                WHEN f.no2 > 25 THEN 'WHO NO₂'
                WHEN f.o3 > 100 THEN 'WHO O₃'
                WHEN f.so2 > 40 THEN 'WHO SO₂'
                ELSE 'Normal'
            END AS status
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_city c ON f.city_key = c.city_key
        WHERE c.city_name = :city_name
          AND d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
          AND (f.aqi >= 3 OR f.pm2_5 > 15 OR f.pm10 > 45 OR f.no2 > 25 OR f.o3 > 100 OR f.so2 > 40)
        ORDER BY d.full_date DESC, d.hour DESC LIMIT 20
    """, {"city_name": city_name, "interval": interval})


# ─── Dashboard 3: Deep Analysis ───

@_cached_30s
def correlation_matrix(period: str = "30d"):
    """Panel 3.1 — Pollutant correlation matrix."""
    interval = period_to_interval(period)
    return query("""
        SELECT
            COALESCE(ROUND(CORR(f.pm2_5, f.pm10)::numeric, 3), 0) AS "PM2.5_x_PM10",
            COALESCE(ROUND(CORR(f.pm2_5, f.no2)::numeric, 3), 0)  AS "PM2.5_x_NO2",
            COALESCE(ROUND(CORR(f.pm2_5, f.o3)::numeric, 3), 0)   AS "PM2.5_x_O3",
            COALESCE(ROUND(CORR(f.pm2_5, f.so2)::numeric, 3), 0)  AS "PM2.5_x_SO2",
            COALESCE(ROUND(CORR(f.pm2_5, f.co)::numeric, 3), 0)   AS "PM2.5_x_CO",
            COALESCE(ROUND(CORR(f.pm2_5, f.nh3)::numeric, 3), 0)  AS "PM2.5_x_NH3",
            COALESCE(ROUND(CORR(f.pm10, f.no2)::numeric, 3), 0)   AS "PM10_x_NO2",
            COALESCE(ROUND(CORR(f.pm10, f.o3)::numeric, 3), 0)    AS "PM10_x_O3",
            COALESCE(ROUND(CORR(f.pm10, f.so2)::numeric, 3), 0)   AS "PM10_x_SO2",
            COALESCE(ROUND(CORR(f.pm10, f.co)::numeric, 3), 0)    AS "PM10_x_CO",
            COALESCE(ROUND(CORR(f.pm10, f.nh3)::numeric, 3), 0)   AS "PM10_x_NH3",
            COALESCE(ROUND(CORR(f.no2, f.o3)::numeric, 3), 0)     AS "NO2_x_O3",
            COALESCE(ROUND(CORR(f.no2, f.so2)::numeric, 3), 0)    AS "NO2_x_SO2",
            COALESCE(ROUND(CORR(f.no2, f.co)::numeric, 3), 0)     AS "NO2_x_CO",
            COALESCE(ROUND(CORR(f.no2, f.nh3)::numeric, 3), 0)    AS "NO2_x_NH3",
            COALESCE(ROUND(CORR(f.o3, f.so2)::numeric, 3), 0)     AS "O3_x_SO2",
            COALESCE(ROUND(CORR(f.o3, f.co)::numeric, 3), 0)      AS "O3_x_CO",
            COALESCE(ROUND(CORR(f.o3, f.nh3)::numeric, 3), 0)     AS "O3_x_NH3",
            COALESCE(ROUND(CORR(f.so2, f.co)::numeric, 3), 0)     AS "SO2_x_CO",
            COALESCE(ROUND(CORR(f.so2, f.nh3)::numeric, 3), 0)    AS "SO2_x_NH3",
            COALESCE(ROUND(CORR(f.co, f.nh3)::numeric, 3), 0)     AS "CO_x_NH3",
            COALESCE(ROUND(CORR(f.aqi, f.pm2_5)::numeric, 3), 0)  AS "AQI_x_PM25",
            COALESCE(ROUND(CORR(f.aqi, f.pm10)::numeric, 3), 0)   AS "AQI_x_PM10",
            COALESCE(ROUND(CORR(f.aqi, f.o3)::numeric, 3), 0)     AS "AQI_x_O3"
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
    """, {"interval": interval})


@_cached_30s
def monthly_statistics():
    """Panel 3.2 — Monthly statistical distribution."""
    return query("""
        SELECT
            d.year::text || '-' || LPAD(d.month::text, 2, '0') AS month,
            COUNT(*) AS count,
            ROUND(MIN(f.aqi)::numeric, 2) AS min,
            ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY f.aqi)::numeric, 2) AS p25,
            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY f.aqi)::numeric, 2) AS median,
            ROUND(AVG(f.aqi)::numeric, 2) AS avg,
            ROUND(STDDEV(f.aqi)::numeric, 2) AS std,
            ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY f.aqi)::numeric, 2) AS p75,
            ROUND(MAX(f.aqi)::numeric, 2) AS max
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY d.year, d.month ORDER BY d.year, d.month
    """)


@_cached_30s
def seasonal_analysis():
    """Panel 3.3 — Dry vs wet season comparison."""
    return query("""
        SELECT
            CASE WHEN d.month BETWEEN 5 AND 10 THEN 'Dry Season (May-Oct)'
                 ELSE 'Wet Season (Nov-Apr)'
            END AS season,
            ROUND(AVG(f.aqi)::numeric, 2) AS avg_aqi,
            ROUND(AVG(f.pm2_5)::numeric, 2) AS avg_pm25,
            ROUND(AVG(f.pm10)::numeric, 2) AS avg_pm10,
            ROUND(AVG(f.no2)::numeric, 2) AS avg_no2,
            ROUND(AVG(f.o3)::numeric, 2) AS avg_o3,
            COUNT(*) AS measurements
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY season ORDER BY season
    """)


@_cached_30s
def weekday_weekend():
    """Panel 3.4 — Weekday vs weekend comparison."""
    return query("""
        SELECT
            CASE WHEN d.is_weekend THEN 'Weekend' ELSE 'Weekday' END AS day_type,
            ROUND(AVG(f.aqi)::numeric, 2) AS avg_aqi,
            ROUND(AVG(f.pm2_5)::numeric, 2) AS avg_pm25,
            ROUND(AVG(f.pm10)::numeric, 2) AS avg_pm10,
            ROUND(AVG(f.no2)::numeric, 2) AS avg_no2,
            ROUND(AVG(f.o3)::numeric, 2) AS avg_o3,
            COUNT(*) AS measurements
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY d.is_weekend ORDER BY d.is_weekend
    """)


@_cached_30s
def boxplot_data():
    """Panel 3.5 — Raw AQI values by month for boxplot."""
    return query("""
        SELECT d.year::text || '-' || LPAD(d.month::text, 2, '0') AS month, f.aqi
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.year >= 2025
        ORDER BY month
    """)


@_cached_30s
def scatter_data(period: str = "30d"):
    """Panel 3.6 — PM2.5 vs AQI scatter data."""
    interval = period_to_interval(period)
    return query("""
        SELECT f.pm2_5, f.aqi, c.city_name
        FROM fact_aqi f JOIN dim_city c ON f.city_key = c.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
    """, {"interval": interval})


@_cached_30s
def heatmap_data():
    """Panel 3.7 — AQI by hour and day of week for heatmap."""
    return query("""
        SELECT d.hour, d.day_of_week, ROUND(AVG(f.aqi)::numeric, 2) AS avg_aqi
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY d.hour, d.day_of_week,
            CASE d.day_of_week
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END
        ORDER BY d.hour,
            CASE d.day_of_week
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END
    """)


@_cached_30s
def records_per_day():
    """Panel 4.2 — Records per day for the last 7 days."""
    return query("""
        SELECT d.full_date, COUNT(*) AS records
        FROM fact_aqi f JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY d.full_date ORDER BY d.full_date
    """)


@_cached_30s
def data_gaps():
    """Panel 4.3 — Missing data detection for last 24h."""
    return query("""
        SELECT d.full_date, d.hour, c.city_name,
               CASE WHEN f.aqi IS NULL THEN 'Missing' ELSE 'OK' END AS status
        FROM dim_date d
        CROSS JOIN dim_city c
        LEFT JOIN fact_aqi f ON d.date_key = f.date_key AND c.city_key = f.city_key
        WHERE d.full_date >= CURRENT_DATE - INTERVAL '24 hours'
        ORDER BY d.full_date, d.hour, c.city_name
    """)


@_cached_30s
def list_cities():
    """Get list of all cities."""
    return query("SELECT city_name FROM dim_city ORDER BY city_name")


@_cached_30s
def get_all_cities():
    """Get all cities with coordinates."""
    return query("SELECT * FROM dim_city ORDER BY city_name")


# ─── Dashboard 5: City Comparison ───

@_cached_30s
def comparison_current():
    """Current AQI per city for the inter-city comparison panel."""
    return query("""
        SELECT c.city_name,
               COALESCE(ROUND(AVG(f.aqi)::numeric, 2), 0) AS current_aqi
        FROM fact_aqi f
        JOIN dim_city c ON c.city_key = f.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date = CURRENT_DATE
        GROUP BY c.city_name
        ORDER BY current_aqi DESC
    """)


@_cached_30s
def comparison_trend_7d():
    """Daily average AQI per city over the last 7 days."""
    return query("""
        SELECT c.city_name, d.full_date,
               COALESCE(ROUND(AVG(f.aqi)::numeric, 2), 0) AS avg_aqi
        FROM fact_aqi f
        JOIN dim_city c ON c.city_key = f.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.full_date >= CURRENT_DATE - INTERVAL '6 days'
        GROUP BY c.city_name, d.full_date
        ORDER BY d.full_date, c.city_name
    """)


@_cached_30s
def comparison_pollutants(city_a: str, city_b: str):
    """Average pollutant levels for two cities over the last 7 days (A/B mode)."""
    return query("""
        SELECT c.city_name,
               COALESCE(ROUND(AVG(f.pm2_5)::numeric, 2), 0) AS pm2_5,
               COALESCE(ROUND(AVG(f.pm10)::numeric, 2), 0) AS pm10,
               COALESCE(ROUND(AVG(f.no2)::numeric, 2), 0) AS no2,
               COALESCE(ROUND(AVG(f.o3)::numeric, 2), 0) AS o3
        FROM fact_aqi f
        JOIN dim_city c ON f.city_key = c.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE c.city_name IN (:city_a, :city_b)
          AND d.full_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY c.city_name
        ORDER BY c.city_name
    """, {"city_a": city_a, "city_b": city_b})


# ─── WHO thresholds (City Drill-down) ───

@_cached_30s
def city_pollutant_timeseries(city_name: str, period: str = "30d"):
    """Daily average pollutant concentrations for a city (WHO overlay)."""
    interval = period_to_interval(period)
    return query("""
        SELECT d.full_date,
               COALESCE(ROUND(AVG(f.pm2_5)::numeric, 2), 0) AS pm2_5,
               COALESCE(ROUND(AVG(f.pm10)::numeric, 2), 0) AS pm10,
               COALESCE(ROUND(AVG(f.no2)::numeric, 2), 0) AS no2,
               COALESCE(ROUND(AVG(f.o3)::numeric, 2), 0) AS o3,
               COALESCE(ROUND(AVG(f.so2)::numeric, 2), 0) AS so2,
               COALESCE(ROUND(AVG(f.co)::numeric, 2), 0) AS co,
               COALESCE(ROUND(AVG(f.nh3)::numeric, 2), 0) AS nh3
        FROM fact_aqi f
        JOIN dim_city c ON c.city_key = f.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE c.city_name = :city_name
          AND d.full_date >= CURRENT_DATE - CAST(:interval AS INTERVAL)
        GROUP BY d.full_date
        ORDER BY d.full_date
    """, {"city_name": city_name, "interval": interval})


# ─── Dashboard: Alerts History ───

@_cached_30s
def control_room_status():
    """Live status per city for the control room: latest AQI + reading time.

    Returns one row per city with the most recent reading (AQI value and
    the timestamp of that reading). The timestamp is returned as UTC
    (tz-aware) so the freshness logic never compares naive datetimes.
    Result is cached for 30s (matches the fragment auto-refresh).
    """
    return query("""
        WITH ranked AS (
            SELECT c.city_name, f.aqi,
                   ((d.full_date::text || 'T' || LPAD(d.hour::text, 2, '0') || ':00:00')::timestamp
                        AT TIME ZONE 'UTC') AS last_record,
                   ROW_NUMBER() OVER (PARTITION BY c.city_name
                                      ORDER BY d.full_date DESC, d.hour DESC) AS rn
            FROM fact_aqi f
            JOIN dim_city c ON f.city_key = c.city_key
            JOIN dim_date d ON f.date_key = d.date_key
        )
        SELECT city_name, aqi, last_record
        FROM ranked
        WHERE rn = 1
        ORDER BY city_name
    """)


@_cached_30s
def citizen_who_exceedance():
    """Share of *days* exceeding WHO guidelines per city (last 7 days).

    A day counts as exceeding when at least one hourly reading of PM2.5,
    PM10, NO₂ or O₃ is above its WHO 24h guideline (W6 fix: percentage
    of days, not percentage of readings).
    """
    return query("""
        WITH daily AS (
            SELECT c.city_name, d.full_date,
                   BOOL_OR(f.pm2_5 > 15 OR f.pm10 > 45 OR f.no2 > 25 OR f.o3 > 100) AS exceeded
            FROM fact_aqi f
            JOIN dim_city c ON c.city_key = f.city_key
            JOIN dim_date d ON f.date_key = d.date_key
            WHERE d.full_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY c.city_name, d.full_date
        )
        SELECT city_name,
               ROUND(COUNT(*) FILTER (WHERE exceeded) * 100.0 / NULLIF(COUNT(*), 0), 1)
                   AS exceedance_rate
        FROM daily
        GROUP BY city_name
        ORDER BY city_name
    """)


@_cached_30s
def alert_episodes(days: int = 90):
    """Recent alert episodes (AQI >= 3) across cities."""
    return query("""
        SELECT c.city_name, d.full_date, d.hour, f.aqi,
               CASE WHEN f.aqi >= 4 THEN 'Severe'
                    WHEN f.aqi >= 3 THEN 'Alert'
                    ELSE 'Moderate' END AS level
        FROM fact_aqi f
        JOIN dim_city c ON c.city_key = f.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE f.aqi >= 3 AND d.full_date >= CURRENT_DATE - (:days || ' days')::interval
        ORDER BY d.full_date DESC, d.hour DESC, c.city_name
    """, {"days": days})


@_cached_30s
def alert_summary(days: int = 90):
    """Alerts per city: count, worst AQI, and number of affected days."""
    return query("""
        SELECT c.city_name,
               COUNT(*) AS alert_count,
               MAX(f.aqi) AS max_aqi,
               COUNT(DISTINCT d.full_date) AS affected_days
        FROM fact_aqi f
        JOIN dim_city c ON c.city_key = f.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE f.aqi >= 3 AND d.full_date >= CURRENT_DATE - (:days || ' days')::interval
        GROUP BY c.city_name
        ORDER BY alert_count DESC
    """, {"days": days})


# ─── Dashboard: AQI Forecast ───

@_cached_30s
def city_daily_aqi(city_name: str, days: int = 60):
    """Daily average AQI history used to train the forecast model."""
    return query("""
        SELECT d.full_date, ROUND(AVG(f.aqi)::numeric, 2) AS daily_avg
        FROM fact_aqi f
        JOIN dim_city c ON c.city_key = f.city_key
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE c.city_name = :city_name
          AND d.full_date >= CURRENT_DATE - (:days || ' days')::interval
        GROUP BY d.full_date
        ORDER BY d.full_date
    """, {"city_name": city_name, "days": days})
