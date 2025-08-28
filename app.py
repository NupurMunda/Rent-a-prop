import streamlit as st
from supabase import create_client, Client
import pandas as pd
from PIL import Image
import io, uuid, requests, datetime as dt

st.set_page_config(page_title="Rent-a-Cos", page_icon="🗡️", layout="wide")

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["anon_key"]
HF_TOKEN = st.secrets.get("HF_TOKEN", "")
REDIRECT_URL = st.secrets["supabase"].get("redirect_url", "")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------- AUTH HELPERS -----------------
def sign_in_with_google():
    try:
        res = sb.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": REDIRECT_URL}
        })
        return res.get("url") if isinstance(res, dict) else None
    except Exception:
        return None

# Exchange code from redirect
code = st.query_params.get("code")
if code and not st.session_state.get("user"):
    try:
        session = sb.auth.exchange_code_for_session({"auth_code": code})
        st.session_state.user = session.user
        st.query_params.clear()
        st.rerun()
    except Exception:
        pass

# ----------------- AI HELPERS -----------------
FRANCHISE_CANDIDATES = [
    "Naruto","One Piece","Demon Slayer","Jujutsu Kaisen","Attack on Titan","Bleach","My Hero Academia",
    "Genshin Impact","Zelda","Final Fantasy","Star Wars","Marvel","DC","Harry Potter","Chainsaw Man",
    "Spy x Family","Sailor Moon","Dragon Ball","Nier","Elden Ring"
]

POPULAR_CHARACTERS = {
    "Naruto": ["Naruto Uzumaki","Sasuke Uchiha","Sakura Haruno","Kakashi Hatake","Itachi Uchiha"],
    "One Piece": ["Monkey D. Luffy","Roronoa Zoro","Nami","Sanji","Tony Tony Chopper"],
    "Demon Slayer": ["Tanjiro Kamado","Nezuko Kamado","Zenitsu Agatsuma","Inosuke Hashibira","Giyu Tomioka"],
    "Jujutsu Kaisen": ["Yuji Itadori","Megumi Fushiguro","Nobara Kugisaki","Satoru Gojo","Sukuna"],
    "Attack on Titan": ["Eren Yeager","Mikasa Ackerman","Armin Arlert","Levi Ackerman","Hange Zoe"],
    "Bleach": ["Ichigo Kurosaki","Rukia Kuchiki","Renji Abarai","Byakuya Kuchiki","Toshiro Hitsugaya"],
    "My Hero Academia": ["Izuku Midoriya","Katsuki Bakugo","Shoto Todoroki","Ochaco Uraraka","All Might"],
    "Genshin Impact": ["Aether","Lumine","Diluc","Venti","Zhongli","Raiden Shogun","Hu Tao"],
    "Zelda": ["Link","Zelda","Ganondorf"],
    "Star Wars": ["Darth Vader","Luke Skywalker","Princess Leia","Obi-Wan Kenobi","Ahsoka Tano"],
    "Marvel": ["Spider-Man","Iron Man","Captain America","Black Widow","Wanda Maximoff"],
    "DC": ["Batman","Superman","Wonder Woman","Harley Quinn","Joker"],
    "Harry Potter": ["Harry Potter","Hermione Granger","Ron Weasley","Severus Snape","Draco Malfoy"],
    "Chainsaw Man": ["Denji","Makima","Power","Aki Hayakawa"],
    "Dragon Ball": ["Goku","Vegeta","Gohan","Bulma","Trunks"]
}

@st.cache_data(show_spinner=False)
def write_with_ai(title, franchise, character, ltype, handmade):
    if not HF_TOKEN:
        return "Add HF_TOKEN in Streamlit secrets to enable AI."
    url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3.1-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = (
        f"Write an 80-120 word marketplace listing for a cosplay item.\n"
        f"Title: {title}\nFranchise: {franchise}\nCharacter: {character}\n"
        f"Type: {ltype}. Handmade: {handmade}. Include fit, sizing, materials, condition, who it suits."
    )
    try:
        r = requests.post(url, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 200}}, timeout=60)
        js = r.json()
        if isinstance(js, list) and js and "generated_text" in js[0]:
            return js[0]["generated_text"].strip()
    except Exception:
        pass
    return "AI is busy. Try again."

@st.cache_data(show_spinner=False)
def auto_tags(text):
    if not HF_TOKEN: return []
    url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    labels = [
        "anime","manga","cosplay","prop","weapon","costume","figure","collectible","handmade","official","wig","accessory",
        "Naruto","One Piece","Attack on Titan","My Hero Academia","Demon Slayer","Dragon Ball","Bleach"
    ]
    payload = {"inputs": text, "parameters": {"candidate_labels": labels}}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        out = r.json()
        return [lbl for lbl,score in zip(out.get("labels",[]), out.get("scores",[])) if score>0.35][:12]
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def hf_caption(image_bytes: bytes) -> str:
    if not HF_TOKEN: return ""
    url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Accept": "application/json"}
    try:
        r = requests.post(url, headers=headers, data=image_bytes, timeout=60)
        js = r.json()
        if isinstance(js, list) and js and "generated_text" in js[0]:
            return js[0]["generated_text"]
    except Exception:
        pass
    return ""

@st.cache_data(show_spinner=False)
def guess_franchise_from_text(text: str):
    if not HF_TOKEN: return []
    url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text, "parameters": {"candidate_labels": FRANCHISE_CANDIDATES}}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        out = r.json()
        pairs = list(zip(out.get("labels",[]), out.get("scores",[])))
        return [lbl for lbl,score in sorted(pairs, key=lambda x: -x[1])][:5]
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def hf_ner_people(text: str):
    if not HF_TOKEN or not text: return []
    url = "https://api-inference.huggingface.co/models/dslim/bert-base-NER"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    r = requests.post(url, headers=headers, json={"inputs": text}, timeout=60)
    names=[]
    try:
        for ent in r.json():
            if isinstance(ent, dict) and ent.get("entity_group") == "PER" and ent.get("score",0)>0.80:
                names.append(ent.get("word"))
    except Exception:
        pass
    seen=set(); out=[]
    for n in names:
        if n not in seen:
            seen.add(n); out.append(n)
    return out

@st.cache_data(show_spinner=False)
def suggest_characters(franchise: str, context_text: str):
    base = POPULAR_CHARACTERS.get(franchise, [])
    ner = hf_ner_people(context_text)
    ranked=[]
    for name in base:
        score = 2.0 if any(name.lower() in n.lower() or n.lower() in name.lower() for n in ner) else 1.0
        ranked.append((score,name))
    ranked.sort(reverse=True)
    result=[n for _,n in ranked]
    for n in ner:
        if not any(n.lower()==b.lower() for b in result):
            result.append(n)
    return result[:10]

# ----------------- Main UI -----------------
st.title("🗡️ Rent-a-Cos")
if "user" not in st.session_state: st.session_state.user=None

browse, post, chat, my, saved = st.tabs(["Browse","Post listing","Chat","My listings","Saved searches"])

# ----------------- Browse (Explore) -----------------
with browse:
    colf1, colf2, colf3 = st.columns([1,1,2])
    cities = ["All","Bengaluru","Mumbai","Delhi","Hyderabad","Pune","Kolkata","Chennai","Remote"]
    city_q = colf1.selectbox("City", cities, index=0)
    type_q = colf2.multiselect("Type", ["rent","sell","commission"], default=["rent","sell","commission"])
    text_q = colf3.text_input("Search title / franchise / character")

    # Alerts banner for saved searches
    if st.session_state.user:
        uid = st.session_state.user.id
        saved_rows = sb.table("saved_searches").select("*").eq("user_id", uid).order("created_at", desc=True).execute().data
        if saved_rows:
            with st.expander("🔔 Saved search alerts"):
                for s in saved_rows:
                    q = sb.table("listings").select("id,title,franchise,character,city,ltype,created_at").eq("status","active").gte("created_at", s.get("last_seen"))
                    new_rows = q.order("created_at", desc=True).execute().data
                    qtext = s.get("query") or ""
                    count = 0
                    for r in new_rows:
                        hay = " ".join([r.get("title") or "", r.get("franchise") or "", r.get("character") or ""]).lower()
                        if not qtext or qtext.lower() in hay:
                            count += 1
                    cols_alert = st.columns([3,1,1])
                    with cols_alert[0]:
                        st.write(f"**{qtext or 'Any'}** — new since last check")
                    with cols_alert[1]:
                        if st.button(f"View {count} new", key=f"view_{s['id']}"):
                            sb.table("saved_searches").update({"last_seen": dt.datetime.utcnow().isoformat()}).eq("id", s['id']).execute()
                            if qtext:
                                st.session_state["text_q_override"] = qtext
                            st.rerun()
                    with cols_alert[2]:
                        if st.button("Delete", key=f"del_{s['id']}"):
                            sb.table("saved_searches").delete().eq("id", s['id']).execute()
                            st.rerun()

    # apply override text
    _text_q = st.session_state.pop("text_q_override", None) or text_q

    q = sb.table("listings").select("*").eq("status","active")
    if city_q != "All": q = q.eq("city", city_q)
    if type_q: q = q.in_("ltype", type_q)
    rows = q.order("created_at", desc=True).execute().data

    if _text_q:
        t = _text_q.lower()
        rows = [r for r in rows if t in (" ".join([(r.get("title") or ""),(r.get("franchise") or ""),(r.get("character") or "")] )).lower()]

    if st.session_state.user and st.button("⭐ Save this search"):
        sb.table("saved_searches").insert({
            "user_id": st.session_state.user.id,
            "city": None if city_q=="All" else city_q,
            "ltypes": type_q or ["rent","sell","commission"],
            "query": _text_q or ""
        }).execute()
        st.toast("Saved! You'll see alerts here when new listings match.")

    cols = st.columns(3)
    for i, it in enumerate(rows[:60]):
        with cols[i%3]:
            st.subheader(it.get("title","Untitled"))
            if it.get("images"): st.image(it["images"][0], use_container_width=True)
            price_text = f"₹{int(it.get('price') or 0)}" + ("/day" if it.get("price_unit")=="day" else "")
            st.caption(f"{it.get('ltype','').title()} • {price_text} • {it.get('city') or '-'}")
            st.write(f"**Franchise:** {it.get('franchise') or '-'}  |  **Character:** {it.get('character') or '-'}")

# ----------------- Post Listing -----------------
with post:
    if not st.session_state.user:
        st.info("Sign in to post.")
    else:
        title=st.text_input("Title *")
        ltype=st.selectbox("Type *",["rent","sell","commission"])
        price=st.number_input("Price (₹) *",min_value=0,step=50)
        price_unit=st.selectbox("Price unit *", ["fixed","day"], index=0 if ltype!="rent" else 1)
        city=st.text_input("City *")
        desc=st.text_area("Description *")
        uploads=st.file_uploader("Images (up to 5)",type=["png","jpg","jpeg"],accept_multiple_files=True)

        auto_context=desc or ""
        caption=""
        if uploads:
            caption=hf_caption(uploads[0].getvalue())
            if caption:
                auto_context += "\n" + caption  # <-- fixed unterminated string
                st.caption(f"AI image hint: {caption}")
        guessed=guess_franchise_from_text(auto_context) if auto_context else []
        options=guessed+[x for x in FRANCHISE_CANDIDATES if x not in guessed]
        franchise=st.selectbox("Franchise (auto)",options, index=0 if guessed else options.index("Naruto"))

        # Character auto-suggest
        char_sugs=suggest_characters(franchise,auto_context)
        char_options=(char_sugs or ["Naruto Uzumaki","Sasuke Uchiha"]) + ["Other (type below)"]
        character_sel=st.selectbox("Character (suggested)",char_options)
        character=st.text_input("Or type character") if character_sel=="Other (type below)" else character_sel

        # AI helpers
        c1,c2 = st.columns(2)
        with c1:
            if st.button("✍️ Write with AI", use_container_width=True):
                out = write_with_ai(title, franchise, character, ltype, True)
                st.session_state.ai_desc = out
        with c2:
            if st.button("🏷️ Auto-tag", use_container_width=True):
                base = f"{title} {franchise} {character} {desc} {caption}"
                st.session_state.tags = auto_tags(base)
                st.toast(", ".join(st.session_state.tags) or "No tags")
        if st.session_state.get("ai_desc"):
            desc = st.text_area("AI Description", st.session_state.ai_desc, height=140)

        st.markdown("### Terms & Safety")
        st.write("This platform **does not** handle delivery, payments, or escrow. Arrange directly and keep proofs.")
        agree = st.checkbox("I understand and agree to the terms *")

        def upload_images_to_storage(files, owner_id):
            urls = []
            for f in files[:5]:
                image = Image.open(f).convert("RGB")
                buf = io.BytesIO()
                image.save(buf, format="JPEG", quality=85)
                buf.seek(0)
                path = f"{owner_id}/{uuid.uuid4().hex}.jpg"
                sb.storage.from_("listing-images").upload(path, buf.getvalue(), {"content-type": "image/jpeg"})
                urls.append(sb.storage.from_("listing-images").get_public_url(path))
            return urls

        if st.button("Publish", use_container_width=True):
            if not all([title, ltype, city, desc]) or price is None or not agree:
                st.error("Fill all required fields and agree to terms.")
            else:
                uid=st.session_state.user.id
                image_urls = upload_images_to_storage(uploads, uid) if uploads else []
                data={
                    "owner":uid,
                    "ltype":ltype,
                    "title":title,
                    "price":int(price),
                    "price_unit":price_unit,
                    "city":city,
                    "description":desc,
                    "franchise":franchise,
                    "character":character,
                    "tags": st.session_state.get("tags", []),
                    "images": image_urls,
                    "quantity": 1,
                    "status":"active"
                }
                sb.table("listings").insert(data).execute()
                st.success("Listing published!")
                st.session_state.pop("ai_desc", None)
                st.session_state.pop("tags", None)
                st.rerun()

# ----------------- Saved Searches -----------------
with saved:
    if not st.session_state.user:
        st.info("Sign in to save searches.")
    else:
        uid=st.session_state.user.id
        st.subheader("My Saved Searches")
        q_city=st.text_input("City filter")
        q_types=st.multiselect("Types",["rent","sell","commission"],["rent","sell","commission"])
        q_text=st.text_input("Keyword filter")
        if st.button("Save this search"):
            sb.table("saved_searches").insert({
                "user_id":uid,
                "city":None if not q_city else q_city,
                "ltypes":q_types,
                "query":q_text
            }).execute()
            st.success("Saved! You'll see alerts on Browse when new listings match.")

        saved_list=sb.table("saved_searches").select("*").eq("user_id",uid).execute().data
        for s in saved_list:
            st.write(f"🔎 {s.get('query') or 'Any'} — {s.get('city') or 'All cities'} — {', '.join(s.get('ltypes') or [])}")
            if st.button("Delete",key=f"del{s['id']}"):
                sb.table("saved_searches").delete().eq("id",s['id']).execute()
                st.rerun()

# ----------------- Footer -----------------
st.markdown("---")
st.write("⚠️ Rent-a-Cos does not provide delivery or payments. Users arrange their own transactions securely.")
