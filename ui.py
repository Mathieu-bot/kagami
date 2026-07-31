"""UI constants shared across the app — Material icons and navigation.

Material Symbols are the official icon set used by the dashboard. Any
element that renders Markdown (titles, headers, metrics, captions,
buttons, ``st.page_link``) can embed one via ``:material/icon_name:``.
Keeping the mapping here centralizes every icon so pages, the sidebar
and the navigation stay consistent.
"""

# Page id → Material icon name (see https://fonts.google.com/icons).
PAGE_ICONS = {
    "hq_overview": "dashboard",
    "city_drilldown": "location_city",
    "deep_analysis": "analytics",
    "city_comparison": "balance",
    "alerts_history": "notifications_active",
    "forecast": "query_stats",
    "citizens": "health_and_safety",
    "pipeline_monitor": "monitor_heart",
    "user_management": "manage_accounts",
    "data_explorer": "table_view",
}

# Brand + footer icons.
BRAND_ICON = "eco"
FOOTER_ICON = "air"

# Navigation sections: {section_i18n_key: [page_id, ...]}. Section keys
# are resolved through t() at render time, so they stay bilingual.
NAV_SECTIONS = {
    "nav.section_analysis": [
        "hq_overview", "city_drilldown", "deep_analysis",
        "city_comparison", "forecast",
    ],
    "nav.section_operations": [
        "alerts_history", "citizens",
    ],
    "nav.section_admin": [
        "pipeline_monitor", "data_explorer", "user_management",
    ],
}


def icon(name: str) -> str:
    """Return a Material icon for use inside a Streamlit text element."""
    return f":material/{name}:"


def page_icon(page_id: str) -> str:
    """Return the ``:material/...:`` icon for a page id."""
    return icon(PAGE_ICONS.get(page_id, "apps"))
