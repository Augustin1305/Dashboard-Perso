"""Authentification par compte (email + mot de passe), via Supabase Auth.

Chaque onglet/navigateur ouvre sa propre session Streamlit : le client
Supabase est donc stocké dans `st.session_state` (scope par session), jamais
mis en cache globalement — sinon la connexion d'un utilisateur "fuiterait"
vers les autres visiteurs du même serveur.
"""
from __future__ import annotations

import streamlit as st
from supabase import Client, create_client

from app.utils import theme

_CLIENT_KEY = "_supabase_client"
_USER_KEY = "user"


def get_client() -> Client:
    if _CLIENT_KEY not in st.session_state:
        st.session_state[_CLIENT_KEY] = create_client(
            st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"]
        )
    return st.session_state[_CLIENT_KEY]


def current_user() -> dict | None:
    return st.session_state.get(_USER_KEY)


def _set_current_user(auth_user) -> None:
    st.session_state[_USER_KEY] = {"id": auth_user.id, "email": auth_user.email}


def _render_login_tab():
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Mot de passe", type="password", key="login_password")
        submitted = st.form_submit_button("Se connecter", type="primary")

        if submitted:
            try:
                response = get_client().auth.sign_in_with_password(
                    {"email": email.strip(), "password": password}
                )
                _set_current_user(response.user)
                st.rerun()
            except Exception as exc:
                st.error(f"Connexion impossible : {exc}")


def _render_signup_tab():
    with st.form("signup_form"):
        email = st.text_input("Email", key="signup_email")
        password = st.text_input(
            "Mot de passe (6 caractères minimum)", type="password", key="signup_password"
        )
        submitted = st.form_submit_button("Créer mon compte", type="primary")

        if submitted:
            if not email.strip() or len(password) < 6:
                st.error("Email requis et mot de passe d'au moins 6 caractères.")
            else:
                try:
                    response = get_client().auth.sign_up(
                        {"email": email.strip(), "password": password}
                    )
                    if response.session is None:
                        st.warning("Vérifie ta boîte mail pour confirmer ton compte, puis connecte-toi.")
                    else:
                        _set_current_user(response.user)
                        st.rerun()
                except Exception as exc:
                    st.error(f"Inscription impossible : {exc}")


def render_auth_gate() -> dict | None:
    """Affiche l'écran de connexion/inscription tant qu'aucun utilisateur n'est
    connecté. Retourne l'utilisateur courant (id, email) une fois connecté."""
    user = current_user()
    if user is not None:
        return user

    theme.render_wordmark()
    st.caption("Connecte-toi pour accéder à ton carnet et à celui que tes proches t'envoient.")

    tab_login, tab_signup = st.tabs(["Se connecter", "Créer un compte"])
    with tab_login:
        _render_login_tab()
    with tab_signup:
        _render_signup_tab()

    return None


def render_logout_button() -> None:
    user = current_user()
    if user is None:
        return
    st.sidebar.caption(f"Connecté·e : {user['email']}")
    if st.sidebar.button("🚪 Se déconnecter"):
        try:
            get_client().auth.sign_out()
        except Exception:
            pass
        st.session_state.pop(_USER_KEY, None)
        st.session_state.pop(_CLIENT_KEY, None)
        st.rerun()
