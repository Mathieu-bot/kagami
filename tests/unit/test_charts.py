"""Unit tests for the charts module — reusable Plotly helpers."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from unittest.mock import patch


class TestAqiLevelLabel:
    """Verify AQI level labels (language-aware)."""

    @pytest.mark.parametrize("level,expected", [
        (1, "Good"),
        (2, "Moderate"),
        (3, "Unhealthy"),
        (4, "Very Unhealthy"),
        (5, "Hazardous"),
    ])
    def test_label_english(self, level, expected):
        from utils.charts import aqi_level_label
        assert aqi_level_label(level, lang="en") == expected

    @pytest.mark.parametrize("level,expected", [
        (1, "Bon"),
        (2, "Modéré"),
        (3, "Mauvais pour la santé"),
        (5, "Dangereux"),
    ])
    def test_label_french(self, level, expected):
        from utils.charts import aqi_level_label
        assert aqi_level_label(level, lang="fr") == expected

    def test_default_language_is_french(self):
        from utils.charts import aqi_level_label
        assert aqi_level_label(1) == "Bon"

    def test_unknown_level(self):
        from utils.charts import aqi_level_label
        assert "6" in aqi_level_label(6, lang="en")
        assert "6" in aqi_level_label(6, lang="fr")


class TestStylePlotlyChart:
    """Verify chart styling helper."""

    def test_returns_figure(self):
        from utils.charts import style_plotly_chart
        fig = px.line(x=[1, 2], y=[1, 2])
        result = style_plotly_chart(fig, title="Test")
        assert isinstance(result, go.Figure)

    def test_sets_title(self):
        from utils.charts import style_plotly_chart
        fig = px.line(x=[1, 2], y=[1, 2])
        result = style_plotly_chart(fig, title="My Title")
        assert "My Title" in result.layout.title.text

    def test_no_title_removes_title_object(self):
        """Without a title the title object must be absent from the spec.

        Some Streamlit/plotly.js versions render an empty layout.title as
        the literal text "undefined", so we must not leave an empty object.
        """
        import json
        from utils.charts import style_plotly_chart
        fig = px.line(x=[1, 2], y=[1, 2])
        result = style_plotly_chart(fig)  # No title
        spec = json.loads(json.dumps(result.to_plotly_json()))
        assert "title" not in spec["layout"], "empty layout.title must be removed"

    def test_does_not_fail_without_title(self):
        from utils.charts import style_plotly_chart
        fig = px.line(x=[1, 2], y=[1, 2])
        result = style_plotly_chart(fig)  # No title
        assert isinstance(result, go.Figure)


class TestRenameTraces:
    """Verify trace renaming for translated legends."""

    def test_renames_known_traces(self):
        from utils.charts import rename_traces
        df = pd.DataFrame({"d": [1, 2], "daily_avg": [1.0, 2.0], "trend": [1.1, 2.1]})
        fig = px.line(df, x="d", y=["daily_avg", "trend"])
        names = [t.name for t in fig.data]
        assert "daily_avg" in names and "trend" in names  # raw px behavior
        rename_traces(fig, {"daily_avg": "Moyenne", "trend": "Tendance"})
        assert [t.name for t in fig.data] == ["Moyenne", "Tendance"]

    def test_leaves_unknown_traces_untouched(self):
        from utils.charts import rename_traces
        df = pd.DataFrame({"x": [1, 2], "other_a": [1, 2], "other_b": [2, 3]})
        fig = px.line(df, x="x", y=["other_a", "other_b"])
        rename_traces(fig, {"daily_avg": "Moyenne"})
        assert {t.name for t in fig.data} == {"other_a", "other_b"}


class TestSetHoverTemplate:
    """Verify the compact hover template helper."""

    def test_sets_hovertemplate_on_all_traces(self):
        from utils.charts import set_hover_template
        df = pd.DataFrame({"x": [1, 2], "a": [1.1, 2.2], "b": [3.3, 4.4]})
        fig = px.line(df, x="x", y=["a", "b"])
        set_hover_template(fig, fmt=".2f")
        for trace in fig.data:
            assert trace.hovertemplate is not None
            assert "%{y:.2f}" in trace.hovertemplate


class TestDropnaForChart:
    """Verify NaN rows are dropped before charting."""

    def test_drops_nan_rows(self):
        from utils.charts import dropna_for_chart
        df = pd.DataFrame({"x": [1, 2, 3], "y": [1.0, None, 3.0]})
        out = dropna_for_chart(df, cols=["y"])
        assert len(out) == 2

    def test_empty_df_is_safe(self):
        from utils.charts import dropna_for_chart
        empty = pd.DataFrame({"x": [], "y": []})
        out = dropna_for_chart(empty, cols=["y"])
        assert out is empty


class TestFmtNum:
    """Verify safe number formatting."""

    def test_formats_float(self):
        from utils.charts import fmt_num
        assert fmt_num(2.5) == "2.5"

    def test_nan_returns_dash(self):
        from utils.charts import fmt_num
        assert fmt_num(float("nan")) == "–"

    def test_none_returns_dash(self):
        from utils.charts import fmt_num
        assert fmt_num(None) == "–"

    def test_non_numeric_returns_dash(self):
        from utils.charts import fmt_num
        assert fmt_num("oops") == "–"


class TestAqiBadgeColor:
    """Verify badge color thresholds."""

    def test_green_below_alert(self):
        from utils.charts import aqi_badge_color
        assert aqi_badge_color(2) == "green"

    def test_orange_at_alert(self):
        from utils.charts import aqi_badge_color
        assert aqi_badge_color(3) == "orange"

    def test_red_above_alert(self):
        from utils.charts import aqi_badge_color
        assert aqi_badge_color(5) == "red"


class TestPipelineStatusLabel:
    """Verify the pipeline status -> (emoji, label) helper."""

    def test_known_status(self, mock_streamlit):
        from utils.charts import pipeline_status_label
        emoji, label = pipeline_status_label("Up to date")
        assert emoji == "🟢"
        assert label == "À jour"

    def test_unknown_status_falls_back(self, mock_streamlit):
        from utils.charts import pipeline_status_label
        emoji, label = pipeline_status_label("??")
        assert emoji == "❓"
        assert label == "??"
