"""
services/agent.py
------------------
Orchestrates the FNOL pipeline for the Django app: takes raw text OR an
uploaded file (Django's UploadedFile / InMemoryUploadedFile), extracts
fields, detects missing fields, classifies/routes the claim, and returns
the result dict in the exact JSON shape required by the assessment brief.
"""

from typing import Dict, Optional

from .classifier import classify_claim
from .extractor import extract_fields, find_missing_fields, normalize_value


def extract_text_from_upload(uploaded_file) -> str:
    """
    Read raw text out of a Django UploadedFile.

    Supports .txt (read directly) and .pdf (extracted via pypdf, if
    installed). Raises ValueError for unsupported file types.
    """
    name = (uploaded_file.name or "").lower()

    if name.endswith(".txt"):
        raw_bytes = uploaded_file.read()
        return raw_bytes.decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError(
                "Reading .pdf files requires the 'pypdf' package. "
                "Install it with: pip install pypdf"
            ) from exc
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    raise ValueError(f"Unsupported file type for '{uploaded_file.name}'. Use .txt or .pdf")


def process_fnol_text(raw_text: str) -> Dict:
    """
    Run the full pipeline on raw FNOL text and return the result dict in the
    exact shape required by the assessment brief:

        {
          "extractedFields": {...},
          "missingFields": [...],
          "recommendedRoute": "...",
          "reasoning": "..."
        }
    """
    raw_extracted = extract_fields(raw_text)
    missing_fields = find_missing_fields(raw_extracted)

    extracted_fields = {
        field: normalize_value(value) for field, value in raw_extracted.items()
    }

    classification = classify_claim(raw_extracted, missing_fields)

    return {
        "extractedFields": extracted_fields,
        "missingFields": missing_fields,
        "recommendedRoute": classification["recommendedRoute"],
        "reasoning": classification["reasoning"],
    }


def process_uploaded_file(uploaded_file) -> Dict:
    """Convenience wrapper: read an uploaded file, then run the pipeline."""
    raw_text = extract_text_from_upload(uploaded_file)
    return process_fnol_text(raw_text)
