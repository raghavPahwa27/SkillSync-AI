# utils/gemini_service.py
# ─────────────────────────────────────────────────────────────────────────────
# Gemini AI Service — Phase 2: AI-Assisted Resume Editor
#
# Wraps google-generativeai to generate section-level resume rewrites
# that are grounded in the target Job Description and identified skill gaps.
#
# Actions supported per section:
#   improve        → general quality improvement
#   ats_friendly   → optimise for ATS keyword matching
#   shorten        → condense without losing key info
#   expand         → add more relevant detail
#   add_metrics    → inject quantifiable achievements
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import os
from typing import Optional

# ── Try to load Gemini ────────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

# ── Section-level system prompts ──────────────────────────────────────────────
_SYSTEM_BASE = (
    "You are an expert resume writer and ATS optimization specialist. "
    "Your rewrites are concise, impactful, and specifically tailored to "
    "the provided job description. Never invent companies, dates, or roles "
    "that are not implied by the original text. Output ONLY the rewritten "
    "text — no preamble, no explanations, no markdown headers."
)

_ACTION_INSTRUCTIONS: dict[str, str] = {
    "improve": (
        "Improve the quality and impact of this section. Use strong action verbs. "
        "Make it more relevant to the job description. Keep roughly the same length."
    ),
    "ats_friendly": (
        "Rewrite to maximise ATS keyword matching against the job description. "
        "Naturally integrate the missing skills listed below where contextually "
        "accurate. Preserve all factual information."
    ),
    "shorten": (
        "Condense this section to about half its current length while preserving "
        "all key achievements and technical details. Remove filler words and "
        "redundant phrases."
    ),
    "expand": (
        "Expand this section with more relevant technical detail and context. "
        "Where the original implies metrics or impact, make them explicit. "
        "Add 1-2 additional relevant details that would strengthen the application."
    ),
    "add_metrics": (
        "Add quantifiable metrics and concrete impact numbers to every statement "
        "that implies but doesn't state them. For example: 'improved performance' "
        "→ 'improved API response time by ~35%'. Keep numbers realistic and "
        "framed as estimates where appropriate."
    ),
}

_SECTION_GUIDANCE: dict[str, str] = {
    "summary": (
        "This is the professional summary/objective. Keep it to 3-4 sentences. "
        "It should open with a strong identity statement, mention 2-3 key "
        "technical strengths relevant to the JD, and close with value proposition."
    ),
    "experience": (
        "This is the work experience section. Each bullet point should start "
        "with a strong past-tense action verb (e.g. Developed, Architected, "
        "Optimised). Include tech stack where relevant. Add metrics where implied."
    ),
    "projects": (
        "These are project descriptions. Each should state: what it does, "
        "the tech stack used, and its impact or scale. Keep each project "
        "description to 2-3 sentences."
    ),
    "skills": (
        "This is the skills section. List skills clearly, grouped by category "
        "where appropriate (Languages, Frameworks, Tools, Cloud). "
        "Integrate missing JD skills that the candidate can honestly claim."
    ),
    "education": (
        "This is the education section. Keep factual. Add relevant coursework, "
        "GPA (if strong), or academic achievements if they support the JD."
    ),
    "certifications": (
        "This is the certifications section. List each certification clearly "
        "with the issuing body and year."
    ),
}


def _build_prompt(
    section_name: str,
    current_text: str,
    jd_text: str,
    missing_skills: list[str],
    action: str,
) -> str:
    """Compose the full generation prompt for a section rewrite."""
    action_instr = _ACTION_INSTRUCTIONS.get(action, _ACTION_INSTRUCTIONS["improve"])
    section_guide = _SECTION_GUIDANCE.get(section_name.lower(), "")
    missing_str = ", ".join(missing_skills[:15]) if missing_skills else "None identified"

    prompt = f"""{_SYSTEM_BASE}

--- TASK ---
{action_instr}

--- SECTION BEING EDITED ---
Section: {section_name.upper()}
{section_guide}

--- CURRENT TEXT ---
{current_text.strip()}

--- JOB DESCRIPTION (for context) ---
{jd_text[:2000].strip()}

--- MISSING SKILLS TO CONSIDER ---
{missing_str}

--- YOUR REWRITE ---"""
    return prompt


def configure_gemini(api_key: str) -> bool:
    """
    Configure the Gemini client with the provided API key.
    Returns True if successful, False if unavailable or key is blank.
    """
    if not _GENAI_AVAILABLE:
        return False
    if not api_key or not api_key.strip():
        return False
    try:
        genai.configure(api_key=api_key.strip())
        return True
    except Exception:
        return False


def generate_section_suggestion(
    section_name: str,
    current_text: str,
    jd_text: str,
    missing_skills: list[str],
    action: str = "improve",
    api_key: Optional[str] = None,
    model_name: str = "gemini-1.5-flash",
) -> tuple[bool, str]:
    """
    Generate an AI-powered rewrite for a single resume section.

    Args:
        section_name:   Name of the section (e.g. "summary", "experience").
        current_text:   The current text content of that section.
        jd_text:        Full job description text (for grounding).
        missing_skills: List of skills identified as missing from the analysis.
        action:         One of: improve, ats_friendly, shorten, expand, add_metrics.
        api_key:        Gemini API key (overrides env var / secrets if provided).
        model_name:     Gemini model to use (default: gemini-1.5-flash).

    Returns:
        Tuple of (success: bool, result_text: str).
        On failure, result_text contains the error message.
    """
    if not _GENAI_AVAILABLE:
        return False, (
            "❌ `google-generativeai` is not installed. "
            "Run: pip install google-generativeai"
        )

    if not current_text.strip():
        return False, "⚠️ This section is empty — nothing to rewrite."

    # Resolve API key: argument → env var
    resolved_key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not configure_gemini(resolved_key):
        return False, (
            "🔑 Gemini API key is missing or invalid. "
            "Please enter your key in the sidebar to enable AI suggestions."
        )

    try:
        prompt = _build_prompt(section_name, current_text, jd_text, missing_skills, action)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1024,
                top_p=0.9,
            ),
        )
        result = response.text.strip()
        if not result:
            return False, "⚠️ Gemini returned an empty response. Please try again."
        return True, result

    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "API key" in err.lower():
            return False, "🔑 Invalid Gemini API key. Please check and re-enter it."
        if "quota" in err.lower():
            return False, "⏳ Gemini API quota exceeded. Please wait a moment and retry."
        return False, f"❌ Gemini error: {err[:200]}"
