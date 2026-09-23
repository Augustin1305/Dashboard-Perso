"""Recherche d'adresses à partir d'un nom, via l'API Nominatim (OpenStreetMap).

Gratuit, sans clé API. Respecte la politique d'usage de Nominatim
(https://operations.osmfoundation.org/policies/nominatim/) via un User-Agent
identifiable — approprié pour cet usage personnel ponctuel (pas de gros volume).
"""
from __future__ import annotations

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "DashboardPerso/1.0 (usage personnel ; contact: augustinpaget13@gmail.com)"
TIMEOUT_SECONDS = 6


def search_places(query: str, limit: int = 5) -> list[dict]:
    """Cherche des lieux correspondant à `query` (nom, adresse partielle, ville...).

    Retourne une liste de dicts {"label", "adresse", "lat", "lon"}, ou une liste
    vide en cas d'absence de résultat ou d'échec réseau — on ne bloque jamais
    l'ajout manuel d'une entrée à cause d'un souci de connexion.
    """
    query = query.strip()
    if not query:
        return []

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "jsonv2", "addressdetails": 1, "limit": limit},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        return []

    places = []
    for r in results:
        try:
            lat, lon = float(r["lat"]), float(r["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        display_name = r.get("display_name", query)
        places.append({"label": display_name, "adresse": display_name, "lat": lat, "lon": lon})
    return places
