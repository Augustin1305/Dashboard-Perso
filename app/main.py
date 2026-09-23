"""Point d'entrée du dashboard personnel."""
import os
import sys

import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Permet d'exécuter `streamlit run app/main.py` depuis la racine du projet
sys.path.insert(0, PROJECT_ROOT)

# Charge les secrets locaux (ex. OPENAI_API_KEY) depuis .env, jamais versionné.
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from app.modules import agenda, bucket_list, discoveries, finances, sport  # noqa: E402

st.set_page_config(page_title="Dashboard Perso", page_icon="🏠", layout="wide")

PAGES = {
    "🏠 Accueil": None,
    "📅 Agenda": agenda,
    "💶 Finances": finances,
    "🏃 Sport": sport,
    "📍 Mes découvertes": discoveries,
    "🪣 Bucket list": bucket_list,
}


def render_home():
    st.header("🏠 Dashboard personnel")
    st.write(
        "Bienvenue ! Utilise le menu à gauche pour naviguer entre tes suivis : "
        "**Agenda**, **Finances**, **Sport**, **Mes découvertes**."
    )
    st.info(
        "Les données sont lues depuis le dossier `data/`. Dépose tes exports "
        "(Strava, relevés bancaires, calendrier `.ics`) pour remplacer les données "
        "d'exemple, puis recharge la page."
    )


def main():
    st.sidebar.title("📊 Dashboard Perso")
    choice = st.sidebar.radio("Navigation", list(PAGES.keys()))

    module = PAGES[choice]
    if module is None:
        render_home()
    else:
        module.render()

    st.sidebar.divider()
    st.sidebar.caption("Toutes les données restent en local, dans le dossier `data/`.")


if __name__ == "__main__":
    main()
