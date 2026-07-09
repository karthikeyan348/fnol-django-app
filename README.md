# FNOL Claims Processing Agent

A Django + Django REST Framework backend that ingests First Notice of Loss
(FNOL) documents (pasted text or uploaded `.txt`/`.pdf` files), extracts
structured fields from them, flags anything missing, and recommends a
routing decision with a human-readable explanation. A React (CDN, no build
step) frontend is served alongside it for manual testing, and every
processed claim is persisted to SQLite so past claims can be browsed via
the API or Django admin.

## Approach

### 1. Rule-based / regex field extraction (`claims/services/extractor.py`)

FNOL intake documents — whether they originate from a PDF export, a web
form, or an email — are almost always structured as `Label: value` lines
(`Policy Number: ...`, `Date: ...`, `Estimated Damage: ...`, etc.). Given
that structure, a label-matching extractor was chosen over an LLM or a
general-purpose NLP model, for a few concrete reasons:

- **Determinism & auditability.** Insurance workflows need to be able to
  explain exactly why a field was or wasn't picked up. A regex match on a
  known label is trivial to trace; a model's extraction is not.
- **No dependency / cost / latency overhead.** No API calls, no model
  weights, no non-determinism between runs — extraction is instant and free.
- **Good fit for the data.** The documents aren't free-form prose that
  needs semantic understanding to parse; they're semi-structured forms.
  Regex-per-field with multiple label aliases (e.g. `"policy number"`,
  `"policy no"`, `"policy #"` all map to `policyNumber`) comfortably covers
  the realistic variation between carriers/forms without needing ML.
- **Easy to extend.** Adding a new field or label variant is a one-line
  addition to the `FIELD_ALIASES` dict — no retraining or prompt tuning.

The tradeoff is that it won't generalize to wildly unstructured, free-text
narratives the way an LLM-based extractor might. If that became a real
requirement, the extractor is isolated behind a single function
(`extract_fields(raw_text) -> dict`), so it could be swapped for a model-based
implementation without touching the classifier, views, or database layer.

Values are also normalized (`normalize_value`) so placeholder tokens like
`"None"`, `"N/A"`, `"-"`, `"TBD"` are treated as genuinely missing rather
than as valid data — otherwise a lazily-filled form would incorrectly pass
validation.

### 2. Priority-ordered classification (`claims/services/classifier.py`)

Once fields are extracted, the claim is routed using a fixed, ordered list
of rules rather than a scoring/weighting model:

1. **Investigation Flag** — suspicious language in the description
   (e.g. "fraud", "inconsistent", "staged"). Always wins, even over an
   otherwise complete/small/clean claim, because a fraud signal has to be
   reviewed by a human before anything else happens.
2. **Manual Review** — any mandatory field is missing/blank. An incomplete
   claim can't be safely auto-routed regardless of its content.
3. **Specialist Queue** — claim type is "Injury". Bodily injury claims need
   a specialist adjuster regardless of dollar amount.
4. **Fast-Track** — complete, no red flags, and estimated damage is below
   the auto-approval threshold (₹25,000 by default).
5. **Standard Review** — fallback: complete and clean, but above the
   fast-track threshold (or damage couldn't be reliably parsed), so a human
   adjuster reviews it at normal priority.

**Why priority order instead of a score/weight system:** a single claim can
satisfy more than one rule simultaneously (e.g. a small claim that also
contains fraud language). The workflow needs exactly one unambiguous
destination per claim, and business rules like "always investigate
suspected fraud first" are naturally expressed as precedence, not as
weights that need tuning to produce the same guarantee. This also keeps the
logic fully explainable — each decision returns a plain-English `reasoning`
string naming the exact rule and data that triggered it, which matters for
an insurance audit trail in a way a black-box score wouldn't.

Both modules are framework-independent (no Django imports), so they're unit
-testable in isolation and orchestrated by `claims/services/agent.py`, which
Django's views call to turn raw text/files into the final JSON response.

## Project Structure

```
fnol-django-app/
├── manage.py
├── requirements.txt
├── fnol_backend/            # Django project settings/urls
├── claims/
│   ├── models.py            # Claim model (persisted results)
│   ├── views.py             # /api/claims/... , /api/samples/... endpoints
│   ├── serializers.py
│   ├── services/
│   │   ├── extractor.py     # rule-based field extraction
│   │   ├── classifier.py    # priority-ordered routing rules
│   │   └── agent.py         # orchestrates extractor + classifier
│   └── migrations/
├── templates/claims/index.html   # React (CDN) frontend
├── static/claims/                # CSS/JS for the frontend
└── samples/                      # example FNOL .txt documents
```

## Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd fnol-django-app

# 2. (recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Run the development server
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`:

- `http://127.0.0.1:8000/` — React frontend (paste text or upload a file)
- `http://127.0.0.1:8000/api/claims/process-text/` — POST `{"rawText": "...", "sourceFilename": "..."}`
- `http://127.0.0.1:8000/api/claims/process-file/` — POST multipart file upload (field `file`)
- `http://127.0.0.1:8000/api/claims/` — GET list of past claims
- `http://127.0.0.1:8000/api/claims/<id>/` — GET full detail of one claim
- `http://127.0.0.1:8000/api/samples/` — GET bundled demo FNOL filenames
- `http://127.0.0.1:8000/admin/` — Django admin (create a superuser with `python manage.py createsuperuser` to access)

Optional: `pypdf` (already in `requirements.txt`) enables uploading `.pdf`
FNOL documents in addition to `.txt`.

## Example request

```bash
curl -X POST http://127.0.0.1:8000/api/claims/process-text/ \
  -H "Content-Type: application/json" \
  -d @samples/sample1_fasttrack.txt
```

Response shape:

```json
{
  "extractedFields": { "policyNumber": "...", "policyholderName": "...", "...": "..." },
  "missingFields": [],
  "recommendedRoute": "Fast-Track",
  "reasoning": "Fast-tracked because all mandatory fields are present, ...",
  "id": 1,
  "createdAt": "2026-07-09T12:34:56.000000+00:00"
}

```

## Running tests

```bash
python manage.py test
```
## assessment video
it is in fnol_project-compressed.mp4

