---
name: pingone-to-descope
description: >
  Use this skill for migrations from PingOne for Customers / PingOne CIAM to Descope. Trigger
  on requests such as "migrate PingOne to Descope", "PingOne CIAM to Descope", "replace
  PingOne for Customers", "move DaVinci flows to Descope", "PingOne customer auth migration",
  or questions about PingOne customer applications, populations, authentication policies,
  DaVinci, customer MFA, Protect, Verify, customer SSO, SCIM/provisioning, token claims, or
  PingOne APIs and supported client orchestration SDKs in the context of Descope. This skill is CIAM-only and must stop for
  workforce IAM, employee SSO, PingFederate, PingDirectory, PingAccess, PingID workforce auth,
  or general ForgeRock/PingOne Advanced Identity Cloud migrations unless the user explicitly
  says those products are in scope.
---

# PingOne CIAM -> Descope Migration Skill

This skill guides migrations from PingOne for Customers / PingOne CIAM to Descope. It runs in
three parts:

1. **MCP Check** - confirm whether the Descope MCP Server is available before giving SDK/API guidance
2. **Migration Plan** - confirm CIAM scope, triage PingOne surfaces, analyze the codebase, and write `MIGRATION-PLAN.md`
3. **Execution** - only after the user reviews the plan, execute with `MIGRATION-STATE.md` continuity

Do not collapse these parts or skip ahead. The plan must be reviewed before code changes begin.

Primary references in this skill:

- `references/pingone-detection-patterns.md` - grep patterns, import/package/env hints, and out-of-scope detection
- `references/implementation-nuances.md` - framework notes for Federated App/protocol migration, client orchestration SDK/Flow migration, token validation, and claims

## Scope

This skill handles customer identity migrations from **PingOne for Customers / PingOne CIAM** to
Descope. The app must authenticate external customers, members, patients, partners, buyers,
citizens, or end users.

In scope: PingOne customer applications, PingOne users, PingOne populations, PingOne authentication policies, PingOne DaVinci flows, PingOne MFA for customer auth, PingOne Protect, PingOne Verify, PingOne Authorize for customer-facing authorization, Social login, Customer SSO, Customer SCIM/provisioning, Token claims, PingOne APIs/SDKs

Out of scope: Workforce IAM, Employee SSO/app launcher, PingID workforce authentication, PingFederate, PingDirectory, PingAccess, General ForgeRock/PingOne Advanced Identity Cloud migrations, Employee lifecycle / HR-driven provisioning

If analysis detects out-of-scope products, stop and explain that this PingOne CIAM-only skill is
not the right migration path. Do not provide broad PingFederate, PingDirectory, PingAccess, PingID,
workforce, or ForgeRock migration recipes.

## Guiding Principles

**CIAM only.** Treat every decision through the customer-identity lens. Stop when the evidence points
to employee IAM, workforce SSO, internal app-launcher access, device trust for employees, or
HR-driven lifecycle management.

**Flow-first.** PingOne authentication policies and DaVinci flows usually map to Descope Flows. Look
for journey logic, branching, connectors, risk checks, MFA, progressive profiling, account recovery,
and claim-setting behavior before recommending code.

**Map the PingOne hierarchy deliberately.** Classify environments, applications, populations, and
groups by behavior before creating Descope objects. Populations become tenants only for true
customer organizations, realms, or isolated user communities; policy, segment, region, product,
lifecycle, and reporting buckets usually become attributes, Flow branches, project strategy, or no
object.

**Protocol migration is valid only for generic protocol clients.** If the app uses generic
OIDC/OAuth/SAML middleware or a standards library with PingOne as IdP, a Federated App/config swap
may be the first phase. Never recommend keeping a Ping Orchestration/OIDC SDK in Swift, Kotlin,
React Native, or JavaScript and merely pointing it at Descope.

**Use Descope SDK terms precisely.** Descope Client SDKs are for web apps: Web JS, React, Vue,
Angular, and Next.js. Descope Mobile SDKs are for mobile apps: Swift/iOS, Kotlin/Android, Flutter,
and React Native. When replacing Ping Swift, Kotlin, or React Native SDK code, say "Descope Mobile
SDK", not "client SDK".

**Ping SDK evidence is client-side/mobile and limited.** Ping Orchestration SDKs are for
Kotlin/Android, Swift/iOS, JavaScript/TypeScript, and React Native TypeScript. Prioritize Swift and
Kotlin evidence, especially when PingOne Protect collects native device or risk context. Do not look
for nonexistent Ping orchestration SDKs in Python, Go, Node server code, Java, or .NET; in those
stacks, look for generic OIDC/SAML config, token validation, REST/API calls, claims, sessions, and
authorization logic.

**SDK migration is only one path.** Do not assume the app imports a Ping SDK. Many PingOne
CIAM apps use generic OIDC middleware, hosted redirects, custom UI, direct REST calls, DaVinci
widgets, or backend token validation.

**Console-first.** Prefer Descope Console, Flows, Widgets, JWT Templates, SSO Setup Suite, and
tenant configuration before custom code. Code owns app integration and business authorization;
Console/Flows should own the auth journey whenever possible.

**MCP over memory.** Verify every Descope SDK/API method against the Descope MCP before writing code.
Use static guidance only after the MCP check is explicitly resolved.

## Part 1: MCP Check (BLOCKING)

Before doing anything else, check whether the Descope MCP Server is available by calling
`docs_search` with a simple query (e.g., "session validation").

**If the tool is available:** proceed to Part 2 immediately.

**If the tool is not available**, show this message and use `AskUserQuestion` to ask whether
they want to install it first:

> **Descope MCP is not installed.**
>
> This skill uses the Descope MCP server to look up current API signatures, SDK methods, and
> feature availability during migration. Without it, guidance is based on static training data,
> which may be stale and can produce SDK calls that don't exist.
>
> You can install it in a few minutes at **[https://docs.descope.com/mcp/mcp-server](https://docs.descope.com/mcp/mcp-server)** (server URL:
> `https://mcp.descope.com`). It significantly improves the accuracy of the
> migration output - especially for SDK lookups and flow-specific configuration.
>
> **Would you like to install the MCP before we continue, or proceed without it?**

- If they choose to install: pause and wait. Once they confirm it's installed, re-check by calling `docs_search` again before proceeding.
- If they choose to proceed without it: continue, but flag any SDK-specific answers as "based on last known documentation - verify against the current SDK."

Do not proceed to Part 2 until this step is resolved.

## Part 2: Migration Plan

Part 2 has four blocking phases:

1. CIAM scope guard
2. PingOne surface triage
3. Engineer review checkpoint
4. Codebase/config analysis and `MIGRATION-PLAN.md`

### Step 0: CIAM Scope Guard (BLOCKING)

Confirm the app authenticates external customers, members, patients, partners, or end users - not
employees.

Proceed for: Customer registration, Customer login, Customer profile management, Passwordless login, Social login, Customer MFA, Account recovery, Risk checks, Identity verification, Customer-facing authorization, Customer-organization SSO

Stop if the app is primarily: Employee SSO, Workforce app-launcher access, Internal employee auth, PingID workforce auth, Workforce device trust, Employee lifecycle management, PingFederate, PingDirectory, PingAccess, or ForgeRock/PingOne Advanced Identity Cloud migration

When stopping, explain that this skill is restricted to PingOne CIAM and ask whether the user wants a
separate migration path for the detected product.

### Step 0.25: PingOne Surface Triage (BLOCKING - requires `AskUserQuestion`)

Use `AskUserQuestion` to gather:

1. Backend language/framework.
2. Migration goal: full cutover, phased/incremental, or evaluating.
3. Existing user base: active production users, staging/dev only, or starting fresh.
4. PingOne CIAM capabilities in use, as a multi-select:
   - OIDC/OAuth application login
   - Embedded/custom login UI
   - iOS Swift Ping Orchestration/OIDC SDK
   - Android Kotlin Ping Orchestration/OIDC SDK
   - PingOne Protect mobile SDK/device info collection
   - JavaScript/TypeScript Ping SDK or DaVinci widget
   - React Native TypeScript Ping SDK
   - DaVinci flows
   - Authentication policies
   - Users and populations
   - Password login
   - Passwordless / OTP / magic link
   - Social login
   - Passkeys / WebAuthn
   - PingOne MFA
   - PingOne Protect
   - PingOne Verify
   - PingOne Authorize
   - Customer SSO
   - SCIM / provisioning
   - Worker app / client credentials / admin API automation
   - Custom claims
   - Webhooks/events
   - Other

After triage, summarize the likely migration path:

- **Path A: Federated App / protocol-config migration** - generic OIDC/SAML middleware can trust Descope as IdP first; never keep Ping SDKs and point them at Descope
- **Path B: Descope web Client SDK or Mobile SDK + Flow migration** - Ping SDK, DaVinci SDK/widget, custom UI, or direct auth API code is replaced with the correct Descope web or mobile SDK + Flow
- **Path C: Journey/config migration** - PingOne auth policies or DaVinci-heavy usage becomes Descope Flows + Connectors
- **Mixed path** - more than one path applies across apps/services

### Step 0.5: Engineer Review Checkpoint (BLOCKING - requires `AskUserQuestion`)

Ask about:

- Descope Console access and Project ID
- Whether a Management Key is required
- PingOne admin/API access
- PingOne Worker apps, client credentials, or admin/service automation
- Existing users and password cutover
- PingOne populations and what they represent
- Whether each population is a customer organization/realm, isolated user community, segment, policy
  bucket, region, product line, or lifecycle bucket
- Token claims currently read by the app
- Roles, groups, permissions, and entitlements
- Which groups grant access, which groups classify users, which are dynamic, and which are externally
  managed through SSO/SCIM
- Multiple environments
- Multiple apps or services validating PingOne tokens
- Maintenance window or zero-downtime requirement
- Whether users can be forced to log in again after cutover

Include this population question exactly:

> Do PingOne populations represent true customer organizations/tenants, or are they segments/policy
> groups/regions/product lines?

Include this group question exactly:

> Which PingOne groups grant access or permissions, which only classify or segment users, which are
> dynamic, which are externally managed through SSO/SCIM, and which are unused?

Summarize blockers and decisions before codebase analysis. If users/passwords, DaVinci logic,
Protect decisions, Verify requirements, SSO, SCIM, or authorization are unclear, mark the gap in the
plan rather than inventing an answer.

### Step 1: Codebase + Config Analysis

Read `references/pingone-detection-patterns.md`, then scan the repo for PingOne CIAM evidence.
Prefer `rg`; keep grep-compatible commands in notes when the user's environment needs portability.
At minimum, cover these evidence groups:

- PingOne/Ping Identity/DaVinci/ForgeRock strings and PingOne URLs.
- Swift/iOS and Kotlin/Android Ping SDK imports and dependencies, including Protect/device-context patterns.
- JavaScript/TypeScript Ping or DaVinci SDK/widget usage.
- Generic OIDC/OAuth/SAML config: issuer, discovery, JWKS, metadata, client ID/secret, redirect,
  callback, ACS, token, and logout settings.
- PingOne env vars, Worker app/client-credentials variables, and deployment/secrets config.
- User/profile, population, group, role, permission, entitlement, claim, MFA, Protect, Verify,
  social, SSO, SCIM, webhook, event, and audit references.

Use `references/pingone-detection-patterns.md` for the full grep/rg command set, including the
high-signal Swift patterns (`PingOrchestrate`, `PingOidc`, `OidcWebClient`) and Kotlin patterns
(`OidcWeb`, `module(Oidc)`, `web.authorize`). Use
`references/implementation-nuances.md` before recommending implementation details.

For each hit, record:

- File path and line
- What it does
- Which PingOne surface it suggests
- Whether it maps to code, Console/Flow config, data migration, or architecture review
- Complexity: Low / Medium / High

Also scan for out-of-scope products:

```bash
grep -rni "pingfederate\|pingdirectory\|pingaccess\|pingauthorize\|pingid" . 2>/dev/null
```

If found, flag that this may be outside the PingOne CIAM-only skill. Stop unless the user explicitly
confirms those products are in scope for a separate migration path.

### Step 2: Write `MIGRATION-PLAN.md`

Write `MIGRATION-PLAN.md` to the working directory using triage answers and codebase evidence. The
plan must include these sections in this order. Keep the plan specific to confirmed PingOne CIAM
surfaces; use Step 3 as the canonical feature-mapping source instead of repeating every rule.

#### Overview

Write 2-3 sentences explaining what PingOne CIAM behavior is being replaced by Descope.

#### CIAM Scope Confirmation

State why this appears to be customer identity, not workforce IAM. If uncertain, list what evidence
is missing.

#### PingOne Surfaces Found

Use this table:

| Surface | Evidence | File/source | Confidence | Migration implication |
|---|---|---|---|---|

#### PingOne -> Descope Hierarchy Mapping

Use this table:

| PingOne object | Descope mapping | Evidence | Decision / rationale |
|---|---|---|---|
| Environment | Project | [environment IDs, issuer, env vars, console evidence] | [project strategy] |
| Application | Federated App, SDK/Flow integration, or service automation pattern | [application type, protocol, client ID, repo/config evidence] | [mapping by application type] |
| Population | Tenant, custom attribute, Flow branch, project split, or no object | [population ID/name usage, SSO/SCIM scope, app data boundary] | [classification result] |
| Group | Tenant role, project role, custom attribute, dynamic rule, SSO/SCIM mapping, FGA/app logic, or no object | [group usage in claims, authz, SSO/SCIM, policies, app code] | [classification result] |

Classify populations and groups using Step 3. Do not automatically map populations to tenants or
groups to roles.

#### Migration Path

Explain whether this is Path A, Path B, Path C, or Mixed.

#### What's Changing and Why

Use plain-English prose explaining today vs. after migration.

#### Client Integration vs Backend Validation vs Console/Flow Mapping

For every PingOne touchpoint, explain whether it maps to:

- Descope web Client SDK / web component / React/Next SDK for browser auth UI
- Descope Mobile SDK for Swift/iOS, Kotlin/Android, Flutter, or React Native mobile auth
- Descope backend token/session validation or Management API, where server-side work is actually needed
- Descope Console / Flow / JWT Template / Widget / SSO Setup Suite
- App-side authorization logic

#### Auth Touchpoints: What the Code Analysis Found

Group by functional area:

- Login / signup
- Callback / redirect / OIDC
- Session validation
- Token claims
- User profile
- MFA / step-up
- Social login
- SSO
- Authorization
- Webhooks/events

#### PingOne Feature Migration

Include only confirmed features. For each one, use the matching Step 3 feature section and explain:

- What the PingOne feature does today.
- The Descope target: Federated App, Flow, Connector, tenant config, JWT Template, Widget,
  Management API, RBAC/FGA, or app-side authorization.
- Required code/config/data changes.
- Complexity and unresolved decisions.

#### Required Descope Configuration

Split into:

- Required before testing
- Required before production

Include Descope project, Flow, auth methods, JWT Template for profile/custom claims, social
providers, tenants only if customer organizations exist, roles/permissions if used, SSO/SCIM if
used, and event/webhook/audit forwarding if used.

#### Environment Variables

Use a diff table:

| Remove PingOne var | Add Descope var | Why |
|---|---|---|

Likely additions:

- `DESCOPE_PROJECT_ID`
- `NEXT_PUBLIC_DESCOPE_PROJECT_ID`, if applicable
- `DESCOPE_MANAGEMENT_KEY`, if server-side management operations are needed

#### User and Password Cutover

Include only if existing users exist. State clearly that PingOne does not support exporting
passwords or password hashes, so password preservation is not an available migration path. Discuss
user export/import, forced re-login, dry runs in dev/staging, and the two Descope Flow-based
password cutover options: require password reset on first login, or move users to passwordless
authentication.

#### Population / Tenant / Attribute Mapping

Include when populations are found. Classify each population using Step 3, state whether it maps to
a tenant, attribute, Flow branch, project strategy, or no object, and document the evidence.
PingOne users belong to exactly one population; do not introduce multi-tenant Descope membership
unless the app already has that customer model.

#### Group / Role / Attribute Mapping

This section is required when PingOne groups, roles, permissions, entitlements, group claims,
SSO/SCIM group mappings, or dynamic groups are found. Classify each group using Step 3 as an access
role, segmentation attribute, dynamic rule, external SSO/SCIM mapping, flattened nested group,
FGA/app-side authorization concern, or no object.

#### Claims, Roles, and Authorization

Map PingOne groups, roles, permissions, entitlements, and custom claims by function. Document each
claim reader, enforcement point, Descope JWT Template/RBAC/FGA/app-side target, and any claim-shape
changes.

#### Risks and Things to Decide

Include applicable risks:

- Workforce IAM out of scope
- Populations are not automatically tenants
- Groups are not automatically roles
- DaVinci flows may hide important journey logic outside the app repo
- OIDC apps may have little Ping-specific code
- Protect may affect user friction and security decisions
- Verify may be a business requirement, not just auth
- Claims will change
- Password cutover must be decided before cutover: first-login reset Flow or passwordless Flow
- Active PingOne sessions will not automatically survive

#### Execution Plan

Use phases:

- Console setup
- Code/config changes
- User/password cutover
- Testing
- Production cutover

After writing `MIGRATION-PLAN.md`, stop and tell the user:

> `MIGRATION-PLAN.md` has been written to your working directory. It maps the PingOne CIAM surfaces
> found, lists Descope Console setup needed before testing, and calls out the decisions that affect
> cutover.
>
> Please review it before we start making changes. When you're ready to proceed, say so.

Do not begin execution until the user confirms.

## Part 3: Execution

Execute the plan in `MIGRATION-PLAN.md` Execution Plan order. Follow the detailed guidance below
for each step.

### Context Continuity Protocol

Context can be lost between turns. These rules keep the migration coherent.

**Step 3.0 - Create `MIGRATION-STATE.md` before touching any code.**

Write `MIGRATION-STATE.md` to the working directory from the template below. It is the source of
truth for migration state - keep it current throughout execution.

```markdown
# Migration State

_Last updated: [timestamp of last completed step]_

## Project Context
- Framework: [e.g., Next.js 15, Express + React, Flask, Go]
- Language: [TypeScript / Python / Go / Java / C# / etc.]
- Package manager: [npm / yarn / pnpm / pip / go / Maven / Gradle / dotnet / etc.]
- Migration path: [Path A: Federated App / protocol-config / Path B: Descope web Client SDK or Mobile SDK + Flow / Path C: Journey/config / Mixed]
- Migration goal: [Full cutover / Phased / Evaluating]

## PingOne Surfaces in Use
- Applications: [confirmed / not found]
- Worker apps/admin API automation: [confirmed / not found]
- Authentication policies: [confirmed / not found]
- DaVinci flows: [confirmed / not found]
- Users/populations: [confirmed / not found]
- MFA/Protect/Verify: [confirmed / not found]
- Customer SSO/SCIM: [confirmed / not found]
- Authorize/roles/claims: [confirmed / not found]

## Populations Mapping
- [population name/id]: [Tenant / custom attribute / Flow branch / project split / no object / unknown] - [rationale]
- Tenant membership model: [one tenant per migrated user from original population / multi-tenant membership confirmed / unknown]

## Groups Mapping
- [group name/id]: [tenant role / project role / custom attribute / dynamic rule / SSO-SCIM group mapping / FGA-ReBAC / app-side logic / no object / unknown] - [rationale]
- Dynamic groups: [source attributes and recreated rule, or not applicable]
- External directory groups: [authoritative source and group-to-role mapping, or not applicable]
- Nested groups: [flattened effective access / FGA-ReBAC review / not applicable]

## Users and Password Cutover Decision
- Existing users: [active production / staging only / starting fresh]
- Password cutover: [first-login reset Flow / passwordless Flow / undecided]
- Password/hash export: not available from PingOne
- Forced re-login acceptable: [yes / no / undecided]

## Claims and JWT Template Requirements
- Claims read by app: [list]
- JWT Template needed: [yes/no]
- Roles/groups/permissions/entitlements: [list]

## Descope Console Checklist
- [ ] Descope project created - Project ID: [fill in]
- [ ] Flow selected/created
- [ ] Auth methods configured
- [ ] JWT Template configured for profile/custom claims
- [ ] Social providers configured, if used
- [ ] Tenants created only for true customer organizations or isolated customer communities, if any
- [ ] Roles/permissions configured, if used
- [ ] SSO Setup Suite / tenant SSO configured, if used
- [ ] SCIM/provisioning configured, if used
- [ ] Event/webhook/audit forwarding configured, if used

## Files Inventory
_All files that need to change. Update status after each step._

| File | Change | Status |
|---|---|---|
| `path/to/file` | [change] | Pending |

## Current Phase
Phase 1 - Console setup (not started)

## Next Action
Complete console setup per `MIGRATION-PLAN.md` before making code changes.

## Blockers
_(none)_

## Decisions Log
_(none yet)_
```

---

**Rule 1 - Re-read before every turn.**

At the start of every execution turn, re-read `MIGRATION-PLAN.md` and `MIGRATION-STATE.md` before
writing code or making a migration decision.

**Rule 2 - Verify context before every code change.**

If the framework, migration path, triage answers, population mapping, or next step are not clear
from the conversation, re-read both files before proceeding. Then output a context line:

> `Migration context: Next.js 15 - Mixed Path A+B - Phase 2, step 2/7 - Next: replace PingOne issuer config`

If this line cannot be filled in accurately, re-read the files first.

**Rule 3 - Update `MIGRATION-STATE.md` immediately after each step.**

Mark files done in the Files Inventory, update Current Phase and Next Action, and append any
non-obvious decision to the Decisions Log before moving on.

---

## Pre-Generation Protocol (apply before writing any code)

Run before generating any import, wrapper type, helper, or Management API call. Skipping produces
code that compiles but fails at runtime.

**1. Verify SDK exports before writing any import.**
When the Descope MCP server is available, use `docs_ask_question` to confirm the exact method name,
option shape, and return type before writing any SDK call. Do not write a method name and add a
hedge like "verify the exact name" - verify it.

When the Descope MCP server is unavailable: resolve the package's type declarations
(`node_modules/<pkg>/dist/types/` or its `package.json` `types` field) and confirm the exact export
and signature. For Go, run `go doc`. For Python, check SDK stubs. For Java/.NET, inspect the
installed package docs or generated IDE metadata.

This verification is for Descope SDK/API calls the migration actually needs. Do not infer Ping
SDK usage from backend Python, Go, Node, Java, or .NET code; those findings are usually protocol,
token validation, REST/API, claims, cookies, or authorization work.

**Prefer local installed SDK types over GitHub** when available. Installed packages reflect the exact
version in use. If the Descope package is not installed yet, verify the package version before
adding it.

This applies to every Descope SDK call you write: Flow components, hooks, session validation,
logout, Management API calls, SSO, SCIM, tenant operations, roles, and user import helpers.

**1a. After rewriting any module, grep for remaining PingOne imports/config.**

```bash
grep -rni "pingone\|pingidentity\|davinci\|forgerock" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.java" --include="*.cs" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
  .
```

Add remaining relevant hits to the work list. If the hit is an intentional migration note or
rollback reference, record it in `MIGRATION-STATE.md`.

**2. Derive wrapper types from the actual return type.**
Do not infer Descope session or user shapes from PingOne token/user shapes. Read the SDK return type
or validate through MCP, then build adapters only where the app needs a stable internal shape.

**3. Check dependency versions before generating framework-specific code.**
For Next.js: `cookies()` and `headers()` from `next/headers` are synchronous in v14 and async in
v15. Read `package.json` first. For Java, check Spring Security version. For .NET, check target
framework and auth middleware version. For Go/Python, check module/package versions.

**4. When making a helper async, propagate to all callers immediately.**
Grep for every call site of a changed auth helper and update the cascade in the same pass.

**5. Verify published package versions before writing to package manifests or running installs.**
Do not reuse PingOne package versions or rely on memory. Check package registries when network is
available; otherwise use `"latest"` or a clearly flagged placeholder and record that it needs
verification.

---

## Step 1.5: Descope Project Setup & Console Configuration

Several steps require Descope Console setup that cannot be done in code. The app may compile without
them but will not work correctly at runtime.

Use `AskUserQuestion` to ask whether they already have a Project ID and working Flow. If yes, skip
to verifying items 5-9 - those are easy to miss even for existing projects.

### 1. Create a project and get your Project ID

- Sign in at [console.descope.com](https://console.descope.com).
- Your **Project ID** appears in the project selector and under Project settings. It starts with `P`.
- For browser-rendered Next.js/React code, this becomes `NEXT_PUBLIC_DESCOPE_PROJECT_ID`.
- For server-side SDKs, this becomes `DESCOPE_PROJECT_ID`.
- Create separate projects for dev/staging/prod if the PingOne setup has separate environments.

### 2. Get a Management Key (if needed)

Required for user CRUD, user import, tenant operations, role/permission management, SSO/SCIM
configuration, FGA/ReBAC, access keys, and most migration scripts.

- Console -> Company -> Management Keys -> create a Management Key.
- Store as `DESCOPE_MANAGEMENT_KEY`.
- Treat it like a secret. Never expose it in client-side code or `NEXT_PUBLIC_` variables.

### 3. Choose or create a Flow

A Flow is the authentication UI and journey. It is the usual target for PingOne authentication
policies and DaVinci flows.

- Console -> Flows.
- Start with the built-in `sign-up-or-in` Flow for simple login/signup.
- Duplicate and customize it when PingOne policies, DaVinci logic, MFA, Protect, Verify, or
  progressive profiling require branching.
- Record the Flow ID in `MIGRATION-STATE.md`.
- For DaVinci-heavy migrations, do not create a custom Flow until the DaVinci graph, connectors,
  conditions, and claim-setting steps are understood.

### 4. Configure authentication methods

- Console -> Authentication methods.
- Configure only the methods confirmed in triage: password, OTP, magic link, social, passkeys,
  WebAuthn, SSO, MFA, or passwordless.
- For social providers, recreate provider credentials in Descope and add provider steps to the Flow.
- For customer SSO, configure tenant SSO or the SSO Setup Suite after tenant strategy is confirmed.

### 5. Configure a JWT Template

PingOne tokens often include profile fields, population IDs, groups, roles, permissions,
entitlements, or custom claims. Descope tokens should include only claims the app actually reads.

- Console -> JWT Templates.
- Add profile claims such as `email`, `name`, `picture`, `locale`, or `preferredLanguage` only if
  app code reads them from the token.
- Add legacy PingOne identifiers only if the app needs them for a migration bridge.
- Add `aud` or other API audience claims if downstream services validate them today.
- Record every claim in `MIGRATION-STATE.md` with the file or service that consumes it.

### 6. Create tenants for true customer organizations or isolated customer communities

Create tenants only after the Step 3 population mapping is decided. When a population maps to a
tenant, assign each migrated user to the tenant created from their original PingOne population unless
the app already has a confirmed multi-organization membership model.

### 7. Create roles and permissions (if using authorization)

- Console -> Authorization -> RBAC.
- Create only the project-level roles, tenant-level roles, permissions, FGA objects, or app-side
  authorization changes selected in the Step 3 group/authorization mapping.
- Preserve segmentation groups as attributes, dynamic groups as rules, and external SSO/SCIM groups
  as authoritative mappings rather than blanket role imports.

### 8. Configure customer SSO and SCIM (if used)

- For true customer organizations, configure tenant SSO.
- Prefer SSO Setup Suite when customer admins self-configure SAML/OIDC and SCIM.
- Treat SCIM/provisioning as a continuing lifecycle, not a one-time import.
- Confirm group-to-role mapping, deprovisioning behavior, and whether SCIM was scoped by population.

### 9. Configure events, webhooks, audit forwarding, Protect, and Verify replacements (if used)

- Recreate only confirmed event/webhook/audit flows.
- For Protect, decide whether Descope built-in fingerprinting signals, Fraud & Risk Connectors,
  Flow risk branching, webhooks, or an external provider replace the current behavior.
- For Verify, decide whether Descope Flow orchestration plus an external IDV provider is required.

### 10. Env var summary

| Variable | Where to get it | Used by |
|---|---|---|
| `DESCOPE_PROJECT_ID` | Console -> Project settings | Server-side SDKs and token validation |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same project ID | Browser-rendered Next.js/React providers/components |
| `DESCOPE_MANAGEMENT_KEY` | Console -> Company -> Management Keys | User import, users, tenants, roles, SSO/SCIM, FGA |

**After completing console setup:** Update `MIGRATION-STATE.md` - check off each completed item,
record Project ID and Flow ID, and set Next Action to the first code/config change step.

---

## Step 2: Framework-Specific Migration

Use this section to choose the integration style. Use Step 3 to map PingOne features and
`references/implementation-nuances.md` for framework-specific details before writing code.

Classify each code touchpoint:

- **Path A: Federated App / protocol-config migration** - generic OIDC/OAuth/SAML middleware points
  at PingOne as IdP and can be repointed to Descope OIDC or SAML Federated Apps. Do not use this
  path to keep Ping SDK code and only swap issuer/discovery/client settings.
- **Path B: Descope web Client SDK or Mobile SDK + Flow migration** - web/mobile code owns login UI
  or imports supported Ping SDKs, DaVinci SDK/widget code, or direct auth API calls.
- **Path C: Journey/config migration** - PingOne authentication policies or DaVinci define the
  journey and must be rebuilt in Descope Flows + Connectors.
- **Token/API-only backend work** - APIs/services validate PingOne tokens, read claims, call PingOne
  REST/Admin APIs, or enforce authorization; this is not a Ping SDK swap.

Read `references/implementation-nuances.md` in two passes before writing code:

1. **General sections** - Path Selection, Federated App/protocol migration, web Client SDK/Mobile SDK/Flow migration, token
   validation, claim mapping, Console-first decisions.
2. **Framework section** - read only the section matching the user's stack.

### Path A: Federated App / protocol-config migration

Use this when the app uses a generic OIDC/OAuth or SAML client configuration pointed at PingOne as
the IdP.

- For PingOne OIDC Web applications: create/configure a Descope OIDC Federated Application.
- For PingOne SAML applications: create/configure a Descope SAML Federated Application.
- Replace PingOne issuer/authority/discovery metadata with Descope OIDC Federated App settings.
- Replace PingOne SAML metadata/certificate/SSO URL with Descope SAML Federated App metadata.
- Replace PingOne client credentials with the Descope OIDC Federated App/client values required by the framework.
- Update redirect URI, ACS URL, and post-logout redirect URI in Descope Console as applicable.

Good for phased migrations when the app already uses generic protocol middleware: swap the IdP to
Descope Federated Apps first, then refactor web apps to Descope web Client SDK/embedded Flow later
if needed. Caveat: PingOne authentication policies, DaVinci flows, Protect, Verify, customer SSO,
SCIM, and user/password cutover may still require separate work.

Do not recommend Path A for Swift/Kotlin/React Native/JavaScript code that imports Ping
Orchestration, Ping OIDC, or DaVinci SDKs. In those cases the Ping SDK is part of the app
integration and must be replaced, usually by Path B plus Path C when policies or DaVinci are in use.

### Path B: Descope web Client SDK or Mobile SDK + Flow migration

Use this when a web or mobile app imports Ping Orchestration/OIDC SDKs or DaVinci SDK/widget code,
owns custom login UI, or directly calls PingOne auth APIs. Ping SDK evidence should appear in
Kotlin/Android, Swift/iOS, JavaScript/TypeScript, or React Native TypeScript code. Do not use Path B
only because a Python, Go, Node API, Java, or .NET service validates PingOne tokens.

- Treat Swift/iOS and Kotlin/Android as high-priority SDK surfaces, especially for OIDC redirect
  login and PingOne Protect/device-context collection.
- Record client ID, scopes, redirect/deep link, discovery endpoint, browser/session mode, token
  storage, refresh/logout, callbacks, and any device/risk payload handoff.
- Replace web login/signup/account recovery/MFA UI with Descope web Client SDKs or web components.
- Replace Swift/iOS, Kotlin/Android, Flutter, or React Native mobile auth with Descope Mobile SDKs.
- Never keep Ping mobile/OIDC SDK code and point it at Descope discovery metadata.
- Move journey logic to Descope Console/Flows unless the app has confirmed post-login business logic.
- Use `references/pingone-detection-patterns.md` for complete Swift/Kotlin import patterns.

### Path C: Journey/config migration for PingOne policies or DaVinci-heavy usage

Use this when PingOne admin configuration or DaVinci carries most of the behavior.

- Request DaVinci exports/screenshots and authentication policy details.
- Inventory screens, nodes, connectors, conditions, risk branches, Verify steps, MFA steps,
  progressive profiling, claims, and side effects.
- Rebuild the journey in Descope Flows using screens, actions, conditions, subflows, connectors,
  scriptlets only when necessary, and JWT Templates.
- Keep custom business logic in the app only when it belongs after session validation; auth-time
  decisions should usually become Flow logic.

### Framework routing notes

- Browser/React/Next apps may use Path A when they already use generic OIDC middleware, or Path B
  when they render/own the auth UI. Keep `DESCOPE_MANAGEMENT_KEY` server-only and use
  `NEXT_PUBLIC_DESCOPE_PROJECT_ID` only for browser-rendered Descope components/providers.
- Node, Python, Go, Java, and .NET backends usually need issuer/JWKS/audience/claim validation,
  cookie/session, REST/API, or Management API updates. Do not describe these as Ping orchestration
  SDK replacements.
- Native Swift/Kotlin/Flutter/React Native apps use Descope Mobile SDKs and require mobile-specific
  callback/deep-link, token storage, logout, and Protect/device-context review.
- Verify all Descope SDK/API method names through MCP or local type declarations before generating
  code.

**After completing framework code changes:** Update `MIGRATION-STATE.md` - mark each modified file
as Done in the Files Inventory, update Current Phase and Next Action, and log non-obvious decisions.

---

## Step 2.5: Non-Code File Updates

Scan for PingOne references in non-code files after updating source files.

### `.env.example` / `.env.template` / `.env.sample`

Remove PingOne variables that are no longer used and add only the Descope variables the chosen path
requires. Common additions are `DESCOPE_PROJECT_ID`, `NEXT_PUBLIC_DESCOPE_PROJECT_ID` for
browser-rendered Descope UI, and `DESCOPE_MANAGEMENT_KEY` only for server-side management/import
work. Use `references/pingone-detection-patterns.md` for the full PingOne env-var list.

Run:

```bash
grep -rni "PINGONE_\|PING_ONE_\|PING_CLIENT\|PING_ENVIRONMENT\|PING_REGION\|PING_ISSUER\|PING_AUTH\|davinci" \
  --include="*.env*" --include="*.md" --include="*.yml" --include="*.yaml" \
  --include="Dockerfile" --include="*.sh" \
  . 2>/dev/null
```

### README / docs

Search all `.md` files for PingOne references. At minimum, update:

- Setup instructions - replace PingOne application/environment setup with Descope project, Flow, and
  Federated App setup as applicable.
- Environment variables - remove PingOne env vars and add Descope vars.
- Auth flow descriptions - describe Descope Flow/OIDC path and session validation.
- User migration docs - describe export/import, first-login password reset Flow vs. passwordless Flow decision, and forced re-login.
- SSO/SCIM docs - describe tenant SSO/SSO Setup Suite and SCIM re-pointing if used.

### Docker / CI / deployment config

Check Dockerfiles, docker-compose, CI workflows, deployment templates, secrets managers, and
infrastructure config for PingOne variables. Replace only variables the migration actually removes.
For phased cutovers, document whether both PingOne and Descope config are temporarily needed.

### Setup / bootstrap / import scripts

Split setup into:

1. **Console setup** - Flows, auth methods, JWT Templates, social providers, SSO Setup Suite, and
   Protect/Verify replacement decisions.
2. **SDK automation** - user import, tenant creation, roles/permissions, tenant membership,
   SSO/SCIM configuration, and FGA schema/relations after method names are verified.

### PingOne exports and rollback notes

For production migrations, keep PingOne environment/application IDs, DaVinci flow IDs, population
IDs, and export files documented for rollback and audit. Do not leave secrets in repo docs.

**After completing non-code file updates:** Update `MIGRATION-STATE.md` - mark env files, docs, CI,
and scripts done in the Files Inventory, and advance Next Action.

---

## Step 3: Feature Migration Mapping

For each confirmed PingOne CIAM feature, write a short paragraph in the plan and execute against
that mapping during code/config changes. Explain what the PingOne feature accomplishes, the best
Descope approach for that goal, what is different, and what action is required. Reason about intent,
not API names. The best Descope approach may be a Flow, Widget, SSO Setup Suite, JWT Template, tenant
configuration, or app-side authorization rather than a direct SDK equivalent.

Only include confirmed features in customer-facing migration output. Keep out-of-scope product
detections as blockers, not recipes.

### PingOne CIAM -> Descope mapping table

| PingOne CIAM surface | Descope target | Primary migration action | Notes |
|---|---|---|---|
| PingOne environment | Descope Project | Create separate Descope projects for dev/staging/prod | Project IDs replace PingOne environment/issuer identifiers. |
| PingOne application records | Descope Federated App, SDK/Flow integration, or service automation pattern | Inventory application type, protocol, client ID, redirects, scopes, assigned policy/flow, and whether it serves users or services | Map by PingOne application type, not repo name. |
| SAML and OIDC Web applications | Descope SAML or OIDC Federated Application | Repoint metadata/issuer/discovery/client/JWKS/claims from PingOne to Descope | This is the usual Path A for standards-based apps. |
| SPA applications | Descope web Client SDK, web component, Flow, or protocol-preserving OIDC | Replace browser public-client, callback, token, and session handling as appropriate | Never introduce server-only secrets into browser code. |
| Native/mobile and device applications | Descope Mobile SDK or device-flow architecture review | Replace Ping mobile SDK, deep-link, callback, device-flow, and token handling | Do not keep Ping mobile/OIDC SDKs and point them at Descope. |
| Worker applications | Descope Management API, Management Key, Access Keys, or M2M pattern | Separate service/admin automation from customer login | Worker apps are not normal sign-on apps and must not map to Federated Apps or login Flows. |
| Supported Ping SDKs | Descope web Client SDK for web or Descope Mobile SDK for mobile | Replace confirmed Swift, Kotlin, JavaScript/TypeScript, or React Native TypeScript SDK usage | Swift/Kotlin evidence is high signal, especially for Protect/device context. |
| Authentication policies and DaVinci flows | Descope Flows + Connectors | Rebuild screens, branches, MFA, risk, Verify, social, SSO, external calls, and claim-setting behavior | Request exports/screenshots when the repo only shows IDs or callbacks. |
| Users and password auth | Descope Users + Flow-based password cutover | Export/import users; choose first-login reset or passwordless authentication | PingOne cannot export passwords or password hashes. |
| Populations, groups, roles, and entitlements | Tenants, attributes, Flow branches, RBAC/FGA, JWT Templates, SSO/SCIM mappings, or app logic | Classify by business function before creating Descope objects | This is the core hierarchy decision; see the dedicated section below. |
| MFA, Protect, and Verify | Descope MFA/step-up Flows, fingerprinting `riskInfo`, Fraud & Risk Connectors, IDV connectors | Preserve the decision behavior: allow, step up, block, verify, notify, log, or review | These are security/product requirements, not simple SDK swaps. |
| Social login, customer SSO, and SCIM | Descope social providers, tenant SSO/SSO Setup Suite, and SCIM provisioning | Recreate provider credentials and re-point enterprise lifecycle integrations | SSO/SCIM require a confirmed tenant/customer-organization model. |
| Token claims | Descope JWT Templates and Flow custom claims | Recreate only claims the app reads | Claim names and nesting may change; update validators and tests. |
| Events, webhooks, and audit | Descope events, audit connectors, webhooks, or platform-specific audit forwarding | Update event names, payload handling, auth, and signing validation | Set up before production when compliance or automation depends on events. |
| PingOne APIs and admin automation | Descope Management API, Console configuration, token validation, or app logic | Replace only confirmed source calls and verify Descope method names with MCP | Backend Python/Go/Node/Java/.NET findings are usually protocol, token, API, claims, or authz work, not Ping SDK swaps. |

### PingOne hierarchy, populations, and groups -> Descope hierarchy

Use the hierarchy model as a starting point, then override it when evidence shows a different
business function:

```text
PingOne environment -> Descope Project
PingOne application -> Federated App, SDK/Flow integration, or service automation pattern
PingOne population -> Descope Tenant only when it is a real customer organization/community
PingOne group -> Descope role only when it grants access or permissions
```

Do this classification before user import, tenant creation, role creation, SSO/SCIM setup, or claim
mapping. PingOne users belong to exactly one population; Descope users can belong to multiple
tenants, but do not create multi-tenant memberships unless the app already supports that customer
model.

Population mapping rules:

| If the population represents... | Map it to... |
|---|---|
| Customer organization, account, school, clinic, partner, realm, or isolated customer community | Descope Tenant |
| Region, market, locale, language, product line, plan, lifecycle state, beta cohort, or reporting segment | User/tenant custom attribute, Flow branch, app routing, or project strategy |
| Password, MFA, risk, or auth-policy grouping | Descope Flow/auth configuration, not tenant |
| Compliance/residency data partition | Separate project/environment strategy, plus attributes when needed |

Ask exactly:

> Do PingOne populations represent true customer organizations/tenants, or are they segments/policy
> groups/regions/product lines?

Treat population-to-tenant mapping as likely only when SSO/SCIM, roles, admins, data access, or app
account IDs are scoped by population. Treat it as risky when population names look like `US`, `EU`,
`B2C`, `beta`, `passwordless`, `mfa-required`, `retail`, or `mobile`, or when the app never treats
the population ID as a customer/account boundary.

Group mapping rules:

| If the group represents... | Map it to... |
|---|---|
| Population/customer-scoped access, tenant admin, or permission set | Tenant-level role, when the population maps to a tenant |
| Environment/global access across populations | Project-level role |
| Segmentation, region, department, cohort, plan, lifecycle, reporting, or personalization | Attribute, Flow condition, or app-side filter |
| Dynamic membership | Source attributes plus ABAC, Flow condition, FGA/ReBAC, or app logic |
| External IdP, LDAP, or directory-managed membership | SSO/SCIM group-to-role or group-to-attribute mapping |
| Nested hierarchy | Flattened effective roles/permissions, or FGA/ReBAC if hierarchy matters |
| Unused group | No Descope object after dependency analysis |

Dropping a group requires confirming it is not used for application access, role/permission
assignment, auth policies, token claims, SSO/SCIM, dynamic segmentation, delegated administration,
audit, reporting, personalization, or app-side filters.

### PingOne Applications -> Descope Federated Apps or native integration by application type

PingOne applications are configured integrations inside a PingOne environment that let PingOne
manage access to a specific application. When a PingOne application is created, PingOne assigns a
client ID to that application. Do not treat "application" as a generic repo/service bucket or infer
the migration path only from code imports. Inventory the PingOne application record first.

For every PingOne application, record:

- Application type: SAML, OIDC Web, Native, Single Page Application, Device Authorization, Worker,
  or another Ping-specific integration.
- Client ID, issuer/environment, enabled grants or response types, redirect URIs, logout URIs, JWKS
  or certificate settings, scopes, claims, and token lifetimes.
- Assigned authentication policy or DaVinci policy/flow.
- Whether it authenticates external customers/end users, validates tokens for an API, or is a Worker
  app performing service/admin automation.
- Whether it is linked to customer SSO, MFA, Protect, Verify, Authorize, SCIM/provisioning, or
  population-specific behavior.

Map by application type:

| PingOne application type | What it usually means | Descope migration direction |
|---|---|---|
| **OIDC Web application** | Browser-based app with a server-side component using PingOne as OIDC IdP | Map first to a Descope OIDC Federated Application. Update the app from PingOne issuer/discovery/client/JWKS/claims to Descope's OIDC Federated App settings. Descope web Client SDK + embedded Flow is a later refactor option, not the default protocol-preserving migration. |
| **Single Page Application** | Browser-only public client using OIDC and no client secret | Usually map to Descope web Client SDK/web component + Flow. If the SPA already has solid OIDC handling and protocol preservation is required, use a Descope OIDC Federated Application/public-client setup. Never add Management Key or client secret to browser code. |
| **Native application** | Mobile/desktop installed app using OIDC, sometimes involved in MFA | Use Descope Mobile SDK for Swift/iOS, Kotlin/Android, Flutter, or React Native migrations. If the app imports Ping OIDC/Orchestration SDKs, replace them; do not keep Ping SDK and point it at Descope. Review callback/deep links, token storage, logout, and any MFA-authenticator role before implementation. |
| **SAML application** | Browser app using PingOne as SAML IdP | Map first to a Descope SAML Federated Application. Configure Descope's IdP metadata/certificate/SSO URL in the app's Service Provider settings, and configure the SP ACS/entity ID in Descope. Stop if it is employee/Microsoft 365/WS-Fed/WS-Trust scope unless explicitly included. |
| **Device Authorization** | Input-constrained device gets user authorization through a second device | Treat as a dedicated device-flow migration or architecture review; do not collapse it into normal web login. |
| **Worker** | Service/admin API client, usually using client credentials and administrator role assignments | Treat as supporting automation, not customer login. Map to Descope Management API with `DESCOPE_MANAGEMENT_KEY` when it manages Descope resources, or to Descope Access Keys/M2M when it authenticates machine-to-machine calls to your own APIs. Do not map Worker apps to Descope Federated Apps or login Flows. |

Action: inventory every PingOne application record and every app/service validating tokens or SAML
assertions from it. Multi-application environments often need a mixed path: OIDC Web and SAML apps
usually map to Descope Federated Apps for Path A, SPAs may need Descope web Client SDK/Flow work,
native/mobile apps need Descope Mobile SDK/Flow work, DaVinci/policy-bound apps need Path C, and
Worker apps need a separate service/admin-auth review.

### PingOne Authentication Policies -> Descope Flows

PingOne authentication policies decide which methods are allowed, when MFA is required, whether
risk changes the journey, and how recovery or verification happens. Descope Flows are the primary
replacement because they own screens, conditions, actions, subflows, connectors, and final token issuance.

Map policy elements:

- Allowed methods -> authentication method settings + Flow screens/actions
- Password policy -> Descope password settings and Flow behavior
- MFA requirements -> MFA Flow step, subflow, or step-up Flow
- Risk/adaptive rules -> Flow conditions using Descope fingerprinting `riskInfo` signals and Fraud & Risk Connectors
- Account recovery -> password reset / OTP / magic link Flow
- Email verification -> Flow verification step
- Claims set during login -> JWT Template or Flow custom claims

Action: request policy exports/screenshots if the repo only shows OIDC config. Policy logic often
lives entirely outside code.

### PingOne DaVinci Flows -> Descope Flows + Connectors

DaVinci is journey orchestration. Do not reduce it to an SDK or `flowId` swap.

Inventory each DaVinci flow:

- Screens/forms and user inputs
- Nodes/actions and their order
- Connectors and external endpoints
- Branch conditions
- MFA, Protect, Verify, social, SSO, or Authorize nodes
- Claims set on tokens
- User creation/update side effects
- Error, retry, deny, and fallback paths

Map to Descope:

- DaVinci screens -> Descope Flow screens
- DaVinci nodes/actions -> Flow actions or subflows
- DaVinci connectors -> Descope Connectors or Generic HTTP Connector
- DaVinci conditions -> Flow conditions
- Claim-setting -> JWT Templates or Flow custom claims
- End of journey -> Flow End action/session issuance

Action: if only `DAVINCI_FLOW_ID`, `flowId`, or `interactionId` appears in code, mark analysis
incomplete and request the DaVinci configuration before implementation.

### PingOne Users -> Descope Users

PingOne users map to Descope users. The hard part is not the object name; it is stable identifiers,
password cutover, profile fields, MFA factors, social identities, and claims.

PingOne does **not** support exporting passwords or password hashes. Do not plan a hash import or
password-preservation migration. See `references/implementation-nuances.md` -> User Migration and
Password Cutover for the two Flow-based cutover options.

Decide before cutover:

- Whether PingOne user ID must be stored as a Descope custom attribute for lookup/rollback.
- Whether email, username, or another identifier becomes Descope `loginId`.
- Whether migrated users will reset passwords on first login or move to passwordless authentication.
- Whether MFA factors, passkeys, or social identities can be recreated or must be re-enrolled.
- Whether active PingOne sessions will be invalidated and users must log in again.

Action: run user export/import dry runs in dev/staging before production. In the same dry run,
exercise the selected Descope Flow path: first-login password reset or passwordless authentication.

### PingOne Populations -> Tenant / Attribute / Flow Branch / Project Strategy

Use the hierarchy rules above; do not repeat the classification from memory. For each population,
record the observed purpose, evidence, Descope target, and whether user membership remains
one-population-to-one-tenant or needs confirmed multi-organization support.

Action: write a population mapping table in `MIGRATION-PLAN.md` and `MIGRATION-STATE.md` before
creating tenants, importing users, configuring SSO/SCIM, assigning roles, or changing tenant-scoped
code.

### PingOne Groups -> Roles, attributes, rules, or SSO/SCIM mappings

Use the hierarchy rules above; group names alone are not enough. For each group, record whether it
grants access, classifies users, is calculated dynamically, is externally managed, is nested, or is
unused, then migrate the effective behavior rather than only the group label.

Action: complete group classification before creating roles, JWT claim mappings, SSO/SCIM
group-to-role mappings, FGA rules, or app-side authorization changes.

### PingOne MFA -> Descope MFA / step-up Flow

PingOne customer MFA maps to Descope MFA and step-up Flows. Keep MFA in the auth journey unless the
app has a confirmed post-login factor-management requirement.

Map:

- Login-time MFA -> MFA step in the main sign-in Flow
- Conditional MFA -> Flow condition + MFA subflow
- Sensitive action re-authentication -> step-up Flow
- MFA enrollment -> Flow step or User Profile Widget where appropriate
- Factor management UI -> User Profile Widget before custom code

Action: identify whether MFA is mandatory, optional, risk-triggered, tenant-specific, or role-based.
Recreate that decisioning in Flow logic.

### PingOne Protect -> Descope fingerprinting, Fraud & Risk Connectors, and adaptive Flows

Preserve the Protect **decision** (block / challenge / score / notify / log), not just the signal.
Use built-in fingerprinting (`riskInfo`) first; add Fraud & Risk Connectors when the policy needs
specialized bot, device, IP, phone, breach, or behavioral risk. Docs:
`https://docs.descope.com/fingerprinting`,
`https://docs.descope.com/connectors/connector-configuration-guides/fraud`.

Record: decision type, which signals matter, where the decision is made (policy / DaVinci / app /
analytics), which journey points are affected, acceptable friction, and whether an iOS Swift or
Android Kotlin SDK collects device information, device ID, behavioral signals, browser/session
context, or Protect payloads before/during login.

Mobile Protect evidence is high signal:

- Swift/iOS: `PingProtect`, `PingOneProtect`, `PingOrchestrate`, `PingOidc`, `OidcWebClient`,
  `authorize`, `discoveryEndpoint`, `browserMode`, `browserType`, `acrValues`.
- Kotlin/Android: `PingProtect`, Ping Android SDK or DaVinci client Gradle dependencies,
  `com.pingidentity.oidc.OidcWeb`, `com.pingidentity.oidc.module.Oidc`, `Logger.STANDARD`,
  `module(Oidc)`, `web.authorize`, `viewModelScope.launch`, `onSuccess`, `onFailure`,
  `orchestrate`, `oidc`, `protect`, device ID, device profiling, `Journey`, `Node`, `ContinueNode`,
  `SuccessNode`, `FailureNode`.

If mobile SDK code is collecting Protect/device context, do not treat it as generic login SDK code.
Preserve the purpose of that collection when designing Descope fingerprinting, Fraud & Risk
Connectors, and Flow branches.

Built-in mapping:

- `riskInfo.botDetected` -> CAPTCHA, step-up, or block before session
- `riskInfo.impossibleTravel` -> MFA/step-up, notify, or block
- `riskInfo.riskScore` -> low/medium/high Flow branches
- `riskInfo.trustedDevice` -> reduced friction vs extra verification
- Bot Trap screen -> low-friction bot check

When built-in signals are not enough, add a Fraud & Risk Connector (CAPTCHA, Fingerprint, IP/threat,
phone/identity, behavioral fraud, or breach/email reputation - see fraud connector docs) or a
Generic HTTP Connector to the existing risk service.

Decision mapping: risk branch -> Flow conditions; challenge -> MFA/OTP/CAPTCHA; block -> deny with
no session; allow -> success / skip extra MFA; notify/log -> connector, webhook, or audit
forwarding.

Action: treat Protect as a design checkpoint, not a toggle (unless it only logs). Test low-, medium-,
and high-risk plus bot, impossible-travel, and trusted-device paths before cutover.

### PingOne Verify -> Incode or external identity-verification provider

PingOne Verify is an identity-proofing service used to confirm that a user is a real person and that their claimed identity matches a government-issued document. A Verify journey may collect a passport, driver's license, or other identity document, extract and validate document data, capture a selfie, compare the selfie with the document photo, perform liveness checks, and return a pass, fail, or review result. PingOne Verify may therefore support business or compliance requirements such as KYC, age verification, patient or member verification, marketplace trust, fraud prevention, or regulated onboarding.

Descope does not provide a first-party identity-verification service equivalent to PingOne Verify. Instead, rebuild the verification journey using a Descope Flow and a supported KYC or face-verification connector.

Preferred mapping:

* PingOne Verify policy or journey -> Descope Flow plus Incode connector
* Government-ID and selfie capture -> Incode-hosted verification journey
* Document authenticity, face matching, and liveness checks -> Incode verification configuration
* Verification decision -> connector response evaluated by a Flow condition
* Pass, fail, pending, or manual-review behavior -> separate Flow branches
* Verified status -> Descope user custom attribute and, when required, JWT Template claim
* Re-verification -> dedicated verification Flow or step-up branch
* Audit and compliance evidence -> Incode verification records plus Descope audit-event or webhook forwarding

The Incode connector is the strongest general replacement because it can provide a complete external identity-proofing journey, including government-document verification, selfie comparison, and verification outcomes that can be consumed by a Descope Flow.

The AWS Rekognition connector can be used for narrower face-verification requirements. It can compare a captured selfie with a previously registered identity image and return confidence scores. However, it does not validate the authenticity of the government document and should not be treated as a complete KYC or PingOne Verify replacement.

Action: identify the legal, compliance, fraud, or business requirement currently satisfied by PingOne Verify. Prefer the Incode connector for full identity-proofing requirements. Use AWS Rekognition only when face comparison is sufficient. For unsupported provider-specific requirements, integrate another external identity-verification provider through a custom Descope Flow connector.

### Social login -> Descope social provider config

PingOne social providers map to Descope social provider configuration plus Flow steps.

Action:

- Recreate OAuth credentials in Descope.
- Add only confirmed providers to the Flow.
- Update callback/redirect URLs at each social provider.
- Map profile claims the app reads through JWT Templates or user profile reads.
- Test account linking behavior if users can sign in with both password and social.

This is usually Console/Flow work plus claim testing, not custom SDK code.

### Customer SSO -> Descope tenant SSO / SSO Setup Suite

Customer SSO maps to Descope tenant SSO only when the customer organization model is real. If the
current app uses populations as policy groups, do not create tenants solely for SSO until the account
model is clarified.

Prefer:

- Tenant SSO for per-customer SAML/OIDC.
- SSO Setup Suite when customer admins self-configure IdPs.
- Tenant Profile Widget when the app needs embedded tenant-admin setup UI.
- Domain-based routing/home realm discovery when users enter email first.
- Explicit tenant routing when each customer has a dedicated login path.

Action: identify each customer IdP, domains, certificates/secrets, ACS/callback URLs, and whether
setup is internal-admin-driven or customer-self-serve.

### Customer SCIM/provisioning -> Descope SCIM / tenant provisioning

SCIM is a lifecycle, not a one-time import. Enterprise directories will continue to create, update,
suspend, delete, and group users after cutover.

Map:

- PingOne SCIM/provisioning endpoint -> Descope tenant SCIM endpoint/token
- Directory groups -> group-to-role or group-to-attribute mapping
- Deprovisioning -> disable/delete behavior in Descope and app
- Provisioned membership -> tenant membership
- SCIM events/webhooks -> Descope events/audit forwarding if downstream systems depend on them

Action: re-point every customer directory before production cutover or provisioning silently breaks.
Test create, update, deactivate, group change, and reactivation in staging.

### PingOne Authorize -> Descope RBAC/FGA or app-side authorization review

PingOne Authorize for customer-facing authorization maps based on enforcement model. Do not confuse
this with a standalone PingAuthorize product migration unless the user explicitly includes it.

Classify:

- Simple roles/permissions -> Descope RBAC
- Customer-organization scoped roles -> tenant roles
- Claims-only authorization -> JWT Templates plus app checks
- Relationship/resource authorization -> Descope FGA/ReBAC or existing app-side authorization
- External policy decision service -> architecture review before replacement

Action: document each role, group, permission, entitlement, policy, resource, and enforcement point.
For FGA/ReBAC, require a dedicated schema review before writing implementation code.

### Token claims -> Descope JWT Templates

PingOne custom claims often glue the app together. Descope JWT Templates recreate claims the app
actually reads.

Map common claims:

| PingOne claim/source | Descope target | Notes |
|---|---|---|
| `sub` / PingOne user ID | Descope user ID or legacy ID custom attribute | Preserve old ID only if needed. |
| `email`, `email_verified` | JWT Template and user profile | Add explicitly if code reads token claims. |
| `given_name`, `family_name`, `name` | JWT Template / user profile | Update adapters if shape changes. |
| `username` | Login ID or custom attribute | PingOne username may not equal email. |
| `populationId` | Tenant, custom attribute, Flow branch, or project strategy | Classify first. |
| `groups` | Tenant roles, project roles, custom attributes, SSO/SCIM mappings, FGA, JWT Templates, or app-side logic | Classify access vs. segmentation vs. dynamic/external membership before recreating claims. |
| `roles` | Descope RBAC roles / JWT roles | Roles must exist before assignment. |
| `permissions`, `entitlements` | Permissions, FGA, JWT Templates, or app-side authz | Entitlements may need model review. |
| Custom claims | JWT Templates or Flow custom claims | Recreate only consumed claims. |

Action: list every claim reader in the plan. Do not ship code that expects `email`, groups, roles,
or population fields until the JWT Template is configured and tested.

### Webhooks / events / audit -> Descope connectors, webhooks, events

PingOne events may drive downstream automation, analytics, compliance, audit logs, lifecycle sync,
or notifications.

Map:

- Event endpoint -> Descope's Audit Webhook Connector (most important mapping - this is the direct equivalent of a PingOne generic webhook: point it at your own HTTPS endpoint and it streams Descope audit events to it, with Bearer/API Key/Basic auth support)
- Signature verification -> Descope's HMAC secret on the Audit Webhook Connector (x-descope-webhook-s256 header, validated the same way you'd validate a PingOne webhook signature)
- Event names -> Descope event/audit action names and payloads (e.g. UserCreated, LoginSucceed, UserModified, FlowUpdated)
- Audit streams -> Descope Audit Webhook Connector by default; if the org already has a named platform integration (Datadog, Splunk, Groundcover, Sumo Logic, AWS S3, Cribl, Coralogix, New Relic, Snowflake), use that platform's dedicated audit connector instead of building a custom endpoint
- User lifecycle events -> Descope user events or SCIM lifecycle events

Action: identify business-critical events and set up Descope forwarding before production. Default
to the Audit Webhook Connector for a 1:1 replacement of PingOne's generic webhook - deploy an
endpoint, set auth + HMAC signing, and confirm events land. Only reach for a named connector
(Datadog, Splunk, etc.) if the org is already standardized on that specific platform; don't build a
custom endpoint just to re-implement what a dedicated connector already does out of the box. The
app can appear to work while compliance or automation silently breaks.

### PingOne APIs and supported SDKs -> Descope web Client SDK, Mobile SDK, Management API, token validation, or Console

Ping Orchestration/OIDC SDKs appear in client-side web or mobile code for Kotlin/Android,
Swift/iOS, JavaScript/TypeScript, and React Native TypeScript. Do not look for or plan a replacement
of Ping orchestration SDKs in Python, Go, Node server code, Java, or .NET.

For every confirmed PingOne API or supported SDK call found, decide whether it should become:

- A Descope web Client SDK or web component call for browser auth UI
- A Descope Mobile SDK call for Swift/iOS, Kotlin/Android, Flutter, or React Native mobile auth
- Descope session/token validation in backend code
- A Descope Management API call
- A Console/Flow/JWT Template/Widget/SSO Setup Suite configuration item
- App-side authorization or business logic
- Out-of-scope review

If the source is a Ping mobile/OIDC SDK, the migration replaces that SDK. Do not write a plan that
keeps Ping SDK and only changes discovery endpoint, issuer, client ID, or redirect URI to Descope.

Classify backend Python, Go, Node, Java, and .NET findings as OIDC/SAML config, JWT validation,
session handling, PingOne REST/API calls, claims, or Management API automation. Do not describe them
as SDK-replacement work.

Action: verify every Descope method name through MCP before writing code. Prefer Console/Flow
configuration for auth journey behavior.

### Out-of-scope product handling

If any of these appear, stop and ask for explicit scope confirmation:

- PingFederate
- PingDirectory
- PingAccess
- PingID used for workforce authentication
- Workforce IAM / employee app launcher
- HR-driven employee lifecycle provisioning
- ForgeRock / PingOne Advanced Identity Cloud
- PingAuthorize as a standalone product migration

Suggested stop message:

> I found evidence of Ping workforce or platform products outside PingOne CIAM. This skill is scoped
> only to PingOne for Customers / PingOne CIAM migrations. I should not continue with this migration
> path because I may not be able to provide the most accurate migration information for these features.

---

## Step 4: Critical Gotchas (Always Cover These)

Always cover these in `MIGRATION-PLAN.md`, `MIGRATION-STATE.md`, and `MIGRATION-SUMMARY.md` when
they apply:

- **CIAM boundary:** stop for workforce IAM, employee SSO/app-launcher, PingID workforce auth,
  PingFederate, PingDirectory, PingAccess, ForgeRock/PingOne Advanced Identity Cloud, or standalone
  PingAuthorize unless explicitly scoped.
- **Hierarchy classification:** populations are not automatically tenants and groups are not
  automatically roles; use Step 3 before creating tenants, roles, claims, SSO, or SCIM mappings.
- **Hidden journey logic:** OIDC/SAML code may show only issuer, metadata, callback, or `flowId`;
  request PingOne policy or DaVinci exports when journey behavior is not visible in repo.
- **Path A restraint:** generic OIDC/SAML apps can often migrate through Descope Federated Apps
  first, but token/assertion validators, sessions, claims, and tests still change.
- **Claim drift:** Descope tokens will not automatically match PingOne tokens; configure JWT
  Templates only for consumed profile/custom/authorization claims.
- **Password cutover:** PingOne cannot export passwords or password hashes; existing users need a
  Descope Flow for first-login reset or passwordless authentication.
- **Session cutover:** active PingOne sessions do not automatically survive; plan for forced re-login
  unless a bridging strategy is designed and tested.
- **Protect and Verify:** Protect affects security and user friction; Verify can be legal,
  compliance, or business scope. Preserve decisions, audit evidence, and failure/manual-review paths.
- **SCIM lifecycle:** customer provisioning must be re-pointed and tested as an ongoing lifecycle,
  not treated as a one-time import.
- **Management Key:** keep `DESCOPE_MANAGEMENT_KEY` server-only and out of browser/mobile clients.

---

## Step 5: Automated Testing

Run the app and verify it works. Do not hand over only a checklist.

### Phase 0: Final stale PingOne sweep (BLOCKING)

```bash
grep -rni "pingone\|pingidentity\|davinci\|forgerock\|PINGONE_\|PING_ONE_\|PING_CLIENT\|PING_ENVIRONMENT\|PING_REGION\|PING_ISSUER\|PING_AUTH" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.java" --include="*.cs" \
  --include="*.env*" --include="*.yml" --include="*.yaml" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
  .
```

If this returns results, classify each one as migrated, intentional docs/rollback, or remaining work.
Do not proceed with production-ready status while unclassified PingOne references remain.

Also run the out-of-scope sweep:

```bash
grep -rni "pingfederate\|pingdirectory\|pingaccess\|pingauthorize\|pingid" . 2>/dev/null
```

Stop if it reveals unhandled out-of-scope products.

### Phase 1: Install, compile, and start

```bash
npm install   # or: pip install -r requirements.txt / go mod tidy / mvn install / dotnet restore
```

```bash
npx tsc --noEmit
go test ./...
mvn test
./gradlew test
dotnet test
```

Use the project's actual commands from `package.json`, `go.mod`, `pyproject.toml`, `pom.xml`,
Gradle files, or solution files. Do not proceed until compilation/tests for touched areas pass or
failures are understood and recorded.

Start the server with the project's normal command and verify it stays running.

### Phase 2: Run existing tests

Auth-related failures usually mean:

- Test fixtures still contain PingOne issuer/JWKS/claims.
- Mocks still use PingOne user/profile shapes.
- Code expects `populationId` after it moved to tenant/custom attribute/Flow branch.
- Code expects PingOne groups after they moved to tenant roles, project roles, custom attributes,
  SSO/SCIM mappings, FGA, or app-side logic.
- JWT Template claims are missing.
- Authorization tests still read groups/roles/entitlements from old claim paths.

### Phase 3: Smoke test the running app

Verify:

- Public routes load.
- Unauthenticated protected routes return redirect/401, not 500.
- Login page renders Descope Flow or starts the Descope OIDC redirect.
- Successful login creates a Descope session.
- API routes reject missing/invalid tokens.
- User profile fields display after JWT Template configuration.
- Logout clears local session and invalidates refresh token where applicable.
- MFA/step-up branches trigger as expected.
- Social login works in dev/staging if used.
- Customer SSO routes to the correct tenant/IdP if used.
- SCIM create/update/deactivate/group-change flows work if used.
- Webhook/event handlers receive Descope events if used.

### Phase 4: Verify JWT claims

Decode a test session token only for verification, not app logic. Confirm `email`, `name`,
population/tenant strategy claims, roles, permissions, entitlements, and custom claims match the
plan.

### Phase 5: Report results

```markdown
## Test Results

**Compile/static checks:** Pass/fail with command output summary
**Existing tests:** N passed / N failed
**Server startup:** Started on port X / failed
**Unauthenticated protected route:** 302 or 401 / unexpected
**Login:** Descope Flow/OIDC starts and completes / blocked
**JWT claims:** Present / missing
**MFA/Protect/Verify:** Tested / not applicable / blocked
**SSO/SCIM:** Tested / not applicable / blocked
**Webhooks/events:** Tested / not applicable / blocked

**Blockers before going live:**
- [ ] ...
```

Do not proceed to Step 6 until all critical auth paths either pass or are explicitly marked as
manual blockers.

---

## Step 6: Post-Migration Summary (Required)

Every migration produces `MIGRATION-SUMMARY.md` covering what was done, manual setup remaining, and
behavioral differences that matter before production.

### `MIGRATION-SUMMARY.md`

1. **What was migrated** - table mapping each confirmed PingOne CIAM concept to its Descope replacement.
2. **Behavioral differences and open questions** - numbered list. For each item: PingOne behavior,
   Descope behavior, action required.
3. **Hierarchy mapping decisions** - list each environment/project, population/tenant-or-attribute,
   application/integration, and group/role-or-attribute decision with rationale.
4. **User/password cutover status** - first-login reset/passwordless decision, dry-run results, and
   forced re-login expectation.
5. **Claims/roles/authorization differences** - JWT Template claims, RBAC/FGA/app-side checks, and
   remaining decisions.
6. **Pre-deploy checklist** - actionable checkbox items for Console setup, Flow/JWT Template, tenants,
   roles, social providers, SSO/SCIM, Protect/Verify replacements, events/webhooks, and cutover.
7. **Test results** - compile/test/smoke results and blockers.

---

## Step 7: Output Format

Write a numbered migration guide in Markdown, scoped to the user's stack and confirmed PingOne CIAM
surfaces. Use code snippets only after SDK/API names are verified. Always include
`MIGRATION-SUMMARY.md` after execution.

For complex migrations - DaVinci, Protect, Verify, SCIM, customer SSO, Authorize/FGA, ambiguous
population mapping, or multi-service token validation - flag the high-effort items explicitly with
complexity (Low/Medium/High) so the user can plan.

---

## Reference Files

- `references/pingone-detection-patterns.md` - grep patterns, package/import hints, env var hints,
  OIDC/SAML hints, DaVinci hints, and out-of-scope detection.
- `references/implementation-nuances.md` - path selection, Federated App/protocol compatibility, web Client SDK/Mobile SDK/Flow
  migration, token validation, claim mapping, framework notes, Console-first decisions, and testing notes.
