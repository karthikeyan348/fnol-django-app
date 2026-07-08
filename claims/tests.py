from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Claim
from .services.agent import process_fnol_text

SAMPLE_FAST_TRACK = """
Policy Number: POL-100234
Policyholder Name: Ravi Kumar
Effective Dates: 01-Jan-2026 to 31-Dec-2026
Date: 03-Jul-2026
Time: 14:20
Location: MG Road, Bengaluru, Karnataka
Description: Vehicle was scratched by a shopping cart in a parking lot.
Claimant: Ravi Kumar
Third Parties: None
Contact Details: ravi.kumar@example.com
Asset Type: Motor Vehicle
Asset ID: KA-01-AB-1234
Estimated Damage: 8500
Claim Type: Property Damage
Attachments: photos.zip
Initial Estimate: 8500
"""

SAMPLE_FRAUD = SAMPLE_FAST_TRACK.replace(
    "Description: Vehicle was scratched by a shopping cart in a parking lot.",
    "Description: The scene appears staged and witness accounts are inconsistent.",
)

SAMPLE_MISSING_FIELDS = """
Policy Number: POL-999
Policyholder Name: Test Person
Date: 01-Jul-2026
Description: Minor bump.
Claimant: Test Person
Asset Type: Motor Vehicle
Estimated Damage: 5000
Claim Type: Property Damage
Initial Estimate: 5000
"""


class ServiceLogicTests(TestCase):
    """Tests for the pure business logic (independent of Django views/DB)."""

    def test_fast_track_routing(self):
        result = process_fnol_text(SAMPLE_FAST_TRACK)
        self.assertEqual(result["recommendedRoute"], "Fast-Track")
        self.assertEqual(result["missingFields"], [])

    def test_fraud_keywords_trigger_investigation(self):
        result = process_fnol_text(SAMPLE_FRAUD)
        self.assertEqual(result["recommendedRoute"], "Investigation Flag")

    def test_missing_fields_trigger_manual_review(self):
        result = process_fnol_text(SAMPLE_MISSING_FIELDS)
        self.assertEqual(result["recommendedRoute"], "Manual Review")
        self.assertIn("incidentTime", result["missingFields"])
        self.assertIn("assetId", result["missingFields"])


class ApiEndpointTests(TestCase):
    """Tests for the DRF API endpoints, including database persistence."""

    def setUp(self):
        self.client = APIClient()

    def test_process_text_creates_claim_in_db(self):
        response = self.client.post(
            reverse("process-text"),
            {"rawText": SAMPLE_FAST_TRACK, "sourceFilename": "unit_test.txt"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["recommendedRoute"], "Fast-Track")
        self.assertEqual(Claim.objects.count(), 1)

    def test_process_text_requires_raw_text(self):
        response = self.client.post(reverse("process-text"), {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_claim_list_and_detail(self):
        self.client.post(
            reverse("process-text"),
            {"rawText": SAMPLE_FRAUD, "sourceFilename": "fraud_case.txt"},
            format="json",
        )
        claim = Claim.objects.first()

        list_response = self.client.get(reverse("claim-list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)

        detail_response = self.client.get(reverse("claim-detail", args=[claim.id]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["recommendedRoute"], "Investigation Flag")
        self.assertIn("extractedFields", detail_response.data)
