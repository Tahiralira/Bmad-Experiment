# ClearDues — Backend

FastAPI + SQLModel + Alembic on PostgreSQL. Python 3.13.

## Requirements

* [Docker](https://www.docker.com/) — the supported way to run this
* [uv](https://docs.astral.sh/uv/) — dependency management (and a local venv so
  your editor can resolve imports)

Start the stack from the repo root; see [../development.md](../development.md).

```bash
docker compose up -d
```

For editor support, also create the local environment:

```bash
cd backend && uv sync && source .venv/bin/activate
```

Point your interpreter at `backend/.venv/bin/python`. The venv is for
autocomplete and type checking — the app itself runs in the container.

---

## Architecture

Code is organised **by feature, not by layer**. Everything a domain needs lives
in one directory.

```
app/
  features/
    auth/           users, magic links, OAuth, sessions, payment methods
    groups/         expense groups, membership, invites, settings, balances
    expenses/       expenses, splits, the ledger, settlement claims
    ai/             LLM expense parsing and quota
    notifications/  the nudge engine: sweep, preferences, push + email delivery
  api/
    main.py         mounts every feature router
    deps.py         shared FastAPI dependencies
    routes/         infrastructure routes only (health check, utils)
  core/             config, db, security, limiter, oauth, currency, payment providers
  alembic/          migrations
  models.py         re-exports every feature's models — see the rule below
  crud.py           user-creation helpers used by bootstrap and tests
tests/
```

Each feature directory holds the same three files:

| File | Responsibility |
|---|---|
| `models.py` | SQLModel table and schema definitions |
| `router.py` | HTTP layer — path operations, request/response schemas, auth checks |
| `service.py` | Business logic and **all** database access |

Routers do not touch the database directly. The service layer owns it.
(`notifications/` adds a fourth, `delivery.py`, which owns the two transports
and nothing else.)

### Scheduled work — there is no worker

This service has **no Celery, no Redis, and no background process.** Render's
free plan offers neither a background worker nor a cron job, so scheduled work
is written as an ordinary idempotent function and triggered over HTTP:

```
.github/workflows/nudge-sweep.yml   (hourly cron)
      │  POST, X-Nudge-Secret header
      ▼
POST /api/v1/notifications/internal/run-sweep
      ▼
notifications/service.py :: run_nudge_sweep()
```

The endpoint returns 404 unless `NUDGE_CRON_SECRET` is set, so an unconfigured
deployment exposes nothing. Two properties make this safe to trigger from
anywhere: the sweep is **idempotent** (a per-relationship cooldown, not the
schedule, bounds how often anyone is contacted), and it accepts `?dry_run=true`
to report what *would* happen without writing.

Add new scheduled work the same way. Moving to a real worker later means
changing the trigger, not the engine — the rationale and the conditions for
revisiting it are in `_bmad-output/planning-artifacts/architecture.md` under
"WS12 CORRECTION".

### The `models.py` rule

`app/models.py` imports the model modules of every feature. Alembic's
autogenerate, `scripts/prestart.sh`, and the test suite all rely on that import
to register the complete schema.

**A new feature's model module must be added to `app/models.py`.** If you skip
it, autogenerate will silently emit a migration that drops your tables, and
tests fail with SQLAlchemy's `Mapper "failed to locate a name"`.

### Adding an endpoint

1. Model in `app/features/<name>/models.py` (and register it in `app/models.py`
   if the feature is new).
2. Logic in `app/features/<name>/service.py`.
3. Path operation in `app/features/<name>/router.py`, with a typed request body
   — never a raw `dict` — and an explicit group-membership or ownership check.
4. Mount the router in `app/api/main.py` if the feature is new.
5. Generate a migration (below).
6. Regenerate the frontend client: `cd ../frontend && npm run generate-client`.

---

## Tests

From the repo root:

```bash
docker compose exec backend pytest -q
```

Tests run against a dedicated `<database>_test` database, created automatically
on first run, so your development data is never touched. The suite **refuses to
run unless `ENVIRONMENT=local`** — a guard against ever pointing it at staging or
production.

With coverage (writes `htmlcov/index.html`):

```bash
docker compose exec backend bash scripts/test.sh
```

Extra pytest arguments pass straight through — for example, stop on first
failure:

```bash
docker compose exec backend bash scripts/tests-start.sh -x
```

Tests live in `backend/tests/`. Note that only `tests/` is volume-mounted into
the container: if a new test fails against application code that is obviously
correct, the image is stale. Rebuild it:

```bash
docker compose build backend
```

A known-broken behaviour gets an `xfail`/`skip` carrying a reason that names the
work session which will fix it — never a green assertion that the bug is
correct.

---

## Migrations

Alembic reads models through `app/models.py`. Every model change needs a
revision; there is no "just create the tables" escape hatch, and
`SQLModel.metadata.create_all()` must stay out of the startup path — production
schema comes from migrations only.

Open a shell in the container:

```bash
docker compose exec backend bash
```

Autogenerate a revision after changing a model:

```bash
alembic revision --autogenerate -m "add settled_at to settlement claims"
```

**Read the generated file before applying it.** Autogenerate misses table and
column renames (it emits a drop plus an add, which loses data), server defaults,
and most constraint changes. Edit it until it says what you meant.

Apply it:

```bash
alembic upgrade head
```

Commit the file in `app/alembic/versions/`. `scripts/prestart.sh` runs
`alembic upgrade head` on every deploy, so an unapplied revision reaches
production as soon as it merges.

To undo the most recent revision locally:

```bash
alembic downgrade -1
```

---

## Dependencies

Managed with uv. Add one with `uv add <package>` from `backend/`, which updates
both `pyproject.toml` and `uv.lock`. Commit both.

CI fails if they disagree, so verify before pushing:

```bash
docker compose exec backend uv lock --check
```

## Linting and formatting

```bash
bash scripts/lint.sh
```

```bash
bash scripts/format.sh
```

## Email templates

Sources are MJML in `app/email-templates/src/`; the application sends the
compiled HTML in `app/email-templates/build/`. Editing a template means
recompiling it — install the
[MJML extension](https://marketplace.visualstudio.com/items?itemName=attilabuti.vscode-mjml),
open the `.mjml` file, and run `MJML: Export to HTML` into `build/`. Commit both
files.

`nudge_reminder.html` is the exception: it is **hand-authored with no `.mjml`
source**, because a committed build artifact whose source nobody generates it
from drifts the moment someone re-exports. Edit that one directly, keeping it
table-based and inline-styled.

Templates render through `render_email_template()`, which is Jinja **without
autoescape**. Escape any user-supplied value before putting it in the context —
group names and display names both reach these templates.

Locally, all outbound mail is captured by Mailcatcher at
<http://localhost:1080> — nothing is actually sent. Because the local override
sets `SMTP_HOST=mailcatcher`, `emails_enabled` is **true** in dev: nudge emails
really do get sent, and land there.
