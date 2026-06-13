# utils/skill_extractor.py
# ─────────────────────────────────────────────────────────────────────────────
# Skill Extraction Utility
#
# Scans document text against a curated skills database and returns the set
# of skills that appear in the text.
#
# Approach:
#   - Regex word-boundary matching (case-insensitive) for precise detection.
#   - Multi-word skills (e.g., "machine learning") are matched as phrases.
#   - Returns a Python set so callers can easily compute intersections and diffs.
#
# Usage:
#   from utils.skill_extractor import extract_skills
#   skills = extract_skills("Proficient in Python, machine learning, and AWS")
#   # → {'python', 'machine learning', 'aws'}
# ─────────────────────────────────────────────────────────────────────────────

import re
from typing import Set, Dict, List

from assets.skills_database import ALL_SKILLS


# ── Implied Skills Mapping ───────────────────────────────────────────────────
# Scanning project descriptions / resume text for these trigger words
# will automatically imply the corresponding technical skills.
IMPLIED_SKILLS: Dict[str, List[str]] = {
    "cnn": ["deep learning", "computer vision", "neural networks", "machine learning", "pytorch", "tensorflow"],
    "convolutional neural network": ["deep learning", "computer vision", "neural networks", "machine learning", "pytorch", "tensorflow"],
    "convolutional neural networks": ["deep learning", "computer vision", "neural networks", "machine learning", "pytorch", "tensorflow"],
    "rnn": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning"],
    "recurrent neural network": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning"],
    "recurrent neural networks": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning"],
    "lstm": ["deep learning", "neural networks", "machine learning", "time series"],
    "gru": ["deep learning", "neural networks", "machine learning", "time series"],
    "transformer": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning", "hugging face"],
    "transformers": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning", "hugging face"],
    "bert": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning", "hugging face"],
    "gpt": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning", "openai", "llm", "large language models"],
    "llm": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning", "large language models"],
    "large language model": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning", "large language models"],
    "large language models": ["deep learning", "nlp", "natural language processing", "neural networks", "machine learning", "large language models"],
    "yolo": ["computer vision", "deep learning", "object detection", "pytorch", "tensorflow"],
    "object detection": ["computer vision", "deep learning", "machine learning"],
    "image classification": ["computer vision", "deep learning", "machine learning"],
    "semantic segmentation": ["computer vision", "deep learning", "machine learning"],
    "face recognition": ["computer vision", "deep learning", "machine learning"],
    "gan": ["deep learning", "neural networks", "generative ai"],
    "generative adversarial network": ["deep learning", "neural networks", "generative ai"],
    "generative adversarial networks": ["deep learning", "neural networks", "generative ai"],
    "diffusion model": ["deep learning", "neural networks", "generative ai", "stable diffusion"],
    "diffusion models": ["deep learning", "neural networks", "generative ai", "stable diffusion"],
    "stable diffusion": ["deep learning", "neural networks", "generative ai"],
    "recommendation system": ["machine learning", "data science"],
    "recommendation systems": ["machine learning", "data science"],
    "recommender system": ["machine learning", "data science"],
    "recommender systems": ["machine learning", "data science"],
    "chatbot": ["nlp", "natural language processing", "machine learning"],
    "chatbots": ["nlp", "natural language processing", "machine learning"],
    "rest api": ["backend development", "api gateway"],
    "restful api": ["backend development", "api gateway"],
    "rest apis": ["backend development", "api gateway"],
    "restful apis": ["backend development", "api gateway"],
    "docker": ["devops", "ci/cd"],
    "kubernetes": ["devops", "docker"],
    "k8s": ["devops", "docker"],
    "ci/cd": ["devops"],
    "jenkins": ["devops", "ci/cd"],
    "github actions": ["devops", "ci/cd"],
    "gitlab ci": ["devops", "ci/cd"],
    "terraform": ["devops", "infrastructure as code", "iac"],
    "microservices": ["backend development", "system design"],
    "serverless": ["cloud computing", "backend development"],
    "aws lambda": ["serverless", "cloud computing", "backend development"],
    "web scraping": ["data collection", "python"],
    "selenium": ["web scraping", "automation"],
    "beautifulsoup": ["web scraping", "python"],
    "scrapy": ["web scraping", "python"],
}


def infer_implied_skills(text: str) -> Set[str]:
    """
    Scan text for technical project keywords and return inferred implied tech skills.
    For example, mentioning 'CNN' implies 'deep learning', 'computer vision', etc.
    """
    if not text:
        return set()

    normalised = text.lower()
    inferred = set()

    for trigger, skills in IMPLIED_SKILLS.items():
        pattern = re.escape(trigger)
        if re.search(rf"\b{pattern}\b", normalised):
            for skill in skills:
                inferred.add(skill.lower())

    return inferred


def extract_skills(text: str) -> Set[str]:
    """
    Extract all recognised skills from the provided text.

    The function performs case-insensitive whole-word (or whole-phrase) matching
    so that, for example, "JavaScript" matches the skill "javascript", and
    "R programming" does NOT accidentally match just the letter "r".

    Args:
        text: Plain text extracted from a resume or job description PDF.

    Returns:
        A set of lowercase skill strings that were found in the text.
        Example: {'python', 'aws', 'machine learning', 'docker'}
    """
    if not text:
        return set()

    # Normalise text to lowercase for uniform comparison
    normalised = text.lower()

    found_skills: Set[str] = set()

    for skill in ALL_SKILLS:
        # Escape special regex characters in the skill name (e.g., "c++", "asp.net")
        pattern = re.escape(skill.lower())

        # Use word boundaries (\b) to avoid partial matches.
        # For multi-word skills the boundary applies to the start/end of the phrase.
        if re.search(rf"\b{pattern}\b", normalised):
            found_skills.add(skill.lower())

    return found_skills


def compare_skills(resume_skills: Set[str], jd_skills: Set[str]) -> dict:
    """
    Compare skill sets from the resume and job description.

    Args:
        resume_skills: Skills extracted from the candidate's resume.
        jd_skills:     Skills extracted from the job description.

    Returns:
        A dictionary with three keys:
            - "matched":  Skills present in both resume and job description.
            - "missing":  Skills required by JD but absent from resume.
            - "extra":    Skills on resume not explicitly mentioned in JD.
    """
    matched = resume_skills & jd_skills          # intersection
    missing = jd_skills - resume_skills          # in JD but not resume
    extra   = resume_skills - jd_skills          # in resume but not JD

    return {
        "matched": sorted(matched),
        "missing": sorted(missing),
        "extra":   sorted(extra),
    }


def get_jd_skill_frequencies(jd_text: str, jd_skills: Set[str]) -> Dict[str, int]:
    """
    Count the frequency of each JD skill inside the Job Description.
    Returns a dictionary of {skill: count} sorted by frequency descending.
    """
    if not jd_text or not jd_skills:
        return {}

    normalised = jd_text.lower()
    counts = {}
    for skill in jd_skills:
        pattern = re.escape(skill.lower())
        occurrences = len(re.findall(rf"\b{pattern}\b", normalised))
        counts[skill] = max(occurrences, 1)

    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
