"""Module Rep'r : carnet d'adresses personnel (restaurants, cafés, musées...),
avec recherche d'adresse automatique, ressenti coloré, fiches partageables en
image et envoi d'une fiche à un autre utilisateur de l'app.
"""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from app.utils import db, geocoding, share_card, theme
from app.utils.categories import (
    CATEGORIES,
    RESSENTI_IDS,
    icon_for,
    ressenti_color,
    ressenti_label,
    ressenti_pill_label,
)

_MANUAL_ADDRESS_OPTION = "✏️ Aucun ne correspond — je saisis l'adresse moi-même"


def _safe_filename(titre: str) -> str:
    return re.sub(r"[^\w\-. ]", "_", titre).strip() or "repr"


def _maps_url(adresse: str | None, lat=None, lon=None) -> str | None:
    """Lien Google Maps cliquable : coordonnées précises si on les a, sinon
    une recherche texte sur l'adresse (fonctionne même sans géocodage)."""
    if lat is not None and lon is not None and pd.notna(lat) and pd.notna(lon):
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    if isinstance(adresse, str) and adresse.strip():
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(adresse.strip())}"
    return None


def _ressenti_badge_html(vecu: bool, ressenti: str | None) -> str:
    if vecu and ressenti:
        return theme.render_ressenti_badge(ressenti_color(ressenti), ressenti_label(ressenti))
    return theme.render_ressenti_badge(theme.MUTED, "Envie — pas encore testé", dashed=True)


def _render_inbox(user: dict):
    inbox = db.fetch_inbox(user["id"])
    if not inbox:
        return

    st.subheader("📥 Rep'rs reçus")
    for share in inbox:
        snapshot = share.get("snapshot") or {}
        categorie = snapshot.get("categorie") or "Autre lieu"
        with st.container(border=True):
            st.markdown(f"#### {icon_for(categorie)} {snapshot.get('titre') or 'Sans titre'}")
            st.caption(f"Envoyé par {share['from_email']}")

            adresse = snapshot.get("adresse")
            if isinstance(adresse, str) and adresse.strip():
                st.markdown(f"{icon_for(categorie)} [{adresse}]({_maps_url(adresse, snapshot.get('lat'), snapshot.get('lon'))})")

            st.markdown(_ressenti_badge_html(bool(snapshot.get("vecu")), snapshot.get("ressenti")), unsafe_allow_html=True)

            if snapshot.get("commentaire"):
                st.write(snapshot["commentaire"])

            c1, c2 = st.columns(2)
            if c1.button("➕ Ajouter à mes rep'rs", key=f"accept_{share['id']}"):
                db.respond_to_share(share["id"], True, user["id"], share["from_email"], snapshot)
                st.success(f"« {snapshot.get('titre')} » ajouté à tes rep'rs !")
                st.rerun()
            if c2.button("🗑️ Ignorer", key=f"dismiss_{share['id']}"):
                db.respond_to_share(share["id"], False, user["id"], share["from_email"], snapshot)
                st.rerun()

    st.divider()


def _render_add_form(user: dict, df: pd.DataFrame):
    with st.expander("📍 Poser un rep'r", expanded=df.empty):
        col1, col2 = st.columns([3, 2])
        nom = col1.text_input(
            "Nom",
            key="disc_nom",
            placeholder="Ex: Chez Odette, Le Comptoir du Relais…",
        )
        categorie = col2.selectbox(
            "Catégorie", CATEGORIES, key="disc_categorie", format_func=lambda c: f"{icon_for(c)} {c}"
        )

        adresse, lat, lon = "", None, None

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

        if isinstance(adresse, str) and adresse.strip():
            st.markdown(f"{icon_for(categorie)} [{adresse}]({_maps_url(adresse, lat, lon)})")

        mode = st.segmented_control("Statut", ["Vécu", "Envie"], default="Vécu", key="disc_mode")
        vecu = mode == "Vécu"

        ressenti = None
        if vecu:
            st.caption("Ton ressenti")
            ressenti = st.pills(
                "Ressenti", RESSENTI_IDS, format_func=ressenti_pill_label,
                default="coeur", key="disc_ressenti", label_visibility="collapsed",
            )
        else:
            st.caption("Pas encore testé : tu noteras ton ressenti après.")

        commentaire = st.text_input("Une ligne pour t'en souvenir", key="disc_commentaire")
        entry_date = st.date_input("Date", value=date.today(), key="disc_date")

        if st.button("Enregistrer", type="primary", key="disc_submit"):
            if not nom.strip():
                st.error("Le nom est obligatoire.")
            else:
                db.insert_discovery(
                    user["id"],
                    {
                        "date": entry_date.isoformat(),
                        "categorie": categorie,
                        "titre": nom.strip(),
                        "adresse": adresse.strip() if isinstance(adresse, str) else "",
                        "lat": lat,
                        "lon": lon,
                        "vecu": vecu,
                        "ressenti": ressenti or "",
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
                    "disc_ressenti",
                ]:
                    st.session_state.pop(key, None)
                st.success(f"« {nom} » posé sur ta carte !")
                st.rerun()


def _render_edit_section(user: dict, df: pd.DataFrame):
    if df.empty:
        return

    with st.expander("✏️ Modifier un rep'r", expanded=False):
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
            categorie_actuelle = row["categorie"] if row["categorie"] in CATEGORIES else CATEGORIES[0]
            edit_categorie = c2.selectbox(
                "Catégorie",
                CATEGORIES,
                index=CATEGORIES.index(categorie_actuelle),
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

            edit_mode = st.segmented_control(
                "Statut", ["Vécu", "Envie"],
                default="Vécu" if bool(row["vecu"]) else "Envie",
                key=f"edit_mode_{selected_id}",
            )
            edit_vecu = edit_mode == "Vécu"
            edit_ressenti = None
            if edit_vecu:
                ressenti_actuel = row["ressenti"] if row["ressenti"] in RESSENTI_IDS else None
                edit_ressenti = st.pills(
                    "Ton ressenti", RESSENTI_IDS, format_func=ressenti_pill_label,
                    default=ressenti_actuel, key=f"edit_ressenti_{selected_id}",
                )

            edit_commentaire = st.text_input(
                "Une ligne pour t'en souvenir",
                value=row["commentaire"] if pd.notna(row["commentaire"]) else "",
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

                    db.update_discovery(
                        user["id"],
                        selected_id,
                        {
                            "date": edit_date.isoformat(),
                            "categorie": edit_categorie,
                            "titre": edit_titre.strip(),
                            "adresse": edit_adresse.strip(),
                            "lat": lat,
                            "lon": lon,
                            "vecu": edit_vecu,
                            "ressenti": edit_ressenti or "",
                            "commentaire": edit_commentaire.strip(),
                        },
                    )
                    st.success(f"« {edit_titre} » mis à jour !")
                    st.rerun()


def _render_stats(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rep'rs posés", len(df))
    c2.metric("Vécu", int(df["vecu"].sum()))
    c3.metric("Envie", int((~df["vecu"]).sum()))
    c4.metric("Coups de cœur", int((df["ressenti"] == "coeur").sum()))


def _render_filters(df: pd.DataFrame) -> pd.DataFrame:
    c1, c2, c3 = st.columns([2, 2, 3])
    categories_selectionnees = c1.multiselect(
        "Catégories", CATEGORIES, key="filter_categories", format_func=lambda c: f"{icon_for(c)} {c}"
    )
    mode_filtre = c2.segmented_control("Statut", ["Tous", "Vécu", "Envie"], default="Tous", key="filter_mode")
    recherche = c3.text_input("Recherche (titre ou adresse)", key="filter_recherche")

    ressentis_selectionnes = st.multiselect(
        "Ressenti", RESSENTI_IDS, key="filter_ressentis", format_func=ressenti_pill_label
    )

    filtered = df
    if categories_selectionnees:
        filtered = filtered[filtered["categorie"].isin(categories_selectionnees)]
    if mode_filtre == "Vécu":
        filtered = filtered[filtered["vecu"]]
    elif mode_filtre == "Envie":
        filtered = filtered[~filtered["vecu"]]
    if ressentis_selectionnes:
        filtered = filtered[filtered["ressenti"].isin(ressentis_selectionnes)]
    if recherche.strip():
        q = recherche.strip().lower()
        filtered = filtered[
            filtered["titre"].str.lower().str.contains(q, na=False)
            | filtered["adresse"].str.lower().str.contains(q, na=False)
        ]
    return filtered


def _render_card(user: dict, row: pd.Series):
    categorie = row["categorie"]
    with st.container(border=True):
        st.markdown(f"#### {icon_for(categorie)} {row['titre']}")
        st.caption(categorie)

        if isinstance(row.get("adresse"), str) and row["adresse"].strip():
            st.markdown(f"{icon_for(categorie)} [{row['adresse']}]({_maps_url(row['adresse'], row.get('lat'), row.get('lon'))})")

        st.markdown(_ressenti_badge_html(bool(row.get("vecu")), row.get("ressenti")), unsafe_allow_html=True)

        if isinstance(row.get("commentaire"), str) and row["commentaire"].strip():
            st.write(row["commentaire"])

        c1, c2, c3 = st.columns(3)
        export_key = f"export_open_{row['id']}"
        send_key = f"send_open_{row['id']}"
        if c1.button("💾 Exporter", key=f"export_btn_{row['id']}"):
            st.session_state[export_key] = not st.session_state.get(export_key, False)
        if c2.button("✉️ Envoyer", key=f"send_btn_{row['id']}"):
            st.session_state[send_key] = not st.session_state.get(send_key, False)
        if c3.button("🗑️ Supprimer", key=f"del_btn_{row['id']}"):
            db.delete_discovery(user["id"], row["id"])
            st.rerun()

        if st.session_state.get(export_key):
            png_bytes = share_card.generate_share_card(row.to_dict())
            st.image(png_bytes, width="stretch")
            st.download_button(
                "💾 Télécharger la fiche",
                data=png_bytes,
                file_name=f"{_safe_filename(row['titre'])}.png",
                mime="image/png",
                key=f"dl_btn_{row['id']}",
            )

        if st.session_state.get(send_key):
            with st.form(f"send_form_{row['id']}"):
                to_email = st.text_input("Email du destinataire (doit déjà avoir un compte)", key=f"send_email_{row['id']}")
                if st.form_submit_button("Envoyer"):
                    try:
                        db.share_discovery(user, to_email, row.to_dict())
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.session_state[send_key] = False
                        st.success(f"Fiche envoyée à {to_email.strip()} !")
                        st.rerun()


def _render_grid(user: dict, df: pd.DataFrame):
    if df.empty:
        st.info("Aucun rep'r ne correspond à ces filtres.")
        return

    display_df = df.sort_values("date", ascending=False)
    cols = st.columns(3)
    for i, (_, row) in enumerate(display_df.iterrows()):
        with cols[i % 3]:
            _render_card(user, row)


def _hex_to_rgb(hex_color: str) -> list[int]:
    hex_color = hex_color.lstrip("#")
    return [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]


def _render_map(df: pd.DataFrame):
    place_df = df.dropna(subset=["lat", "lon"]).copy()
    if place_df.empty:
        return
    st.subheader("🗺️ Carte de mes rep'rs")
    place_df["color"] = place_df.apply(
        lambda r: _hex_to_rgb(ressenti_color(r["ressenti"])) if r["vecu"] and r["ressenti"] else [154, 165, 177],
        axis=1,
    )
    st.map(place_df[["lat", "lon", "color"]], color="color")


def render(user: dict):
    theme.render_wordmark()
    st.caption("Un carnet d'adresses privé, sans réseau social ni pub.")

    _render_inbox(user)

    df = db.fetch_discoveries(user["id"])

    _render_add_form(user, df)
    _render_edit_section(user, df)

    if df.empty:
        st.info("Aucun rep'r pour le moment. Pose le premier ci-dessus.")
        return

    st.divider()
    _render_stats(df)

    st.divider()
    st.subheader("🔎 Filtrer")
    filtered = _render_filters(df)
    _render_grid(user, filtered)

    _render_map(df)

    st.divider()
    st.subheader("Historique complet")
    display_all = df.sort_values("date", ascending=False).copy()
    display_all["date"] = display_all["date"].dt.strftime("%d/%m/%Y")
    display_all["statut"] = display_all["vecu"].map({True: "Vécu", False: "Envie"})
    display_all["ressenti"] = display_all["ressenti"].apply(ressenti_label)
    st.dataframe(
        display_all[["date", "categorie", "titre", "adresse", "statut", "ressenti", "commentaire"]],
        hide_index=True,
        width="stretch",
    )
