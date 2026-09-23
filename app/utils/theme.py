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
SURFACE = "#FFFFFF"
LINE = "#E6E1D6"
SOFT = "#ECE8DF"

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
        .stButton > button { border-radius: 999px !important; min-height: 44px; }
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


def render_mood_stamp(color: str, rotate: int = 0, size: int = 52) -> str:
    """Le « tampon » de ressenti : double anneau (un plein, un pointillé)
    autour du pin, légèrement pivoté — repris de la maquette (carnet, fiche,
    planche de style). Utilisé pour un rep'r Vécu avec un ressenti choisi."""
    inner = size - 10
    pin_w, pin_h = round(size * 0.31), round(size * 0.38)
    return f"""
    <div style="width:{size}px;height:{size}px;box-sizing:border-box;border-radius:999px;
                border:1.5px solid {color};display:flex;align-items:center;justify-content:center;
                transform:rotate({rotate}deg);flex-shrink:0">
      <div style="width:{inner}px;height:{inner}px;box-sizing:border-box;border-radius:999px;
                  border:1px dashed {color};display:flex;align-items:center;justify-content:center">
        <svg width="{pin_w}" height="{pin_h}" viewBox="0 0 24 30" aria-hidden="true">
          <path d="{_PIN_PATH}" fill="{color}"/>
          <circle cx="12" cy="11.6" r="3.4" fill="{SURFACE}"/>
        </svg>
      </div>
    </div>
    """


def render_envie_pin(size: int = 28) -> str:
    """Pin en contour pointillé, sans remplissage : un rep'r "Envie" (pas
    encore testé), comme sur la carte et la planche de style."""
    height = round(size * 1.25)
    return f"""
    <svg width="{size}" height="{height}" viewBox="0 0 24 30" aria-label="Envie">
      <path d="{_PIN_PATH}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-dasharray="2.6 2.2"/>
      <circle cx="12" cy="11.6" r="2.6" fill="none" stroke="{INK}" stroke-width="1.4"/>
    </svg>
    """


def render_mood_badge(ressenti_color_hex: str, ressenti_label_text: str) -> str:
    """Petite puce plate (couleur + libellé), utilisée en ligne dans du texte
    (ex. filtres, en-tête de fiche) là où le tampon complet serait trop gros."""
    dot = f'<span style="display:inline-block;width:10px;height:10px;border-radius:999px;background:{ressenti_color_hex}"></span>'
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;'
        f'border-radius:999px;background:{SURFACE};border:1px solid {LINE};font-size:13px;'
        f'font-weight:600;color:{INK}">{dot} {ressenti_label_text}</span>'
    )
