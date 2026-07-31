"""CSV export helpers for dashboard pages."""

import streamlit as st


def csv_download(df, label: str, filename: str):
    """Render a CSV download button if the DataFrame is non-empty."""
    if df is None or df.empty:
        return
    st.download_button(
        label=f":material/download: {label}",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )
