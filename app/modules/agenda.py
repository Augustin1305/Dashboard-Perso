"""Module Agenda : événements à venir importés depuis un export .ics."""
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from app.utils.parsers import parse_ics

ICS_PATH = "data/calendrier/export.ics"


def render():
    st.header("📅 Agenda")

    events = parse_ics(ICS_PATH)

    if events.empty:
        st.info(
            "Aucun événement trouvé. Dépose un export `.ics` de ton calendrier "
            f"dans `{ICS_PATH}`."
        )
        return

    now = pd.Timestamp.now()
    horizon = st.radio("Horizon", ["7 prochains jours", "30 prochains jours"], horizontal=True)
    days = 7 if horizon.startswith("7") else 30
    limit = now + timedelta(days=days)

    upcoming = events[(events["debut"] >= now) & (events["debut"] <= limit)].sort_values("debut")

    col1, col2 = st.columns(2)
    col1.metric("Événements à venir", len(upcoming))
    if not upcoming.empty:
        col2.metric("Prochain événement", upcoming.iloc[0]["titre"])

    st.divider()

    view_mode = st.radio("Vue", ["Liste", "Par jour"], horizontal=True)

    if upcoming.empty:
        st.success(f"Aucun événement dans les {days} prochains jours 🎉")
        return

    if view_mode == "Liste":
        display = upcoming.copy()
        display["Date"] = display["debut"].dt.strftime("%a %d %b %Y")
        display["Heure"] = display["debut"].dt.strftime("%H:%M")
        display = display.rename(columns={"titre": "Titre", "lieu": "Lieu"})
        st.dataframe(
            display[["Date", "Heure", "Titre", "Lieu"]],
            hide_index=True,
            width="stretch",
        )
    else:
        for day, group in upcoming.groupby(upcoming["debut"].dt.date):
            st.subheader(day.strftime("%A %d %B %Y"))
            for _, ev in group.iterrows():
                lieu = f" — 📍 {ev['lieu']}" if ev["lieu"] else ""
                st.markdown(f"- **{ev['debut'].strftime('%H:%M')}** {ev['titre']}{lieu}")
