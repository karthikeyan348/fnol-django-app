"""
models.py
---------
A single model, Claim, stores every FNOL document that has been processed:
the raw input text, the extracted structured fields, which mandatory fields
were missing, the routing decision, and the reasoning behind it.

Storing this in the database (instead of just returning JSON and forgetting
it) means:
  - Adjusters can look back at claim history via the Django admin or the
    /api/claims/ list endpoint.
  - The frontend can show a running list of everything processed so far.
  - It's straightforward to add reporting/analytics later (e.g. "how many
    claims were fast-tracked this month?").
"""

from django.db import models


class Claim(models.Model):
    class Route(models.TextChoices):
        INVESTIGATION_FLAG = "Investigation Flag", "Investigation Flag"
        MANUAL_REVIEW = "Manual Review", "Manual Review"
        SPECIALIST_QUEUE = "Specialist Queue", "Specialist Queue"
        FAST_TRACK = "Fast-Track", "Fast-Track"
        STANDARD_REVIEW = "Standard Review", "Standard Review"

    # Where the FNOL text came from (nice for the claim history list)
    source_filename = models.CharField(max_length=255, blank=True, default="")

    # The raw FNOL text that was submitted (kept for audit / re-processing)
    raw_text = models.TextField()

    # Structured extraction output. JSONField works out of the box with
    # SQLite on modern Django versions - no extra dependency needed.
    extracted_fields = models.JSONField(default=dict)
    missing_fields = models.JSONField(default=list)

    recommended_route = models.CharField(max_length=32, choices=Route.choices)
    reasoning = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        policy_number = self.extracted_fields.get("policyNumber") or "Unknown Policy"
        return f"Claim #{self.pk} ({policy_number}) -> {self.recommended_route}"
