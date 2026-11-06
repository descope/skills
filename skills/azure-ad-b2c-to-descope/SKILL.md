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

This skill guides self-service migrations from Azure AD B2C to Descope, in order:

1. **Part 1 — MCP Check** and **Part 1.5 — Scope Guard** (Azure AD B2C only; not Entra External ID or workforce Entra ID)
2. **Part 2 — Migration Plan** — triage, discovery (codebase and, optionally, the B2C tenant), then `MIGRATION-PLAN.md` for the user to review
3. **Part 3 — Execution** — only after the user approves the plan
4. **Part 4 — Wrap-up** — `MIGRATION-SUMMARY.md`

Don't collapse or skip parts. The plan is reviewed before any code changes.

**Rule of this skill:** SKILL.md holds the workflow, decisions and short rules; details, tables and
code live in the references and are linked as `file.md` → Section.

**References** (in this skill's directory):
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

**Match first, then enhance.** Rebuild what B2C does today 1:1 — same sign-in methods, same
screens, same tenants and roles — so every test has one question: does the app behave the same as
before? Passkeys, adaptive MFA, or a redesigned login are post-cutover improvements: list them in
`MIGRATION-SUMMARY.md`, don't build them into the migration. See
[docs.descope.com/migrate/strategy](https://docs.descope.com/migrate/strategy).

**One app at a time, tests first.** Get automated sign-in tests running through Descope before
moving any app, then move apps one at a time. A per-app cutover keeps each change small and each
failure easy to trace.

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

- **Do not ship MSAL pointed at Descope to production.** Reconfiguring MSAL is a POC step only
  (Microsoft calls its non-Microsoft mode limited support); the plan always replaces MSAL with the
  Descope SDK or a standard OIDC library before cutover (`implementation-nuances.md` → MSAL POC
  first, then replace MSAL).
- **Do not promise a no-reconfiguration enterprise SSO cutover by default.** It only works for
  SAML or OIDC connections whose old ACS / redirect URLs are on a domain the customer controls;
  OIDC also needs the original client secret from outside B2C. Build the
  per-connection inventory first (Step 1c) and state which customer IdP admins must act.
- **Do not plan to export B2C secrets or private keys** — none can be read back
  (`implementation-nuances.md` → Secrets can't be exported).
- **Do not plan to import password hashes.** B2C does not export them. Use a reset, passwordless,
  or JIT path (see User Migration).
- **Do not promise passkey or TOTP migration.** Neither can be moved; users re-enroll.
- **Do not key migrated users on email when the app keys on the B2C `oid`.** Follow
  `implementation-nuances.md` → User ID strategy.
- **Do not import an enterprise SSO user into more than one tenant** unless the user explicitly
  asks — multi-tenant conversion carries cross-tenant takeover risk
  (`implementation-nuances.md` → Enterprise SSO users).
- **Do not read `scp`, `tfp`, or `emails` from Descope tokens.** Map each claim (see Execution Phase 4d:
  Critical Gotchas). `oid` is the exception: keep the claim name when the JWT Template emits it.
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

> **Descope Docs MCP is not installed.** This skill uses it to check current SDK methods and
> features; without it, guidance may be stale. Install it at **https://docs-mcp.descope.com/**
> (server URL `https://docs-mcp.descope.com/mcp`).
>
> **Install it before we continue, or proceed without it?**

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

No evidence either way — for example B2C on a custom domain (`login.<company>.com`), or the
authority kept in Key Vault, app settings or a deployment pipeline rather than the repo — ask the
user with `AskUserQuestion` whether the app uses Azure AD B2C, Entra External ID, or workforce Entra
ID. Proceed only on an explicit "Azure AD B2C".

---

## Part 2: Migration Plan

Part 2 has these sub-steps:

1. **Step 0 — Triage** — three decisions, then the remaining questions
2. **Step 0.5 — Engineer review checkpoint** — detailed questions; surface blockers
3. **Step 0.75 — Fast-track assessment**
4. **Step 1 — Discovery** — codebase, optional read-only tenant discovery, SSO inventory
5. **Step 2 — `MIGRATION-PLAN.md`** — write it and pause for review

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
├── (a) MSAL redirect/popup (SPA)            → Descope-hosted login: Descope SDK with oidcConfig
│                                              (per-SDK notes: implementation-nuances.md → Hosted login by default)
│     Customer asks for in-page login        → Embedded <Descope flowId="..."/> instead
├── (b) Server-side web app (OIDC middleware) → Standard OIDC library pointed at Descope
│                                              (.NET OpenIdConnect, openid-client, Authlib, Spring)
├── (c) B2C iframe embedded sign-in          → Embedded <Descope flowId="..."/> (customer chose in-page login)
└── (d) ROPC native app                      → Descope native SDK / native Flows (MFA and passkeys
                                               can follow after cutover)
```

`loginPopup` / `acquireTokenPopup` users move to the redirect: Descope-hosted login is
redirect-based.

**POC with MSAL first — always offer it.** For MSAL.js (browser, React, Angular, Node) and
MSAL.NET apps, ask:

> "Do you want to start with a proof of concept that keeps MSAL and only changes its configuration
> to point at Descope, then replace MSAL with the Descope SDK? Or replace MSAL straight away?"

If yes, the plan runs the MSAL POC first and the SDK replacement afterwards, both before
production cutover (`implementation-nuances.md` → MSAL POC first, then replace MSAL). Apps on
`Microsoft.Identity.Web` or native MSAL go straight to their replacement — say so.

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
│     → Confidential Inbound App with client credentials (not Access Keys)
└── No API, or API only checks "signed in"
      → Federated App (standard OIDC library) or plain Descope SDK session
```

**Inbound App rules** (details: `implementation-nuances.md` → Which Descope app):
- No consent screen for first-party users: **Update User Consent** with **Scopes auto approval**
  (→ Consent for first-party Inbound Apps).
- Take the issuer from a real token — never construct it or copy it from the settings page
  (→ Finding the Inbound App issuer).
- Send the Resource on both requests: `loginWithRedirect({ resource, extraTokenParams: { resource } })`
  (→ Selecting the Resource).
- An embedded Flow issues a session token (no `scope`) and can't mint Inbound App access tokens —
  keep hosted login for scoped APIs (→ Embedded Flows and scoped APIs).

---

**Decision 2 — What "tenant" means in their B2C setup:**

Customers use "tenant" for two different things. Ask, don't assume:

> "When you say 'tenant', which do you mean? (a) separate B2C directories — one per environment,
> brand, or region (`contoso-dev.onmicrosoft.com`, `contoso-eu.onmicrosoft.com`), (b) one B2C
> directory where customer organizations are separated inside your custom policies (per-customer
> identity providers, `domain_hint`, a tenant or organization claim, an API connector lookup),
> (c) both, or (d) no customer separation?"

Decision tree:
```
What is a "tenant"?
├── (a) Separate B2C directories           → One Descope project per directory, each in the
│                                            directory's region (Step 0.5 → Deployment)
├── (b) Customer orgs inside custom policies → Descope tenants in one project
│                                            Record how the policy identifies the org today
│                                            (domain_hint, claim, lookup) — the Flow does the same
│                                            with tenant selection or email-domain routing
├── (c) Both                               → Projects per directory, tenants inside each
└── (d) No separation                      → One project, no tenants
```

Dev / staging / prod directories are case (a) even when the customer doesn't call them tenants.

Each B2C app registration then maps to one Descope app by platform type
(`b2c-detection-patterns.md` → App registration type → Descope app).

Do not proceed until all three decisions are resolved.

---

**Remaining triage — first `AskUserQuestion` call (up to 4 questions):**

1. **Frontend and backend stack** — React, Angular, Next.js, Vue, plain JS, .NET, Node.js, Python, Java, mobile.
2. **Migration goal** — full cut-over, phased, or evaluating.
3. **Users** — consumers, business customers who log in with their company SSO, or both? Roughly how many?
4. **Where sign-in logic lives** — user flows (`B2C_1_…`), custom policies (`B2C_1A_…`, Identity Experience Framework), Conditional Access policies, or a mix? Discovery reads every place they name. Can they share the custom policy XML files, or grant read-only Graph access to the tenant?

**Second `AskUserQuestion` call — B2C features in use.** Four `multiSelect: true` questions with
four options each (the tool allows at most four options per question):

| Question | Options |
|---|---|
| Journeys and identity | Custom policies with REST technical profiles / API connectors · Social IdPs (Google, Facebook, Apple, Microsoft) · Enterprise IdPs (customer Entra ID, SAML, multi-tenant `common`) · MFA or Conditional Access |
| Users and data | Custom attributes (`extension_*`) · Roles or groups in tokens · Passkeys via Microsoft's sample or a partner · Invitations or custom verification / reset emails |
| Hosting and UX | Custom page layouts · Custom domain (Azure Front Door) · Non-default languages (`ui_locales`) · Embedded iframe sign-in or ROPC |
| Apps and security | Client-credentials (M2M) apps · B2C issuing SAML to the customer's apps · An app-launcher portal (Azure My Apps or custom) · Fraud controls (risk policies, CAPTCHA, fraud vendors, phone country limits, smart lockout) |

Follow up on anything selected. After both calls, summarize findings and flag high-complexity
items (custom policies with many REST technical profiles, many enterprise IdPs, roles built via
API connectors) before Step 0.5.

---

### Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

Ask even the ones you think you know. Batch into calls of up to 4 questions. Skip clearly
inapplicable ones.

**Policies and journeys**
- List every user flow and custom policy, which apps call it, and whether it is per app, per
  customer organization, or shared. This decides how many Flows to build.
- Does the app choose the journey by calling a specific policy (the policy name in the authority
  URL or the `p=` parameter), or does one policy branch internally on its inputs (`domain_hint`,
  client ID, a query parameter, a claim from an API connector)?
- Does app code read `tfp` / `acr` after login and act on it (for example "came back from
  profile edit", "came back from password reset")?

Decision tree:
```
How is the journey chosen?
├── App picks the policy                  → One Flow per journey
│     Sign-up / sign-in (+ password reset)  → One login Flow. Hosted login runs the Flow set in
│                                           that app's Flow Hosting settings (one per app);
│                                           embedded login sets the flowId prop
│     Profile edit, change MFA, etc.       → User Profile Widget or an embedded Flow in the app,
│                                           not a second hosted login
├── One policy branches on inputs         → One Flow with conditions on the same inputs
│                                           (form fields, query params, connector results)
└── Both                                  → Map each policy separately using the two rules above
App code reads tfp / acr?
├── Only to handle AADB2C90118 / B2C redirects → Delete it; Descope returns from the Flow directly
└── Real branching on which journey ran      → Add a claim in each Flow with the Custom Claims
                                               action and read that claim instead
```

**Apps** (skip if Step 1b will read app registrations through Graph)
- List each B2C app registration: its platform (SPA, web, mobile/desktop, or none), whether it
  has a client secret or certificate, and whether it requests delegated scopes or application
  permissions (`.default`) on the API.
- Is the implicit grant enabled on any of them (ID tokens or access tokens)?

**Identity and data**
- Which systems key users on the B2C object ID, and does the code read `oid`, `sub`, or both?
  Which strategy: **keep the B2C ID**, **switch to the Descope user ID**, or **remap on first
  login** (`implementation-nuances.md` → User ID strategy)?
- Can every user ID column and downstream system store a string? New users' IDs aren't GUIDs —
  if not, "keep the B2C ID" is blocked (→ App changes when keeping the B2C ID).
- Where do roles come from (custom attribute, app database via API connector, Graph groups,
  nowhere), and how do users get them (portal admin, Graph calls, a policy step, a sync job, the
  customer's IdP)? (`implementation-nuances.md` → Roles and groups)
- Do any B2C "groups" or customer IdPs actually represent customer organizations? (They become Descope tenants.)

**Enterprise SSO** (if enterprise IdPs are in use)
- Does the B2C tenant use a custom domain, and are the existing customer IdPs configured with URLs on that domain or on `b2clogin.com`?
- For OIDC enterprise connections: do they still have the client secrets their customers issued, stored outside B2C? (B2C cannot return them.)
- For enterprise users, does B2C add its own MFA after the company login, skip it, or skip it only when the company IdP already did MFA (`amr` contains `mfa`)?

**Passwords and sessions** (if existing users)
- Password strategy: full import without passwords (reset or passwordless), JIT via ROPC (keeps passwords; B2C stays running), or JIT with B2C as an OIDC provider.
- Session behavior per policy (lifetimes, rolling/absolute, "Keep me signed in", SSO scope):
  do policies differ, and by app or by customer? Which actions send users back to B2C to re-enter
  credentials (they become step-up)? Do apps on different root domains share one session?
  (`implementation-nuances.md` → Session behavior and token lifetimes)
- Can users sign in again at cutover? Plan for it — B2C session migration needs Descope Support
  to confirm first (→ Password strategy).

**Deployment**
- Multiple environments (dev / staging / prod)? Each needs its own Descope project.
- **Data residency:** where is each B2C directory's data stored (tenant overview → country/region),
  and must it stay there? Create each Descope project in the matching region — US, EU, AP (Sydney),
  CA, UK, SG or SA — before any import. The region is fixed at creation and needs a Growth or
  Enterprise plan ([multi-region](https://docs.descope.com/management/project-settings/multi-regional)).
- Multiple services validating B2C tokens, or an API gateway doing it? Each needs updating.
- Where do B2C audit and sign-in logs go, and what depends on them? (→ Audit and sign-in logs)
- Does B2C run on a custom domain, and what else does its Azure Front Door profile do (WAF, rules)?
  (`implementation-nuances.md` → Custom domain on Azure Front Door)
- How many apps sign in through B2C (MSAL apps, server-side web apps, SAML apps), and can they move one at a time?
- Is a new hostname available for Descope during the move (e.g. `auth.<company>.com`), separate from the hostname B2C uses today? The two-stage cutover needs it.

**Gaps to flag immediately** (don't ask — flag based on answers)
- No password hashes, passkeys or TOTP carry over (see DO NOT).
- Enterprise IdP admins who must act — `b2clogin.com` URLs, OIDC secrets, SAML signing keys
  (`implementation-nuances.md` → Per-connection inventory and cutover rules).
- **Embedded sign-in (iframe)** → embedded Descope Flow; social login starts working.

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
5. Decision 2 = (d), or (a) where the directories are only dev / staging / prod

If all are true, the work is mostly Console setup (Flow, Inbound App + Resource or Federated App,
JWT Template) plus an SDK swap in one frontend and one backend. Keep the codebase analysis short.
Otherwise run full discovery.

---

### Step 1: Discovery

Read `references/b2c-detection-patterns.md` before this step.

**Step 1a — Code analysis.** Run the search groups in `b2c-detection-patterns.md` → Search Groups
(MSAL packages, authority/policy names, MSAL call sites, B2C-specific logic, token claims, roles,
`domain_hint`, iframe sign-in, custom policy XML, user IDs stored or parsed as GUIDs). Record each
hit as the search groups describe.

**Step 1b — Tenant discovery (optional, read-only).** If the user granted read-only Graph access,
run the routes in `b2c-detection-patterns.md` → Read-Only Microsoft Graph Discovery: user flows,
custom policies (download XML), identity providers, API connectors, app registrations, custom
attributes, Conditional Access policies, user counts. If not, ask for the custom policy XML
files, a list of identity providers, and each Conditional Access policy's conditions and grant
(require MFA / block).

Also build, from the same sources:
- **Sign-in methods** — the union of the tenant's identity providers, user flows' providers, and
  the IdPs custom policy journeys actually reach (`b2c-detection-patterns.md` → Sign-in method
  inventory).
- **Policy keys** in use and their expiry (`implementation-nuances.md` → Policy key inventory).
- **Session settings, SAML relying parties, fraud controls, localized strings** — read from the
  portal or policy XML (`b2c-detection-patterns.md` → Custom Policy XML Hints).

**Step 1c — Enterprise SSO inventory (required if enterprise IdPs are in use).** One row per
customer connection (`b2c-detection-patterns.md` → Evidence Recording Template), with a cutover
result from `implementation-nuances.md` → Per-connection inventory and cutover rules.

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

#### Journeys: B2C Policies → Descope Flows
One row per user flow / custom policy from Step 0.5:
| B2C policy | Called by (apps) | Scope (app / customer / shared) | How the journey is chosen | Descope Flow ID | Notes (branches, `tfp`/`acr` consumers) |
|---|---|---|---|---|---|

#### Sign-in Methods
One row per method from the Step 1b inventory:
| Method | Defined in (tenant list / policy XML) | Offered by (policies) | Descope equivalent | Credential to re-obtain |
|---|---|---|---|---|

#### Policy Keys (custom policies)
| Keyset (`B2C_1A_…`) | Used by (policy / technical profile) | Purpose | Expires | Descope action | Who provides the credential |
|---|---|---|---|---|---|

#### Other Inventories (include those that apply)
One table each, built in Step 1; the reference section names the columns:
- **Session behavior** — one row per policy: B2C values → Descope setting and level (`implementation-nuances.md` → Session behavior and token lifetimes)
- **Sensitive actions** — each action that re-prompts for credentials → step-up (→ Split-clock setups → step-up)
- **User schema** — attribute, type, where collected / returned / read, placement (→ User schema)
- **SAML apps** — B2C SAML relying parties (→ B2C as a SAML IdP → Descope SAML app)
- **Fraud controls** — each B2C control and its Descope replacement (→ Fraud and risk detection)
- **Localized strings** — languages and the B2C `StringId` → screen-text mapping (→ Localization)
- **App launcher tiles** — app, protocol, launch URL, assignments (→ App launcher portal (Azure My Apps))

#### Feature Migration: Azure AD B2C → Descope
One short paragraph per confirmed feature: goal, best Descope approach (Flow, Widget, SSO Setup
Suite, Console, or SDK), differences, action, effort (`implementation-nuances.md` → Feature Mapping).

#### Cutover Strategy
**Direct, per app** or **two-stage broker**, and why (`implementation-nuances.md` → Cutover
strategy). List the apps in the order they move, with the test each must pass.

#### Enterprise SSO Cutover (if applicable)
The Step 1c inventory table, the count of customer IdP admins who must act, and a draft notice to
send them in advance (what changes, new URL/certificate/secret, date).

#### Before the Code Can Run: Required Configuration
Checkboxes, "Required before any testing" and "Required before production":
- [ ] Create Descope project(s) in the region matching each B2C directory's data location (fixed at creation)
- [ ] Create the Flow(s) replacing each user flow / custom policy journey
- [ ] Create the Resource (same scope names as the B2C API registration) and the Inbound App for the frontend — or a Federated App for server-side OIDC without scopes
- [ ] Configure a JWT Template: `email`, `name`, `oid` (and `sub` if needed — User ID strategy), custom attributes
- [ ] Enable auth methods matching B2C (password, email OTP, SMS, TOTP, social providers)
- [ ] Create roles/permissions (if roles were built in B2C)
- [ ] Create tenants + SSO per enterprise customer (before importing their users)
- [ ] Descope custom domain (a subdomain of the app's site); recreate any Front Door WAF rules as Flow rate limits, Lists and fraud protection
- [ ] Audit connector (or Audit Webhook) to wherever B2C logs go today, before cutover

#### Environment Variables

| Remove | Add | Why |
|---|---|---|
| `AzureAdB2C:Instance`, `Domain`, `TenantId`, policy IDs (`SignUpSignInPolicyId`, `ResetPasswordPolicyId`, `EditProfilePolicyId`) | `DESCOPE_PROJECT_ID` | One project replaces tenant + per-policy authorities |
| B2C `ClientId` (SPA / web app) | Inbound App or Federated App client ID / issuer | Client ID from the app's settings page; Inbound App issuer from a real token (`implementation-nuances.md` → Finding the Inbound App issuer) |
| B2C `ClientSecret` (confidential web apps) | Inbound App secret, or Access Key for a Federated App | New credential — B2C secrets aren't reused |
| API `ClientId` / App ID URI / `Scopes` | Resource identifier (audience) + scope names | Backend validates `aud` = Resource |
| — | `DESCOPE_MANAGEMENT_KEY` | Only for user/tenant/role management |

#### User Migration (if existing users)
Start with the user count and chosen password strategy (`implementation-nuances.md` → User
Migration). PM checklist:
- [ ] Choose password strategy (reset / passwordless / JIT via ROPC / JIT via B2C as OIDC provider)
- [ ] Choose user ID strategy (keep the B2C ID / switch to Descope user ID / remap on first login), decide what new users get, and list every system keyed on the B2C ID
- [ ] Build the user schema table; create typed custom attributes (incl. `b2cObjectId`) and tenants before import
- [ ] Export users via Microsoft Graph (`$select` incl. `identities` and `extension_*`)
- [ ] Transform and import into dev, then staging, then production
- [ ] Verify one local, one social, one enterprise SSO user end to end

#### Trade-offs and considerations
Each: **what it is**, **what breaks if ignored**, **what to do**. Include every Execution Phase 4d
gotcha that applies, plus the enterprise IdP admins who must act (Step 1c).

#### Execution Plan
- **Phase 1 — Console setup** (~30–60 min): project, auth methods, JWT Template, Resource + Inbound App / Federated App, roles, custom attributes
- **Phase 2 — Flow migration** (~1–6 h): one Flow per user flow / custom policy journey; API connectors → HTTP Connectors; MFA steps; branding from page layouts
- **Phase 3 — Tenants and SSO** (if enterprise): one tenant per customer connection, SSO config, domains, MFA-for-SSO-users rule
- **Phase 4 — Code changes**: MSAL POC first if chosen (MSAL pointed at Descope, B2C policy logic removed, backend validation, claims), then replace MSAL / Microsoft.Identity.Web with the Descope SDK or an OIDC library
- **Phase 5 — User migration**: dev → staging → prod
- **Phase 6 — Testing**
- **Phase 7 — Cutover**: per the Cutover Strategy; dual-token window; decommission B2C policies

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

**First — create `MIGRATION-STATE.md` before touching any code:**

```markdown
# Migration State

_Last updated: [timestamp]_

## Project Context
- Frontend / backend: [e.g., React 18 + ASP.NET Core 8]
- Login mode: [Descope-hosted via Inbound App / Federated App / Embedded Flow]
- API authorization: [Inbound App + Resource / session token]
- Migration goal: [Full cutover / Phased / Evaluating]
- MSAL POC first: [Yes / No — stage: POC / SDK replacement]

## Triage Answers
- Users: [consumers / business SSO / both — N users]
- Sign-in logic: [user flows / custom policies (IEF) / Conditional Access — list all that apply]
- Password strategy: [...]
- User ID strategy: [keep B2C ID / switch / remap on first login]
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

### Pre-Generation Protocol (apply before writing any code)

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

### Execution Phases 1–3: Console Setup, Flows, Tenants and SSO

Ask whether they already have a Project ID and working Flow; if yes, verify items 3–9.

1. **Project** — [app.descope.com](https://app.descope.com); Project ID under Project → Settings. One project per environment.
2. **Management Key** (if needed) — Company → Management Keys. Server-side only.
3. **Flows** — start from `sign-up-or-in`; one Flow per B2C user flow / custom policy journey (sign-up-or-in, password reset, profile edit can be one Flow with branches). Check the template library first.
4. **Auth methods** — match B2C: email + password, email OTP, SMS, TOTP, social providers (register new client IDs/secrets with Google etc.; B2C secrets can't be read).
5. **Resource + Inbound App** (Decision 1) — Resource with the B2C scope names (e.g. `tasks.read`); Inbound App for the frontend (public client with PKCE for an SPA), following the Inbound App rules under Decision 1. Federated App instead when no API scopes are needed.
6. **JWT Template** — `email` → `user.email`, `name` → `user.name` (not in Descope tokens by default), `oid` / `sub` per the User ID strategy, and custom attributes the app reads. It also applies to Inbound App access tokens.
7. **Roles and permissions** — Authorization → RBAC, if roles were built in B2C.
8. **Custom attributes** — define them (incl. `b2cObjectId`) before importing users.
9. **Tenants + SSO** — one tenant per enterprise customer connection, with email domains; configure SSO before importing that customer's users.
10. **Widgets** — check before migrating profile or user-management pages.

---

### Execution Phase 4a: Framework-Specific Migration

If the MSAL POC was chosen, do it first (`implementation-nuances.md` → MSAL POC first, then
replace MSAL), run its checklist with the user, then come back here for the SDK replacement.

Read `references/implementation-nuances.md` in two passes before writing code:

1. **Architecture** and **Feature Mapping** (always).
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

### Execution Phase 4b: Non-Code File Updates

- **`appsettings*.json`** — remove the `AzureAdB2C` section; add a `Descope` section (`ProjectId`, Inbound App issuer/audience as needed).
- **`.env*`** — remove `AZURE_AD_B2C_*` / `B2C_*` / `MSAL_*` variables; add `DESCOPE_PROJECT_ID` (+ framework-prefixed copies, e.g. `NEXT_PUBLIC_DESCOPE_PROJECT_ID`, `VITE_DESCOPE_PROJECT_ID`).
- **Docker / CI / IaC** — update secrets and env declarations; remove B2C policy upload steps from pipelines.
- **Custom policy XML and page layout templates** — keep them until cutover for rollback; delete after B2C is decommissioned.
- **README / docs** — replace "create a B2C app registration and user flow" setup steps with Descope Console steps.

---

### Execution Phase 4c: Feature Migration Mapping

B2C concept → Descope: `flows-and-widgets.md` → Terminology. How to build each one:
`implementation-nuances.md` → Feature Mapping.

---

### Execution Phase 4d: Critical Gotchas (Always Cover These)

#### `oid` is the B2C user ID — Descope assigns new IDs
Apps keyed on `oid` / `sub` treat every migrated user as new unless the JWT Template carries the B2C
ID over, and new users' IDs aren't GUIDs (`implementation-nuances.md` → User ID strategy).

#### `scp` → `scope`
B2C access tokens carry granted scopes in `scp` as a space-separated string of short names
(`"tasks.read tasks.write"`). Descope Inbound App access tokens use `scope`, also a
space-separated string. Keep the same scope names on the Resource; update the claim name. In
.NET, `[RequiredScope]` / `VerifyUserHasAnyAcceptedScope` read `scp` and its mapped URI claim,
not `scope` — replace them with a policy that reads `scope` (see `backend-sdks.md`).

#### `emails` array → `email`
B2C local accounts emit `emails` (an array). Code doing `emails[0]` gets `undefined`. Add
`email` via JWT Template and update the code.

#### Policy-specific code becomes dead code
Remove: per-policy authorities, account filtering by policy name (`homeAccountId` /
`idTokenClaims.tfp` contains `B2C_1_…`), `AADB2C90118` password-reset redirects, `tfp`/`acr`
checks, per-policy metadata/JWKS URLs.

#### Validate `iss` and `aud` on Inbound App tokens
Take the issuer from discovery, never hardcoded (`implementation-nuances.md` → Finding the Inbound
App issuer), and check `aud` = the Resource. .NET and Java SDKs check neither, and Python rejects
Inbound App tokens without `audience` (`backend-sdks.md` → Which token does the API receive?).

#### Secrets and keys are not exportable
Plan new or re-obtained credentials (`implementation-nuances.md` → Secrets, Certificates and Policy Keys).

#### Enterprise SSO users must match on first login
Create the tenant + SSO first, then import each SSO user into one tenant with the login ID Descope
looks up — `<NameID>-<tenantID>` (SAML) or `<claim mapped to Login ID>-<tenantID>` (OIDC) — or
Descope creates a duplicate (`implementation-nuances.md` → Enterprise SSO users).

#### Dual-token validation during phased rollouts
Route by exact `iss` (configured values, not hardcoded) until every client is on Descope and B2C
sessions have expired; size the window from the tenant's refresh-token settings
(`backend-sdks.md` → Dual-token validation during rollout).

#### Profile changes show up after the next refresh
In B2C, a profile-edit user flow redirects back with a fresh ID token, so the app sees new values
immediately. In Descope, claims backed by user attributes update when the session next refreshes.
After a profile update (Flow, User Profile Widget, or Management API), either wait for the SDK's
automatic refresh or call the SDK's refresh (for example `useDescope().refresh()` in React) before
reading the new claims.

#### Cookie names
If tokens are delivered as cookies, Descope uses `DS` (session) and `DSR` (refresh). Rename them in
the Flow's End action when several Descope projects share one root domain (for example dev and prod
under `example.com`), and update any backend or gateway code that reads the cookie by name.

#### Audit and sign-in logs
Set up an audit connector before cutover (`implementation-nuances.md` → Audit and sign-in logs).

#### Logout
Hosted (OIDC) login: `sdk.oidc.logout()` for full OIDC logout. Plain SDK sessions:
`sdk.logout()` / backend `logout(refreshToken)` and clear `DS`/`DSR` cookies.

---

### Execution Phase 5: User Migration (run by the team)
The agent doesn't import users. When asked, prepare the export and transform scripts from
`implementation-nuances.md` → User Migration and run them against the dev
project only. Staging and production imports are run by the team, in that order, after dev sign-in
tests pass.

### Execution Phase 6: Testing

#### Test 1: Final stale-reference sweep (BLOCKING)
Scan app code and config only — not this skill's own `MIGRATION-*.md` files or the custom policy
XML kept for rollback:
```bash
grep -rnI "@azure/msal\|Microsoft.Identity.Web\|passport-azure-ad\|b2clogin.com\|B2C_1\|AzureAdB2C\|\.scp\b\|\"scp\"\|emails\[0\]\|AADB2C" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.mjs" --include="*.vue" \
  --include="*.cs" --include="*.py" --include="*.java" --include="*.kt" --include="*.swift" --include="*.go" \
  --include="*.json" --include="*.env*" --include="*.yml" --include="*.yaml" --include="*.properties" \
  --include="*.config" --include="Dockerfile" \
  --exclude="MIGRATION-*.md" --exclude="package-lock.json" --exclude="*.lock" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=bin --exclude-dir=obj --exclude-dir=.git .
```
Fix every hit before continuing. **MSAL POC stage:** `@azure/msal` hits are expected until the SDK
replacement — the sweep must be clean before cutover. **Phased rollout:** the dual-token validator and the code that
accepts `scp` are expected to remain — exclude those files until B2C is decommissioned, then run the
full sweep again. Delete the rollback policy XML after decommission.

#### Test 2: Install, compile, start
`npm install && npx tsc --noEmit` / `dotnet build` / `pip install -r requirements.txt` / `mvn compile`. Zero errors before continuing. Then start the app.

#### Test 3: Existing tests
Failures usually mean fixtures still use B2C claim shapes (`scp`, `emails`, `oid`, `tfp`).

#### Test 4: Checks the agent runs
Without a browser login, check what `curl` can prove:
- The Descope discovery document loads: `curl -s <issuer>/.well-known/openid-configuration` returns
  200, and its `issuer` equals the issuer the app is configured with.
- An unauthenticated protected page redirects (302) to the Descope host — not to `b2clogin.com`.
- A protected API returns 401 with no token and with a malformed token — never 500.

#### Test 5: Checks that need a real sign-in (human checklist)
The agent can't complete an interactive login, and Part 3 doesn't import users. List these in
`MIGRATION-SUMMARY.md` under **Not yet verified — needs a person**, with exact steps:
- Login completes on the Descope-hosted page (or embedded Flow) and returns to the app.
- API call with the new token succeeds; with a token missing the scope → 403. After the access token
  refreshes, `aud` is still the Resource (the SDK's refresh call doesn't send `resource`). If every call returns
  403, check the token's `scope` first — an Inbound App Flow without Scopes auto approval or the
  Inbound App Scopes component issues tokens with no scopes.
- Logout clears the session.
- Token claims: `iss` (Inbound App issuer), `aud` (Resource), `scope`, `email`, `oid` (and `sub` if
  overridden — Descope's ID is then in `dsub`), roles. Check one migrated user (B2C GUID) and one new
  user (Descope `U…` ID), and confirm the new user's row is created in the app's database. If the
  user pastes a token from a test login, decode it and check these claims for them.
- After the user import (Execution Phase 5): sign in as one imported local user, one social
  user, one enterprise SSO user — each must land on the imported account, not a new user.
- An M2M Inbound App client-credentials token is accepted by the API.
- During a phased rollout, the dual-token validator accepts both B2C and Descope tokens.

Report results in a short table: what the agent verified, what's left for a person, and blockers
before going live.

**Do not proceed to Part 4 (Wrap-up) until:** the Test 1 sweep is clean (allowing the dual-token code in
phased mode), the build passes, the app starts, and the Test 4 checks pass. Test 5 items don't
block the wrap-up — they move to the summary as not yet verified.

---

### Execution Phase 7: Cutover (run by the team)
Follow the Cutover Strategy in `MIGRATION-PLAN.md` (`implementation-nuances.md` → Cutover strategy).
The agent can draft the customer IdP admin notices and the cutover checklist; DNS changes, Worker
deployment and B2C decommissioning are done by the team. No app goes to production on MSAL pointed
at Descope — the SDK replacement comes first.

---

## Part 4: Wrap-up

### Post-Migration Summary (Required)

Write `MIGRATION-SUMMARY.md`, scoped to the user's stack, with code snippets and doc links:
1. **What was migrated** — B2C concept → Descope replacement table
2. **Behavioral differences and open questions** — B2C behavior, Descope behavior, action
3. **Pre-deploy checklist** — Console tasks, customer IdP admin notices, user import, cutover
   steps; mark high-effort items (many REST technical profiles, many enterprise IdPs, roles built via
   API connectors) Low / Medium / High
4. **Not yet verified — needs a person** — every Execution Phase 6 → Test 5 check, with exact steps
   and the expected result
5. **After cutover** — improvements deliberately left out of the migration (Match first, then
   enhance), such as passkeys or adaptive MFA

---

## External Docs

- Descope Azure AD B2C migration guide: https://docs.descope.com/migrate/azure-ad-b2c
- Descope SSO migration: https://docs.descope.com/migrate/sso
- Descope session migration: https://docs.descope.com/migrate/session-migration
- Inbound Apps: https://docs.descope.com/identity-federation/inbound-apps
- Resources: https://docs.descope.com/resources
- Federated OIDC Apps: https://docs.descope.com/identity-federation/applications/oidc-apps
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
