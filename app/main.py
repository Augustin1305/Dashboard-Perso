"""Point d'entrée de Rep'r."""
import os
import sys

import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Permet d'exécuter `streamlit run app/main.py` depuis la racine du projet
sys.path.insert(0, PROJECT_ROOT)

# Charge les secrets locaux (ex. OPENAI_API_KEY) depuis .env, jamais versionné.
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from app.modules import discoveries  # noqa: E402
from app.utils import auth, theme  # noqa: E402

st.set_page_config(page_title="Rep'r", page_icon="📍", layout="wide")
theme.inject_css()


def main():
    user = auth.render_auth_gate()
    if user is None:
        return

    auth.render_logout_button()
    discoveries.render(user)

    st.sidebar.divider()
    st.sidebar.caption("Chacun ne voit que ses propres rep'rs.")


if __name__ == "__main__":
    main()
