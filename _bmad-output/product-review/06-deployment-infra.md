# Session 6 — Deployment & Infrastructure (Part 5)

**Date:** 2026-07-06
**Scope:** Docker setup, Railway readiness, CI/CD, monitoring, backups, environment
management, scaling (NFR7: 1k WebSocket connections), cost.
**Inputs reviewed:** docker-compose.yml / .override.yml / .traefik.yml, backend and
frontend Dockerfiles, deployment.md, cleardues/scripts/, backend/scripts/, hooks/,
cleardues/.github/workflows/ (13 files), .env.example, .pre-commit-config.yaml,
nginx.conf, git repo layout. Prior-session facts cross-referenced, not re-derived.
**Method:** Adversarial. Severity per CLAUDE.md review scoping; every recommendation
states impact and effort.

**Overall deployment & infrastructure readiness: 2.5 / 10.** The local dev experience
(docker compose with hot-reload, mailcatcher, healthchecked Postgres) genuinely works and
is the best-engineered part of this area — but it is 100% inherited from the FastAPI
full-stack template. Everything above local dev is absent or broken: **all 13 CI/CD
workflows are dead** because they sit in a subdirectory GitHub never scans; the stated
deployment target (Railway) has zero artifacts and is incompatible with everything
actually present (Traefik/VPS compose, plus a third vestigial Docker Swarm path); there
are **no backups, no monitoring, no log rotation**; the architecture's entire real-time/
worker tier (Redis, Celery, WebSockets — the substrate for Epic 6, the product's
differentiator) is not provisioned in any compose file and `redis`/`celery` are not even
declared dependencies. Nothing has ever been deployed (S2). Dead CI is not cosmetic: it
is the single process failure that let a broken test suite (S3), a failing typecheck
(S4), and a stale lockfile (S5-C2) accumulate on the main line unnoticed.

---

## Severity Summary

| # | Severity | Finding | Cross-ref |
|---|----------|---------|-----------|
| C1 | CRITICAL | All CI/CD is dead: workflows live in `cleardues/.github/`, not repo-root `.github/` — GitHub never runs them; triggers also reference `master` (repo uses `main`) and self-hosted runners that don't exist. Dependabot config equally dead | S3/S4/S5 |
| C2 | CRITICAL | No backup or restore story for a financial-records app: one Docker volume on one host, no dumps, no offsite copy, no runbook — compounds S5-C1 key-loss data-bricking | S5 |
| C3 | CRITICAL | Deployment target unresolved: planning says Railway; the repo contains only a Traefik/VPS compose stack plus a vestigial Docker **Swarm** deploy script; zero Railway artifacts; config can't consume `DATABASE_URL`. Three incompatible half-paths, nothing ever shipped | S2 |
| H1 | HIGH | Docker build silently re-resolves security-critical deps: layer 1 `uv sync --frozen` against the stale lock, layer 2 plain `uv sync` re-locks in-container → authlib/cryptography/google-genai float at every build | S5-C2 |
| H2 | HIGH | Real-time/worker tier unprovisioned: no Redis, no Celery worker/beat, no scheduler in any compose file; NFR7 (1k WebSockets) unsupported and untestable; Epic 6 has no infra to land on | S3 |
| H3 | HIGH | No monitoring, alerting, or log management: Sentry DSN plumb-through only (SDK is EOL 1.x), no uptime checks, no metrics, unbounded json-file container logs + Traefik access logs (which contain tokens per S5-H1) → disk-fill on a VPS | S5 |
| H4 | HIGH | Unhardened, semi-reproducible images: backend runs as root on full `python:3.10` (EOL 2026-10 — 3 months away), ships `tests/` into prod; frontend uses `npm install` (lockfile not enforced) with floating `nginx:1` tag; no resource limits anywhere | — |
| M1 | MEDIUM | Entire `.env` injected via `env_file` into db, prestart, backend, and playwright containers — SMTP/OAuth/SECRET_KEY land in the Postgres container's environment | — |
| M2 | MEDIUM | deployment.md is a 100% unedited template runbook (`fastapi-project.example.com`, Swarm-era scripts, GH Actions that can't run) — no accurate way to deploy ClearDues exists on paper | S7 input |
| M3 | MEDIUM | Fine-grained GitHub PAT embedded in plaintext in the git remote URL on the dev machine (visible to `git remote -v`, process listings, tooling logs) | — |
| M4 | MEDIUM | Product nested at `cleardues/` inside a BMAD experiment repo — the root cause of C1; breaks PaaS "connect repo" defaults; template generator machinery (copier.yml, .copier/, hooks/) and fastapi-org community files committed | — |
| M5 | MEDIUM | prestart auto-runs `alembic upgrade head` + superuser bootstrap on every start with no gating or rollback plan; autogenerate is blind to feature models (S3), so drift is detected only in prod | S3, S5-L3 |
| L1 | LOW | Dev override exposes Postgres :5432 / Adminer :8080 on the host and runs Traefik with `--api.insecure` — safe locally, dangerous if ever run on a public box | S5-H3 |
| L2 | LOW | Script rot: build.sh/deploy.sh call legacy `docker-compose` v1 (EOL); pre-commit config uses invalid `language: unsupported` for ruff hooks (pre-commit errors if actually run) | — |
| L3 | LOW | Windows `nul` file artifact in cleardues/ root (untracked); stray redirect accident | — |

---

## CRITICAL

### C1 — CI/CD does not exist in practice (13 dead workflows)
**Where:** `cleardues/.github/workflows/*` (13 files), git repo root =
`Bmad-Experiment/` (verified via `git rev-parse --show-toplevel`); root `.github/`
contains only BMAD agent definitions.

GitHub Actions **only** discovers workflows in `.github/workflows/` at the repository
root. Every workflow in this project — test-backend, playwright, deploy-staging,
deploy-production, pre-commit, smokeshow, generate-client, labeler, etc. — lives under
`cleardues/.github/workflows/`, a path GitHub never scans. `cleardues/.github/
dependabot.yml` is equally invisible, which is why `starlette 0.38.6` (CVE-2024-47874,
S5-H4) and EOL `sentry-sdk 1.x` sat unnoticed. Three more layers of dead-on-arrival
even if the files were moved:

1. **Wrong branch:** `deploy-staging.yml` and `test-backend.yml` trigger on `master`;
   the repo's default branch is `main` (feature branches like `ClearDues/Sprint/Stories/1`).
2. **No runners:** both deploy workflows require self-hosted runners labeled
   `staging`/`production` (deployment.md's VPS-runner recipe) — never provisioned; no
   GitHub environment secrets configured.
3. **Would fail anyway:** `test-backend.yml` runs the pytest suite (broken repo-wide per
   S3) and then `coverage report --fail-under=90`; `playwright.yml` runs the four stale
   template password-auth specs (S4). The first honest CI run will be red.

This is the process root cause behind the state found by Sessions 3–5: **zero automated
gate has ever run** on this codebase. A broken test suite, a failing `npm run
typecheck`, tests importing uninstalled libraries, and a stale uv.lock are exactly the
defects a single working CI job would have rejected at the first offending commit.

**Impact:** No quality gate, no deploy automation, no dependency alerts; broken main
line accumulates silently.
**Effort:** Low for a minimal gate — add root-level `.github/workflows/ci.yml` with
`defaults.run.working-directory: cleardues`, two jobs (backend pytest, frontend
typecheck + build), triggers on `main` + PRs (~0.5 day). Note the jobs only go green
after the S3 annotation fix and S4 typecheck fixes — sequence accordingly. Deleting or
adapting the other 12 template workflows is another ~0.5 day.

### C2 — No backup, no restore, no disaster-recovery story
**Where:** `docker-compose.yml:165-166` (single `app-db-data` named volume); no dump
service, cron, or object-storage target anywhere in compose/scripts/docs.

ClearDues stores **shared financial records** — the one data class users will not
forgive losing. The entire persistence story is one Docker named volume on one host.
There is no `pg_dump` sidecar or cron, no offsite/object-storage copy, no
point-in-time recovery, no restore runbook, and no backup mention in deployment.md.
Compounding factors already on file:

- S5-C1: `SECRET_KEY` defaults to random-per-process and derives the Fernet key — a
  restart with a missing `.env` **permanently bricks all stored Gemini API keys**. With
  no backups, "permanently" is literal.
- S3: `DELETE /users/me` can cascade-delete shared expenses; with no backups, one
  user's account deletion irreversibly corrupts other users' balances.
- A `docker compose down -v` (the exact command in `scripts/test.sh` and the CI
  workflow!) removes the data volume if run against the wrong environment.

Nothing is deployed yet, so nothing has been lost — this is a **launch blocker**, not
an incident. Per CLAUDE.md scoping, data-loss risk = CRITICAL.

**Impact:** First disk failure, bad migration, fat-fingered `down -v`, or key rotation
after launch = unrecoverable loss of user financial data.
**Effort:** Low. Nightly `pg_dump` sidecar (e.g. `prodrigestivill/postgres-backup-local`
or a 10-line cron container) shipping to B2/S3-class storage + one documented,
**tested** restore ≈ 0.5 day. Managed-Postgres (Railway/Neon) backups are an argument
for C3's PaaS option.

### C3 — Deployment target is unresolved: Railway on paper, Traefik/VPS in code, Swarm in scripts
**Where:** architecture.md:123/154/157, epics.md:82, CLAUDE.md ("Infra: Docker + Railway
(Target)") vs docker-compose*.yml + deployment.md (Traefik/VPS/self-hosted-runner) vs
`scripts/deploy.sh` (Docker **Swarm**: `docker stack deploy` + `docker-auto-labels`).

Three mutually incompatible deployment stories coexist:

1. **Planning says Railway** — chosen explicitly for Celery/Redis support
   (architecture.md:123), with "GitHub Actions deploy to Railway" (architecture.md:157).
   **Zero Railway artifacts exist**: no railway.toml/json, no Procfile, no service
   config. Railway ignores docker-compose entirely (one service per deploy; Traefik,
   adminer, and the prestart-container pattern don't map). `config.py` builds its DSN
   from `POSTGRES_*` parts (config.py:62-75) and cannot consume the `DATABASE_URL`
   Railway injects — a small but real adapter gap.
2. **The repo implements the tiangolo Traefik/VPS path** — wildcard DNS, manual Traefik
   bootstrap, self-hosted GitHub runners on the box (deployment.md). Nobody has executed
   any of it (S2: zero deployments).
3. **`scripts/deploy.sh` targets Docker Swarm** — `docker stack deploy` with
   `docker-auto-labels`, a leftover from an older template generation that matches
   neither of the above.

Any engineer (or agent) told to "deploy ClearDues" today gets three contradictory
answers, none executable as-is. Combined with C1, the release plan ("bundled after
Epic 5", S2) has no mechanical path to happen.

**Impact:** Shipping is blocked on an undecided architecture question; effort spent
maintaining three paths' worth of config that all rot.
**Effort:** The decision is ~0. Recommendation below (see "Recommended path"): deploy
the existing compose to a single cheap VPS for the private beta (closest to working
today, ~1 day including hardening), and revisit Railway only when Epic 6 forces managed
Redis. Committing to Railway instead ≈ 2-3 days (service split, DATABASE_URL adapter,
drop Traefik/adminer/prestart, static-host the frontend). Either way, **delete the two
losing paths** (~1 h) so only one truth remains.

---

## HIGH

### H1 — Docker build silently re-resolves the security-critical dependencies
**Where:** `backend/Dockerfile:25-28` (`uv sync --frozen --no-install-project`) vs
`:41-42` (plain `uv sync`); `backend/uv.lock` (verified: no `authlib`, `cryptography`,
`google-genai`, `redis`, or `celery` entries).

S5-C2 established the lockfile omits authlib/cryptography/google-genai. The
**infrastructure consequence** is in the Dockerfile: the first sync installs from the
stale lock, then the second `uv sync` (no `--frozen`/`--locked`) detects the
lock-vs-pyproject drift, **re-resolves and rewrites the lockfile inside the container**,
and installs whatever versions are current at build time. Verified import chain:
`authlib` is a top-level import (`app/core/oauth.py:6`), so without that second sync
the image wouldn't even boot — meaning every image ever built has depended on this
silent re-resolution. Consequences:

- Non-reproducible builds precisely for the OAuth/JWT/encryption libraries; a staging
  image and a production image built a week apart can run different crypto code.
- `authlib>=1.3.0` can legitimately resolve to the CVE-2024-37568-vulnerable 1.3.0 (S5).
- The committed uv.lock is fiction: nothing that runs in Docker matches it.
- Also verified: `redis` and `celery` appear in **neither** uv.lock **nor**
  pyproject.toml — the architecture's worker stack isn't a dependency, let alone a
  service (see H2).

**Impact:** Supply-chain/reproducibility hole in every image built since the OAuth
stories; masks S5-C2 instead of failing fast.
**Effort:** Low. `uv lock` locally, commit, change both Dockerfile syncs to `--locked`
(which **fails the build** on drift instead of papering over it), pin authlib>=1.3.1.
~1-2 h. Add the lock-freshness check to the C1 CI job (~15 min).

### H2 — The real-time/worker tier the architecture depends on is not provisioned
**Where:** all three compose files (services: db, adminer, prestart, backend, frontend;
override adds proxy, mailcatcher, playwright — verified complete list); pyproject.toml
(no redis/celery); S3 (zero WebSocket/Celery code, event publisher no-ops).

Architecture and CLAUDE.md promise "WebSockets + Redis Pub/Sub" and "Celery + Redis".
Infrastructure reality: **no redis service, no celery worker, no celery beat, no
scheduler of any kind in any compose file**, and the libraries aren't dependencies.
This isn't just "Epic 6 not started" (S1) — there is no substrate for it:

- **NFR7 ("support 1,000 concurrent WebSocket connections") is unsupported and
  untestable.** There is nothing to scale, no load-test harness, and no pub/sub
  backplane — required the moment WebSockets meet the backend's `--workers 4`
  (Dockerfile:44), since two workers can't share connection state without Redis.
- **Progressive Urgency notifications** (the product's core differentiator) require a
  scheduler (beat) to escalate nudges over time. No component in the stack can wake up
  on a timer.
- The single Redis event publisher already written silently no-ops via a swallowed
  ImportError (S3) — so when Redis is finally added, code that "worked" for months will
  start emitting events nobody has ever seen. Integration risk deferred to the worst
  possible moment.

**Impact:** Epic 6 is blocked on infra that doesn't exist; NFR7 is currently a fictional
requirement; deferred-integration risk on the differentiator.
**Effort:** Medium, and correctly sequenced it's *deferred*: add redis + worker + beat
services to compose (or Railway plugins) **when Epic 6 starts** (~0.5-1 day), plus a
basic WS load test (locust/k6, ~1 day) before claiming NFR7. Flagged now so the C3
platform decision weighs managed Redis availability.

### H3 — No monitoring, no alerting, no log management
**Where:** `app/main.py` Sentry init (S5); compose files (no `logging:` config on any
service, no resource limits); `docker-compose.override.yml:28`/`docker-compose.traefik.yml:59`
(`--accesslog` with no rotation); no uptime/metrics/alerting config anywhere.

Observability today is exactly one thing: a `SENTRY_DSN` env passthrough to an EOL 1.x
SDK (S5-M7) that nobody has configured (zero deployments). Missing, in order of pain:

- **Uptime:** nothing pings `/api/v1/utils/health-check/` from outside. The endpoint
  exists and the compose healthcheck uses it (good — verified `utils.py:29`), but a
  healthcheck without an alert only restarts containers; nobody finds out the site is
  down except users. The frontend service has no healthcheck at all.
- **Log rotation:** every service uses Docker's default json-file driver with **no
  max-size/max-file limits**, and Traefik's access log is enabled with no rotation. On
  the C3 VPS path this fills the disk — and per S5-H1 those access logs contain 30-day
  bearer tokens, so unbounded retention is also a security-retention problem.
- **Metrics/APM:** none (no Prometheus, no Traefik metrics endpoint, no DB metrics).
  Acceptable pre-beta; uptime + logs are not.

**Impact:** Post-launch outages and disk-fill are discovered by users; token-bearing
logs retained indefinitely.
**Effort:** Low for the essentials: UptimeRobot/Better Stack on the health-check (~1 h,
free tier), `logging: {driver: json-file, options: {max-size: 10m, max-file: "3"}}` on
all services + Traefik log rotation (~1 h), Sentry SDK 2.x upgrade with PII scrubbing
(S5-M7, ~2-3 h).

### H4 — Unhardened, oversized, soon-to-be-EOL production images
**Where:** `backend/Dockerfile:1,37,44`; `frontend/Dockerfile:2,8,18`; compose (no
`deploy.resources` / `mem_limit` anywhere).

- **Backend** runs as **root** (no `USER` directive) on the full `python:3.10` image
  (~1 GB base, not `-slim`). **Python 3.10 reaches end-of-life October 2026 — three
  months from today** — after which no security patches; `requires-python = ">=3.10,<4.0"`
  permits moving to 3.12/3.13 now. The image also ships `COPY ./tests /app/tests`
  (Dockerfile:37) into production.
- **Frontend** builds with `npm install` instead of `npm ci` (Dockerfile:8) — the same
  lockfile-not-enforced defect class as H1, on `node:24` (fine) — and serves from the
  floating `nginx:1` major tag. nginx.conf sets no gzip, no cache headers, and none of
  the security headers from S5-M1; it will serve the S4-flagged 1.48 MB bundle
  uncompressed unless nginx defaults save it.
- **No resource limits on any service**: a memory leak in the backend (or the S5-H4
  multipart DoS) takes down Postgres on the same box.

**Impact:** Larger attack surface, root-owned containers, EOL runtime at/just after
launch, noisy-neighbor failure modes on a single host.
**Effort:** Low-Medium, one pass (~0.5 day): `python:3.13-slim` + non-root `USER`,
drop tests COPY, `npm ci`, pin `nginx:1.27-alpine`, add mem/cpu limits and gzip +
security headers in nginx.conf (kills S5-M1 for the frontend at the same time).

---

## MEDIUM

### M1 — The entire `.env` is injected into containers that shouldn't have it
**Where:** `docker-compose.yml:14-15` (db), `:57-58` (prestart), `:90-91` (backend);
`docker-compose.override.yml:116-117` (playwright).

`env_file: .env` hands **every** secret — `SECRET_KEY`, SMTP credentials, OAuth client
secrets, superuser password — to the **Postgres container**, the prestart container,
and (locally) the Playwright container, on top of the explicit `environment:` blocks
that already pass what each service needs. `docker inspect db`, a Postgres-container
compromise, or an Adminer RCE (it runs adjacent — S5-H3) now yields the app's full
secret set, not just DB credentials.
**Impact:** Needlessly wide secret blast radius across containers.
**Effort:** Trivial. Delete `env_file` from db/playwright (their `environment:` blocks
already enumerate what they need); keep it only on backend/prestart or enumerate there
too. ~30 min.

### M2 — There is no accurate deployment runbook (deployment.md is untouched template)
**Where:** `cleardues/deployment.md` (entire file).

deployment.md still says `fastapi-project.example.com` throughout, documents the
self-hosted-runner + Traefik recipe that C1/C3 show is dead, references GitHub secrets
nobody set, and mentions Smokeshow/latest-changes actions irrelevant to ClearDues. It
contains **zero** ClearDues-specific facts (no OAuth callback URL setup, no
SECRET_KEY/Fernet warning from S5-C1, no SMTP provider choice, no domain). The one
document an operator would reach for during a launch or an incident is fiction.
Session 7 should count this in the docs inventory; the **operational** risk is logged
here.
**Impact:** Any deploy/incident becomes archaeology; the S5-C1 key-loss trap is
undocumented, making the C2 data-bricking scenario *likely* rather than possible.
**Effort:** Low once C3 is decided: rewrite as a 1-2 page ClearDues runbook (provision,
secrets checklist incl. Fernet-key warning, deploy, rollback, restore-from-backup).
~0.5 day.

### M3 — GitHub PAT embedded in plaintext in the git remote URL
**Where:** local `.git/config` remote URL (observed via `git remote -v`; token not
reproduced here).

The `origin` remote embeds a fine-grained GitHub PAT directly in the HTTPS URL. It is
not committed to the repo, but it sits in plaintext on disk, prints in full on every
`git remote -v`, leaks into any tool/agent log that echoes remotes (this review's
tooling included), and grants push access to the repo. This is exactly the class of
credential the (currently dead) CI would eventually need — set a precedent of managed
credentials now.
**Impact:** Repo write-access credential exposed to anything that can read the dev
machine's disk or logs.
**Effort:** Trivial. Rotate the token, switch the remote to a credential helper
(Git Credential Manager on Windows) or SSH. ~30 min.

### M4 — Repo nesting and committed template machinery
**Where:** repo root `Bmad-Experiment/` vs product at `cleardues/`; `cleardues/copier.yml`,
`.copier/`, `hooks/post_gen_project.py`, `.github/FUNDING.yml` (funds the fastapi org),
`ISSUE_TEMPLATE/`, `DISCUSSION_TEMPLATE/`, `labeler.yml`, `release-notes.md`.

The product living one directory down inside a BMAD-experiment repo is the **root
cause of C1** (workflows/dependabot invisible) and adds friction to every PaaS
"connect your repo" flow (root-directory overrides needed per service). Additionally
the copier template generator machinery and fastapi-org community files (funding
config pointing at tiangolo's sponsors, fastapi issue/discussion templates) are
committed as if this were still the template repo.
**Impact:** Structural cause of dead CI; misdirected community metadata; every
deploy/CI config pays a working-directory tax forever.
**Effort:** Two options — (a) live with nesting and use `working-directory`/root-dir
overrides everywhere (~0 upfront, permanent tax), or (b) extract `cleardues/` to its
own repo (~2-3 h with history via `git filter-repo`, or ~30 min without). Deleting
template metadata: ~30 min either way. Recommend (b) before the first real deploy.

### M5 — Ungated auto-migrations + superuser bootstrap on every container start
**Where:** `backend/scripts/prestart.sh` (`alembic upgrade head` + `initial_data.py`),
`docker-compose.yml:45-56` (prestart runs on every `up`).

Every environment start unconditionally migrates the schema and re-asserts a
password-authable superuser (S5-L3). There is no migration review gate, no dry-run, no
rollback script, and no backup taken first (C2). S3 established Alembic autogenerate is
blind to all feature models (env.py imports only `app.models`) — so the first
hand-written feature-model migration that's wrong gets applied to production
automatically at deploy time, with no backup to restore.
**Impact:** Bad migration auto-applies to prod; combined with C2, unrecoverable.
**Effort:** Low. Keep auto-migrate (fine at this scale) but: fix env.py imports (S3),
add `pg_dump` before `upgrade head` in prestart (~1 h), and document downgrade steps
per migration. Superuser hardening tracked as S5-L3.

---

## LOW

- **L1 — Dev override is unsafe to run anywhere public.** Host-published Postgres
  (`5432:5432`) and Adminer (`8080:8080`), Traefik with `--api.insecure=true`
  (override:36). Fine on a laptop; one `docker compose up` on a cloud box exposes a DB
  and an admin panel. Effort: add a comment warning + consider binding to 127.0.0.1
  (~15 min).
- **L2 — Script/config rot.** `scripts/build.sh`, `build-push.sh`, `deploy.sh` invoke
  the EOL v1 `docker-compose` binary (others use `docker compose`); `deploy.sh` targets
  Swarm (see C3); `.pre-commit-config.yaml` declares `language: unsupported` for the
  ruff hooks — not a valid pre-commit language, so the hook set errors if anyone
  actually installs it (evidence nobody runs pre-commit locally, consistent with C1's
  "no gate has ever run"). Effort: delete dead scripts, fix or remove pre-commit
  config (~1 h).
- **L3 — `cleardues/nul` file.** Stray Windows artifact from a `> nul` redirect under
  a POSIX shell; untracked. Delete (~1 min; needs `\\.\nul`-style handling or git bash
  `rm`).

---

## Scaling & NFR7 Assessment

**Current ceiling is irrelevant — and that's the finding.** With zero deployments and
zero users, the stack's scaling properties are hypothetical, but the promises are on
paper:

- **NFR7 (1k concurrent WebSockets):** unsupported today (H2 — no WS code, no Redis
  backplane, no load harness). When built: 1k idle WS connections are trivial for
  uvicorn memory-wise, but `--workers 4` requires Redis pub/sub for cross-worker
  fan-out from day one, and Traefik handles WS upgrades natively (no config needed).
  A single 4 GB VPS will meet NFR7 comfortably **if** the backplane exists. Declare
  NFR7 "not yet applicable" honestly instead of implying readiness.
- **Database:** SQLAlchemy default pool (5 + 10 overflow) × 4 workers = up to 60
  connections against Postgres's default `max_connections=100`. Fine now; add pool
  sizing config before adding Celery workers (which take their own connections).
- **Horizontal scale:** none on the VPS path (single host, no registry-based images —
  compose builds locally). Acceptable for beta; Railway path scales services
  independently. Neither matters before Epic 6 ships and real load exists.

## Cost Estimate

Cost is a non-issue at this stage; decision paralysis is the expensive part.

| Path | Monthly estimate | Notes |
|------|------------------|-------|
| **VPS (recommended for beta)** | **$10–25** | Hetzner CX22/CPX21 (~€5–9) or DO 4 GB ($24); staging+prod on one box via STACK_NAME; domain ~$12/yr; SMTP (SES/Mailgun) $0–15; Sentry + UptimeRobot free tiers; backups to B2 ~$1 |
| **Railway** | **$15–35 early** | Hobby seat $5 + usage: backend $5–10, Postgres $5–10, frontend $1–3 (or free on Cloudflare Pages), Redis +$5–10 at Epic 6; managed backups included (partially offsets C2) |
| **AI (Gemini)** | $0 to ClearDues | BYOK — users bear parse costs (S1); revisit if BYOK is dropped (S1/S2 flagged BYOK as an onboarding problem) |

Either path is under the cost of one hour of development time per month.

## Recommended Path (prioritized, impact × effort)

1. **Decide C3 now — recommendation: existing compose on one cheap VPS for private
   beta; defer Railway until Epic 6 forces managed Redis.** Delete the Swarm script
   and either the Railway claim or the Traefik stack from planning docs. (Unblocks
   everything; decision free, cleanup ~1 h.)
2. **Stand up minimal root-level CI** (C1): one workflow, `working-directory:
   cleardues`, backend tests + frontend typecheck/build, on `main` + PRs. Prerequisites:
   S3 annotation fix, S4 typecheck fixes. (~0.5 day; highest process ROI in the
   entire review — it converts S3/S4/S5 regressions from chronic to impossible.)
3. **Re-lock dependencies and make builds fail on drift** (H1 + S5-C2/H4): `uv lock`,
   `--locked` in both Dockerfile syncs, bump starlette/authlib/sentry, add lock check
   to CI. (~2-3 h.)
4. **Backups before the first external user** (C2): nightly pg_dump → object storage +
   one tested restore + pre-migration dump in prestart (M5). (~0.5-1 day.)
5. **One hardening pass on compose + images** (H4/M1/L1 + S5-H3): remove adminer from
   prod compose, non-root slim py3.13 image, npm ci, log rotation, resource limits,
   env_file scoping, nginx gzip + security headers. (~1 day, closes five findings.)
6. **Minimal observability** (H3): uptime monitor on health-check + Sentry 2.x
   scrubbed. (~0.5 day.)
7. **Rotate the PAT, adopt a credential helper** (M3). (~30 min.)
8. **When Epic 6 starts:** provision Redis/Celery/beat + WS load test (H2). Not before.

Total to a deployable, monitored, backed-up beta stack: **~4 developer-days** once the
S3/S4 code fixes land. The infrastructure is not the long pole — the broken test/type
gates and the unbuilt product surface (S3/S4) are.

## What is actually done well (verified, not assumed)

- **Local dev environment is genuinely good:** hot-reload via `develop.watch` with
  correct .venv excludes, mailcatcher for email flows, Adminer for DB inspection,
  Playwright container wired for e2e — all working per compose config.
- **Compose fundamentals are right:** db healthcheck (`pg_isready`) with
  `depends_on: condition: service_healthy`, prestart-as-a-service migration pattern
  with `service_completed_successfully` gating the backend, backend healthcheck against
  a real endpoint (verified `utils.py:29`), fail-fast `${VAR?Variable not set}`
  interpolation on secrets.
- **Secrets hygiene at the repo level:** `.env` properly gitignored and never in git
  history (re-verified this session after an initial false alarm), `.env.example`
  provided, prod compose exposes no DB port.
- **Traefik TLS story is sound:** Let's Encrypt TLS-challenge resolver, https-redirect
  middleware, `exposedbydefault=false`, basic-auth on the Traefik dashboard.
- **Backend Dockerfile follows uv best practices** (layer-cached deps, bytecode
  compile, bind-mounted lock for the dep layer) — undermined only by the H1 second
  sync; **frontend build is properly multi-stage** (node build → nginx serve).
- **`.dockerignore` files exist** for both images.

---

## Key Facts Established in Session 6 (do not re-verify)

- **CI/CD is entirely dead:** 13 workflows + dependabot live under
  `cleardues/.github/`, which GitHub never scans (repo root is `Bmad-Experiment/`);
  triggers also target `master` (default branch is `main`) and self-hosted runners
  that don't exist. No automated gate has ever run on this codebase. (C1.)
- **No backups of any kind** — one Docker volume, no dumps, no offsite, no restore
  runbook; `docker compose down -v` appears in scripts/CI. Launch blocker for a
  financial app. (C2.)
- **Three contradictory deployment paths, none executed:** Railway (planning docs only,
  zero artifacts, config.py can't read DATABASE_URL), Traefik/VPS (template compose +
  deployment.md), Docker Swarm (`scripts/deploy.sh`). (C3.)
- **backend/Dockerfile line 41's plain `uv sync` silently re-locks in-container**,
  installing unpinned authlib/cryptography/google-genai at every build (uv.lock omits
  them; authlib is a top-level import at core/oauth.py:6). Committed lock ≠ shipped
  deps. `redis`/`celery` are in neither uv.lock nor pyproject. (H1, extends S5-C2.)
- **No Redis/Celery/WS services in any compose file** — NFR7 (1k WebSockets)
  unsupported/untestable; Epic 6 has no infra substrate and nothing can run scheduled
  jobs. (H2.)
- **No monitoring/log rotation:** Sentry DSN passthrough only; unbounded json-file +
  Traefik access logs (which carry tokens per S5-H1). Backend healthcheck endpoint
  exists and is wired. (H3.)
- Backend image: root user, full `python:3.10` (EOL 2026-10), ships tests/; frontend:
  `npm install` not `npm ci`, floating `nginx:1`; no resource limits. (H4.)
- Full `.env` (SMTP/OAuth/SECRET_KEY) injected into the Postgres container via
  `env_file`. (M1.)
- deployment.md is 100% unedited template (`fastapi-project.example.com`); no accurate
  runbook exists. (M2.)
- A GitHub PAT sits in plaintext in the local git remote URL. (M3.)
- `.env` is confirmed ignored and absent from all git history (S5's claim re-verified —
  a `git check-ignore` output was initially misread as `git ls-files`).
- Deployment & infrastructure readiness score: 2.5/10. Estimated ~4 dev-days to a
  deployable, backed-up, monitored beta stack once S3/S4 code fixes land.
