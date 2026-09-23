"""Accès aux données du carnet Découvertes (Supabase/Postgres) et au partage
d'une fiche entre utilisateurs. Remplace l'ancien stockage CSV."""
from __future__ import annotations

import pandas as pd

from app.utils.auth import get_client

DISCOVERY_COLUMNS = [
    "id",
    "date",
    "categorie",
    "titre",
    "adresse",
    "lat",
    "lon",
    "vecu",
    "ressenti",
    "commentaire",
]


def _clean(fields: dict) -> dict:
    """Remplace les chaînes vides par None : les colonnes numériques
    nullable (note, lat, lon) côté Postgres n'acceptent pas `""`."""
    return {key: (None if value == "" else value) for key, value in fields.items()}


def fetch_discoveries(user_id: str) -> pd.DataFrame:
    response = get_client().table("discoveries").select("*").eq("user_id", user_id).execute()
    if not response.data:
        return pd.DataFrame(columns=DISCOVERY_COLUMNS)

    df = pd.DataFrame(response.data)
    for col in DISCOVERY_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["vecu"] = df["vecu"].astype(bool)
    return df[DISCOVERY_COLUMNS]


def insert_discovery(user_id: str, entry: dict) -> None:
    payload = _clean({**entry, "user_id": user_id})
    payload.pop("id", None)  # généré par Postgres
    get_client().table("discoveries").insert(payload).execute()


def update_discovery(user_id: str, entry_id: str, fields: dict) -> None:
    get_client().table("discoveries").update(_clean(fields)).eq("id", entry_id).eq(
        "user_id", user_id
    ).execute()


def delete_discovery(user_id: str, entry_id: str) -> None:
    get_client().table("discoveries").delete().eq("id", entry_id).eq("user_id", user_id).execute()


def share_discovery(from_user: dict, to_email: str, entry: dict) -> None:
    """Envoie une fiche à un autre utilisateur, qui doit déjà avoir un compte.

    Lève une ValueError avec un message prêt à afficher tel quel si l'email
    ne correspond à aucun compte.
    """
    to_email = to_email.strip().lower()
    if not to_email:
        raise ValueError("Indique l'email de la personne à qui envoyer cette fiche.")

    client = get_client()
    result = client.rpc("find_user_id_by_email", {"lookup_email": to_email}).execute()
    to_user_id = result.data
    if not to_user_id:
        raise ValueError(f"Aucun compte trouvé pour {to_email} — elle doit d'abord s'inscrire sur l'app.")

    def _or_none(value):
        return value if pd.notna(value) else None

    snapshot = {
        "categorie": entry.get("categorie"),
        "titre": entry.get("titre"),
        "adresse": entry.get("adresse"),
        "lat": _or_none(entry.get("lat")),
        "lon": _or_none(entry.get("lon")),
        "vecu": bool(entry.get("vecu")),
        "ressenti": entry.get("ressenti") or None,
        "commentaire": entry.get("commentaire"),
    }
    client.table("shares").insert(
        {
            "from_user_id": from_user["id"],
            "from_email": from_user["email"],
            "to_user_id": to_user_id,
            "snapshot": snapshot,
        }
    ).execute()


def fetch_inbox(user_id: str) -> list[dict]:
    response = (
        get_client()
        .table("shares")
        .select("*")
        .eq("to_user_id", user_id)
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def respond_to_share(share_id: str, accept: bool, user_id: str, from_email: str, snapshot: dict) -> None:
    client = get_client()
    if accept:
        commentaire = f"Recommandé par {from_email}"
        if snapshot.get("commentaire"):
            commentaire += f" : {snapshot['commentaire']}"
        insert_discovery(
            user_id,
            {
                "date": pd.Timestamp.today().date().isoformat(),
                "categorie": snapshot.get("categorie") or "Autre lieu",
                "titre": snapshot.get("titre") or "Sans titre",
                "adresse": snapshot.get("adresse") or "",
                "lat": snapshot.get("lat"),
                "lon": snapshot.get("lon"),
                "vecu": False,
                "ressenti": "",
                "commentaire": commentaire,
            },
        )

    status = "accepted" if accept else "dismissed"
    client.table("shares").update({"status": status}).eq("id", share_id).execute()
