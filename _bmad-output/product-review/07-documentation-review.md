# Session 7 — Documentation Review (Part 6)

**Date:** 2026-07-06
**Scope:** README(s), CLAUDE.md, BMAD artifact consistency, API docs, onboarding docs.
**Inputs reviewed:** CLAUDE.md, cleardues/README.md, development.md, deployment.md
(status only — content reviewed in S6), backend/README.md, frontend/README.md,
SECURITY.md, release-notes.md, .env.example, session-context.md, sprint-status.yaml,
\_bmad/bmm/docs/BMAD-USAGE-GUIDE.md, \_bmad/bmm/docs/TRACKING-SETUP-GUIDE.md,
\_bmad-output/BMAD-SETUP-GUIDE.md, generated client (frontend/src/client),
backend/app/main.py (OpenAPI config), git history of doc files.
**Method:** Adversarial. Severity per CLAUDE.md review scoping; every recommendation
states impact and effort. Prior-session facts cross-referenced, not re-derived.

**Overall documentation health: 4 / 10 — with an extreme split.** The AI-facing
documentation (BMAD guides, session-context.md, solution-patterns, story files) is
genuinely good: current, specific, and demonstrably load-bearing. The human-facing
documentation is **effectively nonexistent**: every file a new contributor, beta tester,
or auditor would open — README, development.md, deployment.md, backend/frontend READMEs,
SECURITY.md, release-notes.md — is the **unedited FastAPI full-stack template**, last
touched at Story 1.6 (commit `b9df621`, ~6 months ago). Worse than absent, several docs
are *actively wrong*: CLAUDE.md (auto-loaded into every session with OVERRIDE authority)
misstates the project status by five months and lists a tech stack (Redux, WebSockets,
Redis, Celery) that S3/S4 proved does not exist; backend/README.md teaches the exact
monolithic-models pattern whose violation is the root cause of the S3 Alembic blindness;
and every quality-gate command the docs tell you to run (`pytest`, `npm run typecheck`,
`scripts/test.sh`, Playwright) fails today. In an AI-driven development process, docs
are not an afterthought — they are the process. Half of that process is world-class;
the other half would embarrass the project the moment a second human looks at the repo.

---

## Severity Summary

| # | Severity | Finding | Cross-ref |
|---|----------|---------|-----------|
| C1 | CRITICAL | CLAUDE.md — the only file auto-injected into every AI session, with "OVERRIDE" authority — is materially false: status table 5 months stale (says Epic 2.5 next; reality Epic 5 at 2/3), tech stack lists Redux/WebSockets/Redis-PubSub/Celery (none exist in code), and both documented verification commands fail today | S3, S4 |
| H1 | HIGH | ClearDues has no README anywhere: git repo root has none at all; cleardues/README.md is the unedited template ("Full Stack FastAPI Template", upstream CI badges, template admin screenshots, instructions to clone tiangolo's repo, MIT license for the *template*) with one ClearDues OAuth section grafted on | S6-M4 |
| H2 | HIGH | backend/README.md documents the architecture the project explicitly abandoned (`app/models.py`, `app/crud.py`) and states "Alembic is already configured to import your SQLModel models from ./backend/app/models.py" — the precise assumption that makes autogenerate blind to all feature models (S3). The doc *teaches* the bug | S3 |
| H3 | HIGH | Every documented quality-gate workflow fails in practice: `pytest`/`scripts/test.sh` (suite broken, S3), `npm run typecheck` (17 errors, S4), `npx playwright test` (stale template password-auth specs, S4), "If you use GitHub Actions the tests will run automatically" (all CI dead, S6-C1). Docs describe a quality process that does not exist | S3, S4, S6 |
| M1 | MEDIUM | SECURITY.md routes vulnerability reports to `security@tiangolo.com` (the template author) — a misdirected disclosure channel for a financial-records app; no actual security policy exists | S5 |
| M2 | MEDIUM | Tracking artifacts internally inconsistent: session-context.md says Epic 5 "IN-PROGRESS (1/3)" in Next Up but "2/3" in its own header table; "32 completed, 13 remaining" (actual: 47 total → 15 remaining); "Epic 6-7 BACKLOG 0/18" (actual 0/10 — the 18 was copied from CLAUDE.md's Epic 4-7 row) | — |
| M3 | MEDIUM | frontend/README.md "Generate Client" workflow abandoned since Epic 2: generated client has GroupsService but no expense/settlement services (and still ships template ItemsService/PrivateService/LoginService); Epic 3-5 features hand-roll requests via `@/client/core/request`, a pattern documented nowhere; manual-regen URL is wrong (`localhost/api/v1/openapi.json` vs `:8000`) | S4 |
| M4 | MEDIUM | sprint-status.yaml comment rot undermines its authority: "⚠️ BEFORE PRODUCTION" blockers (incl. "Setup Automated Testing Infrastructure — BLOCKER for Epic 4") still listed as pending while epic-4 is marked done above them; the blocker was never done (S4) and the bypass is recorded nowhere | S4 |
| M5 | MEDIUM | No API or user documentation beyond auto-generated Swagger: /docs is the only API reference, degraded by `dict` returns (per session-context's own lesson #10); zero user-facing docs — notably BYOK Gemini key setup, which FR1 requires and which currently has neither doc nor endpoint | S1, S3 |
| M6 | MEDIUM | release-notes.md is 755 lines of the upstream template's changelog (dependabot bumps, tiangolo PRs) presented as the project's release notes; template `img/` screenshots and copier machinery still committed | S6-M4 |
| L1 | LOW | BMAD doc drift: CLAUDE.md says post-hooks run at "Step 9/5", TRACKING-SETUP-GUIDE.md says Step 11/6; CLAUDE.md contains the Known Issues table twice verbatim; BMAD-USAGE-GUIDE.md invents "Build Measure Analyze Deploy" as the acronym expansion | — |
| L2 | LOW | Small staleness: `.env.example` retains `PROJECT_NAME="Your Project Name"`; sprint-status.yaml duplicates its header block (comments 1–5 + keys 37–41); development.md's `localhost.tiangolo.com` sections; untracked local clutter (`temp.py`, `nul`, `cleardues-old-prd/`, `_bmad-backup/`) | S6-L3 |

---

## CRITICAL

### C1 — CLAUDE.md is materially false in every load-bearing section
**Where:** `CLAUDE.md` (repo root) — auto-loaded into every Claude session with
"IMPORTANT: These instructions OVERRIDE any default behavior."

Three independent falsehoods, each in a section a fresh session acts on:

1. **Status table 5 months stale.** "Epic 2.5: UX Foundation — **NEXT** — 0/7" and
   "Next: Epic 2.5, Story 2.5.1." Epic 2.5 completed 2026-01-20 (retro on file).
   Reality: Epics 1–4 done, Epic 5 at 2/3. The review plan itself had to carry a
   "KNOWN STALE" warning to inoculate reviewers against the project's own top-level doc.
2. **Tech stack fiction.** Lists "Redux Toolkit" (zero Redux code exists — S4),
   "Real-Time: WebSockets + Redis Pub/Sub" and "Worker: Celery + Redis" (zero
   WebSocket/Celery code; `redis` not even a dependency — S3, S6-H2). A session asked
   to "add a Redux slice" or "publish over the WebSocket layer" would hunt for
   infrastructure that was never built.
3. **Commands that fail.** The 🚀 Commands section offers exactly two verification
   commands — `docker compose exec backend pytest -v` (entire suite broken by the
   GroupSettings annotation, S3) and `npm run typecheck && npm run build` (typecheck:
   17 errors, S4). A conscientious session following the docs cannot distinguish "I
   broke it" from "it was already broken."

**Why CRITICAL here:** in this project's AI-driven model, CLAUDE.md is the one document
whose errors propagate into *every* future working session — the documentation
equivalent of S6's dead CI. The mitigation (session-context.md is current) only fires
for BMAD workflows that load it; CLAUDE.md explicitly tells non-BMAD sessions the wrong
facts first.

**Root cause worth fixing, not just the symptom:** CLAUDE.md *duplicates* status that
sprint-status.yaml/session-context.md already own and auto-update. Hand-duplicated
state always rots. The fix is structural: CLAUDE.md should carry zero status of its
own and point at the auto-updated files.

**Fix (impact: correct context for all future sessions; effort: 1–2 h):**
- Replace the status table with one line: "Status lives in
  `_bmad-output/implementation-artifacts/sprint-status.yaml` — always read it."
- Correct the stack section to what exists (FastAPI + SQLModel + PostgreSQL; React +
  TS + Vite + TanStack Router/Query; Docker Compose) and move Redis/Celery/WebSockets
  to a "planned (Epic 6/7) — NOT yet present" note.
- Annotate the two commands with current caveats until S3/S4 fixes land.
- Deduplicate the twice-repeated Known Issues table (also L1).

---

## HIGH

### H1 — The product has no README; the repo has no front door
**Where:** repo root (`Bmad-Experiment/` — no README.md at all);
`cleardues/README.md` (unedited template).

The git repository root contains `CLAUDE.md`, `_bmad/`, `_bmad-output/`, `cleardues/`
— and no README. GitHub's landing page for this project renders nothing. One level
down, `cleardues/README.md` opens with "# Full Stack FastAPI Template," carries the
*upstream template's* CI badges (pointing at `fastapi/full-stack-fastapi-template`
workflows), screenshots of the template's admin dashboard (`img/` still committed),
instructions for cloning tiangolo's repo and syncing with upstream, Copier project
generation, and "The Full Stack FastAPI Template is licensed under the terms of the
MIT license" as the project's license statement. The only ClearDues content in any
README is the OAuth setup section (added at Story 1.6, the last time any of these
files were touched).

Consequences: (a) a beta invite, investor, or contributor who opens the repo learns
nothing — not even the product's name; (b) the badges display *another project's* CI
status, compounding the S6 illusion that CI exists; (c) the license of ClearDues
itself is formally undefined (the MIT statement covers the template); (d) the S2
"Walled Garden" onboarding problem extends to the repository itself.

**Fix (impact: first-impression + onboarding for every human; effort: 2–3 h):**
Write a repo-root README: what ClearDues is (2 paragraphs from the product brief),
honest status ("pre-alpha, not yet deployed"), actual stack, quickstart
(`docker compose up -d` + .env.example), repo layout (`cleardues/` = product,
`_bmad*/` = AI process), link map to BMAD docs. Reduce cleardues/README.md to
dev-setup content; delete upstream badges/screenshots/clone-the-template sections;
add an explicit LICENSE decision.

### H2 — backend/README.md documents the forbidden architecture — and the S3 bug
**Where:** `cleardues/backend/README.md:30` ("Modify or add SQLModel models for data
and SQL tables in `./backend/app/models.py` … CRUD utils in `./backend/app/crud.py`"),
`:136` ("Alembic is already configured to import your SQLModel models from
`./backend/app/models.py`").

Story 1.2 was literally "reorganize to feature-based architecture," and CLAUDE.md
mandates `app/features/{name}` with a strict service layer. The backend README —
the file a new backend developer reads first — instructs the opposite. Line 136 is
the sharpest instance: it asserts Alembic sees your models if they're in
`app/models.py`, which is *exactly why* `alembic/env.py` (importing only
`app.models`) is blind to every feature model — S3's finding, root cause documented
as a feature. A developer following this README would add a model to `app/models.py`
(where autogenerate works!) and re-entrench the split the project spent a story
undoing.

**Fix (impact: prevents onboarding devs from re-introducing the monolith and masking
the migration gap; effort: 1–2 h, bundled with H1's rewrite):** Replace the "General
Workflow" and "Migrations" sections with the feature-based reality: where models
live, the env.py import requirement for *each* feature module (until the S3 fix
centralizes it), router/service/model conventions, and the real test entry point
with its current caveat.

### H3 — Every documented quality gate is a dead end
**Where:** backend/README.md:97 (`bash ./scripts/test.sh`), :102 ("If you use GitHub
Actions the tests will run automatically"), frontend/README.md:125–153 (Playwright
guide), CLAUDE.md Commands, session-context.md Common Commands.

Cross-referencing S3/S4/S6 against what the docs promise:

| Documented workflow | Reality |
|---|---|
| `docker compose exec backend pytest -v` / `scripts/test.sh` | 0 of 193 tests can run (GroupSettings annotation, S3) |
| `npm run typecheck` | fails with 17 errors (S4) |
| `npx playwright test` | 4 specs test template password auth that ClearDues doesn't use (S4) |
| "GitHub Actions will run tests automatically" | all 13 workflows dead (S6-C1) |
| development.md pre-commit (`prek`) guide | hook config itself invalid if run (S6-L2) |

No single doc lies uniquely — the pattern is the finding: the documentation describes
an aspirational quality process, and nothing flags the gap. Anyone (human or AI)
verifying their change "per the docs" hits a wall and must archaeology their way to
the truth, or worse, concludes failures are expected noise and ships anyway — the
exact normalization that let S3/S4 rot accumulate.

**Fix (impact: restores meaning of "I ran the checks"; effort: 30 min now, resolved
properly by S3/S4/S6 fixes):** Until the underlying fixes land, add a single
prominent "⚠️ Current known-broken gates" block to CLAUDE.md and the backend README
listing what fails and the tracking pointer. Delete the GitHub-Actions sentence.
Remove this block when the gates are green — it doubles as the checklist.

---

## MEDIUM

### M1 — SECURITY.md sends vulnerability reports to the template author
**Where:** `cleardues/SECURITY.md:15` — "report it right away by sending an email to:
security@tiangolo.com."

For a product that stores financial records and encrypted API keys, the only security
policy on file directs disclosures to an unrelated third party. If the repo ever goes
public (implied by beta plans), a well-meaning researcher's report goes to tiangolo's
inbox. Given S5's findings, a working disclosure channel will be needed.
**Fix (impact: correct disclosure routing; effort: 15 min):** Replace with a minimal
policy naming the maintainer's contact and a response expectation, or delete the file
until launch (absence is better than misdirection).

### M2 — session-context.md contradicts itself on the project's headline numbers
**Where:** `_bmad-output/session-context.md:17` (header: Epic 5 "2/3"), `:132`
(Next Up: "Epic 5 ← IN-PROGRESS (1/3)"), `:21` ("32 stories completed, 13 remaining"),
`:18` ("Epic 6-7 | BACKLOG | 0/18").

The math: total stories = 6+4+7+8+5+3+5+5+4 = 47; with 32 done, 15 remain (11 if
Epic 8 is excluded — neither equals 13). Epics 6+7 hold 10 stories, not 18 (the 18
was copied from CLAUDE.md's "Epic 4-7" row without adjusting the label). The 1/3 vs
2/3 conflict is two sections updated at different times. Individually trivial; but
this file is the designated "READ THIS FIRST" source of truth, and its post-hook
update process (TRACKING-SETUP-GUIDE's core promise) demonstrably patches one section
while leaving stale numbers in others — the same hand-duplication disease as C1,
inside the automated system meant to prevent it.
**Fix (impact: trustworthy status file + honest signal about hook reliability;
effort: 30 min):** Correct the three numbers; restructure so each fact appears once
(status table only in the header; "Next Up" lists only the next story, no counters).

### M3 — Documented client-generation workflow silently abandoned
**Where:** `cleardues/frontend/README.md:75–102`; `frontend/src/client/sdk.gen.ts`
(services: Auth, Groups, Items, Login, Private, Users, Utils — nothing for expenses,
splits, settlements, audit); `features/{expenses,dashboard,groups}/api/*.ts`
(hand-written wrappers importing `request` from `@/client/core/request`).

The README presents `generate-client.sh` → typed SDK as *the* API-consumption
pattern. That stopped at Epic 2: everything since is hand-rolled on the generated
client's private request core — a reasonable pattern, but documented nowhere, while
the documented pattern would regenerate a client whose template services
(Items/Login/Private) S4 flagged as dead weight. New contributors get to choose
between a doc that's wrong and a convention they must reverse-engineer. The manual
instructions also point to `http://localhost/api/v1/openapi.json` (no port — actual
is `:8000`).
**Fix (impact: one honest API pattern; effort: 1 h doc, or 2–3 h to re-adopt
generation):** Decide the pattern first. Either regenerate (after S3 adds the missing
GET endpoints) and migrate wrappers, or bless the hand-rolled pattern in the README
with a template. Fix the URL either way.

### M4 — sprint-status.yaml's own "BEFORE PRODUCTION" blockers were bypassed silently
**Where:** `sprint-status.yaml:79–96` — Epic 3 block still lists 11 pending
pre-production action items including "Setup Automated Testing Infrastructure (4-6
hours) — **BLOCKER for Epic 4**"; line 113: `epic-4: done`.

The testing infrastructure was never set up (S4: vitest not even installed), yet
Epic 4 and most of Epic 5 shipped past the recorded blocker with no annotation
lifting or deferring it. Some listed items *were* later done (security checklist, MVS
standard — per CLAUDE.md) but the block was never updated, so it's now impossible to
tell from the tracking file which warnings are live. A tracking system whose warnings
can be ignored without trace trains everyone to ignore its warnings.
**Fix (impact: tracking file regains authority; effort: 30 min + process rule):**
Annotate each item done/deferred-with-link/dropped-with-reason. Process rule for the
retro: an epic cannot be marked `done` while an unresolved BLOCKER comment for it
exists in the file.

### M5 — No API docs beyond auto-generated Swagger; zero user-facing docs
**Where:** `backend/app/main.py:21` (OpenAPI enabled — the good part); nothing else.

Swagger at /docs is the only API reference. Acceptable pre-beta, but: several
endpoints return bare `dict` (session-context lesson #10), degrading the schema the
docs consist of; the schema still advertises the whole template surface (items,
private, password login) alongside real endpoints — S4/S5's confusion, now also a
documentation problem since the API's only reference can't distinguish real from
vestigial. And FR1's BYOK requirement — the user must supply a Gemini key — has no
documentation for how a user would do it (consistent with S3: no endpoint exists).
When the S3 fix lands, the doc must land with it or FR1 stays undiscoverable.
**Fix (impact: API reference reflects the real API; effort: piggybacks on S3/S4
fixes + 1–2 h):** Remove template routers from the schema (S4 fix), add
response_models where dict is returned (S3 list), write a BYOK setup section in the
README when the endpoint ships.

### M6 — Template exhaust presented as project history
**Where:** `cleardues/release-notes.md` (755 lines of upstream changelog),
`cleardues/img/` (7 template screenshots incl. `github-social-preview.png`),
`.copier/` + `copier.yml` (S6-M4).

The release-notes file chronicles another project's dependabot bumps as this
project's history; ClearDues' actual releasable history (32 stories, 5 epics) is
recorded only in BMAD artifacts. Harmless until someone reads it — then it's noise
at best, misattribution at worst.
**Fix (impact: repo hygiene; effort: 30 min):** Reset release-notes.md to "##
Unreleased" (or generate a real changelog from the epic retros — 1 h), delete
`img/`, fold into S6-M4's template-machinery cleanup.

---

## LOW

### L1 — Internal BMAD doc drift
CLAUDE.md's hook table says auto-update at "Step 9/5"; TRACKING-SETUP-GUIDE.md says
Step 11 (dev-story) / Step 6 (code-review). CLAUDE.md contains the identical Known
Issues table twice ("Known Issues Quick Reference" + "Known Issues"). BMAD-USAGE-GUIDE
expands BMAD as "Build Measure Analyze Deploy" (upstream: "Breakthrough Method for
Agile AI-Driven Development") — cosmetic, but it's an invented fact in a reference
doc. **Fix: 20 min during the C1 rewrite.**

### L2 — Small staleness inventory
`.env.example` keeps `PROJECT_NAME="Your Project Name"` (surfaces in API title/docs
and email templates); sprint-status.yaml opens with its five header keys duplicated
as comments; development.md's `localhost.tiangolo.com` walkthrough and Traefik/Adminer
URLs describe the template topology (accurate only because the infra is still
template — will silently rot when S6 fixes land); untracked local clutter at repo
root (`temp.py`, `nul`, `cleardues-old-prd/`, `_bmad-backup/`) — not in git, so
hygiene-only. **Fix: 30 min sweep.**

---

## What's genuinely good (credit where due)

- **TRACKING-SETUP-GUIDE.md and BMAD-USAGE-GUIDE.md** are real documentation:
  versioned, structured, with troubleshooting sections and accurate file locations.
- **session-context.md's "Key Learnings" and 19-item "What NOT to Do"** list is the
  best documentation in the repo — specific, earned, and demonstrably reused (its
  lessons match real S3/S4 findings).
- **Story files** (e.g., 5-1, 5-2) carry detailed ACs, security sections, and code-
  review records — better per-change documentation than most human teams produce.
- **.env.example** is maintained (OAuth vars added with setup pointers) — the one
  template file that was properly adopted.

The asymmetry is the diagnosis: docs that BMAD workflows auto-touch stay alive; docs
only a human process would touch have been dead since Story 1.6. MVS checklist item
11 ("Documentation Updated") has been interpreted as "BMAD artifacts updated" for 26
consecutive stories.

---

## Prioritized Recommendations

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Rewrite CLAUDE.md: remove duplicated status (point at sprint-status.yaml), fix stack, caveat broken commands, dedupe Known Issues (C1, L1) | Every future AI session works from true context | 1–2 h |
| 2 | Write repo-root ClearDues README; strip template README to dev-setup; add LICENSE decision (H1) | First human impression; onboarding | 2–3 h |
| 3 | Add "known-broken gates" block until S3/S4 fixes land; delete false CI claims (H3) | Stops normalization of failing checks | 30 min |
| 4 | Rewrite backend/README workflow+migrations sections for feature architecture (H2) | Prevents re-entrenching the S3 Alembic bug | 1–2 h |
| 5 | Fix SECURITY.md contact (M1) | Correct vuln disclosure routing | 15 min |
| 6 | Reconcile session-context.md numbers; de-duplicate facts (M2) | Source-of-truth file becomes trustworthy | 30 min |
| 7 | Annotate sprint-status blocker comments; adopt "no epic done past a live BLOCKER" rule (M4) | Tracking regains authority | 30 min |
| 8 | Decide + document the one API-client pattern (M3) | Ends doc/practice fork | 1 h (doc) |
| 9 | Reset release-notes.md; delete img/; hygiene sweep (M6, L2) | Repo credibility | 1 h |
| 10 | Process fix: make code-review verify human-doc impact explicitly (MVS #11 with teeth) | Stops the rot recurring | 1 h |

**Total: ~1.5 dev-days** to take human-facing docs from "template debris" to "honest
and minimal" — the right target pre-beta. The deeper fixes (API docs quality, BYOK
user docs) are gated on S3/S4 code fixes, not on writing.

---

## Key Facts for Session 8/9 (summary)

- Human-facing docs are unedited FastAPI-template files, untouched since Story 1.6;
  ClearDues has no README, no license decision, no real security policy, no user docs.
- CLAUDE.md (always-loaded) is materially false: 5-months-stale status, phantom
  Redux/Redis/Celery/WebSockets stack, verification commands that fail (C1).
- Docs actively teach the S3 Alembic bug (backend README's app/models.py pattern).
- All documented quality gates fail today; docs claim CI runs tests automatically.
- AI-facing docs (BMAD guides, session-context learnings, story files) are the best
  docs in the repo, but session-context's headline numbers self-contradict (1/3 vs
  2/3; "13 remaining" vs actual 15; "Epic 6-7 0/18" vs actual 0/10) and
  sprint-status's "BLOCKER for Epic 4" comment sits unresolved above `epic-4: done`.
- Generated API client is frozen at Epic 2; Epics 3–5 hand-roll requests, pattern
  undocumented. Swagger is the only API reference and includes template endpoints.
- Root cause: documentation only survives here if a BMAD hook touches it; MVS item
  11 has never been enforced for human docs.
- Documentation health score: 4/10 (AI-facing ~7/10, human-facing ~1.5/10).
