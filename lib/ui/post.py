import streamlit as st
from PIL import Image
import datetime as dt

from lib.sb import sb_client
from lib.images import upload_images_to_storage
from lib.constants import FRANCHISE_CANDIDATES, POPULAR_CHARACTERS
from lib.ai import (
    write_with_ai,
    auto_tags,
    hf_caption,
    guess_franchise_from_text,
    suggest_characters,  # expects to use POPULAR_CHARACTERS + optional NER
)

def render_post_tab():
    sb = sb_client()

    # Basic form
    title = st.text_input("Title *")
    ltype = st.selectbox("Type *", ["rent", "sell", "commission"])
    price = st.number_input("Price (₹) *", min_value=0, step=50)
    # default price_unit: "day" for rent, "fixed" otherwise
    price_unit_default_index = 1 if ltype == "rent" else 0
    price_unit = st.selectbox("Price unit *", ["fixed", "day"], index=price_unit_default_index)
    city = st.text_input("City *")
    desc = st.text_area("Description *")
    uploads = st.file_uploader("Images (up to 5)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    # --- Auto context from image caption + text guesses ---
    auto_context = desc or ""
    caption = ""
    if uploads:
        try:
            caption = hf_caption(uploads[0].getvalue())
        except Exception:
            caption = ""
        if caption:
            auto_context += "\n" + caption
            st.caption(f"AI image hint: {caption}")

    guessed = guess_franchise_from_text(auto_context) if auto_context else []
    options = guessed + [x for x in FRANCHISE_CANDIDATES if x not in guessed]
    # safe default if nothing guessed
    default_idx = 0 if options else 0
    if not options:
        options = FRANCHISE_CANDIDATES
    try:
        default_idx = 0 if guessed else options.index("Naruto")
    except Exception:
        default_idx = 0

    franchise = st.selectbox("Franchise (auto)", options, index=default_idx)

    # Character auto-suggest
    char_sugs = suggest_characters(franchise, auto_context) if franchise else []
    fallback_chars = POPULAR_CHARACTERS.get(franchise, ["Naruto Uzumaki", "Sasuke Uchiha"])
    char_options = (char_sugs or fallback_chars) + ["Other (type below)"]
    character_sel = st.selectbox("Character (suggested)", char_options)
    character = st.text_input("Or type character") if character_sel == "Other (type below)" else character_sel

    # --- AI helpers ---
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✍️ Write with AI", use_container_width=True):
            out = write_with_ai(title, franchise, character, ltype, True)
            st.session_state.ai_desc = out
    with c2:
        if st.button("🏷️ Auto-tag", use_container_width=True):
            base = f"{title} {franchise} {character} {desc} {caption}"
            st.session_state.tags = auto_tags(base)
            st.toast(", ".join(st.session_state.tags) if st.session_state.get("tags") else "No tags")

    if st.session_state.get("ai_desc"):
        desc = st.text_area("AI Description", st.session_state.ai_desc, height=140)

    # Terms
    st.markdown("### Terms & Safety")
    st.write("This platform **does not** handle delivery, payments, or escrow. Arrange directly and keep proofs.")
    agree = st.checkbox("I understand and agree to the terms *")

    # --- Publish ---
    if st.button("Publish", use_container_width=True):
        missing = []
        if not title: missing.append("Title")
        if not ltype: missing.append("Type")
        if price is None: missing.append("Price")
        if not city: missing.append("City")
        if not desc: missing.append("Description")
        if not agree: missing.append("Agreement")

        if missing:
            st.error("Fill all required fields and agree to terms. Missing: " + ", ".join(missing))
            return

        try:
            uid = st.session_state.user.id
        except Exception:
            st.error("You must be signed in to publish.")
            return

        # Upload images to Supabase Storage (public)
        image_urls = []
        try:
            image_urls = upload_images_to_storage(uploads, uid) if uploads else []
        except Exception as e:
            st.error(f"Image upload failed: {e}")
            return

        data = {
            "owner": uid,
            "ltype": ltype,
            "title": title,
            "price": int(price),
            "price_unit": price_unit,
            "city": city,
            "description": desc,
            "franchise": franchise,
            "character": character,
            "tags": st.session_state.get("tags", []),
            "images": image_urls,
            "quantity": 1,
            "status": "active",
        }

        try:
            sb.table("listings").insert(data).execute()
            st.success("Listing published!")
            st.session_state.pop("ai_desc", None)
            st.session_state.pop("tags", None)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to publish listing: {e}")
