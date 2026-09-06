"""Parsers pour les différentes sources de données du dashboard."""
from __future__ import annotations

import glob
import os
import re
import uuid

import pandas as pd
from dateutil import parser as dateparser
from icalendar import Calendar


# ---------------------------------------------------------------------------
# Strava
# ---------------------------------------------------------------------------

def parse_strava(path: str) -> pd.DataFrame:
    """Parse un export Strava (bulk export) et retourne un DataFrame standardisé.

    Colonnes en sortie : date, type, distance_km, duree_min, denivele_m,
    fc_moyenne, effort_relatif
    """
    if not os.path.exists(path):
        return _empty_strava_df()

    df = pd.read_csv(path)
    if df.empty:
        return _empty_strava_df()

    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df.get("Activity Date"), errors="coerce", format="mixed")
    out["type"] = df.get("Activity Type")
    out["distance_km"] = pd.to_numeric(df.get("Distance"), errors="coerce")
    out["duree_min"] = df.get("Moving Time").apply(_duration_to_minutes) if "Moving Time" in df else None
    out["denivele_m"] = pd.to_numeric(df.get("Elevation Gain"), errors="coerce")
    out["fc_moyenne"] = pd.to_numeric(df.get("Average Heart Rate"), errors="coerce")
    out["effort_relatif"] = pd.to_numeric(df.get("Relative Effort"), errors="coerce")

    out = out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return out


def _duration_to_minutes(value) -> float | None:
    if pd.isna(value):
        return None
    try:
        parts = str(value).split(":")
        parts = [int(p) for p in parts]
        if len(parts) == 3:
            h, m, s = parts
            return h * 60 + m + s / 60
        if len(parts) == 2:
            m, s = parts
            return m + s / 60
    except (ValueError, TypeError):
        return None
    return None


def _empty_strava_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["date", "type", "distance_km", "duree_min", "denivele_m", "fc_moyenne", "effort_relatif"]
    )


# ---------------------------------------------------------------------------
# Relevés bancaires
# ---------------------------------------------------------------------------

# Mapping configurable : nom de colonne standard -> liste des noms possibles
# dans les exports bruts de banques différentes.
COLUMN_MAPPING = {
    "date": ["date", "Date", "DATE"],
    "libelle": ["Libelle", "libelle", "Libellé", "libellé", "Description", "Label"],
    "montant": ["Montant", "montant", "Amount", "amount"],
    "categorie": ["Categorie", "categorie", "Catégorie", "catégorie", "Category"],
}


def _find_column(columns: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def parse_releve_bancaire(path: str) -> pd.DataFrame:
    """Parse un relevé bancaire CSV brut et le convertit au schéma standard.

    Schéma en sortie : date, libelle, montant, categorie (optionnelle, vide si absente)
    """
    # Detection auto du séparateur (virgule ou point-virgule)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        first_line = f.readline()
    sep = ";" if first_line.count(";") >= first_line.count(",") else ","

    df = pd.read_csv(path, sep=sep)
    columns = list(df.columns)

    col_date = _find_column(columns, COLUMN_MAPPING["date"])
    col_libelle = _find_column(columns, COLUMN_MAPPING["libelle"])
    col_montant = _find_column(columns, COLUMN_MAPPING["montant"])
    col_categorie = _find_column(columns, COLUMN_MAPPING["categorie"])

    out = pd.DataFrame()
    out["date"] = df[col_date].apply(_safe_parse_date) if col_date else pd.NaT
    out["libelle"] = df[col_libelle] if col_libelle else ""
    out["montant"] = (
        pd.to_numeric(
            df[col_montant].astype(str).str.replace(",", ".", regex=False).str.replace(" ", "", regex=False),
            errors="coerce",
        )
        if col_montant
        else 0.0
    )
    out["categorie"] = df[col_categorie] if col_categorie else ""

    out = out.dropna(subset=["date"]).reset_index(drop=True)
    return out


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}")


def _safe_parse_date(value):
    text = str(value).strip()
    try:
        if _ISO_DATE_RE.match(text):
            # Format ISO (YYYY-MM-DD), ex. produit par l'agent d'extraction : non-ambigu,
            # à ne PAS passer à dayfirst=True qui inverserait jour/mois (dateutil #1053).
            return pd.Timestamp(text)
        # Format français probable (DD/MM/YYYY) : jour en premier en cas d'ambiguïté.
        return dateparser.parse(text, dayfirst=True)
    except (ValueError, TypeError):
        return pd.NaT


def parse_all_releves(folder: str) -> pd.DataFrame:
    """Parse tous les CSV présents dans le dossier banque et les concatène."""
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        return pd.DataFrame(columns=["date", "libelle", "montant", "categorie", "source_fichier"])

    frames = []
    for f in files:
        try:
            df = parse_releve_bancaire(f)
            df["source_fichier"] = os.path.basename(f)
            frames.append(df)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame(columns=["date", "libelle", "montant", "categorie", "source_fichier"])

    return pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Calendrier (.ics)
# ---------------------------------------------------------------------------

def parse_ics(path: str) -> pd.DataFrame:
    """Parse un fichier .ics et retourne un DataFrame des événements.

    Colonnes : titre, debut, fin, lieu
    """
    if not os.path.exists(path):
        return _empty_ics_df()

    with open(path, "rb") as f:
        cal = Calendar.from_ical(f.read())

    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        summary = str(component.get("summary", ""))
        location = str(component.get("location", "") or "")
        dtstart = component.get("dtstart")
        dtend = component.get("dtend")

        debut = dtstart.dt if dtstart else None
        fin = dtend.dt if dtend else None

        events.append({"titre": summary, "debut": debut, "fin": fin, "lieu": location})

    if not events:
        return _empty_ics_df()

    df = pd.DataFrame(events)
    df["debut"] = pd.to_datetime(df["debut"], utc=True, errors="coerce").dt.tz_localize(None)
    df["fin"] = pd.to_datetime(df["fin"], utc=True, errors="coerce").dt.tz_localize(None)
    df = df.dropna(subset=["debut"]).sort_values("debut").reset_index(drop=True)
    return df


def _empty_ics_df() -> pd.DataFrame:
    return pd.DataFrame(columns=["titre", "debut", "fin", "lieu"])


# ---------------------------------------------------------------------------
# Media log
# ---------------------------------------------------------------------------

MEDIA_COLUMNS = ["id", "date", "type", "titre", "statut", "note", "commentaire"]


def parse_media_log(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=MEDIA_COLUMNS)

    df = pd.read_csv(path)
    for col in MEDIA_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Backfill des identifiants stables pour les entrées créées avant l'ajout
    # de l'édition (nécessaire pour pouvoir modifier une ligne de façon fiable).
    missing_id = df["id"].isna() | (df["id"].astype(str).str.strip() == "")
    if missing_id.any():
        df.loc[missing_id, "id"] = [uuid.uuid4().hex[:8] for _ in range(int(missing_id.sum()))]
        write_media_log(path, df[MEDIA_COLUMNS])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["note"] = pd.to_numeric(df["note"], errors="coerce")
    return df[MEDIA_COLUMNS]


def write_media_log(path: str, df: pd.DataFrame) -> None:
    """Réécrit le fichier media_log en entier (utilisé après une modification)."""
    df = df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df[MEDIA_COLUMNS].to_csv(path, index=False)


def append_media_entry(path: str, entry: dict) -> None:
    """Ajoute une ligne au CSV media_log, en créant le fichier si besoin."""
    entry = {**entry}
    entry.setdefault("id", uuid.uuid4().hex[:8])
    row = pd.DataFrame([entry], columns=MEDIA_COLUMNS)
    file_exists = os.path.exists(path)
    row.to_csv(path, mode="a", header=not file_exists, index=False)


def update_media_entry(path: str, entry_id: str, updated_fields: dict) -> None:
    """Met à jour les champs d'une entrée existante (identifiée par son id).

    Reconstruit la ligne plutôt que d'assigner en place : une colonne comme
    "note" est de dtype float64 (à cause des lignes sans note), et y écrire une
    chaîne vide via .loc lève un TypeError qui fait échouer toute la sauvegarde.
    """
    df = parse_media_log(path)
    mask = df["id"] == entry_id
    if not mask.any():
        return

    idx = df.index[mask][0]
    row = df.loc[idx].to_dict()
    row.update(updated_fields)
    row["id"] = entry_id

    df = df.drop(index=idx)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_media_log(path, df)
