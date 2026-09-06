"""Module Lectures / films : suivi mensuel, édition, liste à voir/à lire et agent IA."""
from datetime import date

import pandas as pd
import streamlit as st

from app.utils import ai_chat
from app.utils.parsers import append_media_entry, parse_media_log, update_media_entry

MEDIA_PATH = "data/media_log.csv"
STATUTS = ["à voir", "en cours", "terminé"]


def _render_add_form(df: pd.DataFrame):
    with st.expander("➕ Ajouter une entrée", expanded=False):
        with st.form("add_media_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            entry_date = c1.date_input("Date", value=date.today())
            entry_type = c2.selectbox("Type", ["livre", "film"])
            titre = st.text_input("Titre")
            c3, c4 = st.columns(2)
            statut = c3.selectbox("Statut", STATUTS, index=1)
            note = c4.slider("Note (/5)", min_value=0, max_value=5, value=0)
            commentaire = st.text_area("Commentaire", height=80)
            submitted = st.form_submit_button("Ajouter")

            if submitted:
                if not titre.strip():
                    st.error("Le titre est obligatoire.")
                else:
                    append_media_entry(
                        MEDIA_PATH,
                        {
                            "date": entry_date.isoformat(),
                            "type": entry_type,
                            "titre": titre.strip(),
                            "statut": statut,
                            "note": note if note > 0 else "",
                            "commentaire": commentaire.strip(),
                        },
                    )
                    st.success(f"« {titre} » ajouté !")
                    st.rerun()


def _render_edit_section(df: pd.DataFrame):
    if df.empty:
        return

    with st.expander("✏️ Modifier une entrée", expanded=False):
        display_df = df.sort_values("date", ascending=False)
        options = display_df["id"].tolist()

        def _label(entry_id: str) -> str:
            row = df[df["id"] == entry_id].iloc[0]
            date_str = row["date"].strftime("%d/%m/%Y") if pd.notna(row["date"]) else "?"
            return f"{row['titre']} ({date_str})"

        selected_id = st.selectbox("Choisir une entrée", options, format_func=_label, key="edit_select")
        row = df[df["id"] == selected_id].iloc[0]

        # Les clés des widgets incluent selected_id : sans ça, Streamlit conserve les
        # valeurs du précédent formulaire affiché et l'édition semble ne rien faire.
        with st.form(f"edit_media_form_{selected_id}"):
            c1, c2 = st.columns(2)
            edit_date = c1.date_input(
                "Date",
                value=row["date"].date() if pd.notna(row["date"]) else date.today(),
                key=f"edit_date_{selected_id}",
            )
            edit_type = c2.selectbox(
                "Type", ["livre", "film"], index=["livre", "film"].index(row["type"]), key=f"edit_type_{selected_id}"
            )
            edit_titre = st.text_input("Titre", value=row["titre"], key=f"edit_titre_{selected_id}")
            c3, c4 = st.columns(2)
            statut_actuel = row["statut"] if row["statut"] in STATUTS else "en cours"
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
                    update_media_entry(
                        MEDIA_PATH,
                        selected_id,
                        {
                            "date": edit_date.isoformat(),
                            "type": edit_type,
                            "titre": edit_titre.strip(),
                            "statut": edit_statut,
                            "note": edit_note if edit_note > 0 else "",
                            "commentaire": edit_commentaire.strip(),
                        },
                    )
                    st.success(f"« {edit_titre} » mis à jour !")
                    st.rerun()


def _send_chat_message(chat_key: str, titre: str, media_type: str, statut: str, user_text: str):
    st.session_state[chat_key].append({"role": "user", "content": user_text})
    with st.spinner("L'agent réfléchit…"):
        try:
            reply = ai_chat.chat_about_title(titre, media_type, statut, st.session_state[chat_key])
            st.session_state[chat_key].append({"role": "assistant", "content": reply})
        except Exception as exc:
            st.session_state[chat_key].append({"role": "assistant", "content": f"⚠️ Erreur : {exc}"})


def _render_ai_chat(df: pd.DataFrame):
    st.subheader("🤖 Résumé & questions sur un titre")

    if not ai_chat.is_configured():
        st.warning(
            "Clé API OpenAI manquante. Définis `OPENAI_API_KEY` dans `.env` pour discuter "
            "d'un livre ou d'un film avec l'agent."
        )
        return

    if df.empty:
        st.caption("Ajoute au moins un livre ou un film pour pouvoir en discuter avec l'agent.")
        return

    display_df = df.sort_values("date", ascending=False)
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
            _send_chat_message(chat_key, titre_sel, entry["type"], entry["statut"], "Fais-moi un résumé.")
            st.rerun()

    question = st.chat_input(f"Pose une question sur « {titre_sel} »…")
    if question:
        _send_chat_message(chat_key, titre_sel, entry["type"], entry["statut"], question)
        st.rerun()


def render():
    st.header("📚 Lectures / Films")

    df = parse_media_log(MEDIA_PATH)

    _render_add_form(df)
    _render_edit_section(df)

    if df.empty:
        st.info("Aucune entrée pour le moment. Ajoute ta première lecture ou film ci-dessus.")
        return

    df["mois"] = df["date"].dt.to_period("M")
    mois_disponibles = sorted(df["mois"].dropna().unique())
    mois_courant = mois_disponibles[-1]
    df_mois = df[df["mois"] == mois_courant]

    st.divider()
    st.subheader(f"Ce mois-ci — {mois_courant}")

    # statut peut être saisi "terminé" ou "termine" selon la source -> normaliser
    termines_mois = df_mois[df_mois["statut"].str.lower().isin(["terminé", "termine"])]

    col1, col2, col3 = st.columns(3)
    n_livres = (termines_mois["type"] == "livre").sum()
    n_films = (termines_mois["type"] == "film").sum()
    col1.metric("Livres terminés", n_livres)
    col2.metric("Films terminés", n_films)
    note_moyenne = termines_mois["note"].mean()
    col3.metric("Note moyenne", f"{note_moyenne:.1f}/5" if pd.notna(note_moyenne) else "—")

    if termines_mois.empty:
        st.caption("Rien de terminé ce mois-ci pour l'instant.")
    else:
        display = termines_mois.sort_values("date", ascending=False).copy()
        display["date"] = display["date"].dt.strftime("%d/%m/%Y")
        st.dataframe(
            display[["date", "type", "titre", "note", "commentaire"]],
            hide_index=True,
            width="stretch",
        )

    a_voir = df[df["statut"] == "à voir"]
    if not a_voir.empty:
        st.divider()
        st.subheader("🔖 À voir / à lire")
        display_a_voir = a_voir.sort_values("date", ascending=False).copy()
        display_a_voir["date"] = display_a_voir["date"].dt.strftime("%d/%m/%Y")
        st.dataframe(
            display_a_voir[["date", "type", "titre", "commentaire"]],
            hide_index=True,
            width="stretch",
        )

    en_cours = df[df["statut"].str.lower() == "en cours"]
    if not en_cours.empty:
        st.divider()
        st.subheader("📖 En cours")
        display_en_cours = en_cours.sort_values("date", ascending=False).copy()
        display_en_cours["date"] = display_en_cours["date"].dt.strftime("%d/%m/%Y")
        st.dataframe(
            display_en_cours[["date", "type", "titre", "commentaire"]],
            hide_index=True,
            width="stretch",
        )

    st.divider()
    _render_ai_chat(df)

    st.divider()
    st.subheader("Historique complet")
    display_all = df.sort_values("date", ascending=False).copy()
    display_all["date"] = display_all["date"].dt.strftime("%d/%m/%Y")
    st.dataframe(
        display_all[["date", "type", "titre", "statut", "note", "commentaire"]],
        hide_index=True,
        width="stretch",
    )
