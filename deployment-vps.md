# ClearDues Deployment Runbook — VPS fallback (SUPERSEDED)

**SUPERSEDED 2026-07-16 (WS9.5):** the active deployment path is **Vercel +
Render + Neon** — see [deployment.md](./deployment.md). This file is kept as
the self-host fallback (the compose stack it describes still exists and passed
a full local verification incl. an executed restore drill in WS9), and its
"Backups" section still documents the local-compose backup sidecar used in dev.

**Original decision (WS9, 2026-07-15):** ClearDues deploys as **Docker Compose
on a single VPS behind Traefik** for the private beta. The former Railway plan
and the Docker Swarm script are void and deleted (S6-C3).

Stack: `docker-compose.traefik.yml` (shared Traefik, TLS via Let's Encrypt) +
`docker-compose.yml` (db, db-backup, pre-migrate-dump, prestart, backend,
frontend). Local dev additionally layers `docker-compose.override.yml`
(Adminer, mailcatcher, hot-reload) — **never run the override on a public box**:
it publishes Postgres/Adminer and runs Traefik with `--api.insecure`.

## 1. Provision (one-time)

1. VPS: 4 GB RAM / 2 vCPU (Hetzner CX22-class, ~€6/mo), Ubuntu 24.04 LTS.
   Install Docker Engine + compose plugin; enable unattended security upgrades;
   SSH keys only.
2. DNS A records → VPS IP: `api.<domain>`, `dashboard.<domain>`,
   `traefik.<domain>`.
3. Clone the repo on the box (the app lives at the repo root since the WS9.6
   flattening — compose files, backend/ and frontend/ are all top-level).
4. Traefik bootstrap (once per box):

   ```bash
   docker network create traefik-public
   export USERNAME=admin EMAIL=<you> DOMAIN=<domain>
   export HASHED_PASSWORD=$(openssl passwd -apr1)   # dashboard basic-auth
   docker compose -f docker-compose.traefik.yml up -d
   ```

## 2. Secrets checklist (`.env` on the VPS, mode 600, NEVER committed)

Copy `.env.example` and set — generators in parentheses:

| Variable | Notes |
|----------|-------|
| `ENVIRONMENT` | `staging` or `production` — gates HSTS, key validation, docs |
| `DOMAIN`, `FRONTEND_HOST` | your domain; `https://dashboard.<domain>` |
| `SECRET_KEY` | (`python -c "import secrets; print(secrets.token_urlsafe(32))"`) — signs JWTs; **changing it logs everyone out** |
| `ENCRYPTION_KEY` | same generator. **WARNING (S5-C1): losing or rotating this permanently bricks every stored user Gemini key** — users must re-enter them. Keep a copy in your password manager, not only in `.env`. |
| `POSTGRES_PASSWORD` | same generator; only the db/backup/backend containers see it |
| `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD` | bootstrap admin identity |
| `GOOGLE_CLIENT_ID/SECRET` | Google Cloud Console → OAuth client. Authorized redirect URI: `https://api.<domain>/api/v1/auth/oauth/google/callback`. Set `OAUTH_REDIRECT_BASE_URL=https://api.<domain>` |
| `GITHUB_CLIENT_ID/SECRET` | GitHub Developer settings; callback as above with `github` |
| `GEMINI_API_KEY` | hosted AI parsing; empty disables hosted parses (BYOK still works) |
| `SMTP_*`, `EMAILS_FROM_EMAIL` | transactional email (magic links). SES/Mailgun free tiers fine |
| `SENTRY_DSN` | error reporting (SDK 2.x, `send_default_pii=False`) |
| `STACK_NAME`, `DOCKER_IMAGE_*`, `TAG` | e.g. `cleardues`, `cleardues-backend`, `cleardues-frontend`, git SHA for `TAG` |
| `BACKUP_KEEP_DAYS`, `BACKUP_TIME` | optional; defaults 14 days, 03:00 UTC |

## 3. Deploy (staging and production are the same procedure, different `.env`)

```bash
git pull
export TAG=$(git rev-parse --short HEAD)
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
curl -fsS https://api.<domain>/api/v1/utils/health-check/   # expect 200 true
```

Startup order is enforced by compose: db (healthy) → **pre-migrate-dump** (a
fresh `pg_dump` MUST succeed or the deploy stops) → prestart (`alembic upgrade
head`) → backend. The frontend is static nginx and starts independently.

## 4. Rollback

Application code (no bad migration): `git checkout <last-good-sha>`, rebuild,
`up -d` — images are immutable per-TAG, so re-running with the old TAG works too.

Bad migration: every deploy took a dump seconds before migrating.

```bash
docker compose -f docker-compose.yml stop backend prestart
docker compose -f docker-compose.yml exec db-backup bash -c \
  'export PGPASSWORD="$POSTGRES_PASSWORD";
   pg_restore -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists \
   $(ls -t /backups/pre-migrate-*.dump | head -1)'
git checkout <last-good-sha> && docker compose -f docker-compose.yml build backend
docker compose -f docker-compose.yml up -d
```

## 5. Backups (S6-C2)

- **Nightly:** the `db-backup` sidecar (postgres:17 + `scripts/db-backup.sh`)
  dumps to the `app-db-backups` volume at `BACKUP_TIME` UTC, keeps
  `BACKUP_KEEP_DAYS` days. **Pre-migration:** `pre-migrate-dump` gates every
  deploy (above).
- **Offsite (host cron, REQUIRED before real users):** sync the volume to
  object storage, e.g. Backblaze B2 via rclone:

  ```bash
  # /etc/cron.d/cleardues-backup-offsite  (04:00 UTC, after the nightly dump)
  0 4 * * * root docker run --rm -v cleardues_app-db-backups:/backups:ro \
    -v /root/.config/rclone:/config/rclone rclone/rclone \
    sync /backups b2:cleardues-backups
  ```

- **Manual dump any time:**
  `docker compose -f docker-compose.yml exec db-backup bash /usr/local/bin/db-backup.sh once manual`

### Restore drill (run once per quarter — an untested backup is not a backup)

```bash
# 1. restore newest dump into a scratch database
docker compose -f docker-compose.yml exec db-backup bash -c '
  export PGPASSWORD="$POSTGRES_PASSWORD";
  latest=$(ls -t /backups/*.dump | head -1); echo "restoring $latest";
  psql -h db -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS restore_drill" &&
  psql -h db -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE restore_drill" &&
  pg_restore -h db -U "$POSTGRES_USER" -d restore_drill "$latest"'
# 2. sanity: row counts match production expectations
docker compose -f docker-compose.yml exec db psql -U postgres -d restore_drill -c \
  'SELECT (SELECT count(*) FROM "user") users, (SELECT count(*) FROM expense) expenses;'
# 3. clean up
docker compose -f docker-compose.yml exec db psql -U postgres -d postgres -c \
  'DROP DATABASE restore_drill;'
```

## 6. Monitoring & logs (S6-H3)

- **Uptime (do this on day one):** free UptimeRobot/Better Stack monitor on
  `https://api.<domain>/api/v1/utils/health-check/` AND
  `https://dashboard.<domain>/` — alert to email/phone. A container healthcheck
  only restarts; the monitor is what tells a human.
- **Logs:** every service (Traefik included) uses `json-file` capped at
  10 MB × 3 files — `docker compose logs backend --since 1h` is the tool.
- **Sentry:** set `SENTRY_DSN`; PII is not sent by default.

## 7. One-time credential/repo actions (WS9 — owner to-do)

1. **Rotate the GitHub PAT** that was embedded in the old remote URL
   (github.com → Settings → Developer settings → Fine-grained tokens → revoke +
   recreate). It sat in plaintext in `.git/config` and printed in tool logs.
2. **Repoint the remote without the token** (Git Credential Manager then
   handles auth): `git remote set-url origin https://github.com/Tahiralira/Bmad-Experiment.git`
3. **Extract ClearDues to its own repository** (S6-M4 — optional since the
   WS9.6 flattening put the app at the repo root; a subtree split was drilled
   successfully in WS9 against the old `cleardues/` prefix, 55 commits
   preserved). Today the extraction is just pushing this repo to a new remote —
   optionally dropping the BMAD artifacts first:

   ```bash
   git remote add cleardues <new-empty-github-repo-url>
   git push -u cleardues main
   # optional slimming afterwards: git rm -r _bmad-output && commit
   ```
