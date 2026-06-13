# assets/skills_database.py
# ─────────────────────────────────────────────────────────────────────────────
# Comprehensive curated list of skills used by the skill extractor.
# Skills are grouped by category for readability. Each entry is a lowercase
# string that will be matched case-insensitively against the document text.
# ─────────────────────────────────────────────────────────────────────────────

# ── Programming Languages ────────────────────────────────────────────────────
PROGRAMMING_LANGUAGES = [
    "python", "java", "javascript", "typescript", "c++", "c#", "c",
    "go", "golang", "rust", "swift", "kotlin", "scala", "r", "matlab",
    "ruby", "php", "perl", "shell", "bash", "powershell", "sql",
    "html", "css", "sass", "scss", "dart", "lua", "haskell", "elixir",
    "julia", "fortran", "cobol", "vba", "groovy", "objective-c",
]

# ── Web Frameworks & Libraries ───────────────────────────────────────────────
WEB_FRAMEWORKS = [
    "react", "angular", "vue", "svelte", "next.js", "nuxt", "gatsby",
    "django", "flask", "fastapi", "express", "nest.js", "spring",
    "spring boot", "laravel", "rails", "ruby on rails", "asp.net",
    "blazor", "htmx", "jquery", "backbone", "ember",
]

# ── Machine Learning / AI ────────────────────────────────────────────────────
ML_AI = [
    "machine learning", "deep learning", "neural networks", "nlp",
    "natural language processing", "computer vision", "reinforcement learning",
    "transformers", "bert", "gpt", "llm", "large language models",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "xgboost", "lightgbm", "catboost", "hugging face", "langchain",
    "openai", "stable diffusion", "yolo", "opencv", "spacy", "nltk",
    "sentence-transformers", "rag", "retrieval augmented generation",
    "fine-tuning", "prompt engineering", "embeddings", "vector database",
    "faiss", "pinecone", "weaviate", "chroma",
]

# ── Data Science & Analytics ─────────────────────────────────────────────────
DATA_SCIENCE = [
    "data science", "data analysis", "data engineering", "data visualization",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly", "tableau",
    "power bi", "looker", "dbt", "airflow", "spark", "pyspark",
    "hadoop", "hive", "kafka", "flink", "etl", "data pipeline",
    "feature engineering", "a/b testing", "statistics", "regression",
    "classification", "clustering", "time series",
]

# ── Cloud Platforms ───────────────────────────────────────────────────────────
CLOUD = [
    "aws", "amazon web services", "gcp", "google cloud", "azure",
    "heroku", "digitalocean", "vercel", "netlify", "cloudflare",
    "lambda", "ec2", "s3", "rds", "dynamodb", "bigquery", "firebase",
    "cloud run", "cloud functions", "sagemaker", "vertex ai",
]

# ── DevOps & Infrastructure ───────────────────────────────────────────────────
DEVOPS = [
    "docker", "kubernetes", "k8s", "terraform", "ansible", "puppet",
    "chef", "jenkins", "github actions", "gitlab ci", "circleci",
    "travis ci", "helm", "prometheus", "grafana", "elk stack",
    "elasticsearch", "logstash", "kibana", "nginx", "apache",
    "linux", "unix", "ci/cd", "devops", "site reliability engineering",
    "sre", "infrastructure as code", "iac",
]

# ── Databases ─────────────────────────────────────────────────────────────────
DATABASES = [
    "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite",
    "oracle", "sql server", "cassandra", "couchdb", "neo4j",
    "influxdb", "mariadb", "snowflake", "databricks", "supabase",
]

# ── Tools & Platforms ─────────────────────────────────────────────────────────
TOOLS = [
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "notion", "slack", "trello", "figma", "sketch", "adobe xd",
    "postman", "swagger", "graphql", "rest api", "grpc", "websocket",
    "celery", "rabbitmq", "sqs", "microservices", "api gateway",
    "oauth", "jwt", "saml", "sso",
]

# ── Soft Skills ───────────────────────────────────────────────────────────────
SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem solving",
    "critical thinking", "adaptability", "time management",
    "project management", "agile", "scrum", "kanban", "lean",
    "collaboration", "mentoring", "presentation", "negotiation",
    "customer service", "analytical", "attention to detail",
    "self-motivated", "organizational skills",
]

# ── Combined master list ──────────────────────────────────────────────────────
ALL_SKILLS = (
    PROGRAMMING_LANGUAGES
    + WEB_FRAMEWORKS
    + ML_AI
    + DATA_SCIENCE
    + CLOUD
    + DEVOPS
    + DATABASES
    + TOOLS
    + SOFT_SKILLS
)
