"""Module Mes découvertes : carnet de lieux (restaurants, cafés, musées...) et de
médias (livres, films), avec recherche d'adresse automatique et fiches partageables.
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd
import streamlit as st

from app.utils import ai_chat, geocoding, share_card
from app.utils.categories import (
    ALL_CATEGORIES,
    MEDIA_CATEGORIES,
    PLACE_CATEGORIES,
    STATUTS,
    icon_for,
    is_place,
)
from app.utils.parsers import (
    append_discovery_entry,
    delete_discovery_entry,
    migrate_legacy_media_log,
    parse_discoveries,
    update_discovery_entry,
)

DISCOVERIES_PATH = "data/decouvertes.csv"
LEGACY_MEDIA_PATH = "data/media_log.csv"

_MANUAL_ADDRESS_OPTION = "✏️ Aucun ne correspond — je saisis l'adresse moi-même"


def _safe_filename(titre: str) -> str:
    return re.sub(r"[^\w\-. ]", "_", titre).strip() or "decouverte"


def _render_add_form(df: pd.DataFrame):
    with st.expander("➕ Ajouter une découverte", expanded=df.empty):
        col1, col2 = st.columns([3, 2])
        nom = col1.text_input(
            "Nom",
            key="disc_nom",
            placeholder="Ex: Le Comptoir du Relais, Dune, Le Fabuleux Destin d'Amélie Poulain…",
        )
        categorie = col2.selectbox(
            "Catégorie", ALL_CATEGORIES, key="disc_categorie", format_func=lambda c: f"{icon_for(c)} {c}"
        )

        adresse, lat, lon = "", None, None

        if is_place(categorie):
            st.caption("Cherche l'adresse automatiquement à partir du nom, ou saisis-la toi-même.")
            search_col, btn_col = st.columns([4, 1])
            if btn_col.button("🔍 Chercher l'adresse", disabled=not nom.strip(), key="disc_search_btn"):
                st.session_state["disc_results"] = geocoding.search_places(nom)
                st.session_state["disc_searched_for"] = nom

            results = st.session_state.get("disc_results", [])
            if results:
                options = [r["label"] for r in results] + [_MANUAL_ADDRESS_OPTION]
                choice = search_col.selectbox("Résultat trouvé", options, key="disc_choice")
                if choice != _MANUAL_ADDRESS_OPTION:
                    selected = next(r for r in results if r["label"] == choice)
                    adresse, lat, lon = selected["adresse"], selected["lat"], selected["lon"]
            elif st.session_state.get("disc_searched_for") == nom and nom.strip():
                search_col.caption("Aucun résultat — saisis l'adresse manuellement ci-dessous.")

            if not adresse:
                adresse = st.text_input("Adresse (optionnelle si non trouvée)", key="disc_adresse_manuelle")

        c1, c2, c3 = st.columns(3)
        entry_date = c1.date_input("Date", value=date.today(), key="disc_date")
        statut = c2.selectbox("Statut", STATUTS, index=0, key="disc_statut")
        note = c3.slider("Note (/5)", min_value=0, max_value=5, value=0, key="disc_note")
        commentaire = st.text_area("Commentaire", height=80, key="disc_commentaire")

        if st.button("Ajouter", type="primary", key="disc_submit"):
            if not nom.strip():
                st.error("Le nom est obligatoire.")
            else:
                append_discovery_entry(
                    DISCOVERIES_PATH,
                    {
                        "date": entry_date.isoformat(),
                        "categorie": categorie,
                        "titre": nom.strip(),
                        "adresse": adresse.strip() if isinstance(adresse, str) else "",
                        "lat": lat,
                        "lon": lon,
                        "statut": statut,
                        "note": note if note > 0 else "",
                        "commentaire": commentaire.strip(),
                    },
                )
                for key in [
                    "disc_nom",
                    "disc_results",
                    "disc_searched_for",
                    "disc_choice",
                    "disc_adresse_manuelle",
                    "disc_commentaire",
                    "disc_note",
                ]:
                    st.session_state.pop(key, None)
                st.success(f"« {nom} » ajouté !")
                st.rerun()


def _render_edit_section(df: pd.DataFrame):
    if df.empty:
        return

    with st.expander("✏️ Modifier une découverte", expanded=False):
        display_df = df.sort_values("date", ascending=False)
        options = display_df["id"].tolist()

        def _label(entry_id: str) -> str:
            row = df[df["id"] == entry_id].iloc[0]
            date_str = row["date"].strftime("%d/%m/%Y") if pd.notna(row["date"]) else "?"
            return f"{icon_for(row['categorie'])} {row['titre']} ({date_str})"

        selected_id = st.selectbox("Choisir une entrée", options, format_func=_label, key="edit_disc_select")
        row = df[df["id"] == selected_id].iloc[0]

        with st.form(f"edit_disc_form_{selected_id}"):
            c1, c2 = st.columns(2)
            edit_date = c1.date_input(
                "Date",
                value=row["date"].date() if pd.notna(row["date"]) else date.today(),
                key=f"edit_date_{selected_id}",
            )
            categorie_actuelle = row["categorie"] if row["categorie"] in ALL_CATEGORIES else ALL_CATEGORIES[0]
            edit_categorie = c2.selectbox(
                "Catégorie",
                ALL_CATEGORIES,
                index=ALL_CATEGORIES.index(categorie_actuelle),
                format_func=lambda c: f"{icon_for(c)} {c}",
                key=f"edit_cat_{selected_id}",
            )
            edit_titre = st.text_input("Titre", value=row["titre"], key=f"edit_titre_{selected_id}")
            edit_adresse = st.text_input(
                "Adresse",
                value=row["adresse"] if pd.notna(row["adresse"]) else "",
                key=f"edit_adresse_{selected_id}",
                help="Si tu changes l'adresse, les coordonnées sont recalculées automatiquement à l'enregistrement.",
            )
            c3, c4 = st.columns(2)
            statut_actuel = row["statut"] if row["statut"] in STATUTS else STATUTS[0]
            edit_statut = c3.selectbox(
                "Statut", STATUTS, index=STATUTS.index(statut_actuel), key=f"edit_statut_{selected_id}"
            )
            note_actuelle = int(row["note"]) if pd.notna(row["note"]) else 0
            edit_note = c4.slider(
                "Note (/5)", min_value=0, max_value=5, value=note_actuelle, key=f"edit_note_{selected_id}"
            )
            edit_commentaire = st.text_area(
                "Commentaire",
                value=row["commentaire"] if pd.notna(row["commentaire"]) else "",
                height=80,
                key=f"edit_commentaire_{selected_id}",
            )
            submitted = st.form_submit_button("💾 Enregistrer les modifications")

            if submitted:
                if not edit_titre.strip():
                    st.error("Le titre est obligatoire.")
                else:
                    ancienne_adresse = row["adresse"] if pd.notna(row["adresse"]) else ""
                    lat, lon = row["lat"], row["lon"]
                    if edit_adresse.strip() != ancienne_adresse:
                        resultats = geocoding.search_places(edit_adresse) if edit_adresse.strip() else []
                        lat, lon = (resultats[0]["lat"], resultats[0]["lon"]) if resultats else (None, None)

                    update_discovery_entry(
                        DISCOVERIES_PATH,
                        selected_id,
                        {
                            "date": edit_date.isoformat(),
                            "categorie": edit_categorie,
                            "titre": edit_titre.strip(),
                            "adresse": edit_adresse.strip(),
                            "lat": lat,
                            "lon": lon,
                            "statut": edit_statut,
                            "note": edit_note if edit_note > 0 else "",
                            "commentaire": edit_commentaire.strip(),
                        },
                    )
                    st.success(f"« {edit_titre} » mis à jour !")
                    st.rerun()


def _render_stats(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Découvertes", len(df))
    c2.metric("Lieux", int(df["categorie"].isin(PLACE_CATEGORIES).sum()))
    c3.metric(
        "Livres/films terminés",
        int(((df["categorie"].isin(MEDIA_CATEGORIES)) & (df["statut"] == "fait")).sum()),
    )
    note_moyenne = df["note"].mean()
    c4.metric("Note moyenne", f"{note_moyenne:.1f}/5" if pd.notna(note_moyenne) else "—")


def _render_filters(df: pd.DataFrame) -> pd.DataFrame:
    c1, c2, c3 = st.columns([2, 2, 3])
    categories_selectionnees = c1.multiselect(
        "Catégories", ALL_CATEGORIES, key="filter_categories", format_func=lambda c: f"{icon_for(c)} {c}"
    )
    statut_selectionne = c2.selectbox("Statut", ["Tous"] + STATUTS, key="filter_statut")
    recherche = c3.text_input("Recherche (titre ou adresse)", key="filter_recherche")

    filtered = df
    if categories_selectionnees:
        filtered = filtered[filtered["categorie"].isin(categories_selectionnees)]
    if statut_selectionne != "Tous":
        filtered = filtered[filtered["statut"] == statut_selectionne]
    if recherche.strip():
        q = recherche.strip().lower()
        filtered = filtered[
            filtered["titre"].str.lower().str.contains(q, na=False)
            | filtered["adresse"].str.lower().str.contains(q, na=False)
        ]
    return filtered


def _render_card(row: pd.Series):
    categorie = row["categorie"]
    with st.container(border=True):
        st.markdown(f"#### {icon_for(categorie)} {row['titre']}")
        st.caption(categorie)

        if isinstance(row.get("adresse"), str) and row["adresse"].strip():
            st.write(f"📍 {row['adresse']}")
            if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                maps_url = f"https://www.google.com/maps/search/?api=1&query={row['lat']},{row['lon']}"
                st.markdown(f"[Voir sur Google Maps]({maps_url})")

        note = row.get("note")
        if pd.notna(note) and note:
            st.write("⭐" * int(note) + "☆" * (5 - int(note)))

        st.caption(f"Statut : {row['statut']}")

        if isinstance(row.get("commentaire"), str) and row["commentaire"].strip():
            st.write(row["commentaire"])

        c1, c2 = st.columns(2)
        share_key = f"share_open_{row['id']}"
        if c1.button("📤 Partager", key=f"share_btn_{row['id']}"):
            st.session_state[share_key] = not st.session_state.get(share_key, False)
        if c2.button("🗑️ Supprimer", key=f"del_btn_{row['id']}"):
            delete_discovery_entry(DISCOVERIES_PATH, row["id"])
            st.rerun()

        if st.session_state.get(share_key):
            png_bytes = share_card.generate_share_card(row.to_dict())
            st.image(png_bytes, width="stretch")
            st.download_button(
                "💾 Télécharger la fiche",
                data=png_bytes,
                file_name=f"{_safe_filename(row['titre'])}.png",
                mime="image/png",
                key=f"dl_btn_{row['id']}",
            )


def _render_grid(df: pd.DataFrame):
    if df.empty:
        st.info("Aucune découverte ne correspond à ces filtres.")
        return

    display_df = df.sort_values("date", ascending=False)
    cols = st.columns(3)
    for i, (_, row) in enumerate(display_df.iterrows()):
        with cols[i % 3]:
            _render_card(row)


def _render_map(df: pd.DataFrame):
    place_df = df[df["categorie"].isin(PLACE_CATEGORIES)].dropna(subset=["lat", "lon"])
    if place_df.empty:
        return
    st.subheader("🗺️ Carte de mes lieux")
    st.map(place_df[["lat", "lon"]])


def _send_chat_message(chat_key: str, titre: str, media_type: str, statut: str, user_text: str):
    st.session_state[chat_key].append({"role": "user", "content": user_text})
    with st.spinner("L'agent réfléchit…"):
        try:
            reply = ai_chat.chat_about_title(titre, media_type, statut, st.session_state[chat_key])
            st.session_state[chat_key].append({"role": "assistant", "content": reply})
        except Exception as exc:
            st.session_state[chat_key].append({"role": "assistant", "content": f"⚠️ Erreur : {exc}"})


def _render_ai_chat(media_df: pd.DataFrame):
    st.subheader("🤖 Résumé & questions sur un livre ou un film")

    if not ai_chat.is_configured():
        st.warning(
            "Clé API OpenAI manquante. Définis `OPENAI_API_KEY` dans `.env` pour discuter "
            "d'un livre ou d'un film avec l'agent."
        )
        return

    display_df = media_df.sort_values("date", ascending=False)
    titres = display_df["titre"].tolist()
    titre_sel = st.selectbox("Titre", titres, key="chat_titre_select")
    entry = display_df[display_df["titre"] == titre_sel].iloc[0]

    chat_key = f"_chat_{titre_sel}"
    st.session_state.setdefault(chat_key, [])

    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state[chat_key]:
        if st.button(f"📝 Résumer « {titre_sel} »"):
            _send_chat_message(chat_key, titre_sel, entry["categorie"].lower(), entry["statut"], "Fais-moi un résumé.")
            st.rerun()

    question = st.chat_input(f"Pose une question sur « {titre_sel} »…")
    if question:
        _send_chat_message(chat_key, titre_sel, entry["categorie"].lower(), entry["statut"], question)
        st.rerun()


def render():
    st.header("📍 Mes découvertes")
    st.caption("Restaurants, cafés, musées, livres, films… tout ce que tu découvres, au même endroit.")

    migrate_legacy_media_log(LEGACY_MEDIA_PATH, DISCOVERIES_PATH)
    df = parse_discoveries(DISCOVERIES_PATH)

    _render_add_form(df)
    _render_edit_section(df)

    if df.empty:
        st.info("Aucune découverte pour le moment. Ajoute la première ci-dessus.")
        return

    st.divider()
    _render_stats(df)

    st.divider()
    st.subheader("🔎 Filtrer")
    filtered = _render_filters(df)
    _render_grid(filtered)

    _render_map(df)

    media_df = df[df["categorie"].isin(MEDIA_CATEGORIES)]
    if not media_df.empty:
        st.divider()
        _render_ai_chat(media_df)

    st.divider()
    st.subheader("Historique complet")
    display_all = df.sort_values("date", ascending=False).copy()
    display_all["date"] = display_all["date"].dt.strftime("%d/%m/%Y")
    st.dataframe(
        display_all[["date", "categorie", "titre", "adresse", "statut", "note", "commentaire"]],
        hide_index=True,
        width="stretch",
    )
