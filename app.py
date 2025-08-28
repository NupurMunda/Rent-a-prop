import streamlit as st
from lib.sb import sb_client
from lib.auth import handle_oauth_exchange, sign_in_with_google_button
from lib.ui.browse import render_browse_tab
from lib.ui.post import render_post_tab
from lib.ui.saved import render_saved_tab
from lib.ui.theme import load_css
from lib.ui.components import hero, search_bar, listing_card

load_css()        # injects lib/ui/styles.css
hero()            # shows the banner/header
q = search_bar()  # pretty search bar under the banner

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

cols = st.columns(2)
with cols[0]:
    listing_card(
        title="Gojo blindfold (silk) + wig",
        price="₹299/day",
        mode_badge="RENT",
        tags=["Gojo", "Accessory", "Wig"],
        key="gojo_0",          # 👈 unique
    )
with cols[1]:
    listing_card(
        title="Rengoku flame katana",
        price="₹399",
        mode_badge="BUY",
        tags=["Katana", "Prop"],
        key="rengoku_1",       # 👈 unique
    )


st.markdown("---")
st.write("⚠️ Rent-a-Cos does not provide delivery or payments. Users arrange their own transactions securely.")
