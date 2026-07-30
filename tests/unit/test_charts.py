"""Unit tests for the charts module — reusable Plotly helpers."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pandas as pd
import plotly.graph_objects as go
from unittest.mock import patch


class TestAqiColorMap:
    """Verify the AQI color mapping."""

    def test_has_five_levels(self):
        from utils.charts import aqi_color_map
        cmap = aqi_color_map()
        assert len(cmap) == 5
        assert all(k in cmap for k in [1, 2, 3, 4, 5])

    def test_all_values_are_hex_colors(self):
        from utils.charts import aqi_color_map
        cmap = aqi_color_map()
        for color in cmap.values():
            assert color.startswith("#")
            assert len(color) == 7  # #RRGGBB

    def test_level_1_is_green(self):
        from utils.charts import aqi_color_map
        assert aqi_color_map()[1].lower() in ("#00e400", "#00ff00")

    def test_level_5_is_dark_red(self):
        from utils.charts import aqi_color_map
        assert aqi_color_map()[5].lower() == "#7e0023"


class TestAqiLevelLabel:
    """Verify AQI level labels."""

    @pytest.mark.parametrize("level,expected", [
        (1, "Good"),
        (2, "Moderate"),
        (3, "Unhealthy"),
        (4, "Very Unhealthy"),
        (5, "Hazardous"),
    ])
    def test_label_correct(self, level, expected):
        from utils.charts import aqi_level_label
        assert aqi_level_label(level) == expected

    def test_unknown_level(self):
        from utils.charts import aqi_level_label
        assert "6" in aqi_level_label(6)


class TestStylePlotlyChart:
    """Verify chart styling helper."""

    def test_returns_figure(self):
        from utils.charts import style_plotly_chart
        import plotly.express as px
        fig = px.line(x=[1, 2], y=[1, 2])
        result = style_plotly_chart(fig, title="Test")
        assert isinstance(result, go.Figure)

    def test_sets_title(self):
        from utils.charts import style_plotly_chart
        import plotly.express as px
        fig = px.line(x=[1, 2], y=[1, 2])
        result = style_plotly_chart(fig, title="My Title")
        assert "My Title" in result.layout.title.text

    def test_does_not_fail_without_title(self):
        from utils.charts import style_plotly_chart
        import plotly.express as px
        fig = px.line(x=[1, 2], y=[1, 2])
        result = style_plotly_chart(fig)  # No title
        assert isinstance(result, go.Figure)


class TestAddAlertThresholds:
    """Verify alert threshold lines."""

    def test_adds_hline(self):
        from utils.charts import add_alert_thresholds
        import plotly.express as px
        fig = px.line(x=[1, 2], y=[1, 2])
        result = add_alert_thresholds(fig, y_threshold=3)
        assert isinstance(result, go.Figure)


class TestSparklineMetric:
    """Verify the sparkline_metric component (smoke test)."""

    def test_runs_without_error(self, mock_streamlit):
        """sparkline_metric() should not crash with valid inputs."""
        from utils.charts import sparkline_metric
        df = pd.DataFrame({"time": [1, 2], "value": [1, 2]})
        # Should not raise
        sparkline_metric("Test", 1.5, sparkline_df=df)

    def test_runs_without_sparkline(self, mock_streamlit):
        """sparkline_metric() should not crash without sparkline data."""
        from utils.charts import sparkline_metric
        sparkline_metric("Test", 1.5)  # No sparkline_df
