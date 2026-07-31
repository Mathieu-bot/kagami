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
