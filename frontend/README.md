# ClearDues — Frontend

The frontend is built with [Vite](https://vitejs.dev/), [React](https://reactjs.org/), [TypeScript](https://www.typescriptlang.org/), [TanStack Query](https://tanstack.com/query), [TanStack Router](https://tanstack.com/router) and [Tailwind CSS](https://tailwindcss.com/).

There is no Redux and no global store: server state belongs to TanStack Query,
UI state to React local state.

## Frontend development

Before you begin, ensure that you have either the Node Version Manager (nvm) or Fast Node Manager (fnm) installed on your system.

* To install fnm follow the [official fnm guide](https://github.com/Schniz/fnm#installation). If you prefer nvm, you can install it using the [official nvm guide](https://github.com/nvm-sh/nvm#installing-and-updating).

* After installing either nvm or fnm, proceed to the `frontend` directory:

```bash
cd frontend
```
* If the Node.js version specified in the `.nvmrc` file isn't installed on your system, you can install it using the appropriate command:

```bash
# If using fnm
fnm install

# If using nvm
nvm install
```

* Once the installation is complete, switch to the installed version:

```bash
# If using fnm
fnm use

# If using nvm
nvm use
```

* Within the `frontend` directory, install the necessary NPM packages:

```bash
npm install
```

* And start the live server with the following `npm` script:

```bash
npm run dev
```

* Then open your browser at http://localhost:5173/.

Notice that this live server is not running inside Docker, it's for local development, and that is the recommended workflow. Once you are happy with your frontend, you can build the frontend Docker image and start it, to test it in a production-like environment. But building the image at every change will not be as productive as running the local development server with live reload.

Check the file `package.json` to see other available options.

## The API client — one pattern, no exceptions

**Decided in WS11.** Every call to the backend goes through the **generated
client** in `src/client/`, produced from the backend's OpenAPI schema by
[`@hey-api/openapi-ts`](https://heyapi.dev/). Nothing hand-writes a URL, a
request body, or a response type.

Before WS11 the codebase ran two patterns at once: a generated client that had
not been regenerated in months (it still shipped the template's `ItemsService`
and knew nothing about expenses, payments, or settlements) and 33 hand-built
`__request(OpenAPI, { method, url })` calls filling the gaps, backed by ~480
lines of hand-maintained types. A backend field rename type-checked perfectly
and broke at runtime. That is the failure this rule exists to prevent.

### Regenerating

From the **repo root** (not `frontend/`), with the Compose stack up:

```bash
docker compose up -d && bash scripts/generate-client.sh
```

It pulls the schema out of the **running backend container**, writes
`frontend/openapi.json`, and runs `npm run generate-client`. Commit the
resulting `src/client/` changes — `openapi.json` itself is gitignored, since
it is a build input, while the generated client is committed so a fresh clone
type-checks without Docker.

The script used to shell out to a host Python interpreter with the backend
importable. No such interpreter exists on a normal checkout — the backend's
dependencies live in the image — so the documented command could not run at
all. It goes through `docker compose exec` now (fixed in WS11), and refuses to
regenerate from an empty schema dump rather than wiping `src/client/`.

Run it **every time a backend endpoint or schema changes**. A stale client is
how the two-pattern problem started.

### Using it

Import services and types through `@/shared/api` and `@/client`:

```ts
import { GroupsService } from "@/shared/api"

queryFn: () => GroupsService.getGroupDetail({ groupId })
```

Feature-level type modules alias the generated types rather than restating
them — see `src/features/groups/types.ts`, which is WS11's exemplar for the
pattern. The other features still carry hand-written types and raw `__request`
calls; they are queued to follow, feature by feature.

### When a generated type is wrong

Fix the **backend schema**, then regenerate. Do not patch the type on the
frontend — that recreates the two-source-of-truth problem in a new place.

WS11's worked example: `GroupSettingsPublic.ai_personality` was declared `str`
on the backend even though only three values are possible, so the generated
client emitted `string` and the UI lost the union it switches on. The fix was a
`Literal` on the response schema, not a cast in TypeScript.

## Using a Remote API

If you want to use a remote API, you can set the environment variable `VITE_API_URL` to the URL of the remote API. For example, you can set it in the `frontend/.env` file:

```env
VITE_API_URL=https://api.my-domain.example.com
```

Then, when you run the frontend, it will use that URL as the base URL for the API.

## Observability (optional, WS10.6)

Three optional build-time variables wire up analytics and error monitoring;
leaving them unset makes both a complete no-op (nothing is downloaded):

```env
VITE_POSTHOG_KEY=phc_...          # PostHog project API key
VITE_POSTHOG_HOST=                # only for non-US PostHog Cloud (e.g. https://eu.i.posthog.com)
VITE_SENTRY_DSN=https://...       # Sentry React project DSN
```

The event taxonomy and privacy rules live in
[`_bmad-output/planning-artifacts/analytics-spec.md`](../_bmad-output/planning-artifacts/analytics-spec.md);
owner setup steps in [`deployment.md`](../deployment.md) §6.5. Add new events
in `src/lib/analytics.ts` (`EVENTS`) and the spec together.

## Code Structure

Code is organised **by feature**, not by layer:

```
src/
  features/           auth · groups · expenses · payments · dashboard
    <feature>/
      api/            TanStack Query hooks — the only place that calls the client
      components/     components owned by this feature
      types.ts        aliases over the generated types (see the API client rule)
  client/             generated OpenAPI client — DO NOT hand-edit
  shared/api/         re-export shim over src/client
  routes/             TanStack Router file-based routes (file name = URL)
  components/         cross-feature UI (Common/, ui/)
  lib/                analytics, sentry, utils
  hooks/              cross-feature hooks
```

Conventions: `camelCase` for values, `PascalCase` for components, and API/DB
field names stay `snake_case` on the wire — the generated types keep them that
way deliberately, so a property name always matches the backend.

Routes are file-based. A file's name determines its URL, so adding
`src/routes/groups.$groupId.tsx` creates `/groups/:groupId`; a 404 on a route
you just added almost always means the filename doesn't match the convention.

## End-to-end journeys

`tests/` holds four smoke journeys (WS11) that drive the real stack — Postgres,
the API, the production frontend image, and mailcatcher for sign-in emails.
They replaced the template's `login` / `sign-up` / `reset-password` /
`user-settings` specs, which tested a password login this app removed in WS8.

| Spec | What it proves |
|---|---|
| `auth-magic-link.spec.ts` | Registration and sign-in work end to end, and a tampered token leaves no session |
| `group-invite.spec.ts` | The viral loop: create a group, invite, join — and that *viewing* an invite never joins you |
| `expense-confirm.spec.ts` | An expense reaches the other member, who can confirm or reject it, and the balance follows |
| `settle-up.spec.ts` | The debtor claims payment, the creditor confirms, the balance clears — and nothing settles itself |

Plus `csp-headers.spec.ts`, which asserts the served Content-Security-Policy.

### Running them

From the repo root, bring the stack up first:

```bash
docker compose up -d --wait db backend frontend mailcatcher
```

Then, from `frontend/`:

```bash
npx playwright test --project=chromium
```

Interactive mode, for writing new ones:

```bash
npx playwright test --ui
```

To wipe the data the journeys created:

```bash
docker compose down -v
```

### Two things to know before adding a journey

**The suite runs with `bypassCSP`.** The production image serves
`connect-src 'self' https:`, which blocks the plain-http `localhost:8000` API,
so without it every journey renders a page that can do nothing
(solution-patterns FE-008). `csp-headers.spec.ts` is the compensating check —
don't delete it.

**Splits are applied over the API, not the UI.** `tests/utils/api.ts`
explains why: the manual "Add Expense" form creates a `draft` and nothing in
the interface can then split it, so a manually-created expense can never be
confirmed or settled. The journeys work around that to cover the confirm and
settle screens. When the manual form grows a split step, delete the workaround
and click it instead.

For more on writing Playwright tests, see the official
[Playwright documentation](https://playwright.dev/docs/intro).
