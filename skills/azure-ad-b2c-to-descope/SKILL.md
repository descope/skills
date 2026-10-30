---
name: azure-ad-b2c-to-descope
description: >
  Use this skill whenever anyone asks about migrating from Azure AD B2C (Azure Active Directory B2C)
  to Descope — whether they're a developer doing it themselves or a technical lead evaluating the
  move. Triggers on: "migrate from Azure AD B2C", "replace Azure B2C with Descope", "we're moving
  off B2C", "B2C end of sale", "Azure AD B2C to Descope", "our app uses @azure/msal-browser /
  @azure/msal-react / @azure/msal-angular / @azure/msal-node / Microsoft.Identity.Web /
  passport-azure-ad with b2clogin.com and we want to use Descope instead", or any question about
  B2C features (user flows, custom policies / Identity Experience Framework, API connectors,
  b2c-extensions-app custom attributes, identity providers, ROPC, embedded sign-in, scp claim) in
  the context of Descope. Works for any language or framework with a Descope SDK. Always use this
  skill before producing migration guidance — do not rely on memory alone.
---

# Azure AD B2C → Descope Migration Skill

This skill guides self-service migrations from Azure AD B2C to Descope. It runs in three parts:

1. **MCP Check** — confirm whether the Descope Docs MCP is available and suggest installing it if not
2. **Migration Plan** — gather context via triage questions, analyze the codebase and (optionally) the B2C tenant, and produce a human-readable `MIGRATION-PLAN.md` for the user to review
3. **Execution** — if the user confirms they want to proceed, execute the plan

Do not collapse these parts or skip ahead. The plan must be reviewed before code changes begin.

**Scope:** Azure AD B2C only. Microsoft Entra External ID and workforce Microsoft Entra ID are
different products — if detection shows either, stop and say this skill does not cover it.

**Primary references** (all in this skill's directory):
- `references/implementation-nuances.md` — B2C → Descope feature mapping, token gotchas, framework sections (MSAL React, Angular, Next.js, Vue, plain JS, server-side web apps), user migration, enterprise SSO migration
- `references/flows-and-widgets.md` — B2C → Descope lingo, Flow structure and templates, Widgets, SSO Setup Suite, Console-vs-code decision guide
- `references/backend-sdks.md` — backend migration patterns: .NET (`Microsoft.Identity.Web`), Node.js, Python, Java
- `references/b2c-detection-patterns.md` — code search patterns, read-only Microsoft Graph discovery of the B2C tenant, out-of-scope detection, evidence template

---

## Guiding Principles

**Console-first.** Before recommending SDK code for any user-facing auth feature, check whether
the Console, a Flow, or a Widget covers the use case. B2C teams configure auth through user flows
in the Azure portal or custom policy XML (Identity Experience Framework). Descope Flows replace
both — visually, without XML or policy uploads. Engineers integrate once (SDK setup + token
validation). Later auth changes — new methods, MFA changes, branding — happen in the Console.
See `references/flows-and-widgets.md` → Console vs. Code.

**Ask, don't assume.** At every design decision — login mode, which Descope app type, password
strategy, where roles come from, SSO cutover — use `AskUserQuestion` rather than proceeding with
an assumption. A wrong assumption compounds across 20+ files.

**MCP over memory.** When the Docs MCP is available (confirmed in Part 1), use
`ask-question-about-descope` to verify every SDK method name, option shape, and return type
before writing it. Do not write a method name and add a hedge like "verify the exact name" —
verify it.

**B2C configuration often lives outside the repo.** User flows, custom policies, identity
providers, API connectors, and app registrations live in the Azure portal. Read them from the
tenant (read-only Microsoft Graph, see `references/b2c-detection-patterns.md`) or ask the user
for the custom policy XML files. Do not infer the auth experience from code alone.

---

## DO NOT

- **Do not reconfigure MSAL to point at Descope** — including `protocolMode: "OIDC"` in
  `@azure/msal-browser` / `@azure/msal-node`. Microsoft documents that mode as limited support.
  Always replace MSAL with the Descope SDK or a standard OIDC library.
- **Do not promise a no-reconfiguration enterprise SSO cutover by default.** It only works for
  SAML connections whose old ACS URLs are on a domain the customer controls. Build the
  per-connection inventory first (Step 1c) and state which customer IdP admins must act.
- **Do not plan to export B2C secrets or private keys.** Microsoft Graph returns `****` for
  identity provider client secrets and marks policy key values (`k`, `d`, `p`, `q`…) as not
  readable. Plan for new secrets/certificates instead.
- **Do not plan to import password hashes.** B2C does not export them. Use a reset, passwordless,
  or JIT path (see User Migration).
- **Do not promise passkey or TOTP migration.** Neither can be moved; users re-enroll.
- **Do not key migrated users on email when the app's database keys on the B2C `oid`.** Carry
  `oid` over as a custom attribute and emit it via JWT Template.
- **Do not import an enterprise SSO user into more than one tenant** unless the user explicitly
  asks — Descope only converts single-tenant users on first SSO login by default; multi-tenant
  conversion carries cross-tenant takeover risk.
- **Do not read `scp`, `tfp`, `acr`, `emails`, or `oid` from Descope tokens.** Map each claim (see
  Step 4: Critical Gotchas).
- **Do not write to the B2C tenant.** All tenant discovery is read-only.
- **Do not skip `aud` validation for Inbound App tokens.** Validate against the Resource identifier, not the project ID.
- **Do not expose `DESCOPE_MANAGEMENT_KEY` or Inbound App client secrets client-side.**
- **Do not import users into production before dev/staging imports and sign-in tests pass.**

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

## Part 1.5: Scope Guard (BLOCKING)

Before triage, confirm the app uses Azure AD B2C. Quick check: grep for the login host
(`b2clogin.com`, `B2C_1`, `AzureAdB2C`). If the authority is `*.ciamlogin.com` (Microsoft Entra
External ID) or plain `login.microsoftonline.com/<tenant>` without a B2C policy (workforce Entra
ID), stop and tell the user this skill does not cover it. See `references/b2c-detection-patterns.md`
→ Out-of-Scope Detection.

---

## Part 2: Migration Plan

Part 2 has these sub-steps:

1. **Triage** — ask the questions needed to understand scope
2. **Engineer review checkpoint** — surface blockers
3. **Discovery** — scan the codebase, optionally read the B2C tenant, build the SSO inventory
4. **Plan file** — produce `MIGRATION-PLAN.md` and pause for review

### Step 0: Triage (BLOCKING — requires `AskUserQuestion`)

**Use the `AskUserQuestion` tool to gather the information below. Do not infer answers from
memory, prior conversations, or assumptions — even if you think you know.**

Do not proceed to Step 0.5 until the user has answered.

**Decision 0 — How users log in today (resolve this first):**

> "How does the app send users to B2C today? (a) MSAL redirect or popup to the B2C-hosted page
> (`loginRedirect`, `loginPopup`, `MsalProvider`, `b2clogin.com`), (b) a server-side web app using
> OpenID Connect middleware (`Microsoft.Identity.Web`, `passport-azure-ad`, `msal-node`),
> (c) B2C embedded sign-in in an iframe (custom policy with `JourneyFraming`), or (d) a native/mobile
> app that collects the password itself (ROPC)?"

Decision tree:
```
Login mode today?
├── (a) MSAL redirect/popup (SPA)            → Descope-hosted login (default)
│     React, Angular, Next.js, plain JS      → Descope SDK with oidcConfig + sdk.oidc.loginWithRedirect()
│     Vue                                    → Descope SDK with oidcConfig (type cast) + manual
│                                              sdk.oidc.finishLoginIfNeed() on the redirect page
│     Customer asks for in-page login        → Embedded <Descope flowId="..."/> instead
├── (b) Server-side web app (OIDC middleware) → Standard OIDC library pointed at Descope
│                                              (.NET OpenIdConnect, openid-client, Authlib, Spring)
├── (c) B2C iframe embedded sign-in          → Embedded <Descope flowId="..."/> (customer chose in-page login)
└── (d) ROPC native app                      → Descope native SDK / native Flows (adds MFA + passkeys)
```

`loginPopup` / `acquireTokenPopup` users move to the redirect: Descope-hosted login is
redirect-based.

Rule of thumb: **Descope-hosted login by default** — B2C users already redirect to
`b2clogin.com`, so a hosted page is the smallest UX change. Use an embedded Flow only for B2C
iframe users or when the customer asks for it.

---

**Decision 1 — Which Descope app the login goes through:**

> "Does the app's frontend call its own API with B2C access tokens (it requests a scope like
> `https://<tenant>.onmicrosoft.com/api/tasks.read` and the API checks `scp` / `[RequiredScope]`)?
> Are there other callers — partner apps, scripts, background services using client credentials,
> AI agents?"

Decision tree:
```
Who calls the API?
├── Own frontend with B2C scopes (most B2C apps with a backend)
│     → Inbound App for the frontend + Descope Resource for the API
│       Recreate the same scope names on the Resource; backend scope checks stay scope checks
│       (only the claim name changes: scp → scope)
├── Also partners / agents / CLIs
│     → One additional Inbound App per caller (consent + scoped tokens)
├── Client-credentials (M2M) apps
│     → Inbound App with client credentials (not Access Keys)
└── No API, or API only checks "signed in"
      → Federated App (standard OIDC library) or plain Descope SDK session
```

**Embedded Flow + scoped API:** an embedded Flow (B2C iframe users, or on request) issues a
Descope **session token** — `aud` is the project ID and there is no `scope` claim. Either keep
hosted login through the Inbound App for apps whose API checks scopes, or map the API's scope
checks to roles/permissions in the session token. Confirm with the Docs MCP whether an embedded
Flow can issue Inbound App tokens before promising scopes.

Descope-hosted login with an Inbound App uses the Inbound App's `issuer` and `clientId` in
`oidcConfig` (the issuer is shown on the Inbound App settings page — do not construct it).
Verify the current `oidcConfig` shape with the Docs MCP before writing code.

Do not proceed until both decisions are resolved.

---

**Remaining triage — first `AskUserQuestion` call (up to 4 questions):**

1. **Frontend and backend stack** — React, Angular, Next.js, Vue, plain JS, .NET, Node.js, Python, Java, mobile.
2. **Migration goal** — full cut-over, phased, or evaluating.
3. **Users** — consumers, business customers who log in with their company SSO, or both? Roughly how many?
4. **Policy type** — user flows (`B2C_1_…`), custom policies (`B2C_1A_…`), or both? Can they share the custom policy XML files, or grant read-only Graph access to the tenant?

**Second `AskUserQuestion` call — B2C features in use (`multiSelect: true`):**

- Custom policies with REST technical profiles or API connectors (after IdP federation, before user creation, before token issuance)
- Social identity providers (Google, Facebook, Apple, Microsoft accounts)
- Enterprise identity providers (customer Entra ID, SAML IdPs, multi-tenant Entra `common`)
- MFA (SMS/voice, email OTP, authenticator app TOTP)
- Conditional Access (require MFA / block)
- Custom user attributes (`extension_*`)
- Roles or groups in tokens (custom attribute, API connector, Graph `memberOf`)
- Custom page layouts (HTML/CSS/JS templates)
- Custom domain (B2C on `login.<company>.com` instead of `<tenant>.b2clogin.com`)
- Embedded sign-in (iframe), ROPC
- Client-credentials (M2M) app registrations
- Passkeys/FIDO2 via Microsoft's sample or a partner (Nok Nok, Authsignal, Transmit)

Follow up on anything selected. After both calls, summarize findings and flag high-complexity
items (custom policies with many REST technical profiles, many enterprise IdPs, roles built via
API connectors) before Step 0.5.

---

### Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

Ask even the ones you think you know. Batch into calls of up to 4 questions. Skip clearly
inapplicable ones.

**Identity and data**
- Does the app's database key users on the B2C object ID (`oid` / `sub`)? If yes, plan to carry it as a custom attribute (e.g. `b2cObjectId`) plus a JWT Template claim.
- Where do roles come from today: a custom attribute, the app's own database (possibly injected via an API connector), Graph groups, or nowhere?
- Do any B2C "groups" or customer IdPs actually represent customer organizations? (They become Descope tenants.)

**Enterprise SSO** (if enterprise IdPs are in use)
- Does the B2C tenant use a custom domain, and are the existing customer IdPs configured with URLs on that domain or on `b2clogin.com`?
- For OIDC enterprise connections: do they still have the client secrets their customers issued, stored outside B2C? (B2C cannot return them.)
- For enterprise users, does B2C add its own MFA after the company login, skip it, or skip it only when the company IdP already did MFA (`amr` contains `mfa`)?

**Passwords and sessions** (if existing users)
- Password strategy: full import without passwords (reset or passwordless), JIT via ROPC (keeps passwords; B2C stays running), or JIT with B2C as an OIDC provider.
- Can users be asked to log in again at cutover, or is session migration required?

**Deployment**
- Multiple environments (dev / staging / prod)? Each needs its own Descope project.
- Multiple services validating B2C tokens, or an API gateway doing it? Each needs updating.

**Gaps to flag immediately** (don't ask — flag based on answers)
- **Password hashes cannot be exported** from B2C.
- **Passkeys and TOTP cannot be migrated** — users re-enroll after their first Descope login.
- **B2C on `b2clogin.com` + enterprise IdPs** → every customer IdP admin must update ACS/redirect URLs at cutover.
- **OIDC enterprise connections** → each customer IdP admin issues a new client secret unless the original was kept outside B2C.
- **SAML connections with signed requests or encrypted assertions** → B2C private keys can't be exported; upload the original PFX to the Descope tenant if the company still has it, otherwise the customer IdP admin trusts Descope's certificate.
- **Embedded sign-in (iframe)** → move to embedded Descope Flow; social login starts working.

**Console/Flow/Widget opportunities** (flag, then ask)
- Profile edit or user management pages → a Descope Widget may replace them.
- Custom SSO onboarding for business customers → SSO Setup Suite + Tenant Profile Widget.
- API connectors / REST technical profiles → Flow HTTP Connectors at the same point in the journey.

Summarize blockers and opportunities before discovery.

---

### Step 0.75: Fast-Track Assessment

**Fast-track — SPA with hosted login, no custom policy logic (all must be true):**
1. Decision 0 = (a) MSAL redirect/popup
2. Only user flows (no custom policies with REST technical profiles)
3. No enterprise IdPs
4. No roles built via API connectors

If all are true, the work is mostly Console setup (Flow, Inbound App + Resource or Federated App,
JWT Template) plus an SDK swap in one frontend and one backend. Keep the codebase analysis short.
Otherwise run full discovery.

---

### Step 1: Discovery

Read `references/b2c-detection-patterns.md` before this step.

**Step 1a — Code analysis.** Run the search groups in `b2c-detection-patterns.md` → Search Groups
(MSAL packages, authority/policy names, MSAL call sites, B2C-specific logic, token claims, roles,
`domain_hint`, iframe sign-in, custom policy XML). For each hit, record file:line, what it does,
and complexity (Low / Medium / High).

**Step 1b — Tenant discovery (optional, read-only).** If the user granted read-only Graph access,
run the routes in `b2c-detection-patterns.md` → Read-Only Microsoft Graph Discovery: user flows,
custom policies (download XML), identity providers, API connectors, app registrations, custom
attributes, user counts. If not, ask for the custom policy XML files and a list of identity
providers.

**Step 1c — Enterprise SSO inventory (required if enterprise IdPs are in use).** Build one row
per customer connection using `b2c-detection-patterns.md` → Evidence Recording Template:

| Customer | IdP | Protocol | Email domain(s) | ACS / redirect URL host | Signed requests / encrypted assertions | OIDC secret available outside B2C | Cutover result |
|---|---|---|---|---|---|---|---|

Cutover result rules:
- URL host is `*.b2clogin.com` → **customer IdP admin must update URLs**
- SAML on a customer-controlled domain, no signing/encryption dependency → **may move without IdP changes** (DNS redirect, see [docs.descope.com/migrate/sso](https://docs.descope.com/migrate/sso))
- SAML with signed requests / encrypted assertions and no original key file → **admin must trust Descope's certificate**
- OIDC without the original secret → **admin must issue a new client secret**

If the Descope Docs MCP is available, verify SDK method names you plan to reference.

---

### Step 2: Write MIGRATION-PLAN.md

Write `MIGRATION-PLAN.md` to the working directory. Two audiences: the engineer needs enough
detail to execute; the PM or tech lead needs scope, risk, and timeline without jargon. Use plain
English, explain terms on first use, open each section with a one-sentence summary, say what
breaks if a risk is missed, pair complexity with time estimates.

Sections, in this order:

#### Overview
2–3 sentences: what's replaced, what replaces it, the recommended approach. Then:

| | |
|---|---|
| **Login** | Descope-hosted (via Inbound App / Federated App) / Embedded Flow |
| **API authorization** | Inbound App + Resource (scopes kept) / Session token only |
| **Files changing** | N files across N areas |
| **Console setup** | N steps |
| **User impact** | Re-login once / password reset / no change |
| **Enterprise customers affected** | N of N customer IdP admins must act (from Step 1c) |
| **Estimated effort** | N–N hours |
| **Biggest risk** | One sentence |

#### What's Changing and Why
Prose: today B2C hosts login via user flows / custom policies, issues ID + access tokens per
policy, and validates them through `Microsoft.Identity.Web` / MSAL; after migration Descope does
each of these. List B2C features in use in plain English.

#### Auth Touchpoints: What the Code Analysis Found
Group by area (frontend login, token acquisition, backend validation, claims, roles, config).
Table per group: File | What it does today | What changes. End with total and effort.

#### Feature Migration: Azure AD B2C → Descope
One short paragraph per confirmed feature: goal, best Descope approach (Flow, Widget, SSO Setup
Suite, Console, or SDK), differences, action, effort. Use the feature-mapping sections of
`references/implementation-nuances.md` (User flows and custom policies → Flows through Passkeys).

#### Enterprise SSO Cutover (if applicable)
The Step 1c inventory table, the count of customer IdP admins who must act, and a draft notice to
send them in advance (what changes, new URL/certificate/secret, date).

#### Before the Code Can Run: Required Configuration
Checkboxes, "Required before any testing" and "Required before production":
- [ ] Create Descope project(s)
- [ ] Create the Flow(s) replacing each user flow / custom policy journey
- [ ] Create the Resource (same scope names as the B2C API registration) and the Inbound App for the frontend — or a Federated App for server-side OIDC without scopes
- [ ] Configure a JWT Template: `email`, `name`, `b2cObjectId` (if keyed on `oid`), custom attributes
- [ ] Enable auth methods matching B2C (password, email OTP, SMS, TOTP, social providers)
- [ ] Create roles/permissions (if roles were built in B2C)
- [ ] Create tenants + SSO per enterprise customer (before importing their users)
- [ ] Custom domain, if B2C used one

#### Environment Variables

| Remove | Add | Why |
|---|---|---|
| `AzureAdB2C:Instance`, `Domain`, `TenantId`, policy IDs (`SignUpSignInPolicyId`, `ResetPasswordPolicyId`, `EditProfilePolicyId`) | `DESCOPE_PROJECT_ID` | One project replaces tenant + per-policy authorities |
| B2C `ClientId` (SPA / web app) | Inbound App or Federated App client ID / issuer | Copy from the app's settings page in the Console |
| B2C `ClientSecret` (confidential web apps) | Inbound App secret, or Access Key for a Federated App | New credential — B2C secrets aren't reused |
| API `ClientId` / App ID URI / `Scopes` | Resource identifier (audience) + scope names | Backend validates `aud` = Resource |
| — | `DESCOPE_MANAGEMENT_KEY` | Only for user/tenant/role management |

#### User Migration (if existing users)
Start with the user count and chosen password strategy. See
`references/implementation-nuances.md` → User Migration for the export call, field mapping,
SSO and social user recipes. PM checklist:
- [ ] Choose password strategy (reset / passwordless / JIT via ROPC / JIT via B2C as OIDC provider)
- [ ] Create custom attributes (incl. `b2cObjectId`) and tenants before import
- [ ] Export users via Microsoft Graph (`$select` incl. `identities` and `extension_*`)
- [ ] Transform and import into dev, then staging, then production
- [ ] Verify one local, one social, one enterprise SSO user end to end

#### Trade-offs and considerations
Each: **what it is**, **what breaks if ignored**, **what to do**. Always include those that apply:
- `scp` → `scope` claim name (Inbound App tokens use `scope`, space-separated — same shape as B2C `scp`)
- `oid` → Descope user ID (app database lookups break)
- `emails` array → `email` (JWT Template)
- Policy-specific code (`tfp`, `AADB2C90118`, per-policy authorities) becomes dead code
- Password hashes not exportable; passkeys/TOTP must be re-enrolled
- Enterprise IdP admins who must act (from Step 1c)
- Dual-token validation during phased rollout

#### Execution Plan
- **Phase 1 — Console setup** (~30–60 min): project, auth methods, JWT Template, Resource + Inbound App / Federated App, roles, custom attributes
- **Phase 2 — Flow migration** (~1–6 h): one Flow per user flow / custom policy journey; API connectors → HTTP Connectors; MFA steps; branding from page layouts
- **Phase 3 — Tenants and SSO** (if enterprise): one tenant per customer connection, SSO config, domains, MFA-for-SSO-users rule
- **Phase 4 — Code changes**: remove MSAL / Microsoft.Identity.Web; add Descope SDK or OIDC library; backend validation; claim updates
- **Phase 5 — User migration**: dev → staging → prod
- **Phase 6 — Testing**
- **Phase 7 — Cutover**: customer IdP admin notices, DNS redirect (if eligible), dual-token window, decommission B2C policies

Total effort and blocking dependencies at the end.

After writing `MIGRATION-PLAN.md`, **stop and tell the user:**

> `MIGRATION-PLAN.md` has been written to your working directory. It maps every auth touchpoint
> found, lists the Console setup needed before the first test, shows which enterprise customers'
> IT admins will need to make changes, and calls out trade-offs that could affect the timeline.
>
> Take a look before we start making changes. When you're ready to proceed, say so.

Do not proceed to Part 3 unless the user confirms.

---

## Part 3: Execution

Execute the Execution Plan from `MIGRATION-PLAN.md`, following the guidance below.

### Context Continuity Protocol

**Step 3.0 — Create `MIGRATION-STATE.md` before touching any code:**

```markdown
# Migration State

_Last updated: [timestamp]_

## Project Context
- Frontend / backend: [e.g., React 18 + ASP.NET Core 8]
- Login mode: [Descope-hosted via Inbound App / Federated App / Embedded Flow]
- API authorization: [Inbound App + Resource / session token]
- Migration goal: [Full cutover / Phased / Evaluating]

## Triage Answers
- Users: [consumers / business SSO / both — N users]
- Policy type: [user flows / custom policies / both]
- Password strategy: [...]
- Keyed on oid: [Yes / No]
- Roles source: [...]
- Enterprise connections: [N — N need admin action]

## Files Inventory
| File | Change | Status |
|---|---|---|

## Console Setup Checklist
- [ ] Project — Project ID:
- [ ] Flows:
- [ ] Resource + Inbound App / Federated App:
- [ ] JWT Template:
- [ ] Roles / custom attributes:
- [ ] Tenants + SSO:

## Decisions Log
_(none yet)_

## Current Phase
Phase 1 — Console Setup (not started)

## Next Action
## Blockers
```

**Rule 1** — Re-read `MIGRATION-PLAN.md` and `MIGRATION-STATE.md` at the start of every execution turn.

**Rule 2** — Before each code change, output a context line:
> `Migration context: React + ASP.NET Core · Inbound App + Resource · Phase 4, step 3/8 · Next: replace AddMicrosoftIdentityWebApi`

**Rule 3** — Update `MIGRATION-STATE.md` immediately after each step.

---

## Pre-Generation Protocol (apply before writing any code)

1. **Verify SDK exports before writing any import.** Use the Docs MCP; without it, read the
   installed package's type declarations (`node_modules/<pkg>/dist/types/`, NuGet XML docs).
2. **After rewriting any module, grep for remaining B2C/MSAL references:**
   ```bash
   grep -rn "@azure/msal\|Microsoft.Identity.Web\|passport-azure-ad\|b2clogin.com\|B2C_1" \
     --exclude-dir=node_modules --exclude-dir=bin --exclude-dir=obj .
   ```
3. **Derive wrapper types from the Descope return types** — MSAL's `AccountInfo` /
   `AuthenticationResult` shapes don't carry over.
4. **Check framework versions** (`package.json`, `*.csproj`) before writing framework code.
   Next.js 15: `cookies()` / `headers()` are async.
5. **Propagate async changes** to every caller in the same pass.
6. **Verify published package versions** before writing them:
   ```bash
   npm view @descope/react-sdk version
   npm view @descope/node-sdk version
   dotnet package search Descope --exact-match   # .NET SDK (NuGet package: Descope)
   ```

---

## Step 1.5: Descope Project Setup & Console Configuration

Ask whether they already have a Project ID and working Flow; if yes, verify items 4–8.

1. **Project** — [app.descope.com](https://app.descope.com); Project ID under Project → Settings. One project per environment.
2. **Management Key** (if needed) — Company → Management Keys. Server-side only.
3. **Flows** — start from `sign-up-or-in`; one Flow per B2C user flow / custom policy journey (sign-up-or-in, password reset, profile edit can be one Flow with branches). Check the template library first.
4. **Auth methods** — match B2C: email + password, email OTP, SMS, TOTP, social providers (register new client IDs/secrets with Google etc.; B2C secrets can't be read).
5. **Resource + Inbound App** (Decision 1) — create the Resource with the same scope names as the B2C "Expose an API" registration (e.g. `tasks.read`); create the Inbound App for the frontend; note its issuer and client ID from the settings page. Federated App instead when no API scopes are needed.
6. **JWT Template** — Descope session tokens don't include `email`/`name` by default. Add dynamic claims: `email` → `user.email`, `name` → `user.name`, `b2cObjectId` → the user custom attribute, plus custom attributes the app reads. The template also applies to Inbound App access tokens.
7. **Roles and permissions** — Authorization → RBAC, if roles were built in B2C.
8. **Custom attributes** — define them (incl. `b2cObjectId`) before importing users.
9. **Tenants + SSO** — one tenant per enterprise customer connection, with email domains; configure SSO before importing that customer's users.
10. **Widgets** — check before migrating profile or user-management pages.

---

## Step 2: Framework-Specific Migration

Read `references/implementation-nuances.md` in two passes before writing code:

1. **General Insights** (always) — login architecture, Decision 1, token claim mapping, feature mapping, gotchas.
2. **Framework section** — only the user's stack:
   - React + `@azure/msal-react` → `### React + @azure/msal-react`
   - Angular + `@azure/msal-angular` → `### Angular + @azure/msal-angular`
   - Next.js (MSAL or NextAuth Azure AD B2C provider) → `### Next.js`
   - Vue + `@azure/msal-browser` → `### Vue + @azure/msal-browser`
   - Plain JS + `@azure/msal-browser` → `### Plain JavaScript + @azure/msal-browser`
   - B2C iframe embedded sign-in → `### Embedded sign-in (iframe) → embedded Flow`
   - Server-side web apps (`Microsoft.Identity.Web` OIDC, `msal-node`, `passport-azure-ad` OIDCStrategy) → `### Server-side web apps`
   - Mobile (`MSAL.iOS`, `MSAL Android`, ROPC) → `### Native / mobile`
   - Backends (.NET, Node.js, Python, Java) → `references/backend-sdks.md`

---

## Step 2.5: Non-Code File Updates

- **`appsettings*.json`** — remove the `AzureAdB2C` section; add a `Descope` section (`ProjectId`, Inbound App issuer/audience as needed).
- **`.env*`** — remove `AZURE_AD_B2C_*` / `B2C_*` / `MSAL_*` variables; add `DESCOPE_PROJECT_ID` (+ framework-prefixed copies, e.g. `NEXT_PUBLIC_DESCOPE_PROJECT_ID`, `VITE_DESCOPE_PROJECT_ID`).
- **Docker / CI / IaC** — update secrets and env declarations; remove B2C policy upload steps from pipelines.
- **Custom policy XML and page layout templates** — keep them until cutover for rollback; delete after B2C is decommissioned.
- **README / docs** — replace "create a B2C app registration and user flow" setup steps with Descope Console steps.

---

## Step 3: Feature Migration Mapping

Details are in the feature-mapping sections of `references/implementation-nuances.md`. Summary:

| Azure AD B2C | Descope |
|---|---|
| B2C tenant | Project (one per environment) |
| User flows (sign-up/sign-in, password reset, profile edit) | Flows |
| Custom policy user journey + orchestration steps | One Flow with steps and subflows |
| IdP technical profiles (Google, OIDC, SAML) | Social login, or tenant SSO |
| REST technical profiles / API connectors | HTTP Connector actions at the same journey point |
| Claims transformations | Scriptlets, JWT Templates |
| Page layouts (HTML/CSS/JS) | Flow screens and styles |
| MFA (SMS, email OTP, TOTP) | MFA steps in the Flow |
| Conditional Access (require MFA / block) | Flow conditions, risk connectors |
| App registration with "Expose an API" | Resource (same scope names) |
| App registration for the frontend / callers | Inbound App |
| Client-credentials app registration | Inbound App (client credentials) |
| `oid` / `sub` | Descope user ID; old `oid` as custom attribute + JWT claim |
| `extension_*` attributes | Custom attributes + JWT Template |
| Roles via custom attribute / API connector / Graph groups | Roles and permissions (per tenant if needed) |
| Per-customer IdP + `domain_hint` routing | Tenant SSO + email domains; `tenant` parameter on hosted login |
| Multi-tenant Entra (`common` + allowlist) | "Sign in with Microsoft" social login + Flow condition |
| Embedded sign-in (`JourneyFraming`) | Embedded `<Descope />` component |
| Custom domain | Descope custom domain |
| Passkeys via sample / partner | Native passkeys (users re-enroll) |

---

## Step 4: Critical Gotchas (Always Cover These)

### `oid` is the B2C user ID — Descope assigns new IDs
`sub` defaults to the B2C object ID. Apps keyed on it treat every migrated user as new. Import
`oid` into a custom attribute (`b2cObjectId`) and add it to tokens via JWT Template, or remap the
app's database before cutover.

### `scp` → `scope`
B2C access tokens carry granted scopes in `scp` as a space-separated string of short names
(`"tasks.read tasks.write"`). Descope Inbound App access tokens use `scope`, also a
space-separated string. Keep the same scope names on the Resource; update the claim name. In
.NET, `[RequiredScope]` / `VerifyUserHasAnyAcceptedScope` read `scp` and its mapped URI claim,
not `scope` — replace them with a policy that reads `scope` (see `backend-sdks.md`).

### `emails` array → `email`
B2C local accounts emit `emails` (an array). Code doing `emails[0]` gets `undefined`. Add
`email` via JWT Template and update the code.

### Policy-specific code becomes dead code
Remove: per-policy authorities, account filtering by policy name (`homeAccountId` /
`idTokenClaims.tfp` contains `B2C_1_…`), `AADB2C90118` password-reset redirects, `tfp`/`acr`
checks, per-policy metadata/JWKS URLs.

### Audience
Inbound App tokens carry the Resource identifier in `aud`; validate against it, not the project
ID. Descope session tokens carry the project ID unless a JWT Template changes it.

### Validate Inbound App tokens with the issuer and keys from discovery
Issuer is `https://api.descope.com/v1/apps/<ProjectID>` (custom client IDs:
`/v1/apps/customized/<ProjectID>`); read `issuer` and `jwks_uri` from the discovery document
rather than hardcoding. Confirm with the Docs MCP whether the Descope backend SDK's session
validation accepts Inbound App tokens; otherwise use standard JWT validation (examples in
`backend-sdks.md`).

### Secrets and keys are not exportable
Graph returns `****` for identity provider client secrets and marks policy key values as not
readable. Register new secrets with social providers; plan new secrets/certificates with
enterprise customers (Step 1c).

### Enterprise SSO users must match on first login
Create the tenant + SSO first, then import each SSO user into exactly one tenant with the login
ID Descope looks up first — `<NameID>-<tenantID>` (SAML) or `<sub>-<tenantID>` (OIDC). Otherwise
Descope creates a duplicate SSO user. Details: `implementation-nuances.md` → Enterprise SSO users.

### Dual-token validation during phased rollouts
B2C tokens: `iss` = `https://<tenant>.b2clogin.com/<tenant-guid>/v2.0/` (or the `tfp` variant /
custom domain). Descope tokens: `iss` = `https://api.descope.com/<ProjectID>` (session) or
`/v1/apps/<ProjectID>` (Inbound App). Route by exact `iss` until every client has moved to Descope and remaining B2C
sessions are revoked or expired (B2C refresh tokens: 14-day default with up to a 90-day sliding
window; SPAs 24 hours).

### Logout
Hosted (OIDC) login: `sdk.oidc.logout()` for full OIDC logout. Plain SDK sessions:
`sdk.logout()` / backend `logout(refreshToken)` and clear `DS`/`DSR` cookies.

---

## Step 5: Automated Testing

### Phase 0: Final stale-reference sweep (BLOCKING)
```bash
grep -rn "@azure/msal\|Microsoft.Identity.Web\|passport-azure-ad\|b2clogin.com\|B2C_1\|AzureAdB2C\|\.scp\b\|\"scp\"\|emails\[0\]\|AADB2C" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=bin --exclude-dir=obj .
```
Fix every hit before continuing. **Phased rollout:** the dual-token validator and the code that accepts `scp` are expected to remain — exclude those files from this sweep until B2C is decommissioned, then run the full sweep again.

### Phase 1: Install, compile, start
`npm install && npx tsc --noEmit` / `dotnet build` / `pip install -r requirements.txt` / `mvn compile`. Zero errors before continuing. Then start the app.

### Phase 2: Existing tests
Failures usually mean fixtures still use B2C claim shapes (`scp`, `emails`, `oid`, `tfp`).

### Phase 3: Smoke test
- Unauthenticated protected page → redirect to login; protected API → 401
- Login completes on the Descope-hosted page (or embedded Flow) and returns to the app
- API call with the new token succeeds; with a token missing the scope → 403
- Logout clears the session

### Phase 4: Verify token claims
Decode the access token: `iss` (Inbound App issuer), `aud` (Resource), `scope`, `email`,
`b2cObjectId`, roles. Decode a session token if the plain SDK path is used.

### Phase 5: Migrated users
Sign in as one imported local user, one social user, one enterprise SSO user — each must land on
the imported account (not a new user).

Report results in a short table with blockers before going live.

**Do not proceed to Step 6 until:** the Phase 0 sweep is clean (allowing the dual-token code in
phased mode), the build passes, the app starts, protected routes return 302/401 (not 500), and
the token claims check passes.

---

## Step 6: Post-Migration Summary (Required)

Write `MIGRATION-SUMMARY.md`:
1. **What was migrated** — B2C concept → Descope replacement table
2. **Behavioral differences and open questions** — B2C behavior, Descope behavior, action
3. **Pre-deploy checklist** — Console tasks, customer IdP admin notices, user import, cutover steps

---

## Step 7: Output Format

Write a numbered migration guide in Markdown, scoped to the user's stack, with code snippets and
direct doc links. Always include `MIGRATION-SUMMARY.md` (Step 6). Flag high-effort items
explicitly (custom policies with many REST technical profiles, many enterprise IdPs, roles built
via API connectors) with Low / Medium / High complexity.

---

## Reference Files

- `references/implementation-nuances.md`
- `references/flows-and-widgets.md`
- `references/backend-sdks.md`
- `references/b2c-detection-patterns.md`
- Descope Azure AD B2C migration guide: https://docs.descope.com/migrate/azure-ad-b2c
- Descope SSO migration: https://docs.descope.com/migrate/sso
- Descope session migration: https://docs.descope.com/migrate/session-migration
- Inbound Apps: https://docs.descope.com/identity-federation/inbound-apps
- Resources: https://docs.descope.com/resources
- Federated OIDC Apps: https://docs.descope.com/sso-integrations/applications/oidc-apps
- Auth Hosting: https://docs.descope.com/identity-federation/auth-hosting
- React OIDC quickstart: https://docs.descope.com/getting-started/react/react-oidc
- .NET SDK: https://docs.descope.com/getting-started/dotnet
- SSO settings (user conversion): https://docs.descope.com/auth-methods/sso/settings
- Flow dynamic keys (`idpOIDCClaims`, `idpSAMLAttributes`): https://docs.descope.com/flows/dynamic-keys
- JS SDKs (React, Angular, Vue, Next.js, Web JS): https://github.com/descope/descope-js

### Azure AD B2C Reference
- Tokens overview: https://learn.microsoft.com/azure/active-directory-b2c/tokens-overview
- User flows vs custom policies: https://learn.microsoft.com/azure/active-directory-b2c/user-flow-overview
- API connectors: https://learn.microsoft.com/azure/active-directory-b2c/api-connectors-overview
- Custom attributes: https://learn.microsoft.com/azure/active-directory-b2c/user-flow-custom-attributes
- ROPC: https://learn.microsoft.com/azure/active-directory-b2c/add-ropc-policy
- Embedded sign-in: https://learn.microsoft.com/azure/active-directory-b2c/embedded-login
- B2C FAQ (end of sale, support timeline): https://learn.microsoft.com/azure/active-directory-b2c/faq
