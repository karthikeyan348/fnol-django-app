"""
serializers.py
--------------
Two serializers:
  - ClaimListSerializer: lightweight, used for the claim history list
    (avoids sending the full raw_text/reasoning for every row).
  - ClaimDetailSerializer: full detail, and also shapes the output to match
    the exact JSON contract required by the assessment brief
    (extractedFields / missingFields / recommendedRoute / reasoning).
"""

from rest_framework import serializers

from .models import Claim


class ClaimListSerializer(serializers.ModelSerializer):
    policyNumber = serializers.SerializerMethodField()

    class Meta:
        model = Claim
        fields = [
            "id",
            "source_filename",
            "policyNumber",
            "recommended_route",
            "created_at",
        ]

    def get_policyNumber(self, obj):
        return obj.extracted_fields.get("policyNumber")


class ClaimDetailSerializer(serializers.ModelSerializer):
    extractedFields = serializers.JSONField(source="extracted_fields")
    missingFields = serializers.JSONField(source="missing_fields")
    recommendedRoute = serializers.CharField(source="recommended_route")

    class Meta:
        model = Claim
        fields = [
            "id",
            "source_filename",
            "created_at",
            "extractedFields",
            "missingFields",
            "recommendedRoute",
            "reasoning",
        ]
