"""Module Bucket list : envies/objectifs à réaliser, avec un nom et une année cible."""
import os
import uuid

import pandas as pd
import streamlit as st

BUCKET_PATH = "data/bucket_list.csv"
BUCKET_COLUMNS = ["id", "nom", "annee"]


def _load() -> pd.DataFrame:
    if not os.path.exists(BUCKET_PATH):
        return pd.DataFrame(columns=BUCKET_COLUMNS)
    df = pd.read_csv(BUCKET_PATH)
    for col in BUCKET_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")
    return df[BUCKET_COLUMNS]


def _save(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(BUCKET_PATH), exist_ok=True)
    df[BUCKET_COLUMNS].to_csv(BUCKET_PATH, index=False)


def render():
    st.header("🪣 Bucket list")
    st.caption("Les envies et objectifs à réaliser, avec une année cible.")

    df = _load()

    with st.expander("➕ Ajouter un élément", expanded=df.empty):
        with st.form("add_bucket_form", clear_on_submit=True):
            nom = st.text_input("Nom")
            annee = st.number_input(
                "Année cible", min_value=2000, max_value=2100, value=pd.Timestamp.now().year, step=1
            )
            submitted = st.form_submit_button("Ajouter")
            if submitted:
                if not nom.strip():
                    st.error("Le nom est obligatoire.")
                else:
                    new_row = pd.DataFrame(
                        [{"id": uuid.uuid4().hex[:8], "nom": nom.strip(), "annee": int(annee)}]
                    )
                    df = pd.concat([df, new_row], ignore_index=True)
                    _save(df)
                    st.success(f"« {nom} » ajouté à la bucket list !")
                    st.rerun()

    if df.empty:
        st.info("Ta bucket list est vide. Ajoute ta première envie ci-dessus.")
        return

    st.divider()
    st.subheader(f"{len(df)} élément(s)")

    for annee, group in df.sort_values("annee").groupby("annee", dropna=False):
        st.markdown(f"**{annee}**" if pd.notna(annee) else "**Sans année précise**")
        for _, row in group.iterrows():
            c1, c2 = st.columns([6, 1])
            c1.write(row["nom"])
            if c2.button("🗑️", key=f"del_{row['id']}"):
                df = df[df["id"] != row["id"]]
                _save(df)
                st.rerun()
