# Daksha - AI-Powered Underwriting Platform

Daksha is a full-stack, multi-agent underwriting platform for loan and health insurance applications. It combines browser-side OCR (via Puter.js), a multi-step declaration form, a simulated AI agent pipeline, and an explainable decision engine that shows exactly what drove every approval or rejection.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS v3 |
| Routing | Context-based view switching (ShieldContext) |
| OCR | Puter.js (puter.ai.img2txt + puter.ai.chat) - runs in browser, no API key |
| Backend | FastAPI (Python 3.11+), Uvicorn |
| Auth | In-memory token store (token::email scheme) |
| Storage | In-memory Python dicts (api/state.py) - no database |
| ML Models | EBM (Explainable Boosting Machine) .pkl files for loan + insurance |
| Fonts | Crimson Text (serif) + Hanken Grotesk (sans) via Google Fonts |
| Icons | lucide-react |

---

## Running Locally

Backend:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Health check: `GET http://localhost:8000/health` returns `{"status": "ok"}`

---

## Project Structure

```
daksha/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, router registration
│   ├── api/
│   │   ├── state.py             # In-memory stores + token helpers
│   │   ├── auth.py              # Register + login endpoints
│   │   ├── applications.py      # Application CRUD
│   │   └── workflow.py          # KYC, OCR, submit, status, results, stream
│   ├── core/
│   │   ├── config.py            # Settings (env vars)
│   │   ├── security.py          # bcrypt + JWT helpers (unused in active flow)
│   │   └── database.py          # SQLAlchemy setup (unused in active flow)
│   ├── agents/                  # LangGraph agent stubs
│   ├── graph/                   # LangGraph workflow graph
│   ├── ml/                      # EBM model loaders
│   ├── ml_models/               # .pkl model files
│   ├── ocr/                     # OCR service stubs
│   ├── rules/                   # IRDAI + USDA rule text files
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Service layer stubs
│   └── requirements.txt
└── frontend/
    ├── index.html               # Puter.js CDN script tag
    └── src/
        ├── App.jsx              # ShieldProvider + view router
        ├── main.jsx             # React root mount
        ├── index.css            # Tailwind directives + CSS variables
        ├── context/
        │   ├── ShieldContext.jsx # Global app state (single source of truth)
        │   └── AppContext.jsx    # Re-export of ShieldContext
        ├── pages/               # Landing, KYC, Selection, Preliminary, Upload,
        │                        # Config, Analysis, Result, HowItWorks, Partners, About
        ├── components/          # Navbar, AgentStatus, GlassCard, FeatureChart
        ├── hooks/               # useAuth, useWorkflowStream
        └── utils/
            ├── api.js           # All backend fetch calls
            └── ocr.js           # Browser-side Puter.js OCR
```

---

## Authentication

The active auth flow uses a simplified in-memory token scheme (not JWT in production).

On the KYC page, the user enters their name and Aadhaar number. The frontend derives a synthetic email and password:
- email = `<aadhaar>@daksha.local`
- password = `daksha-<aadhaar>`

It calls register (silently ignores 409 if already exists), then login to get a token. The token format is `token::<email>`. All subsequent API calls send this as `Authorization: Bearer <token>`. `parse_token()` in `api/state.py` strips the prefix to recover the email. No JWT signing, no expiry.

### POST /api/auth/register

Input:
```json
{ "email": "string", "password": "string", "name": "string (optional)" }
```
Output (200):
```json
{
  "message": "User registered successfully",
  "user": { "id": "1", "email": "...", "name": "...", "role": "user" }
}
```
Error (409): `{ "detail": "User already exists" }`

### POST /api/auth/login

Input:
```json
{ "email": "string", "password": "string" }
```
Output (200):
```json
{
  "message": "Login successful",
  "access_token": "token::<email>",
  "refresh_token": "token::<email>",
  "user": { "id": "1", "email": "...", "name": "...", "role": "user" }
}
```
Error (401): `{ "detail": "Invalid credentials" }`

---

## In-Memory State (api/state.py)

Four global dicts hold all runtime data. All data is lost on backend restart.

| Dict | Key | Value shape |
|---|---|---|
| `USERS_DB` | email (str) | `{ id, email, password, name, role }` |
| `APPLICATIONS_DB` | app_id (str) | `{ id, user_email, status, request_type, loan_type, applicant_data, uploaded_documents, ... }` |
| `WORKFLOW_DB` | app_id (str) | `{ status, request_id, rejected, loan_prediction, insurance_prediction, ... }` |
| `WORKFLOW_EVENTS` | app_id (str) | list of `{ agent, status }` dicts |

Helper functions:
- `create_token(email)` → `"token::<email>"`
- `parse_token(token)` → email string or None
- `new_id(prefix)` → `"<prefix>_<12-char uuid hex>"`

---

## Applications API

All endpoints require `Authorization: Bearer <token>`.

### POST /api/applications/

Creates a new application in APPLICATIONS_DB with status `"draft"`.

Input:
```json
{
  "request_type": "loan | insurance",
  "loan_type": "home | personal | null",
  "submitted_name": "string",
  "submitted_dob": "YYYY-MM-DD",
  "submitted_aadhaar": "string",
  "applicant_data": { "...all form fields" },
  "uploaded_documents": [
    { "type": "bank_statement", "name": "file.pdf", "mime_type": "application/pdf", "content_base64": "..." }
  ]
}
```
Output:
```json
{ "message": "Application created", "application": { "...full application object" } }
```

### GET /api/applications/

Returns all applications belonging to the authenticated user.

Output:
```json
{ "items": [ "...application objects" ] }
```

---

## Workflow API

### POST /api/workflow/verify-kyc

Validates Aadhaar format and returns mock KYC data including a mock CIBIL score of 742.

Input:
```json
{ "name": "string", "aadhaar": "123456789012", "dob": "YYYY-MM-DD" }
```
Validation: name and aadhaar required, aadhaar must be exactly 12 digits.

Output (200):
```json
{
  "verified": true,
  "kyc_data": {
    "name": "string",
    "aadhaar_number": "123456789012",
    "dob": "YYYY-MM-DD",
    "cibil_score": 742,
    "gender": "Male",
    "address": "Mock Address, India"
  }
}
```
Error (400): `{ "detail": "Aadhaar must be exactly 12 digits" }`

---

### POST /api/workflow/preview-ocr

Two-path endpoint. If the frontend sends `client_ocr` (Puter.js pre-extracted JSON), it runs server-side cross-validation. Otherwise it falls back to raw document validation.

**Path A — client_ocr present (Puter.js flow)**

Input:
```json
{
  "request_type": "loan | insurance",
  "declared_data": { "...applicant form fields" },
  "uploaded_documents": [ "...base64 docs" ],
  "client_ocr": {
    "extracted_data": {
      "monthly_income": 85000,
      "existing_emi": 5000,
      "property_value": 5000000,
      "employer_name": "Acme Corp"
    },
    "document_freshness_passed": true,
    "consistency_flags": [],
    "confidence_score": 0.92,
    "raw_by_type": {
      "salary_slip": { "employee_name": "...", "employer_name": "...", "net_income": 85000, "slip_date": "2026-01-01" },
      "bank_statement": { "account_name": "...", "recurring_salary_deposits": 84000, "statement_date": "2026-02-01" },
      "aadhaar_card": { "full_name": "...", "dob": "1993-05-10", "id_number": "..." }
    }
  }
}
```

Server-side cross-validation (`_cross_validate_ocr`):
- Name match: salary slip employee name = bank account name = ID proof full name (case-insensitive)
- Income match: salary slip net income vs bank recurring deposits — flags if difference > 20%
- Freshness: salary slip must be within 3 months, bank statement within 6 months

Output (200):
```json
{
  "ocr_extracted_data": { "...merged prefill fields" },
  "declared_prefill": { "...merged prefill fields" },
  "consistency_flags": [ "Name mismatch: ...", "Income mismatch: ..." ],
  "document_freshness_passed": true,
  "confidence_score": 0.92
}
```

**Path B — raw documents fallback**

Validates each uploaded document:
- Checks required doc types are present (`bank_statement`, `salary_slip`, `aadhaar_card` for loan; `diagnostic_report`, `aadhaar_card` for insurance)
- Decodes base64 and checks file size — rejects files under 500 bytes
- Validates MIME type (PDF, JPG, PNG only)
- Computes simulated confidence score per document based on file size (range 10–98%)

Error (422):
```json
{
  "detail": {
    "message": "Document validation failed",
    "errors": [ "Missing required documents: bank statement", "'file.txt' has unsupported format..." ],
    "confidence_scores": { "bank_statement": 0.0 }
  }
}
```

Output (200):
```json
{
  "ocr_extracted_data": { "...prefilled fields" },
  "declared_prefill": { "...prefilled fields" },
  "ocr_documents": [ "...uploaded docs" ],
  "confidence_scores": { "bank_statement": 87.3, "aadhaar_card": 91.0 },
  "consistency_flags": [],
  "document_freshness_passed": true
}
```

---

### POST /api/workflow/submit/{application_id}

Marks the application as completed and populates WORKFLOW_DB with mock results.

Output (200):
```json
{ "message": "Workflow started", "app_id": "app_abc123", "request_id": "req_xyz456", "status": "processing" }
```
Errors: 404 (not found), 403 (wrong user), 400 (already submitted)

---

### GET /api/workflow/status/{application_id}

Returns current workflow status from WORKFLOW_DB.

Output:
```json
{
  "app_id": "app_abc123",
  "status": "completed",
  "request_id": "req_xyz456",
  "rejected": false,
  "rejection_reason": null,
  "loan_prediction": { "approved": true, "probability": 0.84 },
  "insurance_prediction": { "premium": 15300 }
}
```

---

### GET /api/workflow/results/{application_id}

Returns full results including model feature contributions.

Output:
```json
{
  "app_id": "app_abc123",
  "request_id": "req_xyz456",
  "loan": {
    "prediction": { "approved": true, "probability": 0.84 },
    "explanation": "Income stability and credit profile support approval.",
    "description": "Loan approved with strong affordability ratio."
  },
  "insurance": {
    "prediction": { "premium": 15300 },
    "explanation": "Health and lifestyle profile support moderate premium.",
    "description": "Premium estimated from age and reported health profile."
  },
  "ocr_confidence_scores": { "bank_statement": 92.0, "aadhaar_card": 96.0 },
  "model_output": {
    "loan": {
      "feature_contributions": {
        "credit_score": 0.38, "monthly_income": 0.29, "emi_load": -0.17,
        "loan_to_value": -0.12, "employment_stability": 0.21, "debt_to_income": -0.09
      }
    },
    "insurance": {
      "feature_contributions": {
        "age": -0.22, "smoker": -0.31, "bmi": -0.18,
        "pre_existing_diseases": -0.14, "family_history": -0.08, "sum_insured": 0.11
      }
    }
  },
  "completed": true
}
```

---

### GET /api/workflow/stream/{application_id}

Server-Sent Events stream. Emits one event per agent step, then a done signal.

```
data: {"agent": "kyc", "status": "complete"}
data: {"agent": "onboarding", "status": "complete"}
data: {"done": true}
```

---

## Browser-Side OCR (frontend/src/utils/ocr.js)

Uses Puter.js loaded from CDN (`https://js.puter.com/v2/`). No API key required — User-Pays model.

### ocrDocument(file, docType)

Input: a `File` object and a document type string.

Steps:
1. Calls `window.puter.ai.img2txt(file)` to extract raw text from the image/PDF
2. Builds a structured extraction prompt for the document type
3. Calls `window.puter.ai.chat(prompt + rawText)` to parse structured JSON fields
4. Strips markdown code fences and parses the JSON response (falls back to regex extraction if needed)

Document types and extracted fields:

| docType | Extracted fields |
|---|---|
| `bank_statement` | `account_name`, `current_balance`, `avg_monthly_balance`, `recurring_salary_deposits`, `statement_date`, `bank_name` |
| `salary_slip` | `employee_name`, `employer_name`, `net_income`, `slip_date` |
| `loan_statement` | `current_emi`, `outstanding_balance`, `lender_name` |
| `property_document` | `property_value`, `owner_name`, `property_address` |
| `aadhaar_card` | `full_name`, `dob`, `id_number` |
| `diagnostic_report` | `patient_name`, `report_date`, `diagnosis` |
| `itr` | `taxpayer_name`, `annual_income`, `assessment_year` |

Returns:
```js
{ docType: "bank_statement", extracted: { account_name: "...", net_income: 85000 }, rawText: "...", error: null }
// on failure:
{ docType: "bank_statement", extracted: null, rawText: null, error: "OCR failed" }
```

### validateOcrResults(ocrResults)

Input: array of `ocrDocument()` results.

Cross-document consistency checks:
- Name consistency: `salary_slip.employee_name` = `bank_statement.account_name` = `aadhaar_card.full_name` (case-insensitive exact match). Flags each mismatched pair.
- Income consistency: `salary_slip.net_income` vs `bank_statement.recurring_salary_deposits` — flags if difference > 20%
- Freshness: salary slip must be dated within 3 months of today, bank statement within 6 months

Confidence scoring:
- Starts at 1.0
- Deducts 0.15 per consistency flag raised
- Deducts 0.1 if monthly income could not be extracted from any document
- Deducts 0.1 if no ID proof (aadhaar_card) was scanned
- Clamped to minimum 0.1

Income extraction priority: `salary_slip.net_income` → `itr.annual_income / 12` → `bank_statement.recurring_salary_deposits`

Returns:
```js
{
  extracted_data: { monthly_income: 85000, existing_emi: 5000, property_value: 5000000, employer_name: "Acme" },
  document_freshness_passed: true,
  consistency_flags: [ "Name mismatch: Salary slip (\"John\") != ID proof (\"John Doe\")" ],
  confidence_score: 0.85,
  raw_by_type: { bank_statement: {...}, salary_slip: {...}, aadhaar_card: {...} }
}
```

---

## Frontend API Client (frontend/src/utils/api.js)

Base URL: `VITE_API_URL` env var, defaults to `http://localhost:8000/api`.

All functions throw `Error` with the detail message on non-2xx responses. FastAPI 422 structured errors are serialized as JSON strings so the caller can parse and display individual error lines.

| Function | Method | Endpoint | Auth |
|---|---|---|---|
| `registerUser(payload)` | POST | `/auth/register` | No |
| `loginUser(payload)` | POST | `/auth/login` | No |
| `verifyKyc(token, payload)` | POST | `/workflow/verify-kyc` | Bearer |
| `createApplication(token, payload)` | POST | `/applications/` | Bearer |
| `previewOcr(token, payload)` | POST | `/workflow/preview-ocr` | Bearer |
| `submitWorkflow(token, appId)` | POST | `/workflow/submit/:id` | Bearer |
| `getWorkflowStatus(token, appId)` | GET | `/workflow/status/:id` | Bearer |
| `getWorkflowResults(token, appId)` | GET | `/workflow/results/:id` | Bearer |

---

## Global State (ShieldContext.jsx)

Single React context wrapping the entire app. All pages read and write to this context — no prop drilling.

| Field | Type | Purpose |
|---|---|---|
| `view` | string | Current page: `landing`, `kyc`, `selection`, `prelim`, `upload`, `config`, `analysis`, `result`, `how`, `partner`, `about` |
| `service` | `'loan'` / `'insurance'` / null | Selected service type |
| `loanType` | `'home'` / `'personal'` | Loan sub-type |
| `userData` | object | `{ aadhaar, name, dob, email, password }` |
| `kycData` | object | Response from `/verify-kyc`: `{ name, aadhaar_number, dob, cibil_score, gender, address }` |
| `applicantData` | object | Merged form data from Preliminary + Config pages |
| `uploadedDocs` | object | `{ [docLabel]: true }` — tracks which doc cards are checked in the UI |
| `uploadedDocuments` | array | `[{ type, name, mime_type, content_base64 }]` — raw base64 docs for backend |
| `ocrPreviewData` | object | OCR-extracted fields merged with declared data. Internal metadata: `_ocr_confidence` (float), `_ocr_flags` (string[]), `_ocr_freshness` (boolean) |
| `authToken` | string / null | Bearer token from login |
| `applicationId` | string / null | Created application ID |
| `requestId` | string / null | Workflow request ID |
| `workflowStatus` | object / null | Latest status poll response |
| `workflowResult` | object / null | Full results from `/results` endpoint |
| `workflowError` | string / null | Error message if workflow fails |

---

## Page-by-Page Flow

### 1. Landing (view: landing)

Marketing page. Sections: hero with large "Daksha" serif heading + CTA, multi-agent architecture cards (5 agents + transparent decisions card), "What Daksha Checks" (income verification, document authenticity, regulatory compliance), "Why Choose Daksha" (explainable AI, OTP KYC, fraud-resistant, sub-2-minute decisions), footer. CTA navigates to `kyc`.

### 2. KYC (view: kyc)

Collects full name and 12-digit Aadhaar number. On submit:
1. Derives `<aadhaar>@daksha.local` email and `daksha-<aadhaar>` password
2. Calls `registerUser` — silently ignores 409
3. Calls `loginUser` → stores `authToken`
4. Calls `verifyKyc` → stores `kycData` (includes mock CIBIL score 742)
5. Navigates to `selection`

Validation: Aadhaar input strips non-digits on change. Submit button disabled until exactly 12 digits entered and name is non-empty.

### 3. Selection (view: selection)

Two clickable cards: "Loan Shield" (Landmark icon) and "Life Shield" (Heart icon). Clicking sets `service` and navigates to `prelim`.

### 4. Preliminary (view: prelim)

Collects minimal required fields before document upload.

Loan required: `loan_type`, `loan_amount_requested`, `tenure_months`. Optional: `property_value` (home loans only).
Insurance required: `age`, `city`, `sum_insured`.

On continue: validates required fields, merges into `applicantData`, sets `loanType`, navigates to `upload`.

### 5. Upload (view: upload)

Document upload with live browser-side OCR running immediately on file select.

Loan documents: Bank Statement (required), Salary Slip (required), Existing Loan Statements (optional), Property Documents (required for home), ID Proof (required).
Insurance documents: Medical Reports (required), ID Proof (required), Income Proof/ITR (optional).

Per-document flow on file select:
1. Validates file size ≤ 5MB
2. Reads file as base64 via FileReader, stores in `uploadedDocuments` (deduplicates by doc type)
3. Marks doc card as uploaded (lime dashed border, checkmark icon)
4. If `window.puter` is defined: runs `ocrDocument(file, docType)` asynchronously
5. Shows per-card status badge: spinning Loader2 while running → green "OCR ✓" on success → amber "OCR skipped" on error

OCR extracted data panel: appears below upload cards once at least one document is successfully scanned. Shows a grid of all extracted fields per document type with human-readable labels. Numeric values formatted as `₹ X,XX,XXX` (Indian locale).

Consistency flags panel: amber warning box listing name mismatches, income mismatches, or stale documents. Non-blocking — user can still continue.

On "Continue to Declaration Form":
- If client OCR results exist: runs `validateOcrResults()`, shows consistency flags, merges extracted fields into `ocrPreviewData` with `_ocr_confidence`, `_ocr_flags`, `_ocr_freshness` metadata, navigates to `config` directly
- If no OCR results: calls backend `/preview-ocr` with raw base64 documents as fallback

Button disabled while any OCR is still running or backend call is in progress.

### 6. Config / Declaration Form (view: config)

Full declaration form pre-filled from OCR + KYC data.

OCR confidence banner: lime badge showing `OCR confidence: XX%`.
OCR flags banner: amber box listing document inconsistency flags (if any).
OCR field highlighting: fields populated by OCR show a lime "OCR" badge next to the label and a lime-tinted border + background.

Loan form sections:

Personal Profile: age*, gender*, city*, marital status, employment type (Salaried/Self-employed), employer category (Govt/MNC/Pvt Ltd/Small firm), total work experience (years), current company tenure (years), residential status.

Loan Details: loan type* (Home/Personal), loan amount*, tenure in months*, property value (OCR-highlighted, home only), property city (home only), property type (home only).

Financial Declaration: declared monthly income* (OCR-highlighted), declared existing EMI* (OCR-highlighted), credit score*.

Insurance form sections:

Health Profile: age*, gender*, city*, family size, height in cm*, weight in kg*, smoker (No/Yes), alcohol (None/Moderate/High).

Medical History: pre-existing diseases (multi-select checkboxes: Diabetes, Hypertension, Asthma, Cardiac, Thyroid, None — selecting None clears others), family history.

Coverage: sum insured*, deductible.

On submit: validates required fields, merges into `applicantData` + `userData`, navigates to `analysis`.

### 7. Analysis (view: analysis)

Dark forest-colored page showing the multi-agent pipeline running.

Agent steps (9 total): KYC Agent, Onboarding Agent, Rules Agent, Fraud Agent, Feature Engineering, Compliance Agent, Underwriting Agent, Verification Agent, Transparency Agent.

Each step rendered by `AgentStatus`: pending (dim), running (lime spinner), complete (teal checkmark).

Workflow execution:
1. Calls `createApplication` with all collected data
2. Calls `submitWorkflow` — silently ignores "already submitted" error
3. Polls `getWorkflowStatus` every 2 seconds, advances step counter on each successful poll
4. On `status === 'completed'`: calls `getWorkflowResults`, stores in `workflowResult`, navigates to `result`
5. On `status === 'failed'`: shows error message in red
6. Max 5 retries on network errors; retry counter shown in amber

Progress bar fills proportionally to current step. `runRef` prevents double-execution on re-renders.

### 8. Result (view: result)

Hero decision card (three variants):
- Loan: dark forest card, large lime approval probability percentage, "Approved"/"Under Review" badge
- Insurance: teal card, estimated annual premium in ₹ (Indian locale), "Health Risk Assessed" badge
- Rejected: red card with rejection reason text

AI Summary card: plain-text explanation string from the backend.

"What drove this decision" panel: feature contributions sorted by absolute impact. For each feature:
- Icon: TrendingUp (green) for positive, TrendingDown (red) for negative, Minus (grey) for near-zero (abs < 0.03)
- Human-readable label (mapped from raw key, e.g. "emi_load" → "EMI Burden")
- Signed score badge: green pill for positive (+0.38), red pill for negative (-0.17)
- Proportional bar: width = abs(value) / max(abs(all values)) × 100%, green for positive, red for negative
- Plain-English explanation sentence (different text for positive vs negative value)

Loan feature explanations:
- `credit_score` / Credit Score: strong history boosts approval / lower score reduces confidence
- `monthly_income` / Monthly Income: income supports loan / insufficient for loan size
- `emi_load` / EMI Burden: low EMIs leave room / high EMIs reduce capacity (FOIR exceeded)
- `loan_to_value` / Loan-to-Value Ratio: strong collateral / loan high relative to property (LTV risk)
- `employment_stability` / Employment Stability: stable employment / short tenure raises risk
- `debt_to_income` / Debt-to-Income Ratio: debt within limits / total debt high relative to income

Insurance feature explanations:
- `age` / Age: lower-risk bracket / older age raises actuarial risk
- `smoker` / Smoking Status: non-smoker lowers risk / smoking substantially increases premium
- `bmi` / BMI / Weight: healthy BMI / outside range raises risk
- `pre_existing_diseases` / Pre-existing Conditions: no conditions / declared conditions increase risk
- `family_history` / Family Medical History: no concerning history / chronic illness history raises risk
- `sum_insured` / Sum Insured: proportionate coverage / high coverage increases premium

Unknown keys fall back to title-cased label and generic positive/negative explanation.

OCR Extracted Data panel: summary grid of key fields extracted from documents (Monthly Income, Existing EMI, Property Value, Employer, Name (ID), Date of Birth). Numeric values formatted as ₹ Indian locale. Confidence percentage badge in lime. Any `_ocr_flags` shown as amber bullet list below the grid.

"Start New Application" button resets view to `landing`.

---

## Components

### Navbar

Floating navigation bar. Transparent and full-width at top of page (scrollY ≤ 40px). Morphs to dark forest rounded pill on scroll (scrollY > 40px). Transition uses cubic-bezier easing over 500ms. Logo navigates to `landing`. Nav links (desktop only): How It Works, Partners, About. Shows user name + "Sign out" when authenticated; "Get Started" otherwise. Sign out clears `authToken` and navigates to `landing`.

### AgentStatus

Renders a single agent step row. Props: `name`, `description`, `status`.

| Status | Appearance |
|---|---|
| `pending` / `waiting` | 40% opacity, grey circle, muted text |
| `running` / `loading` | Lime-tinted background, lime border ring, animated SVG spinner |
| `complete` | Teal-tinted background, teal checkmark circle |

### GlassCard

White card with subtle border and shadow. Accepts `className` prop. Used as container in Config and Result pages.

### FeatureChart

Legacy bar chart component showing feature contributions as horizontal bars. Superseded by the inline feature explanation section in Result.jsx.

---

## Hooks

### useAuth

Thin wrapper around ShieldContext. Returns `{ authToken, setAuthToken, userData, setUserData }`.

### useWorkflowStream

Opens an `EventSource` SSE connection to `/api/workflow/stream/:applicationId`. Returns `{ events: Array<object>, connected: boolean }`. Events parsed as JSON. Connection closes on error or unmount. Not currently used in the main Analysis flow (which uses polling) but available for real-time streaming.

---

## Design System

Colors:
- `#04221f` — forest green (primary dark, hero backgrounds, button fill, text)
- `#005b52` — teal (brand color, borders, labels, secondary text)
- `#dbf226` — lime yellow (accent, CTA hover, OCR badges, progress bars, agent spinner)
- `#f7faf9` — off-white (page backgrounds, card backgrounds)

Typography:
- Serif: Crimson Text (400, 600, 700, italic) — headings, logo, hero text
- Sans: Hanken Grotesk (400, 500, 600, 700) — body, labels, UI elements

CSS variables in `frontend/src/index.css`:
```css
--font-serif: 'Crimson Text', Georgia, serif;
--font-sans: 'Hanken Grotesk', system-ui, sans-serif;
```

Tailwind v3 directives: `@tailwind base; @tailwind components; @tailwind utilities;`

---

## Known Limitations

- Auth tokens have no expiry and are not cryptographically signed — for demo only. `core/security.py` (bcrypt + JWT) exists but is not used.
- All data is lost on backend restart (in-memory store). `core/database.py` (SQLAlchemy + aiosqlite) exists but is not wired up.
- Workflow results are static mock data — the EBM models in `ml_models/` and LangGraph agents in `agents/` are not connected to the active API flow.
- Puter.js OCR requires the user to be signed into a Puter account in their browser. If not signed in, OCR silently fails and the backend fallback path is used.
- The backend fallback OCR path (`_extract_fields`) returns mock values for missing fields rather than real OCR extraction.
- `useWorkflowStream` SSE hook is implemented but not used in the current Analysis page (polling is used instead).
- `FeatureChart` component is implemented but superseded by the inline feature explanation in Result.jsx.
