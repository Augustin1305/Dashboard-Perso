"""Extraction de transactions bancaires via l'API OpenAI.

Permet de lire un relevé bancaire dans un format quelconque (CSV brut, PDF)
et d'en extraire une liste de transactions structurées, pour les cas où le
mapping de colonnes fixe de `parsers.py` ne suffit pas (formats inconnus,
relevés PDF).

Nécessite une clé API OpenAI dans la variable d'environnement
`OPENAI_API_KEY`. Le contenu du relevé est envoyé à l'API OpenAI pour
l'extraction : à utiliser en connaissance de cause pour des données
bancaires.
"""
from __future__ import annotations

import base64
import json
import os

import pandas as pd
from openai import OpenAI

MODEL = "gpt-5.6-terra"

TRANSACTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date de l'opération au format ISO 8601 (YYYY-MM-DD).",
                    },
                    "libelle": {
                        "type": "string",
                        "description": "Libellé / description de l'opération, tel qu'il apparaît sur le relevé.",
                    },
                    "montant": {
                        "type": "number",
                        "description": (
                            "Montant signé de l'opération : négatif pour un débit/une dépense, "
                            "positif pour un crédit."
                        ),
                    },
                },
                "required": ["date", "libelle", "montant"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["transactions"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "Tu extrais les transactions d'un relevé bancaire personnel. "
    "Le document a généralement deux colonnes de montant : Débit (dépense, à extraire en "
    "négatif) et Crédit (entrée d'argent, à extraire en positif) — identifie bien dans quelle "
    "colonne se trouve chaque montant avant de choisir son signe ; ne te fie pas seulement au "
    "libellé de l'opération, qui peut être ambigu (ex. un 'VRST' ou 'VERSEMENT' est un dépôt "
    "donc un crédit positif, même si le mot ressemble à un retrait). "
    "Ignore les en-têtes, totaux, soldes et lignes de pagination — mais si le document affiche "
    "un total des mouvements (ex. 'TOTAUX DES MOUVEMENTS : Débit X / Crédit Y'), utilise-le "
    "pour t'auto-vérifier : la somme de tes montants négatifs doit correspondre au total Débit, "
    "et la somme de tes montants positifs au total Crédit ; corrige le signe d'une transaction "
    "douteuse si besoin pour que ça corresponde avant de répondre. "
    "N'invente aucune transaction et ne modifie pas les valeurs des montants (seul le signe "
    "peut nécessiter une correction pour matcher la bonne colonne)."
)


class ApiKeyMissingError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def extract_transactions(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Extrait les transactions d'un relevé (CSV ou PDF) via l'API OpenAI.

    Retourne un DataFrame avec les colonnes : date, libelle, montant.
    """
    if not is_configured():
        raise ApiKeyMissingError(
            "Aucune clé API OpenAI trouvée (variable d'environnement OPENAI_API_KEY)."
        )

    client = OpenAI()
    is_pdf = filename.lower().endswith(".pdf")

    if is_pdf:
        b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
        content = [
            {
                "type": "input_file",
                "filename": filename,
                "file_data": f"data:application/pdf;base64,{b64}",
            },
            {"type": "input_text", "text": "Extrais toutes les transactions de ce relevé bancaire."},
        ]
    else:
        raw_text = file_bytes.decode("utf-8", errors="replace")
        content = [
            {
                "type": "input_text",
                "text": (
                    "Voici le contenu brut d'un fichier de relevé bancaire "
                    f"(nom du fichier : {filename}) :\n\n{raw_text}\n\n"
                    "Extrais toutes les transactions de ce relevé."
                ),
            }
        ]

    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "bank_transactions",
                "strict": True,
                "schema": TRANSACTIONS_SCHEMA,
            }
        },
    )

    message = next((item for item in response.output if item.type == "message"), None)
    if message is None or not message.content:
        return pd.DataFrame(columns=["date", "libelle", "montant"])

    block = message.content[0]
    if getattr(block, "type", None) == "refusal":
        raise RuntimeError(f"Le modèle a refusé la demande : {block.refusal}")

    parsed = json.loads(block.text)
    transactions = parsed.get("transactions", [])
    df = pd.DataFrame(transactions, columns=["date", "libelle", "montant"])
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce")
    df = df.dropna(subset=["date"]).reset_index(drop=True)
    return df
