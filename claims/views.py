"""
views.py
--------
API endpoints:

  POST /api/claims/process-text/   { "rawText": "...", "sourceFilename": "..." }
        -> runs the FNOL pipeline on pasted/raw text, saves a Claim row,
           returns the result JSON.

  POST /api/claims/process-file/   multipart/form-data, field name "file"
        -> runs the FNOL pipeline on an uploaded .txt/.pdf file, saves a
           Claim row, returns the result JSON.

  GET  /api/claims/                 -> list of past claims (summary)
  GET  /api/claims/<id>/            -> full detail for one past claim

  GET  /api/samples/                -> list of bundled demo FNOL filenames
  GET  /api/samples/<filename>/     -> raw text of one bundled demo file
                                        (used by the "quick test" chips in
                                        the frontend so users can try the
                                        agent without writing their own FNOL)
"""

from pathlib import Path

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Claim
from .serializers import ClaimDetailSerializer, ClaimListSerializer
from .services.agent import process_fnol_text, process_uploaded_file

SAMPLES_DIR = Path(settings.BASE_DIR) / "samples"


def _save_and_respond(result: dict, source_filename: str, raw_text: str) -> Response:
    """Persist a pipeline result to the database and return it as JSON."""
    claim = Claim.objects.create(
        source_filename=source_filename,
        raw_text=raw_text,
        extracted_fields=result["extractedFields"],
        missing_fields=result["missingFields"],
        recommended_route=result["recommendedRoute"],
        reasoning=result["reasoning"],
    )
    payload = dict(result)
    payload["id"] = claim.id
    payload["createdAt"] = claim.created_at.isoformat()
    return Response(payload, status=status.HTTP_201_CREATED)


class ProcessTextView(APIView):
    """Process raw FNOL text pasted directly into the frontend."""

    def post(self, request):
        raw_text = (request.data.get("rawText") or "").strip()
        source_filename = request.data.get("sourceFilename") or "(pasted text)"

        if not raw_text:
            return Response(
                {"error": "rawText is required and cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = process_fnol_text(raw_text)
        return _save_and_respond(result, source_filename, raw_text)


class ProcessFileView(APIView):
    """Process an uploaded .txt/.pdf FNOL document."""

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error": "No file uploaded. Attach a file under the 'file' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = process_uploaded_file(uploaded_file)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Re-read isn't possible after parsing (stream consumed), so store
        # a plain-text snapshot only when we can; otherwise store a note.
        raw_text_note = f"[Original file: {uploaded_file.name}]"
        return _save_and_respond(result, uploaded_file.name, raw_text_note)


class ClaimListView(ListAPIView):
    """GET /api/claims/ - history of all processed claims (summary view)."""

    queryset = Claim.objects.all()
    serializer_class = ClaimListSerializer


class ClaimDetailView(RetrieveAPIView):
    """GET /api/claims/<id>/ - full detail for one processed claim."""

    queryset = Claim.objects.all()
    serializer_class = ClaimDetailSerializer


@api_view(["GET"])
def list_samples(request):
    """List the bundled demo FNOL filenames (for the frontend's quick-test chips)."""
    if not SAMPLES_DIR.exists():
        return Response([])
    filenames = sorted(p.name for p in SAMPLES_DIR.glob("*.txt"))
    return Response(filenames)


@api_view(["GET"])
def get_sample_text(request, filename):
    """Return the raw text of one bundled demo FNOL file, by filename."""
    safe_name = Path(filename).name  # strip any path traversal attempt
    file_path = SAMPLES_DIR / safe_name
    if not file_path.exists() or file_path.suffix != ".txt":
        return Response({"error": "Sample not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response({"rawText": file_path.read_text(encoding="utf-8")})

