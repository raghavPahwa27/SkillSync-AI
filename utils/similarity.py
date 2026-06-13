# utils/similarity.py
# ─────────────────────────────────────────────────────────────────────────────
# Semantic Similarity Utility
#
# This module provides sentence-level semantic similarity scoring using the
# `sentence-transformers` library with the lightweight `all-MiniLM-L6-v2`
# model (22M parameters, 384-dim embeddings, fast inference).
#
# Pipeline:
#   text ──► SentenceTransformer.encode() ──► embedding vector (384-d)
#   cosine_similarity(resume_vec, jd_vec) ──► score in [0, 1]
#   score * 100 ──► percentage (0 – 100 %)
#
# The model is cached in Streamlit's session state to avoid reloading on
# every interaction.
#
# Usage:
#   from utils.similarity import get_embedding, calculate_cosine_similarity
#   vec1 = get_embedding("Python developer with ML experience")
#   vec2 = get_embedding("Looking for a Python ML engineer")
#   score = calculate_cosine_similarity(vec1, vec2)  # e.g. 87.4
# ─────────────────────────────────────────────────────────────────────────────

import logging
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Model configuration ────────────────────────────────────────────────────────
# all-MiniLM-L6-v2 is chosen for its balance of speed and quality.
# It produces 384-dimensional embeddings and runs efficiently on CPU.
MODEL_NAME = "all-MiniLM-L6-v2"

# Module-level cache so the model is only loaded once per Python session.
_model: Optional[SentenceTransformer] = None


def _load_model() -> SentenceTransformer:
    """
    Lazily load and cache the SentenceTransformer model.

    The model is downloaded from HuggingFace Hub on first use and cached
    locally in the default HuggingFace cache directory.

    Returns:
        Loaded SentenceTransformer instance.
    """
    global _model
    if _model is None:
        logger.info(f"Loading SentenceTransformer model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded successfully.")
    return _model


def get_embedding(text: str) -> np.ndarray:
    """
    Generate a semantic embedding vector for the given text.

    The text is encoded into a fixed-size (384-d) dense float32 vector that
    captures its semantic meaning. Similar texts will have vectors that are
    close together in embedding space.

    Args:
        text: Input string (e.g., full resume text or job description text).
              Long texts are handled internally by the model via chunking.

    Returns:
        A 1-D NumPy array of shape (384,) representing the text embedding.
    """
    model = _load_model()

    # encode() returns a 2-D array (batch_size × embedding_dim).
    # We pass a single string so we take index [0] to get a 1-D vector.
    embedding: np.ndarray = model.encode([text], convert_to_numpy=True)[0]
    return embedding


def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate the cosine similarity between two embedding vectors and
    express the result as a percentage.

    Cosine similarity measures the angle between two vectors in embedding
    space, giving a value between -1 and 1. For text embeddings this is
    typically in [0, 1] (no negative similarity).

    Args:
        vec1: First embedding vector (1-D NumPy array, shape (384,)).
        vec2: Second embedding vector (1-D NumPy array, shape (384,)).

    Returns:
        Similarity score in the range [0.0, 100.0] as a float.
        100.0 means semantically identical; 0.0 means no similarity.
    """
    # sklearn's cosine_similarity expects 2-D arrays: (n_samples, n_features)
    v1 = vec1.reshape(1, -1)  # shape: (1, 384)
    v2 = vec2.reshape(1, -1)  # shape: (1, 384)

    # Returns a 2-D matrix [[score]]; extract the scalar value
    similarity_score: float = cosine_similarity(v1, v2)[0][0]

    # Clamp to [0, 1] to handle any floating-point edge cases, then scale
    clamped = float(np.clip(similarity_score, 0.0, 1.0))
    return round(clamped * 100, 2)
