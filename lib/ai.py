# lib/ai.py
import streamlit as st, requests

from lib.constants import FRANCHISE_CANDIDATES, POPULAR_CHARACTERS

@st.cache_data(show_spinner=False)
def write_with_ai(title, franchise, character, ltype, handmade):
    HF_TOKEN = st.secrets.get("HF_TOKEN","")
    if not HF_TOKEN: return "Add HF_TOKEN in Streamlit secrets to enable AI."
    url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3.1-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = (f"Write an 80-120 word marketplace listing for a cosplay item.\n"
              f"Title: {title}\nFranchise: {franchise}\nCharacter: {character}\n"
              f"Type: {ltype}. Handmade: {handmade}. Include fit, sizing, materials, condition, who it suits.")
    try:
        r = requests.post(url, headers=headers, json={"inputs": prompt, "parameters":{"max_new_tokens":200}}, timeout=60)
        js = r.json()
        if isinstance(js, list) and js and "generated_text" in js[0]:
            return js[0]["generated_text"].strip()
    except Exception:
        pass
    return "AI is busy. Try again."

@st.cache_data(show_spinner=False)
def auto_tags(text):
    HF_TOKEN = st.secrets.get("HF_TOKEN","")
    if not HF_TOKEN: return []
    url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    labels = ["anime","manga","cosplay","prop","weapon","costume","figure","collectible","handmade","official",
              "wig","accessory","Naruto","One Piece","Attack on Titan","My Hero Academia","Demon Slayer","Dragon Ball","Bleach"]
    try:
        r = requests.post(url, headers=headers, json={"inputs": text, "parameters":{"candidate_labels": labels}}, timeout=60)
        out = r.json()
        return [lbl for lbl,score in zip(out.get("labels",[]), out.get("scores",[])) if score>0.35][:12]
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def hf_caption(image_bytes: bytes) -> str:
    HF_TOKEN = st.secrets.get("HF_TOKEN","")
    if not HF_TOKEN: return ""
    url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Accept":"application/json"}
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
    HF_TOKEN = st.secrets.get("HF_TOKEN","")
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
    HF_TOKEN = st.secrets.get("HF_TOKEN","")
    if not HF_TOKEN or not text: return []
    url = "https://api-inference.huggingface.co/models/dslim/bert-base-NER"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        r = requests.post(url, headers=headers, json={"inputs": text}, timeout=60)
        names=[]
        for ent in r.json():
            if isinstance(ent, dict) and ent.get("entity_group") == "PER" and ent.get("score",0)>0.80:
                names.append(ent.get("word"))
    except Exception:
        names=[]
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
