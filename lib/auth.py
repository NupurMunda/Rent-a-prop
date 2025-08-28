import streamlit as st
from lib.sb import sb_client

def handle_oauth_exchange():
    code = st.query_params.get("code")
    if code and not st.session_state.get("user"):
        sb = sb_client()
        try:
            session = sb.auth.exchange_code_for_session({"auth_code": code})
            # store user in session
            st.session_state["user"] = getattr(session, "user", None)
            # clear ?code=... from URL to avoid re-exchange on rerun
            st.query_params.clear()
            st.rerun()
        except Exception:
            # You may want to st.warning(...) here while debugging
            pass

def sign_in_with_google_button(key: str = "signin_google"):
    """Render a Google sign-in button. Pass a unique `key` if used in multiple places."""
    if st.button("Sign in with Google", key=key):
        sb = sb_client()
        redirect = st.secrets["supabase"].get("redirect_url", "")
        try:
            res = sb.auth.sign_in_with_oauth(
                {"provider": "google", "options": {"redirect_to": redirect}}
            )
            url = res.get("url") if isinstance(res, dict) else None
            if url:
                # Prefer a proper link button so it doesn't create another identical button widget
                st.link_button("Continue →", url)
        except Exception:
            st.error("Unable to start sign-in. Check Supabase auth settings.")
