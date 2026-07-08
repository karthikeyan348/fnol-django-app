"""
classifier.py
-------------
Applies routing rules to a claim once fields have been extracted, and
produces a short human-readable explanation for the decision.

Routing precedence (highest priority first). Precedence matters because a
claim can technically satisfy more than one rule at once (e.g. a low-value
injury claim), and the workflow needs a single, unambiguous destination:

    1. Investigation Flag  - suspicious language in the description.
                              Always wins: potential fraud must be reviewed
                              by an investigator even if the claim is small
                              or otherwise "clean".
    2. Manual Review        - any mandatory field is missing/blank. We can't
                              safely automate a decision on incomplete data.
    3. Specialist Queue     - claim type is "injury" (bodily injury claims
                              need a specialist adjuster regardless of size).
    4. Fast-Track           - complete claim, no red flags, estimated damage
                              below the auto-approval threshold.
    5. Standard Review      - fallback: complete, no red flags, but above
                              the fast-track threshold -> a human adjuster
                              reviews it at normal priority.
"""

from typing import Dict, List, Optional

from .extractor import normalize_value, parse_estimated_damage

FAST_TRACK_THRESHOLD = 25000  # currency units, e.g. INR/USD as configured by carrier

FRAUD_KEYWORDS = ["fraud", "inconsistent", "staged"]

ROUTE_INVESTIGATION = "Investigation Flag"
ROUTE_MANUAL_REVIEW = "Manual Review"
ROUTE_SPECIALIST_QUEUE = "Specialist Queue"
ROUTE_FAST_TRACK = "Fast-Track"
ROUTE_STANDARD_REVIEW = "Standard Review"


def _find_fraud_keywords(description: Optional[str]) -> List[str]:
    if not description:
        return []
    lowered = description.lower()
    return [kw for kw in FRAUD_KEYWORDS if kw in lowered]


def classify_claim(
    extracted: Dict[str, Optional[str]],
    missing_fields: List[str],
) -> Dict[str, str]:
    """
    Decide the recommended route for a claim and explain why.

    Returns: {"recommendedRoute": str, "reasoning": str}
    """
    description = normalize_value(extracted.get("incidentDescription"))
    claim_type = (normalize_value(extracted.get("claimType")) or "").strip().lower()
    damage_raw = normalize_value(extracted.get("estimatedDamage"))
    damage_value = parse_estimated_damage(damage_raw)

    hit_keywords = _find_fraud_keywords(description)

    # Rule 1: Investigation Flag (highest priority - potential fraud)
    if hit_keywords:
        found = ", ".join(f'"{k}"' for k in hit_keywords)
        reasoning = (
            f"Flagged for investigation because the incident description contains "
            f"suspicious language ({found}), which may indicate a fraudulent or "
            f"staged claim. This overrides other routing rules pending investigator review."
        )
        return {"recommendedRoute": ROUTE_INVESTIGATION, "reasoning": reasoning}

    # Rule 2: Manual Review (missing mandatory data)
    if missing_fields:
        field_list = ", ".join(missing_fields)
        reasoning = (
            f"Routed to manual review because the following mandatory field(s) are "
            f"missing or blank: {field_list}. The claim cannot be safely auto-processed "
            f"until this information is completed."
        )
        return {"recommendedRoute": ROUTE_MANUAL_REVIEW, "reasoning": reasoning}

    # Rule 3: Specialist Queue (bodily injury)
    if claim_type == "injury":
        reasoning = (
            "Routed to the specialist queue because the claim type is 'Injury'. "
            "Bodily injury claims require review by a specialist adjuster regardless "
            "of the estimated damage amount."
        )
        return {"recommendedRoute": ROUTE_SPECIALIST_QUEUE, "reasoning": reasoning}

    # Rule 4: Fast-Track (small, clean claim)
    if damage_value is not None and damage_value < FAST_TRACK_THRESHOLD:
        reasoning = (
            f"Fast-tracked because all mandatory fields are present, no fraud indicators "
            f"were detected, and the estimated damage ({damage_raw}) is below the "
            f"fast-track threshold of {FAST_TRACK_THRESHOLD:,}."
        )
        return {"recommendedRoute": ROUTE_FAST_TRACK, "reasoning": reasoning}

    # Rule 5: Standard Review (fallback - complete but above threshold, or damage
    # amount could not be parsed reliably)
    if damage_value is None:
        reasoning = (
            "Routed to standard review because the estimated damage amount could not "
            "be reliably parsed, so an automated fast-track decision cannot be made safely."
        )
    else:
        reasoning = (
            f"Routed to standard review because all mandatory fields are present and no "
            f"fraud indicators were detected, but the estimated damage ({damage_raw}) is "
            f"at or above the fast-track threshold of {FAST_TRACK_THRESHOLD:,}, so it "
            f"requires a standard adjuster review rather than automatic approval."
        )
    return {"recommendedRoute": ROUTE_STANDARD_REVIEW, "reasoning": reasoning}
