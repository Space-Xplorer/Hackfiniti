# Niyati — Forensic Multi-Agent GST Intelligence Platform

Niyati (internally codenamed **Daksha**) is a real-time GST fraud detection and forensic intelligence platform. It uses a multi-agent AI architecture to detect circular trading loops, ghost invoices, shell-company networks, and compliance anomalies in Indian GST data. Every decision is backed by explainable AI reasoning for audit-ready transparency.

---

## Tech Stack

**Backend**
- Python + FastAPI (async REST API)
- SQLAlchemy (async ORM) + SQLite via `aiosqlite`
- `python-jose` + `passlib[bcrypt]` — JWT auth & password hashing
- LangGraph — agent orchestration (referenced, not yet wired)
- EBM (Explainable Boosting Machine) `.pkl` models for scoring
- pytest + pytest-asyncio + httpx — testing

**Frontend**
- React 18 + Vite 5
- Tailwind CSS 3
- Framer Motion 11 — scroll-driven animations
- React Router (not yet installed/wired)

**Infrastructure**
- Docker Compose (stubs — no Dockerfiles yet)

---

## Project Structure

```
.
├── backend/
│   ├── agents/          # 8 AI agent modules (all stubs)
│   ├── api/             # FastAPI route handlers
│   ├── core/            # Config, DB engine, security utils
│   ├── graph/           # LangGraph workflow state & builder
│   ├── ml/              # ML scoring functions + model loader
│   ├── ml_models/       # Pre-trained EBM .pkl files
│   ├── models/          # SQLAlchemy ORM models
│   ├── ocr/             # OCR service (mock + production modes)
│   ├── rules/           # Domain rule text files (placeholders)
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic layer
│   ├── tests/           # pytest test suite (stubs)
│   └── main.py          # FastAPI app entry point
└── frontend/
    └── src/
        ├── api/         # API client (stub)
        ├── components/  # Shared + landing section components
        ├── context/     # React context (stub)
        ├── hooks/       # useAuth, useWorkflowStream (stubs)
        ├── pages/       # 8 page components (1 implemented, 7 stubs)
        └── App.jsx      # Root component (renders Landing only)
```

---

## Implemented Features

### Frontend — Landing Page (fully built)
- **NiyatiHero** — animated hero section with sticky nav, product dropdown, and ASCII globe canvas
- **AsciiGlobeCanvas** — interactive WebGL-style ASCII globe with mouse-tracking parallax and auto-rotation
- **AgentCollaboration** — scroll-driven SVG path animations connecting 6 agent cards
- **LangGraphOrchestration** — 6-card grid explaining the orchestration pipeline
- **DetectionCapabilities** — 3-card showcase: Circular Trading, Ghost Invoices, Spider Web Networks
- **BenefitsSecurity** — 4-card benefits section: Explainable AI, Role-Based Access, Real-Time Monitoring, PII Protection
- **LandingFooter** — minimal branded footer

### Backend — Skeleton / Scaffolding
- **Health check** — `GET /health` returns `{"status": "ok"}`
- **Auth routing** — `POST /auth/login` (placeholder response)
- **Applications routing** — `GET /applications` (returns empty list)
- **Workflow routing** — `POST /workflow/submit`, `GET /workflow/status/{id}`, `GET /workflow/results/{id}` (all stubs)
- **JWT token generation** — `create_access_token()` with HS256, configurable expiry
- **Database setup** — async SQLAlchemy engine + session factory wired to SQLite
- **ORM models** — `User` (id, email, full_name) and `Application` (id, user_id, product_type, status)
- **Pydantic schemas** — `UserCreate/Read`, `ApplicationCreate/Read`, `WorkflowSubmitRequest/StatusResponse`
- **Config** — `pydantic-settings` with `.env` support (app_name, env, db url, secret key, token expiry, algorithm)
- **OCR service** — dispatcher routing to `mock` or `production` mode based on config flag
- **ML model files** — `ebm_finance.pkl`, `ebm_health.pkl`, `fin_encoders.pkl`, `health_encoders.pkl` present on disk

### Page Stubs (scaffolded, not implemented)
`Selection`, `Upload`, `Preliminary`, `KYC`, `Analysis`, `Config`, `Result`

### Agent Stubs (scaffolded, not implemented)
`compliance`, `feature_engineering`, `fraud`, `kyc`, `onboarding`, `rules`, `transparency`, `underwriting`

---

## API Endpoints

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| GET | `/health` | ✅ Working | Health check |
| POST | `/auth/login` | ⚠️ Stub | Returns placeholder, no real auth |
| GET | `/applications` | ⚠️ Stub | Returns empty list |
| POST | `/workflow/submit` | ⚠️ Stub | Returns `"submitted"` |
| GET | `/workflow/status/{id}` | ⚠️ Stub | Returns `"pending"` |
| GET | `/workflow/results/{id}` | ⚠️ Stub | Returns `null` result |

---

## Running Locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # edit SECRET_KEY before running
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Docker** *(Dockerfiles not yet created)*
```bash
docker-compose up
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Daksha` | Application name |
| `ENV` | `development` | Environment mode |
| `DATABASE_URL` | `sqlite+aiosqlite:///./daksha.db` | Async DB connection string |
| `SECRET_KEY` | `change-me` | JWT signing secret — **must change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT token lifetime |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `OCR_MODE` | `mock` | `mock` or `production` |

---

## Known Issues & Backlog

See the Issues section below for a prioritized list of everything that needs to be built or fixed.

---

## Issues — Prioritized Fix List

### 🔴 Critical (Blockers — nothing works without these)

**ISSUE-01** — `main.py` does not register any routers  
`app = FastAPI(...)` exists but `auth`, `applications`, and `workflow` routers are never included via `app.include_router()`. All API endpoints except `/health` are unreachable.

**ISSUE-02** — No database table creation on startup  
`engine` and `SessionLocal` are defined but `Base.metadata.create_all()` is never called. The app will crash on any DB operation because the tables don't exist.

**ISSUE-03** — `User` model has no `hashed_password` column  
`UserCreate` schema accepts a `password` field but the `User` ORM model has no `hashed_password` column. Registration and login are impossible to implement without this.

**ISSUE-04** — Auth login endpoint is a non-functional stub  
`POST /auth/login` returns `{"message": "login endpoint"}` with no credential validation, no DB lookup, and no token issuance. The `AuthService.login()` method also returns a hardcoded placeholder token.

**ISSUE-05** — No user registration endpoint  
`UserCreate` schema exists but there is no `POST /auth/register` (or equivalent) endpoint. Users cannot be created.

**ISSUE-06** — No JWT verification / auth dependency  
`create_access_token()` is implemented but there is no `get_current_user` dependency that decodes and validates the token. All protected routes are effectively open.

**ISSUE-07** — `App.jsx` only renders `<Landing />` — no routing  
React Router is not installed and `App.jsx` hardcodes `<Landing />`. The 7 other pages (`Selection`, `Upload`, `Preliminary`, `KYC`, `Analysis`, `Config`, `Result`) are completely unreachable.

---

### 🟠 High (Core functionality missing)

**ISSUE-08** — All 8 agents are empty pass-through stubs  
Every agent file (`compliance.py`, `feature_engineering.py`, `fraud.py`, `kyc.py`, `onboarding.py`, `rules.py`, `transparency.py`, `underwriting.py`) contains only `return state`. No fraud detection, compliance checking, or KYC logic exists.

**ISSUE-09** — LangGraph workflow is not wired  
`build_workflow()` returns `{"nodes": [], "edges": []}`. No LangGraph `StateGraph` is constructed, no agents are added as nodes, and no edges define execution order.

**ISSUE-10** — `WorkflowService.run()` does not execute the graph  
The service returns a hardcoded `{"status": "running"}` dict. It never calls `build_workflow()` or invokes any agent.

**ISSUE-11** — `ApplicationService` does not persist to the database  
`create_application()` returns a plain dict without writing anything to the DB. No SQLAlchemy session is injected or used.

**ISSUE-12** — `GET /applications` returns a hardcoded empty list  
The endpoint ignores the database entirely and always returns `{"items": []}`.

**ISSUE-13** — `ModelLoader` singleton is not implemented  
The class body is empty (only `__new__` for singleton pattern). No models are loaded from `ml_models/`. `score_insurance()` and `score_loan()` both return `{"score": 0.0, ...}` dummy data.

**ISSUE-14** — `useAuth()` hook always returns unauthenticated  
Returns `{ user: null, isAuthenticated: false }` unconditionally. No token storage, no API call, no session persistence.

**ISSUE-15** — `useWorkflowStream()` hook is a stub  
Returns `{ connected: false, events: [] }` unconditionally. No SSE connection, no event handling.

**ISSUE-16** — `apiClient` is a stub  
`client.js` only has a `getHealth()` method that returns a hardcoded object. No actual `fetch`/`axios` calls, no auth headers, no base URL configuration.

---

### 🟡 Medium (Features advertised but not built)

**ISSUE-17** — No CORS middleware configured  
The frontend (port 5173) will be blocked by the browser when calling the backend (port 8000). `fastapi.middleware.cors.CORSMiddleware` is not added to `main.py`.

**ISSUE-18** — `AppContext` is created but never provided  
`AppContext = createContext(null)` exists but no `<AppContext.Provider>` wraps the app in `main.jsx` or `App.jsx`. Context is unusable.

**ISSUE-19** — `Navbar`, `GlassCard`, `AgentTracePanel`, `FeatureChart` components are stubs  
These components render bare placeholder text/elements. They are referenced in the page stubs but have no real implementation.

**ISSUE-20** — OCR service returns hardcoded strings  
`run_mock_ocr()` returns `{"text": "mock-ocr-output"}` and `run_production_ocr()` returns `{"text": "production-ocr-output"}`. Neither parses a real document.

**ISSUE-21** — Rules files are placeholders  
`irdai_insurance_rules.txt` and `usda_loan_rules.txt` contain only one-line placeholder text. No actual rule content exists for the rules agent to process.

**ISSUE-22** — No role-based access control  
The landing page advertises "Role-Based Access" for admins, analysts, and operators, but no roles, permissions, or access control logic exists anywhere in the codebase.

**ISSUE-23** — No Server-Sent Events (SSE) implementation  
The landing page advertises real-time SSE updates for workflow traces. No SSE endpoint exists in the backend and `useWorkflowStream` is a stub.

**ISSUE-24** — `SECRET_KEY` defaults to `"change-me"` in config  
`core/config.py` sets `secret_key: str = "change-me"` as a hardcoded default. If `.env` is missing, the app starts with an insecure key and no warning.

**ISSUE-25** — No input validation on workflow/application endpoints  
Endpoints accept `application_id` path params but perform no existence checks, ownership validation, or type coercion beyond FastAPI's basic parsing.

---

### 🔵 Low (Quality / DevEx)

**ISSUE-26** — All tests are `assert True` placeholders  
`test_applications.py`, `test_auth.py`, and `test_workflow.py` contain single-line placeholder tests with no real assertions or coverage.

**ISSUE-27** — Docker Compose has no Dockerfiles  
`docker-compose.yml` references `build: ./backend` and `build: ./frontend` but neither directory has a `Dockerfile`. `docker-compose up` will fail immediately.

**ISSUE-28** — No database migration system  
There is no Alembic setup. Schema changes require manual intervention and there is no migration history.

**ISSUE-29** — `deps.py` is a redundant passthrough  
`get_database_session` in `deps.py` simply re-yields from `get_db`. It adds an indirection layer with no added value and is not used anywhere.

**ISSUE-30** — Frontend has no error boundaries or loading states  
No `<Suspense>`, no error boundary components, and no loading indicators exist anywhere in the frontend.

**ISSUE-31** — `react-router-dom` is missing from `package.json`  
Routing is needed for the 8-page app flow but the dependency is not listed and not installed.

**ISSUE-32** — `langgraph` is missing from `requirements.txt`  
The graph workflow module and landing page both reference LangGraph but it is not listed as a dependency.

**ISSUE-33** — No `Dockerfile` for backend or frontend  
Both are missing, making the Docker Compose setup non-functional.

**ISSUE-34** — `vite.config.js` has no proxy configuration  
Without a proxy, all frontend API calls need absolute URLs. A `/api` proxy to `http://localhost:8000` would simplify development.
