# JTI Promotion Scheduling POC

## Instructions for Claude

- After **any backend change**, run `make be-lint` (auto-fixes black + isort, then checks flake8).
- After **any frontend change**, run `make fe-lint`.
- After adding or changing frontend behaviour, run `make fe-test` to verify tests pass.
- Fix all lint errors before considering a task complete.

---

## Business Context

An AI-powered **promoter scheduling application** piloted in **JTI Greece**. It automates the planning of promoter/informer visits to Points of Sale (POS — retail kiosks) to maximise sales impact.

### The problem

Currently scheduling is entirely manual: field teams check each POS individually in BI tools to decide when to visit and who to send. This is slow, error-prone, and leads to visits at suboptimal times.

### Domain concepts

| Term | Meaning |
|---|---|
| **POS** | Point of Sale — a retail kiosk. Identified by a `CDB Code`. |
| **Promoter / Informer** | Field staff who visit POS to sell devices and conduct customer interviews. |
| **Activity / Visit** | One promoter visit to one POS. Has a date, start/end time, and outcome (devices sold, interviews). |
| **Programme type** | Nature of the promoter assignment: `Permanent` (JTI full-time), `Exclusive` (JTI dedicated contractor), `Radical` (external collaborator). |
| **Schedule** | A planning period (e.g. next month) containing a set of assigned visits. Created by a scheduling admin. |

### Tool outputs

1. Complete visit plan per POS — day, time, frequency, promoter assignment
2. Peak time detection per POS from historical data
3. Optimised visit frequency per POS
4. Promoter–POS matching based on past performance
5. Exportable plan (Excel / CSV / PDF)

### Scope

Pilot POC for Greece. Goal is to validate approach before broader rollout.

---

## Project Structure

```
jti-promotion-scheduling-poc/
├── CLAUDE.md
├── Makefile
├── .gitignore
├── .github/workflows/ci.yml
├── backend/
│   ├── .venv/                        # Python 3.14, managed by uv
│   ├── manage.py
│   ├── setup.cfg                     # flake8 + isort config
│   ├── pyproject.toml                # black config
│   ├── config/                       # Django project settings, urls, wsgi, asgi
│   ├── api/                          # Auth endpoints
│   ├── scheduling/                   # Core domain models + admin
│   │   └── fixtures/initial_data.json
│   ├── metrics/                      # POSMetrics model
│   └── data_integration/             # CSV importers, DataSyncLog, admin Pull buttons
│       └── sample_data/              # Sample CSVs for PoC demo
└── frontend/
    ├── package.json
    ├── vite.config.js                 # proxies /api → :8000
    ├── eslint.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx                    # Router + AuthProvider
        ├── index.css                  # Global styles
        ├── theme.js                   # JTI color tokens
        ├── context/AuthContext.jsx    # JWT auth state, login/logout
        ├── components/
        │   ├── JtiLogo.jsx
        │   └── ProtectedRoute.jsx
        └── pages/
            ├── LoginPage.jsx
            └── HomePage.jsx
```

---

## Backend

### Python environment

- Venv: `backend/.venv/` (Python 3.14)
- Dependency manager: **uv** — `backend/.venv/Scripts/uv.exe`
- **Never use `pip` or `requirements.txt`. Always use `uv`.**

```bash
backend/.venv/Scripts/uv.exe pip install <package>
backend/.venv/Scripts/Activate.ps1   # activate (PowerShell)
```

### Stack

- Django 6.x + Django REST Framework
- `djangorestframework-simplejwt` — JWT authentication
- `django-cors-headers`
- `openpyxl` — Excel reading (fixture/data generation scripts)

### Django apps

| App | Responsibility |
|---|---|
| `api` | Auth endpoints: login, logout, me |
| `scheduling` | Core domain models: PointOfSale, Promoter, Schedule, ScheduledVisit |
| `metrics` | POSMetrics — time-windowed historical performance per POS |
| `data_integration` | CSV importers + DataSyncLog; admin Pull buttons |

### Authentication

JWT via `djangorestframework-simplejwt`:
- Access token: **8 hours**
- Refresh token: **7 days**, rotation + blacklist enabled

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/login/` | POST | No | Returns access + refresh tokens |
| `/api/auth/logout/` | POST | Yes | Blacklists refresh token |
| `/api/auth/me/` | GET | Yes | Returns current username |
| `/api/hello/` | GET | Yes | Hello world (protected) |

All endpoints require `IsAuthenticated` by default. Users created via Django Admin only — no frontend registration.

### Linting

| Tool | Purpose | Config |
|---|---|---|
| `black` | Formatter | `pyproject.toml` |
| `isort` | Import sorter | `setup.cfg` |
| `flake8` | Style/error checker | `setup.cfg` |

`max-line-length = 88`. `.venv` and `migrations` excluded.

---

## Data Model

### `scheduling` app — `backend/scheduling/models.py`

#### `PointOfSale`
Master POS registry. Unique key: `cdb_code`.

Key fields: `pos_type`, `priority` (Strategic/Prime/BaseLine/Developing), `address/city/county/department/district/territory`, `chain`, `contractor`, `warehouse`, `is_active`.

#### `Promoter`
All promoter types. Unique key: `username`.

Key fields: `code` (nullable for Radical), `programme_type` (Permanent/Exclusive/Radical), `base_city` (nullable for Radical — data quality gap, will be filled via JTI infrastructure), `team` (SOUTH TEAM / NORTH TEAM, nullable for Radical), `is_active`.

#### `Schedule`
A planning period container. Lifecycle: `Draft → Published → Archived`.

Constraints:
- `period_end >= period_start`
- **No overlapping schedules** — enforced in `clean()`
- Periods are **arbitrary** (not fixed to month/week)
- No historical data imported — DB starts fresh going forward

#### `ScheduledVisit`
One promoter visit to one POS within a schedule. Central fact record.

Key fields: `schedule`, `promoter` (nullable for Radical until data integration), `pos`, `date`, `start_time`, `end_time`, `programme_type` (stored explicitly per visit), `out_of_premises`, `week_label`, `action` (blank = planned, not yet executed), `reason`, `comments`, `comments_meeting`.

Constraints: `end_time > start_time`, `date` must fall within `schedule` period.

---

### `metrics` app — `backend/metrics/models.py`

#### `POSMetrics`
Historical performance per POS broken down by **time window**. Used by the scheduling AI to detect peak times and prioritise visits.

Fields: `pos`, `reference_type`, `period_start`, `period_end`, `window_date`, `window_start`, `window_end`, `sales`, `interviews`.

Unique constraint: `(pos, reference_type, period_start, period_end, window_date, window_start, window_end)`.

**`reference_type`** — expandable enum:
- `previous_year` — same calendar period from the prior year *(primary for PoC)*
- `previous_month` — the immediately preceding month

---

### `data_integration` app — `backend/data_integration/`

#### `DataSyncLog`
Audit log of every pull operation: `sync_type`, `status` (Success/Failed), `records_created/updated/skipped`, `file_used`, `triggered_by`, `triggered_at`, `notes`.

#### Importers — `data_integration/importers/`

All imports are **idempotent** (upsert). Each returns `{created, updated, skipped, errors}`.

| Module | Match key | Target model |
|---|---|---|
| `promoters.py` | `username` | `scheduling.Promoter` |
| `pos.py` | `cdb_code` | `scheduling.PointOfSale` |
| `metrics.py` | `(pos, reference_type, period_start, period_end, window_date, window_start, window_end)` | `metrics.POSMetrics` |

Metrics importer parses `period_start`, `period_end`, and `reference_type` from the filename automatically:
`period_YYYY-MM-DD_YYYY-MM-DD_(previous_year|previous_month)_metrics.csv`

#### Django Admin Pull buttons

In Django Admin → **Data Sync Logs**, three buttons trigger imports from sample CSVs:
- **↓ Pull Promoters**
- **↓ Pull Points of Sale**
- **↓ Pull Metrics**

Each creates a `DataSyncLog` entry with counts and row-level errors.

---

## Test Data

### Fixtures — `backend/scheduling/fixtures/initial_data.json`

Load with: `make be-loaddata`

| Entity | Count | Notes |
|---|---|---|
| `auth.User` (admin) | 1 | username: `admin`, password: `admin123!` |
| `Promoter` (Permanent) | 19 | Real — from Excel `Personnel` sheet |
| `Promoter` (Exclusive) | 27 | Real — from Excel `Personnel` sheet |
| `Promoter` (Radical) | 8 | **Fake** — codes prefixed `RAD_`; real data pending JTI integration |
| `PointOfSale` | 50 | Real — from Excel `CDB List` sheet |

### Sample CSVs — `backend/data_integration/sample_data/`

| File | Rows | Notes |
|---|---|---|
| `sample_promoters.csv` | 54 | Same data as fixtures |
| `sample_pos.csv` | 50 | Same data as fixtures |
| `period_2026-04-01_2026-04-30_previous_year_metrics.csv` | 408 | Fake but plausible time-windowed metrics |

**Metrics time windows:**
- Morning `09:00–11:00` — weekdays, ~60% of dates
- Afternoon `15:00–17:00` or `17:00–19:00` — ~75% of dates
- Night `21:00–23:00` Fri/Sat only — ~20% of POS flagged as high night-traffic venues

---

## Frontend

Framework: React 19 + Vite 6. Dev server at `:5173`, proxies `/api` → `:8000`.

### Auth flow

1. Unauthenticated users redirected to `/login`
2. `LoginPage` POSTs to `/api/auth/login/`
3. Access + refresh tokens stored in `localStorage`
4. `authHeaders()` injects `Authorization: Bearer <token>` on API calls
5. Logout calls `/api/auth/logout/` and clears storage

### JTI theming — `src/theme.js`

| Token | Value | Usage |
|---|---|---|
| `bgPage` | `#141414` | Page background |
| `bgCard` | `#1e1e1e` | Cards, forms |
| `bgNavbar` | `#0f0f0f` | Navbar |
| `bgInput` | `#2a2a2a` | Input fields |
| `text` | `#ffffff` | Primary text |
| `textMuted` | `#aaaaaa` | Secondary text |
| `border` | `#2e2e2e` | Borders |
| `buttonBg` | `#ffffff` | Primary button |
| `buttonText` | `#141414` | Primary button text |

Font: **Inter** (Google Fonts). Logo: SVG in `JtiLogo.jsx`.

### Linting

ESLint with `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`. Config: `eslint.config.js`.

---

## Makefile Commands

```bash
make help                # List all commands

# Backend
make be-run              # Django dev server (:8000)
make be-migrate          # Apply migrations
make be-makemigrations   # Create new migrations
make be-install          # Install backend deps via uv
make be-createsuperuser  # Create Django admin superuser
make be-loaddata         # Load fixture data (promoters, POS, test admin)
make be-lint             # Format + lint, auto-fix (black + isort + flake8)
make be-lint-check       # Lint check only, no changes (CI mode)

# Frontend
make fe-run              # Vite dev server (:5173)
make fe-install          # npm install
make fe-build            # Production build
make fe-lint             # ESLint
make fe-test             # Vitest (run once)

# Combined
make install             # Install all deps
make lint                # All linters in CI mode
```

---

## CI — `.github/workflows/ci.yml`

Triggers: push or PR to `main`.

| Job | Steps |
|---|---|
| `backend-lint` | black --check, isort --check, flake8 |
| `frontend-lint` | npm ci, eslint |

---

## Dev Ports

| Service | Port |
|---|---|
| Django API | 8000 |
| Django Admin | 8000/admin |
| React / Vite | 5173 |

---

## Source Excel Reference

File: `SWAP TTL Program Jan '26 Week 3.xlsx` — the manually produced weekly schedule this tool replaces.

### Main schedule sheet: `SWAP TTL Program Jan '26_W3`

Each row = one promoter visit to one POS.

| Column | Description |
|---|---|
| `Week` | Week label e.g. `W1`, `W3` |
| `Base` | Promoter home city. Null for Radical (data quality issue). |
| `Program` | Programme type: `Permanent`, `Exclusive`, `Radical` |
| `Out of Premises` | `Yes` if visit is outside POS premises |
| `Brand Ambassador` | `SPC_<Lastname> <Firstname>`. Null for Radical (data quality issue). |
| `Date` / `Start` / `End` / `Duration` | Visit timing |
| `CDB Code` / `POS Name` | POS identifier and name |
| `Priority` | Strategic / Prime / BaseLine / Developing |
| `Type` | POS category (kiosk, convenience, minimarket, vape store…) |
| `Address` / `City` / `County` / `Department` / `District` / `Territory` | Location hierarchy |
| `Chain` / `W/H` / `Contractor` | Commercial relationships |
| `Action` | Outcome: Executed / Cancelled / Change Visit / Double Visit |
| `Reason` | Reason when not executed |
| `Comments` / `Comments Meeting` | Free-text notes |

### Other sheets

| Sheet | Purpose |
|---|---|
| `Personnel` | Master list of JTI promoters (Permanent + Exclusive, ~46 records) |
| `CDB List` | Master POS registry (~866 records) |
| `Priority` | POS analysis with recommended visit Day/Time slots and volume metrics |
| `schedules` | Output template for downstream system (`promoterCode`, `posCode`, `startAt`, `endAt`) |
| `Strategic PoS_Monthly Plan` | Monthly grid view of strategic POS |
| `Detailed Pan Provences` | Province-level planning breakdown |
| `DropDownLists` | Reference values for Action, Reason, Trade Offer, PoS Gift fields |

---

## Open Questions

Early-stage PoC — these require stakeholder clarification before building scheduling logic.

| # | Area | Question |
|---|---|---|
| 2 | Programme types | **Exclusive vs Permanent** — is Exclusive a dedicated third-party contractor (not direct payroll) while Permanent is a full-time JTI hire? |
| 3 | Promoter data | **`Base` column for Radical** — null because data isn't tracked, or because Radical promoters are always local to the POS area? |
| 4 | Output | **`schedules` sheet** — confirmed as downstream system output format? What system consumes it? |
| 5 | AI input | **`Priority` sheet Day/Time columns** — are these manually determined optimal slots that the AI should learn to generate? Ground truth for validation? |
| 6 | POS data | **`W/H` column** — does warehouse/distributor affect scheduling (e.g. promoter–distributor ties) or is it logistics-only? |
| 7 | POS data | **`Contractor` column** (`JTI`/`Competition`/`Owner`) — does this affect which POS is scheduled, which programme type is used, or which promoter is assigned? |
