"""Lightweight internationalization (FR/EN) for the Kagami dashboards.

- `t("key")`      → translated string for the current session language
- `col("key")`    → translated DataFrame column header
- `init_lang()`   → seed ``st.session_state["lang"]`` (default: "fr")
- `lang_selector()` → FR/EN widget for the sidebar
- `translate_df(df)` → rename DataFrame columns to the current language

Internal identifiers (roles, page ids, SQL aliases) stay in English; only
what is displayed to the user is translated.
"""

import streamlit as st

DEFAULT_LANG = "fr"
LANGUAGES = ("fr", "en")

# ─── Display strings ───
STRINGS = {
    "fr": {
        # ── common ──
        "common.db_error": "❌ Erreur base de données : {msg}",
        "common.no_data": "Aucune donnée disponible",
        "common.no_data_yet": "Aucune donnée disponible pour le moment.",
        "common.no_cities": "Aucune ville trouvée dans la base",
        "common.no_cities_avail": "Aucune ville disponible.",
        "common.export_csv": "⬇️ Exporter les données (CSV)",
        "common.download_csv": "⬇️ Télécharger le CSV",
        "common.period": "Période",
        "common.cities": "Villes",
        "common.select_city": "Choisir la ville",
        "common.trend_7d": "Tendance 7 jours",
        "common.alert_threshold": "Seuil d'alerte (AQI ≥ 3)",
        "common.alert_threshold_short": "Seuil d'alerte",
        "common.value": "Valeur",
        "common.metric": "Indicateur",
        "common.date": "Date",
        "common.average": "Moyenne",
        "common.hour_of_day": "Heure du jour",
        "common.pollutant": "Polluant",
        "common.no_pollutant_data": "Aucune donnée de polluants sur cette période.",
        "common.last_record": "Dernier enregistrement : {ts}",

        # ── navigation ──
        "nav.hq_overview": "📊 Vue d'ensemble",
        "nav.city_drilldown": "🏙️ Détail par ville",
        "nav.deep_analysis": "🔬 Analyse approfondie",
        "nav.city_comparison": "⚖️ Comparateur de villes",
        "nav.alerts_history": "🚨 Salle de contrôle & alertes",
        "nav.forecast": "🔮 Prévision AQI",
        "nav.citizens": "🏥 Info citoyens & santé",
        "nav.pipeline_monitor": "⚙️ Monitoring technique",
        "nav.user_management": "👥 Gestion des utilisateurs",
        "nav.data_explorer": "🗄️ Explorateur de données",

        # ── sidebar ──
        "sidebar.signed_in_as": "Connecté en tant que **{name}**",
        "sidebar.role": "Rôle : **{role}**",
        "sidebar.sign_out": "🚪 Se déconnecter",
        "sidebar.public_viewer": "Visiteur public — données ouvertes",
        "sidebar.navigation": "Navigation",
        "sidebar.filters": "Filtres",
        "sidebar.language": "🌐 Langue / Language",
        "sidebar.cities_error": "⚠️ Impossible de charger les villes depuis la base.",
        "sidebar.footer": "🌱 Données publiques de qualité de l'air · Connexion admin pour la gestion",

        # ── auth ──
        "auth.login_title": "## 🔐 Connexion admin",
        "auth.login_caption": "_Connectez-vous pour accéder aux pages admin. Les données de qualité de l'air restent publiques._",
        "auth.tab_google": "Se connecter avec Google",
        "auth.tab_password": "Identifiant & mot de passe",
        "auth.google_unconfigured": "La connexion Google n'est pas encore configurée — utilisez Identifiant & mot de passe.",
        "auth.username": "Identifiant",
        "auth.password": "Mot de passe",
        "auth.sign_in": "Se connecter",
        "auth.invalid_credentials": "❌ Identifiant ou mot de passe invalide.",
        "auth.access_denied": "⛔ Accès refusé — rôle {role} requis.",
        "auth.role_admin": "admin",
        "auth.role_viewer": "lecteur",

        # ── HQ Overview ──
        "hq.title": "📊 Vue d'ensemble",
        "hq.caption": "_Puis-je respirer l'air aujourd'hui ? — Réponse en 5 secondes_",
        "hq.aqi_today": "🌤️ AQI aujourd'hui",
        "hq.cities_in_alert": "🚨 Villes en alerte",
        "hq.data_completeness": "📡 Complétude des données",
        "hq.days_without_alert": "🏆 Jours sans alerte",
        "hq.aqi_evolution": "📈 Évolution de l'AQI",
        "hq.aqi_map": "🗺️ Carte de la qualité de l'air",
        "hq.aqi_distribution": "📊 Répartition de l'AQI",
        "hq.worst_pollutant": "🏭 Pire polluant vs seuil OMS",
        "hq.pct_of_who": "{pct}% de la limite OMS ({thr} µg/m³)",
        "hq.pct_of_who_threshold": "{pct}% du seuil OMS",
        "hq.who_exceedance": "⚠️ Taux de dépassement OMS",
        "hq.readings_exceeding": "Mesures dépassant les limites OMS",
        "hq.pipeline_health": "🔄 Santé du pipeline",
        "hq.status_up_to_date": "À jour",
        "hq.status_delayed": "En retard",
        "hq.status_critical": "Critique",
        "hq.measure": "Mesure",
        "hq.measurements": "Mesures",
        "hq.aqi_level": "Niveau d'AQI",
        "hq.exec_attention": "📋 Points d'attention & recommandations",
        "hq.exec_caption": "_Généré automatiquement depuis les dernières données_",
        "hq.attention_best_city": "🟢 Meilleure ville aujourd'hui : **{city}** (AQI {aqi})",
        "hq.attention_worst_city": "🔴 Ville la plus polluée aujourd'hui : **{city}** (AQI {aqi})",
        "hq.attention_worst_pollutant": "🏭 Pire polluant : **{pollutant}** à {pct}% du seuil OMS",
        "hq.attention_cities_alert": "🚨 {n} ville(s) en alerte actuellement",
        "hq.attention_trend_up": "📈 L'AQI est en hausse de {delta} vs hier",
        "hq.attention_trend_down": "📉 L'AQI a baissé de {delta} vs hier",
        "hq.attention_trend_flat": "➡️ AQI stable vs hier ({delta})",
        "hq.attention_no_alerts": "✅ Aucune ville en alerte — bonne qualité de l'air",
        "hq.attention_gap": "⚠️ {pct}% de complétude des données — vérifier le pipeline",

        # ── City Drill-down ──
        "drill.title": "🏙️ Détail par ville",
        "drill.caption": "_Analyse détaillée d'une ville spécifique_",
        "drill.current_aqi_city": "🌤️ AQI actuel — {city}",
        "drill.right_now": "À l'instant",
        "drill.vs_national": "⚖️ {city} vs moyenne nationale",
        "drill.hourly_profile": "🕐 Profil horaire — {city}",
        "drill.avg_by_hour": "Niveaux moyens de polluants par heure (derniers {period})",
        "drill.all_pollutants": "📈 Tous les polluants — Série temporelle",
        "drill.all_pollutants_title": "Tous les polluants — {city}",
        "drill.who_thresholds_city": "🏭 Polluants vs seuils OMS — {city}",
        "drill.who_caption": "_Les lignes pointillées sont les lignes directrices OMS 24h (µg/m³)_",
        "drill.worst_episodes": "⚠️ Pires épisodes",
        "drill.no_bad_episodes": "✅ Aucun mauvais épisode sur cette période !",
        "drill.status_alert": "Alerte",
        "drill.status_who_pm25": "OMS PM2.5",

        # ── Deep Analysis ──
        "deep.title": "🔬 Analyse approfondie",
        "deep.caption": "_Conforme EDA : statistiques, valeurs aberrantes, corrélations, multi-dimensionnel_",
        "deep.boxplot": "📦 Boîte à moustaches — AQI par mois",
        "deep.boxplot_caption": "_Détection de valeurs aberrantes : les points au-delà des moustaches sont des mesures inhabituelles_",
        "deep.boxplot_title": "Répartition de l'AQI par mois",
        "deep.scatter": "🔵 PM2.5 vs AQI",
        "deep.scatter_caption": "_Avec ligne de tendance de régression linéaire_",
        "deep.ols_warning": "⚠️ Ligne OLS indisponible (statsmodels non installé). Affichage sans tendance.",
        "deep.heatmap": "🟥 Carte de chaleur — AQI par heure × jour",
        "deep.heatmap_caption": "_Vue multi-dimensionnelle : plus sombre = air de moins bonne qualité_",
        "deep.corr_matrix": "🔗 Matrice de corrélation des polluants",
        "deep.corr_caption": "_1.0 = corrélation parfaite, 0 = aucune, -1 = inverse_",
        "deep.key_insight": "💡 **Point clé :** l'AQI est le plus corrélé avec PM2.5 ({pm25}) et PM10 ({pm10})",
        "deep.monthly_stats": "📊 Distribution statistique mensuelle",
        "deep.seasonal": "🏜️ Analyse saisonnière",
        "deep.seasonal_title": "Saison sèche vs saison des pluies",
        "deep.weekday_weekend": "💼 Jour de semaine vs week-end",
        "deep.weekday_weekend_title": "Effet jour de semaine vs week-end",
        "deep.correlation": "Corrélation",
        "deep.hour": "Heure",
        "deep.day": "Jour",

        # ── City Comparison ──
        "compare.title": "⚖️ Comparateur de villes",
        "compare.caption": "_Comment les villes se comparent-elles maintenant et sur la dernière semaine ?_",
        "compare.mode": "Mode",
        "compare.mode_all": "Toutes les villes",
        "compare.mode_2cities": "Comparer 2 villes",
        "compare.city_a": "Ville A",
        "compare.city_b": "Ville B",
        "compare.best_air": "🟢 Meilleur air",
        "compare.worst_air": "🔴 Pire air",
        "compare.cities_count": "🏙️ Villes",
        "compare.current_aqi_by_city": "📊 AQI actuel par ville",
        "compare.current_aqi": "AQI actuel",
        "compare.trend_7d_title": "📈 Tendance AQI sur 7 jours",
        "compare.avg_aqi": "AQI moyen",
        "compare.ranking": "🏆 Classement",
        "compare.versus": "⚖️ {a} vs {b}",
        "compare.aqi_now": "AQI maintenant",
        "compare.aqi_diff": "{a} vs {b}",
        "compare.winner": "🏆 Meilleur air : **{city}**",
        "compare.pollutant_compare": "📊 Comparaison des polluants",
        "compare.avg_this_week": "Moyenne sur 7 jours",

        # ── Alerts / Control room ──
        "alerts.title": "🚨 Salle de contrôle & alertes",
        "alerts.caption": "_Historique des épisodes où l'AQI a atteint le niveau d'alerte (≥ 3)_",
        "alerts.last_days": "Derniers {d} jours",
        "alerts.no_alerts": "✅ Aucun épisode d'alerte sur cette période — excellente qualité de l'air !",
        "alerts.total_alerts": "🚨 Total d'alertes",
        "alerts.worst_episode": "🔥 Pire épisode",
        "alerts.cities_affected": "🏙️ Villes touchées",
        "alerts.alerts_per_city": "📊 Alertes par ville",
        "alerts.alerts": "Alertes",
        "alerts.worst_aqi": "Pire AQI",
        "alerts.recent_episodes": "🗒️ Épisodes récents",
        "alerts.control_title": "🖥️ État en direct des villes",
        "alerts.control_caption": "_Rafraîchi automatiquement toutes les 30 secondes_",
        "alerts.now": "Maintenant",
        "alerts.fresh_min": "il y a {m} min",
        "alerts.offline": "Hors ligne",
        "alerts.no_control_data": "Aucune donnée temps réel disponible.",

        # ── Forecast ──
        "forecast.title": "🔮 Prévision AQI",
        "forecast.caption": "_Prévision AQI sur 7 jours par ville (ARIMA, avec repli moyenne mobile)_",
        "forecast.no_history": "Historique insuffisant pour prévoir — les données s'accumulent encore.",
        "forecast.no_history2": "Historique insuffisant pour prévoir.",
        "forecast.next_7d_avg": "🔮 Moyenne 7 prochains jours",
        "forecast.day7": "📅 Jour 7",
        "forecast.trend_metric": "📈 Tendance",
        "forecast.improving": "Amélioration 📉",
        "forecast.worsening": "Dégradation 📈",
        "forecast.stable": "Stable ➡️",
        "forecast.history_forecast": "📈 Historique + Prévision — {city}",
        "forecast.history": "Historique",
        "forecast.forecast_series": "Prévision",
        "forecast.details": "🗓️ Détails de la prévision",
        "forecast.ci": "IC 80%",

        # ── Pipeline Monitor ──
        "pipeline.title": "⚙️ Monitoring technique",
        "pipeline.caption": "_Panneau admin — santé et qualité du pipeline de données_",
        "pipeline.status": "🔄 Statut du pipeline",
        "pipeline.last_ingestion": "🕐 Dernière ingestion",
        "pipeline.last_record": "Dernier enregistrement",
        "pipeline.data_completeness": "📡 Complétude des données",
        "pipeline.today": "Aujourd'hui",
        "pipeline.records_per_day": "📊 Enregistrements par jour (7 derniers jours)",
        "pipeline.records": "Enregistrements",
        "pipeline.missing_data": "🔍 Détection des données manquantes (24 dernières heures)",
        "pipeline.complete_records": "✅ Enregistrements complets",
        "pipeline.missing_records": "❌ Enregistrements manquants",
        "pipeline.missing_warning": "⚠️ {n} enregistrements manquants sur {total}",
        "pipeline.no_missing": "✅ Aucune donnée manquante sur les 24 dernières heures",
        "pipeline.complete": "Complet",
        "pipeline.missing": "Manquant",

        # ── User Management ──
        "users.title": "👥 Gestion des utilisateurs",
        "users.caption": "_Gérez l'accès admin — utilisateurs stockés en local, NeonDB inchangée._",
        "users.create": "➕ Créer un utilisateur",
        "users.email_optional": "Email (optionnel, pour la connexion Google)",
        "users.create_btn": "Créer l'utilisateur",
        "users.required": "Identifiant et mot de passe sont requis.",
        "users.created": "Utilisateur '{name}' créé.",
        "users.existing": "Utilisateurs existants",
        "users.none": "Aucun utilisateur — créez le premier ci-dessus.",
        "users.update_role": "Mettre à jour le rôle",
        "users.role_updated": "Rôle de '{name}' défini sur {role}.",
        "users.active": "Actif",
        "users.toggle_active": "Activer/Désactiver",
        "users.toggled": "'{name}' actif = {active}.",
        "users.new_password": "Nouveau mot de passe",
        "users.reset_password": "Réinitialiser le mot de passe",
        "users.password_updated": "Mot de passe de '{name}' mis à jour.",
        "users.enter_password": "Saisissez d'abord un nouveau mot de passe.",
        "users.delete": "🗑 Supprimer",
        "users.deleted": "Utilisateur '{name}' supprimé.",

        # ── Data Explorer ──
        "explorer.title": "🗄️ Explorateur de données",
        "explorer.caption": "_Accès SQL en lecture seule à l'entrepôt NeonDB (admin)_",
        "explorer.quick": "⚡ Requêtes rapides",
        "explorer.pick": "Choisir une requête",
        "explorer.custom": "— SQL personnalisé —",
        "explorer.sql_label": "SQL (lecture seule)",
        "explorer.run": "▶️ Exécuter la requête",
        "explorer.hint": "Uniquement SELECT / WITH / EXPLAIN. Résultats limités à {max} lignes.",
        "explorer.write_query": "Écrivez d'abord une requête.",
        "explorer.read_only": "⛔ Seules les requêtes en lecture seule (SELECT / WITH / EXPLAIN) sont autorisées.",
        "explorer.running": "Exécution de la requête...",
        "explorer.rows": "✅ {n} ligne(s) renvoyée(s).",

        # ── Citizens page ──
        "citizens.title": "🏥 Info citoyens & santé publique",
        "citizens.caption": "_Comprendre la qualité de l'air et protéger sa santé — en langage simple_",
        "citizens.understand_aqi": "🧠 Comprendre l'indice AQI",
        "citizens.aqi_explained": "L'indice de qualité de l'air (AQI) va de **1 (excellent)** à **5 (dangereux)**. Plus il est élevé, plus l'air est pollué et plus les effets sur la santé peuvent être graves.",
        "citizens.what_to_do": "💡 Que faire selon le niveau ?",
        "citizens.vulnerable": "👶 Groupes vulnérables",
        "citizens.vulnerable_text": "Les **enfants**, les **personnes âgées**, les **femmes enceintes** et les personnes souffrant d'**asthme** ou de **maladies cardiaques** sont les plus sensibles à la pollution de l'air.",
        "citizens.pollutants": "🧪 Les polluants surveillés",
        "citizens.pm25_text": "Poussières fines (PM2.5) : pénètrent profondément dans les poumons et le sang.",
        "citizens.pm10_text": "Poussières plus grossières (PM10) : irritent les voies respiratoires.",
        "citizens.no2_text": "Dioxyde d'azote (NO₂) : issu du trafic et de la combustion.",
        "citizens.o3_text": "Ozone (O₃) : se forme en plein soleil, irrite les poumons.",
        "citizens.who_health": "🏥 Dépassements des seuils OMS par ville",
        "citizens.who_health_caption": "_Pourcentage de jours où la concentration dépasse la ligne directrice OMS 24h (7 derniers jours)_",
        "citizens.realtime": "🟢 Qualité de l'air en ce moment",
        "citizens.realtime_caption": "_Badges en direct pour chaque ville (mise à jour manuelle via rechargement)_",
        "citizens.aqi_good": "Bon",
        "citizens.aqi_moderate": "Modéré",
        "citizens.aqi_unhealthy": "Mauvais pour la santé",
        "citizens.aqi_very_unhealthy": "Très mauvais pour la santé",
        "citizens.aqi_hazardous": "Dangereux",
        "citizens.advice_1": "Vous pouvez profiter de l'air libre, l'air est propre.",
        "citizens.advice_2": "Air acceptable. Les personnes très sensibles peuvent réduire les efforts prolongés en extérieur.",
        "citizens.advice_3": "Réduisez les activités physiques intenses à l'extérieur. Groupes vulnérables : restez à l'intérieur si possible.",
        "citizens.advice_4": "Évitez toute activité en extérieur. Fermez les fenêtres et utilisez un masque si vous devez sortir.",
        "citizens.advice_5": "Restez à l'intérieur, portez un masque en extérieur, aérez peu et suivez les consignes des autorités.",

        # ── AQI levels ──
        "level.good": "Bon",
        "level.moderate": "Modéré",
        "level.unhealthy": "Mauvais pour la santé",
        "level.very_unhealthy": "Très mauvais pour la santé",
        "level.hazardous": "Dangereux",
        "level.fallback": "Niveau {v}",
    },
    "en": {
        # ── common ──
        "common.db_error": "❌ Database error: {msg}",
        "common.no_data": "No data available",
        "common.no_data_yet": "No data available yet.",
        "common.no_cities": "No cities found in database",
        "common.no_cities_avail": "No cities available.",
        "common.export_csv": "⬇️ Export data (CSV)",
        "common.download_csv": "⬇️ Download CSV",
        "common.period": "Period",
        "common.cities": "Cities",
        "common.select_city": "Select City",
        "common.trend_7d": "7-day Trend",
        "common.alert_threshold": "Alert Threshold (AQI ≥ 3)",
        "common.alert_threshold_short": "Alert Threshold",
        "common.value": "Value",
        "common.metric": "Metric",
        "common.date": "Date",
        "common.average": "Average",
        "common.hour_of_day": "Hour of Day",
        "common.pollutant": "Pollutant",
        "common.no_pollutant_data": "No pollutant data for this period.",
        "common.last_record": "Last record: {ts}",

        # ── navigation ──
        "nav.hq_overview": "📊 HQ Overview",
        "nav.city_drilldown": "🏙️ City Drill-down",
        "nav.deep_analysis": "🔬 Deep Analysis",
        "nav.city_comparison": "⚖️ City Comparison",
        "nav.alerts_history": "🚨 Alerts & Control Room",
        "nav.forecast": "🔮 AQI Forecast",
        "nav.citizens": "🏥 Citizens & Health Info",
        "nav.pipeline_monitor": "⚙️ Pipeline Monitor",
        "nav.user_management": "👥 User Management",
        "nav.data_explorer": "🗄️ Data Explorer",

        # ── sidebar ──
        "sidebar.signed_in_as": "Signed in as **{name}**",
        "sidebar.role": "Role: **{role}**",
        "sidebar.sign_out": "🚪 Sign out",
        "sidebar.public_viewer": "Public viewer — data is open",
        "sidebar.navigation": "Navigation",
        "sidebar.filters": "Filters",
        "sidebar.language": "🌐 Language / Langue",
        "sidebar.cities_error": "⚠️ Could not load cities from database.",
        "sidebar.footer": "🌱 Public air quality data · Admin login for management",

        # ── auth ──
        "auth.login_title": "## 🔐 Admin Login",
        "auth.login_caption": "_Sign in to access admin pages. Air quality data stays public._",
        "auth.tab_google": "Sign in with Google",
        "auth.tab_password": "Username & Password",
        "auth.google_unconfigured": "Google login is not configured yet — use Username & Password.",
        "auth.username": "Username",
        "auth.password": "Password",
        "auth.sign_in": "Sign in",
        "auth.invalid_credentials": "❌ Invalid username or password.",
        "auth.access_denied": "⛔ Access denied — {role} role required.",
        "auth.role_admin": "admin",
        "auth.role_viewer": "viewer",

        # ── HQ Overview ──
        "hq.title": "📊 HQ Overview",
        "hq.caption": "_Can I trust the air today? — Answered in 5 seconds_",
        "hq.aqi_today": "🌤️ AQI Today",
        "hq.cities_in_alert": "🚨 Cities in Alert",
        "hq.data_completeness": "📡 Data Completeness",
        "hq.days_without_alert": "🏆 Days Without Alert",
        "hq.aqi_evolution": "📈 AQI Evolution",
        "hq.aqi_map": "🗺️ Air Quality Map",
        "hq.aqi_distribution": "📊 AQI Distribution",
        "hq.worst_pollutant": "🏭 Worst Pollutant vs WHO Threshold",
        "hq.pct_of_who": "{pct}% of WHO limit ({thr} µg/m³)",
        "hq.pct_of_who_threshold": "{pct}% of WHO threshold",
        "hq.who_exceedance": "⚠️ WHO Exceedance Rate",
        "hq.readings_exceeding": "Readings exceeding WHO limits",
        "hq.pipeline_health": "🔄 Pipeline Health",
        "hq.status_up_to_date": "Up to date",
        "hq.status_delayed": "Delayed",
        "hq.status_critical": "Critical",
        "hq.measure": "Measure",
        "hq.measurements": "Measurements",
        "hq.aqi_level": "AQI Level",
        "hq.exec_attention": "📋 Key Points & Recommendations",
        "hq.exec_caption": "_Auto-generated from the latest data_",
        "hq.attention_best_city": "🟢 Best city today: **{city}** (AQI {aqi})",
        "hq.attention_worst_city": "🔴 Most polluted city today: **{city}** (AQI {aqi})",
        "hq.attention_worst_pollutant": "🏭 Worst pollutant: **{pollutant}** at {pct}% of the WHO limit",
        "hq.attention_cities_alert": "🚨 {n} city/cities in alert right now",
        "hq.attention_trend_up": "📈 AQI up by {delta} vs yesterday",
        "hq.attention_trend_down": "📉 AQI down by {delta} vs yesterday",
        "hq.attention_trend_flat": "➡️ AQI stable vs yesterday ({delta})",
        "hq.attention_no_alerts": "✅ No city in alert — good air quality",
        "hq.attention_gap": "⚠️ {pct}% data completeness — check the pipeline",

        # ── City Drill-down ──
        "drill.title": "🏙️ City Drill-down",
        "drill.caption": "_Detailed analysis for a specific city_",
        "drill.current_aqi_city": "🌤️ Current AQI — {city}",
        "drill.right_now": "Right Now",
        "drill.vs_national": "⚖️ {city} vs National Average",
        "drill.hourly_profile": "🕐 Hourly Profile — {city}",
        "drill.avg_by_hour": "Average pollutant levels by hour (last {period})",
        "drill.all_pollutants": "📈 All Pollutants — Time Series",
        "drill.all_pollutants_title": "All Pollutants — {city}",
        "drill.who_thresholds_city": "🏭 Pollutants vs WHO Thresholds — {city}",
        "drill.who_caption": "_Dashed lines are WHO 24h air quality guidelines (µg/m³)_",
        "drill.worst_episodes": "⚠️ Worst Episodes",
        "drill.no_bad_episodes": "✅ No bad episodes in this period!",
        "drill.status_alert": "Alert",
        "drill.status_who_pm25": "WHO PM2.5",

        # ── Deep Analysis ──
        "deep.title": "🔬 Deep Analysis",
        "deep.caption": "_EDA-compliant: statistics, outliers, correlations, multi-dimensional_",
        "deep.boxplot": "📦 Boxplot — AQI by Month",
        "deep.boxplot_caption": "_Outlier detection: dots beyond whiskers are unusual readings_",
        "deep.boxplot_title": "AQI Distribution by Month",
        "deep.scatter": "🔵 PM2.5 vs AQI",
        "deep.scatter_caption": "_With linear regression trendline_",
        "deep.ols_warning": "⚠️ OLS trendline unavailable (statsmodels not installed). Showing scatter without trendline.",
        "deep.heatmap": "🟥 Heatmap — AQI by Hour × Day",
        "deep.heatmap_caption": "_Multi-dimensional view: darker = worse air quality_",
        "deep.corr_matrix": "🔗 Pollutant Correlation Matrix",
        "deep.corr_caption": "_1.0 = perfect correlation, 0 = none, -1 = inverse_",
        "deep.key_insight": "💡 **Key insight:** AQI is most correlated with PM2.5 ({pm25}) and PM10 ({pm10})",
        "deep.monthly_stats": "📊 Monthly Statistical Distribution",
        "deep.seasonal": "🏜️ Seasonal Analysis",
        "deep.seasonal_title": "Dry Season vs Wet Season",
        "deep.weekday_weekend": "💼 Weekday vs Weekend",
        "deep.weekday_weekend_title": "Weekday vs Weekend Effect",
        "deep.correlation": "Correlation",
        "deep.hour": "Hour",
        "deep.day": "Day",

        # ── City Comparison ──
        "compare.title": "⚖️ City Comparison",
        "compare.caption": "_How do cities compare right now and over the last week?_",
        "compare.mode": "Mode",
        "compare.mode_all": "All cities",
        "compare.mode_2cities": "Compare 2 cities",
        "compare.city_a": "City A",
        "compare.city_b": "City B",
        "compare.best_air": "🟢 Best Air",
        "compare.worst_air": "🔴 Worst Air",
        "compare.cities_count": "🏙️ Cities",
        "compare.current_aqi_by_city": "📊 Current AQI by City",
        "compare.current_aqi": "Current AQI",
        "compare.trend_7d_title": "📈 7-Day AQI Trend",
        "compare.avg_aqi": "Average AQI",
        "compare.ranking": "🏆 Ranking",
        "compare.versus": "⚖️ {a} vs {b}",
        "compare.aqi_now": "AQI now",
        "compare.aqi_diff": "{a} vs {b}",
        "compare.winner": "🏆 Best air: **{city}**",
        "compare.pollutant_compare": "📊 Pollutant Comparison",
        "compare.avg_this_week": "7-day average",

        # ── Alerts / Control room ──
        "alerts.title": "🚨 Alerts & Control Room",
        "alerts.caption": "_History of episodes where AQI reached alert level (≥ 3)_",
        "alerts.last_days": "Last {d} days",
        "alerts.no_alerts": "✅ No alert episodes in this period — great air quality!",
        "alerts.total_alerts": "🚨 Total Alerts",
        "alerts.worst_episode": "🔥 Worst Episode",
        "alerts.cities_affected": "🏙️ Cities Affected",
        "alerts.alerts_per_city": "📊 Alerts per City",
        "alerts.alerts": "Alerts",
        "alerts.worst_aqi": "Worst AQI",
        "alerts.recent_episodes": "🗒️ Recent Episodes",
        "alerts.control_title": "🖥️ Live City Status",
        "alerts.control_caption": "_Auto-refreshes every 30 seconds_",
        "alerts.now": "Now",
        "alerts.fresh_min": "{m} min ago",
        "alerts.offline": "Offline",
        "alerts.no_control_data": "No real-time data available.",

        # ── Forecast ──
        "forecast.title": "🔮 AQI Forecast",
        "forecast.caption": "_7-day AQI forecast per city (ARIMA, with moving-average fallback)_",
        "forecast.no_history": "Not enough history to forecast yet — data is still accumulating.",
        "forecast.no_history2": "Not enough history to forecast yet.",
        "forecast.next_7d_avg": "🔮 Next 7d Avg",
        "forecast.day7": "📅 Day 7",
        "forecast.trend_metric": "📈 Trend",
        "forecast.improving": "Improving 📉",
        "forecast.worsening": "Worsening 📈",
        "forecast.stable": "Stable ➡️",
        "forecast.history_forecast": "📈 History + Forecast — {city}",
        "forecast.history": "History",
        "forecast.forecast_series": "Forecast",
        "forecast.details": "🗓️ Forecast Details",
        "forecast.ci": "80% CI",

        # ── Pipeline Monitor ──
        "pipeline.title": "⚙️ Pipeline Monitor",
        "pipeline.caption": "_Admin panel — data pipeline health and quality_",
        "pipeline.status": "🔄 Pipeline Status",
        "pipeline.last_ingestion": "🕐 Last Ingestion",
        "pipeline.last_record": "Last Record",
        "pipeline.data_completeness": "📡 Data Completeness",
        "pipeline.today": "Today",
        "pipeline.records_per_day": "📊 Records per Day (Last 7 Days)",
        "pipeline.records": "Records",
        "pipeline.missing_data": "🔍 Missing Data Detection (Last 24h)",
        "pipeline.complete_records": "✅ Complete Records",
        "pipeline.missing_records": "❌ Missing Records",
        "pipeline.missing_warning": "⚠️ {n} missing records detected out of {total}",
        "pipeline.no_missing": "✅ No missing data in the last 24 hours",
        "pipeline.complete": "Complete",
        "pipeline.missing": "Missing",

        # ── User Management ──
        "users.title": "👥 User Management",
        "users.caption": "_Manage admin access — users are stored locally, NeonDB stays untouched._",
        "users.create": "➕ Create user",
        "users.email_optional": "Email (optional, for Google login)",
        "users.create_btn": "Create user",
        "users.required": "Username and password are required.",
        "users.created": "User '{name}' created.",
        "users.existing": "Existing users",
        "users.none": "No users yet — create the first one above.",
        "users.update_role": "Update role",
        "users.role_updated": "Role of '{name}' set to {role}.",
        "users.active": "Active",
        "users.toggle_active": "Toggle active",
        "users.toggled": "'{name}' active = {active}.",
        "users.new_password": "New password",
        "users.reset_password": "Reset password",
        "users.password_updated": "Password of '{name}' updated.",
        "users.enter_password": "Enter a new password first.",
        "users.delete": "🗑 Delete",
        "users.deleted": "User '{name}' deleted.",

        # ── Data Explorer ──
        "explorer.title": "🗄️ Data Explorer",
        "explorer.caption": "_Read-only SQL access to the NeonDB warehouse (admin)_",
        "explorer.quick": "⚡ Quick Queries",
        "explorer.pick": "Pick a query",
        "explorer.custom": "— custom SQL —",
        "explorer.sql_label": "SQL (read-only)",
        "explorer.run": "▶️ Run query",
        "explorer.hint": "Only SELECT / WITH / EXPLAIN. Results capped at {max} rows.",
        "explorer.write_query": "Please write a query first.",
        "explorer.read_only": "⛔ Only read-only queries (SELECT / WITH / EXPLAIN) are allowed.",
        "explorer.running": "Running query...",
        "explorer.rows": "✅ {n} row(s) returned.",

        # ── Citizens page ──
        "citizens.title": "🏥 Citizens & Health Info",
        "citizens.caption": "_Understand air quality and protect your health — in plain language_",
        "citizens.understand_aqi": "🧠 Understanding the AQI",
        "citizens.aqi_explained": "The Air Quality Index (AQI) runs from **1 (excellent)** to **5 (hazardous)**. The higher it is, the more polluted the air and the more severe the possible health effects.",
        "citizens.what_to_do": "💡 What to do by level?",
        "citizens.vulnerable": "👶 Vulnerable Groups",
        "citizens.vulnerable_text": "**Children**, **elderly people**, **pregnant women** and people with **asthma** or **heart disease** are the most sensitive to air pollution.",
        "citizens.pollutants": "🧪 Monitored Pollutants",
        "citizens.pm25_text": "Fine particles (PM2.5): penetrate deep into the lungs and bloodstream.",
        "citizens.pm10_text": "Coarser particles (PM10): irritate the airways.",
        "citizens.no2_text": "Nitrogen dioxide (NO₂): from traffic and combustion.",
        "citizens.o3_text": "Ozone (O₃): forms in strong sunlight, irritates the lungs.",
        "citizens.who_health": "🏥 WHO threshold exceedances by city",
        "citizens.who_health_caption": "_Share of days where the concentration exceeds the WHO 24h guideline (last 7 days)_",
        "citizens.realtime": "🟢 Live air quality",
        "citizens.realtime_caption": "_Live badges for each city (refresh to update)_",
        "citizens.aqi_good": "Good",
        "citizens.aqi_moderate": "Moderate",
        "citizens.aqi_unhealthy": "Unhealthy",
        "citizens.aqi_very_unhealthy": "Very unhealthy",
        "citizens.aqi_hazardous": "Hazardous",
        "citizens.advice_1": "Enjoy the outdoors, the air is clean.",
        "citizens.advice_2": "Air is acceptable. Highly sensitive people may reduce prolonged outdoor effort.",
        "citizens.advice_3": "Reduce intense outdoor physical activity. Vulnerable groups: stay indoors if possible.",
        "citizens.advice_4": "Avoid all outdoor activity. Close windows and wear a mask if you must go out.",
        "citizens.advice_5": "Stay indoors, wear a mask outdoors, ventilate little and follow official advice.",

        # ── AQI levels ──
        "level.good": "Good",
        "level.moderate": "Moderate",
        "level.unhealthy": "Unhealthy",
        "level.very_unhealthy": "Very Unhealthy",
        "level.hazardous": "Hazardous",
        "level.fallback": "Level {v}",
    },
}

# ─── DataFrame column headers ───
COLUMN_LABELS = {
    "fr": {
        "city_name": "Ville", "full_date": "Date", "hour": "Heure", "aqi": "AQI",
        "current_aqi": "AQI actuel", "avg_aqi": "AQI moyen", "daily_avg": "Moyenne journalière",
        "yesterday_avg": "Moyenne hier", "trend": "Tendance",
        "alert_count": "Nb d'alertes", "max_aqi": "AQI max", "affected_days": "Jours touchés",
        "level": "Niveau", "status": "Statut",
        "forecast_date": "Date de prévision", "forecast": "Prévision",
        "lower": "Borne basse", "upper": "Borne haute",
        "records": "Enregistrements", "month": "Mois",
        "count": "Nombre", "min": "Min", "p25": "P25", "median": "Médiane", "avg": "Moyenne",
        "std": "Écart-type", "p75": "P75", "max": "Max",
        "username": "Identifiant", "email": "Email", "role": "Rôle", "active": "Actif",
        "created_at": "Créé le", "last_record": "Dernier enregistrement",
        "completeness": "Complétude", "days_without_alert": "Jours sans alerte",
        "pm2_5": "PM2.5", "pm10": "PM10", "no2": "NO₂", "o3": "O₃",
        "so2": "SO₂", "co": "CO", "nh3": "NH₃",
        "city_val": "Ville", "national_val": "Nationale", "metric": "Indicateur",
        "day_of_week": "Jour", "day_type": "Type de jour", "season": "Saison",
        "avg_pm25": "Moy. PM2.5", "avg_pm10": "Moy. PM10", "avg_o3": "Moy. O₃",
        "avg_no2": "Moy. NO₂", "time": "Heure",
    },
    "en": {
        "city_name": "City", "full_date": "Date", "hour": "Hour", "aqi": "AQI",
        "current_aqi": "Current AQI", "avg_aqi": "Average AQI", "daily_avg": "Daily average",
        "yesterday_avg": "Yesterday avg", "trend": "Trend",
        "alert_count": "Alerts", "max_aqi": "Max AQI", "affected_days": "Affected days",
        "level": "Level", "status": "Status",
        "forecast_date": "Forecast date", "forecast": "Forecast",
        "lower": "Lower bound", "upper": "Upper bound",
        "records": "Records", "month": "Month",
        "count": "Count", "min": "Min", "p25": "P25", "median": "Median", "avg": "Average",
        "std": "Std dev", "p75": "P75", "max": "Max",
        "username": "Username", "email": "Email", "role": "Role", "active": "Active",
        "created_at": "Created at", "last_record": "Last record",
        "completeness": "Completeness", "days_without_alert": "Days without alert",
        "pm2_5": "PM2.5", "pm10": "PM10", "no2": "NO₂", "o3": "O₃",
        "so2": "SO₂", "co": "CO", "nh3": "NH₃",
        "city_val": "City", "national_val": "National", "metric": "Metric",
        "day_of_week": "Day", "day_type": "Day type", "season": "Season",
        "avg_pm25": "Avg PM2.5", "avg_pm10": "Avg PM10", "avg_o3": "Avg O₃",
        "avg_no2": "Avg NO₂", "time": "Time",
    },
}

# ─── Export display names (keys of the per-page exports dict) ───
EXPORT_LABELS = {
    "fr": {
        "aqi_evolution": "Évolution de l'AQI",
        "air_quality_map": "Carte de la qualité de l'air",
        "aqi_distribution": "Répartition de l'AQI",
        "hourly_profile": "Profil horaire",
        "all_pollutants": "Tous les polluants",
        "pollutants_vs_who": "Polluants vs seuils OMS",
        "worst_episodes": "Pires épisodes",
        "boxplot_data": "Données boîte à moustaches",
        "monthly_statistics": "Statistiques mensuelles",
    },
    "en": {
        "aqi_evolution": "AQI Evolution",
        "air_quality_map": "Air Quality Map",
        "aqi_distribution": "AQI Distribution",
        "hourly_profile": "Hourly Profile",
        "all_pollutants": "All Pollutants",
        "pollutants_vs_who": "Pollutants vs WHO",
        "worst_episodes": "Worst Episodes",
        "boxplot_data": "Boxplot Data",
        "monthly_statistics": "Monthly Statistics",
    },
}


def current_lang() -> str:
    """Return the active language (defaults to French)."""
    return st.session_state.get("lang", DEFAULT_LANG)


def t(key: str, lang: str = None, **kwargs) -> str:
    """Return the translated string for `key`, falling back safely.

    `lang` overrides the session language when provided (used by helpers
    that must render a specific language without a running session).
    """
    lang = lang or current_lang()
    table = STRINGS.get(lang) or STRINGS.get(DEFAULT_LANG, {})
    text = table.get(key) or STRINGS.get(DEFAULT_LANG, {}).get(key) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def col(key: str) -> str:
    """Return the translated DataFrame column header for the current language."""
    return COLUMN_LABELS.get(current_lang(), {}).get(key, key)


def export_label(key: str) -> str:
    """Return the display label for an export (download button)."""
    return EXPORT_LABELS.get(current_lang(), {}).get(key, key)


def init_lang():
    """Seed the session language if it is not set yet."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = DEFAULT_LANG


def lang_selector():
    """Render the FR/EN selector (used in the sidebar)."""
    options = list(LANGUAGES)
    fmt = {"fr": "🇫🇷 Français", "en": "🇬🇧 English"}
    st.selectbox(
        t("sidebar.language"),
        options,
        index=0 if current_lang() == "fr" else 1,
        format_func=lambda code: fmt.get(code, code),
        key="lang",
    )


def translate_df(df):
    """Rename DataFrame columns to the current language (unknown ones kept)."""
    labels = COLUMN_LABELS.get(current_lang(), {})
    return df.rename(columns=lambda c: labels.get(str(c), c) if isinstance(c, str) else c)
