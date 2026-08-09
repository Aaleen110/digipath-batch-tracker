# DigiPath Batch Tracker

Full-stack diagnostic batch tracking system for the DigiPathAI Technical Skills Assessment. A FastAPI backend tracks sample batches through a lab pipeline; a React frontend lists, filters, and updates batches.

## Stack

API - Python, FastAPI, SQLAlchemy
Database - SQLite (development)
Frontend - React, TypeScript, Vite, Tailwind CSS
Tests - pytest, httpx

## Quick start

### 1. Environment

Copy the example env file at the repo root:

```bash
cp .env.example .env
```

Edit `.env` and set `API_KEY` to a value of your choice. **Never commit `.env`** — it is gitignored.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000  
Interactive docs: http://127.0.0.1:8000/docs

### 3. Frontend (optional)

```bash
cd frontend
cp .env.example .env
# Set VITE_API_KEY to the same value as API_KEY in the root .env

npm install
npm run dev
```

UI: http://localhost:5173

Leave `VITE_API_BASE_URL` empty in `frontend/.env` — Vite proxies `/batches` to the backend during local development.

### 4. Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

Tests use an isolated in-memory SQLite database (not `batches.db`).

---

## Authentication

All `/batches/*` endpoints require an API key. The public `/health` endpoint does not.

| Item | Value |
|------|-------|
| Header | `X-API-Key` |
| Config | `API_KEY` in root `.env` |
| Missing key | `401` — "Missing API key" |
| Invalid key | `401` — "Invalid API key" |

**Example:**

```bash
curl -H "X-API-Key: dev-secret-key" \
     -H "Idempotency-Key: demo-001" \
     -H "Content-Type: application/json" \
     -d '{"sample_id":"Sample #123","batch_type":"Blood Panel","submitted_by":"lab-user-01"}' \
     http://127.0.0.1:8000/batches
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/batches` | Create batch — requires `Idempotency-Key` header |
| `GET` | `/batches/{id}` | Batch detail (status, result, webhook, timestamps) |
| `PATCH` | `/batches/{id}/status` | Update status — valid transitions only |
| `GET` | `/batches` | List/filter by `status` and `type`, paginated |
| `POST` | `/batches/{id}/notify` | Notify partner via webhook URL on the batch |
| `GET` | `/health` | Health check (no auth) |

**Status transitions:** `queued → processing → completed | failed`. Any other transition returns `409 Conflict`.

**Pagination:** `GET /batches?page=1&page_size=20&status=queued&type=PCR`

---

## Persistence

**Development:** SQLite (`DATABASE_URL=sqlite:///./batches.db`). Zero setup, file-based, ideal for local work and this exercise.

**Production trade-off:** I would use **PostgreSQL** instead. SQLite has a single-writer lock, no built-in replication, and weak concurrent-write behaviour under load. Postgres gives proper connection pooling, backups, replication, and scales with multiple API workers. For a lab pipeline with many concurrent status updates and partner notifications, a server-grade database is the right default.

---

## Scaling `GET /batches`

If list/filter became slow as data grew, I would:

1. **Keep indexes on filter columns** — already added on `status`, `batch_type`, and `(status, batch_type)`.
2. **Use cursor-based pagination** instead of large `OFFSET` values (offset scans get expensive on big tables).
3. **Move to PostgreSQL** with connection pooling and optional read replicas for heavy read traffic.
4. **Cache hot queries** — e.g. Redis for common filter combinations with short TTL.
5. **Archive old batches** to a cold store so the active table stays small.
6. **Optimize & vaccum** - Optimize query plans with ANALYZE and periodic VACUUM (for Postgres) to keep indexes effective.
7. **Partitioning** - Shard or partition table by date or status to reduce scan size.
8. **Return whats required** - Return only required fields (select specific columns vs. *) to reduce payload and I/O.
9. **Profiling & Monitoring** - Profile and monitor query performance regularly to catch new slow paths as usage evolves

---

## Design decisions

- **API key auth** — simple and sufficient for service-to-service calls in this scope; JWT would be better for user sessions at scale. But for this excercise would add complexity, new table etc. Hence used API key auth to keep things simple yet secure.

- **Idempotency via `Idempotency-Key`** — unique DB constraint plus pre-insert lookup; handles retries and race conditions via `IntegrityError` fallback.

- **Atomic status updates** — `UPDATE ... WHERE id = ? AND status = current` so two concurrent PATCH requests cannot both succeed; loser gets `409`.

- **Webhook safety** — HTTPS only, DNS resolution check, block private/loopback IPs (SSRF protection), exponential backoff retries (1s, 2s, 4s) before returning `502`.

- **Pydantic validation** — request/response schemas with meaningful HTTP status codes (`400`, `401`, `404`, `409`, `422`, `502`).

- **Loggin & Tracing** - added logs for debugging.

- **Config via env variables** - all secrets, timeouts, and retry limits are set using env vars for safe ops/deployment.

- **Test Coverage** - coverage for edge cases like duplicate requests, webhook failure, invalid inputs, and status transitions.

- **Structured error responses** — provide clear, machine-readable error codes and messages to client debugging.

- **OpenAPI/Swagger docs** — autogenerated, ensuring up-to-date and testable API documentation.

---

## What I would add with more time

### Backend
- JWT or OAuth2 for user-facing auth with role-based access management
- Background job queue (Celery/ARQ or SQS) for webhook delivery instead of blocking the request
- Docker Compose for one-command local setup
- CI pipeline (pytest + lint on every PR)
- Improved and Structured logging and request tracing (correlation IDs)
- Result field updates via a dedicated endpoint when lab processing completes
- Rate limiting per API key
- API versioning for backward compatibility
- Audit logs
- Admin dashboard for system management
- Sentry for error monitoring
- notified_at + notification_status on Batch for idempotency on sending notification again

### Frontend
- TanStack Query — right now list fetching is all manual in App.tsx (useEffect + reloadTick). Would clean that up a lot.
- Playwright for e2e tests — pytest covers the API well, but nothing tests the UI yet. Would add flows for filters, pagination, optimistic rollback, bad API key, etc.
- Vitest + Testing Library for component/hook tests — lighter than Playwright, good for StatusBadge, modals, error banner.
- Confirm modals before status change / notify — easy to misclick today, especially under time pressure.
- Virtualised list — pagination helps, but if page size goes up or we switch to a table view, @tanstack/react-virtual keeps scrolling smooth.
- Polling or WebSocket for live status — list only updates when you filter, paginate, or hit refresh. Other users changing a batch won't show up automatically.
- React Router — everything is in one App.tsx file. Fine for this size, would split once it grows.
- Storybook / design system — if this UI gets reused across apps, worth documenting BatchCard, StatusBadge, modals properly.
- Next.js — probably overkill here, Vite is enough for this exercise. Next js provides SSR, and is faster.
- GraphQL — same, REST is fine for this. Would only revisit if we had lots of clients needing different query shapes.
- Accesibility check — Make sure all code are accesible to keyboard and devices.
- Sentry or bugsnag on the frontend — match backend error monitoring so we catch client crashes too.

## Other assessment tasks

| Task | File |
|------|------|
| Task 2 — Debug | `DEBUG.md` |
| Task 4 — Code review | `REVIEW.md` |
| Task 5 — System design | `DESIGN.md` |
| Task 7 - Delegation Brief | `DELEGATION.md` |

---
