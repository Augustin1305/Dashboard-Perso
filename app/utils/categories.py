"""Catégories de lieux et échelle de ressenti du carnet Rep'r."""
from __future__ import annotations

CATEGORIES = [
    "Restaurant",
    "Café",
    "Bar",
    "Bar à vin",
    "Cinéma",
    "Théâtre",
    "Musée",
    "Hôtel",
    "Parc",
    "Boutique",
    "Autre lieu",
]

CATEGORY_ICONS = {
    "Restaurant": "🍽️",
    "Café": "☕",
    "Bar": "🍸",
    "Bar à vin": "🍷",
    "Cinéma": "🎬",
    "Théâtre": "🎭",
    "Musée": "🖼️",
    "Hôtel": "🛏️",
    "Parc": "🌳",
    "Boutique": "🛍️",
    "Autre lieu": "📍",
}

# Échelle de ressenti (uniquement pour les rep'rs "Vécu") : ordre et couleurs
# repris de la charte Rep'r.
RESSENTIS = [
    {"id": "coeur", "label": "Coup de cœur", "color": "#E4572E"},
    {"id": "tb", "label": "Très bien", "color": "#F2A541"},
    {"id": "ok", "label": "Correct", "color": "#8FB9A8"},
    {"id": "bof", "label": "Bof", "color": "#9AA5B1"},
    {"id": "ev", "label": "À éviter", "color": "#5B5F66"},
]
RESSENTI_IDS = [r["id"] for r in RESSENTIS]
RESSENTI_BY_ID = {r["id"]: r for r in RESSENTIS}

# Un st.pills ne peut pas être coloré nativement : on approxime la teinte de
# chaque ressenti avec un émoji, pour garder un repère visuel dans le picker.
RESSENTI_EMOJI = {
    "coeur": "🧡",
    "tb": "🟡",
    "ok": "🟢",
    "bof": "⚪",
    "ev": "⚫",
}


def icon_for(categorie: str) -> str:
    return CATEGORY_ICONS.get(categorie, "📍")


def ressenti_label(ressenti_id: str | None) -> str:
    if not ressenti_id:
        return ""
    return RESSENTI_BY_ID.get(ressenti_id, {}).get("label", "")


def ressenti_color(ressenti_id: str | None) -> str:
    if not ressenti_id:
        return "#9AA5B1"
    return RESSENTI_BY_ID.get(ressenti_id, {}).get("color", "#9AA5B1")


def ressenti_pill_label(ressenti_id: str) -> str:
    return f"{RESSENTI_EMOJI.get(ressenti_id, '')} {ressenti_label(ressenti_id)}".strip()
