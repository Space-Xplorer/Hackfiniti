# Daksha — AI-Powered Loan & Insurance Underwriting Platform

Daksha is a full-stack web application that automates loan and health insurance underwriting using document OCR, rule-based validation, and ML-based risk scoring. It provides applicants with a transparent, step-by-step decision with feature-level explanations, a risk scorecard, and a personalised improvement plan.

---

## Architecture Overview

```
frontend/          React + Vite + Tailwind SPA (single-page, view-based routing)
backend/           FastAPI REST API (in-memory state, no DB required for demo)
  api/             Route handlers
  agents/          LangGraph agent definitions (not in active call path — future)
  graph/           LangGraph workflow definition (future integration)
  ml/              EBM model loaders and scorers
  ml_models/       Serialised .pkl model files
  ocr/             OCR service abstraction (mock + production)
  rules/           Plain-text underwriting rule files (IRDAI, USDA)
  schemas/         Pydantic request/response schemas
  services/        Business logic services
  core/            Config, database, security utilities
```

---

## Application Flow (User Journey)

```
Landing → KYC → Selection → Preliminary → Upload → Config (Declaration) → Analysis → Result
```

Each step is a React view controlled by `ShieldContext`. There is no URL routing — `setView(name)` drives navigation.

---

## Frontend Pages

### `Landing.jsx`
Entry point. Displays product branding and a "Get Started" CTA that navigates to `kyc`.

### `KYC.jsx`
**Purpose:** Identity verification and account creation.

**Inputs (user-entered):**
| Field | Type | Validation |
|---|---|---|
| Full Name | text | Required |
| Aadhaar Number | text | Exactly 12 digits |

**What it does:**
1. Derives a synthetic email (`<aadhaar>@daksha.local`) and password (`daksha-<aadhaar>`) — no real email needed.
2. Calls `POST /api/auth/register` — silently ignores 409 (already exists).
3. Calls `POST /api/auth/login` → stores `access_token` in `ShieldContext`.
4. Calls `POST /api/workflow/verify-kyc` → stores returned `kyc_data` (name, DOB, CIBIL score, gender, address).
5. Navigates to `selection`.

**State written:** `authToken`, `kycData`, `userData`

---

### `Selection.jsx`
**Purpose:** Choose service type.

**Options:**
- Loan Shield → sets `service = 'loan'`, navigates to `prelim`
- Life Shield → sets `service = 'insurance'`, navigates to `prelim`

**State written:** `service`

---

### `Preliminary.jsx`
**Purpose:** Capture minimal loan or insurance parameters before document upload.

**Loan inputs:**
| Field | Required |
|---|---|
| Loan Type (home / personal) | Yes |
| Loan Amount Requested (₹) | Yes |
| Tenure (months) | Yes |
| Property Value (₹) | Only for home loans |

**Insurance inputs:**
| Field | Required |
|---|---|
| Age | Yes |
| City | Yes |
| Sum Insured (₹) | Yes |

**State written:** `applicantData`, `loanType`

---

### `Upload.jsx`
**Purpose:** Document upload with browser-side OCR via Puter.js.

**Required documents — Loan:**
| Document | Type key | Required |
|---|---|---|
| Bank Statement (6 months) | `bank_statement` | Yes |
| Salary Slip (last 3 months) | `salary_slip` | Yes |
| ID Proof (Aadhaar) | `aadhaar_card` | Yes |
| Existing Loan Statements | `loan_statement` | No |
| Property Documents | `property_document` | Home loans only |

**Required documents — Insurance:**
| Document | Type key | Required |
|---|---|---|
| Medical Reports | `diagnostic_report` | Yes |
| ID Proof (Aadhaar) | `aadhaar_card` | Yes |
| Income Proof (ITR) | `itr` | No |

**File constraints:** PDF, JPG, PNG; max 5 MB per file.

**OCR pipeline (Puter.js path — when `window.puter` is available):**
1. `ocrDocument(file, docType)` in `utils/ocr.js`:
   - Calls `puter.ai.img2txt(file)` → raw text
   - Calls `puter.ai.chat(prompt + rawText)` with a document-type-specific structured extraction prompt
   - Returns `{ docType, extracted, rawText, error }`
2. `validateOcrResults(ocrResults)` cross-validates all scanned documents:
   - Name consistency across salary slip, bank statement, and Aadhaar
   - Income consistency: salary slip net income vs bank recurring deposits (>20% diff = flag)
   - Document freshness: salary slip must be ≤3 months old; bank statement ≤6 months old
   - Computes a `confidence_score` (starts at 1.0, deducted per flag and missing field)
3. Merged OCR data is stored in `ocrPreviewData` with special keys:
   - `_ocr_confidence` — float 0–1
   - `_ocr_flags` — array of consistency warning strings
   - `_ocr_freshness` — boolean

**Fallback (no Puter.js):** Sends raw base64 documents to `POST /api/workflow/preview-ocr` for server-side validation and mock extraction.

**OCR fields extracted per document type:**

| Doc type | Extracted fields |
|---|---|
| `bank_statement` | account_name, current_balance, avg_monthly_balance, recurring_salary_deposits, statement_date, bank_name |
| `salary_slip` | employee_name, employer_name, net_income, slip_date |
| `loan_statement` | current_emi, outstanding_balance, lender_name |
| `property_document` | property_value, owner_name, property_address |
| `aadhaar_card` | full_name, dob, id_number |
| `diagnostic_report` | patient_name, report_date, diagnosis |
| `itr` | taxpayer_name, annual_income, assessment_year |

**State written:** `uploadedDocs`, `uploadedDocuments`, `ocrPreviewData`

---

### `Config.jsx` (Declaration Form)
**Purpose:** Full applicant declaration form, pre-filled from OCR and KYC data. Fields populated by OCR are highlighted with a yellow "OCR" badge.

**Loan fields:**

*Personal Profile:*
| Field | Required |
|---|---|
| Age | Yes |
| Gender | Yes |
| City | Yes |
| Marital Status | No |
| Employment Type (Salaried / Self-employed) | No |
| Employer Category (Govt / MNC / Pvt Ltd / Small firm) | No |
| Total Work Experience (years) | No |
| Current Company Tenure (years) | No |
| Residential Status | No |

*Loan Details:*
| Field | Required |
|---|---|
| Loan Type | Yes |
| Loan Amount Requested (₹) | Yes |
| Tenure (months) | Yes |
| Property Value (₹) | Home loans |
| Property City | No |
| Property Type | No |

*Financial Declaration:*
| Field | Required | OCR-prefilled |
|---|---|---|
| Declared Monthly Income (₹) | Yes | Yes (from salary slip / bank statement) |
| Declared Existing EMI (₹) | Yes | Yes (from loan statement) |
| Credit Score | Yes | No (manual entry) |

**Insurance fields:**

*Health Profile:* Age, Gender, City, Family Size, Height (cm), Weight (kg), Smoker (Yes/No), Alcohol (None/Moderate/High)

*Medical History:* Pre-existing Diseases (multi-select: Diabetes, Hypertension, Asthma, Cardiac, Thyroid, None), Family History (text)

*Coverage:* Sum Insured (₹), Deductible (₹)

**State written:** `applicantData`, `userData`

---

### `Analysis.jsx`
**Purpose:** Workflow execution and progress display.

**Agent steps shown (UI only — simulated progress):**
1. KYC Agent — Verifying identity
2. Onboarding Agent — OCR extraction
3. Rules Agent — Checking underwriting rules
4. Fraud Agent — OCR fraud scan
5. Feature Engineering — Deriving risk features
6. Compliance Agent — Regulatory checks
7. Underwriting Agent — Model inference
8. Verification Agent — Sanity checks
9. Transparency Agent — Explanation draft

**What it does:**
1. Calls `POST /api/applications/` to create an application record.
2. Calls `POST /api/workflow/submit/{app_id}` to trigger processing.
3. Polls `GET /api/workflow/status/{app_id}` every 2 seconds (max 5 retries on error).
4. On `status = completed`, calls `GET /api/workflow/results/{app_id}` and navigates to `result`.

**State written:** `applicationId`, `requestId`, `workflowStatus`, `workflowResult`

---

### `Result.jsx`
**Purpose:** Full decision display with 5 sections.

**Section 1 — Hero Decision Card**
- Loan: approval probability (0–100%), approved/under-review badge, risk grade (A–E)
- Insurance: estimated annual premium (₹), risk category (Low/Medium/High)
- Rejected: red card with rejection reason

**Section 2 — AI Summary**
Plain-English explanation of the decision, generated by the backend from the applicant's actual values (CIBIL, FOIR, LTV, BMI, smoking status, etc.).

**Section 3 — What Drove This Decision (Feature Contributions)**
Each feature is shown with:
- Label (human-readable name)
- Signed contribution value (positive = helped, negative = hurt)
- Proportional bar chart
- Plain-English explanation of why that value helped or hurt

Loan features: Credit Score, Monthly Income, EMI Burden, Loan-to-Value Ratio, Employment Stability, Debt-to-Income Ratio

Insurance features: Age, Smoking Status, BMI/Weight, Pre-existing Conditions, Family Medical History, Sum Insured

**Section 4 — OCR Extracted Data**
Displays the data that was read from uploaded documents:
- Monthly Income, Existing EMI, Property Value, Employer, Name (ID), Date of Birth
- OCR confidence score badge
- Document flags (name mismatches, income mismatches, stale documents) shown as warnings

**Section 5 — Start New Application button**

---

## Backend API

Base URL: `http://localhost:8000/api`

All protected endpoints require `Authorization: Bearer <token>` header.

---

### Auth

#### `POST /api/auth/register`
**Input:**
```json
{ "email": "string", "password": "string", "name": "string (optional)" }
```
**Output:**
```json
{ "message": "User registered successfully", "user": { "id", "email", "name", "role" } }
```
**Errors:** 409 if email already exists.

---

#### `POST /api/auth/login`
**Input:**
```json
{ "email": "string", "password": "string" }
```
**Output:**
```json
{
  "message": "Login successful",
  "access_token": "string",
  "refresh_token": "string",
  "user": { "id", "email", "name", "role" }
}
```
**Errors:** 401 if credentials invalid.

Token format: `<email>:<timestamp>` base64-encoded (stateless, no JWT library in active path).

---

### Applications

#### `POST /api/applications/`
Creates a new application record (status: `draft`).

**Input:**
```json
{
  "request_type": "loan | insurance",
  "loan_type": "home | personal | null",
  "submitted_name": "string",
  "submitted_dob": "string",
  "submitted_aadhaar": "string",
  "applicant_data": { ...all declaration form fields... },
  "uploaded_documents": [
    { "type": "bank_statement", "name": "file.pdf", "mime_type": "application/pdf", "content_base64": "..." }
  ]
}
```
**Output:**
```json
{ "message": "Application created", "application": { "id", "user_email", "status", "request_type", ... } }
```

---

#### `GET /api/applications`
Lists all applications for the authenticated user.

**Output:**
```json
{ "items": [ { ...application objects... } ] }
```

---

### Workflow

#### `POST /api/workflow/verify-kyc`
**Input:**
```json
{ "name": "string", "aadhaar": "12-digit string", "dob": "string (optional)" }
```
**Output:**
```json
{
  "verified": true,
  "kyc_data": {
    "name": "string",
    "aadhaar_number": "string",
    "dob": "string",
    "cibil_score": 742,
    "gender": "Male",
    "address": "Mock Address, India"
  }
}
```
**Errors:** 400 if name/Aadhaar missing or Aadhaar not 12 digits.

---

#### `POST /api/workflow/preview-ocr`
Validates uploaded documents and extracts fields. Supports two paths:

**Path A — Client OCR JSON (preferred):**
Input includes `client_ocr` with pre-extracted data from Puter.js.
```json
{
  "request_type": "loan",
  "declared_data": { ...form fields... },
  "client_ocr": {
    "extracted_data": { "monthly_income": 85000, "existing_emi": 5000, ... },
    "raw_by_type": {
      "salary_slip": { "employee_name": "...", "net_income": 85000, "slip_date": "2026-01-01" },
      "bank_statement": { "account_name": "...", "recurring_salary_deposits": 84000, "statement_date": "2026-02-01" },
      "aadhaar_card": { "full_name": "...", "dob": "..." }
    },
    "confidence_score": 0.92
  }
}
```

**Path B — Raw documents (fallback):**
```json
{
  "request_type": "loan",
  "declared_data": { ... },
  "uploaded_documents": [ { "type": "...", "content_base64": "...", "mime_type": "...", "name": "..." } ]
}
```

**Output (both paths):**
```json
{
  "ocr_extracted_data": { "declared_monthly_income": 85000, "declared_existing_emi": 5000, "name": "...", "dob": "..." },
  "declared_prefill": { ...same as above, merged with declared_data... },
  "consistency_flags": [ "Name mismatch: Salary slip 'X' ≠ Bank account 'Y'" ],
  "document_freshness_passed": true,
  "confidence_score": 0.92
}
```

**Server-side cross-validation checks:**
- Name consistency across salary slip, bank statement, and Aadhaar
- Income consistency: >20% difference between salary slip and bank deposits triggers a flag
- Salary slip freshness: must be ≤3 months old
- Bank statement freshness: must be ≤6 months old

**Document size validation (Path B):**
- Files under 500 bytes are rejected as empty/corrupt
- Unsupported MIME types are rejected
- OCR confidence simulated from file size: `50 + (size/10000)*20 ± 5`, capped 10–98%
- Documents with <40% confidence trigger a 422 error

**Errors:** 400 if no documents, 422 with `{ message, errors[], confidence_scores{} }` on validation failure.

---

#### `POST /api/workflow/submit/{application_id}`
Triggers workflow processing. Sets application status to `completed` and creates a workflow record.

**Output:**
```json
{ "message": "Workflow started", "app_id": "...", "request_id": "req_...", "status": "processing" }
```
**Errors:** 404 if app not found, 403 if not owner, 400 if already submitted.

---

#### `GET /api/workflow/status/{application_id}`
**Output:**
```json
{
  "app_id": "...",
  "status": "completed",
  "request_id": "req_...",
  "rejected": false,
  "rejection_reason": null,
  "loan_prediction": { "approved": true, "probability": 0.84 },
  "insurance_prediction": { "premium": 15300 }
}
```

---

#### `GET /api/workflow/results/{application_id}`
Returns the full decision payload computed from `applicant_data`.

**Output:**
```json
{
  "app_id": "string",
  "request_id": "string",
  "completed": true,

  "loan": {
    "prediction": { "approved": true, "probability": 0.84 },
    "explanation": "Your application has been approved with 84% confidence (Grade B). Your CIBIL score of 742...",
    "description": "Decision: APPROVED | Probability: 84% | Grade: B"
  },

  "insurance": {
    "prediction": { "premium": 15300 },
    "explanation": "Your health and lifestyle profile places you in the Low risk category...",
    "description": "Risk: Low | Annual premium: ₹15,300"
  },

  "model_output": {
    "loan": {
      "feature_contributions": {
        "credit_score": 0.37,
        "monthly_income": 0.21,
        "emi_load": 0.09,
        "loan_to_value": -0.06,
        "employment_stability": 0.12,
        "debt_to_income": -0.05
      }
    },
    "insurance": {
      "feature_contributions": {
        "age": -0.08,
        "smoker": 0.05,
        "bmi": -0.03,
        "pre_existing_diseases": 0.05,
        "family_history": 0.03,
        "sum_insured": 0.11
      }
    }
  },

  "loan_scorecard": {
    "overall_score": 84.0,
    "risk_grade": "B",
    "components": [
      { "name": "CIBIL Score", "value": 742, "score": 80, "weight": "30%", "status": "good" },
      { "name": "Income-to-EMI Ratio", "value": "28.5%", "score": 80, "weight": "25%", "status": "good" },
      { "name": "Loan-to-Value", "value": "66.7%", "score": 60, "weight": "20%", "status": "fair" },
      { "name": "Employment Stability", "value": "5 yrs", "score": 50, "weight": "15%", "status": "good" },
      { "name": "Annual Income", "value": "₹10,20,000", "score": 51, "weight": "10%", "status": "good" }
    ]
  },

  "insurance_scorecard": {
    "premium": 15300,
    "risk_category": "Low",
    "components": [
      { "name": "Age", "value": 31, "weight": "25%", "status": "good" },
      { "name": "BMI", "value": 24.2, "weight": "20%", "status": "good" },
      { "name": "Smoking Status", "value": "Non-smoker", "weight": "15%", "status": "good" }
    ]
  },

  "loan_improvement_plan": [
    {
      "action": "Improve your CIBIL score",
      "current_value": "680",
      "target_value": "750+",
      "expected_impact": "probability +10-15%",
      "timeframe": "6-12 months",
      "how_to": "Pay all EMIs and credit card bills on time...",
      "priority": "high",
      "category": "credit"
    }
  ],

  "insurance_improvement_plan": [
    {
      "action": "Quit smoking to reduce premium",
      "current_value": "Smoker",
      "target_value": "Non-smoker (2+ years)",
      "expected_impact": "₹8,000-15,000/year reduction",
      "timeframe": "24 months",
      "how_to": "Enroll in a smoking cessation program...",
      "priority": "high",
      "category": "lifestyle"
    }
  ],

  "verification_result": {
    "verified": true,
    "concerns": [],
    "recommendation": "APPROVE",
    "hard_fail": false
  },

  "ocr_confidence_scores": { "bank_statement": 92.0, "aadhaar_card": 96.0 },
  "ocr_freshness_warnings": []
}
```

---

#### `GET /api/workflow/stream/{application_id}`
Server-Sent Events stream of agent completion events.

**Event format:**
```
data: {"agent": "kyc", "status": "complete"}
data: {"agent": "onboarding", "status": "complete"}
...
data: {"done": true}
```

---

#### `GET /health`
```json
{ "status": "ok" }
```

---

## Decision Engine (backend/api/workflow.py — `get_results`)

All scoring is computed from `applicant_data` stored at application creation time.

### Loan Scoring

**Derived metrics:**
| Metric | Formula |
|---|---|
| FOIR (Fixed Obligation to Income Ratio) | `(existing_emi + loan_amount / (12 * 20)) / monthly_income` |
| LTV (Loan-to-Value) | `loan_amount / property_value` |
| Annual Income | `monthly_income * 12` |

**Base probability:** 0.50, adjusted by:
| Condition | Adjustment |
|---|---|
| CIBIL ≥ 750 | +0.20 |
| CIBIL 650–749 | +0.10 |
| FOIR < 0.35 | +0.15 |
| FOIR > 0.55 | −0.20 |
| LTV < 0.70 | +0.10 |
| LTV > 0.85 | −0.15 |

**Hard-fail overrides** (force rejection regardless of probability):
- FOIR > 55% → concern flagged, approved = false
- LTV > 85% → concern flagged, approved = false
- CIBIL < 600 → concern flagged, approved = false

**Risk grade:** A (≥85%), B (≥70%), C (≥55%), D (≥40%), E (<40%)

**Approval threshold:** probability ≥ 0.60

**Scorecard component scoring:**
| Component | Score 100 | Score 80 | Score 60 | Score 40 | Score 0 |
|---|---|---|---|---|---|
| CIBIL | ≥800 | ≥750 | ≥700 | ≥650 | <650 |
| FOIR | ≤20% | ≤35% | ≤50% | ≤60% | >60% |
| LTV | ≤50% | ≤65% | ≤75% | ≤80% | >80% |
| Employment | years×10 (capped 100) | — | — | — | — |
| Annual Income | income/20000 (capped 100) | — | — | — | — |

**Improvement plan triggers:**
- CIBIL < 750 → "Improve your CIBIL score" (high priority)
- FOIR > 0.40 → "Reduce existing EMI obligations" (high priority)
- LTV > 0.75 → "Increase your down payment" (medium priority)
- Employment < 2 years → "Build employment stability" (medium priority)

### Insurance Scoring

**BMI:** `weight / (height_m)²`

**Base premium:** `sum_insured * 0.03`, multiplied by:
| Condition | Multiplier |
|---|---|
| Age > 45 | ×1.4 |
| Smoker | ×1.5 |
| BMI > 30 | ×1.2 |

**Risk category:** Low (<₹20,000/yr), Medium (<₹50,000/yr), High (≥₹50,000/yr)

**Improvement plan triggers:**
- Smoker → "Quit smoking" (high priority)
- BMI > 27 → "Reduce BMI to healthy range" (medium priority)

---

## State Management (ShieldContext)

All application state lives in `ShieldContext` (`frontend/src/context/ShieldContext.jsx`):

| Key | Type | Description |
|---|---|---|
| `view` | string | Current page/view |
| `service` | `'loan' \| 'insurance'` | Selected service |
| `userData` | object | Name, Aadhaar, DOB, email, password |
| `kycData` | object | KYC response (name, CIBIL, gender, address) |
| `applicantData` | object | All declaration form fields |
| `loanType` | `'home' \| 'personal'` | Loan sub-type |
| `uploadedDocs` | object | `{ [docLabel]: boolean }` — UI upload state |
| `uploadedDocuments` | array | `[{ type, name, mime_type, content_base64 }]` |
| `ocrPreviewData` | object | OCR-extracted fields + `_ocr_confidence`, `_ocr_flags`, `_ocr_freshness` |
| `authToken` | string | Bearer token from login |
| `applicationId` | string | Created application ID |
| `requestId` | string | Workflow request ID |
| `workflowStatus` | object | Latest status poll response |
| `workflowResult` | object | Full results payload |
| `workflowError` | string | Error message if workflow fails |

---

## Backend In-Memory State (api/state.py)

Three in-memory dicts (reset on server restart):
- `USERS_DB` — `{ email: { id, email, password, name, role } }`
- `APPLICATIONS_DB` — `{ app_id: { ...application fields... } }`
- `WORKFLOW_DB` — `{ app_id: { status, request_id, rejected, loan_prediction, ... } }`
- `WORKFLOW_EVENTS` — `{ app_id: [ { agent, status }, ... ] }`

Token format: `base64(email:timestamp)` — stateless, no expiry in demo mode.

---

## OCR Service (backend/ocr/)

Three modes controlled by `settings.ocr_mode`:
- `mock` — returns hardcoded mock data (default)
- `production` — uses Tesseract + OpenCV + pdf2image for real OCR
- `service.py` — factory that selects mode based on config

The active API path does not call these directly — OCR is handled client-side via Puter.js or via the `preview-ocr` endpoint's Path B fallback.

---

## ML Models (backend/ml/)

Four serialised EBM (Explainable Boosting Machine) models in `backend/ml_models/`:
- `ebm_finance.pkl` — loan approval model
- `ebm_health.pkl` — insurance premium model
- `fin_encoders.pkl` — categorical encoders for finance model
- `health_encoders.pkl` — categorical encoders for health model

`model_loader.py` loads these at startup. `loan_scorer.py` and `insurance_scorer.py` wrap inference. These are not called in the active API path — the `get_results` endpoint uses formula-based scoring. The ML models are available for future integration via the LangGraph agent pipeline.

---

## Agent Pipeline (backend/agents/ — future integration)

Nine LangGraph agents defined but not wired into the active API:

| Agent | File | Purpose |
|---|---|---|
| KYC | `kyc.py` | Identity and Aadhaar verification |
| Onboarding | `onboarding.py` | Document ingestion and OCR |
| Rules | `rules.py` | RAG-based underwriting rule checks (IRDAI/USDA) |
| Fraud | `fraud.py` | Document fraud detection |
| Feature Engineering | `feature_engineering.py` | Derive FOIR, LTV, BMI, etc. |
| Compliance | `compliance.py` | Regulatory compliance checks |
| Underwriting | `underwriting.py` | EBM model inference |
| Verification | `verification.py` | Sanity and hard-rule checks |
| Transparency | `transparency.py` | SHAP/EBM explanation generation |

Supervisor agent in `supervisor.py` orchestrates the pipeline. Graph definition in `graph/workflow.py`.

---

## Setup & Running

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit SECRET_KEY for production
uvicorn main:app --reload --port 8000
```

**Environment variables (`.env`):**
| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-me` | JWT signing key (required in production) |
| `ENV` | `development` | Environment name |
| `DATABASE_URL` | `sqlite+aiosqlite:///./daksha.db` | SQLAlchemy DB URL |
| `OCR_MODE` | `mock` | `mock` or `production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |

### Frontend

```bash
cd frontend
npm install
npm run dev          # development server on http://localhost:5173
npm run build        # production build to dist/
```

**Environment variables (`frontend/.env`):**
| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API base URL |

### Docker

```bash
docker-compose up --build
```

Services: `backend` on port 8000, `frontend` on port 80.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Lucide React |
| Backend | FastAPI, Uvicorn, Pydantic v2 |
| ML | Interpret (EBM), scikit-learn, pandas, numpy |
| Agent orchestration | LangGraph, LangChain, Groq LLM |
| OCR (client) | Puter.js (`puter.ai.img2txt` + `puter.ai.chat`) |
| OCR (server) | Tesseract, OpenCV, pdf2image, PyPDF2 |
| Auth | Base64 token (demo); python-jose + passlib (production-ready) |
| Vector store | FAISS + pypdf (for RAG rules agent) |
| Containerisation | Docker, docker-compose |
