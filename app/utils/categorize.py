"""Logique de catégorisation automatique des dépenses par mots-clés."""
from __future__ import annotations

import os

import pandas as pd
import yaml

from app.utils.viz import CATEGORICAL, FLOW_COLORS, NEUTRAL_UNCATEGORIZED

NON_CATEGORISE = "Non catégorisé"
# Virement reçu générique (tiers ou WERO) sans règle plus spécifique (Salaire,
# Reprise épargne...) qui ait matché avant — cf. category_rules.yaml.
VIREMENT_RECU = "Remboursements"
VIREMENT_ENVOYE = "Virement envoyé"

# Libellés génériques de virement (ni un vrai commerce, ni une vraie catégorie de
# dépense) : reconnus séparément des règles métier, puis distingués par le signe
# du montant pour ne jamais mélanger l'argent qui rentre et celui qui sort.
_TRANSFER_KEYWORDS = [
    "vir instantane emis",
    "vir europeen emis",
    "vir inst re",
    "vir recu",
    "virement recu",
    "virement emis",
]


def load_rules(path: str) -> dict[str, list[str]]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f) or {}
    return {category: [kw.lower() for kw in keywords] for category, keywords in rules.items()}


def categorize_label(libelle: str, rules: dict[str, list[str]]) -> str:
    if not isinstance(libelle, str) or not libelle:
        return NON_CATEGORISE

    label_lower = libelle.lower()
    for category, keywords in rules.items():
        if any(keyword in label_lower for keyword in keywords):
            return category
    return NON_CATEGORISE


def categorize_dataframe(df: pd.DataFrame, rules_path: str) -> pd.DataFrame:
    """Complète la colonne 'categorie' : garde la valeur existante si présente,
    sinon applique les règles de mots-clés, sinon détecte un virement générique
    (classé par signe du montant), sinon 'Non catégorisé'.
    """
    rules = load_rules(rules_path)
    df = df.copy()

    def resolve(row):
        existing = row.get("categorie")
        if isinstance(existing, str) and existing.strip():
            return existing

        libelle = row.get("libelle", "")
        category = categorize_label(libelle, rules)
        if category != NON_CATEGORISE:
            return category

        label_lower = libelle.lower() if isinstance(libelle, str) else ""
        montant = row.get("montant")
        if pd.notna(montant) and any(kw in label_lower for kw in _TRANSFER_KEYWORDS):
            return VIREMENT_RECU if montant > 0 else VIREMENT_ENVOYE

        return NON_CATEGORISE

    df["categorie"] = df.apply(resolve, axis=1)
    return df


def build_category_colors(rules_path: str) -> dict[str, str]:
    """Associe une couleur fixe à chaque catégorie, dans l'ordre du fichier de
    règles (jamais réordonné selon les données affichées), + une couleur neutre
    dédiée pour 'Non catégorisé'. Garantit que la couleur d'une catégorie ne
    change jamais selon le mois/l'année sélectionné.
    """
    rules = load_rules(rules_path)
    colors = {category: CATEGORICAL[i % len(CATEGORICAL)] for i, category in enumerate(rules.keys())}
    colors[NON_CATEGORISE] = NEUTRAL_UNCATEGORIZED
    colors[VIREMENT_RECU] = FLOW_COLORS["Entrées"]
    colors[VIREMENT_ENVOYE] = FLOW_COLORS["Dépenses"]
    return colors
