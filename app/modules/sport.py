"""Module Sport : résumé du mois, progression, répartition par type."""
import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils.parsers import parse_strava
from app.utils.viz import CATEGORICAL, apply_layout_defaults

STRAVA_PATH = "data/strava/activities.csv"


def render():
    st.header("🏃 Sport")

    df = parse_strava(STRAVA_PATH)
    if df.empty:
        st.info(
            "Aucune activité trouvée. Dépose l'export Strava (bulk export) "
            f"dans `{STRAVA_PATH}`."
        )
        return

    df["mois"] = df["date"].dt.to_period("M")
    mois_disponibles = sorted(df["mois"].unique())
    mois_courant = mois_disponibles[-1]
    df_mois = df[df["mois"] == mois_courant]

    st.subheader(f"Résumé — {mois_courant}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Séances", len(df_mois))
    col2.metric("Distance totale", f"{df_mois['distance_km'].sum():.1f} km")
    col3.metric("Dénivelé total", f"{df_mois['denivele_m'].sum():.0f} m")
    total_min = df_mois["duree_min"].sum()
    col4.metric("Temps total", f"{total_min / 60:.1f} h")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Progression dans le temps")
        metric_choice = st.radio(
            "Métrique", ["Distance (km)", "Effort relatif"], horizontal=True, label_visibility="collapsed"
        )
        y_col = "distance_km" if metric_choice.startswith("Distance") else "effort_relatif"
        fig = px.line(
            df.sort_values("date"),
            x="date",
            y=y_col,
            markers=True,
            color_discrete_sequence=CATEGORICAL,
            labels={"date": "Date", y_col: metric_choice},
        )
        fig.update_traces(line=dict(width=2))
        apply_layout_defaults(fig)
        st.plotly_chart(fig, width="stretch")

    with c2:
        st.subheader("Répartition par type d'activité")
        repartition = df_mois.groupby("type").size().reset_index(name="nombre")
        fig2 = px.bar(
            repartition.sort_values("nombre", ascending=True),
            x="nombre",
            y="type",
            orientation="h",
            color="type",
            color_discrete_sequence=CATEGORICAL,
            labels={"nombre": "Séances", "type": ""},
        )
        fig2.update_layout(showlegend=False)
        apply_layout_defaults(fig2)
        st.plotly_chart(fig2, width="stretch")

    st.divider()
    st.subheader("Historique des activités")
    display = df.sort_values("date", ascending=False).copy()
    display["date"] = display["date"].dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(display, hide_index=True, width="stretch")
