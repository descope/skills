---
name: okta-cis-to-descope
description: >
  Use this skill whenever anyone asks about migrating from Okta Customer Identity Service (CIS)
  to Descope — whether they're a developer doing it themselves or a technical lead evaluating
  the move. Triggers on: "how do I migrate from Okta", "replace Okta CIS with Descope", "we're
  moving off Okta", "Okta to Descope", "switch from Okta", "our app uses okta-auth-js /
  @okta/okta-react / @okta/okta-angular / @okta/oidc-middleware / okta-jwt-verifier and we want
  to use Descope instead", or any question about Okta CIS features (Sign-On Policies, Authorization
  Servers, Authenticators, Identity Providers, Log Streams, Service Apps, scp claim) in the
  context of Descope. Works for any language or framework with a Descope SDK. Always use this
  skill before producing migration guidance — do not rely on memory alone.
---

# Okta CIS → Descope Migration Skill

This skill guides self-service migrations from Okta Customer Identity Service (CIS) to Descope.
It runs in three parts:

1. **MCP Check** — confirm whether the Descope Docs MCP is available and suggest installing it if not
2. **Migration Plan** — gather context via triage questions, analyze the codebase's auth touchpoints, and produce a human-readable `MIGRATION-PLAN.md` for the user to review
3. **Execution** — if the user confirms they want to proceed, execute the plan

Do not collapse these parts or skip ahead. The plan must be reviewed before code changes begin.

**Primary references** (all in this skill's directory):
- `references/implementation-nuances.md` — verified migration patterns for each JS/TS framework, Okta CIS feature-to-Descope mappings, and known gotchas
- `references/flows-and-widgets.md` — Descope terminology/lingo (Okta→Descope), Flow structure and templates, Widgets, SSO Setup Suite, Console-vs-code decision guide
- `references/backend-sdks.md` — Python and Java backend migration patterns (Flask, FastAPI, Django, Spring Boot, management SDK, M2M)

---

## Guiding Principles

**Console-first.** Before recommending SDK code for any user-facing auth feature, check whether the Console, a Flow, or a Widget covers the use case. Okta CIS is a low-code platform — users configure auth logic through the Okta Sign-In Widget, the visual policy builder (OIE), email customization, and the admin console. Descope has direct equivalents for all of these: Flows replace the visual policy builder, the Descope Flow component replaces the Sign-In Widget, Messaging Templates replace email customization, and Widgets replace custom management UIs. Engineers integrate once (SDK setup + session validation). All subsequent auth evolution — new methods, MFA changes, UI updates, branding — should happen in the Console without code deployments. See `references/flows-and-widgets.md` → Console vs. Code.

**Ask, don't assume.** At any design decision point — especially Inbound Apps vs. Federated Apps (the core Okta strategy fork), Flow vs. custom code, Widget vs. custom page, MFA inline vs. separate enrollment — use `AskUserQuestion` rather than proceeding with an assumption. The cost of a wrong assumption compounds across 20+ files. Always confirm whether the backend validates `scp` claims before recommending the Inbound Apps path.

**MCP over memory.** When the Docs MCP is available (confirmed in Part 1), use `ask-question-about-descope` to verify every SDK method name, option shape, and return type before writing it. Do not fall back to "verify the exact method name in the SDK type declarations" as a hedge — just verify it directly.

---

## Part 1: MCP Check (BLOCKING)

Before doing anything else, check whether the Descope Docs MCP is available by calling
`search-descope-docs` with a simple query (e.g., "session validation").

**If the tool is available:** proceed to Part 2 immediately.

**If the tool is not available**, show this message and use `AskUserQuestion` to ask whether
they want to install it first:

> **Descope Docs MCP is not installed.**
>
> This skill uses the Descope Docs MCP to look up current API signatures, SDK methods, and
> feature availability during migration. Without it, guidance is based on static training data,
> which may be stale and can produce SDK calls that don't exist.
>
> You can install it in a few minutes at **https://docs-mcp.descope.com/** (server URL:
> `https://docs-mcp.descope.com/mcp`). It significantly improves the accuracy of the
> migration output — especially for SDK lookups and flow-specific configuration.
>
> **Would you like to install the MCP before we continue, or proceed without it?**

- If they choose to install: pause and wait. Once they confirm it's installed, re-check by calling `search-descope-docs` again before proceeding.
- If they choose to proceed without it: continue, but flag any SDK-specific answers as "based on last known documentation — verify against the current SDK."

Do not proceed to Part 2 until this step is resolved.

---

## Part 2: Migration Plan

Part 2 has two sub-steps:

1. **Triage** — ask the questions needed to understand scope
2. **Codebase Analysis + Plan File** — scan the project, produce `MIGRATION-PLAN.md`, and pause for review

### Step 0: Triage (BLOCKING — requires `AskUserQuestion`)

**Use the `AskUserQuestion` tool to gather the information below. Do not infer answers
from memory, prior conversations, or assumptions — even if you think you know.**
The migration path differs significantly based on these answers.

Do not proceed to Step 0.5 until the user has answered.

**Decision 0 — Login mode (resolve this before anything else):**

Ask this as the first `AskUserQuestion`:

> "Is the app using Okta's **hosted/redirect login** — for example, `loginWithRedirect`, `@okta/oidc-middleware`, or users being sent to an Okta-hosted login page to authenticate? Or does it use an **embedded login UI** — the Okta Sign-In Widget embedded in the page, or a custom auth form built with `okta-auth-js` in non-redirect mode?"

Decision tree:
```
Login mode?
├── REDIRECT (hosted Okta page, loginWithRedirect, oidc-middleware, passport-openidconnect)
│     → Default to OIDC path: update OIDC client config to point at Descope endpoints
│       Set up Federated App or Inbound App in Console (Decision 1 determines which)
│       No new login page, no new SDK required — redirect/callback plumbing stays intact
│
└── EMBEDDED (Okta Sign-In Widget in-page, custom okta-auth-js non-redirect flow)
      → Default to embedded Descope Flow component path
        Replace widget/form with <Descope flowId="sign-up-or-in" />
        Still determine Federated vs. Inbound App via Decision 1
```

Do not proceed until this is resolved — it determines the entire migration approach.

---

**Decision 1 — Inbound Apps vs. Federated Apps:**

Ask as the second `AskUserQuestion` (applies to both login modes — it determines which type of app to configure in the Console):

> "Does the backend validate OAuth scopes from the Okta access token? (i.e., is there backend code that reads `token.scp`, `claims["scp"]`, or similar to make authorization decisions?)"

Decision tree:
```
Does any backend service validate token scopes (scp claim)?
├── YES  → Inbound Apps path
│          (Descope enforces scopes; custom claims go in JWT Template on the Inbound App)
├── NO   → Federated Apps + OIDC layer
│          (Okta used for identity only; often just update JWKS URL + Issuer, no scope changes)
└── UNSURE → Ask them to grep: token.scp  claims["scp"]  req.auth.scp
             Then re-ask.
```

Do not proceed until this is resolved.

---

**Remaining triage — first `AskUserQuestion` call (up to 3 questions):**

1. **Backend language / framework** — Present the most likely options based on cues in the conversation (Node.js/Express, Next.js, Angular, React SPA, Go, Python, Java). The user can always pick "Other."
2. **Migration goal** — Full cut-over, incremental/phased migration, or just evaluating.
3. **Existing user base** — Are they migrating an app with active users in Okta, or starting fresh? This determines whether user migration planning is needed.

**Second `AskUserQuestion` call — Okta CIS feature usage (use `multiSelect: true`):**

Which Okta CIS features are in use? Present these options:
- Okta Sign-In Widget (`@okta/okta-signin-widget` — embedded login UI component)
- Sign-On Policies (per-app auth rule chains / visual policy builder)
- Authenticator Enrollment Policies (MFA factor requirements)
- Authorization Servers / APIs (custom OAuth audiences and scopes)
- Identity Providers (external SAML/OIDC SSO per customer org)
- Authenticators (WebAuthn/Passkeys, TOTP, Okta Verify, SMS, etc.)
- Log Streams (Splunk Cloud, Amazon EventBridge)
- Service Apps / API Services (M2M / client credentials)
- Token Inline Hooks (custom logic during auth)
- Groups (used for RBAC/access control)

The user can add others via "Other." Follow up on anything selected — e.g., if Authorization
Servers is selected, ask about custom claims using Okta Expression Language. If Authenticators
is selected, ask which specific types.

After both calls, summarize findings and flag high-complexity items (Token Inline Hooks with
external dependencies, complex Sign-On Policy rule chains, custom Expression Language claims)
before proceeding to Step 0.5.

---

### Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

These questions surface blockers the framework doesn't expose. Ask even the ones you think
you know. Use `AskUserQuestion` before proceeding to codebase analysis.

Batch into calls of up to 4 questions. Skip questions that are clearly inapplicable given
Step 0 answers (e.g., skip user migration planning if they said they're starting fresh).

**Strategy confirmation**
- Does the backend validate `scp` claims from the Okta access token? (If yes → Inbound Apps. If unsure, show them what to grep for: `token.scp`, `claims["scp"]`, `req.auth.scp`.) — skip if already resolved in Decision 1
- For redirect-mode apps: is the migration goal to keep the redirect flow (OIDC endpoint swap only) or eventually move to the embedded Descope Flow component? (The OIDC path is a valid permanent solution — not just a stepping stone.)
- Are Sign-On Policies per-app, global, or both? (Determines scope of Flow migration.)
- Is scope validation in application code or in an API gateway / JWT authorizer? (If gateway → just update JWKS URL and Issuer, no code change.)

**Access and credentials**
- Do they have access to the Descope Console and a Project ID? (If not, see Step 1.5.)
- Do they need a Management Key? (Required for user CRUD, role management, tenant management, SCIM.)

**Codebase scope**
- Are there places in the app that read claims directly from the token (e.g., `token.scp`, `req.auth.permissions`, `token.groups`)? These need a JWT Template configured before they'll work.
- Do they have Token Inline Hooks? Each one needs to be recreated as a Descope Flow Scriptlet or Generic HTTP Connector.
- Are there multiple services or microservices validating Okta tokens? Each needs to be updated to validate Descope JWTs (or have its JWKS URL + Issuer updated if using an API gateway).

**Deployment and risk**
- Do they have multiple environments (dev / staging / prod)? Each needs its own Descope project and Project ID.
- Is there a maintenance window, or does this need to be zero-downtime?

**User migration** (if they indicated existing users in Step 0)

There are three migration paths — pick one or combine them. Confirm which fits before planning.

- **Full migration**: Export all users from Okta (Management API `GET /api/v1/users`, paginated), transform attributes, and bulk-import into Descope before cutover. Use the Batch Create Users Management API directly. Optionally set a `freshlyMigrated` custom attribute to `true` on import to enable first-login Flow logic.
- **JIT (password verification)**: Don't bulk-export. When a user signs in, verify their password against the Okta Authentication API (`POST /api/v1/authn`), then create or link the user in Descope and issue a Descope session. The user must re-enter credentials but no upfront export is needed.
- **Session migration (JIT without re-login)**: The app sends the user's existing Okta session token to Descope; Descope validates it, provisions the user in Descope just-in-time, and issues a Descope token. The user only needs the app to update — no re-login. This is the highest-quality zero-disruption path. See [docs.descope.com/migrate/session-migration](https://docs.descope.com/migrate/session-migration).

**Password constraint (all paths):** Okta does not export password hashes. For full migration, plan for a reset campaign, a first-login "set new password" Flow step, or a full switch to passwordless.

**Dual-token validation (critical for phased rollouts):** During any gradual cutover, the backend will receive both Okta JWTs (from users not yet migrated) and Descope tokens. The backend must validate both — inspect the token issuer or `kid` to route to the correct validator. See `references/implementation-nuances.md` → Dual Token Validation.

**Passkeys and TOTP cannot be migrated** — Okta does not expose these seeds. Users who enrolled passkeys or TOTP in Okta must reprovision them in Descope after migration.

**Gaps to flag immediately** (don't ask — flag these proactively based on Step 0 answers)
- If they're using **Passkeys or TOTP authenticators**: **these cannot be migrated**. Okta does not expose passkey credentials or TOTP seeds. Users will need to reprovision both in Descope after cutover — this requires a user-facing prompt (add a re-enrollment step to the sign-in Flow for affected users). Flag this early; it directly affects the user experience at launch.
- If they're using **Okta Verify push notifications**: there is no direct equivalent in Descope. Recommend replacing with Email Magic Link, TOTP, or WebAuthn/Passkeys.
- If they're using **Smart Card authenticator**: contact Descope support before migrating.
- If they're using **Security Question authenticator**: no equivalent in Descope. Plan removal or replacement.
- If they're using **Okta Workflows** (separate from CIS Policies): flag as out-of-scope for this skill — Workflows require a separate evaluation.
- If they're using **Log Streams to Datadog**: Datadog is NOT a direct Okta Log Stream destination, and Descope has no native Datadog audit connector. Plan for a custom Audit Webhook.

**Console/Flow/Widget opportunities** (flag before codebase analysis, then ask):
- If the app embeds the **Okta Sign-In Widget** (`@okta/okta-signin-widget`): the migration is almost entirely Console-side. Embed the Descope Flow component (`<Descope flowId="sign-up-or-in" />`) in the same location. No redirect required; the same low-code/no-code principle applies.
- If the app uses Okta's **hosted/redirect login** (`loginWithRedirect`, `@okta/oidc-middleware`, or any redirect-based OIDC flow): **default to the OIDC path** — set up a Federated App or Inbound App in Console and update the issuer/client-ID env vars. Do NOT recommend replacing the redirect flow with an embedded Descope component unless the user explicitly wants that. See `references/implementation-nuances.md` → OIDC compatibility path and the Node.js + @okta/oidc-middleware section (Option A).
- If the app has a custom SSO settings page: ask whether the SSO Setup Suite + Tenant Profile Widget replaces that code.
- If the app has a profile edit page or user management UI: ask whether a Descope Widget covers the use case.
- If the app has a separate MFA enrollment page: ask whether MFA should be integrated into the main sign-in Flow as a step or subflow (almost always cleaner in Descope).
- If any server-side code generates emails or runs logic during the auth journey: ask whether that logic can be a Flow Scriptlet or Connector instead.

Summarize any blockers and Console/Flow opportunities before proceeding to codebase analysis.

---

### Step 0.75: Fast-Track Assessment

Before running codebase analysis, determine whether the app qualifies for a minimal-code migration.

**Fast-track A — OIDC redirect swap (all three must be true):**
1. App uses **hosted/redirect login** (Decision 0 = redirect)
2. **Decision 1 resolved to Federated Apps** (no backend scope validation)
3. **No Token Inline Hooks** selected in the feature multiselect

**If all three are true:** this is a minimal-config migration. The work is ~80% Console setup:
- Create a Federated App in Console (Applications → Federated Apps → + Application); register the callback URL
- Configure the Descope Flow linked to the app (auth methods, branding) — this replaces the Okta hosted login page
- Update env vars: `OKTA_ISSUER` → `https://api.descope.com/DESCOPE_PROJECT_ID`; `OKTA_CLIENT_ID` → Project ID; `OKTA_CLIENT_SECRET` → a Descope Access Key
- If using `@okta/oidc-middleware`: replace with `openid-client` (Okta's middleware is not confirmed to work with non-Okta issuers)
- Check `scp` → `scope` claim rename in any backend authorization code (see `implementation-nuances.md` → scp vs. scope claim)
- Configure JWT Template for `email`/`name` claims
- No new login page, no SDK swap, no changes to callback routes

Skip or abbreviate framework-specific code changes in Step 2. Codebase analysis is still useful to find stale Okta references and `scp` usages, but the diff will be small.

---

**Fast-track B — Embedded widget swap (all four must be true):**
1. App embeds the **Okta Sign-In Widget** (`@okta/okta-signin-widget`) rather than a custom SDK-based auth flow
2. **Decision 1 resolved to Federated Apps** (no backend scope validation)
3. **No Token Inline Hooks** selected in the Step 0 feature multiselect
4. **No Authorization Servers** with custom claims or resource policies selected in Step 0

**If all four are true:** this is a minimal-code migration. The work is 90%+ Console-side:
- Embed `<Descope flowId="sign-up-or-in" />` (or the web component) where the widget was
- Configure the Flow in the Console — auth methods, MFA steps, branding
- Update env vars (`OKTA_*` → `DESCOPE_PROJECT_ID`)
- That's most of the migration

Skip or abbreviate Step 2 (framework-specific code changes). Codebase analysis is still useful to find any stale Okta references, but the diff will be small.

**If neither fast-track applies:** proceed with full codebase analysis below.

---

### Step 1: Codebase Analysis

Scan the codebase and fetch Okta policies before writing the plan. Both are required — code analysis finds what changes, policy analysis determines how complex the Flow migration will be.

**Step 1a — Code analysis (adapt file extensions to the user's language):**

```bash
# Find all Okta import sites
grep -rn "okta-auth-js\|@okta/okta-react\|@okta/okta-angular\|@okta/okta-vue\|@okta/oidc-middleware\|okta-jwt-verifier\|@okta/jwt-verifier\|@okta/okta-signin-widget" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=venv \
  . 2>/dev/null

# Find all Okta env var references
grep -rn "OKTA_\|OKTA_CLIENT\|OKTA_ISSUER\|OKTA_DOMAIN\|OKTA_AUDIENCE\|OKTA_REDIRECT" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --include="*.env*" --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Find scp / scope claim access patterns (things that need scp→scope update or JWT Template)
grep -rn "\.scp\b\|token\.scp\|claims\[.scp.\]\|req\.auth\.scp\|req\.userContext\|token\.claims\b" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Find protected route / auth guard declarations
grep -rn "requiresAuth\|OktaAuthGuard\|loginWithRedirect\|authGuard\|isAuthenticated\$\|oktaAuth\b\|withRequiredAuthInfo\|ensureAuthenticated" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Check package.json / go.mod / requirements.txt for Okta dependencies
find . -maxdepth 3 \( -name "package.json" -o -name "go.mod" -o -name "requirements.txt" \) \
  ! -path "*/node_modules/*" -exec grep -l "okta" {} \;
```

**Step 1b — Policy analysis (required before writing the plan):**

Policy rules determine how complex the Flow migration will be. Retrieve them now so MIGRATION-PLAN.md reflects the actual logic, not a generic template.

```bash
# Sign-On Policies (type=ACCESS_POLICY → called "Sign-On Policies" in the Okta Console)
# Each one becomes a Descope Flow
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=ACCESS_POLICY" \
  | jq '[.[] | {name, id, ruleCount: (.rules | length), conditions: .conditions}]'

# Authenticator Enrollment Policies (MFA requirements → Flow MFA steps or subflows)
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=MFA_ENROLL" \
  | jq '[.[] | {name, id, rules: [.rules[] | {priority, conditions, actions}]}]'

# Global Session Policies (session lifetime → Console → Project Settings → Session Management)
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=OKTA_SIGN_ON" \
  | jq '[.[] | {name, id, rules: [.rules[] | {maxSessionIdleMinutes: .actions.signon.session.maxSessionIdleMinutes, maxSessionLifetimeMinutes: .actions.signon.session.maxSessionLifetimeMinutes}]}]'
```

For each Sign-On Policy found, note: number of rules, conditions per rule (group, network zone,
device), factors required per rule, and any post-auth hooks. This becomes the Flow complexity
estimate in the plan.

For each hit, record:
- **File path and line** — where the change happens
- **What it does** — import, route protection, claim access, logout handler, etc.
- **Complexity** — Low (drop-in replacement), Medium (logic rewrite), High (no equivalent)

Read `package.json` (or equivalent) for the exact framework version — this affects async
behavior (Next.js 15 vs 14) and SDK compatibility.

If the Descope Docs MCP is available, use `search-descope-docs` or `ask-question-about-descope`
to verify current SDK method names for anything you plan to reference in the plan.

---

### Step 2: Write MIGRATION-PLAN.md

Write `MIGRATION-PLAN.md` to the working directory using the triage answers and codebase
analysis.

Two audiences: the engineer needs enough technical detail to execute; the PM or tech lead
needs scope, risk, and timeline without decoding jargon. Use plain English. Explain
technical terms on first use. Open each section with a sentence summarizing what it means
before presenting tables or evidence. Say what breaks if a risk is missed, not just that it
exists. Pair complexity labels with time estimates; skew toward the lower bound. Group
execution into phases so parallel vs. sequential work is clear.

The plan must include these sections, in this order:

#### Overview

2–3 sentences: what's being replaced, what replaces it, and the recommended approach with a
one-sentence rationale. Add one sentence on what doesn't change — user-facing login behavior,
sessions, and existing accounts are preserved.

Include a **Migration at a Glance** table:

| | |
|---|---|
| **Approach** | Inbound Apps (full native) / Federated Apps (OIDC layer) |
| **Files changing** | N source files across N areas |
| **Console setup** | N configuration steps before launch |
| **User impact** | No re-login required / Users will need to log in once after cutover |
| **Estimated engineering effort** | N–N hours |
| **Biggest risk** | One sentence naming the highest-complexity item |

---

#### What's Changing and Why

Prose (not a table) describing what each part of the system does today and what it does
after. Example:

> Today, Okta handles everything related to login: it shows the hosted sign-in page, issues
> tokens, and validates them on every API request. After this migration, Descope takes over all
> of those responsibilities. The login UI becomes a Descope Flow embedded in the app. Token
> validation moves to the Descope SDK. The five Okta environment variables are replaced by a
> single Descope Project ID.
>
> Okta CIS features in use that need to carry over: [list in plain English, one clause each].

Tailor to triage findings.

---

#### Auth Touchpoints: What the Code Analysis Found

Open with the scope count (e.g., "9 files across 3 areas"). Group by area, not file path.
Each group gets a sentence on what it does and what changes.

**Session handling (2 files)** — These files read and validate the current user's login
state. They'll be updated to use the Descope session SDK instead of Okta's.

| File | What it does today | What changes |
|---|---|---|
| `middleware/auth.ts:22` | Validates Okta access token via `okta-jwt-verifier` | Rewritten to call `descopeClient.validateSession()`; `scp` → `scope` claim reference updated |
| `lib/session.ts:8` | Returns `req.userContext.userinfo` | Updated to return Descope `AuthenticationInfo.token` |

Cover all functional groupings. End with: "Total: N files. Estimated code-change effort: N–N hours."

---

#### Feature Migration: Okta CIS → Descope

For each Okta CIS feature confirmed in triage, write a short paragraph: what it's trying to
accomplish, the best Descope approach for that goal, what's different, and what action is
required. The best approach may be a Flow, Widget, SSO Setup Suite, or Console configuration
rather than a direct SDK equivalent. Only recommend SDK code when programmatic control is
genuinely required. Example:

> **Sign-On Policies → Descope Flows**
> Okta Sign-On Policies define per-app authentication rule chains: which factors are required,
> in what order, and under which network or group conditions. Descope Flows replace this with a
> visual pipeline where each rule becomes a Condition or step. The Sign-On Policy can be fetched
> via `GET /api/v1/policies?type=ACCESS_POLICY` to understand the exact logic before building
> the corresponding Flow. Most single-rule policies map to one Flow with a Condition branch.
> **Effort: Low–Medium (30 min per simple policy, 2–3 hours for complex branching logic).**

Only include confirmed features.

---

#### Before the Code Can Run: Required Configuration

List every Console setup item as a checkbox. Group into "Required before any testing" and
"Required before production":

**Required before any testing:**
- [ ] **Create a Descope project** — Takes 2 minutes. Produces a Project ID that replaces all Okta credentials in the app's environment variables.
- [ ] **Create an authentication Flow** — The built-in `sign-up-or-in` flow works for most apps without customization. Use it to start.
- [ ] **Configure a JWT Template** — Okta ID tokens include `email` and `name` by default. Descope does not. In Console → **Project Settings → JWT Templates → + JWT Template → User JWT**, add claims with **Type: Dynamic**: `email` → `user.email`, `name` → `user.name`. Without this, any UI reading the user's name or email shows blank values. (~10 minutes)
- [ ] **Configure authentication methods** — Enable the methods that match the Okta Authenticators in use (Passkeys, TOTP, SMS OTP, Email OTP/Magic Link). (~5 minutes each)

**Required before production:**
- [ ] **Create roles** (if using Groups for RBAC) — List actual roles found in codebase.
- [ ] **Configure Tenant SSO** (if migrating Identity Providers) — Per-tenant SAML/OIDC setup via Console → SSO or SSO Setup Suite.
- [ ] **Set up Audit Connector** (if using Log Streams) — Splunk Connector OOTB; custom webhook for EventBridge/Datadog.
- [ ] (continue for each item found in analysis)

---

#### Environment Variables

Diff table with plain-English notes for each removal and addition:

**For the OIDC path (redirect-based login):**

| Remove | Add | Why |
|---|---|---|
| `OKTA_ISSUER` / `OKTA_DOMAIN` | — | Replaced by `DESCOPE_PROJECT_ID` in the issuer URL (`https://api.descope.com/PROJECT_ID`). |
| `OKTA_CLIENT_ID` | `DESCOPE_PROJECT_ID` | For Federated OIDC Apps, the Project ID is the OIDC `client_id`. |
| `OKTA_CLIENT_SECRET` | `DESCOPE_ACCESS_KEY` | For Federated OIDC Apps, an Access Key is the `client_secret`. Generate one in Console → Access Keys. |
| `OKTA_AUDIENCE` | — | Handled by the Inbound App definition, if in use. |
| — | `DESCOPE_MANAGEMENT_KEY` | Only needed if the app manages users, roles, or tenants server-side. |

`OKTA_REDIRECT_URI` / callback URL stays — Descope's OIDC endpoints accept the same callback path.

**For the embedded path (Descope Flow component):**

| Remove | Add | Why |
|---|---|---|
| `OKTA_CLIENT_ID` | — | Okta identifies apps by client ID. Descope uses a Project ID instead. |
| `OKTA_CLIENT_SECRET` | — | Not needed. Descope's embedded flow doesn't require a secret. |
| `OKTA_ISSUER` / `OKTA_DOMAIN` | — | The Okta tenant URL. Replaced by the Project ID. |
| `OKTA_AUDIENCE` | — | Used for API access scoping. Can be replicated via Inbound App + JWT Template if needed. |
| `OKTA_REDIRECT_URI` | — | Descope's embedded flow doesn't use redirect URIs. |
| — | `DESCOPE_PROJECT_ID` | The single identifier for the Descope project. Replaces all of the above. |
| — | `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value, exposed to the browser for Next.js client components. |
| — | `DESCOPE_MANAGEMENT_KEY` | Only needed if the app manages users, roles, or tenants server-side. |

Follow with: "Net change: [N variables removed, N added — use the appropriate table above based on login mode]."

---

#### User Migration (only if existing users need to be migrated)

Prose strategy first, then steps. Start with: "X existing users need to be in Descope before cutover."

Key Okta-specific constraint: **Okta does not export password hashes to third parties.** Users
will need to reset their passwords or switch to passwordless after cutover. Plan for one of:
- A password reset email campaign sent before cutover
- A "set new password on first login" step added to the Descope sign-in Flow
- A full switch to passwordless (magic link, passkeys, TOTP)

End with a brief PM-trackable checklist:
- [ ] Choose password migration strategy — reset campaign, first-login step, or passwordless
- [ ] Export user list from Okta (Management API `GET /api/v1/users` or Okta Reports)
- [ ] Transform user data to Descope import format
- [ ] Run import against the Descope dev project and review output for errors
- [ ] Run import against staging, then production

---

#### Trade-offs and considerations

Write each in plain English with three parts: **what it is**, **what breaks if it's ignored**, **what to do**.

> **Consideration: scp → scope claim rename (code change, always required)**
> This is a JWT claim name change, separate from the Inbound vs. Federated App decision.
> Okta access tokens carry scopes in `scp` (JSON array). Descope uses `scope` (space-separated
> string or array). Any backend code reading `token.scp`, `claims["scp"]`, or `req.auth.scp`
> will receive `undefined` after migration and authorization checks will fail silently —
> regardless of whether Inbound or Federated Apps are used.
> **Action:** Grep for `.scp` in backend code before testing. Update all references to `.scope`
> and handle both string and array formats. This is separate from configuring Inbound Apps
> (which is about *whether* scopes are enforced, not the claim name).

> **Consideration: User profile data won't appear after login until a JWT Template is configured**
> Descope session tokens don't include `email` or `name` by default. Any UI that shows user
> profile information will show blank values after migration.
> **Action:** Configure the JWT Template in the Console before running any tests. (~10 minutes.)

> **Consideration: Password migration is blocked by Okta policy**
> Okta does not release password hashes. Password users will need to reset their passwords after
> cutover.
> **Action:** Decide on a migration strategy (reset campaign, first-login flow step, or switch
> to passwordless) before setting a cutover date.

> **Consideration: Passkeys and TOTP credentials cannot be migrated**
> Okta does not expose passkey credentials or TOTP seeds. Users who enrolled these authenticators
> in Okta must re-provision them after cutover — there is no way to migrate them silently.
> **Action:** Add a re-enrollment step to the sign-in Flow conditioned on `freshlyMigrated: true`
> and set user expectations before the cutover date.

> **Consideration: Inbound Apps vs. Federated Apps misclassification**
> If the backend validates `scp` claims from Okta access tokens and Federated Apps are configured
> instead of Inbound Apps, the backend receives tokens with no `scope` claim and all scope
> checks fail — likely silently.
> **Action:** Confirm before Console setup whether any backend service validates token scopes.
> If yes, configure Inbound Apps with scope definitions matching the Okta Authorization Server.

Include only applicable trade-offs and considerations.

---

#### Execution Plan

Phases run in sequence. Steps within a phase can run in parallel.

**Phase 1 — Console Setup** (~20–30 minutes, no code required)
Project and credentials boilerplate. Nothing here depends on the codebase.

- [ ] Create Descope project, copy Project ID
- [ ] Generate Management Key (only if the app manages users, roles, or tenants server-side)
- [ ] Enable authentication methods: (list actual methods matching Okta Authenticators found)
- [ ] Configure JWT Template with `email`, `name`, and any custom claims
- [ ] Set up Audit Connector: (Splunk / custom webhook, if Log Streams are in use)

**Phase 2 — Flow Migration** (~1–4 hours, Console only, no code required)
The core work of an Okta migration. Translate Okta authentication policies into Descope Flows
entirely through the Console — no code changes yet. Complexity scales with the number and
complexity of policy rules.

- [ ] Fetch Sign-On Policies: `GET /api/v1/policies?type=ACCESS_POLICY` — review all rules
- [ ] Create Descope Flow for each Sign-On Policy (start from `sign-up-or-in` template; add Condition branches per rule)
- [ ] Fetch Authenticator Enrollment Policies: `GET /api/v1/policies?type=MFA_ENROLL` — note required vs. optional factors
- [ ] Add MFA steps or subflows to sign-in Flow for each required factor
- [ ] Fetch Global Session Policies: `GET /api/v1/policies?type=OKTA_SIGN_ON` — note session lifetime values
- [ ] Set session lifetime in Console → Project Settings → Session Management to match
- [ ] Configure Tenant SSO: (list actual IdPs found, if any)
- [ ] Create roles: (list actual roles found)

**Phase 3 — Code Changes** (~X–Y hours, 1 engineer)

- [ ] Update environment variables in `.env.example` and CI config
- [ ] Replace Okta SDK imports with Descope SDK
- [ ] Rewrite session validation middleware
- [ ] Add `/login` page with `<Descope>` component (or web component)
- [ ] Update protected route guards
- [ ] Update logout handler (two steps: SDK call + cookie clear)
- [ ] Update `scp` → `scope` claim references in backend code
- [ ] Compile check and fix any type errors before proceeding

**Phase 4 — User Migration** (~1–2 hours)
Run import against dev/staging before production. Do not run against production until Phase 5 passes.

**Phase 5 — Testing** (~30–45 minutes)

- [ ] Compilation passes with zero errors
- [ ] Server starts, no crashes on startup
- [ ] Unauthenticated routes redirect to login correctly
- [ ] Login flow completes, user profile data appears
- [ ] Logout invalidates session
- [ ] `scope` claim (not `scp`) is present if scopes are used

**Phase 6 — Production Cutover**
- [ ] (cutover-specific steps based on their strategy)

---

Total estimated engineering effort: **N–N hours** across N engineers.
Blocking dependencies: (list anything on the critical path)

---

After writing `MIGRATION-PLAN.md`, **stop and tell the user:**

> `MIGRATION-PLAN.md` has been written to your working directory. It maps every auth
> touchpoint found, lists what needs Console setup before the first test, and calls out
> trade-offs and considerations that could affect the timeline.
>
> Take a look before we start making changes. When you're ready to proceed, say so.

Do not proceed to Part 3 unless the user confirms.

---

## Part 3: Execution

Execute the Execution Plan from `MIGRATION-PLAN.md` (the final section, Phase 1 through 6). Follow the detailed guidance below for each step.

---

### Context Continuity Protocol

Context can be lost between turns. These rules keep the migration coherent.

**Step 3.0 — Create `MIGRATION-STATE.md` before touching any code.**

Write `MIGRATION-STATE.md` to the working directory from the template below.

```markdown
# Migration State

_Last updated: [timestamp of last completed step]_

## Project Context
- Framework: [e.g., Next.js 14, Express + React]
- Language: [TypeScript / Python / Go]
- Package manager: [npm / yarn / pnpm / pip / etc.]
- Login mode: [Redirect (OIDC path) / Embedded (Descope Flow component)]
- App type in Descope Console: [Federated App / Inbound App]
- Migration path: [OIDC endpoint swap / Embedded Flow component / Full SDK replacement]
- Migration goal: [Full cutover / Phased / Evaluating]

## Triage Answers
- Existing users: [Yes — N users / No — greenfield]
- Password migration strategy: [Reset campaign / First-login step / Passwordless]
- Okta features in use: [comma-separated list]
- Multiple environments: [Yes: dev/staging/prod / No]
- Zero-downtime required: [Yes / No]

## Files Inventory
_All files that need to change. Update status after each step._

| File | Change | Status |
|---|---|---|
| `middleware/auth.ts` | Replace okta-jwt-verifier with Descope SDK | ⬜ Pending |
| `src/App.tsx` | Replace Security/OktaAuth provider | ⬜ Pending |

## Console Setup Checklist
- [ ] Descope project created — Project ID: (fill in when done)
- [ ] JWT Template configured
- [ ] Auth methods enabled: (list)
- [ ] Roles created: (list)
- [ ] Tenant SSO configured: (list IdPs)

## Decisions Log
_Non-obvious decisions made during migration._

_(none yet)_

## Current Phase
Phase 1 — Console Setup (not started)

## Next Action
Complete Phase 1 Console Setup, then Phase 2 Flow Migration (policy translation in Console) before touching any code.

## Blockers
_(none)_
```

---

**Rule 1 — Re-read before every turn.**

At the start of every execution turn, re-read `MIGRATION-PLAN.md` and `MIGRATION-STATE.md`
before writing any code or making any decision.

**Rule 2 — Verify context before every code change.**

Output a context line before each code change:

> `Migration context: Next.js 14 · Inbound Apps · Phase 2, step 4/9 · Next: update scp→scope in middleware.ts`

If this line can't be filled in accurately, re-read the files first.

**Rule 3 — Update `MIGRATION-STATE.md` immediately after each step.**

Mark the file done in the Files Inventory, update "Current Phase" and "Next Action", and
append any non-obvious decision to the Decisions Log.

---

## Pre-Generation Protocol (apply before writing any code)

Run before generating any import, wrapper type, or helper. Skipping produces code that
compiles but fails at runtime.

**1. Verify SDK exports before writing any import.**
When the Docs MCP is available, use `ask-question-about-descope` to confirm the exact method name, option shape, and return type before writing any SDK call. Do not write a method name and add a hedge like "verify the exact name" — just verify it.

When the Docs MCP is unavailable: resolve the package's type declarations (`node_modules/<pkg>/dist/types/` or its `package.json` `types` field) and confirm the exact exported name and signature.

**Prefer local `node_modules/` over GitHub** when reading type declarations. Installed packages reflect the exact version in use. Install the Descope package first if not yet installed, then read local type declarations.

**1a. After rewriting any module, grep for remaining Okta imports.**
```bash
grep -r "@okta\|okta-auth-js\|okta-jwt-verifier" --include="*.ts" --include="*.tsx" --include="*.js" .
```
Add remaining hits to the work list.

**2. Derive wrapper types from the actual return type.**
Read the function's declared return type and build the wrapper to match. Okta's field names,
nesting, and flags differ — don't infer from them.

**3. Check dependency versions before generating framework-specific code.**
For Next.js: `cookies()` and `headers()` from `next/headers` are synchronous in v14 and
async in v15. Read `package.json` first.

**4. When making a helper async, propagate to all callers immediately.**
In TypeScript, `async` on a shared utility silently breaks callers that omit `await`. Grep
for all call sites of the changed function and update them in the same pass.

**5. Verify published package versions before writing to `package.json` or running `npm install`.**
```bash
npm view @descope/node-sdk version
npm view @descope/nextjs-sdk version
npm view @descope/react-sdk version
```
If npm is unavailable, leave the version as `"latest"` and flag it.

---

## Step 1.5: Descope Project Setup & Console Configuration

Use `AskUserQuestion` to ask whether they already have a Project ID and working Flow. If
yes, skip to verifying items 5–7.

### 1. Create a project and get your Project ID
- Sign in at [console.descope.com](https://console.descope.com)
- Your **Project ID** appears in the top-left project selector and under **Project → Settings**. It starts with `P` (e.g. `P2abc123...`).
- For Next.js client-side code: `NEXT_PUBLIC_DESCOPE_PROJECT_ID`. For all server-side SDKs: `DESCOPE_PROJECT_ID`.

### 2. Get a Management Key (if needed)
Required for: user management API, role/permission management, tenant operations, SCIM configuration.
- Console → **Company → Management Keys → Generate Key**
- Store as `DESCOPE_MANAGEMENT_KEY`. Never expose client-side.

### 3. Choose or create a Flow
- Console → **Authentication → Flows**
- The built-in **"sign-up-or-in"** flow handles email OTP, magic link, social, and passkeys. Use it for most migrations.
- To customize: duplicate "sign-up-or-in", rename it, then edit in the visual builder.
- 100+ Flow templates in the library — check for an existing template before building from scratch. See `references/flows-and-widgets.md` → Flows.

### 4. Configure authentication methods
- Console → **Authentication** → select methods matching Okta Authenticators in use
- Passkeys (FIDO2 WebAuthn), TOTP, Email OTP/Magic Link, SMS OTP
- Note: Okta Verify push notifications have no direct equivalent — plan a replacement

### 5. Configure a JWT Template (almost always needed)
Okta ID tokens include `email` and `name` by default. Descope does not.
- Console → **Project Settings → JWT Templates → + JWT Template → User JWT**
- Under **Custom Claims**, add each with **Type: Dynamic**: `email` → `user.email`, `name` → `user.name`, `picture` → `user.picture`
- For custom Okta Expression Language claims: recreate them with Type: Dynamic, value `user.customAttributes.X`
- Without this step, any code reading `token.email` will get `undefined` after migration.

### 6. Create roles in the Console (if using Groups for RBAC)
Descope roles are referenced by **name**, not ID. They must be created in the Console before
the code that assigns them will work.
- Console → **Authorization → RBAC → + Role**

### 7. Define custom attributes (if using Okta user/group metadata)
Okta user profile custom attributes map to Descope `customAttributes`. Pre-define them before
setting them via the SDK.
- Console → **Project → Custom Attributes**

### 8. Env var summary

| Variable | Where to get it | Used by |
|---|---|---|
| `DESCOPE_PROJECT_ID` | Console → Project Settings | All server-side SDKs |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value as above | Next.js `AuthProvider` (client-side) |
| `DESCOPE_MANAGEMENT_KEY` | Console → Company → Management Keys | Management SDK |

### 9. Consider Widgets for management UI

Before migrating custom profile pages or user management pages, ask whether a Descope Widget
covers the use case. See `references/flows-and-widgets.md` → Widgets.

---

## Step 2: Framework-Specific Migration

Read `references/implementation-nuances.md` in two passes before writing any code:

1. **General Insights** (always) — architecture, Inbound vs. Federated Apps decision, scp/scope claim, feature mapping, gotchas.
2. **Framework section** — read only the section matching the user's stack:
   - React + `@okta/okta-react` → `## React + @okta/okta-react` in `implementation-nuances.md`
   - Angular + `@okta/okta-angular` → `## Angular + @okta/okta-angular` in `implementation-nuances.md`
   - Vue + `@okta/okta-vue` → `## Vue + @okta/okta-vue` in `implementation-nuances.md`
   - Node.js / Express + `@okta/oidc-middleware` → `## Node.js / Express + @okta/oidc-middleware` in `implementation-nuances.md`
   - Backend JWT validation only → `## Backend JWT validation (okta-jwt-verifier)` in `implementation-nuances.md`
   - Next.js → `## Next.js` in `implementation-nuances.md`
   - Custom/open-source OIDC client → `## Custom / open-source OIDC clients` in `implementation-nuances.md`
   - **Python** (Flask / FastAPI / Django) → `references/backend-sdks.md` → Python section
   - **Java** (Spring Boot / standalone) → `references/backend-sdks.md` → Java section

---

## Step 2.5: Non-Code File Updates

Scan for Okta references in non-code files after updating source files.

### `.env.example` / `.env.template` / `.env.sample`
```
# REMOVE
OKTA_CLIENT_ID=
OKTA_CLIENT_SECRET=
OKTA_ISSUER=
OKTA_DOMAIN=
OKTA_AUDIENCE=
OKTA_REDIRECT_URI=

# ADD
DESCOPE_PROJECT_ID=                  # Console → Project Settings
NEXT_PUBLIC_DESCOPE_PROJECT_ID=      # Next.js only — same value as above
DESCOPE_MANAGEMENT_KEY=              # Console → Company → Management Keys (if using management SDK)
```
Run `grep -r "OKTA"` to find all env var references — `.env.example`, Docker, CI, shell scripts.

### README / docs
Search all `.md` files for Okta references. At minimum, update:
- **Setup section** — replace "create an Okta application" instructions with Descope Console setup steps
- **Environment variables section** — reflect the reduced env var set
- **Auth flow diagrams or descriptions** — update to reflect Descope's embedded approach

### Docker / CI files
Check `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, and any CI config for
`OKTA_*` env var declarations. Update them to `DESCOPE_*`.

---

## Step 3: Feature Migration Mapping

### Authentication Policies → Descope Flows

Okta has **three distinct policy types**, each with a different Descope migration target. Treat them separately — don't collapse them into a single "Flows" step.

#### Sign-On Policies (per-app) → Flow

Sign-On Policies define per-app rule chains: which factors are required, in what order, and under which conditions (group membership, network zone, device trust). Each rule becomes a Condition branch or auth step in a Descope Flow.

Fetch before building:
```bash
curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=ACCESS_POLICY"
```

| Okta Sign-On Policy rule | Descope Flow equivalent |
|---|---|
| Require factor X | Auth method step in Flow |
| Condition: user in group Y | Condition branch on `user.roles` |
| Condition: network zone | Condition branch on IP/request context |
| Post-auth custom logic (Inline Hook) | Flow Scriptlet or Generic HTTP Connector |

One Sign-On Policy typically maps to one Flow. Complex branching logic (multiple rules with different factor requirements per condition) maps to Conditions + subflows.

#### Authenticator Enrollment Policies → Flow (MFA step or subflow)

Authenticator Enrollment Policies control when users must enroll in MFA and which factors are required vs. optional. In Descope, enrollment happens **inline in the sign-in Flow**, not through a separate enrollment journey.

Fetch before building:
```bash
curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=MFA_ENROLL"
```

Read the policy's `required` vs `optional` authenticator list, then add an MFA step to the sign-in Flow for required factors, or use a subflow triggered by a condition (e.g., user is in an admin group) for context-sensitive enrollment.

#### Global Session Policies → Project session config

Global Session Policies control session lifetime, idle timeout, and re-authentication frequency. These map to Descope's project-level session settings, not to Flows.

Fetch before configuring:
```bash
curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=OKTA_SIGN_ON"
```

In Descope: Console → **Project Settings → Session Management**. Map Okta fields to Descope fields correctly: `maxSessionLifetimeMinutes` → **Refresh Token Timeout** (total logged-in duration); `maxSessionIdleMinutes` → **Session Inactivity** (idle timeout). These are different fields — do not conflate them.

---

### Authenticators → Auth Methods

| Okta Authenticator | Descope Auth Method |
|---|---|
| Passkeys (FIDO2 WebAuthn) | Passkeys |
| TOTP (Google Authenticator, Okta Verify TOTP) | TOTP |
| Password | Password |
| Phone (SMS, Voice) | SMS OTP |
| Email (magic link or OTP) | Email OTP / Magic Link |
| Okta Verify (push) | No direct equivalent — replace with Email Magic Link, TOTP, or Passkeys |
| Security Question | No equivalent — plan removal |

### Identity Providers → Tenant SSO

**Key selling point:** Descope can consume the existing IdP response using the same ACS URL already configured in the customer's IdP. Tenant admins do **not** need to reconfigure their SAML or OIDC settings — the migration is transparent to them. This is handled via DNS redirect at the Okta → Descope cutover. See [docs.descope.com/migrate/sso](https://docs.descope.com/migrate/sso) for the full process.

Before migrating any Management SDK SSO calls, ask whether the SSO Setup Suite eliminates the need for that code. See `references/flows-and-widgets.md` → SSO Setup Suite.

| Okta | Descope |
|---|---|
| SAML Identity Provider (per-org) | `management.sso.configureSAMLByTenant(tenantId, settings)` |
| OIDC Identity Provider (per-org) | `management.sso.configureOIDCByTenant(tenantId, settings)` |

### Authorization Servers → Resources + Inbound Apps

- Recreate the Authorization Server as a Descope Resource with the same audience string (immutable in both).
- Move scope definitions from the Authorization Server to the Inbound App.
- Move custom claims (Expression Language) from the Authorization Server to a JWT Template on the Inbound App.
- Move resource-level policies (which scopes are accessible under which conditions) to Inbound App authorization rules.

### RBAC: Groups → Descope Roles

| Okta | Descope |
|---|---|
| `req.auth.groups.includes('admin')` | `token.roles.includes('admin')` |
| Group membership via Okta | Role assignment via Management SDK or Console |
| `groups` claim in token | `roles` array in JWT (built-in) |

SDK: `descopeClient.management.role.create(name, description, permissionNames, tenantId)`

### Service Apps → Access Keys

| Okta | Descope |
|---|---|
| Service App (client ID + secret) | Access Key |
| `POST /token` (client credentials) | `descopeClient.exchangeAccessKey(accessKey)` |

### Log Streams → Audit Connectors

| Okta Log Stream | Descope Connector |
|---|---|
| Splunk Cloud | Splunk Audit Connector (OOTB — Console → Connectors) |
| Amazon EventBridge | Custom Audit Webhook Connector |
| Datadog (indirect) | Custom Audit Webhook Connector |

Set up before cutover to avoid gaps in event logging.

### Token Inline Hooks → Flow Scriptlets / Connectors

| Okta Inline Hook type | Descope equivalent |
|---|---|
| Token Inline Hook (modify claims) | Flow Scriptlet or JWT Template |
| Token Inline Hook (call external service) | Generic HTTP Connector |

### User Migration

See [docs.descope.com/migrate/okta-cis](https://docs.descope.com/migrate/okta-cis) for the authoritative guide. Three paths:

#### Path 1: Full migration (bulk export → import)

Export all users from Okta, import into Descope before cutover. Use the Descope Batch Create Users API directly.

```bash
# Export users (paginated — max 200 per page)
curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/users?limit=200"
# For next page, use ?after=${lastUserId} from the Link header
```

**Attribute mapping:**

| Okta field | Descope field |
|---|---|
| `profile.login` or `profile.email` | `loginId` (required; unique per user) |
| `profile.firstName` | `givenName` |
| `profile.lastName` | `familyName` |
| `profile.email` | `email` |
| Custom profile fields | `customAttributes` |

Import via Management SDK: `management.user.createBatch([...users])`

Set `freshlyMigrated: true` as a custom attribute on import — use this in Flow Conditions to route newly-migrated users through a first-login experience (password reset prompt, re-enrollment for TOTP/passkeys), then flip it to `false` once done.

**Alternative — own data store:** If Okta sits in front of your own database (via On-prem SCIM Server Agent or Access Gateway), you own the user data. Connect that same DB to Descope via a Generic HTTP Connector in your Flow and sever Okta from the path — no export/import needed.

#### Path 2: JIT migration (password verification)

Don't bulk-export. When a user signs in, verify their password against Okta's Authentication API, then create or link the user in Descope and issue a Descope session. The user must re-enter credentials once.

```bash
curl -X POST \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -d '{"username": "user@example.com", "password": "..."}' \
  "https://${OKTA_DOMAIN}/api/v1/authn"
```

On success: create or link the user in Descope via Management SDK, then issue a Descope session. The Okta session is retired; subsequent sign-ins go directly through Descope.

#### Path 3: Session migration (JIT without re-login)

The highest-quality zero-disruption path. Deploy a new app version using the Descope SDK with session migration enabled. When a user opens the app with an existing Okta session token, Descope validates it, provisions the user just-in-time, and issues a Descope token — no re-login, no interruption. See [docs.descope.com/migrate/session-migration](https://docs.descope.com/migrate/session-migration).

#### Password constraint (Paths 1 and 2)

Okta does not export password hashes. For full migration, plan one of:
1. Password reset campaign before cutover
2. "Set new password on first login" step in the Descope sign-in Flow (use `freshlyMigrated` condition)
3. Full switch to passwordless

#### Passkeys and TOTP cannot be migrated

Okta does not expose passkey credentials or TOTP seeds. Users who enrolled these in Okta must reprovision them in Descope. Add a re-enrollment step to the sign-in Flow conditioned on `freshlyMigrated: true`.

### Email Templates → Descope Messaging Templates
Okta email templates map to Descope [Messaging Templates](https://docs.descope.com/management/messaging-templates),
configured per authentication method in the Console.

### Custom Domains
CNAME `auth.example.com` → `cname.descope.com`, verify in Console, then pass `baseUrl` to
the Descope SDK.

---

## Step 4: Critical Gotchas (Always Cover These)

### scp vs. scope Claim
Okta access tokens use `scp` (JSON array). Descope uses `scope` (array or space-separated string).

```javascript
// Okta
token.scp.includes('read:invoices')  // JSON array

// Descope — handle both formats
const scopes = Array.isArray(token.scope) ? token.scope : (token.scope || '').split(' ')
scopes.includes('read:invoices')
```

This is a silent correctness bug — not a compile error. Grep for `scp` in all backend code.

### JWT Claims Are Not the Same
Descope session JWTs contain `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions`, and `dct`
by default. They do **not** contain `email`, `name`, or `picture`. Okta ID tokens include
these by default.

**Action required:** Configure a JWT Template before any testing.

### Audience Validation Is Opt-In
Descope session tokens have no `aud` claim by default. Apps using `OKTA_AUDIENCE` for
API access control must configure a custom `aud` claim in JWT Templates and pass `audience`
to `validateSession()`.

### Logout Is Two Steps
1. Call `descopeClient.logout(refreshToken)` to invalidate server-side
2. Clear `DS` and `DSR` cookies

Skipping either step leaves a broken state.

### Server-Side Profile Updates Don't Immediately Reflect in the Session Token
Profile changes via the Management SDK don't update the JWT already in the browser. Options:

1. **Wait for auto-refresh** (~5 min default) — no code required; tolerable for most apps.
2. **`useDescope().refresh()` client-side** — triggers an immediate token refresh.
3. **User Profile Widget** — if building a profile edit page, the Widget handles updates and refresh automatically.

### Cookie Names Are Configurable
Default: `DS` (session JWT), `DSR` (refresh JWT). Configure custom names in the Descope
Console under the Flow's End action when running multiple Descope projects on the same root domain.

### One Token, Not Two
Okta issues separate ID tokens and access tokens. Descope has one token: the session JWT
(`DS` cookie). Forward it as `Authorization: Bearer <DS>` to API servers.

### No Drop-In Middleware
Descope has no `@okta/oidc-middleware` equivalent. The middleware is ~20 lines of custom code
(see `references/implementation-nuances.md` → Node.js / Express section).

### `cookies()` and `headers()` Are Async in Next.js 15
Check `package.json` for the Next.js version. If ≥ 15: write `await cookies()` and mark
the containing function `async`. This cascades to all callers — grep for all call sites.

### Dual Token Validation During Phased Rollouts
During any gradual cutover, the backend will receive both Okta JWTs (from users not yet migrated) and Descope tokens (from users already migrated). If you don't handle both, migrated users break on un-updated backends and vice versa.

Inspect the token's issuer (`iss`) or key ID (`kid`) to determine the provider, then route to the correct validator:
- Okta tokens: `iss` is `https://YOUR_DOMAIN.okta.com/oauth2/...`
- Descope tokens: `iss` is `https://api.descope.com/YOUR_PROJECT_ID`

This dual-validation window can be as short as one deployment cycle or as long as weeks depending on rollout speed. Remove the Okta validator once all sessions have expired or been migrated.

See [docs.descope.com/migrate/session-migration#step-1-dual-token-validation-in-your-backend](https://docs.descope.com/migrate/session-migration#step-1-dual-token-validation-in-your-backend).

### Env Var Reduction
Okta: `CLIENT_ID`, `CLIENT_SECRET`, `ISSUER`, `AUDIENCE`, `REDIRECT_URI` (5+).
Descope: `DESCOPE_PROJECT_ID` only (+ `DESCOPE_MANAGEMENT_KEY` for management ops).

---

## Step 5: Automated Testing

Run the app and verify it works — don't just hand over a checklist.

### Phase 0: Final stale-import sweep (BLOCKING)

```bash
grep -r "@okta\|okta-auth-js\|okta-jwt-verifier\|okta-signin-widget\|OKTA_" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
  .
```

If this returns any results, **stop and fix them before proceeding**.

### Phase 1: Install, compile, and start

```bash
npm install   # or: pip install -r requirements.txt / go mod tidy
```

```bash
npx tsc --noEmit    # TypeScript
go build ./...      # Go
```

**Do not proceed until compilation exits with zero errors.**

**If compilation fails, diagnose by error message:**
- `Cannot find module '@okta/...'` → stale import; re-run Phase 0
- `Property 'X' does not exist on type 'AuthenticationInfo'` → wrapper built against Okta shape; re-derive
- `'await' expression is not allowed in synchronous contexts` → async cascade gap
- `Object is possibly 'undefined'` on session fields → add null check or early return

```bash
npm run dev   # or: go run . / python main.py
```

### Phase 2: Run existing tests

```bash
npm test   # or: pytest / go test ./...
```

Auth-related test failures usually mean: a mock or fixture still uses Okta shapes, or a
test validates JWT claims that are now missing (e.g., `email` without a JWT Template), or
`scp` → `scope` claim wasn't updated in the test fixture.

### Phase 3: Smoke test the running app

```bash
# Root path
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/

# Unauthenticated protected route (expect 302 or 401)
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/dashboard

# Login page loads Descope component
curl -s http://localhost:<port>/login | grep -i "descope"

# Invalid token → 401
curl -s -H "Cookie: DS=invalid_token" http://localhost:<port>/api/me
```

### Phase 4: Verify JWT claims

```bash
echo "<DS_cookie_value>" | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

Check that `email`, `name`, and custom claims are present. Verify `scope` claim (not `scp`)
is present if scopes are in use.

### Phase 5: Report results

```
## Test Results

**Server startup:** ✅ Started successfully on port 3000
**Existing tests:** ✅ 12 passed / ❌ 2 failed (list failures)
**Unauthenticated /dashboard:** ✅ 302 → /login
**Unauthenticated /api/protected:** ✅ 401
**Login page loads Descope component:** ✅
**JWT claims (email, name):** ✅ Present / ❌ Missing — JWT Template not yet configured
**scope claim (not scp):** ✅ Present / ❌ Missing — update backend scope-validation code

**Blockers before going live:**
- [ ] (list anything that failed or needs manual action)
```

**Do not proceed to Step 6 until ALL of the following are true:**
- [ ] Phase 0 grep returns zero Okta references
- [ ] Phase 1 compilation passes with zero errors
- [ ] Phase 1 server starts and stays running
- [ ] Phase 3 root path returns 2xx or 3xx (not 5xx)
- [ ] Phase 3 protected routes return 302 or 401 (not 500)

---

## Step 6: Post-Migration Summary (Required)

Every migration produces a `MIGRATION-SUMMARY.md` covering what was done, manual setup
remaining, and behavioral differences that matter before production.

### MIGRATION-SUMMARY.md

1. **What was migrated** — a table mapping each Okta CIS concept to its Descope replacement

2. **Behavioral differences and open questions** — numbered list of significant differences
   between the Okta and Descope implementations. For each item: Okta behavior, Descope
   behavior, action required.

3. **Pre-deploy checklist** — actionable checkbox items for everything that must happen
   before the migrated app can run. Prominently include all Console setup tasks.

---

## Step 7: Output Format

Write a numbered migration guide in Markdown, scoped to the user's stack. Use code
snippets and direct doc links. Always include the MIGRATION-SUMMARY.md deliverable (Step 6).

For complex migrations (Token Inline Hooks, custom Expression Language claims, complex
Sign-On Policy rule chains), flag the high-effort items explicitly with estimated complexity
(Low/Medium/High) so the user can plan.

---

## Reference Files

- `references/implementation-nuances.md` — Verified migration patterns, code-level diffs, and edge cases for each JS/TS framework and Okta CIS feature.
- `references/flows-and-widgets.md` — Okta→Descope lingo map, Flow structure, Widgets, SSO Setup Suite, Console-vs-code decision guide.
- `references/backend-sdks.md` — Python and Java backend migration patterns (Flask, FastAPI, Django, Spring Boot, management SDK, M2M access keys).
- Descope Docs: https://docs.descope.com
- Descope Migration Guide: https://docs.descope.com/migrate
- Descope OIDC Endpoints: https://docs.descope.com/getting-started/oidc-endpoints
- Descope Flows: https://docs.descope.com/flows
- JWT Templates: https://docs.descope.com/management/jwt-templates
- Access Keys (M2M): https://docs.descope.com/management/m2m-access-keys
- Messaging Templates: https://docs.descope.com/management/messaging-templates
- Audit Webhook: https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook
- Custom Domains: https://docs.descope.com/how-to-deploy-to-production/custom-domain
- ReBAC: https://docs.descope.com/authorization/rebac
- Session Migration: https://docs.descope.com/migrate/session-migration

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

### Okta CIS Reference
- Authenticators overview: https://developer.okta.com/docs/guides/authenticators-overview/main/
- Policies concept: https://developer.okta.com/docs/concepts/policies/
- Policy Management API: https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Policy/
- Authorization Servers: https://developer.okta.com/docs/concepts/auth-servers/
- Identity Providers: https://help.okta.com/oie/en-us/content/topics/security/identity_providers.htm
- Log Streams: https://help.okta.com/oie/en-us/Content/Topics/Reports/log-streaming/about-log-streams.htm
- Client Credentials (M2M): https://developer.okta.com/docs/guides/implement-grant-type/clientcreds/main/
