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
from queries import control_room_status, citizen_who_exceedance, best_hour_per_city, list_cities
from utils.charts import render_city_badges
from utils import filters
from i18n import t, col, period_label, translate_df
from ui import page_icon

# ─── Page config (must be first) ───
st.set_page_config(
    page_title="Kagami — Citizens & Health",
    page_icon=page_icon("citizens"),
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
render_sidebar()

st.title(t("citizens.title"))
st.caption(t("citizens.caption"))

try:
    # ─── Local filter: cities ───
    with st.popover(t("common.filters")):
        df_city_opt = list_cities()
        city_options = df_city_opt["city_name"].tolist() if not df_city_opt.empty else []
        filters.cities_multiselect(city_options, key="citizens_cities")
    selected_cities = filters.selected("citizens_cities")

    # ─── Understand the AQI ───
    with st.container(border=True, key="panel_citizens_understand"):
        st.subheader(t("citizens.understand_aqi"))
        st.caption(t("citizens.understand_aqi_caption"))
        st.markdown(t("citizens.aqi_explained"))

    # ─── What to do by level ───
    with st.container(border=True, key="panel_citizens_advice"):
        st.subheader(t("citizens.what_to_do"))
        st.caption(t("citizens.what_to_do_caption"))
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
    with st.container(border=True, key="panel_citizens_vulnerable"):
        st.subheader(t("citizens.vulnerable"))
        st.caption(t("citizens.vulnerable_caption"))
        st.markdown(t("citizens.vulnerable_text"))

    # ─── Monitored pollutants ───
    with st.container(border=True, key="panel_citizens_pollutants"):
        st.subheader(t("citizens.pollutants"))
        st.caption(t("citizens.pollutants_caption"))
        for text in (
            t("citizens.pm25_text"),
            t("citizens.pm10_text"),
            t("citizens.no2_text"),
            t("citizens.o3_text"),
        ):
            st.markdown(f"- {text}")

    # ─── Live air quality badges ───
    with st.container(border=True, key="panel_citizens_realtime"):
        st.subheader(t("citizens.realtime"))
        st.caption(t("citizens.realtime_caption"))
        df_live = control_room_status()
        if selected_cities and not df_live.empty and "city_name" in df_live.columns:
            df_live = df_live[df_live["city_name"].isin(selected_cities)]
        if df_live.empty:
            st.info(t("citizens.no_live_data"))
        else:
            render_city_badges(df_live)

    # ─── WHO threshold exceedances by city ───
    with st.container(border=True, key="panel_citizens_who"):
        st.subheader(t("citizens.who_health"))
        st.caption(t("citizens.who_health_caption"))
        df_who = citizen_who_exceedance()
        if selected_cities and not df_who.empty and "city_name" in df_who.columns:
            df_who = df_who[df_who["city_name"].isin(selected_cities)]
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

    # ─── Best hour to go out (EDA 4.12) ───
    with st.container(border=True, key="panel_citizens_best_hour"):
        st.subheader(t("citizens.best_hour"))
        st.caption(t("citizens.best_hour_caption", period=period_label("30d")))
        df_hour = best_hour_per_city("30d")
        if selected_cities and not df_hour.empty and "city_name" in df_hour.columns:
            df_hour = df_hour[df_hour["city_name"].isin(selected_cities)]
        if not df_hour.empty:
            display = df_hour.copy()
            display["best_hour"] = display["best_hour"].apply(
                lambda h: f"{int(h):02d}:00" if pd.notna(h) else "-")
            st.dataframe(
                translate_df(display[["city_name", "best_hour", "avg_aqi"]]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(t("citizens.best_hour_no_data"))

    # ─── About the data (EDA section 6 limits) ───
    with st.expander(t("citizens.data_notes"), expanded=False):
        st.caption(t("citizens.data_notes_caption"))
        for note in (
            t("citizens.note_aqi_scale"),
            t("citizens.note_co_unit"),
            t("citizens.note_satellite"),
            t("citizens.note_no"),
        ):
            st.markdown(f"- {note}")
except DatabaseError as e:
    st.error(t("common.db_error", msg=e))
