import streamlit as st, datetime as dt
from lib.sb import sb_client

def render_browse_tab():
    sb = sb_client()
    colf1, colf2, colf3 = st.columns([1,1,2])
    cities = ["All","Bengaluru","Mumbai","Delhi","Hyderabad","Pune","Kolkata","Chennai","Remote"]
    city_q = colf1.selectbox("City", cities, index=0)
    type_q = colf2.multiselect("Type", ["rent","sell","commission"], default=["rent","sell","commission"])
    text_q = colf3.text_input("Search title / franchise / character")

    if st.session_state.user:
        uid = st.session_state.user.id
        saved_rows = sb.table("saved_searches").select("*").eq("user_id", uid).order("created_at", desc=True).execute().data
        if saved_rows:
            with st.expander("🔔 Saved search alerts"):
                for s in saved_rows:
                    q = sb.table("listings").select("id,title,franchise,character,city,ltype,created_at") \
                        .eq("status","active").gte("created_at", s.get("last_seen"))
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
