# ClearDues

**Shared expenses that settle themselves.**

ClearDues is an AI-powered "Agentic Mediator" for group expenses. You describe a
cost in plain language ("dinner was 84, split with Sam and Ali"); it parses,
splits, and tracks it. When someone owes you, ClearDues does the asking — a
progressive sequence of nudges that starts gentle and escalates on its own — so
you never have to send the awkward message yourself.

The bet: the hard part of splitting expenses was never the arithmetic. It's the
social cost of collecting.

---

## Status

**Pre-beta. Deployed, not launched.** Not accepting external signups yet.

| | |
|---|---|
| Live app | [cleardues.site](https://cleardues.site) |
| API | [api.cleardues.site](https://api.cleardues.site/api/v1/utils/health-check/) |
| Stage | Work sessions WS1–WS12 complete; private beta lands after WS13 |

What works today: magic-link and Google sign-in, groups with invites, AI expense
parsing with a confirmation step, a double-entry ledger, per-expense and
aggregate settle-up, payment handles/links, analytics instrumentation, and —
since WS12 — **Level 1 nudges**: one gentle reminder when a balance has sat for
a day, delivered by web push with an email fallback, with snooze, mute, quiet
hours and an off switch.

Reminders are addressed to a **relationship inside a group**, never to an
expense: twelve unsettled dinners between the same two people are one debt and
produce one reminder. That is enforced by a database constraint, not by
convention.

What does **not** exist yet: Level 2 escalation (WS13) and offline support.
**Celery, Redis and WebSockets are descoped, not pending** — the nudge scheduler
is a GitHub Actions cron calling an HTTP endpoint, because Render's free plan
has no background worker. `_bmad-output/planning-artifacts/architecture.md` still
describes the old async design in places; its "WS12 CORRECTION" section is the
accurate account.

The plan of record is
[`_bmad-output/product-review/10-execution-plan.md`](./_bmad-output/product-review/10-execution-plan.md).

---

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python 3.13), SQLModel, Alembic |
| Frontend | React 19, TypeScript, Vite, TanStack Router + Query |
| Database | PostgreSQL 17 |
| AI | Hosted LLM parsing with a per-user quota |
| Local dev | Docker Compose (+ Adminer, mailcatcher, hot reload) |
| Production | Vercel (SPA) · Render (API) · Neon (Postgres) |

No Redux — server state lives in TanStack Query, UI state in React local state.

---

## Quickstart

Requires [Docker](https://www.docker.com/) and Docker Compose.

```bash
git clone https://github.com/Tahiralira/Bmad-Experiment.git cleardues
```

```bash
cd cleardues && cp .env.example .env && cp frontend/.env.example frontend/.env.local
```

Fill in `.env` — at minimum `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, and
`POSTGRES_PASSWORD`. Generate each secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then bring the stack up:

```bash
docker compose up -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Adminer (DB) | http://localhost:8080 |
| Mailcatcher | http://localhost:1080 |

Sign-in emails go to Mailcatcher locally — nothing leaves your machine.

Longer setup notes, including running either half outside Docker, are in
[development.md](./development.md).

---

## Tests

```bash
docker compose exec backend pytest -q
```

```bash
cd frontend && npm run typecheck && npm run test && npm run build
```

The dependency lock must stay in sync — CI enforces it:

```bash
docker compose exec backend uv lock --check
```

CI ([`.github/workflows/ci.yml`](./.github/workflows/ci.yml)) runs backend
pytest + lock check and frontend typecheck + unit tests + build on every push to
`main` and every PR.

---

## Layout

```
backend/
  app/
    features/         auth · groups · expenses · ai · notifications (nudge engine)
    models.py         imports EVERY feature model module — new ones must be added
    alembic/          migrations
  tests/
frontend/
  src/
    features/         auth · groups · expenses · payments · dashboard · notifications
    client/           generated OpenAPI client (npm run generate-client)
    routes/           TanStack Router file-based routes
    lib/              analytics, sentry, shared utilities
  public/push-sw.js   web-push handlers, folded into the generated service worker
  tests/              Playwright end-to-end journeys
.github/workflows/    CI, nightly DB backup, and the hourly nudge sweep
_bmad-output/         planning artifacts, product review, execution plan
scripts/
```

Code is organised by feature, not by layer, on both sides. API and database use
`snake_case`; the frontend uses `camelCase` with `PascalCase` components. The
service layer owns database access.

Two rules that bite if you miss them:

- A new backend feature model module **must** be imported in
  `backend/app/models.py`, or Alembic and the test suite will not see its tables.
- The frontend API client is generated from the backend's OpenAPI schema. After
  changing an endpoint's signature, run `npm run generate-client` in `frontend/`
  rather than hand-writing types.
- There is no background worker. Scheduled work runs as an idempotent function
  behind an HTTP endpoint, triggered by a GitHub Actions cron — see
  `backend/app/features/notifications/service.py` and
  `.github/workflows/nudge-sweep.yml`. Add scheduled work the same way; don't
  reach for Celery without revisiting the decision in architecture.md.

---

## Documentation

| Document | What it covers |
|---|---|
| [development.md](./development.md) | Local setup, Docker Compose, mailcatcher, linting |
| [deployment.md](./deployment.md) | Vercel + Render + Neon runbook (the live setup) |
| [deployment-vps.md](./deployment-vps.md) | Docker-Compose-on-a-VPS fallback |
| [beta-launch.md](./beta-launch.md) | Private-beta runbook: pre-flight, weekly metric review, kill criteria, measured scheduler numbers |
| [SECURITY.md](./SECURITY.md) | How to report a vulnerability |
| [CLAUDE.md](./CLAUDE.md) | Working agreements for AI-assisted development |

---

## License

MIT — see [LICENSE](./LICENSE).

ClearDues began from
[full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)
by Sebastián Ramírez, also MIT. Very little of the original remains, but the
copyright notice does, as the license requires.
