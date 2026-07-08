"""
extractor.py
------------
Parses raw FNOL text into a structured dictionary of fields.

The extractor is deliberately rule-based / regex-based rather than relying on a
heavy NLP model. FNOL intake forms (whether PDF, web form export, or email)
are highly structured "Label: value" documents, so a robust label-matching
approach is fast, dependency-free, transparent, and easy to audit -- all
important properties for an insurance workflow.

Each canonical field can have several aliases (different phrasing used by
different carriers/forms). We match the FIRST alias found on its own line.
"""

import re
from typing import Dict, List, Optional


# Canonical field name -> list of possible label aliases found in FNOL docs.
# Matching is case-insensitive and tolerant of minor punctuation differences.
FIELD_ALIASES: Dict[str, List[str]] = {
    "policyNumber": ["policy number", "policy no", "policy #"],
    "policyholderName": ["policyholder name", "policy holder name", "insured name"],
    "effectiveDates": ["effective dates", "effective date", "policy period"],

    "incidentDate": ["date"],
    "incidentTime": ["time"],
    "incidentLocation": ["location"],
    "incidentDescription": ["description"],

    "claimant": ["claimant"],
    "thirdParties": ["third parties", "third party"],
    "contactDetails": ["contact details", "contact information", "contact"],

    "assetType": ["asset type"],
    "assetId": ["asset id", "asset number"],
    "estimatedDamage": ["estimated damage", "damage estimate"],

    "claimType": ["claim type"],
    "attachments": ["attachments", "attachment"],
    "initialEstimate": ["initial estimate"],
}

# Fields that MUST be present and non-empty for a claim to bypass manual review.
# "Third Parties" is intentionally excluded -- a single-vehicle/no-third-party
# claim can legitimately have "None" here, so its absence is not an error.
MANDATORY_FIELDS: List[str] = [
    "policyNumber",
    "policyholderName",
    "effectiveDates",
    "incidentDate",
    "incidentTime",
    "incidentLocation",
    "incidentDescription",
    "claimant",
    "contactDetails",
    "assetType",
    "assetId",
    "estimatedDamage",
    "claimType",
    "attachments",
    "initialEstimate",
]

# Values that count as "empty" even though a label line technically exists
_EMPTY_VALUE_TOKENS = {"", "none", "n/a", "na", "-", "nil", "tbd", "unknown"}


def _build_label_pattern(alias: str) -> re.Pattern:
    """Build a regex that matches `<alias>:<value>` at the start of a line."""
    escaped = re.escape(alias)
    return re.compile(rf"^\s*{escaped}\s*:\s*(.*)$", re.IGNORECASE)


# Pre-compile: canonical field -> list of (alias, compiled pattern)
_COMPILED_ALIASES = {
    field: [(alias, _build_label_pattern(alias)) for alias in aliases]
    for field, aliases in FIELD_ALIASES.items()
}


def extract_fields(raw_text: str) -> Dict[str, Optional[str]]:
    """
    Extract canonical fields from raw FNOL text.

    Returns a dict of canonical_field_name -> extracted value (str) or
    None if the field could not be found / was left blank in the source doc.
    """
    lines = raw_text.splitlines()
    extracted: Dict[str, Optional[str]] = {field: None for field in FIELD_ALIASES}

    # Description often spans until the next section header ("--- ... ---")
    # or the next known label, so we handle it with a small lookahead once
    # we find its starting line.
    for idx, line in enumerate(lines):
        for field, alias_patterns in _COMPILED_ALIASES.items():
            if extracted[field] is not None:
                continue
            for _alias, pattern in alias_patterns:
                match = pattern.match(line)
                if not match:
                    continue
                value = match.group(1).strip()

                # Special-case: description may continue on following lines
                # until a blank line or a new "--- Section ---" header.
                if field == "incidentDescription":
                    continuation = []
                    j = idx + 1
                    while j < len(lines):
                        nxt = lines[j].strip()
                        if not nxt or nxt.startswith("---"):
                            break
                        # stop if the next line looks like another label
                        if re.match(r"^[A-Za-z ]{2,40}:\s*", nxt):
                            break
                        continuation.append(nxt)
                        j += 1
                    if continuation:
                        value = (value + " " + " ".join(continuation)).strip()

                extracted[field] = value if value else None
                break  # stop checking other aliases for this field

    return extracted


def normalize_value(value: Optional[str]) -> Optional[str]:
    """Treat placeholder tokens like 'None', 'N/A', '' as truly empty."""
    if value is None:
        return None
    if value.strip().lower() in _EMPTY_VALUE_TOKENS:
        return None
    return value.strip()


def find_missing_fields(extracted: Dict[str, Optional[str]]) -> List[str]:
    """
    Return the list of mandatory fields that are missing or blank.
    Note: 'thirdParties' is intentionally NOT mandatory (see MANDATORY_FIELDS).
    """
    missing = []
    for field in MANDATORY_FIELDS:
        if normalize_value(extracted.get(field)) is None:
            missing.append(field)
    return missing


def parse_estimated_damage(value: Optional[str]) -> Optional[float]:
    """Parse a currency-ish string like '₹42,000' or '42000' into a float."""
    if not value:
        return None
    cleaned = re.sub(r"[^\d.]", "", value)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None
