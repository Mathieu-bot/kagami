"""Dashboard 13 — Citizens & Health Info (public).

Plain-language explanation of the AQI, what to do at each level, which
groups are vulnerable, the monitored pollutants, plus live per-city
badges and WHO guideline exceedances over the last 7 days.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from auth import init_session_state
from sidebar import render_sidebar
from config import DatabaseError
from queries import control_room_status, citizen_who_exceedance
from utils.charts import aqi_badge_color
from i18n import t, col

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Citizens & Health",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title(t("citizens.title"))
st.caption(t("citizens.caption"))

try:
    # ─── Understand the AQI ───
    with st.container(border=True):
        st.subheader(t("citizens.understand_aqi"))
        st.markdown(t("citizens.aqi_explained"))

    # ─── What to do by level ───
    with st.container(border=True):
        st.subheader(t("citizens.what_to_do"))
        levels = [
            (1, t("citizens.aqi_good"), t("citizens.advice_1")),
            (2, t("citizens.aqi_moderate"), t("citizens.advice_2")),
            (3, t("citizens.aqi_unhealthy"), t("citizens.advice_3")),
            (4, t("citizens.aqi_very_unhealthy"), t("citizens.advice_4")),
            (5, t("citizens.aqi_hazardous"), t("citizens.advice_5")),
        ]
        for lvl, name, advice in levels:
            with st.expander(f"**{lvl} — {name}**", expanded=(lvl == 1)):
                st.markdown(advice)

    # ─── Vulnerable groups ───
    with st.container(border=True):
        st.subheader(t("citizens.vulnerable"))
        st.markdown(t("citizens.vulnerable_text"))

    # ─── Monitored pollutants ───
    with st.container(border=True):
        st.subheader(t("citizens.pollutants"))
        for text in (
            t("citizens.pm25_text"),
            t("citizens.pm10_text"),
            t("citizens.no2_text"),
            t("citizens.o3_text"),
        ):
            st.markdown(f"- {text}")

    # ─── Live air quality badges ───
    with st.container(border=True):
        st.subheader(t("citizens.realtime"))
        st.caption(t("citizens.realtime_caption"))
        df_live = control_room_status()
        if df_live.empty:
            st.info(t("alerts.no_control_data"))
        else:
            cols = st.columns(len(df_live))
            for badge, (_, row) in zip(cols, df_live.iterrows()):
                aqi = int(row["aqi"])
                color = aqi_badge_color(aqi)
                with badge:
                    with st.container(border=True):
                        st.markdown(f"**{row['city_name']}**")
                        st.markdown(f":{color}[**AQI {aqi}**]")

    # ─── WHO threshold exceedances by city ───
    with st.container(border=True):
        st.subheader(t("citizens.who_health"))
        st.caption(t("citizens.who_health_caption"))
        df_who = citizen_who_exceedance()
        if not df_who.empty:
            fig = px.bar(
                df_who, x="city_name", y="exceedance_rate",
                labels={"city_name": col("city_name"), "exceedance_rate": "%"},
                color="exceedance_rate",
                color_continuous_scale=["green", "yellow", "orange", "red"],
                text="exceedance_rate", height=380,
            )
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t("common.no_data"))
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
