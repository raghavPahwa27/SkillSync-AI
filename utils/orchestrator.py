# utils/orchestrator.py
# ─────────────────────────────────────────────────────────────────────────────
# Centralized Analysis Pipeline Orchestrator
#
# Runs text extraction analysis, skill mapping, semantic section scoring,
# project relevance scoring (with embeddings), ATS check, and confidence metrics.
# Compiles everything into a structured result object.
# ─────────────────────────────────────────────────────────────────────────────

import re
from typing import Dict, List, Set

from utils.similarity import get_embedding, calculate_cosine_similarity
from utils.skill_extractor import extract_skills, compare_skills, infer_implied_skills, get_jd_skill_frequencies
from utils.resume_analyzer import analyze_resume, get_section_scores
from utils.topic_analyzer import get_domain_alignment
from utils.feedback_engine import (
    get_score_tier,
    generate_why_score,
    generate_action_plan,
)
from assets.skills_database import SOFT_SKILLS


def run_analysis_pipeline(resume_text: str, jd_text: str) -> Dict:
    """
    Run the full resume analysis pipeline and compile a Structured Result Object.
    
    Args:
        resume_text: Raw plain-text of the candidate's resume.
        jd_text:     Raw plain-text of the job description.
        
    Returns:
        A structured dictionary representing the full analysis results.
    """
    # 1. Parse resume structure, sections, and projects
    deep_analysis = analyze_resume(resume_text, jd_text)
    section_texts = deep_analysis.get("section_texts", {})
    sections_detected = deep_analysis.get("sections_detected", [])
    
    # 2. Extract technical skills (excluding soft skills)
    soft_skills_set = {s.lower() for s in SOFT_SKILLS}
    
    raw_resume_skills = extract_skills(resume_text)
    inferred_skills   = infer_implied_skills(resume_text)
    resume_skills     = (raw_resume_skills | inferred_skills) - soft_skills_set
    
    jd_skills         = extract_skills(jd_text) - soft_skills_set
    skill_report      = compare_skills(resume_skills, jd_skills)
    
    matched_skills    = skill_report["matched"]
    missing_skills    = skill_report["missing"]
    extra_skills      = skill_report["extra"]
    total_jd_skills   = len(jd_skills)
    
    # JD frequency & prioritize missing skills
    jd_frequencies = get_jd_skill_frequencies(jd_text, jd_skills)
    critical_missing = []
    important_missing = []
    nice_to_have_missing = []
    
    for skill in missing_skills:
        freq = jd_frequencies.get(skill, 1)
        if freq >= 3:
            critical_missing.append(skill)
        elif freq == 2:
            important_missing.append(skill)
        else:
            nice_to_have_missing.append(skill)
            
    # 3. Matched skills evidence tracing
    skill_evidence = {}
    projects_raw = deep_analysis.get("projects", [])
    for skill in matched_skills:
        ev = []
        pattern = re.escape(skill.lower())
        
        # Check projects
        for proj in projects_raw:
            proj_text = f"{proj.get('title', '')} {proj.get('description', '')}".lower()
            if re.search(rf"\b{pattern}\b", proj_text):
                ev.append(f"Project: {proj.get('title')}")
                
        # Check sections
        for sec_name, sec_text in section_texts.items():
            if sec_name in ["experience", "education", "summary", "skills"]:
                if re.search(rf"\b{pattern}\b", sec_text.lower()):
                    ev.append(f"{sec_name.title()} Section")
                    
        # Remove duplicates, fallback to general skills section if nothing found
        ev = list(dict.fromkeys(ev))
        if not ev:
            ev = ["Skills Section"]
        skill_evidence[skill] = ev

    # 4. Compute semantic section similarity scores
    section_scores = get_section_scores(section_texts, jd_text)
    experience_score = section_scores.get("experience", 0.0)
    education_score  = section_scores.get("education", 0.0)
    
    # 5. Hybrid Project Relevance Scoring (Semantic + Tech Keyword Overlap)
    project_scores = []
    jd_embedding = get_embedding(jd_text)
    
    for proj in projects_raw:
        proj_desc = proj.get("description", proj.get("title", ""))
        # a. Semantic relevance via embedding
        if proj_desc:
            proj_emb = get_embedding(proj_desc)
            sem_rel = calculate_cosine_similarity(proj_emb, jd_embedding)
        else:
            sem_rel = 0.0
            
        # b. Keyword overlap relevance
        proj_tech = set(proj.get("tech", []))
        matching_jd = list(proj_tech & jd_skills)
        if proj_tech:
            tech_rel = min((len(matching_jd) / max(len(proj_tech) ** 0.5, 1)) * 100, 100)
        else:
            tech_rel = 0.0
            
        # c. Blended relevance: 70% Semantic, 30% Keyword overlap
        final_rel = 0.7 * sem_rel + 0.3 * tech_rel
        final_rel = round(final_rel, 1)
        
        # Determine styling and details
        if final_rel >= 40:
            p_color = "#34D399"
            p_bg    = "rgba(52,211,153,0.06)"
            p_border= "rgba(52,211,153,0.25)"
            p_label = "High Relevance"
            insight = f"Highly aligned — strong semantic overlap and {len(matching_jd)} required technologies."
        elif final_rel >= 20:
            p_color = "#FBBF24"
            p_bg    = "rgba(251,191,36,0.06)"
            p_border= "rgba(251,191,36,0.25)"
            p_label = "Moderate Relevance"
            insight = f"Partially aligned — moderate semantic overlap and {len(matching_jd)} required technologies."
        else:
            p_color = "#EF4444"
            p_bg    = "rgba(239,68,68,0.05)"
            p_border= "rgba(239,68,68,0.2)"
            p_label = "Low Relevance"
            if not proj_tech:
                insight = "Add specific technical keywords to this project description to show JD relevance."
            else:
                insight = "Uses a different tech focus with low semantic overlap."
                
        project_scores.append({
            "title": proj.get("title", "Untitled Project"),
            "description": proj.get("description", ""),
            "tech": proj.get("tech", []),
            "relevance_score": final_rel,
            "matching_jd": matching_jd,
            "color": p_color,
            "bg": p_bg,
            "border": p_border,
            "label": p_label,
            "insight": insight
        })
        
    # Projects Match Score (average of relevance scores, or fallback to section score)
    projects_score = section_scores.get("projects", 0.0)
    if projects_score == 0.0 and project_scores:
        projects_score = sum(p["relevance_score"] for p in project_scores) / len(project_scores)
    projects_score = round(projects_score, 1)

    # 6. Calibrated Overall Match Score
    # final_score = 0.6 * semantic_score + 0.4 * skill_match_score
    raw_semantic = calculate_cosine_similarity(get_embedding(resume_text), jd_embedding)
    skills_score = (len(matched_skills) / len(jd_skills) * 100) if jd_skills else 100.0
    
    raw_calibrated_score = 0.6 * raw_semantic + 0.4 * skills_score
    match_score = min(round(raw_calibrated_score, 1), 99.0)

    # 7. Confidence Scores
    confidence_scores = {
        "skills": "High" if total_jd_skills >= 6 else ("Medium" if total_jd_skills >= 3 else "Low"),
        "projects": "High" if len(project_scores) >= 2 else ("Medium" if len(project_scores) == 1 else "Low"),
        "experience": "High" if len(section_texts.get("experience", "")) >= 400 else ("Medium" if len(section_texts.get("experience", "")) >= 100 else "Low"),
        "education": "High" if len(section_texts.get("education", "")) >= 50 else "Low",
    }

    # 8. ATS Readiness Check
    ats_issues = []
    ats_score = 0
    
    # a. Metrics Check
    has_metrics = bool(re.search(r'\b\d+(%|\s*(percent|x|X|k|K|M|m|sec|ms|hr|hrs|years|yrs|months|GB|TB))\b|\b\d{2,}\b', resume_text))
    if has_metrics:
        ats_score += 25
    else:
        ats_issues.append("Missing quantifiable achievements (e.g. percentages, metrics, or numbers) to prove impact.")
        
    # b. Action Verbs Check
    action_verbs = ["created", "developed", "built", "designed", "managed", "led", "optimized", 
                    "improved", "implemented", "spearheaded", "architected", "engineered", "automated"]
    found_verbs = sum(1 for verb in action_verbs if re.search(rf"\b{verb}\b", resume_text.lower()))
    if found_verbs >= 3:
        ats_score += 25
    elif found_verbs >= 1:
        ats_score += 15
        ats_issues.append("Limited action verbs found. Start responsibility points with strong descriptors (e.g. spearheaded, automated).")
    else:
        ats_issues.append("Missing strong action verbs (e.g. optimized, built, implemented) at the start of responsibility points.")
        
    # c. Contact Info Check
    has_email = bool(re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', resume_text))
    has_phone = bool(re.search(r'\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}', resume_text))
    if has_email:
        ats_score += 15
    else:
        ats_issues.append("Missing email contact details.")
    if has_phone:
        ats_score += 15
    else:
        ats_issues.append("Missing phone contact details.")
        
    # d. Structural Section Check
    if "experience" in sections_detected:
        ats_score += 10
    else:
        ats_issues.append("Missing standard 'Work Experience' section header.")
    if "skills" in sections_detected:
        ats_score += 5
    else:
        ats_issues.append("Missing standard 'Skills' section header.")
    if "education" in sections_detected:
        ats_score += 5
    else:
        ats_issues.append("Missing standard 'Education' section header.")

    # 9. Domain Inference Mapping
    domain_alignment = get_domain_alignment(resume_skills, jd_skills)

    # 10. Generate Feedback using Calibrated Score
    tier = get_score_tier(match_score)
    why_score = generate_why_score(
        match_score, matched_skills, missing_skills,
        domain_alignment, deep_analysis, jd_skills,
    )
    action_plan = generate_action_plan(
        missing_skills, domain_alignment, match_score,
        projects_raw, jd_skills, matched_skills,
    )

    # Compile the Structured Result Object
    return {
        "match_score":          match_score,
        "raw_semantic_score":   raw_semantic,
        
        # Section alignment scores
        "skills_score":         skills_score,
        "experience_score":     experience_score,
        "projects_score":       projects_score,
        "education_score":      education_score,
        
        # Confidence
        "confidence_scores":    confidence_scores,
        
        # ATS Readiness check
        "ats_readiness_score":  ats_score,
        "ats_issues":           ats_issues,
        
        # Skills
        "skills": {
            "matched":           matched_skills,
            "missing":           missing_skills,
            "extra":             extra_skills,
            "critical_missing":  critical_missing,
            "important_missing": important_missing,
            "nice_to_have_missing": nice_to_have_missing,
            "frequencies":       jd_frequencies,
            "evidence":          skill_evidence,
        },
        
        # Section details
        "sections_detected":     sections_detected,
        "section_texts":         section_texts,
        "section_scores":        section_scores,
        "projects":              project_scores,
        "experience_highlights": deep_analysis.get("experience_highlights", []),
        
        # Domain & feedback
        "domain_alignment":      domain_alignment,
        "why_score":             why_score,
        "action_plan":           action_plan,
        "tier":                  tier,
    }
