"""Jetons visuels Rep'r (couleurs, typographie, logo) et CSS léger.

Les couleurs de base de l'app (fond, boutons primaires...) sont gérées par
le thème natif Streamlit (`.streamlit/config.toml`). Ce module ajoute ce que
ce thème ne couvre pas : les polices Fraunces/Inter et le wordmark du logo.
"""
from __future__ import annotations

import streamlit as st

ACCENT = "#E4572E"
INK = "#1D2426"
MUTED = "#6E6A63"
BG = "#F6F3EC"

# Forme du pin du logo, reprise telle quelle de repr-design/HANDOFF.md.
_PIN_PATH = (
    "M12 1.5C6.2 1.5 1.5 6.1 1.5 11.8 1.5 19.3 12 28.5 12 28.5"
    "S22.5 19.3 22.5 11.8C22.5 6.1 17.8 1.5 12 1.5Z"
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Inter:wght@400;500;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4 { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; letter-spacing: -0.01em; }
        .stButton > button { border-radius: 999px !important; }
        div[data-testid="stExpander"] { border-radius: 16px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_wordmark() -> None:
    st.markdown(
        f"""
        <div style="display:flex;align-items:flex-end;gap:1px;font-family:'Fraunces',Georgia,serif;
                    font-weight:600;font-size:32px;line-height:1;letter-spacing:-0.02em;color:{INK};
                    margin-bottom:6px">
          Rep<svg width="12" height="15" viewBox="0 0 24 30" style="margin:0 2px 2px 1px">
            <path d="{_PIN_PATH}" fill="{ACCENT}"/>
            <circle cx="12" cy="11.5" r="4" fill="{BG}"/>
          </svg>r
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ressenti_badge(color: str, label: str, dashed: bool = False) -> str:
    """Retourne le HTML d'une pastille de ressenti (à passer à st.markdown).

    Pastille pleine de la couleur du ressenti pour un rep'r Vécu ; contour en
    pointillé (sans remplissage) pour un rep'r Envie, comme dans la maquette.
    """
    dot_style = (
        f"border:1.5px dashed {color};background:transparent"
        if dashed
        else f"border:1.5px solid {color};background:{color}"
    )
    dot = f'<span style="display:inline-block;width:10px;height:10px;border-radius:999px;{dot_style}"></span>'
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;'
        f'border-radius:999px;background:rgba(0,0,0,0.03);font-size:13px;font-weight:600;'
        f'color:{INK}">{dot} {label}</span>'
    )
