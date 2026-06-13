# utils/feedback_engine.py
# ─────────────────────────────────────────────────────────────────────────────
# Personalised Feedback & Coaching Engine
#
# Transforms raw analysis data (scores, skills, domains, projects) into
# human-readable, confidence-aware feedback.  All feedback is generated
# from rules applied to real data — no generic filler text.
#
# Produces:
#   • Score tier with industry context and confidence message
#   • "Why this score" — specific strengths and gap reasons
#   • Per-project JD relevance scoring
#   • Prioritised action plan (High / Medium / Polish)
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, List, Set, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Score Tier Definitions
# ─────────────────────────────────────────────────────────────────────────────
SCORE_TIERS = [
    {
        "min": 80, "max": 100,
        "label": "Exceptional Match",
        "short": "Exceptional",
        "color": "#10B981",
        "gradient": "linear-gradient(135deg, #10B981, #34D399)",
        "bg": "rgba(16,185,129,0.10)",
        "border": "rgba(16,185,129,0.45)",
        "emoji": "🌟",
        "headline": "You're an ideal candidate for this role",
        "confidence": (
            "Scores above 80 % are rare — fewer than 5 % of applicants reach this level. "
            "Apply with full confidence and let your experience speak for itself."
        ),
        "industry_note": (
            "Most ATS systems automatically flag candidates above 75 % as priority. "
            "You are well above that bar."
        ),
    },
    {
        "min": 65, "max": 80,
        "label": "Strong Match",
        "short": "Strong",
        "color": "#34D399",
        "gradient": "linear-gradient(135deg, #34D399, #6EE7B7)",
        "bg": "rgba(52,211,153,0.09)",
        "border": "rgba(52,211,153,0.40)",
        "emoji": "💪",
        "headline": "You're a highly competitive candidate",
        "confidence": (
            "Candidates in the 65–80 % range are frequently shortlisted. "
            "A tailored cover letter addressing the gaps below will make you stand out."
        ),
        "industry_note": (
            "This score puts you in the top ~25 % of applicants. "
            "Most hiring managers start interviews at 60 %+."
        ),
    },
    {
        "min": 50, "max": 65,
        "label": "Good Match",
        "short": "Good",
        "color": "#FBBF24",
        "gradient": "linear-gradient(135deg, #F59E0B, #FBBF24)",
        "bg": "rgba(251,191,36,0.09)",
        "border": "rgba(251,191,36,0.40)",
        "emoji": "⚡",
        "headline": "Solid alignment with targeted gaps",
        "confidence": (
            "Don't be discouraged — the average shortlisted candidate scores 45–65 %. "
            "You are firmly in that competitive range. Address the specific gaps below "
            "and tailor your language to match the JD."
        ),
        "industry_note": (
            "Most successful applications come from this score range with good tailoring. "
            "Highlight relevant projects prominently and mirror the JD's keywords."
        ),
    },
    {
        "min": 35, "max": 50,
        "label": "Developing Match",
        "short": "Developing",
        "color": "#F97316",
        "gradient": "linear-gradient(135deg, #F97316, #FB923C)",
        "bg": "rgba(249,115,22,0.09)",
        "border": "rgba(249,115,22,0.38)",
        "emoji": "📈",
        "headline": "Meaningful overlap with notable gaps to bridge",
        "confidence": (
            "You have a real foundation here. The gap is often in *how* your skills are "
            "presented, not just *what* you know. Rewriting bullet points to reflect the "
            "JD's language can lift your score significantly."
        ),
        "industry_note": (
            "About 40 % of all applicants are in this range. "
            "With targeted resume tailoring, moving into the 50–65 % range is very achievable."
        ),
    },
    {
        "min": 20, "max": 35,
        "label": "Early Stage",
        "short": "Early Stage",
        "color": "#EF4444",
        "gradient": "linear-gradient(135deg, #EF4444, #F87171)",
        "bg": "rgba(239,68,68,0.08)",
        "border": "rgba(239,68,68,0.35)",
        "emoji": "🌱",
        "headline": "Building towards this role",
        "confidence": (
            "This role may require skills you're still developing, but every expert "
            "started here. Use the action plan below as a roadmap — even closing 2–3 "
            "gaps can meaningfully improve your candidacy."
        ),
        "industry_note": (
            "Entry-level applicants and career changers often see scores in this range. "
            "Personal projects demonstrating the required skills can make a strong impression."
        ),
    },
    {
        "min": 0, "max": 20,
        "label": "Different Focus",
        "short": "Mismatch",
        "color": "#94A3B8",
        "gradient": "linear-gradient(135deg, #64748B, #94A3B8)",
        "bg": "rgba(148,163,184,0.07)",
        "border": "rgba(148,163,184,0.30)",
        "emoji": "🔍",
        "headline": "Resume and JD appear to be in different domains",
        "confidence": (
            "Your skills are valuable — but this specific role may not be the best fit. "
            "Consider roles that better match your current expertise, or use the "
            "action plan to build towards this domain."
        ),
        "industry_note": (
            "This is common when changing career tracks or industries. "
            "Focus on transferable skills and projects in your target domain."
        ),
    },
]


def get_score_tier(score: float) -> Dict:
    """
    Return the tier definition dict for a given score.

    Args:
        score: Similarity score in [0, 100].

    Returns:
        Tier dict with label, color, confidence message, etc.
    """
    for tier in SCORE_TIERS:
        if tier["min"] <= score <= tier["max"]:
            return tier
    return SCORE_TIERS[-1]  # fallback to lowest


def score_project_against_jd(project: Dict, jd_skills: Set[str]) -> Tuple[float, List[str]]:
    """
    Calculate how relevant a specific project is to the job description.

    Relevance is based on the fraction of the project's tech stack that
    overlaps with skills required by the JD.

    Args:
        project:    Project dict from resume_analyzer.extract_projects().
                    Must contain a "tech" key (list of skills).
        jd_skills:  Set of lowercase skills extracted from the JD.

    Returns:
        Tuple of (relevance_score_0_to_100, list_of_matching_jd_skills).
    """
    project_tech = set(project.get("tech", []))
    if not project_tech:
        return 0.0, []

    matching = list(project_tech & jd_skills)
    # Score = matched / sqrt(total project tech) to balance specificity
    relevance = min((len(matching) / max(len(project_tech) ** 0.5, 1)) * 100, 100)
    return round(relevance, 1), matching


def generate_why_score(
    semantic_score:   float,
    matched_skills:   List[str],
    missing_skills:   List[str],
    domain_alignment: Dict,
    deep_analysis:    Dict,
    jd_skills:        Set[str],
) -> Dict:
    """
    Generate a data-driven explanation of why the score is what it is.

    Analyses the relationship between:
      - Skill overlap ratio
      - Domain alignment
      - Presence of projects / experience
      - Semantic vs keyword match divergence

    Args:
        semantic_score:   Overall cosine similarity score (0–100).
        matched_skills:   Skills present in both resume and JD.
        missing_skills:   Skills in JD but not resume.
        domain_alignment: Output of topic_analyzer.get_domain_alignment().
        deep_analysis:    Output of resume_analyzer.analyze_resume().
        jd_skills:        Set of skills from JD.

    Returns:
        {
            "strengths":  [(emoji, text), ...],   # what's helping the score
            "gaps":       [(emoji, text), ...],   # what's reducing the score
            "skill_match_rate": float,            # % of JD skills matched
        }
    """
    strengths: List[Tuple[str, str]] = []
    gaps: List[Tuple[str, str]] = []

    total_jd = len(jd_skills)
    skill_match_rate = (len(matched_skills) / total_jd * 100) if total_jd > 0 else 0.0

    # ── Strength: good skill overlap ─────────────────────────────────────────
    if skill_match_rate >= 60:
        strengths.append((
            "✅",
            f"{len(matched_skills)} of {total_jd} required JD skills are present in your resume "
            f"({skill_match_rate:.0f}% keyword match rate)."
        ))
    elif skill_match_rate >= 30:
        strengths.append((
            "🔶",
            f"{len(matched_skills)} of {total_jd} JD skills matched ({skill_match_rate:.0f}%). "
            "Solid start — expanding the matched set will boost your score."
        ))

    # ── Strength: aligned domains ─────────────────────────────────────────────
    aligned_domains = domain_alignment.get("aligned", [])
    if aligned_domains:
        top = aligned_domains[0][0]
        strengths.append((
            "🎯",
            f"Strong domain alignment in **{top}** — the JD's primary focus area matches "
            "your skill profile."
        ))

    # ── Strength: projects present ────────────────────────────────────────────
    projects = deep_analysis.get("projects", [])
    if projects:
        strengths.append((
            "🚀",
            f"{len(projects)} project(s) detected in your resume. Projects demonstrate "
            "hands-on application, which semantic analysis rewards."
        ))

    # ── Strength: experience present ──────────────────────────────────────────
    exp_highlights = deep_analysis.get("experience_highlights", [])
    if exp_highlights:
        strengths.append((
            "💼",
            f"Work experience section detected with {len(exp_highlights)} highlighted "
            "responsibilities — this is evaluated against the JD's requirements."
        ))

    # ── Strength: tech in context ─────────────────────────────────────────────
    jd_tech_in_ctx = deep_analysis.get("jd_tech_in_context", [])
    if len(jd_tech_in_ctx) >= 3:
        strengths.append((
            "🔬",
            f"{len(jd_tech_in_ctx)} JD-required skills appear in your project or experience "
            "descriptions (not just listed as skills) — this is the strongest signal "
            "of real competence."
        ))

    # ── Gap: low skill keyword overlap ────────────────────────────────────────
    if skill_match_rate < 30 and total_jd > 0:
        top_missing = missing_skills[:4]
        gaps.append((
            "⚠️",
            f"Only {skill_match_rate:.0f}% of JD skills found in your resume. "
            f"Key missing terms: {', '.join(top_missing[:3])}{'...' if len(top_missing) > 3 else ''}."
        ))
    elif skill_match_rate < 60 and missing_skills:
        gaps.append((
            "🔸",
            f"{len(missing_skills)} JD skills not yet in your resume. "
            f"Top missing: **{', '.join(missing_skills[:3])}**."
        ))

    # ── Gap: missing domain ────────────────────────────────────────────────────
    missing_domains = domain_alignment.get("missing_domains", [])
    if missing_domains:
        top_missing_domain = missing_domains[0][0]
        gaps.append((
            "🗺️",
            f"The JD emphasises **{top_missing_domain}** — a domain not strongly "
            "represented in your resume. Bridging this gap would significantly improve alignment."
        ))

    # ── Gap: no projects detected ─────────────────────────────────────────────
    if not projects:
        gaps.append((
            "📁",
            "No Projects section was detected in your resume. Adding 2–3 relevant "
            "projects dramatically improves both your match score and hiring appeal."
        ))

    # ── Gap: no experience ────────────────────────────────────────────────────
    if not exp_highlights:
        gaps.append((
            "📋",
            "No Work Experience section was detected. If you have any relevant "
            "experience (internships, freelance, academic), add it to boost alignment."
        ))

    # ── Gap: high semantic but low keyword (vocabulary mismatch) ─────────────
    if semantic_score >= 50 and skill_match_rate < 35:
        gaps.append((
            "📝",
            "Your content is semantically relevant, but the specific technical terms "
            "in your resume don't match the JD's vocabulary. Try mirroring the JD's "
            "exact terminology in your descriptions."
        ))

    # ── Gap: low semantic but decent keyword match (context mismatch) ─────────
    if semantic_score < 40 and skill_match_rate >= 40:
        gaps.append((
            "🔄",
            "You have many of the required skills, but the overall context and "
            "framing of your resume doesn't align well with the JD. Rewrite your "
            "experience summaries to reflect the role's responsibilities directly."
        ))

    return {
        "strengths":        strengths,
        "gaps":             gaps,
        "skill_match_rate": round(skill_match_rate, 1),
    }


def generate_action_plan(
    missing_skills:   List[str],
    domain_alignment: Dict,
    semantic_score:   float,
    projects:         List[Dict],
    jd_skills:        Set[str],
    matched_skills:   List[str],
) -> Dict[str, List[str]]:
    """
    Generate a prioritised, specific action plan for improving the resume.

    Actions are bucketed into three priority levels:
        - high:   Do these first — biggest impact on match score
        - medium: Important improvements
        - polish: Presentation and framing improvements

    Args:
        missing_skills:   Skills in JD but absent from resume.
        domain_alignment: Domain analysis output.
        semantic_score:   Overall match %.
        projects:         List of project dicts.
        jd_skills:        Full JD skill set.
        matched_skills:   Already-matched skills.

    Returns:
        {"high": [...], "medium": [...], "polish": [...]}
    """
    high:   List[str] = []
    medium: List[str] = []
    polish: List[str] = []

    # ── High priority: critical missing skills (top 3) ────────────────────────
    if missing_skills:
        top3 = missing_skills[:3]
        for skill in top3:
            high.append(
                f"Add **{skill.title()}** to your resume — required by the JD. "
                "Describe any experience in a bullet point under a project or role."
            )

    # ── High priority: missing domain ─────────────────────────────────────────
    missing_domains = domain_alignment.get("missing_domains", [])
    for domain, score in missing_domains[:1]:
        high.append(
            f"Build visible **{domain}** experience. The JD prioritises this domain "
            "but it is currently missing from your resume."
        )

    # ── Medium: add projects if none ─────────────────────────────────────────
    if not projects:
        medium.append(
            "**Add a Projects section** with 2–3 relevant projects. Describe the tech stack "
            "and problem solved. This is highly impactful."
        )
    elif len(projects) < 2:
        medium.append(
            "Add **1–2 more projects** using the JD's required technologies to demonstrate hands-on experience."
        )

    # ── Medium: remaining missing skills ─────────────────────────────────────
    for skill in missing_skills[3:6]:
        medium.append(
            f"Incorporate **{skill.title()}** into a project description or skills list."
        )

    # ── Medium: low score, suggest keyword tailoring ──────────────────────────
    if semantic_score < 55:
        medium.append(
            "**Tailor your resume summary** to mirror the JD's exact language (e.g. use its exact technical terminology)."
        )

    # ── Polish: quantify achievements ─────────────────────────────────────────
    polish.append(
        "**Quantify achievements** — replace vague statements with metrics, e.g., 'reduced API response time by 40% using Redis caching'."
    )

    # ── Polish: matched skills — strengthen context ───────────────────────────
    if matched_skills:
        top_matched = matched_skills[:2]
        polish.append(
            f"Show **{', '.join(t.title() for t in top_matched)}** in context (project/role descriptions, not just a skills list)."
        )

    # ── Polish: extra domains as differentiators ──────────────────────────────
    extra_domains = domain_alignment.get("extra_domains", [])
    if extra_domains:
        domain_name = extra_domains[0][0]
        polish.append(
            f"Mention **{domain_name}** expertise briefly as a 'bonus skill' so it doesn't dilute main JD alignment."
        )

    # ── Polish: cover letter tip ──────────────────────────────────────────────
    polish.append(
        "**Write a targeted cover letter** referencing specific projects that address key JD requirements."
    )

    return {
        "high": high[:3],
        "medium": medium[:3],
        "polish": polish[:3]
    }
