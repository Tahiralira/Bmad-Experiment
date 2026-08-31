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

## Status — what is already live

**Verified 2026-08-05.** The stack below is deployed and serving; the sections
that follow are the runbook for how it got there (and how to rebuild it), not a
to-do list. Only §6.5 is outstanding.

| Section | State | Evidence |
|---|---|---|
| §1 Neon | ✅ live | nightly backup workflow green since 2026-08-02 |
| §2 Render | ✅ live | `api.cleardues.site/api/v1/utils/health-check/` → `200 true` |
| §3 Vercel | ✅ live | `cleardues.site` serves the SPA, no console errors |
| §4 Domain + DNS | ✅ live | apex + `www` → Vercel, `api` → Render, TLS issued on all three |
| §5 Google OAuth | ✅ live | `/auth/oauth/google/login` → 302 to Google with the correct `redirect_uri` |
| §6 Backups | ✅ live | `NEON_DIRECT_URL` set; 4 consecutive green runs |
| **§6.5 Observability** | ❌ **not set up** | live bundle contains no `phc_` key and no Sentry DSN — analytics and error reporting are collecting **nothing** |

§6.5 is three environment variables and two redeploys. Until it's done, all the
WS10.6 instrumentation ships as a no-op, exactly as designed when unset.

---

## §0 Prerequisites (one-time)

1. Accounts (all free, sign up with your GitHub account so repo access is
   one click): [neon.com](https://neon.com), [render.com](https://render.com),
   [vercel.com](https://vercel.com).
2. **Get this code onto `main`.** Render/Vercel default to deploying the
   `main` branch, and GitHub only runs *scheduled* workflows (our nightly DB
   backup) from the default branch. **Already done** — every work session
   through WS10.6 has landed on `main` via pull request. Keep it that way: land
   each `wsN/*` branch with a PR so CI gates the merge, and Render/Vercel pick
   up the deploy automatically.
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
Setting the variables is the entire "integration." The frontend vars are
documented in [frontend/.env.example](./frontend/.env.example); the backend's
`SENTRY_DSN` is in the root [.env.example](./.env.example).

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

## §6.6 Nudge engine — scheduler, push, email (~15 minutes, WS12)

The nudge engine is what the product is *for*, and it ships **switched off**:
with none of the values below set, the sweep endpoint 404s, no reminder is
ever sent, and nothing breaks. Turn it on in three independent steps — each
works without the others.

### a. The scheduler (required — nothing sends without it)

Render's free plan has **no background worker and no cron job**, so the
scheduler lives in GitHub Actions and calls the API over HTTP.

1. Render → your API service → Environment. `NUDGE_CRON_SECRET` was
   auto-generated by the blueprint; **copy its value**.
2. Repo → Settings → Secrets and variables → Actions → New repository secret:
   - `NUDGE_CRON_SECRET` = the value you just copied
   - `API_BASE_URL` = `https://api.cleardues.site` (no trailing slash)
3. The workflow (`.github/workflows/nudge-sweep.yml`) runs hourly — but only
   from the **default branch**, so it must be merged to `main` to fire.
4. Test it now: Actions → "Nudge sweep" → Run workflow → tick **dry_run**.
   The run summary prints what *would* be sent without sending or recording
   anything. Safe to run against production at any time.

Hourly is the *pickup* interval, not the nudge cadence. How often any one
person hears from ClearDues is set by `NUDGE_COOLDOWN_HOURS` (72h) and their
own quiet hours.

### b. Web push (recommended — the primary channel)

No third-party service and no cost: payloads go to the browser vendor's own
push endpoint, encrypted with the recipient's keys.

1. Generate a VAPID keypair (needs the stack up locally):

```bash
docker compose exec backend python -c "from py_vapid import Vapid01; import base64; from cryptography.hazmat.primitives import serialization as s; v=Vapid01(); v.generate_keys(); print('PUBLIC :', base64.urlsafe_b64encode(v.public_key.public_bytes(encoding=s.Encoding.X962, format=s.PublicFormat.UncompressedPoint)).decode().rstrip('=')); print('PRIVATE:', base64.urlsafe_b64encode(v.private_key.private_bytes(encoding=s.Encoding.DER, format=s.PrivateFormat.PKCS8, encryption_algorithm=s.NoEncryption())).decode().rstrip('='))"
```

2. Render → Environment → set `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY` to
   the two printed values. **Keep the private key** — rotating it silently
   invalidates every existing subscription and every user has to re-grant
   notification permission.
3. That's it. The client fetches the public key, and only then does it ever
   offer the permission prompt — with no key set it never asks, because a
   browser grants that prompt once.

A PEM-format private key also works (the server converts it), but the
base64url form above is what the generator prints and what the `web-push`
npm CLI emits.

### c. Email fallback (optional — but it is the iOS story)

Until SMTP is configured, email reminders record as `SKIPPED` rather than
failing, and users whose push is denied or unavailable get **nothing**. On
iPhone, push requires the PWA to be added to the Home Screen first — so
email is what reaches the rest.

1. Create a free sending account (Resend, Mailgun, and SES all have free
   tiers) and verify `cleardues.site` as a sending domain.
2. Render → Environment: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`,
   `EMAILS_FROM_EMAIL` (e.g. `reminders@cleardues.site`).

No redeploy of code is needed — the delivery path is already there and
switches on when the values appear. This is also what finally turns on
magic-link sign-in (§5's deferred item).

### d. Reading the kill switch (WS13)

The same `NUDGE_CRON_SECRET` also opens a read-only metrics endpoint. It
exists because the PRD's stop signal — mute rate — cannot be computed in
PostHog: the browser fires `nudge.notification.muted` (the numerator), but
sends happen server-side in the sweep, so no browser ever witnesses one.

```bash
curl -s -H "X-Nudge-Secret: $NUDGE_CRON_SECRET"   "https://api.cleardues.site/api/v1/notifications/internal/nudge-metrics?window_days=7" | jq
```

`mute_rate` is muted people ÷ people actually **reached**, and is `null`
rather than `0.0` before anyone has been nudged — "nobody minds" and "nobody
has been asked yet" must not look the same on the one number you would halt
the product on. How to read the rest of it: [beta-launch.md §4](./beta-launch.md).

### Turning it all off

Unset `NUDGE_CRON_SECRET` on Render. The endpoint 404s immediately, the
scheduler workflow becomes a no-op that logs a warning, and the metrics
endpoint 404s with it. Nothing is deleted and no user preference changes —
flipping it back on resumes exactly where it left off.

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
- [ ] WS12 nudge proof (needs §6.6a): Actions → "Nudge sweep" → Run workflow
      with **dry_run** ticked → run summary shows a JSON body with
      `relationships_examined`. Then, with push configured (§6.6b), grant
      notification permission on a real device, leave a balance for a day,
      and confirm exactly ONE reminder arrives — not one per expense.
- [ ] WS13 escalation proof: leave that same balance unsettled for three more
      days. The SECOND reminder must read differently from the first (it is
      written from the creditor's side — "… covered this 4 days ago and is
      still out of pocket"). Then settle it: the creditor gets a "settled up
      — you never had to ask" notification, and only if a nudge really went
      out first.
- [ ] WS13 metrics proof (§6.6d): the curl returns JSON with `mute_rate`
      (`null` until someone has been reached) and `sends_by_level`.
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
