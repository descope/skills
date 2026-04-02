---
name: auth0-to-descope
description: >
  Use this skill whenever anyone asks about migrating from Auth0 to Descope — whether they're
  a developer doing it themselves or a technical lead evaluating the move. Triggers on: "how
  do I migrate from Auth0", "replace Auth0 with Descope", "we're moving off Auth0", "Auth0 to
  Descope", "switch from Auth0", "our app uses express-openid-connect / nextjs-auth0 / auth0-fastapi / other Auth0 SDK and we want to use Descope instead",
  or any question about Auth0 features (Actions, FGA, Organizations, Token Vault, CIBA) in the
  context of Descope. Works for any language or framework with a Descope SDK. Always use this
  skill before producing migration guidance — do not rely on memory alone.
---

# Auth0 → Descope Migration Skill

This skill guides self-service migrations from Auth0 to Descope: assessing scope,
choosing a migration path, executing framework-specific changes, and verifying the result.

**Primary reference:** `references/implementation-nuances.md` (in this skill's directory) — read the
relevant sections before answering specific questions. It contains verified migration
patterns for several frameworks and Auth0 feature-to-Descope mappings. For frameworks not
covered there, use the Descope docs and SDK type declarations to apply the same principles.

**Always verify current Descope capabilities** before writing migration guidance. The Descope
Docs MCP (`search-descope-docs`, `ask-question-about-descope`) is the most reliable source
for current API signatures, SDK methods, and feature availability — use it in preference to
training data, which may be stale.

**Before proceeding, check whether the Descope Docs MCP is available.** Try calling
`search-descope-docs` with a simple query. If the tool is not available, tell the user:

> "For the most accurate migration guidance, the Descope Docs MCP is recommended. You can
> set it up at **https://docs-mcp.descope.com/** — it takes a few minutes and significantly
> improves the quality of SDK lookups during migration. Would you like to set it up before
> we continue, or proceed with static documentation?"

If they choose to proceed without it, fall back to the reference links at the bottom of this
file and the Descope SDK type declarations. Flag any SDK-specific answers as "based on last
known documentation — verify against current SDK."

---

## Pre-Generation Protocol (apply before writing any code)

These checks must run before generating imports, wrapper types, or helper functions for
any framework. Skipping them produces code that compiles but fails at runtime. The examples
below use TypeScript/Node.js, but the same principles apply to every language — check Go
SDK godoc, Python SDK type hints, Java SDK javadoc, etc.

**1. Verify SDK exports before writing any import.**
Do not assume an export exists because the name looks plausible or analogous to the source
framework. For TypeScript, resolve the target package's type declarations
(`node_modules/<pkg>/dist/types/` or its `package.json` `types` field) and confirm the exact
exported name and its signature. For Go, run `go doc`. For Python, check the SDK source or
stubs. Reading the actual SDK takes seconds and prevents inventing non-existent exports like
`getServerSession`.

This check applies to **every SDK call you write**, not just the first import in a file.
Field names on option objects (`sendMail` vs `sendEmail`), hook return shapes (`useDescope()`
returns the SDK directly, not `{ sdk }`), and subpath exports (`/client` vs root) are equally
likely to differ. When in doubt, grep the installed type declarations rather than inferring
from the source framework's naming.

**1a. After rewriting any module, grep for remaining imports of the removed package across
the whole project.**
Rewriting one file doesn't guarantee its sibling pages, layouts, or form files are clean.
After each module, run:
```bash
grep -r "from '@/lib/auth0'\|from '@auth0/" --include="*.ts" --include="*.tsx" .
```
(or the equivalent for the removed package) and add any files still importing it to the
work list before moving on.

**2. Derive wrapper types from the actual return type, not the source framework's shape.**
When writing a typed wrapper around a third-party function, read the function's declared return
type and build the wrapper to match. Do not infer the shape from what Auth0 returned — field
names, nesting, and flags differ. For example, `session()` from `@descope/nextjs-sdk` returns
`AuthenticationInfo` (`{ jwt, token, cookies? }`), not an `{ isAuthenticated, claims, user }`
object.

**3. Check dependency versions before generating framework-specific code.**
APIs change between major versions. For Next.js specifically: `cookies()` and `headers()` from
`next/headers` are synchronous in v14 and async in v15. Read `package.json` (or `go.mod`,
`requirements.txt`, etc.) before writing framework-specific code.

**4. When making a helper async, immediately propagate to all callers.**
In TypeScript, adding `async` to a shared utility silently breaks all call sites that don't add
`await`. In Python, switching from sync to async has the same cascade. Before finishing any
async conversion: grep for all call sites of the changed function and update them in the same
pass. The cascade can span 10–20 files.

**5. Verify published package versions before writing to `package.json` or running `npm install`.**
Do not reuse the Auth0 SDK's version number as a substitute for the Descope equivalent, and do
not rely on version numbers from training data — Descope SDK versions don't follow Auth0's
versioning and hallucinated versions will cause install failures or install the wrong package.
Before writing any install command or `package.json` entry, run:
```bash
npm view @descope/node-sdk version          # or dist-tags.latest
npm view @descope/nextjs-sdk version
# etc. for each package
```
Use the version returned. If npm is unavailable (no network), leave the version as `"latest"`
and flag it for the user to pin after install.

---

## Step 0: Triage (BLOCKING — requires `AskUserQuestion`)

**Use the `AskUserQuestion` tool to gather the information below. Do not infer answers
from memory, prior conversations, or assumptions — even if you think you already know.**
The migration path differs significantly based on these answers; getting them wrong wastes
the user's time and produces incorrect guidance.

Do not proceed to Step 0.5 until the user has answered.

**First `AskUserQuestion` call (up to 4 questions):**

1. **Backend language / framework** — Present the most likely options based on any cues
   in the conversation (e.g., Express, Next.js, Flask/FastAPI, Go). The user can always
   pick "Other."
2. **Migration goal** — Full cut-over, incremental/phased migration, or just evaluating.
3. **Existing user base** — Are they migrating an app with active users in Auth0, or
   starting fresh? This determines whether user migration planning is needed (password
   hashes, bulk import, phased vs. big-bang cutover, forced re-login on cutover).

**Second `AskUserQuestion` call — Auth0 feature usage (use `multiSelect: true`):**

4. **Which Auth0 features are in use?** Present the highest-impact categories:
   - Actions / Rules / Hooks (custom login logic)
   - Organizations (multi-tenancy / B2B)
   - FGA / fine-grained authorization
   - Social login / Enterprise SSO

   The user can add others via "Other." Follow up on anything selected — e.g., if
   Organizations is selected, ask about tenant-scoped SSO, SCIM, and invitations. If
   FGA is selected, ask about the authorization model.

   Also surface in a follow-up `AskUserQuestion` if not yet covered:
   - Token Vault / Connected Accounts usage
   - M2M / client credentials apps
   - Custom email templates, Log Streams, Attack Protection, custom domains

After both calls are answered, summarize what you learned and flag any high-complexity
items (CIBA, Token Vault, FGA) before proceeding to Step 0.5.

---

## Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

These questions surface blockers that aren't visible from the framework alone. **Use
`AskUserQuestion` to gather answers before proceeding to Step 1.** Do not skip questions
you think you already know the answer to — ask anyway.

Batch these into `AskUserQuestion` calls (up to 4 questions per call). Prioritize the
questions that are most relevant given what you learned in Step 0 — you don't need to
ask all of them if some are clearly not applicable (e.g., don't ask about user migration
planning if the user already said they're starting fresh).

**Access and credentials**
- Do they have access to the Descope Console and a Project ID? (If not, see Step 1.5.)
- Do they need a Management Key? (Required for user CRUD, role management, ReBAC, Outbound Apps.)

**Codebase scope**
- Are there places in the app that read claims directly from the session token (e.g. `token.email`, `req.auth.permissions`)? These need a JWT Template configured before they'll work.
- Do they have Auth0 Actions, Rules, or Hooks? Each one needs to be recreated as a Descope Flow step or JWT Template.
- Are there multiple services or microservices validating Auth0 tokens? Each needs to be updated to validate Descope JWTs.

**Deployment and risk**
- Do they have multiple environments (dev / staging / prod)? Each needs its own Descope project and Project ID.
- Is there a maintenance window, or does this need to be zero-downtime?

**User migration** (if they indicated existing users in Step 0)
- How many users? Under 1,000 → the migration script can pull directly from the Auth0 API. Over 1,000 → Auth0 API pagination breaks; they'll need to export a JSON file via Auth0's User Import/Export extension first.
- Do they use passwords? If yes, they need to open a support ticket with Auth0 to get password hash exports — this takes time, plan for it. Without hashes, users will need to reset passwords or switch to passwordless.
- Big-bang cutover or phased? For zero-disruption, Descope supports session migration (beta) — active Auth0 sessions can be exchanged for Descope tokens without re-auth, but users must already exist in Descope. For phased, the `freshlyMigrated` custom attribute (set automatically by the migration script) can be used in Flow conditionals to give first-time post-migration users a special onboarding path.
- Are they aware that Auth0 sessions will be invalidated on cutover if not using session migration? Plan for a forced re-login or phased rollout.
- Point them to the `descope/descope-migration` script (Step 3) and recommend a dry run (`--dry-run`) before any live run.

**Gaps to flag immediately** (don't ask — flag these proactively based on Step 0 answers)
- If they're using CIBA or `@auth0/ai` wrappers: flag before going further — these have no Descope equivalent and require custom implementation (see Step 3).
- If they're using Auth0 Token Vault in an AI agent: the migration is Medium complexity; no SDK wrapper exists.
- If they're using Auth0 Log Streams: set up Descope's Audit Webhook Connector before cutover to avoid gaps in event logging.

Once you have answers, summarize any blockers explicitly before proceeding to Step 1.

---

## Step 1: Choose a Migration Path

**Use `AskUserQuestion` to ask which path the user wants.** Present both options with
their trade-offs so the user can make an informed choice. Do not pick for them.

### Path A: OIDC Compatibility (lower risk, incremental)

Descope exposes standard OIDC endpoints. If the app uses an OIDC client library
(`express-openid-connect`, `go-oidc`, `authlib`, etc.), it can point at Descope's OIDC
issuer instead of Auth0's with minimal code changes:

| Endpoint | Auth0 | Descope |
|---|---|---|
| Issuer | `https://YOUR_DOMAIN.auth0.com` | `https://api.descope.com` |
| Authorization | `https://YOUR_DOMAIN.auth0.com/authorize` | `https://api.descope.com/oauth2/v1/authorize` |
| Token | `https://YOUR_DOMAIN.auth0.com/oauth/token` | `https://api.descope.com/oauth2/v1/token` |
| UserInfo | `https://YOUR_DOMAIN.auth0.com/userinfo` | `https://api.descope.com/oauth2/v1/userinfo` |
| JWKS | `https://YOUR_DOMAIN.auth0.com/.well-known/jwks.json` | `https://api.descope.com/__ProjectID__/.well-known/jwks.json` |

**Good for:** Teams that want to swap the IdP first, then refactor to Descope-native SDKs
later. Preserves existing OIDC client code.

**Caveats to flag:** Claim shapes differ (`nickname`, `email_verified` vs `verifiedEmail`),
token lifetimes may differ, and any Auth0 Actions logic will need to be rebuilt in
Descope Flows regardless of which path is taken.

### Path B: Full Native Migration (recommended for new projects or clean breaks)

Replace Auth0 SDKs with Descope SDKs. The frontend handles authentication via the
Descope web component or client SDK; the backend validates JWTs only. No server-side
OAuth callback, no code exchange, no session store.

**Good for:** Teams willing to refactor auth once for a cleaner long-term architecture.
Fewer dependencies, fewer env vars, less backend plumbing.

---

## Step 1.5: Descope Project Setup & Console Configuration

Many parts of a Descope migration require setup in the Descope Console that cannot be done
through code or config files alone. The code will compile fine without these, but it won't
work at runtime.

**Use `AskUserQuestion` to check which of these the user has already done.** A good
opening question: whether they already have a Descope project set up with a Project ID
and working Flow — options: "Yes, already set up", "No, need to create one", "Not sure."
If they already have a Project ID and a working Flow, move on — but still check items 5–7
below via `AskUserQuestion`, since these are easy to miss even for existing projects.

### 1. Create a project and get your Project ID
- Sign in at [console.descope.com](https://console.descope.com)
- Your **Project ID** appears in the top-left project selector and under **Project → Settings**. It starts with `P` (e.g. `P2abc123...`).
- For Next.js client-side code, this becomes `NEXT_PUBLIC_DESCOPE_PROJECT_ID`. For all server-side SDKs, it's `DESCOPE_PROJECT_ID`.

### 2. Get a Management Key (if needed)
Required for: user management API, role/permission management, tenant operations, ReBAC
(FGA), Outbound Apps, SCIM configuration. If the app does any server-side user or tenant
management, they need this.
- Console → **Company → Management Keys → Generate Key**
- Store as `DESCOPE_MANAGEMENT_KEY`. Treat like a secret — never expose client-side.
- Use `AskUserQuestion` to ask whether the app does any server-side user/role/admin
  operations — if so, they need a Management Key.

### 3. Choose or create a Flow
A Flow is the authentication UI and logic sequence users go through. You reference it by
its Flow ID in the web component.

- Console → **Authentication → Flows**
- The built-in **"sign-up-or-in"** flow handles email/password, OTP, and social login out
  of the box. Use this for most migrations — it's the quickest path.
- To customise: duplicate "sign-up-or-in", rename it, then edit steps in the visual builder.
- The Flow ID is shown in the URL when editing a flow and in the flow list. Pass it as the
  `flowId` prop to the Descope component (e.g. `flowId="sign-up-or-in"`).
- If the Auth0 app uses MFA: the Flow needs an MFA step added. MFA enrollment in Descope
  is managed through Flows, not the Management SDK — there's no equivalent to Auth0
  Guardian enrollment tickets. Use `AskUserQuestion` to ask whether the app has a
  self-service MFA settings page — if so, plan how to handle it with Descope Flows or
  the UserProfile widget.

### 4. Configure authentication methods
- Console → **Authentication** → select methods (Email OTP, Magic Link, Social, SSO, etc.)
- For social providers (Google, GitHub, etc.): configure OAuth credentials here, then add
  the provider step to your Flow. The web component renders configured providers automatically.
- For enterprise SSO (SAML/OIDC): Console → **SSO** → configure per tenant.

### 5. Configure a JWT Template (almost always needed)
Auth0 includes `email`, `name`, and `picture` in tokens by default. Descope does not.
- Console → **Authorization → JWT Templates → New Template**
- Add claims: `{"email": "{{user.email}}", "name": "{{user.name}}", "picture": "{{user.picture}}"}`
- Apply the template to your project. Without this step, any code reading `token.email`
  will get `undefined` after migration.
- Use `AskUserQuestion` to ask whether the app displays user name, email, or avatar
  anywhere — if so, a JWT Template must be configured before those will work.

### 6. Create roles in the Console (if using RBAC)
Descope roles are referenced by **name**, not by ID. If the app expects roles like `admin`
and `member` to exist, they must be created manually in the Console before the code that
assigns them will work. Unlike Auth0 where role IDs come from env vars, Descope role names
are hardcoded strings — `addTenantRoles()` will fail if the role doesn't exist.
- Console → **Authorization → RBAC → + Role**
- Create each role the app references (e.g. `admin`, `member`)
- Use `AskUserQuestion` to ask what roles the app uses — they must be created in the
  Descope Console under Authorization → RBAC before role assignment code will work.

### 7. Define custom attributes (if using tenant/user metadata)
If the Auth0 app stores data in Organization `metadata` or User `app_metadata`, the Descope
equivalent is `customAttributes` on tenants or users. These attributes must be pre-defined
in the Console schema before they can be set via the SDK.
- Console → **Project → Custom Attributes**
- Use `AskUserQuestion` to ask whether the app stores custom data on organizations or
  users (verification tokens, feature flags, plan info, etc.) — these need to be declared
  as custom attributes in the Console before they can be set via the SDK.

### 8. Env var summary
| Variable | Where to get it | Used by |
|---|---|---|
| `DESCOPE_PROJECT_ID` | Console → Project Settings | All server-side SDKs |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value as above | Next.js `AuthProvider` (client-side) |
| `DESCOPE_MANAGEMENT_KEY` | Console → Company → Management Keys | Management SDK, Outbound Apps API |

---

## Step 2: Framework-Specific Migration

Read the relevant section of `references/implementation-nuances.md` before answering framework-specific
questions. The notes contain tested, verified patterns for each of these.

### Express.js
- Remove `express-openid-connect`; add `@descope/node-sdk` + `cookie-parser`
- Replace `app.use(auth(config))` with ~20-line custom middleware reading the `DS` cookie
  and calling `descopeClient.validateSession()`
- Add `/login` route rendering `<descope-wc>` web component (EJS, plain HTML, etc.)
- Logout: POST to `descopeClient.logout(refreshToken)` + clear `DS`/`DSR` cookies

**Key gotchas:**
- `express-openid-connect` handled CSRF and cookie parsing internally. You need
  `cookie-parser` explicitly.
- `req.oidc.user` → `req.user` (set from validated JWT claims after `validateSession()`)
- `requiresAuth()` is 3 lines of custom code, not an SDK import.

### Flask / Python
- Remove `authlib`; add `descope` Python SDK
- Remove `/callback` route entirely — no code exchange needed
- `/login` renders the Descope web component instead of calling `authorize_redirect()`
- Logout: `descope_client.logout(refresh_token)` + delete cookies
- Drop Flask `session`; state lives in `DS`/`DSR` cookies

**Key gotchas:**
- `authlib` stored `access_token`, `id_token`, `userinfo` in Flask server-side session.
  Descope doesn't use Flask sessions. Drop `APP_SECRET_KEY` and `session` imports.
- `validate_session()` returns a dict of JWT claims. Profile fields aren't there by
  default — configure a JWT Template first (see Step 3 below).

### Next.js
- `@auth0/nextjs-auth0` → `@descope/nextjs-sdk` + `@descope/node-sdk`
- `UserProvider` → `AuthProvider` (takes `projectId` prop; must use `NEXT_PUBLIC_` prefix)
- `useUser()` → `useSession()` + `useUser()` (Descope separates session state from user data)
- Remove `pages/api/auth/[...auth0].tsx` catch-all — no server-side OIDC handling
- Add `/login` page with `<Descope>` component rendering `sign-up-or-in` flow
- `withPageAuthRequired` → manual `useSession()` check + redirect
- `withApiAuthRequired` → call `session()` at handler top, return 401 manually
- Logout: `sdk.logout()` via `useDescope()` hook (not a link to `/api/auth/logout`)

**Server-side session — exact SDK API (verify before generating):**

The `@descope/nextjs-sdk/server` entry exports exactly:
- `session(config?)` — reads session from request headers/cookies in a server component or server action. No `req` argument. Returns `Promise<AuthenticationInfo | undefined>`.
- `getSession(req, config?)` — reads from an explicit `NextApiRequest`. API routes only.
- `authMiddleware(options)` — Next.js middleware factory.

`getServerSession` **does not exist**. The name looks plausible but isn't exported. Before writing any import, open `node_modules/@descope/nextjs-sdk/dist/types/server/index.d.ts` and confirm the export list.

**Session return type — `AuthenticationInfo`, not an Auth0-style session object:**

`session()` returns `AuthenticationInfo | undefined` from `@descope/node-sdk`:
```ts
interface AuthenticationInfo {
  jwt: string    // raw session JWT
  token: Token   // decoded claims: { sub?, exp?, iss?, [claim: string]: unknown }
  cookies?: string[]
}
```
There is no `isAuthenticated`, no `claims` field, and no `user` wrapper. Do not generate a wrapper type that adds these — write an adapter function instead:
```ts
import { session as sdkSession } from "@descope/nextjs-sdk/server"

export async function getDescopeSession() {
  const authInfo = await sdkSession()
  if (!authInfo) return null
  return { isAuthenticated: true as const, jwt: authInfo.jwt, token: authInfo.token }
}
```
Then generate all server components using `getDescopeSession()` from this local file, not from the SDK directly.

**For apps with a separate API server (Express):**
- Remove `express-jwt` + `jwks-rsa`; replace with `descopeClient.validateSession()`
- Forward the `DS` cookie as `Authorization: Bearer <DS>` from Next.js to the API
- No separate access token — the session token is the bearer token

### FastAPI / Python
- Remove `auth0-fastapi` (AuthConfig, auto-mounted `/api/auth/*` routes, require_session)
- Add custom `TokenVerifier` class: reads `Authorization` header, validates against
  Descope JWKS, attaches claims as FastAPI `Security()` dependency
- No auto-mounted routes; no session store

### Go
- Remove `go-oidc` + `golang.org/x/oauth2`; add `descope/go-sdk`
- Remove login/callback/logout backend endpoints (~150 lines) — only keep token validation
- Session validation: `descopeClient.Auth.ValidateSessionWithToken(ctx, token)` returns
  `(bool, *descope.Token, error)`. `Token.Claims` is `map[string]interface{}`
- `sub` claim maps directly to your auth handler's user ID (same claim name as Auth0, different issuer)
- Auth config: ClientID + ClientSecret + Domain + RedirectURL → ProjectID only

---

## Step 2.5: Non-Code File Updates

Code changes alone don't make a migrated app usable. After updating source files, scan
for and update all non-code files that contain Auth0 references. These are the ones most
likely to be stale and cause confusion for the next person running the app.

**What to update — in order of priority:**

### `.env.example` / `.env.template` / `.env.sample`
These are the first place a new developer looks. Replace Auth0 variables with Descope equivalents:
```
# REMOVE
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_ISSUER_BASE_URL=
AUTH0_AUDIENCE=
AUTH0_BASE_URL=
SECRET=

# ADD
DESCOPE_PROJECT_ID=            # Console → Project Settings
NEXT_PUBLIC_DESCOPE_PROJECT_ID= # Next.js only — same value as above
DESCOPE_MANAGEMENT_KEY=        # Console → Company → Management Keys (only if using management SDK)
```
Use `grep -r "AUTH0"` (or `grep -r "auth0"`) to find all env var references across the project,
including `.env.example`, Docker configs, CI files, and any shell scripts.

### README / docs
Search for Auth0 references in all `.md` files. At minimum, update:
- **Setup section** — replace "create an Auth0 app" instructions with Descope Console setup steps
  (create project, get Project ID, configure a Flow, set up JWT Template)
- **Environment variables section** — reflect the reduced env var set
- **Run instructions** — if the README includes steps like "configure Auth0 tenant," replace them
  with the equivalent Descope Console steps
- **Auth flow diagrams or descriptions** — if the README describes the OIDC callback flow or
  session handling, update to reflect Descope's cookie-based approach

### Docker / CI files
Check `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, and any CI config for
`AUTH0_*` env var declarations. Update them to `DESCOPE_*`. Missing these means the app
will boot with empty auth config in CI and production even if local dev works.

### `AskUserQuestion` before editing docs
Before rewriting setup docs, ask: "Does this project have a README or other documentation
with Auth0-specific setup instructions?" If yes, read those files first and update them
in-place rather than rewriting from scratch — preserves project-specific context and keeps
the diff minimal.

---

## Step 3: Feature Migration Mapping

### Auth0 Actions / Rules → Descope Flows + JWT Templates

| Auth0 pattern | Descope equivalent |
|---|---|
| Custom claims in tokens | [JWT Templates](https://docs.descope.com/management/jwt-templates) (static/dynamic claims) |
| Custom logic during auth | [Descope Flows](https://docs.descope.com/flows) — visual pipeline with conditional branching |
| Post-login webhooks | Flows → [Connectors](https://docs.descope.com/customize/connectors) (HTTP calls to external endpoints) |
| Role assignment at login | Flow actions → RBAC role assignment steps |

Auth0 Actions are imperative Node.js. Descope Flows are declarative and visual, with
custom JS escape hatches. Business logic must be restructured around the visual pipeline.

### Social Login → Descope Social Auth
- Configure providers in the Descope Console under Authentication → Social
- Add them to a Flow (no code changes)
- The Descope web component renders configured providers automatically

### RBAC: Auth0 Roles/Permissions → Descope RBAC
Auth0 embeds roles via Actions; Descope embeds them in the JWT by default (no action needed).

| Auth0 | Descope |
|---|---|
| `req.auth.permissions.includes('read:messages')` | `token.permissions.includes('read:messages')` (same pattern, different source) |
| Role claim via namespace in Actions | `roles` array in JWT (built-in) |
| M2M token for Management API | `DESCOPE_MANAGEMENT_KEY` for management SDK |

SDK: `descopeClient.management.role.create(name, description, permissionNames, tenantId)`

### Multi-Tenancy: Auth0 Organizations → Descope Tenants
- Auth0 `org_id` (flat string) → Descope `tenants` (nested object: `{ tenantId: { roles, permissions } }`)
- Auth0 org-scoped login → Descope routes by email domain or tenant-specific URLs
- Tenant-level SSO enforcement available in Descope (SAML/OIDC required for all tenant users)
- Users are project-level in Descope; associated with tenants, not created per-tenant

### Auth0 FGA (OpenFGA) → Descope ReBAC

Schema translation example:
```
# Auth0/OpenFGA
type doc
  relations
    define owner: [user]
    define viewer: [user, user:*]
    define can_view: owner or viewer

# Descope ReBAC DSL
type doc
  relation owner: user
  relation viewer: user
  permission can_view: owner or viewer
```

API shape differences:
- OpenFGA: `{ user, relation, object }` tuples (e.g., `user:alice`, `owner`, `doc:123`)
- Descope: `{ target, targetType, relation, resource, resourceType }` — explicit typed fields

| Operation | Auth0 FGA | Descope ReBAC |
|---|---|---|
| Write relation | `fgaClient.write({ writes: [...] })` | `descopeClient.management.fga.createRelations([...])` |
| Check | `fgaClient.check({ user, relation, object })` | `descopeClient.management.fga.check([...])` |
| List objects | `fgaClient.listObjects(...)` | `descopeClient.management.authz.whatCanTargetAccessWithRelation(...)` |

Note: `FGARetriever` from `@auth0/ai-langchain` has no Descope equivalent. Build a custom
retriever that calls `descopeClient.management.fga.check()` per candidate document.

### Token Vault / Connected Accounts → Descope Outbound Apps

Users connect accounts via `sdk.outbound.connect(appId, { redirectURL, scopes })` on the client.

Fetch stored tokens server-side:
```
POST https://api.descope.com/v1/mgmt/outbound/app/user/token
Authorization: Bearer {projectId}:{managementKey}
Body: { "appId": "google-calendar", "userId": "U2abc...", "scopes": [...] }
```

No AI-framework wrapper exists (`withTokenVault()` from `@auth0/ai` has no equivalent).
Build a custom tool wrapper that calls the Outbound Apps API directly.

### CIBA / Async Authorization → Custom Implementation Required

Descope has **no CIBA equivalent**. `withAsyncAuthorization()` from `@auth0/ai` requires
a custom replacement. Recommended approach:
1. Agent creates a pending approval record in your database
2. Frontend polls for it (or uses WebSocket)
3. User approves via Descope Flow or custom UI
4. Agent receives approval signal and continues

Flag this explicitly — it's the highest-complexity migration item.

### M2M / Client Credentials → Descope Access Keys
Auth0 M2M apps use the client credentials grant. Descope's equivalent is
[Access Keys](https://docs.descope.com/management/m2m-access-keys) — create one in
Console → Access Keys, exchange it for a JWT via `descopeClient.auth.exchangeAccessKey()`,
and validate the resulting token the same way as user tokens. Access keys support tenant
and role scoping, IP restrictions, and configurable expiration.

### User Migration → Descope Migration Script

Descope provides a Python CLI tool — [`descope/descope-migration`](https://github.com/descope/descope-migration) — that handles bulk import of users, roles, permissions, and Auth0 organizations (→ Descope tenants) in one run.

**Two import modes (based on user count):**
- **Auth0 API** — use when fewer than 1,000 users (Auth0 API pagination limit)
- **JSON export** — use when 1,000+ users; export via Auth0's User Import/Export extension, then pass the file to the script with `--from-json`

**Setup:**
```bash
git clone git@github.com:descope/descope-migration.git
cd descope-migration
python3 -m venv venv && source venv/bin/activate
pip3 install -r requirements.txt
cp .env.example .env  # populate with values below
```

Required `.env` variables:
| Variable | Where to get it |
|---|---|
| `AUTH0_TOKEN` | Auth0 Management API → [token explorer](https://manage.auth0.com/#/apis/management/explorer) (24h token) |
| `AUTH0_TENANT_ID` | Your Auth0 dashboard URL, e.g. `dev-xyz` from `manage.auth0.com/dashboard/us/dev-xyz/` |
| `DESCOPE_PROJECT_ID` | Descope Console → Project Settings |
| `DESCOPE_MANAGEMENT_KEY` | Descope Console → Company → Management Keys |

**Always dry-run first:**
```bash
# Via Auth0 API (< 1,000 users), without passwords
python3 src/main.py auth0 --dry-run

# Via JSON export, with passwords
python3 src/main.py auth0 --dry-run --from-json ./export.json --with-passwords ./password_hashes.json
```

Add `-v` / `--verbose` for detailed output. The dry run shows exactly what would be migrated: users, roles, permissions, organizations/tenants — without touching anything.

**Password migration:** optional. Requires opening a support ticket with Auth0 to get a password hash export file, then passing it via `--with-passwords`. Without it, users will need to reset passwords or use passwordless methods after migration.

**What gets migrated:** users, roles, permissions, Auth0 organizations → Descope tenants.

**Auto-created custom attributes:** the script creates two custom attributes in Descope automatically:
- `connection` (text) — the Auth0 connection type for each user
- `freshlyMigrated` (boolean) — set to `true` on import; use this in Flow conditionals to give newly migrated users a special first-login experience (e.g., prompt to verify email, set a password, or enroll in MFA), then flip it to `false` once done

**Live run (after dry-run passes):**
```bash
python3 src/main.py auth0 --from-json ./export.json --with-passwords ./password_hashes.json
```

A log file is generated at `migration_log_auth0_<timestamp>.log`. Any failed items are listed with their error.

**Session migration (beta):** for zero-disruption cutovers, Descope also supports [session migration](https://docs.descope.com/migrate/session-migration) — users with active Auth0 sessions can exchange their existing token for a Descope token without re-authenticating. Requires users to already exist in Descope (import first), and is currently in beta with no JIT user creation support.

**Hybrid migration:** if a full cut-over isn't possible immediately, Descope can be configured as a federated IdP inside Auth0 — users authenticate via Descope Flows while Auth0 remains in place. Requires completing the import step first, then following the [Descope-as-IdP-for-Auth0 guide](https://docs.descope.com/identity-federation/applications/setup-guides/auth0).

For phased migrations without the script, the [Batch Create User API](https://docs.descope.com/api/management/users/batch-create-users) also supports bcrypt hash import directly.

### Email Templates → Descope Messaging Templates
Auth0 email templates (verification, password reset, invitation) map to Descope
[Messaging Templates](https://docs.descope.com/management/messaging-templates), configured
per authentication method in the Console. Templates support HTML and dynamic content.

### Log Streams → Descope Audit Webhook
Auth0 Log Streams map to Descope's
[Audit Webhook Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook).
Configure it in Console → Connectors to stream auth events to your own HTTP endpoint. Set
this up before cutover to avoid gaps in event logging.

### Custom Domains
Auth0 custom domains map to Descope
[custom domains](https://docs.descope.com/how-to-deploy-to-production/custom-domain).
CNAME `auth.example.com` → `cname.descope.com`, verify in Console, then pass `baseUrl` to
the Descope SDK. Plan this before cutover.

### Attack Protection → Descope Flow Security
Auth0 Attack Protection (bot detection, brute force, breached passwords) maps to Descope
Flow steps using security connectors: Arkose Bot Manager, Google reCAPTCHA, Fingerprint,
Have I Been Pwned, AbuseIPDB. These are composable (add detection steps to Flows) rather
than toggle-based. Not configured by default — flag this if the Auth0 app relies on Attack
Protection.

---

## Step 4: Critical Gotchas (Always Cover These)

These are the most common migration mistakes. Surface them proactively.

### JWT Claims Are Not the Same
Descope session JWTs contain `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions` by
default. They do **not** contain `email`, `name`, or `picture`. Auth0 ID tokens include
these by default.

**Action required:** Configure a JWT Template in the Descope Console to add `email`,
`name`, and any other profile fields the app reads from the token. Without this, code
reading `token.email` or `token.name` will get `undefined`.

### Audience Validation Is Opt-In
Descope session tokens have no `aud` claim by default. Apps using `AUTH0_AUDIENCE` for
API access control must:
1. Configure a custom `aud` claim in JWT Templates
2. Pass `audience` to `validateSession()` on the backend

Easy to miss; without it, any valid Descope token passes backend validation.

### Logout Is Two Steps
1. Call `descopeClient.logout(refreshToken)` to invalidate server-side
2. Clear `DS` and `DSR` cookies

Skipping either step leaves a broken state. Both are required.

### Cookie Names Are Configurable (And May Conflict)
Default: `DS` (session JWT), `DSR` (refresh JWT). Configure custom names in the Descope
Console under the Flow's End action when running multiple Descope projects on the same
root domain.

### One Token, Not Two
Auth0 issues separate ID tokens and access tokens (scoped to `audience`). Descope has
one token: the session JWT (`DS` cookie). Forward it as `Authorization: Bearer <DS>` to
API servers. No separate token endpoint.

### No Drop-In Middleware
Descope has no `express-openid-connect` equivalent package. The middleware is ~20 lines
of custom code. This is a feature (simpler, no hidden behavior) but users expecting
a drop-in replacement need to know upfront.

### `cookies()` and `headers()` Are Async in Next.js 15
`cookies()` and `headers()` from `next/headers` return a `Promise` in Next.js 15+. Code
generated against Next.js 14 assumptions (synchronous `cookies()`) will compile but throw
at runtime. Before generating any server-side helper that reads cookies:

1. Check the project's `package.json` for the Next.js version.
2. If ≥ 15: write `await cookies()` and mark the containing function `async`.
3. Trace upward — making a cookie-reading helper async cascades to every caller.
   A single `getActiveTenantId` becoming async can require `await` additions across
   10–20 files. Plan for this before starting edits.

### Async Cascade: Trace All Callers Before Finishing
When a shared utility (e.g., `getActiveTenantId`, `getRole`) becomes async, TypeScript
accepts `await` on non-Promises without error — so callers that forget `await` silently
return a Promise object instead of the resolved value. Always grep for all call sites of
any utility you make async and update them in the same pass.

### Env Var Reduction
Auth0: `CLIENT_ID`, `CLIENT_SECRET`, `ISSUER_BASE_URL`, `SECRET`, `AUTH0_AUDIENCE` (5+).
Descope: `DESCOPE_PROJECT_ID` only (+ `DESCOPE_MANAGEMENT_KEY` for management ops). No
client secret for frontend flows.

---

## Step 5: Automated Testing

Do not hand the user a checklist and stop. Run the app and verify it actually works.
A migration where "the code compiles" is not done — a migration where "the app starts,
serves the login page, and protects routes correctly" is done.

Work through the phases below in order. Stop and surface any failure immediately rather
than continuing past a broken state.

### Phase 1: Install, compile, and start

```bash
# Install dependencies (use whatever package manager the project uses)
npm install   # or: pip install -r requirements.txt / go mod tidy
```

**Run the compile check immediately after making code changes — before setting up `.env` or
starting the server.** Compilation does not require env vars to be populated. This catches
stale Auth0 imports, wrong return-type destructuring, and async cascade gaps before they become
runtime surprises. It takes seconds and saves far more.

```bash
# TypeScript
npx tsc --noEmit

# Go
go build ./...

# Java / Kotlin (Maven)
mvn compile -q

# Java / Kotlin (Gradle)
./gradlew compileJava compileKotlin

# .NET / C#
dotnet build
```

**Do not report the migration as complete, and do not move to Step 6, until this exits with
zero errors.** A passing compile is the minimum bar — it catches stale imports, wrong
return-type destructuring, and async cascade gaps that code review misses.

Compilation errors at this stage typically mean:
- An Auth0 import was removed from the package but is still referenced in code
- A type that was wrapped around an Auth0 shape no longer exists
- An async cascade wasn't fully propagated (TypeScript: `Promise<X>` where `X` was expected)

Fix all compile errors before starting the server. A server that starts despite type errors
(e.g., `ts-node` with loose settings) can hide bugs that will surface in production.

```bash
# Start the development server
npm run dev   # or: python main.py / go run . / flask run / etc.
```

Watch startup output for:
- Missing env var errors (most common first-run failure — means `.env` wasn't populated)
- Module not found / import errors (means an Auth0 package is still referenced somewhere)
- Port conflicts or config errors

If the server fails to start, fix it before proceeding. Do not move to Phase 2.

### Phase 2: Run existing tests

If the project has a test suite, run it now:
```bash
npm test          # or: pytest / go test ./... / etc.
```

Auth-related test failures at this point usually mean:
- A mock or fixture still uses Auth0 token shapes or env vars
- A test directly imports an Auth0 SDK function that was removed
- A test validates JWT claims that are now missing (e.g., `email` without a JWT Template)

Fix failing tests before proceeding. If there are no existing tests, note this and continue.

### Phase 3: Smoke test the running app

With the server running, verify the core auth paths using `curl` or the browser automation
tools available to you. At minimum, check:

**Unauthenticated access (should redirect or 401):**
```bash
# For a web app — expect redirect to /login
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/dashboard

# For an API — expect 401
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/api/protected
```

**Login page loads:**
```bash
curl -s http://localhost:<port>/login | grep -i "descope"
# Should find the Descope web component or SDK reference
# If it returns Auth0 references, something was missed in Step 2
```

**Protected routes without a session return 401 or redirect:**
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/protected-route
# Expect: 302 (redirect to login) or 401
```

**Session validation endpoint (if one exists):**
```bash
# Pass a deliberately invalid token — expect 401
curl -s -H "Cookie: DS=invalid_token" http://localhost:<port>/api/me
```

### Phase 4: Verify JWT claims (if JWT Template is configured)

If the user confirmed a JWT Template was set up in the Console, verify claims are present.
Obtain a valid `DS` cookie via the login flow (have the user log in and copy the cookie
from DevTools, or use a test credential if available), then:

```bash
# Decode the JWT payload (no verification needed for claim inspection)
echo "<DS_cookie_value>" | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

Check that `email`, `name`, and any other expected claims are present. If they're missing,
the JWT Template wasn't applied — flag this explicitly.

### Phase 5: Report results

After running the phases above, produce a brief test summary:

```
## Test Results

**Server startup:** ✅ Started successfully on port 3000
**Existing tests:** ✅ 12 passed / ❌ 2 failed (list failures)
**Unauthenticated /dashboard:** ✅ 302 → /login
**Unauthenticated /api/protected:** ✅ 401
**Login page loads Descope component:** ✅
**JWT claims (email, name):** ✅ Present / ❌ Missing — JWT Template not yet configured

**Blockers before going live:**
- [ ] (list anything that failed or needs manual action)
```

If something can't be tested automatically (e.g., completing a full login flow requires
a real browser and test credentials), say so explicitly and tell the user exactly what
to do and what to look for. Do not silently skip it.

---

## Step 6: Post-Migration Summary (Required)

Every migration must produce a `MIGRATION-SUMMARY.md` at the end. This captures what was
done, what still needs manual setup, and what behavioral differences the user should
be aware of before going to production. A migration isn't done when the code compiles —
it's done when the user knows exactly what they need to set up, verify, and watch out
for.

### MIGRATION-SUMMARY.md

Include the following sections:

1. **What was migrated** — a table mapping each Auth0 concept to its Descope replacement
   (SDK, session handling, middleware, login UI, organizations, roles, SSO, SCIM, MFA,
   user management, invitations, env vars, etc.). Only include rows relevant to this
   specific migration.

2. **Behavioral differences and open questions** — a numbered list of the significant
   differences between the Auth0 and Descope implementations that the user should
   understand. For each item, briefly describe the Auth0 behavior, the Descope behavior,
   and any action required or question to verify. Focus on things that could cause
   confusion or bugs: features with no SDK equivalent (e.g. MFA enrollment tickets, SCIM
   management), model differences (e.g. invitation objects vs. invited-status users,
   org-scoped login vs. multi-tenant JWTs), session/token refresh gaps (e.g. stale JWTs
   after tenant creation requiring re-login), and anything where the code compiles but
   won't work without Console configuration.

3. **Pre-deploy checklist** — actionable checkbox items for everything that must happen
   before the migrated app can run. This should prominently include all Console setup
   tasks: creating the project, generating a Management Key, configuring a JWT Template,
   creating roles, defining custom attributes, setting up Flows, etc. These are the
   things easiest to forget because the code compiles without them.

---

## Step 7: Output Format

Write a clear, numbered migration guide in Markdown, scoped to the user's specific
stack. Prefer concrete code snippets and direct doc links over general descriptions.
Always include the MIGRATION-SUMMARY.md deliverable (Step 6).

For complex migrations (FGA, CIBA, AI tooling), flag the high-effort items explicitly
with estimated complexity (Low/Medium/High) so the user can plan. Reference the
migration difficulty table in `references/implementation-nuances.md` for the agentic AI scenario
(LangChain/LangGraph + FGA + Token Vault + CIBA).

---

## Reference Files

- `references/implementation-nuances.md` — Verified migration patterns, code-level diffs, and edge
  cases for several frameworks. Use as a reference for the principles and patterns; apply
  them to any language or framework the user is using.
- Descope Docs: https://docs.descope.com
- Auth0 Migration Guide: https://docs.descope.com/migrate/auth0
- User Import (Custom): https://docs.descope.com/migrate/custom
- Descope OIDC Endpoints: https://docs.descope.com/getting-started/oidc-endpoints
- Descope Flows: https://docs.descope.com/flows
- JWT Templates: https://docs.descope.com/management/jwt-templates
- Access Keys (M2M): https://docs.descope.com/management/m2m-access-keys
- Messaging Templates: https://docs.descope.com/management/messaging-templates
- Audit Webhook: https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook
- Custom Domains: https://docs.descope.com/how-to-deploy-to-production/custom-domain
- ReBAC: https://docs.descope.com/authorization/rebac
- Outbound Apps: https://docs.descope.com/identity-federation/outbound-apps

### Session Validation by Language
- Node.js: https://docs.descope.com/getting-started/nodejs#implement-session-validation
- Python: https://docs.descope.com/getting-started/python#implement-session-validation
- Go: https://docs.descope.com/getting-started/golang#implement-session-validation
- Ruby: https://docs.descope.com/getting-started/ruby#implement-session-validation
- Java / Kotlin: https://docs.descope.com/getting-started/java#implement-session-validation
- .NET / C#: https://docs.descope.com/getting-started/dotnet#implement-session-validation
- Next.js: https://docs.descope.com/getting-started/nextjs#implement-session-validation
- React: https://docs.descope.com/getting-started/react#implement-session-validation
- Angular: https://docs.descope.com/getting-started/angular#implement-session-validation
- Vue: https://docs.descope.com/getting-started/vue#implement-session-validation
- Swift / iOS: https://docs.descope.com/getting-started/swift#implement-session-validation
- Kotlin / Android: https://docs.descope.com/getting-started/android#implement-session-validation
- Flutter: https://docs.descope.com/getting-started/flutter#implement-session-validation

### SDKs (GitHub)
- Node SDK: https://github.com/descope/node-sdk
- Python SDK: https://github.com/descope/python-sdk
- Go SDK: https://github.com/descope/go-sdk
- Ruby SDK: https://github.com/descope/descope-ruby-sdk
- Java SDK: https://github.com/descope/descope-java
- .NET SDK: https://github.com/descope/descope-dotnet
- Swift SDK: https://github.com/descope/swift-sdk
- Kotlin SDK: https://github.com/descope/descope-kotlin
- Flutter SDK: https://github.com/descope/descope-flutter
- JS/TS monorepo (React, Angular, Vue, Next.js, Web Component, Web JS): https://github.com/descope/descope-js