"""
ui/app.py — Streamlit UI for Meeting Intelligence Platform
Premium glassmorphism design
"""
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Meeting Intelligence", page_icon="🎙️", layout="wide")

# ── Premium CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 40%, #1c2333 100%);
}
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2rem; }
header[data-testid="stHeader"] { background: transparent; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #0a0e14 100%) !important;
    border-right: 1px solid rgba(56,189,248,0.1);
}
section[data-testid="stSidebar"] .stMarkdown { color: #c9d1d9; }

.hero {
    text-align: center; padding: 40px 20px 20px 20px;
}
.hero h1 {
    font-size: 3rem; font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 8px; letter-spacing: -1px;
}
.hero p { color: #8b949e; font-size: 1.15rem; font-weight: 300; }

.glass {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(56,189,248,0.1);
    border-radius: 16px; padding: 24px; margin: 12px 0; color: #c9d1d9;
}

.metric-glass {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56,189,248,0.1);
    border-radius: 14px; padding: 20px; text-align: center;
}
.metric-glass .value {
    font-size: 2rem; font-weight: 700;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.metric-glass .label { color: #8b949e; font-size: 0.85rem; margin-top: 4px; }

.action-item {
    background: rgba(52,211,153,0.06);
    border-left: 4px solid #34d399;
    padding: 14px 18px; margin: 8px 0; border-radius: 8px;
    color: #a7f3d0; transition: transform 0.2s ease;
}
.action-item:hover { transform: translateX(4px); }

.decision-item {
    background: rgba(251,191,36,0.06);
    border-left: 4px solid #fbbf24;
    padding: 14px 18px; margin: 8px 0; border-radius: 8px;
    color: #fde68a; transition: transform 0.2s ease;
}
.decision-item:hover { transform: translateX(4px); }

.question-item {
    background: rgba(248,113,113,0.06);
    border-left: 4px solid #f87171;
    padding: 14px 18px; margin: 8px 0; border-radius: 8px;
    color: #fca5a5; transition: transform 0.2s ease;
}
.question-item:hover { transform: translateX(4px); }

.sentiment-positive { color: #34d399; font-weight: 700; }
.sentiment-negative { color: #f87171; font-weight: 700; }
.sentiment-neutral  { color: #8b949e; font-weight: 700; }
.sentiment-mixed    { color: #fbbf24; font-weight: 700; }

.summary-box {
    background: rgba(56,189,248,0.06);
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 12px; padding: 18px; color: #c9d1d9;
    line-height: 1.7;
}

.participants-bar {
    background: rgba(129,140,248,0.08);
    border: 1px solid rgba(129,140,248,0.2);
    border-radius: 10px; padding: 10px 16px;
    color: #a5b4fc; font-size: 0.95em;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.02); border-radius: 12px; padding: 4px; gap: 4px;
}
.stTabs [data-baseweb="tab"] { border-radius: 8px; color: #8b949e; font-weight: 500; }
.stTabs [aria-selected="true"] {
    background: rgba(56,189,248,0.15) !important; color: #7dd3fc !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #38bdf8, #818cf8) !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; transition: all 0.3s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(56,189,248,0.3) !important;
}

.stTextArea textarea, .stTextInput input {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(56,189,248,0.12) !important;
    border-radius: 10px !important; color: #c9d1d9 !important;
}

.streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 8px !important; color: #8b949e !important;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🎙️ Meeting Intelligence</h1>
    <p>Transform meeting transcripts into structured insights — action items, decisions, summaries & search</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎙️ Analytics")
    st.caption("Meeting processing stats")
    st.divider()
    try:
        requests.get(f"{API_URL}/health", timeout=5)
        st.success("🟢 API Connected")
        s = requests.get(f"{API_URL}/stats", timeout=5).json()
        st.metric("Meetings Processed", s.get("meetings_processed", 0))
        st.metric("Action Items Found", s.get("total_action_items", 0))
        st.metric("Indexed Meetings",   s.get("indexed_meetings", 0))
    except Exception:
        st.error("🔴 API Offline — run: make run")
        st.stop()
    st.divider()
    st.caption("Built with OpenAI · FastAPI · Streamlit")

tab_analyze, tab_search, tab_digest = st.tabs(["📝 Analyze Transcript", "🔍 Search History", "📧 Email Digest"])

# ── ANALYZE TAB ───────────────────────────────────────────────────────────
with tab_analyze:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("#### 📝 Analyze a Meeting Transcript")

    col1, col2 = st.columns([3, 1])
    with col1:
        meeting_title = st.text_input("Meeting Title", placeholder="Q3 Planning Meeting")
    with col2:
        input_method = st.radio("Input", ["Paste text", "Upload file"], horizontal=True)

    if input_method == "Paste text":
        transcript = st.text_area(
            "Paste transcript here",
            height=300,
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
        uploaded = st.file_uploader("Upload .txt transcript", type=["txt"])
        transcript = None
    st.markdown('</div>', unsafe_allow_html=True)

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

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    f'<div class="metric-glass"><div class="value">{len(r.get("action_items", []))}</div>'
                    f'<div class="label">Action Items</div></div>',
                    unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    f'<div class="metric-glass"><div class="value">{len(r.get("decisions", []))}</div>'
                    f'<div class="label">Decisions</div></div>',
                    unsafe_allow_html=True
                )
            with c3:
                st.markdown(
                    f'<div class="metric-glass"><div class="value">{len(r.get("open_questions", []))}</div>'
                    f'<div class="label">Open Questions</div></div>',
                    unsafe_allow_html=True
                )
            with c4:
                sent = r.get("sentiment", "neutral")
                sent_cls = f"sentiment-{sent}"
                st.markdown(
                    f'<div class="metric-glass"><div class="value" '
                    f'style="-webkit-text-fill-color:unset"><span class="{sent_cls}">'
                    f'{sent.upper()}</span></div><div class="label">Sentiment</div></div>',
                    unsafe_allow_html=True
                )

            participants = r.get("participants", [])
            if participants:
                st.markdown(
                    f'<div class="participants-bar">👥 <b>Attendees:</b> {" · ".join(participants)}</div>',
                    unsafe_allow_html=True
                )

            st.markdown("#### 📋 Summary")
            st.markdown(
                f'<div class="summary-box">{r.get("summary", "No summary available.")}</div>',
                unsafe_allow_html=True
            )

            actions = r.get("action_items", [])
            if actions:
                st.markdown(f"#### ✅ Action Items ({len(actions)})")
                for a in actions:
                    owner = f" — <b>@{a['owner']}</b>" if a.get("owner") else ""
                    due = f" <i>(due {a['due_date']})</i>" if a.get("due_date") else ""
                    prio = f" <code>{a['priority'].upper()}</code>" if a.get("priority", "medium") != "medium" else ""
                    st.markdown(
                        f'<div class="action-item">☐ {a["description"]}{owner}{due}{prio}</div>',
                        unsafe_allow_html=True
                    )

            decisions = r.get("decisions", [])
            if decisions:
                st.markdown(f"#### 🏛️ Decisions Made ({len(decisions)})")
                for d in decisions:
                    by = f" <i>(by {d['made_by']})</i>" if d.get("made_by") else ""
                    st.markdown(
                        f'<div class="decision-item">✅ {d["description"]}{by}</div>',
                        unsafe_allow_html=True
                    )

            questions = r.get("open_questions", [])
            if questions:
                st.markdown(f"#### ❓ Open Questions ({len(questions)})")
                for q in questions:
                    st.markdown(f'<div class="question-item">❓ {q}</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("#### 🔍 Search Meeting History")
    st.caption("Find answers across all your past meetings")

    query = st.text_input("Search query", placeholder="What did we decide about the Q4 roadmap?")
    top_k = st.slider("Results", 1, 10, 5)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔍 Search", type="primary", use_container_width=True):
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
                        m = item["meeting"]
                        score = item["score"]
                        with st.expander(
                            f"📅 {m.get('title', 'Untitled')} — score: {score:.3f}", expanded=(i == 0)
                        ):
                            st.write(m.get("summary", ""))
                            actions = m.get("action_items", [])
                            if actions:
                                st.markdown(f"**{len(actions)} action items** — "
                                           + ", ".join(a.get("description", "")[:40]
                                                       for a in actions[:3]))
            else:
                st.error(f"Search failed: {resp.text}")

# ── DIGEST TAB ────────────────────────────────────────────────────────────
with tab_digest:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("#### 📧 Email / Slack Digest")
    st.caption("Get a formatted digest ready to share")
    st.markdown('</div>', unsafe_allow_html=True)

    try:
        s = requests.get(f"{API_URL}/stats", timeout=5).json()
        n = s.get("indexed_meetings", 0)
        if n == 0:
            st.info("No meetings analyzed yet. Go to the Analyze tab first.")
        else:
            idx = st.number_input("Meeting index (0 = most recent)", 0, max(0, n - 1), 0)
            if st.button("📧 Generate Digest", type="primary"):
                resp = requests.get(f"{API_URL}/digest/{idx}", timeout=30)
                if resp.ok:
                    digest = resp.json().get("digest", "")
                    st.markdown("#### Preview")
                    st.markdown(digest)
                    st.download_button("⬇️ Download as Markdown", digest,
                                       file_name=f"meeting_digest_{idx}.md",
                                       mime="text/markdown")
                else:
                    st.error("Failed to generate digest.")
    except Exception:
        st.warning("Could not load meeting count.")
