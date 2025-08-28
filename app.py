import streamlit as st
from lib.sb import sb_client
from lib.auth import handle_oauth_exchange, sign_in_with_google_button
from lib.ui.browse import render_browse_tab
from lib.ui.post import render_post_tab
from lib.ui.saved import render_saved_tab

st.set_page_config(page_title="Rent-a-Cos", page_icon="🗡️", layout="wide")
if "user" not in st.session_state: st.session_state.user = None

handle_oauth_exchange()  # grabs ?code=..., exchanges, sets session_state.user

st.title("🗡️ Rent-a-Cos")
tabs = st.tabs(["Browse","Post listing","Saved searches"])

with tabs[0]:
    render_browse_tab()

with tabs[1]:
    if not st.session_state.user:
        sign_in_with_google_button(key="signin_google_tab1")
    else:
        render_post_tab()

with tabs[2]:
    if not st.session_state.user:
        st.info("Sign in to save searches.")
        sign_in_with_google_button(key="signin_google_tab2")
    else:
        render_saved_tab()

st.markdown("---")
st.write("⚠️ Rent-a-Cos does not provide delivery or payments. Users arrange their own transactions securely.")
