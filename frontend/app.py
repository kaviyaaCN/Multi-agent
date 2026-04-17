"""
frontend/app.py
===============
Multi-Agent AI Academic Project Assistant — Streamlit Frontend
==============================================================
A premium, light-themed UI organized as a guided multi-step workflow.
Each step corresponds to one agent in the pipeline.
"""

import sys
from pathlib import Path

# ── Ensure project root is on PYTHONPATH ──────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from streamlit.components.v1 import html as st_html

# ── Page configuration (MUST be first Streamlit call) ─────────────────────────
st.set_page_config(
    page_title="AI Academic Project Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "Report a bug": "https://github.com",
        "About": "Multi-Agent AI Academic Project Assistant v1.0",
    },
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary:   #f9fafb;
    --bg-secondary: #ffffff;
    --bg-card:      #ffffff;
    --bg-hover:     #f3f4f6;
    --accent:       #6d28d9;
    --accent-light: #8b5cf6;
    --accent-glow:  rgba(109, 40, 217, 0.2);
    --green:        #059669;
    --amber:        #d97706;
    --red:          #dc2626;
    --blue:         #2563eb;
    --text-primary:   #111827;
    --text-secondary: #4b5563;
    --border:         #e5e7eb;
    --radius:         12px;
    --radius-lg:      16px;
}

/* ── Base ── */
html, body, .stApp {
    background-color: var(--bg-primary) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }
.stDeployButton { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* ── Cards ── */
.agent-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color .2s, box-shadow .2s;
}
.agent-card:hover {
    border-color: var(--accent);
    box-shadow: 0 0 20px var(--accent-glow);
}

/* ── Step badge ── */
.step-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px; height: 32px;
    background: linear-gradient(135deg, var(--accent), #6d28d9);
    border-radius: 50%;
    font-weight: 700;
    font-size: 0.85rem;
    color: white;
    margin-right: 0.6rem;
}

/* ── Section headers ── */
.section-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
}
.section-sub {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-bottom: 1.2rem;
}

/* ── Metric pill ── */
.metric-pill {
    display: inline-block;
    background: var(--bg-hover);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-right: 0.5rem;
}

/* ── Topic card ── */
.topic-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    cursor: pointer;
    transition: background .15s, border-color .15s;
}
.topic-card:hover { background: var(--bg-hover); border-color: var(--accent-light); }
.topic-card .topic-title  { font-weight: 600; font-size: 1rem; color: var(--text-primary); }
.topic-card .topic-desc   { font-size: 0.82rem; color: var(--text-secondary); margin-top: .3rem; }
.topic-card .tech-tag {
    display: inline-block;
    background: rgba(124,58,237,.18);
    color: var(--accent-light);
    border-radius: 4px;
    padding: .1rem .4rem;
    font-size: 0.72rem;
    margin-right: .3rem;
    margin-top: .4rem;
}

/* ── Code block ── */
.code-block {
    background: #f1f5f9;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    overflow-x: auto;
    color: #0f172a;
    max-height: 500px;
    overflow-y: auto;
}

/* ── Score bar ── */
.score-bar-wrap { margin: 0.75rem 0; }
.score-bar-label { font-size: 0.82rem; color: var(--text-secondary); margin-bottom: .3rem; }
.score-bar-bg {
    background: var(--bg-hover);
    border-radius: 8px;
    height: 10px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width .6s ease;
}

/* ── Slide card (Gamma-like Theme) ── */
.slide-card {
    background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    padding: 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: transform .2s, box-shadow .2s;
}
.slide-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(109, 40, 217, 0.15);
    border-color: #8b5cf6;
}
.slide-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 6px; height: 100%;
    background: linear-gradient(to bottom, #8b5cf6, #3b82f6);
}
.slide-num { font-size: .75rem; color: #6d28d9; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.slide-title { font-size: 1.25rem; font-weight: 800; color: #111827; margin: .5rem 0 .75rem; letter-spacing: -0.01em; }
.slide-bullet { font-size: .9rem; color: #4b5563; margin: .4rem 0; line-height: 1.4; display: flex; align-items: flex-start; }
.slide-bullet::before { content: "❖ "; color: #6d28d9; margin-right: 0.5rem; font-size: 0.8rem; padding-top: 0.1rem; }

/* ── Progress indicator ── */
.pipeline-step {
    display: flex;
    align-items: center;
    padding: .5rem .75rem;
    border-radius: 8px;
    margin-bottom: .3rem;
    font-size: .85rem;
}
.pipeline-step.done    { background: rgba(16,185,129,.1); color: #6ee7b7; }
.pipeline-step.active  { background: rgba(124,58,237,.15); color: var(--accent-light); }
.pipeline-step.pending { color: var(--text-secondary); }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent), #6d28d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: .9rem !important;
    padding: .5rem 1.2rem !important;
    transition: opacity .2s, transform .1s !important;
}
.stButton > button:hover { opacity: .88 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* Outline button variant */
div[data-testid*="secondary"] > .stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}

/* ── Form inputs ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > div > textarea {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}
.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 8px !important;
    padding: .25rem !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    border-radius: 6px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* ── Alerts ── */
.stSuccess { background: rgba(16,185,129,.1) !important; border-left-color: var(--green) !important; }
.stWarning { background: rgba(245,158,11,.1) !important; border-left-color: var(--amber) !important; }
.stError   { background: rgba(239,68,68,.1)  !important; border-left-color: var(--red)   !important; }
.stInfo    { background: rgba(59,130,246,.1)  !important; border-left-color: var(--blue)  !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Session state bootstrap
# ═══════════════════════════════════════════════════════════════════════════════

def _init_state() -> None:
    """Initialise Streamlit session state with default values."""
    defaults = {
        "orchestrator": None,
        "step": 0,                  # 0=setup, 1=topics, 2=select, 3=docs, 4=code, 5=plag, 6=ppt
        "topics": [],
        "selected_topic": None,
        "documentation": None,
        "generated_code": None,
        "plagiarism_report": None,
        "presentation": None,
        "rag_ready": False,
        "api_key_set": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def get_orchestrator():
    """Return the singleton AgentOrchestrator, creating it if needed."""
    if st.session_state.orchestrator is None:
        from agents.orchestrator import AgentOrchestrator
        st.session_state.orchestrator = AgentOrchestrator()
    return st.session_state.orchestrator


def _score_color(score: float) -> str:
    if score < 0.20:  return "#10b981"
    if score < 0.40:  return "#f59e0b"
    if score < 0.60:  return "#f97316"
    return "#ef4444"


def _pill(text: str) -> str:
    return f'<span class="metric-pill">{text}</span>'


def _render_pipeline_sidebar() -> None:
    """Render the pipeline progress tracker in the sidebar."""
    steps = [
        ("⚙️", "Setup & API Key"),
        ("💡", "Topic Suggestions"),
        ("🎯", "Select Topic"),
        ("📄", "Generate Documentation"),
        ("💻", "Generate Code"),
        ("🔍", "Plagiarism Check"),
        ("📊", "Generate Presentation"),
    ]
    st.sidebar.markdown("### 🔄 Pipeline Progress")
    current = st.session_state.step
    for i, (icon, label) in enumerate(steps):
        if i < current:
            cls = "done";    icon_s = "✅"
        elif i == current:
            cls = "active";  icon_s = icon
        else:
            cls = "pending"; icon_s = icon
        st.sidebar.markdown(
            f'<div class="pipeline-step {cls}">{icon_s} &nbsp; {label}</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📘 About")
    st.sidebar.info(
        "Multi-Agent AI Academic Project Assistant\n\n"
        "Automates your full project lifecycle:\n"
        "Topic → Docs → Code → Check → Slides"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Step 0: Setup
# ═══════════════════════════════════════════════════════════════════════════════

def render_setup() -> None:
    # Hero banner
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <div style="font-size:4rem; margin-bottom:.5rem;">🎓</div>
        <h1 style="font-size:2.4rem; font-weight:800; background:linear-gradient(135deg,#a78bfa,#7c3aed);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;">
            AI Academic Project Assistant
        </h1>
        <p style="color:#8b949e; font-size:1.05rem; margin-top:.5rem;">
            Multi-Agent System • RAG • LLM-Powered • End-to-End Automation
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="agent-card" style="text-align:center;">
            <div style="font-size:2rem">💡</div>
            <div style="font-weight:600;margin:.4rem 0;">4 AI Agents</div>
            <div style="color:#8b949e;font-size:.82rem;">Topic • Docs • Code • PPT</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="agent-card" style="text-align:center;">
            <div style="font-size:2rem">🧠</div>
            <div style="font-weight:600;margin:.4rem 0;">RAG Pipeline</div>
            <div style="color:#8b949e;font-size:.82rem;">FAISS · sentence-transformers</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="agent-card" style="text-align:center;">
            <div style="font-size:2rem">📊</div>
            <div style="font-weight:600;margin:.4rem 0;">Full Lifecycle</div>
            <div style="color:#8b949e;font-size:.82rem;">Topic → Slides, auto-generated</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Status panel — keys loaded from .env, no UI input needed ────────────
    from utils.config import settings as cfg

    st.markdown("""<div class="section-title">
        <span class="step-badge">1</span> System Status
    </div>
    <div class="section-sub">API keys and model are loaded automatically from your <code>.env</code> file</div>
    """, unsafe_allow_html=True)

    key_count = len(cfg.groq_api_keys)
    if key_count == 0:
        st.error(
            "⚠️ **No Groq API keys found in `.env`.**\n\n"
            "Add at least one key to your `.env` file:\n"
            "```\nGROQ_API_KEY_1=your_key_here\n```\n"
            "Get a free key at: https://console.groq.com/keys"
        )
        return

    col_k, col_m = st.columns([2, 1])
    with col_k:
        st.markdown("**🔑 API Key Pool**")
        for i, key in enumerate(cfg.groq_api_keys, 1):
            masked = f"****{key[-6:]}" if len(key) > 6 else "****"
            st.markdown(
                f'<div class="pipeline-step done">✅ &nbsp; Key #{i} — <code>{masked}</code></div>',
                unsafe_allow_html=True,
            )
        if key_count > 1:
            st.info(
                f"🔄 **{key_count} keys configured** — automatic rotation active. "
                "If one key hits its rate limit, the next is used automatically."
            )
        else:
            st.warning(
                "Only 1 key configured. Add `GROQ_API_KEY_2`, `GROQ_API_KEY_3`… "
                "to `.env` for seamless rate-limit rotation."
            )

    with col_m:
        st.markdown("**🧬 Model**")
        st.markdown(
            f'<div class="pipeline-step done">✅ &nbsp; <code>{cfg.groq_model}</code></div>',
            unsafe_allow_html=True,
        )
        st.markdown("**📦 Embedding**")
        st.markdown(
            f'<div class="pipeline-step done">✅ &nbsp; <code>{cfg.embedding_model}</code></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**📚 Knowledge Base (optional)**")
    ingest_docs = st.checkbox(
        "Index documents in `data/documents/` for RAG",
        value=False,
        help="Place academic PDFs or TXTs in data/documents/ first, then enable this.",
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Launch Assistant", use_container_width=True):
        with st.spinner("🔨 Initialising agents…"):
            try:
                from utils import llm_client as llmc
                llmc._cache.clear()
                llmc.get_llm_client.cache_clear()
                orch = get_orchestrator()
                if ingest_docs:
                    orch.initialise_rag()
                    st.session_state.rag_ready = True
                st.session_state.api_key_set = True
                st.session_state.step = 1
                st.success("✅ System ready! Proceed to Topic Suggestion →")
                st.rerun()
            except Exception as exc:
                st.error(f"Initialisation failed: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# Step 1: Topic Suggestion
# ═══════════════════════════════════════════════════════════════════════════════

def render_topic_input() -> None:
    st.markdown("""<div class="section-title">
        <span class="step-badge">2</span> Project Topic Suggestion
    </div>
    <div class="section-sub">
        Tell the AI about your academic interests and get personalised project topic ideas
    </div>""", unsafe_allow_html=True)

    with st.form("topic_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            domain = st.selectbox("🏛️ Domain", [ "Artificial Intelligence",
                "Machine Learning", "Deep Learning", "Natural Language Processing",
                "Computer Vision", "Data Science", "Web Development",
                "Cybersecurity", "Cloud Computing", "IoT", "Blockchain",
            ])
        with col2:
            interest = st.text_input("🎯 Specific Interest",
                placeholder="e.g. Sentiment Analysis, Object Detection…")
        with col3:
            difficulty = st.select_slider(
                "📈 Difficulty",
                options=["Beginner", "Intermediate", "Advanced"],
                value="Intermediate",
            )

        count = st.slider("Number of topic suggestions", 5, 10, 7)
        generate = st.form_submit_button("💡 Generate Topics", use_container_width=True)

    if generate:
        if not interest.strip():
            st.warning("Please enter a specific interest area.")
            return

        orch = get_orchestrator()
        orch.set_user_context(domain=domain, interest=interest, difficulty=difficulty)

        with st.spinner("🤖 Topic Agent is thinking…"):
            try:
                topics = orch.run_topic_agent(count=count)
                st.session_state.topics = topics
                st.session_state.step = 2
                st.rerun()
            except Exception as exc:
                st.error(f"Topic generation failed: {exc}")
                st.code(str(exc))

    # Show topics if available
    if st.session_state.topics:
        render_topic_list()


def render_topic_list() -> None:
    st.markdown("### 💡 Suggested Topics")
    st.markdown(
        f"*{len(st.session_state.topics)} topics generated — click one to select it*",
    )

    for topic in st.session_state.topics:
        tech_tags = " ".join(f'<span class="tech-tag">{t}</span>' for t in topic.technologies[:4])
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"""
            <div class="topic-card">
                <div class="topic-title">#{topic.id} &nbsp; {topic.title}</div>
                <div class="topic-desc">{topic.description}</div>
                <div style="margin-top:.5rem">{tech_tags}</div>
                <div style="margin-top:.5rem; font-size:.78rem; color:#6d40d9;">
                    📈 {topic.difficulty} &nbsp;|&nbsp; 🎯 {topic.expected_outcome[:80]}…
                </div>
            </div>""", unsafe_allow_html=True)
        with col2:
            if st.button("Select →", key=f"sel_{topic.id}"):
                orch = get_orchestrator()
                orch.select_topic(topic)
                st.session_state.selected_topic = topic
                st.session_state.step = 3
                st.success(f"✅ Selected: {topic.title}")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# Step 3: Documentation
# ═══════════════════════════════════════════════════════════════════════════════

def render_documentation() -> None:
    topic = st.session_state.selected_topic
    st.markdown(f"""<div class="section-title">
        <span class="step-badge">3</span> Documentation Generator
    </div>
    <div class="section-sub">Generating full 13-section MCA project report for: <strong>{topic.title}</strong></div>
    """, unsafe_allow_html=True)

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        tech_tags = " ".join(f'<span class="metric-pill">{t}</span>' for t in topic.technologies)
        st.markdown(f"Technologies: {tech_tags}", unsafe_allow_html=True)
    with col_btn:
        generate = st.button("📄 Generate Report", use_container_width=True,
                             disabled=st.session_state.documentation is not None)

    # Section list (must match agent order)
    _SECTION_LABELS = [
        ("abstract",             "Abstract"),
        ("introduction",         "Introduction"),
        ("system_architecture",  "System Architecture"),
        ("methodology",          "Methodology"),
        ("implementation",       "Implementation"),
        ("conclusion",           "Conclusion"),
    ]

    if generate and st.session_state.documentation is None:
        orch = get_orchestrator()
        progress_bar = st.progress(0)
        status_box   = st.empty()

        with st.spinner("📝 Documentation Agent writing your 6-section core report…"):
            try:
                # Animate progress label section-by-section
                total = len(_SECTION_LABELS)
                for i, (_, label) in enumerate(_SECTION_LABELS):
                    status_box.markdown(
                        f"<div style='color:#a78bfa;font-size:.9rem;'>✍️ Writing: <b>{label}</b> "
                        f"({i+1}/{total})</div>",
                        unsafe_allow_html=True,
                    )
                    progress_bar.progress((i) / total)

                doc = orch.run_documentation_agent()
                st.session_state.documentation = doc
                st.session_state.step = 4
                progress_bar.progress(1.0)
                status_box.success("✅ Full 6-section report generated!")
                st.rerun()
            except Exception as exc:
                progress_bar.empty()
                status_box.empty()
                st.error(f"Documentation generation failed: {exc}")

    if st.session_state.documentation:
        doc = st.session_state.documentation

        # ── Detect stale document ──
        # Since we reduced to 6 sections, no need to show this warning aggressively 
        # for standard missing new fields. We only care if 'conclusion' is missing.
        is_stale = not hasattr(doc, "conclusion")

        if is_stale:
            st.warning(
                "⚠️ **This report is out of sync.** "
                "Click **Reset & Re-generate** to create the new 6-section core report."
            )
            if st.button("🔄 Reset & Re-generate Report", use_container_width=True):
                st.session_state.documentation = None
                st.session_state.step = 3
                st.rerun()
            return  # Don't try to display the stale doc

        # ── Download buttons at top ───────────────────────────────────────────
        col_md, col_doc = st.columns(2)
        
        with col_md:
            full_text = doc.to_full_text()
            st.download_button(
                "📥 Download Markdown (.md)",
                data=full_text,
                file_name=f"{topic.title.replace(' ', '_')}_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
            
        with col_doc:
            try:
                docx_bytes = doc.to_docx()
                st.download_button(
                    "📥 Download Word Document (.docx)",
                    data=docx_bytes,
                    file_name=f"{topic.title.replace(' ', '_')}_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            except Exception as e:
                st.error("DOCX download not available")

        col_reset, _ = st.columns([1, 3])
        with col_reset:
            if st.button("🔄 Reset & Re-generate", key="doc_reset"):
                st.session_state.documentation = None
                st.session_state.step = 3
                st.rerun()

        # ── 14 tabs: 13 sections + Full Report ───────────────────────────────
        tab_names = [label for _, label in _SECTION_LABELS] + ["📄 Full Report"]
        tabs = st.tabs(tab_names)

        for i, (field_name, label) in enumerate(_SECTION_LABELS):
            with tabs[i]:
                if field_name == "references":
                    refs = getattr(doc, "references", [])
                    if refs:
                        for j, ref in enumerate(refs, 1):
                            st.markdown(f"`[{j}]` {ref}")
                    else:
                        st.warning(
                            "⚠️ References section is empty. "
                            "Click **Reset & Re-generate** above to rebuild the report."
                        )
                else:
                    content = getattr(doc, field_name, None)
                    if content and not str(content).startswith("[Section could not"):
                        st.markdown(content)
                    elif content and str(content).startswith("[Section could not"):
                        st.error(f"❌ Generation failed for this section: {content}")
                        st.info("Click **Reset & Re-generate** above to retry.")
                    else:
                        # Truly empty — section was not generated
                        st.warning(
                            f"⚠️ **{label}** section is empty — "
                            "this usually means the report was generated before this "
                            "section was added. Click **Reset & Re-generate** above."
                        )

        # Full report tab
        with tabs[-1]:
            st.markdown(full_text)



# ═══════════════════════════════════════════════════════════════════════════════
# Step 4: Code Generator
# ═══════════════════════════════════════════════════════════════════════════════

def render_code() -> None:
    topic = st.session_state.selected_topic
    st.markdown(f"""<div class="section-title">
        <span class="step-badge">4</span> Code Generator
    </div>
    <div class="section-sub">Generating executable Python implementation for: <strong>{topic.title}</strong></div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        generate = st.button("💻 Generate Code", use_container_width=True,
                             disabled=st.session_state.generated_code is not None)

    if generate and st.session_state.generated_code is None:
        orch = get_orchestrator()
        with st.spinner("⚙️ Code Agent building your implementation…"):
            try:
                code = orch.run_code_agent()
                st.session_state.generated_code = code
                st.session_state.step = 5
                st.rerun()
            except Exception as exc:
                st.error(f"Code generation failed: {exc}")

    if st.session_state.generated_code:
        code_obj = st.session_state.generated_code

        tab1, tab2, tab3 = st.tabs(["📦 main.py", "📖 Explanation", "📁 File Structure"])

        with tab1:
            col_dl, _ = st.columns([1, 3])
            with col_dl:
                st.download_button(
                    "📥 Download main.py",
                    data=code_obj.code,
                    file_name="main.py",
                    mime="text/plain",
                )
            st.code(code_obj.code, language="python", line_numbers=True)

        with tab2:
            st.markdown(code_obj.explanation)
            st.markdown("---")
            st.markdown(code_obj.run_instructions)

        with tab3:
            for filename, purpose in code_obj.file_structure.items():
                if filename != "main.py":
                    st.markdown(f"📄 **`{filename}`** — {purpose}")
                else:
                    st.markdown(f"🟢 **`{filename}`** — Main execution script (generated above)")


# ═══════════════════════════════════════════════════════════════════════════════
# Step 5: Plagiarism Checker
# ═══════════════════════════════════════════════════════════════════════════════

def render_plagiarism() -> None:
    st.markdown("""<div class="section-title">
        <span class="step-badge">5</span> Plagiarism Checker
    </div>
    <div class="section-sub">Semantic similarity check using FAISS embeddings</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        check_target = st.radio(
            "What to check?",
            ["Generated Documentation (Abstract + Introduction)", "Paste custom text"],
            horizontal=True,
        )
    with col2:
        run_check = st.button("🔍 Run Check", use_container_width=True,
                              disabled=st.session_state.plagiarism_report is not None)

    custom_text = ""
    if check_target == "Paste custom text":
        custom_text = st.text_area("Paste text to check…", height=150,
                                   placeholder="Paste your paragraph here…")

    if run_check and st.session_state.plagiarism_report is None:
        orch = get_orchestrator()
        text = custom_text if custom_text.strip() else None

        if check_target == "Paste custom text" and not custom_text.strip():
            st.warning("Please paste some text to check.")
            return

        with st.spinner("🔍 Analysing semantic similarity…"):
            try:
                report = orch.run_plagiarism_agent(text=text)
                st.session_state.plagiarism_report = report
                st.session_state.step = 6
                st.rerun()
            except Exception as exc:
                st.error(f"Plagiarism check failed: {exc}")

    if st.session_state.plagiarism_report:
        r = st.session_state.plagiarism_report
        score = r.overall_score
        color = _score_color(score)

        # Score display
        col_score, col_verdict = st.columns([1, 2])
        with col_score:
            st.markdown(f"""
            <div class="agent-card" style="text-align:center;">
                <div style="font-size:2.8rem; font-weight:800; color:{color};">
                    {score*100:.1f}%
                </div>
                <div style="color:#8b949e; margin-top:.3rem;">Similarity Score</div>
                <div class="score-bar-wrap">
                    <div class="score-bar-bg">
                        <div class="score-bar-fill"
                             style="width:{score*100:.1f}%; background:{color};"></div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        with col_verdict:
            st.markdown(f"""
            <div class="agent-card">
                <div style="font-size:1.2rem; font-weight:700; margin-bottom:.5rem;">
                    {r.verdict}
                </div>
                <div style="color:#8b949e; font-size:.88rem;">{r.summary}</div>
            </div>""", unsafe_allow_html=True)

        # Top matches
        if r.top_matches:
            with st.expander(f"📋 Top Matching Passages ({len(r.top_matches)})"):
                for i, m in enumerate(r.top_matches[:5], 1):
                    st.markdown(f"**Match {i}** — Score: `{m['score']:.2%}` | Source: `{m['source']}`")
                    st.markdown(f"> {m['text'][:250]}…")
                    st.divider()

        # Re-run option
        if st.button("🔄 Check Different Text"):
            st.session_state.plagiarism_report = None
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# Step 6: PPT Generator
# ═══════════════════════════════════════════════════════════════════════════════

def render_ppt() -> None:
    topic = st.session_state.selected_topic
    st.markdown(f"""<div class="section-title">
        <span class="step-badge">6</span> Presentation Generator
    </div>
    <div class="section-sub">Converting documentation into structured slides for: <strong>{topic.title}</strong></div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        generate = st.button("📊 Generate Slides", use_container_width=True,
                             disabled=st.session_state.presentation is not None)

    if generate and st.session_state.presentation is None:
        orch = get_orchestrator()
        with st.spinner("🎨 PPT Agent designing your presentation…"):
            try:
                ppt = orch.run_ppt_agent()
                st.session_state.presentation = ppt
                st.session_state.step = 7
                st.rerun()
            except Exception as exc:
                st.error(f"Presentation generation failed: {exc}")

    if st.session_state.presentation:
        ppt = st.session_state.presentation
        st.markdown(f"✅ **{len(ppt.slides)} slides generated**")

        # Slide cards
        cols = st.columns(2)
        for i, slide in enumerate(ppt.slides):
            with cols[i % 2]:
                bullets_html = "\n".join(
                    f'<div class="slide-bullet">{b}</div>' for b in slide.bullets
                )
                type_icon = {"title": "🎨", "content": "📋", "section": "🔷", "conclusion": "🏁"}.get(
                    slide.slide_type, "📋"
                )
                st.markdown(f"""
                <div class="slide-card">
                    <div class="slide-num">{type_icon} SLIDE {slide.slide_number}</div>
                    <div class="slide-title">{slide.title}</div>
                    {bullets_html}
                </div>""", unsafe_allow_html=True)

                if slide.speaker_notes:
                    with st.expander("🎤 Speaker Notes"):
                        st.markdown(f"*{slide.speaker_notes}*")

        # Export
        st.markdown("---")
        col_exp, _ = st.columns([1, 2])
        with col_exp:
            if st.button("📥 Export as .pptx", use_container_width=True):
                orch = get_orchestrator()
                with st.spinner("Creating .pptx file…"):
                    try:
                        path = orch.export_pptx()
                        with open(path, "rb") as f:
                            st.download_button(
                                "⬇️ Download Presentation",
                                data=f,
                                file_name=path.name,
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True,
                            )
                        st.success(f"PPTX ready: {path.name}")
                    except Exception as exc:
                        st.error(f"Export failed: {exc}")

        # Text outline download
        st.download_button(
            "📝 Download Slide Outline (.txt)",
            data=ppt.summary(),
            file_name=f"{topic.title.replace(' ', '_')}_slides.txt",
            mime="text/plain",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Navigation
# ═══════════════════════════════════════════════════════════════════════════════

def render_nav() -> None:
    """Bottom back/reset navigation bar."""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.session_state.step > 0:
            if st.button("← Back"):
                st.session_state.step = max(0, st.session_state.step - 1)
                st.rerun()
    with col3:
        if st.button("🔄 Start Over"):
            _init_state()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# Main Router
# ═══════════════════════════════════════════════════════════════════════════════

_render_pipeline_sidebar()

step = st.session_state.step

if step == 0:
    render_setup()
elif step == 1:
    render_topic_input()
elif step == 2:
    render_topic_input()    # Still on topic page, showing list
elif step >= 3:
    # Show selected topic header
    if st.session_state.selected_topic:
        topic = st.session_state.selected_topic
        st.markdown(f"""
        <div style="background:rgba(124,58,237,.1); border:1px solid rgba(124,58,237,.3);
                    border-radius:10px; padding:.75rem 1rem; margin-bottom:1.5rem;
                    display:flex; align-items:center; gap:.75rem;">
            <span style="font-size:1.3rem">🎯</span>
            <div>
                <div style="font-weight:700; font-size:1rem">{topic.title}</div>
                <div style="color:#8b949e; font-size:.8rem">
                    {" • ".join(topic.technologies[:4])} • {topic.difficulty}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Sub-step tabs
    tab_labels = ["📄 Documentation", "💻 Code", "🔍 Plagiarism", "📊 Presentation"]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        render_documentation()
    with tabs[1]:
        render_code()
    with tabs[2]:
        render_plagiarism()
    with tabs[3]:
        render_ppt()

render_nav()
