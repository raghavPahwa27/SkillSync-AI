# utils/parser.py
# ─────────────────────────────────────────────────────────────────────────────
# PDF Text Extraction Utility
#
# This module provides a robust PDF-to-text extraction pipeline using two
# complementary libraries:
#   1. pdfplumber  – preferred; handles complex layouts, tables, and spacing
#   2. PyPDF2      – fallback; faster but less accurate for complex PDFs
#
# Usage:
#   from utils.parser import extract_text_from_pdf
#   text = extract_text_from_pdf(uploaded_file)
# ─────────────────────────────────────────────────────────────────────────────

import io
import logging

import pdfplumber
import PyPDF2
import streamlit as st

# Set up module-level logger
logger = logging.getLogger(__name__)


@st.cache_data
def extract_text_from_pdf_bytes(file_bytes: bytes, file_name: str) -> str:
    """
    Extract plain text from PDF bytes. Caches the output using Streamlit's cache_data.
    """
    # ── Attempt 1: pdfplumber ─────────────────────────────────────────────────
    text = _extract_with_pdfplumber(file_bytes)

    # ── Attempt 2: PyPDF2 fallback ────────────────────────────────────────────
    if not text.strip():
        logger.warning("pdfplumber returned empty text; falling back to PyPDF2.")
        text = _extract_with_pypdf2(file_bytes)

    if not text.strip():
        logger.error("Both extraction methods returned empty text.")

    return _clean_text(text)


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract plain text from an uploaded PDF file object.
    Uses cached bytes extraction to speed up subsequent runs.
    """
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # Reset stream position
    return extract_text_from_pdf_bytes(file_bytes, uploaded_file.name)


# ── Private helpers ───────────────────────────────────────────────────────────

def _extract_with_pdfplumber(file_bytes: bytes) -> str:
    """
    Use pdfplumber to extract text from all pages of a PDF.

    pdfplumber preserves layout better and handles multi-column resumes well.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        Concatenated text from all pages, or empty string on failure.
    """
    extracted_pages = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text)
                else:
                    logger.debug(f"pdfplumber: No text on page {page_num}.")
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}")

    return "\n".join(extracted_pages)


def _extract_with_pypdf2(file_bytes: bytes) -> str:
    """
    Use PyPDF2 as a fallback to extract text from all pages of a PDF.

    Args:
        file_bytes: Raw bytes of the PDF file.

    Returns:
        Concatenated text from all pages, or empty string on failure.
    """
    extracted_pages = []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text)
            else:
                logger.debug(f"PyPDF2: No text on page {page_num}.")
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")

    return "\n".join(extracted_pages)


def _clean_text(text: str) -> str:
    """
    Normalize extracted text by collapsing excessive whitespace.

    - Replaces multiple consecutive newlines with a single newline.
    - Strips leading/trailing whitespace.

    Args:
        text: Raw extracted text string.

    Returns:
        Cleaned text string.
    """
    import re
    # Collapse 3+ newlines into 2 (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
