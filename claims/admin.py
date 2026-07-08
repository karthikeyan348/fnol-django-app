from django.contrib import admin

from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ("id", "source_filename", "policy_number", "recommended_route", "created_at")
    list_filter = ("recommended_route", "created_at")
    search_fields = ("source_filename", "raw_text", "reasoning")
    readonly_fields = (
        "source_filename",
        "raw_text",
        "extracted_fields",
        "missing_fields",
        "recommended_route",
        "reasoning",
        "created_at",
    )

    @admin.display(description="Policy Number")
    def policy_number(self, obj):
        return obj.extracted_fields.get("policyNumber", "-")

    def has_add_permission(self, request):
        # Claims are only ever created through the API pipeline (which sets
        # extracted_fields/route/reasoning together); the admin is for
        # viewing/auditing history, not manually authoring claim records.
        return False
