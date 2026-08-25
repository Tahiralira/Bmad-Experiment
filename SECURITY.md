# Security Policy

ClearDues handles money people owe each other. We take reports seriously.

## Supported versions

ClearDues is a continuously deployed application, not a distributed library.
Only the currently deployed version at [cleardues.site](https://cleardues.site)
is supported — there are no maintained older releases to patch.

## Reporting a vulnerability

Email **security@cleardues.site**. If you are not sure whether what you found is
a real issue, report it anyway.

Please include:

- What the issue is, and what an attacker could do with it
- Step-by-step reproduction, with example requests or code where relevant
- Which URL or environment you observed it on

You will get an acknowledgement within **3 business days** and an assessment
with a fix timeline within **10 business days**. ClearDues is pre-beta and
maintained by a very small team, so responses come from a person, not a queue.

## Please do not

- Publicly disclose the issue before we have had a chance to fix it. Private
  disclosure first limits the blast radius for real users.
- Access, modify, or delete data belonging to accounts that are not yours. If a
  proof of concept requires a second account, create one.
- Run automated scanners, load tests, or brute-force attempts against the
  production deployment. Run the stack locally instead —
  [development.md](./development.md) gets you a full environment in one command.

Good-faith research that follows the above will not be pursued or reported.

## Scope

In scope: `cleardues.site`, `api.cleardues.site`, and this repository.

Out of scope: findings against third-party platforms we build on (Vercel,
Render, Neon, PostHog, Sentry) — report those to the respective vendor. Also out
of scope: missing security headers with no demonstrated impact, and reports
generated solely by an automated scanner with no working proof of concept.

## Thank you

Reports that lead to a fix get credited in the changelog, if you would like the
credit.
