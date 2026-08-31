# Private Beta Runbook (WS13)

**Status: NOT LAUNCHED.** Every gate below is either done in code or waiting
on an owner action; nothing here has been performed against a live system,
because as of 2026-08-31 **nothing is deployed** — the WS9.5 owner actions
(Neon, Render, Vercel, domain, Google login) are still outstanding. This
file is the checklist that turns a deployed app into a running beta, plus
the honest numbers behind the claims it makes.

Written for one person doing this alone in an evening. It assumes
[deployment.md](./deployment.md) §0–§7 are complete.

---

## Why 5–10 groups and not 50

The point of this beta is **not** load. It is the only question the product
has never been able to answer: *does an agent that asks for your money on
your behalf feel like help or like a bot?* That is measured by reading mute
rates and talking to people, and both stop scaling past about ten groups —
one person cannot hold thirty conversations and still hear any of them.

Ten groups is also enough to hit the failure modes that matter: someone will
leave a group, someone will settle in cash and never tell the app, and
someone will mute on day two. Those are the findings. More groups would
produce more of the same finding, later.

---

## §1 Before anyone is invited

- [ ] deployment.md §7 fully green, including the **§6.6a dry-run sweep** and
      a real device receiving exactly ONE reminder for a multi-expense debt.
- [ ] `NUDGE_CRON_SECRET` set on Render **and** in GitHub Actions secrets,
      and the "Nudge sweep" workflow has run green from `main` at least once
      on its own schedule (not just via Run workflow). Scheduled workflows
      only fire from the default branch — if WS13 is still on a branch, the
      cron is not running.
- [ ] VAPID keypair configured (§6.6b). Without it push is off, every nudge
      falls back to email, and the headline feature is being tested in its
      degraded mode.
- [ ] SMTP configured (§6.6c). Email is the fallback channel and the ONLY
      channel on iOS unless the PWA is installed.
- [ ] A backup has been taken **and one restore has been rehearsed**. Beta
      data is real people's money records.
- [ ] Uptime monitor live (deployment.md §7). On Render free the first
      request after 15 idle minutes takes ~1 minute; a beta user hitting
      that with no warning reads it as "broken", not "asleep".

## §2 Set expectations in writing before the invite

Send this with every invite. It is short on purpose, and every line is a
promise the code actually keeps:

> ClearDues is an early beta I'm running with a handful of groups.
>
> - It will send **at most one reminder per person you owe, per group** — never
>   one per expense, and never more than four reminders about the same debt.
> - You can mute any single balance, or switch reminders off entirely, in
>   Settings → Notifications. **Muting is a useful answer**, not a failure —
>   I'd rather you mute than uninstall, and I read the mute numbers.
> - It runs on free hosting: the first page load after a quiet spell can
>   take up to a minute.
> - It is a beta. Please don't use it as your only record of a large debt.
>
> Tell me anything, including that it's annoying. That's the thing I most
> need to know.

## §3 Onboarding 5–10 real groups

Use the product's own invite flow — do **not** seed rows into production.

- [ ] Pick groups with a **live shared debt**, not hypothetical ones. The
      nudge engine has nothing to say about a group with a zero balance, and
      a beta where the differentiator never fires tests the ledger only.
- [ ] Aim for a mix: at least one trip group (bursty, ends), one household
      (steady, never ends), and one pair (the simplest possible case).
- [ ] Create the group, invite by link, and let a real member accept. Watch
      the invite funnel land in PostHog (deployment.md §7) for the first one.
- [ ] Log the group, its shape and its start date somewhere private. Week 1
      numbers are meaningless without knowing which groups existed by then.
- [ ] Stagger onboarding across a few days. Ten groups joining at once
      produces ten simultaneous Level 1 nudges 24 hours later, and no way to
      tell which cohort reacted to what.

## §4 The weekly review (30 minutes, same day each week)

Three numbers, in this order. The first is the stop signal.

### 1. Mute rate — the kill switch (PRD §Risk Mitigation)

```bash
curl -s -H "X-Nudge-Secret: $NUDGE_CRON_SECRET" \
  "https://api.cleardues.site/api/v1/notifications/internal/nudge-metrics?window_days=7" | jq
```

Returns `mute_rate` (muted ÷ **reached**), plus the volume behind it:
`users_nudged`, `users_muted_global`, `users_muted_relationship`,
`sends_by_level`, `debts_cleared_after_nudge`, `relationships_exhausted`.

Read it like this:

| Reading | What it means | What to do |
|---|---|---|
| `mute_rate: null` | Nobody has been reached yet. **Not** 0% | Check the cron actually ran |
| Under ~10% | Within tolerance for an unsolicited notification | Continue |
| 10–25% | The tone is wrong, or the cadence is | Soften Level 2 copy; consider raising `NUDGE_COOLDOWN_HOURS` |
| Over ~25% | **This is the PRD's stop signal.** The "friendly nudge" hypothesis is not holding | Stop inviting. Talk to the people who muted before changing any code |
| `relationships_exhausted` climbing | Level 2 is being ignored, not obeyed | The escalation isn't working; ask why before making it firmer |

`users_muted_global` versus `users_muted_relationship` is the important
split: muting **one** balance is the product working as designed (one
awkward debt silenced, the rest still managed). Muting **everything** is a
person switching the agent off. Weight the second far more heavily.

### 2. Settlement velocity — is the nudging doing anything

PostHog: median `claim_age_hours` on `settlement.claim.confirmed`
(analytics-spec §4). Compare against `debts_cleared_after_nudge` from the
metrics endpoint. If debts clear but never after a nudge, the reminders are
decoration.

### 3. Activation — did the group get off the ground

PostHog activation funnel (analytics-spec §5, dashboard 1). Below ~50% for
invited members means the problem is upstream of nudges entirely.

### Then, every week without exception

- [ ] Message one group directly. Not a survey — a question about the last
      reminder they got.
- [ ] Write down what broke. Week-one groups will hit group-exit and
      end-of-life flows (S2-F4/F5), which **do not exist yet**. Expect it.

## §5 Feedback channel

Pick exactly one and put it in the invite:

- A shared email alias that reaches you on your phone, **or**
- A group chat with all beta users in it (better: they see each other's
  reports and stop duplicating them; worse: one loud opinion can anchor
  everyone).

Whichever it is, reply within a day. Beta feedback is a habit that dies the
first time it goes unanswered.

There is **no in-app feedback widget** — that is a deliberate omission, not
an oversight. Ten groups do not need one, and building it would have come
out of the launch.

## §6 Kill criteria — decide these now, not in the moment

Write the numbers down before the data arrives; that is the entire point.

- [ ] Mute rate over 25% sustained across two weekly reviews → **stop and
      rethink the nudge**, do not tune the copy and carry on.
- [ ] Zero debts cleared after a nudge across three weeks with ≥5 active
      groups → the differentiator does not differentiate.
- [ ] Any data-loss or wrong-balance incident → stop, fix, re-verify the
      ledger before inviting anyone else.

---

## Measured numbers — the scheduler (NFR honesty)

The execution plan asks for real numbers rather than aspirations. These were
produced by [`backend/scripts/nudge_benchmark.py`](./backend/scripts/nudge_benchmark.py),
re-runnable at any time:

```bash
docker compose exec backend python scripts/nudge_benchmark.py --groups 200 --members 6
```

**Environment: local Docker Postgres on a developer laptop, 2026-08-31.
NOT staging** — there is no staging, so this is the most honest measurement
available, and it is a floor rather than a promise. Neon's free tier and
Render's shared CPU will both be slower.

Every seeded user has both delivery channels switched off, so these are the
**engine's** costs — query, netting, suppressor checks, writes — with no
network time. Delivery dominates once push and email actually send.

| Relationships | Discovery query | Sweep (dry run) | Sweep (first, writes) | Sweep (cooled down) |
|---|---|---|---|---|
| 149 (beta scale) | 7.7 ms | 102 ms | 230 ms | 104 ms |
| 3,049 (stress) | 85 ms | 2.9 s | 6.0 s | 2.2 s |

What this says:

- **At beta scale the scheduler is a non-issue.** A quarter of a second, once
  an hour.
- **The sweep is linear in relationships, at roughly 2 ms each**, and that
  cost is dominated by one `nudge_state` lookup per eligible relationship —
  an N+1 the single discovery query (85 ms for 3,000) deliberately avoids.
  Logged as technical debt; it does not need fixing before the beta, and it
  is the first thing to fix if the beta grows.
- **Headroom against the trigger:** the GitHub Actions cron allows 180 s per
  call (`--max-time 180`, covering Render's ~1-minute cold start). At the
  measured rate that is tens of thousands of relationships of theoretical
  room — but do not bank the extrapolation. Real delivery, not the engine,
  is what will hit the ceiling first, and it is not measured here.
- **Re-measure before trusting any of this at ten times the scale.**

### NFR7 is not met, and is not being met

The PRD's NFR7 (1,000 concurrent WebSocket connections) and NFR1 (200 ms
real-time updates via WebSockets) are **unvalidated and unmet**. There are no
WebSockets in ClearDues: real-time was descoped in WS12 along with Redis and
Celery, because Render's free plan has no background worker (architecture.md
"WS12 CORRECTION"). Nothing in this beta tests them, and no number in the
table above should be read as evidence about them. Stated plainly here so
that a future reader finds the gap in the runbook rather than in production.

---

## Launch

- [ ] §1 green, §2 written, §5 chosen
- [ ] First group invited
- [ ] First weekly review scheduled as a recurring calendar event **before**
      the second group is invited
