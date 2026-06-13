# utils/topic_analyzer.py
# ─────────────────────────────────────────────────────────────────────────────
# Domain / Topic Knowledge Profiler
#
# Classifies a resume and JD into technology domains, producing a score
# (0–100 %) for each domain based on how many domain-specific skills are
# present.  Comparing the two profiles reveals domain-level alignment gaps.
#
# Domains covered:
#   Frontend · Backend · Machine Learning & AI · Data Science · Cloud & DevOps ·
#   Data Engineering · Databases · Mobile · Security & Auth · Full Stack / API
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, List, Set, Tuple

# ── Domain → skill mapping ────────────────────────────────────────────────────
# Each domain lists the skills that contribute to expertise in that area.
# Skills should match entries in assets/skills_database.py (lowercase).
DOMAIN_SKILLS: Dict[str, List[str]] = {
    "Frontend Development": [
        "react", "angular", "vue", "svelte", "next.js", "nuxt", "gatsby",
        "html", "css", "sass", "scss", "javascript", "typescript",
        "jquery", "htmx", "backbone", "ember", "figma", "adobe xd",
    ],
    "Backend Development": [
        "python", "java", "golang", "go", "rust", "ruby", "php", "scala",
        "django", "flask", "fastapi", "spring", "spring boot", "express",
        "nest.js", "laravel", "ruby on rails", "asp.net", "grpc",
        "rest api", "graphql", "websocket", "microservices", "celery",
        "rabbitmq", "api gateway",
    ],
    "Machine Learning & AI": [
        "machine learning", "deep learning", "neural networks", "nlp",
        "natural language processing", "computer vision", "reinforcement learning",
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "xgboost", "lightgbm", "catboost", "transformers", "bert", "gpt",
        "llm", "large language models", "hugging face", "langchain", "openai",
        "embeddings", "fine-tuning", "prompt engineering", "rag",
        "retrieval augmented generation", "yolo", "opencv", "spacy", "nltk",
        "sentence-transformers",
    ],
    "Data Science & Analytics": [
        "data science", "data analysis", "data visualization", "statistics",
        "pandas", "numpy", "matplotlib", "seaborn", "plotly", "tableau",
        "power bi", "looker", "regression", "classification", "clustering",
        "time series", "a/b testing", "feature engineering",
    ],
    "Cloud & DevOps": [
        "aws", "amazon web services", "gcp", "google cloud", "azure",
        "docker", "kubernetes", "k8s", "terraform", "ansible", "puppet",
        "chef", "jenkins", "github actions", "gitlab ci", "circleci",
        "helm", "prometheus", "grafana", "nginx", "ci/cd", "devops",
        "site reliability engineering", "sre", "infrastructure as code", "iac",
        "lambda", "ec2", "s3", "rds", "sagemaker", "vertex ai",
        "heroku", "vercel", "netlify", "cloudflare",
    ],
    "Data Engineering": [
        "spark", "pyspark", "kafka", "airflow", "dbt", "hadoop", "hive",
        "flink", "etl", "data pipeline", "databricks", "snowflake",
        "data engineering", "bigquery",
    ],
    "Databases": [
        "sql", "mysql", "postgresql", "postgres", "mongodb", "redis",
        "sqlite", "oracle", "sql server", "cassandra", "couchdb",
        "neo4j", "influxdb", "mariadb", "supabase", "dynamodb",
        "elasticsearch", "faiss", "pinecone", "weaviate", "chroma",
    ],
    "Mobile Development": [
        "swift", "kotlin", "dart", "flutter", "react native",
        "objective-c", "android", "ios",
    ],
    "Security & Auth": [
        "oauth", "jwt", "saml", "sso", "cryptography",
    ],
    "Tooling & Collaboration": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence",
        "docker", "postman", "swagger", "agile", "scrum", "kanban",
    ],
}


def score_domains(skills: Set[str]) -> Dict[str, float]:
    """
    Compute a proficiency score (0–100 %) for each domain given a skill set.

    Scoring formula:
        domain_score = (matched_skills / total_domain_skills) * 100

    Only domains with at least one matched skill are included.

    Args:
        skills: Set of lowercase skill strings.

    Returns:
        Dict {domain_name: score_pct}, sorted descending by score.
    """
    scores: Dict[str, float] = {}
    normalised = {s.lower() for s in skills}

    for domain, domain_skill_list in DOMAIN_SKILLS.items():
        matched = sum(1 for s in domain_skill_list if s in normalised)
        if matched > 0:
            score = round((matched / len(domain_skill_list)) * 100, 1)
            scores[domain] = score

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def get_top_domains(skills: Set[str], top_n: int = 5) -> List[Tuple[str, float]]:
    """
    Return the top N domains by proficiency score.

    Args:
        skills: Set of lowercase skill strings.
        top_n:  Maximum number of domains to return.

    Returns:
        List of (domain_name, score_pct) tuples, sorted descending.
    """
    scored = score_domains(skills)
    return list(scored.items())[:top_n]


def get_domain_alignment(
    resume_skills: Set[str],
    jd_skills: Set[str],
) -> Dict:
    """
    Compare resume and JD domain profiles to identify alignment and gaps.

    Returns:
        {
            "resume_domains":  {domain: score},   # candidate's strengths
            "jd_domains":      {domain: score},   # what JD requires
            "aligned":         [(domain, r_score, jd_score)],  # in both
            "missing_domains": [(domain, jd_score)],           # in JD not resume
            "extra_domains":   [(domain, r_score)],            # in resume not JD
        }
    """
    resume_domains = score_domains(resume_skills)
    jd_domains     = score_domains(jd_skills)

    resume_set = set(resume_domains.keys())
    jd_set     = set(jd_domains.keys())

    aligned = [
        (d, resume_domains[d], jd_domains[d])
        for d in resume_set & jd_set
    ]
    aligned.sort(key=lambda x: x[2], reverse=True)  # sort by JD score

    missing_domains = [
        (d, jd_domains[d])
        for d in jd_set - resume_set
    ]
    missing_domains.sort(key=lambda x: x[1], reverse=True)

    extra_domains = [
        (d, resume_domains[d])
        for d in resume_set - jd_set
    ]
    extra_domains.sort(key=lambda x: x[1], reverse=True)

    return {
        "resume_domains":  resume_domains,
        "jd_domains":      jd_domains,
        "aligned":         aligned,
        "missing_domains": missing_domains,
        "extra_domains":   extra_domains,
    }
