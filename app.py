# app.py
# ─────────────────────────────────────────────────────────────────────────────
# SkillSync AI – Phase 1: Resume Analyzer (Full Deep Analysis Edition)
#
# Features:
#   - PDF upload (Resume + Job Description)
#   - Semantic similarity via sentence-transformers (all-MiniLM-L6-v2)
#   - Score tier system with industry context + confidence messaging
#   - "Why this score" breakdown (strengths + specific gap reasons)
#   - Domain inference mapping (candidate vs JD domains)
#   - Per-project JD relevance scoring
#   - Section-level JD relevance scores
#   - Experience highlights
#   - Prioritised action plan (High / Medium / Polish)
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st

st.set_page_config(
    page_title="SkillSync AI – Resume Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: #0F0F1A;
    color: #E2E8F0;
}
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse at 20% 10%, rgba(124,58,237,0.18) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(59,130,246,0.12) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(16,185,129,0.06) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}
[data-testid="stMainBlockContainer"] {
    position: relative;
    z-index: 1;
    padding: 2rem 3rem !important;
}
[data-testid="stSidebar"] {
    background: rgba(26,26,46,0.95) !important;
    border-right: 1px solid rgba(124,58,237,0.2) !important;
    backdrop-filter: blur(20px);
}

/* ── Hero ── */
.hero-header { text-align:center; padding:2.5rem 1rem 1.5rem; margin-bottom:2rem; }
.hero-header .badge {
    display:inline-block;
    background:linear-gradient(135deg,rgba(124,58,237,0.3),rgba(59,130,246,0.3));
    border:1px solid rgba(124,58,237,0.5);
    border-radius:100px; padding:0.3rem 1rem;
    font-size:0.75rem; font-weight:600; letter-spacing:0.1em;
    text-transform:uppercase; color:#C4B5FD; margin-bottom:1rem;
}
.hero-header h1 {
    font-size:3rem; font-weight:800;
    background:linear-gradient(135deg,#A78BFA,#60A5FA,#34D399);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; line-height:1.15; margin:0 0 0.75rem;
}
.hero-header p { font-size:1.1rem; color:#94A3B8; max-width:580px; margin:0 auto; line-height:1.6; }

/* ── Glass card ── */
.glass-card {
    background:rgba(26,26,46,0.6); backdrop-filter:blur(20px);
    -webkit-backdrop-filter:blur(20px);
    border:1px solid rgba(124,58,237,0.2); border-radius:20px;
    padding:1.75rem; margin-bottom:1.5rem;
    transition:border-color 0.3s ease, box-shadow 0.3s ease;
}
.glass-card:hover {
    border-color:rgba(124,58,237,0.45);
    box-shadow:0 8px 40px rgba(124,58,237,0.12);
}
.glass-card h3 {
    font-size:1rem; font-weight:600; color:#C4B5FD;
    margin:0 0 0.5rem; display:flex; align-items:center; gap:0.5rem;
}
.glass-card p { font-size:0.85rem; color:#64748B; margin:0; }

/* ── Score ring ── */
.score-container { display:flex; flex-direction:column; align-items:center;
    justify-content:center; padding:1.5rem; text-align:center; }
.score-ring-wrap { position:relative; width:190px; height:190px; margin:0 auto 1rem; }
.score-ring-wrap svg { transform:rotate(-90deg); }
.score-ring-wrap .score-text { position:absolute; inset:0; display:flex;
    flex-direction:column; align-items:center; justify-content:center; }
.score-ring-wrap .score-number { font-size:2.6rem; font-weight:800; line-height:1; }
.score-ring-wrap .score-label { font-size:0.65rem; font-weight:600; color:#64748B;
    text-transform:uppercase; letter-spacing:0.08em; margin-top:0.25rem; }
.tier-badge {
    display:inline-block; padding:0.35rem 1.1rem; border-radius:100px;
    font-size:0.82rem; font-weight:700; letter-spacing:0.04em; margin-bottom:0.6rem;
}
.score-headline { font-size:1rem; font-weight:600; margin-bottom:0.35rem; }
.score-confidence { font-size:0.8rem; color:#94A3B8; line-height:1.55; max-width:340px; }

/* ── Industry scale ── */
.industry-scale { margin:1.2rem 0 0; }
.scale-track {
    position:relative; height:10px; background:rgba(255,255,255,0.06);
    border-radius:100px; overflow:visible; margin:0.5rem 0 0.35rem;
}
.scale-segment { position:absolute; top:0; height:100%; }
.scale-marker {
    position:absolute; top:-18px;
    font-size:0.6rem; color:#475569; transform:translateX(-50%);
    white-space:nowrap;
}
.scale-needle {
    position:absolute; top:-5px; width:2px; height:20px;
    background:#fff; border-radius:2px;
    box-shadow:0 0 8px rgba(255,255,255,0.6);
}
.scale-labels { display:flex; justify-content:space-between;
    font-size:0.6rem; color:#475569; margin-top:0.25rem; }

/* ── Skill chips ── */
.skill-chip {
    display:inline-block; padding:0.3rem 0.75rem; border-radius:100px;
    font-size:0.78rem; font-weight:500; margin:0.2rem;
    transition:transform 0.2s ease;
}
.skill-chip:hover { transform:translateY(-2px); }
.chip-matched { background:rgba(52,211,153,0.13); border:1px solid rgba(52,211,153,0.38); color:#6EE7B7; }
.chip-missing { background:rgba(239,68,68,0.10); border:1px solid rgba(239,68,68,0.33); color:#FCA5A5; }
.chip-extra   { background:rgba(96,165,250,0.10); border:1px solid rgba(96,165,250,0.33); color:#93C5FD; }
.chip-neutral { background:rgba(167,139,250,0.10); border:1px solid rgba(167,139,250,0.3); color:#C4B5FD; }
.chip-freq    { background:rgba(124,58,237,0.1); border:1px solid rgba(124,58,237,0.3); color:#C4B5FD; display:inline-block; padding:0.25rem 0.65rem; border-radius:8px; font-size:0.75rem; font-weight:500; margin:0.2rem; }

/* ── Section header ── */
.section-header { display:flex; align-items:center; gap:0.6rem; margin-bottom:1rem; }
.section-header h2 { font-size:1.15rem; font-weight:700; color:#E2E8F0; margin:0; }
.section-header .count-badge {
    background:rgba(124,58,237,0.25); border:1px solid rgba(124,58,237,0.4);
    border-radius:100px; padding:0.1rem 0.55rem;
    font-size:0.72rem; font-weight:600; color:#C4B5FD;
}

/* ── Stat bar ── */
.stat-bar-wrap { margin:0.55rem 0; }
.stat-bar-label { display:flex; justify-content:space-between;
    font-size:0.8rem; color:#94A3B8; margin-bottom:0.28rem; }
.stat-bar-track { height:8px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
.stat-bar-fill { height:100%; border-radius:100px; }

/* ── Why-score items ── */
.why-item {
    display:flex; align-items:flex-start; gap:0.65rem;
    padding:0.65rem 0.8rem; border-radius:12px; margin-bottom:0.5rem;
    font-size:0.83rem; line-height:1.55;
}
.why-strength { background:rgba(52,211,153,0.08); border:1px solid rgba(52,211,153,0.2); }
.why-gap      { background:rgba(239,68,68,0.07); border:1px solid rgba(239,68,68,0.2); }
.why-item .why-emoji { font-size:1rem; flex-shrink:0; margin-top:0.05rem; }
.why-item .why-text  { color:#94A3B8; }
.why-item .why-text strong { color:#E2E8F0; }

/* ── Domain bars ── */
.domain-bar-row { margin-bottom:0.6rem; }
.domain-bar-label { display:flex; justify-content:space-between;
    font-size:0.78rem; color:#94A3B8; margin-bottom:0.2rem; }
.domain-bar-track { height:7px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
.domain-bar-fill  { height:100%; border-radius:100px; }

/* ── Project card ── */
.project-card {
    padding:1rem 1.1rem; border-radius:14px; margin-bottom:0.85rem;
    background:rgba(255,255,255,0.025);
    border:1px solid rgba(124,58,237,0.15);
    transition:border-color 0.25s ease;
}
.project-card:hover { border-color:rgba(124,58,237,0.35); }
.project-title { font-weight:700; color:#E2E8F0; font-size:0.92rem; margin-bottom:0.3rem; }
.project-desc  { font-size:0.78rem; color:#64748B; margin-bottom:0.55rem; line-height:1.5; }
.project-relevance-label { font-size:0.72rem; color:#94A3B8; margin-bottom:0.2rem;
    display:flex; justify-content:space-between; }

/* ── Action plan cards ── */
.action-card {
    padding:0.9rem 1rem; border-radius:14px; margin-bottom:0.6rem;
    font-size:0.82rem; line-height:1.6; color:#94A3B8;
}
.action-card strong { color:#E2E8F0; }
.action-high   { background:rgba(239,68,68,0.07); border:1px solid rgba(239,68,68,0.25); }
.action-medium { background:rgba(251,191,36,0.07); border:1px solid rgba(251,191,36,0.25); }
.action-polish { background:rgba(96,165,250,0.07); border:1px solid rgba(96,165,250,0.25); }
.action-priority-label {
    font-size:0.66rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.08em; margin-bottom:0.35rem;
}

/* ── Divider ── */
.custom-divider {
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(124,58,237,0.4),transparent);
    margin:2rem 0; border:none;
}

/* ── Streamlit overrides ── */
.stFileUploader {
    border:1px dashed rgba(124,58,237,0.4) !important;
    border-radius:16px !important;
    background:rgba(124,58,237,0.05) !important;
}
div[data-testid="stFileUploaderDropzone"] { background:transparent !important; }
.stButton > button {
    background:linear-gradient(135deg,#7C3AED,#4F46E5) !important;
    color:white !important; border:none !important; border-radius:12px !important;
    font-weight:600 !important; font-family:'Inter',sans-serif !important;
    font-size:1rem !important; padding:0.75rem 2rem !important; width:100% !important;
    transition:all 0.3s ease !important;
    box-shadow:0 4px 20px rgba(124,58,237,0.3) !important;
}
.stButton > button:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 8px 30px rgba(124,58,237,0.5) !important;
}
#MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
import re
from utils.parser          import extract_text_from_pdf
from utils.similarity      import get_embedding, calculate_cosine_similarity
from utils.skill_extractor import extract_skills, compare_skills, infer_implied_skills, get_jd_skill_frequencies
from utils.resume_analyzer import analyze_resume, get_section_scores
from utils.topic_analyzer  import get_domain_alignment
from utils.feedback_engine import (
    get_score_tier,
    score_project_against_jd,
    generate_why_score,
    generate_action_plan,
    SCORE_TIERS,
)


# ─────────────────────────────────────────────────────────────────────────────
# UI Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def render_score_ring(score: float, tier: dict) -> str:
    """Render SVG circular progress ring with dynamic colour from tier."""
    radius = 84
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference - (score / 100) * circumference
    color = tier["color"]
    gradient_end = tier.get("gradient", "").split(",")[-1].strip().rstrip(")")
    return f"""
    <div class="score-container">
        <div class="score-ring-wrap">
            <svg width="190" height="190" viewBox="0 0 190 190">
                <defs>
                    <linearGradient id="rg" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color}"/>
                        <stop offset="100%" style="stop-color:{gradient_end or color}"/>
                    </linearGradient>
                </defs>
                <circle cx="95" cy="95" r="{radius}" fill="none"
                    stroke="rgba(255,255,255,0.06)" stroke-width="11"/>
                <circle cx="95" cy="95" r="{radius}" fill="none"
                    stroke="url(#rg)" stroke-width="11" stroke-linecap="round"
                    stroke-dasharray="{circumference:.2f}"
                    stroke-dashoffset="{dash_offset:.2f}"/>
            </svg>
            <div class="score-text">
                <div class="score-number" style="color:{color}">{score:.0f}%</div>
                <div class="score-label">Match Score</div>
            </div>
        </div>
    </div>
    """


def render_breakdown_row(label: str, score: float, color: str) -> str:
    """Render a horizontal progress bar for a breakdown score."""
    return f"""
    <div style="margin-bottom:0.6rem; font-size:0.78rem;">
        <div style="display:flex; justify-content:space-between; margin-bottom:0.15rem; color:#94A3B8;">
            <span>{label}</span>
            <span style="font-weight:600; color:{color};">{score:.0f}%</span>
        </div>
        <div style="height:5px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden;">
            <div style="height:100%; width:{min(score, 100):.1f}%; background:{color}; border-radius:100px;"></div>
        </div>
    </div>
    """


def render_industry_scale(score: float) -> str:
    """
    Render a horizontal scale showing where the score falls
    across the six tier bands with a needle indicator.
    """
    # Segment boundaries and colours
    segments = [
        (0,  20,  "#64748B"),
        (20, 35,  "#EF4444"),
        (35, 50,  "#F97316"),
        (50, 65,  "#FBBF24"),
        (65, 80,  "#34D399"),
        (80, 100, "#10B981"),
    ]
    seg_html = ""
    labels_html = ""
    for lo, hi, color in segments:
        left = lo
        width = hi - lo
        seg_html += (
            f'<div class="scale-segment" '
            f'style="left:{left}%;width:{width}%;'
            f'background:{color};opacity:0.35;border-radius:2px;"></div>'
        )
    # Needle at score position
    needle_left = min(max(score, 1), 99)
    seg_html += (
        f'<div class="scale-needle" style="left:{needle_left:.1f}%;'
        f'transform:translateX(-50%);"></div>'
    )
    # Tick labels
    ticks = [(0,"0%"),(20,"20%"),(35,"35%"),(50,"50%"),(65,"65%"),(80,"80%"),(100,"100%")]
    for pos, label in ticks:
        seg_html += (
            f'<div class="scale-marker" style="left:{pos}%;">{label}</div>'
        )
    tier_names = ["Different", "Early", "Developing", "Good", "Strong", "Exceptional"]
    label_cells = "".join(f'<span>{n}</span>' for n in tier_names)
    return f"""
    <div class="industry-scale">
        <div style="font-size:0.72rem;color:#475569;margin-bottom:0.4rem;">
            📊 Industry Score Context — where you stand
        </div>
        <div class="scale-track">{seg_html}</div>
        <div class="scale-labels" style="margin-top:0.85rem;">{label_cells}</div>
        <div style="font-size:0.72rem;color:#475569;margin-top:0.6rem;line-height:1.5;">
            ⬆ Most shortlisted candidates score <strong style="color:#E2E8F0;">45–70%</strong>.
            A perfect 100% match is extremely rare and not expected.
        </div>
    </div>
    """


def render_skill_chips(skills: list, chip_class: str) -> str:
    """Render a list of skill strings as coloured pill chips."""
    if not skills:
        return "<p style='color:#475569;font-size:0.82rem;font-style:italic;'>None found</p>"
    return "".join(
        f'<span class="skill-chip {chip_class}">{s.title()}</span>'
        for s in skills
    )


def render_stat_bar(label: str, value: int, total: int, color: str) -> str:
    """Render a labelled progress bar."""
    pct = (value / total * 100) if total > 0 else 0
    return f"""
    <div class="stat-bar-wrap">
        <div class="stat-bar-label"><span>{label}</span><span>{value}/{total}</span></div>
        <div class="stat-bar-track">
            <div class="stat-bar-fill" style="width:{pct:.1f}%;background:{color};"></div>
        </div>
    </div>
    """


def render_domain_bar(domain: str, score: float, color: str, icon: str = "🔷") -> str:
    """Render a single domain proficiency bar."""
    return f"""
    <div class="domain-bar-row">
        <div class="domain-bar-label">
            <span>{icon} {domain}</span>
            <span style="font-weight:600;color:#E2E8F0;">{score:.0f}%</span>
        </div>
        <div class="domain-bar-track">
            <div class="domain-bar-fill" style="width:{score:.1f}%;background:{color};border-radius:100px;"></div>
        </div>
    </div>
    """


def md_to_html(text: str) -> str:
    """Convert **bold** markdown to HTML <strong> tags for inline display."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 1.5rem;">
        <div style="font-size:3rem;">🎯</div>
        <h2 style="margin:0.5rem 0 0.25rem;font-size:1.3rem;font-weight:700;color:#E2E8F0;">
            SkillSync AI</h2>
        <p style="font-size:0.8rem;color:#64748B;margin:0;">Phase 1 · Deep Resume Analyzer</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 📖 How It Works")
    st.markdown("""
    <div style="font-size:0.85rem;color:#94A3B8;line-height:1.8;">
    <ol style="padding-left:1.2rem;margin:0;">
        <li>Upload your <strong style="color:#C4B5FD;">Resume PDF</strong></li>
        <li>Upload the <strong style="color:#60A5FA;">Job Description PDF</strong></li>
        <li>Click <strong style="color:#34D399;">Analyze Match</strong></li>
        <li>Get your full deep analysis</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 📊 What's Analyzed")
    st.markdown("""
    <div style="font-size:0.82rem;color:#64748B;line-height:1.9;">
        <div>🎯 Overall semantic match score</div>
        <div>🏷️ Skill-by-skill comparison</div>
        <div>🗺️ Domain knowledge profiling</div>
        <div>🚀 Per-project JD relevance</div>
        <div>📑 Resume section analysis</div>
        <div>📋 Experience highlights</div>
        <div>✅ Personalized action plan</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 🤖 Model")
    st.markdown("""
    <div style="font-size:0.82rem;color:#64748B;line-height:1.7;">
        <div>📦 <strong style="color:#A78BFA;">all-MiniLM-L6-v2</strong></div>
        <div>🔢 384-dim embeddings</div>
        <div>🛠️ pdfplumber + PyPDF2</div>
        <div>🎯 150+ skills · 10 domains</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem;color:#334155;text-align:center;">
        SkillSync AI v1.1 · Built with Streamlit
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Hero Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="badge">✨ AI-Powered Deep Resume Analysis</div>
    <h1>SkillSync AI</h1>
    <p>Full analysis of your resume — skills, projects, experience, domain knowledge —
    compared against the job description with confidence-aware scoring.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Upload Section
# ─────────────────────────────────────────────────────────────────────────────
col_r, col_j = st.columns(2, gap="large")

with col_r:
    st.markdown("""
    <div class="glass-card">
        <h3>📄 Your Resume</h3>
        <p>Upload your resume PDF for deep analysis</p>
    </div>""", unsafe_allow_html=True)
    resume_file = st.file_uploader("Resume", type=["pdf"], key="resume_up",
                                   label_visibility="collapsed")
    if resume_file:
        st.markdown(f"""
        <div style="margin-top:0.75rem;padding:0.6rem 1rem;
            background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);
            border-radius:10px;font-size:0.83rem;color:#6EE7B7;">
            ✅ &nbsp;<strong>{resume_file.name}</strong> ({resume_file.size/1024:.1f} KB)
        </div>""", unsafe_allow_html=True)

with col_j:
    st.markdown("""
    <div class="glass-card">
        <h3>💼 Job Description</h3>
        <p>Upload the job description PDF you're targeting</p>
    </div>""", unsafe_allow_html=True)
    jd_file = st.file_uploader("JD", type=["pdf"], key="jd_up",
                                label_visibility="collapsed")
    if jd_file:
        st.markdown(f"""
        <div style="margin-top:0.75rem;padding:0.6rem 1rem;
            background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.3);
            border-radius:10px;font-size:0.83rem;color:#93C5FD;">
            ✅ &nbsp;<strong>{jd_file.name}</strong> ({jd_file.size/1024:.1f} KB)
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    analyze_clicked = st.button("🚀  Analyze My Resume",
                                 disabled=(resume_file is None or jd_file is None))

if not resume_file or not jd_file:
    st.markdown("""
    <div style="text-align:center;margin-top:1rem;color:#475569;font-size:0.85rem;">
        ⬆️  Please upload both PDFs to enable analysis
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Analysis Pipeline
# ─────────────────────────────────────────────────────────────────────────────
if analyze_clicked and resume_file and jd_file:

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # Step 1: Extract text
    with st.spinner("📄 Extracting text from PDFs..."):
        resume_text = extract_text_from_pdf(resume_file)
        jd_text     = extract_text_from_pdf(jd_file)

    if not resume_text.strip():
        st.error("❌ Could not extract text from the Resume PDF. "
                 "Please ensure it contains selectable (non-scanned) text.")
        st.stop()
    if not jd_text.strip():
        st.error("❌ Could not extract text from the Job Description PDF.")
        st.stop()

    # Step 2: Deep section + project analysis
    with st.spinner("🔬 Analysing resume sections, projects & experience..."):
        deep_analysis  = analyze_resume(resume_text, jd_text)
        section_scores = get_section_scores(deep_analysis["section_texts"], jd_text)

    # Step 3: Skill extraction + comparison
    with st.spinner("🔍 Extracting and comparing skills..."):
        from assets.skills_database import SOFT_SKILLS
        soft_skills_set = {s.lower() for s in SOFT_SKILLS}

        # Extract base resume skills, infer implied skills from context, and filter out soft skills
        raw_resume_skills = extract_skills(resume_text)
        inferred_skills   = infer_implied_skills(resume_text)
        resume_skills     = (raw_resume_skills | inferred_skills) - soft_skills_set

        # Extract JD skills and filter out soft skills
        jd_skills         = extract_skills(jd_text) - soft_skills_set
        skill_report      = compare_skills(resume_skills, jd_skills)

    matched_skills  = skill_report["matched"]
    missing_skills  = skill_report["missing"]
    extra_skills    = skill_report["extra"]
    total_jd_skills = len(jd_skills)

    # Calculate JD keyword frequencies
    jd_frequencies = get_jd_skill_frequencies(jd_text, jd_skills)

    # Group missing skills into priority buckets based on JD mention frequency
    critical_missing  = []
    important_missing = []
    optional_missing  = []
    for skill in missing_skills:
        freq = jd_frequencies.get(skill, 1)
        if freq >= 3:
            critical_missing.append(skill)
        elif freq == 2:
            important_missing.append(skill)
        else:
            optional_missing.append(skill)

    # Step 4: Calculate Weighted Match Score & Component Breakdown
    skills_score     = (len(matched_skills) / len(jd_skills) * 100) if jd_skills else 100.0
    experience_score = section_scores.get("experience", 0.0)
    projects_score   = section_scores.get("projects", 0.0)
    education_score  = section_scores.get("education", 0.0)

    raw_weighted_score = 0.4 * skills_score + 0.2 * experience_score + 0.4 * projects_score
    # Apply +12% score boost, capped at 99.0%
    match_score = min(raw_weighted_score + 12.0, 99.0)

    # Step 5: Domain Inference Mapping
    with st.spinner("🗺️ Mapping technical domains..."):
        domain_alignment = get_domain_alignment(resume_skills, jd_skills)

    # Step 6: Feedback generation (fast, rule-based)
    tier         = get_score_tier(match_score)
    why_score    = generate_why_score(
        match_score, matched_skills, missing_skills,
        domain_alignment, deep_analysis, jd_skills,
    )
    action_plan  = generate_action_plan(
        missing_skills, domain_alignment, match_score,
        deep_analysis["projects"], jd_skills, matched_skills,
    )

    # Score each project against JD
    projects = deep_analysis.get("projects", [])
    project_scores = [
        (proj, *score_project_against_jd(proj, jd_skills))
        for proj in projects
    ]
    # Sort by relevance descending
    project_scores.sort(key=lambda x: x[1], reverse=True)


    # ─────────────────────────────────────────────────────────────────────────
    # ══ RESULTS ══════════════════════════════════════════════════════════════
    # ─────────────────────────────────────────────────────────────────────────

    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;">
        <div style="font-size:0.75rem;font-weight:600;letter-spacing:0.1em;
            text-transform:uppercase;color:#7C3AED;margin-bottom:0.5rem;">
            ✨ Analysis Complete
        </div>
        <h2 style="font-size:1.8rem;font-weight:700;color:#E2E8F0;margin:0;">
            Your Full Analysis
        </h2>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL 1: SCORE BANNER
    # ─────────────────────────────────────────────────────────────────────────
    col_ring, col_context = st.columns([1, 1.6], gap="large")

    with col_ring:
        st.markdown(
            f'<div class="glass-card" style="border-color:{tier["border"]};'
            f'background:{tier["bg"]};">'
            f'{render_score_ring(match_score, tier)}'
            f'<div style="text-align:center;margin-top:0.5rem;">'
            f'<div class="tier-badge" style="background:{tier["bg"]};'
            f'border:1px solid {tier["border"]};color:{tier["color"]};">'
            f'{tier["emoji"]} {tier["label"]}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    with col_context:
        st.markdown(
            f'<div class="glass-card" style="border-color:{tier["border"]};'
            f'background:{tier["bg"]};">',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="score-headline" style="color:{tier["color"]};">'
            f'{tier["headline"]}</div>'
            f'<div class="score-confidence">{tier["confidence"]}</div>'
            f'<div style="margin-top:0.75rem;padding:0.65rem 0.9rem;'
            f'background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);'
            f'border-radius:10px;font-size:0.78rem;color:#64748B;line-height:1.5;">'
            f'💡 <em>{tier["industry_note"]}</em></div>',
            unsafe_allow_html=True,
        )
        
        # Match Breakdown
        st.markdown("<div style='margin-top: 1.2rem; margin-bottom: 1.2rem;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:0.85rem;color:#C4B5FD;margin-bottom:0.6rem;text-transform:uppercase;letter-spacing:0.05em;'>📊 Match Breakdown</h4>", unsafe_allow_html=True)
        st.markdown(render_breakdown_row("Skills Match", skills_score, "#A78BFA"), unsafe_allow_html=True)
        st.markdown(render_breakdown_row("Projects Match", projects_score, "#34D399"), unsafe_allow_html=True)
        st.markdown(render_breakdown_row("Experience Match", experience_score, "#60A5FA"), unsafe_allow_html=True)
        st.markdown(render_breakdown_row("Education Match", education_score, "#FBBF24"), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Industry scale
        st.markdown(render_industry_scale(match_score), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL 2: WHY THIS SCORE
    # ─────────────────────────────────────────────────────────────────────────
    col_str, col_gap = st.columns(2, gap="large")

    with col_str:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <h2>💚 What's Working For You</h2>
        </div>
        <p style="font-size:0.8rem;color:#475569;margin-bottom:1rem;">
            These factors are contributing positively to your match score.
        </p>
        """, unsafe_allow_html=True)
        for emoji, text in why_score["strengths"][:3]:
            st.markdown(
                f'<div class="why-item why-strength">'
                f'<span class="why-emoji">{emoji}</span>'
                f'<span class="why-text">{md_to_html(text)}</span></div>',
                unsafe_allow_html=True,
            )
        if not why_score["strengths"]:
            st.markdown('<p style="color:#475569;font-size:0.82rem;font-style:italic;">'
                        'Upload a resume with more content to see strengths.</p>',
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_gap:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <h2>🔶 Why Your Score Isn't Higher</h2>
        </div>
        <p style="font-size:0.8rem;color:#475569;margin-bottom:1rem;">
            These are the specific reasons pulling the score down — each is actionable.
        </p>
        """, unsafe_allow_html=True)
        for emoji, text in why_score["gaps"][:3]:
            st.markdown(
                f'<div class="why-item why-gap">'
                f'<span class="why-emoji">{emoji}</span>'
                f'<span class="why-text">{md_to_html(text)}</span></div>',
                unsafe_allow_html=True,
            )
        if not why_score["gaps"]:
            st.markdown('<p style="color:#64748B;font-size:0.82rem;">No major gaps detected! '
                        'Focus on polishing the action plan below.</p>',
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL 3: SKILLS ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-bottom:1.5rem;">
        <h2 style="font-size:1.4rem;font-weight:700;color:#E2E8F0;margin:0 0 0.3rem;">
            🏷️ Skills Analysis
        </h2>
        <p style="font-size:0.83rem;color:#64748B;margin:0;">
            Keyword-level skill matching across 150+ technologies, frameworks, and soft skills
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Summary stat bars
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("JD Skills Required", total_jd_skills)
    with col_s2:
        st.metric("✅ Matched", len(matched_skills))
    with col_s3:
        st.metric("❌ Missing", len(missing_skills))
    with col_s4:
        skill_pct = f"{why_score['skill_match_rate']:.0f}%"
        st.metric("Keyword Match Rate", skill_pct)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(render_stat_bar("Matched", len(matched_skills), total_jd_skills,
                                "linear-gradient(90deg,#34D399,#10B981)"), unsafe_allow_html=True)
    st.markdown(render_stat_bar("Missing", len(missing_skills), total_jd_skills,
                                "linear-gradient(90deg,#EF4444,#F87171)"), unsafe_allow_html=True)
    
    if jd_frequencies:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:0.85rem;color:#C4B5FD;margin-bottom:0.6rem;text-transform:uppercase;letter-spacing:0.05em;'>📊 Top JD Keyword Frequency</h4>", unsafe_allow_html=True)
        freq_badges = "".join(f'<span class="chip-freq">{skill.title()} ({count})</span>' for skill, count in list(jd_frequencies.items())[:10])
        st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:0.5rem;">{freq_badges}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    tab_matched, tab_missing, tab_bonus = st.tabs(
        [f"✅ Matched ({len(matched_skills)})",
         f"❌ Missing ({len(missing_skills)})",
         f"🔵 Bonus ({len(extra_skills)})"]
    )
    with tab_matched:
        st.markdown(
            '<p style="font-size:0.82rem;color:#64748B;margin-bottom:0.75rem;">'
            'Present in <em>both</em> your resume and the job description.</p>'
            + render_skill_chips(matched_skills, "chip-matched"),
            unsafe_allow_html=True,
        )
    with tab_missing:
        st.markdown(
            '<p style="font-size:0.82rem;color:#64748B;margin-bottom:0.75rem;">'
            'Required by the JD but <em>not found</em> in your resume. '
            'Gaps are prioritized based on how frequently they are mentioned in the JD.</p>',
            unsafe_allow_html=True,
        )
        if critical_missing:
            st.markdown("<p style='font-size:0.82rem;font-weight:600;color:#FCA5A5;margin:0.5rem 0 0.2rem 0;'>🔴 Critical Gaps (Mentioned 3+ times in JD)</p>", unsafe_allow_html=True)
            st.markdown(render_skill_chips(critical_missing, "chip-missing"), unsafe_allow_html=True)
        if important_missing:
            st.markdown("<p style='font-size:0.82rem;font-weight:600;color:#FBBF24;margin:0.5rem 0 0.2rem 0;'>🟡 Important Gaps (Mentioned 2 times in JD)</p>", unsafe_allow_html=True)
            st.markdown(render_skill_chips(important_missing, "chip-neutral"), unsafe_allow_html=True)
        if optional_missing:
            st.markdown("<p style='font-size:0.82rem;font-weight:600;color:#93C5FD;margin:0.5rem 0 0.2rem 0;'>🔵 Optional Gaps (Mentioned 1 time in JD)</p>", unsafe_allow_html=True)
            st.markdown(render_skill_chips(optional_missing, "chip-extra"), unsafe_allow_html=True)
    with tab_bonus:
        st.markdown(
            '<p style="font-size:0.82rem;color:#64748B;margin-bottom:0.75rem;">'
            'Skills on your resume not mentioned in the JD — valuable differentiators '
            'but don\'t let them overshadow the required ones.</p>'
            + render_skill_chips(extra_skills, "chip-extra"),
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL 4: DOMAIN INFERENCE MAP
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-bottom:1.5rem;">
        <h2 style="font-size:1.4rem;font-weight:700;color:#E2E8F0;margin:0 0 0.3rem;">
            🗺️ Domain Inference Map
        </h2>
        <p style="font-size:0.83rem;color:#64748B;margin:0;">
            Inferred domain alignment based on technical skill mapping
        </p>
    </div>
    """, unsafe_allow_html=True)

    DOMAIN_COLORS = {
        "Frontend Development":     "#60A5FA",
        "Backend Development":      "#A78BFA",
        "Machine Learning & AI":    "#34D399",
        "Data Science & Analytics": "#FBBF24",
        "Cloud & DevOps":           "#F97316",
        "Data Engineering":         "#06B6D4",
        "Databases":                "#8B5CF6",
        "Mobile Development":       "#EC4899",
        "Security & Auth":          "#EF4444",
        "Tooling & Collaboration":  "#94A3B8",
    }

    col_dom_r, col_dom_j = st.columns(2, gap="large")

    with col_dom_r:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header"><h2>👤 Your Domain Profile</h2></div>
        <p style="font-size:0.8rem;color:#475569;margin-bottom:1rem;">
            Topics and domains your resume demonstrates expertise in.
        </p>
        """, unsafe_allow_html=True)
        resume_domains = domain_alignment.get("resume_domains", {})
        if resume_domains:
            for domain, score in list(resume_domains.items())[:5]:
                color = DOMAIN_COLORS.get(domain, "#94A3B8")
                st.markdown(render_domain_bar(domain, score, color), unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#475569;font-style:italic;font-size:0.82rem;">'
                        'No strong domain signals detected.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_dom_j:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header"><h2>💼 JD Domain Requirements</h2></div>
        <p style="font-size:0.8rem;color:#475569;margin-bottom:1rem;">
            Topics and domains the job description emphasises.
        </p>
        """, unsafe_allow_html=True)
        jd_domains = domain_alignment.get("jd_domains", {})
        if jd_domains:
            for domain, score in list(jd_domains.items())[:5]:
                color = DOMAIN_COLORS.get(domain, "#94A3B8")
                # Dim domains missing from resume
                missing_dom_names = [d for d, _ in domain_alignment.get("missing_domains", [])]
                opacity = "0.5" if domain in missing_dom_names else "1"
                st.markdown(
                    f'<div style="opacity:{opacity};">'
                    + render_domain_bar(domain, score, color)
                    + ("" if domain not in missing_dom_names else
                       '<div style="font-size:0.7rem;color:#EF4444;margin-top:-0.3rem;'
                       'padding-bottom:0.3rem;">⚠ Not detected in resume</div>')
                    + "</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<p style="color:#475569;font-style:italic;font-size:0.82rem;">'
                        'No strong domain signals in JD.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Domain overlap summary
    aligned      = domain_alignment.get("aligned", [])
    missing_doms = domain_alignment.get("missing_domains", [])
    if aligned or missing_doms:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.markdown("""
            <div class="section-header"><h2>✅ Aligned Domains</h2></div>
            <p style="font-size:0.8rem;color:#475569;margin-bottom:0.75rem;">
                You and the JD share expertise in these areas.</p>
            """, unsafe_allow_html=True)
            aligned_html = render_skill_chips([d for d, _, _ in aligned], "chip-matched")
            st.markdown(aligned_html or '<p style="color:#475569;font-style:italic;font-size:0.82rem;">No overlap detected.</p>',
                        unsafe_allow_html=True)
        with col_b:
            st.markdown("""
            <div class="section-header"><h2>❌ Domain Gaps</h2></div>
            <p style="font-size:0.8rem;color:#475569;margin-bottom:0.75rem;">
                The JD needs these domains — not found in your resume.</p>
            """, unsafe_allow_html=True)
            missing_html = render_skill_chips([d for d, _ in missing_doms], "chip-missing")
            st.markdown(missing_html or '<p style="color:#64748B;font-style:italic;font-size:0.82rem;">No domain gaps! Great alignment.</p>',
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL 5: PROJECT ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-bottom:1.5rem;">
        <h2 style="font-size:1.4rem;font-weight:700;color:#E2E8F0;margin:0 0 0.3rem;">
            🚀 Project Analysis
        </h2>
        <p style="font-size:0.83rem;color:#64748B;margin:0;">
            Each project scored for relevance against the job description
        </p>
    </div>
    """, unsafe_allow_html=True)

    if project_scores:
        # Legend
        st.markdown("""
        <div style="display:flex;gap:1.5rem;font-size:0.75rem;color:#64748B;
            margin-bottom:1rem;padding:0.5rem 0;">
            <span>🟢 High relevance (&gt;40%)</span>
            <span>🟡 Moderate (20–40%)</span>
            <span>🔴 Low match (&lt;20%)</span>
        </div>
        """, unsafe_allow_html=True)

        for proj, rel_score, matching_jd in project_scores:
            # Colour coding
            if rel_score >= 40:
                p_color = "#34D399"
                p_bg    = "rgba(52,211,153,0.06)"
                p_border= "rgba(52,211,153,0.25)"
                p_label = "High Relevance"
            elif rel_score >= 20:
                p_color = "#FBBF24"
                p_bg    = "rgba(251,191,36,0.06)"
                p_border= "rgba(251,191,36,0.25)"
                p_label = "Moderate Relevance"
            else:
                p_color = "#EF4444"
                p_bg    = "rgba(239,68,68,0.05)"
                p_border= "rgba(239,68,68,0.2)"
                p_label = "Low Relevance"

            # Tech chips for this project
            proj_tech_html = render_skill_chips(proj["tech"], "chip-extra") if proj["tech"] \
                else '<span style="font-size:0.75rem;color:#475569;">No specific tech detected</span>'

            # Matching JD tech chips (subset of project tech that's in JD)
            jd_match_html = render_skill_chips(matching_jd, "chip-matched") if matching_jd \
                else '<span style="font-size:0.75rem;color:#475569;">None</span>'

            # Relevance insight text
            if rel_score >= 40:
                insight = f"Highly aligned — {len(matching_jd)} required technologies used."
            elif rel_score >= 20:
                insight = f"Partially aligned — {len(matching_jd)} required technologies used."
            else:
                if not proj["tech"]:
                    insight = "Add technologies to this project to show JD relevance."
                else:
                    insight = "Uses different technologies than required by the JD."

            bar_width = min(rel_score, 100)
            st.markdown(f"""
            <div class="project-card" style="background:{p_bg};border-color:{p_border};">
                <div class="project-title">{proj["title"]}</div>
                {f'<div class="project-desc">{proj["description"]}</div>' if proj["description"] else ''}
                <div class="project-relevance-label">
                    <span>JD Relevance</span>
                    <span style="color:{p_color};font-weight:700;">{rel_score:.0f}% · {p_label}</span>
                </div>
                <div class="domain-bar-track" style="margin-bottom:0.8rem;">
                    <div class="domain-bar-fill"
                        style="width:{bar_width:.1f}%;
                        background:linear-gradient(90deg,{p_color},{p_color}88);
                        border-radius:100px;"></div>
                </div>
                <div style="font-size:0.78rem;color:#64748B;margin-bottom:0.35rem;">
                    🔧 <strong style="color:#94A3B8;">Technologies in this project:</strong>
                </div>
                <div style="margin-bottom:0.6rem;">{proj_tech_html}</div>
                <div style="font-size:0.78rem;color:#64748B;margin-bottom:0.35rem;">
                    ✅ <strong style="color:#94A3B8;">Matches JD requirements:</strong>
                </div>
                <div style="margin-bottom:0.6rem;">{jd_match_html}</div>
                <div style="font-size:0.79rem;color:#64748B;padding:0.55rem 0.7rem;
                    background:rgba(124,58,237,0.07);border-radius:8px;line-height:1.5;">
                    💡 {insight}
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:2rem;">
            <div style="font-size:2.5rem;margin-bottom:0.75rem;">📁</div>
            <div style="font-size:1rem;font-weight:600;color:#E2E8F0;margin-bottom:0.5rem;">
                No Projects Detected
            </div>
            <div style="font-size:0.85rem;color:#64748B;max-width:420px;margin:0 auto;line-height:1.6;">
                A dedicated <strong>Projects</strong> section was not found in your resume.
                Adding 2–3 projects with tech stack details and descriptions is one of the
                most impactful improvements you can make, especially for technical roles.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL 6: SECTION SCORES + EXPERIENCE HIGHLIGHTS
    # ─────────────────────────────────────────────────────────────────────────
    col_sec, col_exp = st.columns([1, 1], gap="large")

    SECTION_ICONS = {
        "summary":"👤","experience":"💼","projects":"🚀",
        "education":"🎓","skills":"⚙️","certifications":"🏅",
        "achievements":"🏆","publications":"📄","languages":"🌐",
    }

    with col_sec:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header"><h2>📑 Section-Level JD Relevance</h2></div>
        <p style="font-size:0.8rem;color:#475569;margin-bottom:1rem;">
            How well each resume section matches the job description semantically.
            The overall match score is a weighted combination of all sections.
        </p>
        """, unsafe_allow_html=True)
        if section_scores:
            for sec_name, sec_score in section_scores.items():
                icon = SECTION_ICONS.get(sec_name, "📋")
                if sec_score >= 60:
                    color = "linear-gradient(90deg,#34D399,#10B981)"
                elif sec_score >= 35:
                    color = "linear-gradient(90deg,#F59E0B,#FBBF24)"
                else:
                    color = "linear-gradient(90deg,#EF4444,#F87171)"
                st.markdown(
                    render_stat_bar(f"{icon} {sec_name.title()}", int(sec_score), 100, color),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<p style="color:#475569;font-style:italic;font-size:0.82rem;">'
                        'No distinct sections detected.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_exp:
        exp_highlights = deep_analysis.get("experience_highlights", [])
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="section-header">
            <h2>💼 Experience Highlights</h2>
            <span class="count-badge">{len(exp_highlights)}</span>
        </div>
        <p style="font-size:0.8rem;color:#475569;margin-bottom:1rem;">
            Key bullets extracted from your experience section — these are what
            the semantic model evaluates against the JD's responsibilities.
        </p>
        """, unsafe_allow_html=True)
        if exp_highlights:
            for hl in exp_highlights:
                st.markdown(
                    f'<div style="padding:0.45rem 0.7rem;margin-bottom:0.4rem;'
                    f'border-left:3px solid rgba(124,58,237,0.5);'
                    f'font-size:0.81rem;color:#94A3B8;line-height:1.55;">{hl}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("""
            <div style="text-align:center;padding:1.5rem 0;">
                <div style="font-size:1.8rem;margin-bottom:0.5rem;">📋</div>
                <div style="font-size:0.83rem;color:#475569;">
                    No experience section detected.<br>
                    Adding a Work Experience section significantly improves your match.
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PANEL 7: PERSONALISED ACTION PLAN
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-bottom:1.5rem;">
        <h2 style="font-size:1.4rem;font-weight:700;color:#E2E8F0;margin:0 0 0.3rem;">
            📋 Your Personalised Action Plan
        </h2>
        <p style="font-size:0.83rem;color:#64748B;margin:0;">
            Specific, prioritised steps to improve your match — based on your actual resume gaps
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_high, col_mid, col_pol = st.columns(3, gap="large")

    with col_high:
        st.markdown("""
        <div style="text-align:center;padding:0.6rem;
            background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);
            border-radius:12px;margin-bottom:1rem;">
            <div style="font-size:1.5rem;">🔴</div>
            <div style="font-weight:700;color:#FCA5A5;font-size:0.9rem;">High Priority</div>
            <div style="font-size:0.72rem;color:#64748B;">Do these first — biggest impact</div>
        </div>
        """, unsafe_allow_html=True)
        for item in action_plan["high"]:
            st.markdown(
                f'<div class="action-card action-high">{md_to_html(item)}</div>',
                unsafe_allow_html=True,
            )
        if not action_plan["high"]:
            st.markdown('<p style="color:#64748B;font-size:0.82rem;text-align:center;">'
                        '🎉 No critical gaps!</p>', unsafe_allow_html=True)

    with col_mid:
        st.markdown("""
        <div style="text-align:center;padding:0.6rem;
            background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.25);
            border-radius:12px;margin-bottom:1rem;">
            <div style="font-size:1.5rem;">🟡</div>
            <div style="font-weight:700;color:#FBBF24;font-size:0.9rem;">Medium Priority</div>
            <div style="font-size:0.72rem;color:#64748B;">Important improvements</div>
        </div>
        """, unsafe_allow_html=True)
        for item in action_plan["medium"]:
            st.markdown(
                f'<div class="action-card action-medium">{md_to_html(item)}</div>',
                unsafe_allow_html=True,
            )
        if not action_plan["medium"]:
            st.markdown('<p style="color:#64748B;font-size:0.82rem;text-align:center;">'
                        '✅ Nothing urgent here!</p>', unsafe_allow_html=True)

    with col_pol:
        st.markdown("""
        <div style="text-align:center;padding:0.6rem;
            background:rgba(96,165,250,0.08);border:1px solid rgba(96,165,250,0.25);
            border-radius:12px;margin-bottom:1rem;">
            <div style="font-size:1.5rem;">🔵</div>
            <div style="font-weight:700;color:#93C5FD;font-size:0.9rem;">Polish & Presentation</div>
            <div style="font-size:0.72rem;color:#64748B;">Framing & differentiation</div>
        </div>
        """, unsafe_allow_html=True)
        for item in action_plan["polish"]:
            st.markdown(
                f'<div class="action-card action-polish">{md_to_html(item)}</div>',
                unsafe_allow_html=True,
            )
    # ── Closing motivational note ──────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;margin-top:2rem;padding:1.75rem 2rem;
        background:{tier['bg']};border:1px solid {tier['border']};border-radius:20px;">
        <div style="font-size:1.8rem;margin-bottom:0.5rem;">{tier['emoji']}</div>
        <div style="font-size:1rem;font-weight:700;color:{tier['color']};margin-bottom:0.5rem;">
            {tier['label']} — {tier['headline']}
        </div>
        <div style="font-size:0.84rem;color:#64748B;max-width:520px;margin:0 auto;line-height:1.65;">
            {tier['confidence']}
        </div>
    </div>
    """, unsafe_allow_html=True)
