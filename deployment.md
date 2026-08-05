# ClearDues Deployment Guide — Vercel + Render + Neon

**Decision (WS9.5, 2026-07-16):** frontend on **Vercel**, API on **Render**,
Postgres on **Neon**, domain **cleardues.site**. Everything runs on free tiers
until real users arrive (upgrade triggers in §8). The previous compose-on-VPS
runbook survives as a fallback in [deployment-vps.md](./deployment-vps.md);
local development via `docker compose up -d` is unchanged.

**The shape of what you're deploying:**

```
browser ──▶ Vercel  (static React SPA, cleardues.site)
               │ fetch()
               ▼
            Render  (FastAPI, api.cleardues.site, free instance)
               │ psycopg + TLS
               ▼
            Neon    (Postgres 17, scale-to-zero)
```

Each platform connects to your GitHub repo and redeploys itself on every push
— you never copy files anywhere. Total hands-on time: ~45 minutes.

---

## §0 Prerequisites (one-time)

1. Accounts (all free, sign up with your GitHub account so repo access is
   one click): [neon.com](https://neon.com), [render.com](https://render.com),
   [vercel.com](https://vercel.com).
2. **Get this code onto `main`.** Render/Vercel default to deploying the
   `main` branch, and GitHub only runs *scheduled* workflows (our nightly DB
   backup) from the default branch. The product currently lives on the
   `ws9.6/repo-restructure` branch chain, so:

   ```bash
   git checkout main
   git merge ws9.6/repo-restructure
   git push origin main
   ```

   (CI runs automatically on that push — wait for the green check.)
3. Buy `cleardues.site` at a registrar (Porkbun/Namecheap — ~$3–10 the first
   year; check the *renewal* price before buying). You can do all of §1–§3
   before the domain exists and add it in §4 later.

## §1 Neon (database) — ~5 minutes

1. Neon dashboard → **New Project**: name `cleardues`, **Postgres version
   17** (must match our tooling — don't leave whatever default is selected),
   region close to your users (and ideally the same one you'll pick on Render).
2. On the project dashboard, open **Connect** and toggle the connection
   string to **Direct** (host **without** `-pooler` — the pooled string
   breaks migrations). It looks like:

   ```
   postgresql://neondb_owner:PASSWORD@ep-xxx-xxx.REGION.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```

3. Save two things somewhere safe:
   - the **whole string** (you'll paste it into GitHub for backups, §6), and
   - its **parts**, which map to the Render env vars you'll fill in §2:

   | Piece of the string | Render env var |
   |---|---|
   | `neondb_owner` | `POSTGRES_USER` |
   | `PASSWORD` | `POSTGRES_PASSWORD` |
   | `ep-xxx-xxx.REGION.aws.neon.tech` | `POSTGRES_SERVER` |
   | `neondb` | `POSTGRES_DB` |
   | (already set in render.yaml) | `POSTGRES_SSLMODE=require` |

Good to know: Neon's free plan suspends compute after ~5 idle minutes and
resumes in well under a second — the backend handles this (`pool_pre_ping`),
you'll never notice.

## §2 Render (backend API) — ~10 minutes

1. Render dashboard → **New → Blueprint** → connect GitHub → pick this repo.
   Render finds [render.yaml](./render.yaml) at the repo root and shows the
   `cleardues-api` service it's about to create.
2. It prompts for every "ask me" variable. Fill from §1 plus:
   - `FIRST_SUPERUSER` — your email
   - `FRONTEND_HOST` — `https://cleardues.site` (if no domain yet, put the
     Vercel URL from §3 and update later)
   - `BACKEND_CORS_ORIGINS` — `https://cleardues.site,https://www.cleardues.site`
     (plus the `https://….vercel.app` URL while testing)
   - `OAUTH_REDIRECT_BASE_URL` — `https://api.cleardues.site` (until DNS is
     live: `https://cleardues-api.onrender.com`)
   - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — from §5 (you can paste
     placeholders now and fix after §5, but you can't log in until §5 is done)
   - Leave `GITHUB_*`, `GEMINI_API_KEY`, `SENTRY_DSN` blank for now.
3. Click **Apply**. First build takes a few minutes: `uv sync --locked`
   installs deps, then the start command runs `alembic upgrade head` (your
   schema lands in Neon) and boots uvicorn. Watch the **Logs** tab — this is
   the best way to *learn* what a deploy actually does.
4. **Immediately** copy the generated `ENCRYPTION_KEY` (service →
   Environment) into your password manager. If this value is ever lost or
   changed, every stored user Gemini key is permanently unreadable.
5. Verify: `https://cleardues-api.onrender.com/api/v1/utils/health-check/`
   in your browser → `true`.

Free-plan reality: the instance spins down after 15 idle minutes; the next
request takes ~1 minute while it wakes. Normal, and gone the day you move to
Starter ($7/mo).

## §3 Vercel (frontend) — ~5 minutes

1. Vercel dashboard → **Add New → Project** → import this repo.
2. The one setting that matters: **Root Directory = `frontend`**
   (Framework Preset auto-detects Vite from there).
3. Environment variable: `VITE_API_URL` = `https://api.cleardues.site`
   (until DNS is live: `https://cleardues-api.onrender.com`). This is baked
   in at build time — changing it later means clicking **Redeploy**.
   Optional observability vars (`VITE_POSTHOG_KEY`, `VITE_SENTRY_DSN`) are
   set up in §6.5 — the app runs fine without them.
4. **Deploy.** You get a live `https://cleardues-xxx.vercel.app` URL.
   [vercel.json](./frontend/vercel.json) rides along automatically: SPA
   deep-links, security headers, and asset caching are already configured.
5. Quick test: open the URL, hard-refresh on a sub-route (no 404 = the SPA
   rewrite works).

## §4 Domain — cleardues.site (~10 minutes + DNS wait)

At your registrar's DNS panel, create:

| Host | Type | Value | Points at |
|------|------|-------|-----------|
| `@` (apex) | A | the IP Vercel shows you (76.76.21.21) | Vercel — frontend |
| `www` | CNAME | `cname.vercel-dns.com` (copy exact value from Vercel) | Vercel |
| `api` | CNAME | `cleardues-api.onrender.com` (copy exact from Render) | Render — API |

Then:
1. Vercel → project → Settings → **Domains** → add `cleardues.site` (accept
   its offer to add `www` too). Vercel shows the exact records it wants —
   trust its panel over this table if they differ.
2. Render → service → Settings → **Custom Domains** → add
   `api.cleardues.site`. (Render is IPv4 — delete any AAAA records for these
   hosts if your registrar created them.)
3. Both platforms issue TLS certificates automatically once DNS propagates
   (minutes to a few hours).
4. Update the three URL env vars to the real domain — Vercel: `VITE_API_URL`
   → redeploy; Render: `FRONTEND_HOST`, `BACKEND_CORS_ORIGINS`,
   `OAUTH_REDIRECT_BASE_URL` → it redeploys itself.

## §5 Google login (required for the first login) — ~10 minutes

Magic-link email needs an SMTP provider you haven't set up yet, so Google
OAuth is your first working login path:

1. [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
   → Create Credentials → **OAuth client ID** → Web application.
2. Authorized redirect URI — exactly:
   `https://api.cleardues.site/api/v1/auth/oauth/google/callback`
   (add the `https://cleardues-api.onrender.com/...` variant too while DNS
   isn't live).
3. Copy the client ID + secret into Render's environment variables.
4. Later, for magic links: add `SMTP_HOST/SMTP_USER/SMTP_PASSWORD/
   EMAILS_FROM_EMAIL` env vars on Render (Resend/Mailgun/SES all have free
   tiers) — no code change needed.

## §6 Backups (do this before inviting anyone) — ~5 minutes

Neon's free plan only keeps a ~6-hour restore history — the nightly
[db-backup workflow](./.github/workflows/db-backup.yml) is your real backup.

1. GitHub repo → Settings → Secrets and variables → Actions → **New secret**:
   `NEON_DIRECT_URL` = the full direct connection string from §1.
2. Actions tab → **DB backup (Neon)** → **Run workflow** (manual test).
   Green run = a `.dump` artifact is attached to the run (kept 30 days).
   The nightly 03:00 UTC schedule runs by itself from `main`.
3. **Restore drill** (run it once now, quarterly after — an untested backup
   is not a backup): download the artifact, then from the repo directory:

   ```bash
   docker compose up -d db   # any Postgres 17 with pg_restore works; local dev db is one
   docker compose cp ./cleardues-YYYYMMDD.dump db:/tmp/restore-test.dump
   docker compose exec db bash -c 'createdb -U postgres restore_test &&
     pg_restore -U postgres -d restore_test /tmp/restore-test.dump &&
     psql -U postgres -d restore_test -c "SELECT count(*) FROM \"user\";" &&
     dropdb -U postgres restore_test'
   ```

   To restore *production*, point pg_restore at Neon instead:
   `pg_restore -d "<NEON_DIRECT_URL>" --clean --if-exists <file>.dump`
   (Neon Pro alternative: restore the branch from its history window.)

## §6.5 Observability — PostHog + Sentry (~15 minutes, WS10.6)

All the instrumentation code already ships in the app and is **env-gated**:
without these variables it is a complete no-op (nothing is even downloaded).
Setting the variables is the entire "integration."

**PostHog (product analytics — frontend only):**

1. [posthog.com](https://posthog.com) → sign up (free tier: 1M events/mo) →
   create project **ClearDues** → copy the **Project API key** (`phc_…`).
2. Vercel → project → Settings → Environment Variables:
   - `VITE_POSTHOG_KEY` = the `phc_…` key
   - `VITE_POSTHOG_HOST` = only if your project is NOT on US Cloud
     (EU: `https://eu.i.posthog.com`; unset defaults to US)
3. **Redeploy** (build-time vars, same rule as `VITE_API_URL`).
4. In PostHog, build the saved views the spec defines — funnel + dashboards
   are step-by-step in
   [analytics-spec.md](./_bmad-output/planning-artifacts/analytics-spec.md) §5.

**Sentry (error monitoring — frontend + backend):**

1. [sentry.io](https://sentry.io) → sign up (free tier) → create TWO
   projects: one **React** (`cleardues-frontend`), one **FastAPI**
   (`cleardues-api`). Each has its own DSN — don't share one.
2. Vercel env var: `VITE_SENTRY_DSN` = the React project's DSN → Redeploy.
3. Render env var: `SENTRY_DSN` = the FastAPI project's DSN (the blueprint
   already has the empty slot) → it redeploys itself. The backend only
   sends events when `ENVIRONMENT` ≠ `local` (it's `staging` on Render).
4. Sanity check: Sentry → both projects → trigger any error (e.g. visit a
   malformed group URL) and confirm an event arrives tagged with the
   right `environment`.

Privacy posture (already enforced in code — nothing to configure): analytics
identifies users by opaque UUID only, no email/name; autocapture and session
replay are OFF; invite/verify tokens and OAuth codes are scrubbed from every
URL before events leave the browser; Sentry runs with `send_default_pii=False`
on both sides.

## §7 Verify the whole thing

- [ ] `https://api.cleardues.site/api/v1/utils/health-check/` → `true`
- [ ] `https://cleardues.site` loads; hard-refresh on a sub-route → no 404
- [ ] Log in with Google → dashboard renders
- [ ] Create a group + expense → appears in the ledger (this proves
      Neon + migrations + CORS end-to-end)
- [ ] Backup workflow ran green; restore drill done once
- [ ] WS10.6 funnel proof (needs §6.5 done): from a logged-out browser,
      open an invite link → join via Google → confirm one expense. In
      PostHog, Activity shows `group.invite.viewed` → `auth.user.logged_in`
      → `group.invite.joined` → `expense.expense.confirmed` for that person.
- [ ] Free uptime monitor (uptimerobot.com) pinging the health-check URL and
      `https://cleardues.site` — the monitor, not you, should be the first to
      know it's down. (Bonus: pinging keeps the Render instance warm.)

## §8 When (and only when) to start paying

| Trigger | Upgrade | Cost |
|---|---|---|
| Real beta users hit 1-min cold starts | Render Starter | $7/mo |
| Real money flows through the app | Vercel Pro **or** move SPA to Cloudflare Pages | $20/mo or $0 |
| Data > 0.5 GB or you want >6h point-in-time restore | Neon Launch | ~$19/mo |
| You want backups off GitHub artifacts | rclone the dump to Cloudflare R2 (10 GB free) | $0 |

## Troubleshooting first deploys

| Symptom | Cause / fix |
|---|---|
| Render build fails on `uv sync` | `uv.lock` out of sync — run CI first; it catches this (`uv lock --check`) |
| API works, browser console shows CORS errors | `BACKEND_CORS_ORIGINS` doesn't contain the exact origin shown in the error (scheme + host, no trailing slash) |
| `password authentication failed` in Render logs | Neon password pasted with whitespace, or you used the pooled host — use the direct host, no `-pooler` |
| First request after idle takes ~1 min | Render free-tier cold start (§8), not a bug |
| 404 when refreshing a sub-route on Vercel | `vercel.json` rewrite missing — confirm Root Directory is `frontend` so the file is picked up |
| Google login redirects to an error | Redirect URI in the Google console must match `OAUTH_REDIRECT_BASE_URL` + `/api/v1/auth/oauth/google/callback` **exactly** |
| `pg_dump: server version mismatch` in backup action | Neon project wasn't created as Postgres 17 (§1) — recreate or bump the client in the workflow |
