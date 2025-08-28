from typing import Optional, List
import streamlit as st
from .theme import img_b64

MASCOT_PATH = "assets/pixel_gojo.png"

def mascot_img_html(width: int = 70) -> str:
    b64 = img_b64(MASCOT_PATH)
    if not b64:
        return "<div class='pill'>Mascot</div>"
    return f'<img src="data:image/png;base64,{b64}" width="{width}" style="image-rendering:pixelated;">'


# ---------------------------
# HERO (banner at top)
# ---------------------------
def hero(title: str = "Rent-a-Cos",
         subtitle: str = "Cosplay your dreams, without breaking your wallet 💖"):
    st.markdown(
        f"""
<div class="app-hero">
  <div class="brand">{mascot_img_html(70)}
    <h1>{title}</h1>
  </div>
  <div style="margin-top:8px;">
    <span class="pill">{subtitle}</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ---------------------------
# SEARCH BAR
# ---------------------------
def search_bar(placeholder: str = "🔍 Search props, wigs, fabrics, or characters…") -> str:
    st.markdown('<div class="search">', unsafe_allow_html=True)
    q = st.text_input("", placeholder=placeholder, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    return q


# ---------------------------
# LISTING CARD
# ---------------------------
def listing_card(
    title: str,
    price: str,
    mode_badge: str,
    tags: List[str],
    img_html: Optional[str] = None,
    key: Optional[str] = None,
):
    card_key = key or f"card_{hash(title) & 0xffff}"

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        f"""
<div style="display:flex;align-items:center;justify-content:center;background:#fff7fc;
            border:2px dashed #ffd6ef;border-radius:12px;height:160px;margin-bottom:10px;">
  {img_html or mascot_img_html(90)}
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    right = f'<span class="badge {"rent" if mode_badge.lower()=="rent" else "sell"}">{mode_badge}</span>'
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<div class='price'>{price}</div>{right}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(" ".join([f"<span class='tag'>#{t}</span>" for t in tags]), unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.button("💖 Save", use_container_width=True, key=f"{card_key}_save")
    with c2:
        st.button("🛒 " + ("Rent Now" if mode_badge.lower()=="rent" else "Buy Now"),
                  use_container_width=True, key=f"{card_key}_cta")

    st.markdown('</div>', unsafe_allow_html=True)
