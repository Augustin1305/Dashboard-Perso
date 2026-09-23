"""Catégories communes au carnet de découvertes (lieux physiques et médias)."""
from __future__ import annotations

PLACE_CATEGORIES = [
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

MEDIA_CATEGORIES = ["Livre", "Film"]

ALL_CATEGORIES = PLACE_CATEGORIES + MEDIA_CATEGORIES

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
    "Livre": "📖",
    "Film": "🎞️",
}

# Couleurs d'accent par catégorie, réutilisées à l'écran et dans les fiches partagées.
CATEGORY_COLORS = {
    "Restaurant": "#E76F51",
    "Café": "#B08968",
    "Bar": "#9D4EDD",
    "Bar à vin": "#6A040F",
    "Cinéma": "#264653",
    "Théâtre": "#7B2CBF",
    "Musée": "#457B9D",
    "Hôtel": "#2A9D8F",
    "Parc": "#588157",
    "Boutique": "#E9C46A",
    "Autre lieu": "#495057",
    "Livre": "#3A5A40",
    "Film": "#1D3557",
}

STATUTS = ["à découvrir", "en cours", "fait"]


def is_place(categorie: str) -> bool:
    return categorie in PLACE_CATEGORIES


def icon_for(categorie: str) -> str:
    return CATEGORY_ICONS.get(categorie, "📍")


def color_for(categorie: str) -> str:
    return CATEGORY_COLORS.get(categorie, "#495057")
