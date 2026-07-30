"""Reusable chart helpers for Streamlit dashboards."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def sparkline_metric(label: str, value, delta=None, sparkline_df: pd.DataFrame = None,
                     x_col="time", y_col="value", color="#1E88E5"):
    """Display a metric with an inline sparkline chart."""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(label, value, delta=delta)
    with col2:
        if sparkline_df is not None and not sparkline_df.empty:
            fig = px.line(sparkline_df, x=x_col, y=y_col, height=80)
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis_visible=False,
                yaxis_visible=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig.update_traces(line=dict(color=color, width=2))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def add_alert_thresholds(fig, y_threshold=3, label="Alert Threshold"):
    """Add a horizontal dashed line for alert threshold."""
    fig.add_hline(
        y=y_threshold,
        line_dash="dash",
        line_color="red",
        opacity=0.7,
        annotation_text=label,
        annotation_position="top left",
    )
    return fig


def style_plotly_chart(fig, title=None, height=None):
    """Apply consistent styling to a Plotly chart."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16), x=0.5) if title else None,
        height=height,
        hovermode="x unified",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    )
    return fig


def aqi_color_map():
    """Return a color mapping for AQI levels."""
    return {1: "#00E400", 2: "#FFFF00", 3: "#FF7E00", 4: "#FF0000", 5: "#7E0023"}


def aqi_level_label(aqi_value: int) -> str:
    """Return a human-readable AQI level label."""
    labels = {1: "Good", 2: "Moderate", 3: "Unhealthy",
              4: "Very Unhealthy", 5: "Hazardous"}
    return labels.get(aqi_value, f"Level {aqi_value}")
