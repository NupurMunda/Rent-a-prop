import streamlit as st
from lib.sb import sb_client

def render_saved_tab():
    sb = sb_client()
    try:
        uid = st.session_state.user.id
    except Exception:
        st.info("Sign in to save searches.")
        return

    st.subheader("My Saved Searches")

    # Create new saved search
    q_city = st.text_input("City filter", help="Leave blank for all cities")
    q_types = st.multiselect("Types", ["rent", "sell", "commission"], ["rent", "sell", "commission"])
    q_text = st.text_input("Keyword filter", help="Matches title, franchise, or character text")

    if st.button("Save this search"):
        try:
            sb.table("saved_searches").insert({
                "user_id": uid,
                "city": None if not q_city else q_city,
                "ltypes": q_types or ["rent", "sell", "commission"],
                "query": q_text or "",
            }).execute()
            st.success("Saved! You'll see alerts on Browse when new listings match.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not save search: {e}")

    # List saved searches
    try:
        saved_list = sb.table("saved_searches").select("*").eq("user_id", uid).order("created_at", desc=True).execute().data
    except Exception as e:
        st.error(f"Failed to load saved searches: {e}")
        return

    if not saved_list:
        st.info("No saved searches yet.")
        return

    for s in saved_list:
        with st.container(border=True):
            st.write(f"🔎 **{s.get('query') or 'Any'}** — **{s.get('city') or 'All cities'}** — {', '.join(s.get('ltypes') or [])}")
            cols = st.columns([1, 1])
            with cols[0]:
                if st.button("Set as active filter", key=f"apply_{s['id']}"):
                    # Pass the query back to Browse tab via session override
                    if s.get("query"):
                        st.session_state["text_q_override"] = s.get("query")
                    st.success("Applied! Go to Browse to see results.")
            with cols[1]:
                if st.button("Delete", key=f"del_{s['id']}"):
                    try:
                        sb.table("saved_searches").delete().eq("id", s['id']).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")
