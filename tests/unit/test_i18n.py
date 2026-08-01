"""Unit tests for the i18n module — FR/EN translation tables and helpers."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import pytest

from i18n import (
    DEFAULT_LANG,
    LANGUAGES,
    STRINGS,
    COLUMN_LABELS,
    EXPORT_LABELS,
    t,
    col,
    export_label,
    init_lang,
    lang_selector,
    current_lang,
    translate_df,
    period_label,
)


class TestTables:
    """Verify the translation tables are complete and symmetric."""

    def test_french_is_default(self):
        assert DEFAULT_LANG == "fr"
        assert "fr" in LANGUAGES and "en" in LANGUAGES

    def test_fr_en_key_parity(self):
        """Every French key must exist in English and vice versa."""
        fr_keys = set(STRINGS["fr"])
        en_keys = set(STRINGS["en"])
        assert fr_keys == en_keys, (
            f"FR/EN key mismatch. Only-FR: {fr_keys - en_keys} "
            f"Only-EN: {en_keys - fr_keys}"
        )

    def test_no_empty_translations(self):
        for lang, table in STRINGS.items():
            for key, value in table.items():
                assert value and len(value) > 0, f"Empty {lang} translation for {key}"

    def test_nav_keys_cover_all_pages(self):
        """Sidebar navigation needs a nav.* label for every page id."""
        from auth import PAGE_ACCESS
        for pid in PAGE_ACCESS:
            assert f"nav.{pid}" in STRINGS["fr"], f"Missing nav.{pid}"
            assert f"nav.{pid}" in STRINGS["en"], f"Missing nav.{pid}"

    def test_column_labels_key_parity(self):
        fr_keys = set(COLUMN_LABELS["fr"])
        en_keys = set(COLUMN_LABELS["en"])
        assert fr_keys == en_keys

    def test_export_labels_key_parity(self):
        fr_keys = set(EXPORT_LABELS["fr"])
        en_keys = set(EXPORT_LABELS["en"])
        assert fr_keys == en_keys


class TestT:
    """Verify the t() translation function."""

    def test_returns_french_by_default(self, mock_streamlit):
        assert t("common.no_data") == "Aucune donnée disponible"

    def test_returns_english_when_session_set(self, mock_streamlit):
        st.session_state["lang"] = "en"
        assert t("common.no_data") == "No data available"

    def test_unknown_key_falls_back_to_key(self, mock_streamlit):
        assert t("no.such.key") == "no.such.key"

    def test_kwargs_are_formatted(self, mock_streamlit):
        st.session_state["lang"] = "fr"
        assert t("alerts.last_days", d=90) == "Derniers 90 jours"

    def test_explicit_lang_overrides_session(self, mock_streamlit):
        st.session_state["lang"] = "fr"
        assert t("common.no_data", lang="en") == "No data available"

    def test_missing_placeholder_is_harmless(self, mock_streamlit):
        # No kwargs supplied for a key with a placeholder: key returned as-is
        assert t("alerts.last_days") == "Derniers {d} jours"


class TestColAndExport:
    """Verify the col() and export_label() helpers."""

    def test_col_returns_translated_header(self, mock_streamlit):
        st.session_state["lang"] = "fr"
        assert col("city_name") == "Ville"
        st.session_state["lang"] = "en"
        assert col("city_name") == "City"

    def test_col_unknown_key_passthrough(self, mock_streamlit):
        assert col("unknown_col") == "unknown_col"

    def test_export_label_french(self, mock_streamlit):
        st.session_state["lang"] = "fr"
        assert export_label("aqi_evolution") == "Évolution de l'AQI"

    def test_export_label_english(self, mock_streamlit):
        st.session_state["lang"] = "en"
        assert export_label("aqi_evolution") == "AQI Evolution"


class TestLangLifecycle:
    """Verify language seeding, selection and DataFrame translation."""

    def test_init_lang_seeds_french(self, mock_streamlit):
        st.session_state.clear()
        init_lang()
        assert st.session_state["lang"] == "fr"
        assert current_lang() == "fr"

    def test_init_lang_keeps_existing_choice(self, mock_streamlit):
        st.session_state.clear()
        st.session_state["lang"] = "en"
        init_lang()
        assert st.session_state["lang"] == "en"

    def test_lang_selector_renders(self, mock_streamlit):
        st.session_state["lang"] = "fr"
        lang_selector()
        st.selectbox.assert_called_once()

    def test_translate_df_renames_known_columns(self, mock_streamlit):
        df = pd.DataFrame({"city_name": ["Antananarivo"], "unknown_x": [1]})
        st.session_state["lang"] = "fr"
        out = translate_df(df)
        assert list(out.columns) == ["Ville", "unknown_x"]

    def test_translate_df_english(self, mock_streamlit):
        df = pd.DataFrame({"city_name": ["Antananarivo"]})
        st.session_state["lang"] = "en"
        out = translate_df(df)
        assert list(out.columns) == ["City"]


class TestPeriodLabel:
    """Verify period selector labels are translated and captions format."""

    PERIODS = ["24h", "7d", "30d", "90d", "1y"]

    def test_french_labels(self, mock_streamlit):
        st.session_state["lang"] = "fr"
        assert period_label("24h") == "24 heures"
        assert period_label("7d") == "7 jours"
        assert period_label("30d") == "30 jours"
        assert period_label("90d") == "3 mois"
        assert period_label("1y") == "1 an"

    def test_english_labels(self, mock_streamlit):
        st.session_state["lang"] = "en"
        assert period_label("24h") == "24 hours"
        assert period_label("7d") == "7 days"
        assert period_label("30d") == "30 days"
        assert period_label("90d") == "3 months"
        assert period_label("1y") == "1 year"

    def test_unknown_period_passthrough(self, mock_streamlit):
        assert period_label("custom") == "custom"

    def test_period_captions_format_for_all_periods(self, mock_streamlit):
        """Every {period}-driven caption must render cleanly for each period."""
        keys = [
            "hq.aqi_evolution_caption", "hq.aqi_distribution_caption",
            "hq.worst_pollutant_caption", "hq.who_exceedance_caption",
            "drill.hourly_profile_caption", "drill.all_pollutants_caption",
            "drill.who_thresholds_city_caption", "drill.worst_episodes_caption",
            "drill.avg_by_hour",
        ]
        for lang in ("fr", "en"):
            st.session_state["lang"] = lang
            for key in keys:
                for p in self.PERIODS:
                    rendered = t(key, period=period_label(p))
                    assert "{period}" not in rendered, f"{key} ({lang}) not formatted for {p}"
                    assert period_label(p) in rendered, f"{key} ({lang}) missing label for {p}"


class TestAllLiteralKeysDefined:
    """W10: every `t("...")` / `col("...")` / `export_label("...")` literal
    used in the application code must exist in the FR and EN tables.

    This is a static (AST) check so a typo in a translation key is caught
    at test time instead of silently falling back to the raw key at runtime.
    """

    @staticmethod
    def _used_keys(path):
        """Return {function_name: {literal_key, ...}} for t()/col() calls."""
        import ast
        from collections import defaultdict
        keys = defaultdict(set)
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else None
            if name not in ("t", "col"):
                continue
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    keys[name].add(arg.value)
        return keys

    def test_all_literal_keys_exist_in_both_languages(self, mock_streamlit):
        import os
        import glob
        from i18n import STRINGS, COLUMN_LABELS

        root = os.path.join(os.path.dirname(__file__), "..", "..")
        files = [os.path.join(root, "app.py")] + \
            glob.glob(os.path.join(root, "pages", "*.py")) + \
            glob.glob(os.path.join(root, "utils", "*.py")) + \
            [os.path.join(root, "sidebar.py"), os.path.join(root, "auth.py")]
        t_keys = set()
        col_keys = set()
        for path in files:
            used = self._used_keys(path)
            t_keys |= used["t"]
            col_keys |= used["col"]
        # t("...") resolves through STRINGS, col("...") through COLUMN_LABELS.
        missing_fr = sorted(k for k in t_keys if k not in STRINGS["fr"])
        missing_en = sorted(k for k in t_keys if k not in STRINGS["en"])
        assert not missing_fr, f"t() keys missing in FR: {missing_fr}"
        assert not missing_en, f"t() keys missing in EN: {missing_en}"
        col_missing_fr = sorted(k for k in col_keys if k not in COLUMN_LABELS["fr"])
        col_missing_en = sorted(k for k in col_keys if k not in COLUMN_LABELS["en"])
        assert not col_missing_fr, f"col() keys missing in FR: {col_missing_fr}"
        assert not col_missing_en, f"col() keys missing in EN: {col_missing_en}"
