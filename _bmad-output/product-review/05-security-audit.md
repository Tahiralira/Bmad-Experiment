# Session 5 — Security Audit (Part 4)

**Date:** 2026-07-06
**Scope:** Auth flows (magic link, JWT, OAuth), per-endpoint authorization, API-key
encryption at rest, rate limiting (NFR5), CSRF/XSS, session management, dependency
audit, secrets in docker-compose.
**Method:** Adversarial. Findings are severity-tagged per CLAUDE.md scoping. Each carries
impact + effort. Prior-session facts are cross-referenced, not re-derived.

**Overall security posture: 3.5 / 10.** The magic-link implementation is genuinely
well-built (hashed tokens, single-use, rate-limited, enumeration-safe). Almost everything
around it is not: one secret key is reused for three different cryptographic purposes and
defaults to a random-per-process value; the OAuth flow leaks a 30-day bearer token through
URL/query strings and access logs; there is no rate limiting on password login or brute-
forceable endpoints; a public **Adminer database console** is wired into the production
compose; the dependency lockfile does not even contain the OAuth and encryption libraries;
and the FastAPI template's parallel password-auth surface (with email enumeration) is still
live in a product that is supposed to be passwordless.

---

## Severity Summary

| # | Severity | Finding | Cross-ref |
|---|----------|---------|-----------|
| C1 | CRITICAL | One `SECRET_KEY` reused for JWT + Fernet + session cookie; random-per-process default bricks stored API keys and all sessions on restart; NFR4 "AES-256" false | S3 |
| C2 | CRITICAL | `uv.lock` omits `authlib`, `cryptography`, `google-genai` — the OAuth/JWT/encryption libs float unpinned in prod builds | S3 |
| H1 | HIGH | 30-day JWT delivered via OAuth redirect **URL query param** → access logs, history, Referer; stored in `localStorage`; no revocation | S4 |
| H2 | HIGH | No rate limiting on password login, OAuth, or AI-parse; NFR5 only partly met (magic-link only, per-email, bypassable) | — |
| H3 | HIGH | Public **Adminer** DB-admin console published in production compose (`adminer.${DOMAIN}`) | S6 |
| H4 | HIGH | `starlette 0.38.6` → CVE-2024-47874 (unbounded multipart → DoS), fixed in 0.40.0 | — |
| H5 | HIGH | Parallel password-auth surface still live (login/recover/reset/signup/private); email enumeration + reusable 48h reset tokens | S4 |
| M1 | MEDIUM | No security headers anywhere (no CSP/HSTS/X-Frame-Options/X-Content-Type-Options) | — |
| M2 | MEDIUM | OAuth callback reflects raw `str(e)` into redirect URL → info disclosure into URL + logs | — |
| M3 | MEDIUM | Google OIDC link path never checks `email_verified`; silent auto-link to existing account | — |
| M4 | MEDIUM | `accept_invite` is a state-changing GET; invites multi-use, 30-day, non-revocable | S4 |
| M5 | MEDIUM | `delete_user_me` cascade-deletes shared data / 500s on audit FK (availability + integrity) | S3 |
| M6 | MEDIUM | `allow_credentials=True` on CORS is unnecessary (Bearer, not cookies) — foot-gun | — |
| M7 | MEDIUM | `sentry-sdk 1.45.1` (EOL 1.x) may capture tokens in request data unless scrubbed | — |
| L1 | LOW | `update_expense_split` takes untyped `dict = Body(...)` — no schema validation | S3/S4 |
| L2 | LOW | `send_email` logs full SMTP response; new-account email sends plaintext password | — |
| L3 | LOW | Env-bootstrapped superuser is password-authable with admin powers | — |

---

## CRITICAL

### C1 — One `SECRET_KEY` does triple duty and defaults to random-per-process
**Where:** `app/core/security.py:35-52`, `app/core/config.py:34`, `app/main.py:36-41`

`SECRET_KEY` is used for **three** unrelated cryptographic purposes:
1. Signing every JWT (`security.py:20`, HS256).
2. Deriving the **Fernet key** that encrypts users' Gemini API keys
   (`security.py:47-48`: `SECRET_KEY.encode()[:32].ljust(32, b"0")`).
3. Signing the OAuth **session cookie** (`main.py:38`, `SessionMiddleware`).

Three compounding problems:
- **Random-per-process default** (`config.py:34`: `SECRET_KEY = secrets.token_urlsafe(32)`).
  If `.env` is ever missing the key, every process/restart gets a new one →
  **all encrypted API keys become permanently undecryptable** (`InvalidToken`) and
  every JWT/session is invalidated. This is silent data loss. (Confirmed in S3.)
- **Weak key derivation.** Truncating/padding the raw secret to 32 bytes and base64-ing
  it is not a KDF. A short secret is padded with literal `0` bytes (low entropy); there
  is no salt and no domain separation between the JWT and encryption uses of the same key.
- **False NFR4 claim.** Model field says "AES-256" (`auth/models.py:75`) and the function
  docstring says "NFR4 Compliance - AES-256", but Fernet is **AES-128-CBC**. The compliance
  claim is untrue.

**Impact:** Data loss (bricked API keys on any rotation/restart), cross-context key reuse
(a JWT-signing leak also compromises API-key confidentiality and session integrity),
and a documented-but-false crypto claim.
**Effort:** Medium. Introduce a dedicated `API_KEY_ENCRYPTION_KEY` (real 32-byte Fernet
key, generated once, stored in secrets manager), keep `SECRET_KEY` for JWT only, and give
`SessionMiddleware` its own key. Fix the model description. ~0.5 day + a data-migration
plan for any keys already encrypted under the derived key.

### C2 — Lockfile omits the OAuth, JWT, and encryption libraries
**Where:** `backend/pyproject.toml:22-28` vs `backend/uv.lock`

`pyproject.toml` declares `authlib>=1.3.0`, `cryptography>=41.0.0`, and `google-genai>=1.0.0`,
but **none of these three appear in `uv.lock`** (verified: 75 locked packages, none named
authlib/cryptography/google-genai). The lockfile is out of sync with the manifest — it was
never regenerated after the AI/OAuth stories were added.

Consequences:
- Production `docker build` resolves these **unpinned** (`>=`), so the libraries doing
  OAuth token exchange, id-token handling, and Fernet encryption float to whatever is
  latest at build time — non-reproducible builds for exactly the security-critical deps.
- `authlib` can legitimately resolve to `1.3.0`, which is vulnerable to
  **CVE-2024-37568** (JWS/JWT `alg` confusion, fixed in 1.3.1). Authlib parses Google's
  OIDC `id_token`, so this path is reachable.
- No lock = no `uv` / `pip-audit` signal for these deps.

**Impact:** Supply-chain and reproducibility risk on the most sensitive libraries in the app.
**Effort:** Low. `uv lock` to regenerate, pin authlib `>=1.3.1`, `cryptography>=43`, commit,
and add a CI check that the lock is in sync. ~1 hour.

---

## HIGH

### H1 — 30-day JWT delivered in the OAuth redirect URL, stored in `localStorage`
**Where:** `auth/router.py:734` (`?token={access_token}`), `frontend/src/routes/auth.callback.tsx:42`,
`frontend/src/main.tsx:17-18`, `docker-compose.override.yml:28` (`--accesslog`)

The OAuth callback redirects the browser to
`{FRONTEND_HOST}/auth/callback?token={access_token}` with a **30-day** JWT
(`LOGIN_TOKEN_EXPIRE_DAYS`, `router.py:728`). Tokens in query strings are the textbook
mistake: they land in the Traefik **access log** (access logging is explicitly enabled),
in browser/proxy history, and in any `Referer` header the callback page emits. The token
is then persisted in `localStorage` (`main.tsx:18`, `auth.callback.tsx:42`), which is
readable by any XSS on the origin. There is **no server-side revocation/blacklist** — a
leaked token is valid for the full 30 days.

**Impact:** A single log-file read or XSS = 30-day account takeover, no way to revoke.
**Effort:** Medium. Deliver the token via a short-lived one-time code exchanged at a POST
endpoint, or set an `HttpOnly; Secure; SameSite` cookie server-side instead of a URL param;
shorten lifetime and add a revocation/`jti` list. ~1 day.

### H2 — No rate limiting on brute-forceable endpoints (NFR5 only partly met)
**Where:** `auth/router.py:69` (`/login/access-token`), `:613-640` (OAuth), `ai/parser_router.py:23`;
no `slowapi`/limiter dependency anywhere (verified).

NFR5 (rate limiting) is implemented **only** for magic-link requests, and even that is a
per-email DB counter (`auth/service.py:89-100`, 3/hour): an attacker rotates the `email`
field to defeat it, and there is no IP-based throttle. Meanwhile:
- `/login/access-token` (the still-live password login) has **no** throttle → unlimited
  password brute-forcing against `FIRST_SUPERUSER` and any password user.
- OAuth login/callback and the AI `/expenses/parse` endpoint have none.
- No global middleware limiter exists.

**Impact:** Credential brute force, and cost/quota abuse on the AI endpoint.
**Effort:** Low-Medium. Add `slowapi` (or Traefik-level rate-limit middleware) with per-IP
limits on auth endpoints and a global default. ~0.5 day.

### H3 — Public Adminer DB console in the production compose
**Where:** `docker-compose.yml:22-43`

The production stack publishes **Adminer** (a full database-administration web UI) at
`adminer.${DOMAIN}` with `restart: always`, behind Traefik TLS but otherwise reachable by
anyone on the internet who finds the subdomain. Its only protection is the Postgres login
form — the same credentials that, per config, must merely not equal `"changethis"`. There
is no IP allow-list, no auth proxy, no reason for it to be internet-facing in prod.

**Impact:** Internet-exposed direct-to-database admin surface; credential-stuffing or a
weak `POSTGRES_PASSWORD` yields full DB read/write.
**Effort:** Low. Remove `adminer` from the production compose (keep it only in
`docker-compose.override.yml` for local), or bind it to an internal network / VPN. ~1 hour.
(Flagged here for security; deployment mechanics belong to Session 6.)

### H4 — Vulnerable `starlette 0.38.6` (multipart DoS)
**Where:** `backend/uv.lock` (`starlette==0.38.6`)

`starlette < 0.40.0` is affected by **CVE-2024-47874**: unbounded multipart/form-data field
parsing enables memory-exhaustion DoS. The app processes multipart via
`OAuth2PasswordRequestForm` + `python-multipart` on the login endpoint, so the vulnerable
path is exposed and (per H2) unthrottled.

**Impact:** Remote DoS with a crafted multipart body.
**Effort:** Low. Bump FastAPI/Starlette (FastAPI `>=0.115.x` pulls `starlette>=0.40`) and
re-lock. ~1 hour. (`sentry-sdk 1.45.1` and unpinned deps in C2 want the same audit pass —
add `pip-audit`/`uv` to CI.)

### H5 — Parallel password-auth surface still live in a "passwordless" product
**Where:** `auth/router.py:69-143` (login/recover/reset), `:306-319` (signup),
`api/routes/private.py:23` (`/private/users/`), `api/routes/utils.py` (superuser email test)

The FastAPI template's password stack was never removed (S4 flagged the template cruft; this
is its security dimension):
- `/password-recovery/{email}` and `/reset-password/` return **404 "user does not exist"**
  for unknown emails (`router.py:107-110, 133-136`) → **email enumeration**, unlike the
  enumeration-safe magic-link endpoints.
- Reset tokens are JWTs valid for **48h and reusable** (not single-use, no DB invalidation;
  `utils.py:139-159`) — weaker than the magic-link design right next to it.
- `reset_password` sets `hashed_password` on any account, including OAuth/magic-link-only
  users that hold a random placeholder password — it can **convert a passwordless account
  into a password-authable one**.
- `/users/signup` and `/login/access-token` keep a full password login path alive.
- `/private/users/` creates arbitrary users with **no authentication**, gated only by
  `ENVIRONMENT == "local"` (`api/main.py:24-25`) — one misconfigured env var in prod =
  unauthenticated user creation.

**Impact:** Enumeration, a second weaker auth path, and an env-flag-gated unauthenticated
user-creation endpoint, all contradicting the product's passwordless model.
**Effort:** Medium. Delete the password/reset/signup/private routes (and their models), or
explicitly gate them off. Aligns with the S4 template-removal recommendation. ~1 day.

---

## MEDIUM

### M1 — No security headers (CSP / HSTS / X-Frame-Options / X-Content-Type-Options)
**Where:** `app/main.py` (no header middleware), `frontend/nginx.conf` (none set — verified)

Nothing sets a Content-Security-Policy, HSTS, `X-Frame-Options`, or `X-Content-Type-Options`
on either the API or the static frontend. Given H1 (JWT in `localStorage`), the absence of a
CSP materially raises the blast radius of any XSS to full token theft, and the missing
`X-Frame-Options`/frame-ancestors allows clickjacking of the app UI.
**Impact:** Amplifies XSS to account takeover; enables clickjacking.
**Effort:** Low. Add a headers middleware (or nginx `add_header`) + HSTS at Traefik. ~2-3h.

### M2 — OAuth callback reflects raw exception text into the redirect URL
**Where:** `auth/router.py:669` (`&message={str(e)}`)

On token-exchange failure the backend redirects to
`.../auth/callback?error=oauth_failed&message={str(e)}`, placing the raw exception string
into a URL that is logged (Traefik) and kept in history. Provider/library exceptions can
carry internal detail.
**Impact:** Information disclosure into logs/history.
**Effort:** Low. Log server-side; send a generic `error` code only. ~30 min.

### M3 — Google OIDC link path doesn't verify `email_verified`
**Where:** `auth/router.py:677-687`, `auth/service.py:190-228`

For Google, the code trusts `sub`/`email` from `userinfo` but never checks the
`email_verified` claim before `find_or_create_oauth_user` **auto-links** the OAuth identity
to any pre-existing account with a matching email (`service.py:217-228`). GitHub's path does
check `primary and verified` (`router.py:700-704`); Google's does not. If a provider ever
returns an unverified-but-matching email, an attacker could silently attach their OAuth login
to a victim's existing account.
**Impact:** Potential account linking/takeover via unverified email.
**Effort:** Low. Reject the login if `user_info.get("email_verified") is not True` for Google;
require an explicit confirmation step before linking to an existing local account. ~2-3h.

### M4 — `accept_invite` is a state-changing GET; invites are multi-use and non-revocable
**Where:** `groups/router.py:143` (`GET /expense-groups/invite/{token}`),
`groups/models.py:162-194`, `groups/service.py:190-219`

Joining a group is a **GET** that mutates membership. Invites are valid 30 days, usable an
**unlimited** number of times, with no revocation endpoint and no per-invite usage cap. A
leaked/forwarded link lets anyone join until expiry; link prefetchers/scanners can trigger
the join. (Classic cookie-CSRF is mitigated because the API uses a Bearer header, not
cookies — see the CORS note in M6 — but the GET-mutates-state and non-revocability problems
stand.) S4 flagged this from the routing side.
**Impact:** Uncontrolled group access from a single leaked link; no way to revoke.
**Effort:** Medium. Make acceptance a POST, add revoke + single-use/expiry-on-use options. ~0.5 day.

### M5 — `delete_user_me` cascade / audit-FK failure
**Where:** `auth/router.py:292-303`, User relationships in `auth/models.py:79-80`

`DELETE /users/me` calls `session.delete(current_user)`. Per S3 this either 500s on the
audit-log FK or cascade-deletes expense/split rows the user is attached to, corrupting
balances for **other** members of shared groups. This is a data-integrity/availability issue
reachable by any authenticated user against shared data.
**Impact:** A user can destroy or corrupt other members' financial records by deleting self.
**Effort:** Medium. Soft-delete/anonymize instead of hard delete; block deletion while the
user has unsettled shared splits. ~0.5-1 day. (Root cause detailed in S3.)

### M6 — `allow_credentials=True` on CORS is unnecessary and a foot-gun
**Where:** `app/main.py:27-33`

The API authenticates via `Authorization: Bearer` from `localStorage`
(`frontend/src/client/core/request.ts:144`, `main.tsx:18`) — it does **not** use cookies for
API auth. `allow_credentials=True` is therefore unneeded, and it is the specific setting that
turns a future wildcard/misconfigured origin into a credential-leaking CORS hole. Origins are
currently explicit (good), so this is latent, not live.
**Impact:** Latent CORS misconfiguration risk.
**Effort:** Trivial. Set `allow_credentials=False` unless/until cookie auth is adopted. ~15 min.

### M7 — `sentry-sdk 1.45.1` (EOL 1.x) may capture tokens
**Where:** `backend/uv.lock` (`sentry-sdk==1.45.1`), `app/main.py:16-17`

The 1.x line is end-of-life. Sentry is initialized in staging/prod and, by default, can
capture request headers/bodies — which here include Bearer tokens and (via H1) tokens in
URLs. Without explicit scrubbing this ships secrets to a third party.
**Impact:** Secret leakage to Sentry; running EOL dependency.
**Effort:** Low. Upgrade to `sentry-sdk 2.x`, enable `send_default_pii=False` and URL/header
scrubbing. ~2-3h.

---

## LOW

- **L1 — Untyped split payload.** `update_expense_split` takes `split_data: dict = Body(...)`
  (`expenses/router.py:129`), bypassing Pydantic validation and hand-parsing everything.
  No injection (SQLModel params), but weak input-validation posture and easy to get wrong.
  Effort: Medium (define request schemas). (S3/S4.)
- **L2 — Logging/email hygiene.** `send_email` logs the full SMTP response at INFO
  (`utils.py:55`); `generate_new_account_email` emails the user's **plaintext password**
  (`utils.py:85-100`, template path). Effort: Low.
- **L3 — Env-bootstrapped superuser.** `FIRST_SUPERUSER`/`_PASSWORD` create a password-authable
  admin with `/users/` (and local `/private/`) powers; config only refuses the literal
  `"changethis"`, not weak passwords. Effort: Low (enforce strength / prefer SSO for admin).

---

## What is actually done well (verified, not assumed)

- **Magic-link auth is solid:** tokens are SHA-256-hashed at rest (`auth/service.py:30-32,
  113-120`), single-use (`used_at`), 15-min expiry, per-email rate-limited, and every
  request/login endpoint returns an **enumeration-safe generic message**
  (`router.py:410-442, 519-556`).
- **Settlement authorization is correct:** confirm/reject verify
  `current_user_id == expense.payer_id` before mutating (`expenses/service.py:967-969`), and
  most group/expense endpoints check membership/ownership explicitly.
- **No SQL injection observed:** all queries go through SQLModel/SQLAlchemy parameterization.
- **Secrets not committed:** `.env` is gitignored and untracked; the local `.env` has real
  (non-`changethis`) `SECRET_KEY`/passwords; `config.py` refuses default secrets outside
  `local`.
- **Bearer-in-header, not cookies:** classic cookie-CSRF is largely N/A for the API.

**Note for downstream sessions:** the swapped-args membership check at
`ai/parser_router.py:67` (S3) **fails closed** here — it denies all AI parsing rather than
opening a hole — so treat it as a correctness bug (S3), not an authz bypass.

---

## Key Facts Established in Session 5 (do not re-verify)

- One `SECRET_KEY` signs JWTs, derives the Fernet API-key encryption key, AND signs the
  OAuth session cookie; it defaults to random-per-process. Fernet = AES-128, so the
  "AES-256" NFR4 claim is false. (C1, extends S3.)
- `uv.lock` does **not** contain `authlib`, `cryptography`, or `google-genai` though
  pyproject declares them — the OAuth/JWT/encryption libs are unpinned in prod builds. (C2.)
- OAuth returns a **30-day** JWT in a **URL query param**; frontend stores it in
  `localStorage`; Traefik access logging is on; there is no token revocation. (H1.)
- Rate limiting exists **only** for magic-link (per-email, bypassable); password login,
  OAuth, and AI-parse are unthrottled; no `slowapi`/global limiter. NFR5 only partly met. (H2.)
- Production compose (`docker-compose.yml:22-43`) publishes a public **Adminer** DB console. (H3.)
- Pinned `starlette 0.38.6` is vulnerable to CVE-2024-47874 (multipart DoS); `sentry-sdk
  1.45.1` is EOL. (H4, M7.)
- Template password stack is still live and **enumerable**: `/password-recovery/{email}`
  and `/reset-password/` 404 on unknown emails; reset JWTs are reusable for 48h; `/private/
  users/` creates users unauthenticated when `ENVIRONMENT=local`. (H5.)
- No security headers on API or nginx (no CSP/HSTS/X-Frame-Options). (M1.)
- Google OIDC linking ignores `email_verified`; `accept_invite` is a state-changing,
  non-revocable, multi-use GET. (M3, M4.)
- Security posture score: 3.5/10. Full details in this file.
