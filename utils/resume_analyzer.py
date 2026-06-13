# utils/resume_analyzer.py
# ─────────────────────────────────────────────────────────────────────────────
# Resume Deep Content Analyzer
#
# Goes beyond keyword skill extraction to analyse the full structural content
# of a resume:
#
#   1. Section Detection   – identifies Work Experience, Projects, Education,
#                            Skills, Summary, Certifications sections via regex
#
#   2. Tech Context Mining – extracts technologies mentioned specifically within
#                            project or experience descriptions (not just a
#                            standalone skills list)
#
#   3. Section Similarity  – compares individual resume sections to the JD to
#                            give section-level relevance scores (requires the
#                            similarity module)
#
#   4. Project Extraction  – pulls project titles and tech stacks listed under
#                            the Projects section
#
# Usage:
#   from utils.resume_analyzer import analyze_resume, get_section_scores
# ─────────────────────────────────────────────────────────────────────────────

import re
from typing import Dict, List, Optional, Tuple

from assets.skills_database import ALL_SKILLS

# ─────────────────────────────────────────────────────────────────────────────
# Section header patterns (case-insensitive)
# Each key maps to a regex that matches common variations of that section title.
# ─────────────────────────────────────────────────────────────────────────────
SECTION_PATTERNS: Dict[str, str] = {
    "summary":          r"(professional\s+)?summary|objective|profile|about\s+me|career\s+goal",
    "experience":       r"(work\s+|professional\s+|relevant\s+)?experience|employment(\s+history)?|work\s+history|positions?\s+held",
    "projects":         r"(personal\s+|academic\s+|key\s+|notable\s+)?projects?|portfolio|open[\s-]source",
    "education":        r"education(al\s+background)?|academic(\s+background)?|qualifications?|degrees?",
    "skills":           r"(technical\s+|core\s+|key\s+)?skills?|competenc(ies|y)|technologies|tech\s+stack|tools(\s+&\s+technologies)?",
    "certifications":   r"certifications?|certificates?|credentials?|licenses?",
    "achievements":     r"achievements?|accomplishments?|awards?|honours?|honors?|recognition",
    "publications":     r"publications?|research|papers?|articles?",
    "languages":        r"languages?(\s+known)?",
}

# ─────────────────────────────────────────────────────────────────────────────
# Bullet / list item pattern – lines that start with common resume bullet styles
# ─────────────────────────────────────────────────────────────────────────────
BULLET_PATTERN = re.compile(r"^[\s]*[•\-\*\u2022\u2023\u25E6\u2043▸▹►>]\s*", re.MULTILINE)


def detect_sections(text: str) -> Dict[str, str]:
    """
    Split a resume into named sections by detecting section header lines.

    Each section header is matched case-insensitively. Text between two
    detected headers is assigned to the first header's section.

    Args:
        text: Full plain-text content of the resume.

    Returns:
        Dictionary mapping section name → section text body.
        Example: {"experience": "Software Engineer at ...", "projects": "..."}
    """
    lines = text.splitlines()
    sections: Dict[str, List[str]] = {}
    current_section = "preamble"  # Text before any detected section header
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        matched_section: Optional[str] = None

        # Check if this line is a section header
        for section_name, pattern in SECTION_PATTERNS.items():
            # A section header is typically a short line (< 60 chars) that
            # matches one of our patterns. We avoid matching skill/tech words
            # mid-sentence by requiring the match to cover most of the line.
            if re.search(rf"\b({pattern})\b", stripped, re.IGNORECASE):
                # Heuristic: section headers are usually short standalone lines
                if len(stripped) < 60:
                    matched_section = section_name
                    break

        if matched_section:
            current_section = matched_section
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(line)

    # Join each section's lines back into a text block, drop empty sections
    result: Dict[str, str] = {}
    for name, lines_list in sections.items():
        body = "\n".join(lines_list).strip()
        if body and name != "preamble":
            result[name] = body
        elif body and name == "preamble":
            # Keep preamble only if it has meaningful content
            if len(body) > 20:
                result["summary"] = result.get("summary", "") + "\n" + body

    return result


def extract_tech_from_context(text: str) -> List[str]:
    """
    Extract technologies and tools mentioned specifically within project
    descriptions and work experience paragraphs — not just from a skills list.

    This provides richer context than simple keyword matching because it finds
    skills used in real-world contexts (e.g., "Built a REST API with FastAPI
    and deployed on AWS using Docker").

    Args:
        text: Full resume text or a specific section (e.g., projects section).

    Returns:
        Sorted list of unique tech skills found within contextual sentences.
    """
    if not text:
        return []

    normalised = text.lower()
    found = set()

    from assets.skills_database import SOFT_SKILLS
    soft_skills_set = {s.lower() for s in SOFT_SKILLS}
    tech_skills = [s for s in ALL_SKILLS if s.lower() not in soft_skills_set]

    for skill in tech_skills:
        pattern = re.escape(skill.lower())
        if re.search(rf"\b{pattern}\b", normalised):
            found.add(skill.lower())

    return sorted(found)


def extract_projects(text: str) -> List[Dict[str, str]]:
    """
    Parse the projects section of a resume to extract individual project entries.

    Heuristic approach:
    - Project titles tend to be short lines (< 80 chars) that are NOT bullet items
      and are followed by indented/bulleted description lines.
    - Tech stack is identified by scanning the description for known skills.

    Args:
        text: Text content of the projects section.

    Returns:
        List of dicts, each with:
            - "title":       Project title (best-effort extraction)
            - "description": Raw description text
            - "tech":        List of detected technologies
    """
    if not text:
        return []

    projects = []
    # Split on blank lines to get project blocks
    blocks = re.split(r"\n{2,}", text.strip())

    for block in blocks:
        if not block.strip():
            continue

        block_lines = block.strip().splitlines()
        # First non-bullet line is treated as the title candidate
        title = ""
        desc_lines = []

        for i, line in enumerate(block_lines):
            stripped = line.strip()
            is_bullet = bool(BULLET_PATTERN.match(line))
            is_short  = len(stripped) < 80

            if not title and not is_bullet and is_short and stripped:
                title = stripped
            else:
                desc_lines.append(stripped)

        description = " ".join(desc_lines).strip()
        full_block_text = block.strip()

        # Extract tech mentioned anywhere in this project block
        tech = extract_tech_from_context(full_block_text)

        if title or description:
            projects.append({
                "title":       title or "Untitled Project",
                "description": description[:150] + ("..." if len(description) > 150 else ""),
                "tech":        tech,
            })

    return projects


def get_experience_highlights(text: str) -> List[str]:
    """
    Extract bullet-point highlights from the experience section.

    Returns up to 10 key achievement/responsibility lines from the experience
    section for display in the UI.

    Args:
        text: Text content of the experience section.

    Returns:
        List of highlight strings (stripped of bullet characters).
    """
    if not text:
        return []

    highlights = []
    for line in text.splitlines():
        stripped = BULLET_PATTERN.sub("", line).strip()
        # Keep non-empty lines that look like descriptions (> 20 chars)
        if stripped and len(stripped) > 20:
            highlights.append(stripped)
        if len(highlights) >= 5:
            break

    return highlights


def analyze_resume(resume_text: str, jd_text: str) -> Dict:
    """
    Run a full deep-content analysis of the resume against the job description.

    This combines:
        - Section detection
        - Project extraction with tech stacks
        - Experience highlight extraction
        - Tech-in-context extraction for each section
        - Identification of which JD tech requirements appear in project context

    Args:
        resume_text: Full extracted text of the candidate's resume.
        jd_text:     Full extracted text of the job description.

    Returns:
        A comprehensive analysis dictionary:
        {
            "sections_detected":   list of section names found,
            "section_texts":       {section_name: text},
            "projects":            list of {title, description, tech},
            "experience_highlights": list of bullet strings,
            "tech_in_projects":    list of tech skills found in project context,
            "tech_in_experience":  list of tech skills found in experience context,
            "jd_tech_in_context":  list of JD-required skills found in resume context
                                   (not just in skills section),
        }
    """
    # 1. Detect resume sections
    section_texts = detect_sections(resume_text)
    sections_detected = list(section_texts.keys())

    # 2. Extract projects
    project_text = section_texts.get("projects", "")
    projects = extract_projects(project_text)

    # 3. Experience highlights
    experience_text = section_texts.get("experience", "")
    experience_highlights = get_experience_highlights(experience_text)

    # 4. Tech found specifically in project descriptions
    tech_in_projects = extract_tech_from_context(project_text)

    # 5. Tech found specifically in experience descriptions
    tech_in_experience = extract_tech_from_context(experience_text)

    # 6. Which JD-required techs appear in the project/experience context
    #    (vs only in a standalone skills section)
    jd_skills_found = set(extract_tech_from_context(jd_text))
    contextual_resume_tech = set(tech_in_projects) | set(tech_in_experience)
    jd_tech_in_context = sorted(jd_skills_found & contextual_resume_tech)

    return {
        "sections_detected":     sections_detected,
        "section_texts":         section_texts,
        "projects":              projects,
        "experience_highlights": experience_highlights,
        "tech_in_projects":      tech_in_projects,
        "tech_in_experience":    tech_in_experience,
        "jd_tech_in_context":    jd_tech_in_context,
    }


def get_section_scores(section_texts: Dict[str, str], jd_text: str) -> Dict[str, float]:
    """
    Compute per-section cosine similarity scores against the job description.

    This shows which section of the resume is most aligned with the JD —
    e.g., whether projects or experience are the strongest match.

    Args:
        section_texts: Dict of {section_name: section_text} from detect_sections().
        jd_text:       Full job description text.

    Returns:
        Dict of {section_name: similarity_score (0–100)} for sections with
        enough text (> 50 chars). Sorted descending by score.
    """
    # Import here to avoid circular imports
    from utils.similarity import get_embedding, calculate_cosine_similarity

    jd_vec = get_embedding(jd_text)
    scores: Dict[str, float] = {}

    for section_name, section_text in section_texts.items():
        # Only score sections with meaningful content
        if len(section_text.strip()) > 50:
            section_vec = get_embedding(section_text)
            score = calculate_cosine_similarity(section_vec, jd_vec)
            scores[section_name] = score

    # Sort descending by score
    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
