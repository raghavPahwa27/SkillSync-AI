# utils/__init__.py
# Makes the utils directory a Python package.

from .parser import extract_text_from_pdf
from .similarity import get_embedding, calculate_cosine_similarity
from .skill_extractor import extract_skills, compare_skills
from .resume_analyzer import analyze_resume, get_section_scores
from .topic_analyzer import get_domain_alignment, score_domains
from .feedback_engine import (
    get_score_tier,
    score_project_against_jd,
    generate_why_score,
    generate_action_plan,
)

