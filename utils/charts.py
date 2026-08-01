"""Reusable chart helpers for Streamlit dashboards.

The styling helpers avoid creating empty ``layout.title`` objects: some
Streamlit/plotly.js versions render an empty title as the literal text
"undefined" (see Plotly Community #96720). Setting ``fig.layout.title =
None`` removes the object from the serialized spec entirely.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Trace colors shared across pages (AQI scale + accents).
AQI_COLORS = ["#00E400", "#FFFF00", "#FF7E00", "#FF0000", "#7E0023"]

# Modern, colorblind-friendly accent palette for multi-series charts.
CHART_COLORWAY = ["#1E88E5", "#D81B60", "#43A047", "#F4511E",
                  "#8E24AA", "#00897B", "#FDD835", "#5E35B1"]

GRID_COLOR = "rgba(0,0,0,0.06)"


def style_plotly_chart(fig, title=None, height=None, hovermode="x unified"):
    """Apply consistent styling to a Plotly chart.

    Parameters
    ----------
    fig : go.Figure
        Figure to style in place.
    title : str, optional
        Chart title. When falsy, the title object is *removed* from the
        spec so plotly.js never renders an empty title (which some
        versions display as "undefined").
    height : int, optional
        Fixed figure height.
    hovermode : str or None, optional
        ``"x unified"`` for time series, ``"closest"`` otherwise.
    """
    if title:
        fig.update_layout(
            title=dict(text=title, font=dict(size=16), x=0.5),
        )
    else:
        # Remove the title object entirely (avoids the empty-title bug).
        fig.layout.title = None
    layout = dict(
        height=height,
        hovermode=hovermode,
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
        colorway=CHART_COLORWAY,
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="rgba(0,0,0,0.2)",
            font=dict(size=12, color="#333"),
        ),
    )
    fig.update_layout(**layout)
    return fig


def rename_traces(fig, labels: dict) -> go.Figure:
    """Rename traces using a ``{trace_name: display_label}`` mapping.

    ``px.line(df, y=["a", "b"], labels=...)`` translates axis/legend
    titles but leaves the raw trace names unchanged in the legend.
    This helper renames each trace so the legend shows friendly labels.
    """
    for trace in fig.data:
        if trace.name in labels:
            trace.name = labels[trace.name]
    return fig


def set_hover_template(fig, fmt: str = ".1f") -> go.Figure:
    """Apply a compact numeric hover template to every trace."""
    fig.update_traces(
        hovertemplate=(
            "<b>%{fullData.name}</b><br>" if hasattr(fig.data[0], "name") else ""
        ) + "%{y:" + fmt + "}<extra></extra>",
    )
    return fig


def dropna_for_chart(df: pd.DataFrame, cols) -> pd.DataFrame:
    """Drop rows with NaN in any of ``cols`` before charting.

    Aggregate queries without a GROUP BY can return a single row with
    NULL aggregates; plotting such rows renders as "nan" / empty values.
    """
    if df is None or df.empty:
        return df
    return df.dropna(subset=list(cols))


def fmt_num(value, digits: int = 2) -> str:
    """Format a number for display, tolerating None/NaN safely."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "–"
    if pd.isna(f):
        return "–"
    return f"{f:.{digits}f}".rstrip("0").rstrip(".") if digits else str(int(f))


def aqi_badge_color(aqi_value: float) -> str:
    """Badge color for an AQI value: green, orange (alert), or red."""
    if aqi_value >= 4:
        return "red"
    if aqi_value >= 3:
        return "orange"
    return "green"


def render_city_badges(df: pd.DataFrame, aqi_col: str = "aqi",
                       max_cols: int = 8, show_freshness: bool = False):
    """Render one badge per city in a stable multi-row grid.

    Uses a fixed number of columns (W3 fix: ``st.columns(len(df))`` is
    unstable when the city count changes between refreshes) and reuses a
    single code path for every page showing live city status (W7 fix:
    citizens + control room share this renderer).

    Parameters
    ----------
    df : pd.DataFrame
        Rows of ``city_name`` + AQI (and optionally ``last_record``).
    aqi_col : str
        Column holding the AQI value.
    max_cols : int
        Number of badges per row.
    show_freshness : bool
        Also display the ``last_record`` freshness caption.
    """
    rows = df.reset_index(drop=True)
    for start in range(0, len(rows), max_cols):
        batch = rows.iloc[start:start + max_cols]
        cols = st.columns(len(batch))
        for col_box, (_, row) in zip(cols, batch.iterrows()):
            aqi = int(round(float(row[aqi_col]))) if pd.notna(row[aqi_col]) else 0
            color = aqi_badge_color(aqi)
            with col_box:
                with st.container(border=True, key=f"panel_badge_{row['city_name']}"):
                    st.markdown(f"**{row['city_name']}**")
                    st.markdown(f":{color}[**AQI {aqi}**]")
                    if show_freshness and "last_record" in rows.columns:
                        st.caption(_freshness(row.get("last_record")))


def _freshness(ts) -> str:
    """Human-readable freshness of a reading timestamp (used by badges)."""
    from datetime import datetime, timezone
    from i18n import t
    if ts is None or (isinstance(ts, float) and pd.isna(ts)):
        return t("alerts.offline")
    parsed = pd.to_datetime(ts)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    minutes = int((datetime.now(timezone.utc) - parsed).total_seconds() / 60)
    if minutes < 2:
        return t("alerts.now")
    if minutes <= 120:
        return t("alerts.fresh_min", m=minutes)
    return t("alerts.offline")


def pipeline_status_label(status: str) -> tuple:
    """Return ``(material_icon, translated_label)`` for a pipeline status."""
    from i18n import t
    icons = {"Up to date": ":material/check_circle:",
             "Delayed": ":material/schedule:",
             "Critical": ":material/error:"}
    label = {
        "Up to date": t("hq.status_up_to_date"),
        "Delayed": t("hq.status_delayed"),
        "Critical": t("hq.status_critical"),
    }
    return icons.get(status, ":material/help:"), label.get(status, status)


def aqi_level_label(aqi_value: int, lang: str = None) -> str:
    """Return a human-readable AQI level label (language-aware).

    Outside a Streamlit runtime (e.g. plain unit tests) the language
    falls back to English so the helper never crashes.
    """
    from i18n import t
    if lang is None:
        try:
            from i18n import current_lang
            lang = current_lang()
        except Exception:
            lang = "en"
    key = {1: "level.good", 2: "level.moderate", 3: "level.unhealthy",
           4: "level.very_unhealthy", 5: "level.hazardous"}.get(aqi_value)
    if key:
        return t(key, lang=lang)
    return t("level.fallback", lang=lang, v=aqi_value)
