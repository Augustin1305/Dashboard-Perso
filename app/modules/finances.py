"""Module Finances : dépenses par catégorie, évolution mensuelle."""
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from app.utils import ai_extract
from app.utils.categorize import NON_CATEGORISE, build_category_colors, categorize_dataframe
from app.utils.parsers import parse_all_releves
from app.utils.viz import FLOW_COLORS, apply_layout_defaults

BANQUE_FOLDER = "data/banque"
RULES_PATH = "config/category_rules.yaml"

MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def _format_period_fr(period: pd.Period) -> str:
    return f"{MOIS_FR[period.month - 1]} {period.year}"


def _fmt_eur(value: float) -> str:
    return f"{value:,.2f} €".replace(",", " ")


def _save_extracted_transactions(extracted: pd.DataFrame, original_filename: str) -> str:
    """Écrit les transactions extraites dans un CSV standard sous data/banque/."""
    os.makedirs(BANQUE_FOLDER, exist_ok=True)
    stem = os.path.splitext(os.path.basename(original_filename))[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    out_path = os.path.join(BANQUE_FOLDER, f"import_agent_{stem}_{timestamp}.csv")

    out = extracted.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out[["date", "libelle", "montant"]].to_csv(out_path, index=False)
    return out_path


def _duplicate_mask(extracted: pd.DataFrame, existing_df: pd.DataFrame) -> pd.Series:
    """Transactions de `extracted` déjà présentes à l'identique (date + libellé + montant)
    dans `existing_df` (les données déjà enregistrées sous data/banque/)."""
    if existing_df.empty:
        return pd.Series(False, index=extracted.index)

    existing_keys = set(
        zip(existing_df["date"].dt.date, existing_df["libelle"], existing_df["montant"].round(2))
    )
    return extracted.apply(
        lambda r: (r["date"].date(), r["libelle"], round(r["montant"], 2)) in existing_keys,
        axis=1,
    )


def _render_import_agent():
    with st.expander("🤖 Importer un relevé via l'agent (CSV ou PDF)", expanded=False):
        st.caption(
            "Dépose un relevé dans un format quelconque : un agent (API OpenAI) lit le "
            "fichier et en extrait les transactions automatiquement. Le contenu du "
            "fichier est envoyé à l'API OpenAI le temps de l'extraction."
        )

        if not ai_extract.is_configured():
            st.warning(
                "Clé API OpenAI manquante. Définis la variable d'environnement "
                "`OPENAI_API_KEY` avant de lancer l'app pour activer cette fonctionnalité."
            )
            return

        # Clé dynamique : après un enregistrement, on l'incrémente pour forcer la
        # réinitialisation du widget. Sans ça, Streamlit garde le fichier chargé après
        # un st.rerun(), qui se retrouve alors re-traité et signalé comme "déjà importé"
        # — alors qu'il vient tout juste d'être enregistré lui-même.
        uploader_version = st.session_state.get("_banque_uploader_version", 0)
        uploaded = st.file_uploader(
            "Relevé bancaire", type=["csv", "pdf"], key=f"banque_uploader_{uploader_version}"
        )

        if uploaded is not None:
            file_key = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.get("_import_key") != file_key:
                with st.spinner("L'agent lit le relevé…"):
                    try:
                        extracted = ai_extract.extract_transactions(uploaded.getvalue(), uploaded.name)
                        st.session_state["_import_key"] = file_key
                        st.session_state["_import_name"] = uploaded.name
                        st.session_state["_import_df"] = extracted
                        st.session_state["_import_error"] = None
                    except ai_extract.ApiKeyMissingError as exc:
                        st.session_state["_import_error"] = str(exc)
                        st.session_state["_import_df"] = None
                    except Exception as exc:  # erreurs API OpenAI, PDF illisible, etc.
                        st.session_state["_import_error"] = f"Échec de l'extraction : {exc}"
                        st.session_state["_import_df"] = None

            if st.session_state.get("_import_error"):
                st.error(st.session_state["_import_error"])
            elif st.session_state.get("_import_df") is not None:
                extracted = st.session_state["_import_df"]
                if extracted.empty:
                    st.warning("Aucune transaction détectée dans ce fichier.")
                else:
                    preview = categorize_dataframe(extracted, RULES_PATH)
                    st.success(f"{len(preview)} transaction(s) extraite(s) et regroupée(s) par catégorie.")
                    st.dataframe(
                        preview.sort_values("date", ascending=False),
                        hide_index=True,
                        width="stretch",
                    )
                    resume = preview.groupby("categorie")["montant"].sum().sort_values()
                    st.bar_chart(resume)

                    # Détecte les transactions déjà présentes à l'identique (date + libellé +
                    # montant) — pas au niveau du mois entier : deux relevés consécutifs
                    # couvrent chacun un bout de deux mois calendaires sans se chevaucher
                    # réellement (ex. relevé de mai : 27/04-26/05 ; juin : 27/05-26/06), donc
                    # bloquer tout un mois dès qu'il contient une seule transaction créerait
                    # de faux blocages.
                    existing_df = parse_all_releves(BANQUE_FOLDER)
                    dup_mask = _duplicate_mask(extracted, existing_df)
                    n_dup = int(dup_mask.sum())
                    a_enregistrer = extracted[~dup_mask]

                    if n_dup and a_enregistrer.empty:
                        st.error(
                            f"⛔ Import bloqué : les {n_dup} transaction(s) de ce fichier sont "
                            f"déjà présentes dans `{BANQUE_FOLDER}/` (import en double)."
                        )
                    else:
                        if n_dup:
                            st.info(
                                f"ℹ️ {n_dup} transaction(s) déjà présente(s) seront ignorée(s) — "
                                f"seules les {len(a_enregistrer)} nouvelle(s) seront enregistrées."
                            )
                        if st.button("✅ Enregistrer ces transactions", type="primary"):
                            out_path = _save_extracted_transactions(
                                a_enregistrer, st.session_state["_import_name"]
                            )
                            st.session_state["_import_key"] = None
                            st.session_state["_import_df"] = None
                            st.session_state["_banque_uploader_version"] = uploader_version + 1
                            st.success(f"Transactions enregistrées dans `{out_path}`.")
                            st.rerun()


def _render_categorie_section(
    periode_df: pd.DataFrame, mask, titre: str, label: str, color_map: dict, key_prefix: str
):
    """Graphique + détail par catégorie, réutilisé pour les dépenses et les entrées."""
    flux_cat = periode_df[mask].copy()
    flux_cat["montant_abs"] = flux_cat["montant"].abs()
    par_categorie = (
        flux_cat.groupby("categorie")["montant_abs"]
        .agg(montant="sum", transactions="count")
        .sort_values("montant", ascending=False)
        .reset_index()
    )
    total = par_categorie["montant"].sum()
    par_categorie["part"] = (par_categorie["montant"] / total * 100) if total else 0

    st.subheader(f"{titre} — {label}")
    if par_categorie.empty:
        st.info("Aucune transaction sur cette période.")
        return

    par_categorie["label"] = par_categorie.apply(
        lambda r: f"{_fmt_eur(r['montant'])} · {r['part']:.0f} %", axis=1
    )
    fig = px.bar(
        par_categorie,
        x="montant",
        y="categorie",
        orientation="h",
        color="categorie",
        color_discrete_map=color_map,
        text="label",
        labels={"montant": "Montant (€)", "categorie": ""},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
    apply_layout_defaults(fig)
    st.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

    st.subheader("Détail des transactions par catégorie")
    categorie_choisie = st.selectbox(
        "Catégorie",
        par_categorie["categorie"].tolist(),
        format_func=lambda c: f"{c} ({_fmt_eur(par_categorie.loc[par_categorie['categorie'] == c, 'montant'].iloc[0])})",
        key=f"{key_prefix}_categorie_select",
    )
    detail = flux_cat[flux_cat["categorie"] == categorie_choisie][
        ["date", "libelle", "montant", "source_fichier"]
    ].sort_values("date", ascending=False)
    st.dataframe(detail, hide_index=True, width="stretch", key=f"{key_prefix}_detail_table")


def render():
    st.header("💶 Finances")

    _render_import_agent()

    df = parse_all_releves(BANQUE_FOLDER)
    if df.empty:
        st.info(
            "Aucun relevé trouvé. Dépose un ou plusieurs CSV de relevé bancaire "
            f"dans `{BANQUE_FOLDER}/`, ou utilise l'import via agent ci-dessus."
        )
        return

    df = categorize_dataframe(df, RULES_PATH)
    df["mois"] = df["date"].dt.to_period("M")
    color_map = build_category_colors(RULES_PATH)

    # --- Sélecteur de période : par mois ou par année, peu importe l'ordre d'import ---
    mois_disponibles = sorted(df["mois"].unique())  # chronologique, indépendant de l'ordre d'import
    annees_disponibles = sorted({m.year for m in mois_disponibles}, reverse=True)

    st.subheader("📆 Période")
    col_vue, col_choix = st.columns([1, 2])
    vue = col_vue.radio("Vue", ["Mois", "Année"], horizontal=True, label_visibility="collapsed")

    if vue == "Mois":
        mois_tries = sorted(mois_disponibles, reverse=True)
        idx = col_choix.selectbox(
            "Choisir un mois",
            range(len(mois_tries)),
            format_func=lambda i: _format_period_fr(mois_tries[i]),
            label_visibility="collapsed",
        )
        periode = mois_tries[idx]
        periode_df = df[df["mois"] == periode]
        label = _format_period_fr(periode)

        idx_chrono = mois_disponibles.index(periode)
        precedent = mois_disponibles[idx_chrono - 1] if idx_chrono > 0 else None
        precedent_df = df[df["mois"] == precedent] if precedent is not None else None
    else:
        annee = col_choix.selectbox("Choisir une année", annees_disponibles, label_visibility="collapsed")
        periode = annee
        periode_df = df[df["date"].dt.year == annee]
        label = str(annee)
        precedent_df = None

    st.divider()

    # --- Métriques clés : dépenses, entrées, solde, moyenne / à catégoriser ---
    depenses_mask = periode_df["montant"] < 0
    depenses_periode = periode_df.loc[depenses_mask, "montant"].abs().sum()
    entrees_periode = periode_df.loc[~depenses_mask, "montant"].sum()
    solde_periode = entrees_periode - depenses_periode
    # Seules les dépenses non reconnues sont actionnables (les entrées, ex. salaire,
    # ne matchent pas les mots-clés de dépenses et ne comptent pas comme "à corriger").
    n_non_cat = (periode_df.loc[depenses_mask, "categorie"] == NON_CATEGORISE).sum()

    col1, col2, col3, col4 = st.columns(4)
    if precedent_df is not None:
        depenses_precedent = precedent_df.loc[precedent_df["montant"] < 0, "montant"].abs().sum()
        col1.metric(
            f"Dépenses — {label}",
            _fmt_eur(depenses_periode),
            delta=_fmt_eur(depenses_periode - depenses_precedent),
            delta_color="inverse",
            help=f"Comparé à {_format_period_fr(precedent_df['mois'].iloc[0])}",
        )
    else:
        col1.metric(f"Dépenses — {label}", _fmt_eur(depenses_periode))

    col2.metric(f"Entrées — {label}", _fmt_eur(entrees_periode))
    col3.metric("Solde", _fmt_eur(solde_periode))

    if vue == "Année":
        nb_mois = periode_df["mois"].nunique()
        moyenne_mensuelle = depenses_periode / nb_mois if nb_mois else 0
        col4.metric("Dépense moyenne / mois", _fmt_eur(moyenne_mensuelle))
    else:
        col4.metric("À catégoriser", n_non_cat)

    st.divider()

    _render_categorie_section(periode_df, periode_df["montant"] < 0, "Répartition des dépenses", label, color_map, "dep")

    st.divider()

    _render_categorie_section(periode_df, periode_df["montant"] > 0, "Répartition des entrées", label, color_map, "ent")

    st.divider()

    # --- Évolution dans le temps : toujours triée chronologiquement, quel que soit
    # l'ordre dans lequel les relevés ont été importés (mai 2026 puis mars 2025, etc.) ---
    st.subheader("Évolution — dépenses vs entrées")
    flux = df.copy()
    flux["flux"] = flux["montant"].apply(lambda m: "Dépenses" if m < 0 else "Entrées")
    flux["montant_abs"] = flux["montant"].abs()
    evolution = flux.groupby(["mois", "flux"])["montant_abs"].sum().reset_index()
    evolution["mois_str"] = evolution["mois"].apply(_format_period_fr)
    ordre_mois = [_format_period_fr(m) for m in mois_disponibles]

    fig2 = px.line(
        evolution,
        x="mois_str",
        y="montant_abs",
        color="flux",
        markers=True,
        category_orders={"mois_str": ordre_mois},
        color_discrete_map=FLOW_COLORS,
        labels={"mois_str": "", "montant_abs": "Montant (€)", "flux": ""},
    )
    fig2.update_traces(line=dict(width=2))
    apply_layout_defaults(fig2)
    st.plotly_chart(fig2, width="stretch")

    st.divider()

    st.subheader(f"⚠️ Dépenses non catégorisées — {label}")
    non_categorisees = periode_df[(depenses_mask) & (periode_df["categorie"] == NON_CATEGORISE)][
        ["date", "libelle", "montant", "source_fichier"]
    ].sort_values("date", ascending=False)

    if non_categorisees.empty:
        st.success("Toutes les dépenses de cette période sont catégorisées ✅")
    else:
        st.dataframe(non_categorisees, hide_index=True, width="stretch")
        st.caption(
            f"{len(non_categorisees)} dépense(s) non reconnue(s). "
            f"Ajoute des mots-clés dans `{RULES_PATH}` pour les catégoriser automatiquement."
        )
