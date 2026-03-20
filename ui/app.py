"""
ui/app.py — Streamlit UI for Meeting Intelligence Platform
"""
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Meeting Intelligence", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
.action-item {
    background:#f0fff4; border-left:4px solid #28a745;
    padding:10px 14px; margin:5px 0; border-radius:4px;
}
.decision-item {
    background:#fff3cd; border-left:4px solid #ffc107;
    padding:10px 14px; margin:5px 0; border-radius:4px;
}
.question-item {
    background:#fff5f5; border-left:4px solid #dc3545;
    padding:10px 14px; margin:5px 0; border-radius:4px;
}
.sentiment-positive { color:#28a745; font-weight:bold; }
.sentiment-negative { color:#dc3545; font-weight:bold; }
.sentiment-neutral  { color:#6c757d; font-weight:bold; }
.sentiment-mixed    { color:#fd7e14; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎙️ Meeting Intel")
    st.caption("Turn transcripts into structured insights")
    st.divider()
    try:
        requests.get(f"{API_URL}/health", timeout=5)
        st.success("🟢 API Connected")
        s = requests.get(f"{API_URL}/stats", timeout=5).json()
        st.metric("Meetings Processed", s.get("meetings_processed", 0))
        st.metric("Action Items Found", s.get("total_action_items", 0))
        st.metric("Indexed Meetings",   s.get("indexed_meetings", 0))
    except:
        st.error("🔴 API Offline — run: make run")
        st.stop()

tab_analyze, tab_search, tab_digest = st.tabs(["📝 Analyze", "🔍 Search", "📧 Digest"])

# ── ANALYZE TAB ───────────────────────────────────────────────────────────
with tab_analyze:
    st.header("Analyze a Meeting Transcript")

    col1, col2 = st.columns([3, 1])
    with col1:
        meeting_title = st.text_input("Meeting Title", placeholder="Q3 Planning Meeting")
    with col2:
        input_method = st.radio("Input", ["Paste text", "Upload file"], horizontal=True)

    if input_method == "Paste text":
        transcript = st.text_area(
            "Paste transcript here",
            height=350,
            placeholder="""Sarah: Let's start the planning meeting.
James: I think we should prioritize the onboarding redesign this quarter.
Lisa: Agreed. Let's make that priority one. James, can you write a scope doc by Friday?
James: Yes, will do.
Sarah: The reporting dashboard moves to Q4 — it's too large for Q3.
Tom: I'll own the API rate limit increase. I can have it done by end of September.
Lisa: Great. Next check-in is October 16th."""
        )
        uploaded = None
    else:
        uploaded  = st.file_uploader("Upload .txt transcript", type=["txt"])
        transcript = None

    if st.button("⚡ Extract Insights", type="primary", use_container_width=True):
        with st.spinner("Analyzing transcript..."):
            if uploaded:
                resp = requests.post(
                    f"{API_URL}/analyze/upload",
                    files={"file": (uploaded.name, uploaded.read(), "text/plain")},
                    data={"title": meeting_title or uploaded.name},
                    timeout=120,
                )
            elif transcript and transcript.strip():
                resp = requests.post(f"{API_URL}/analyze", json={
                    "transcript": transcript,
                    "title": meeting_title or "Meeting",
                }, timeout=120)
            else:
                st.warning("Please provide a transcript.")
                st.stop()

        if resp.ok:
            r = resp.json()
            st.session_state["last_result"] = r

            # Header metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Action Items",  len(r.get("action_items", [])))
            c2.metric("Decisions",     len(r.get("decisions", [])))
            c3.metric("Open Questions",len(r.get("open_questions", [])))
            sent = r.get("sentiment", "neutral")
            sent_cls = f"sentiment-{sent}"
            c4.markdown(f"**Sentiment**<br><span class='{sent_cls}'>{sent.upper()}</span>",
                        unsafe_allow_html=True)

            # Participants
            participants = r.get("participants", [])
            if participants:
                st.markdown(f"**Attendees:** {' · '.join(participants)}")

            # Summary
            st.markdown("### 📋 Summary")
            st.info(r.get("summary", "No summary available."))

            # Action items
            actions = r.get("action_items", [])
            if actions:
                st.markdown(f"### ✅ Action Items ({len(actions)})")
                for a in actions:
                    owner   = f" — **@{a['owner']}**" if a.get("owner") else ""
                    due     = f" _(due {a['due_date']})_" if a.get("due_date") else ""
                    prio    = f" `{a['priority'].upper()}`" if a.get("priority","medium") != "medium" else ""
                    st.markdown(
                        f'<div class="action-item">☐ {a["description"]}{owner}{due}{prio}</div>',
                        unsafe_allow_html=True
                    )

            # Decisions
            decisions = r.get("decisions", [])
            if decisions:
                st.markdown(f"### 🏛️ Decisions Made ({len(decisions)})")
                for d in decisions:
                    by = f" _(by {d['made_by']})_" if d.get("made_by") else ""
                    st.markdown(
                        f'<div class="decision-item">✅ {d["description"]}{by}</div>',
                        unsafe_allow_html=True
                    )

            # Open questions
            questions = r.get("open_questions", [])
            if questions:
                st.markdown(f"### ❓ Open Questions ({len(questions)})")
                for q in questions:
                    st.markdown(f'<div class="question-item">❓ {q}</div>', unsafe_allow_html=True)

            # Topics + next meeting
            col_t, col_n = st.columns(2)
            with col_t:
                topics = r.get("topics", [])
                if topics:
                    st.markdown(f"**Topics:** {' · '.join(topics)}")
            with col_n:
                next_m = r.get("next_meeting")
                if next_m:
                    st.markdown(f"**Next meeting:** {next_m}")

            with st.expander("📋 Raw JSON"):
                st.json(r)
        else:
            st.error(f"Analysis failed: {resp.text}")

# ── SEARCH TAB ────────────────────────────────────────────────────────────
with tab_search:
    st.header("Search Meeting History")
    st.caption("Find answers across all your past meetings")

    query = st.text_input("Search query",
                          placeholder="What did we decide about the Q4 roadmap?")
    top_k = st.slider("Results", 1, 10, 5)

    if st.button("🔍 Search", type="primary"):
        if not query.strip():
            st.warning("Enter a search query.")
        else:
            resp = requests.post(f"{API_URL}/search",
                                 json={"query": query, "top_k": top_k}, timeout=30)
            if resp.ok:
                results = resp.json().get("results", [])
                if not results:
                    st.info("No meetings found. Analyze some transcripts first.")
                else:
                    for i, item in enumerate(results):
                        m     = item["meeting"]
                        score = item["score"]
                        with st.expander(
                            f"📅 {m.get('title','Untitled')} — score: {score:.3f}", expanded=(i==0)
                        ):
                            st.write(m.get("summary",""))
                            actions = m.get("action_items", [])
                            if actions:
                                st.markdown(f"**{len(actions)} action items** — "
                                           + ", ".join(a.get("description","")[:40]
                                                       for a in actions[:3]))
            else:
                st.error(f"Search failed: {resp.text}")

# ── DIGEST TAB ────────────────────────────────────────────────────────────
with tab_digest:
    st.header("Email / Slack Digest")
    st.caption("Get a formatted digest ready to send")

    try:
        s    = requests.get(f"{API_URL}/stats", timeout=5).json()
        n    = s.get("indexed_meetings", 0)
        if n == 0:
            st.info("No meetings analyzed yet. Go to the Analyze tab first.")
        else:
            idx  = st.number_input("Meeting index (0 = most recent)", 0, max(0, n-1), 0)
            if st.button("📧 Generate Digest"):
                resp = requests.get(f"{API_URL}/digest/{idx}", timeout=30)
                if resp.ok:
                    digest = resp.json().get("digest", "")
                    st.markdown("### Preview")
                    st.markdown(digest)
                    st.download_button("⬇️ Download as Markdown", digest,
                                       file_name=f"meeting_digest_{idx}.md",
                                       mime="text/markdown")
                else:
                    st.error("Failed to generate digest.")
    except:
        st.warning("Could not load meeting count.")
