---
name: cognito-to-descope
description: >
  Migrate apps from AWS Cognito to Descope. Triggers on: AWS Cognito, Amplify Auth,
  CognitoJwtVerifier, aws-jwt-verify, amazon-cognito-identity-js, Auth.signIn,
  Auth.currentSession, fetchAuthSession, cognitojwt, User Pool, App Client,
  cognito:groups, NextAuth with Cognito, "migrating from Cognito", "replace Cognito",
  "switch to Descope". Covers all Cognito integration patterns: Amplify v5/v6 + custom UI,
  Amplify Authenticator component, Cognito Hosted UI (OAuth PKCE), federated
  social/SAML login, direct cognito-identity-js, Cognito Identity Pools,
  NextAuth.js + Cognito, M2M client credentials, React Native, and multi-tenant setups.
  Handles automated codebase scanning, package replacement, code transformation,
  user import, JIT migration, Lambda trigger flagging, API Gateway authorizer swap,
  env var updates, and SECRET_HASH / FORCE_CHANGE_PASSWORD edge cases.
---

# AWS Cognito → Descope Migration Skill

Follow a **deep analysis → planning → optional execution** workflow. Do not modify any code until the user explicitly selects Guided Migration Mode. Use the **Descope Docs MCP server** as the source of truth for all Descope-specific information throughout — do not guess at Descope APIs, flows, or configurations.

---

## Workflow Overview

| Phase | Name | Output |
|---|---|---|
| Phase 1 | Deep Codebase & Architecture Understanding | Internal architecture model |
| Phase 2 | Cognito → Descope Concept Mapping (via MCP) | Mapping tables |
| Phase 3 | Generate migration-plan.md | `migration-plan.md` at repo root |
| Phase 4 | Ask user: Plan-Only or Guided Migration Mode? | User decision |
| Phase 5 | Guided Execution (only if user selects it) | Transformed codebase |

Complete Phases 1–3 before asking the user how to proceed.

---

## Full-Stack SDK Model

> **Read this before touching any code.** Mixing up SDK responsibilities — or only migrating one side — is the most common cause of a broken migration.

### Frontend SDK: auth flows, not session validation

The frontend SDK (`@descope/react-sdk`, `@descope/nextjs-sdk/client`) handles:
- Rendering login/signup flows via the `<Descope>` component
- Storing and refreshing the session token on the client
- Exposing `useSession()` and `useUser()` hooks for components
- Triggering logout

> **WARNING: The frontend SDK does NOT validate tokens.** Never use frontend hooks or client-side session state as your authorization gate on the server. A user who manipulates client state would bypass all authorization.

### Backend SDK: session validation and all server-side trust

The backend SDK (`@descope/node-sdk`, `descope` Python package, `@descope/nextjs-sdk/server`) handles:
- Validating every incoming session token on every protected API request
- Extracting verified user identity (`sub`, `email`, `roles`, `tenants`, custom claims)
- All user management operations (create, update, delete; assign roles; manage tenants)
- Global sign-out

> **CRITICAL: Every protected endpoint must validate the session token using the backend SDK.** `descopeClient.validateSession(token)` verifies the JWT signature, expiry, and issuer. If this call does not throw, the token is valid. If it throws, reject the request immediately.

Required env vars:
- `DESCOPE_PROJECT_ID` — always required for session validation
- `DESCOPE_MANAGEMENT_KEY` — required only for management operations. Never expose in frontend code or client-accessible env vars.

### Token flow

```
[User] → signs in via <Descope> component (frontend SDK)
       ← receives session token (JWT) + refresh token

[Frontend] → attaches session token to every API request
             Authorization: Bearer <session_token>

[Backend middleware] → calls descopeClient.validateSession(token)
                     ← returns verified claims: { sub, email, roles, tenants, ... }
                     → sets req.user from verified claims only

[Route handler] → reads req.user (never re-reads the raw token)
               → applies authorization logic using verified claims
```

> **Never decode the JWT manually on the backend** (e.g., `Buffer.from(token.split('.')[1], 'base64')`) as a substitute for validation. Manual decoding skips signature verification. The only exception is peeking at the `iss` claim for dual-validation routing during cutover — and even then the token must still be fully verified afterward.

### Next.js client/server split

Using the wrong import path in the wrong context fails silently or leaks server secrets. **This is the most common source of errors in Next.js migrations — read carefully.**

| Context | Correct hook/function | Wrong (do not use here) |
|---|---|---|
| Client components (`'use client'`) | `useSession()`, `useUser()` from `@descope/nextjs-sdk/client` | `session()` — that's server-only |
| Server components, API routes | `session()` from `@descope/nextjs-sdk/server` | `useSession()` — hooks don't run on the server |
| Next.js middleware (App Router) | `authMiddleware` from `@descope/nextjs-sdk/server` | — |

> **CRITICAL: `session()` is a server-only function. `useSession()` / `useUser()` are React hooks for client components.** Migrating a client component that calls `useSession()` by replacing it with `session()` will cause a runtime error or return stale/unvalidated data. Always check `'use client'` at the top of the file — if it's there, use hooks.

> **Never import from `@descope/nextjs-sdk/server` in a client component** — it will break the build or leak the management key.
> **Never import from `@descope/nextjs-sdk/client` in a server component or API route** — session state from the client bundle is not validated and cannot be trusted.

> **WARNING: If `DESCOPE_MANAGEMENT_KEY` is in a client-accessible env var (prefixed `NEXT_PUBLIC_`, `VITE_`, or `REACT_APP_`), flag it immediately as a critical security issue.** Management keys have full read/write access to all users in the project.

### Session refresh in Next.js

Descope session tokens **refresh automatically** — the SDK handles this transparently with no polling or manual setup needed. However, if a server action updates user attributes (name, email, custom claims) and the UI needs to reflect the change immediately without a page reload, the client must trigger a manual refresh:

```tsx
// Profile update pattern — client component
'use client';
import { useDescope } from '@descope/nextjs-sdk/client';

const { refresh } = useDescope();

async function handleProfileSave(formData: FormData) {
  await updateProfileServerAction(formData); // your server action
  await refresh(); // pull updated claims into session immediately
}
```

> **Note**: `appClient.updateSession()` (Cognito/NextAuth pattern) has no direct server-side equivalent in Descope. The correct pattern is either: (a) call `useDescope().refresh()` client-side after the server action returns, or (b) accept a brief lag (≤5 min) until the next automatic session refresh. Plan profile-editing pages as client components when immediate token claim updates are required.

---

## MCP Setup (Run Before Everything Else)

Before any phase begins, ensure the Descope Docs MCP server is available at `https://docs-mcp.descope.com/mcp`. Run this check automatically — do not ask the user.

The server provides two tools used throughout this skill:
- `ask-question-about-descope` — AI-powered Q&A about Descope features
- `search-descope-docs` — semantic search across Descope documentation

### Step 1: Detect the environment

```bash
# Claude Code (CLI)
claude mcp list 2>/dev/null | grep descope-docs

# VS Code
ls .vscode/mcp.json 2>/dev/null || echo "not found"

# Cursor
ls ~/.cursor/mcp.json 2>/dev/null || echo "not found"

# Generic project-level fallback
ls .mcp.json 2>/dev/null || echo "not found"
```

### Step 2: Check if `descope-docs` is already registered

If `claude mcp list` shows `descope-docs` — it is already registered. Skip to Step 4.

If a config file was found, read it and check whether `descope-docs` is present.

### Step 3: Register the server

Apply the method that matches the detected environment. If multiple environments are present, apply all of them.

**Claude Code (CLI)** — preferred; registers server globally:
```bash
claude mcp add --transport http descope-docs https://docs-mcp.descope.com/mcp
```

**VS Code** — create or patch `.vscode/mcp.json` in the project root:
```json
{
  "servers": {
    "descope-docs": {
      "type": "http",
      "url": "https://docs-mcp.descope.com/mcp"
    }
  }
}
```

**Cursor** — patch `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "descope-docs": {
      "url": "https://docs-mcp.descope.com/mcp"
    }
  }
}
```

**Windsurf** — patch `mcp_config.json` (found via Settings → MCP → view raw config):
```json
{
  "mcpServers": {
    "descope-docs": {
      "serverUrl": "https://docs-mcp.descope.com/mcp"
    }
  }
}
```

**Fallback (unknown environment)** — create `.mcp.json` in the project root:
```json
{
  "mcpServers": {
    "descope-docs": {
      "url": "https://docs-mcp.descope.com/mcp"
    }
  }
}
```

When patching an existing JSON file: preserve all existing keys. Only append `descope-docs`. Never create duplicate entries.

### Step 4: Validate

After any write, re-read the file and confirm: JSON is valid, the `descope-docs` entry is present with the correct URL, and no other entries were modified or removed.

Report to the user:
```
MCP: descope-docs server [already configured / registered via claude mcp add / added to <config file>]
```

Then ask the pre-migration discovery questions below before proceeding to Phase 1.

---

## Pre-Migration Discovery Questions

Before beginning Phase 1 analysis, use the **AskUserQuestion** tool to ask the following questions. These answers shape the entire migration plan — ask them all in a single prompt so the user can respond in one go.

```
I have a few quick questions before diving into the analysis — your answers will shape the migration plan:

1. **Auth UX preference**: Would you like to embed Descope flows directly in your app (users never leave your UI), or keep a redirect-based OIDC/OAuth experience (users redirect to Descope-hosted pages and back)?

2. **Low-code vs code changes**: Do you prefer configuring auth behavior through the Descope Console and pre-built widgets (less code, visual configuration), or do you want full programmatic control (more code, full flexibility)?

3. **Enterprise SSO** (skip if not applicable): Do you have SAML or OIDC-based enterprise SSO today? If yes, would you prefer a no-code setup via the Descope SSO Setup Suite, or do you want to configure it programmatically?

4. **User volume**: Roughly how many users will be migrated? (Helps choose between bulk migration, JIT migration, or working with a Descope CSM for large-scale migrations.)
```

Record the answers in the architecture model and use them throughout:
- **Embed flow**: Use `<Descope flowId="..." />` everywhere (no OIDC endpoints needed). **OIDC redirect**: Use Descope as an OIDC provider — configure Applications in Console.
- **Low-code preferred**: Recommend Console-based flow configuration, Descope User Management Widget, and SSO Setup Suite wherever possible over programmatic equivalents.
- **Large user base (50k+)**: Flag early that they should reach out to their Descope CSM to coordinate the migration cutover, and consider a preemptive Lambda trigger to push users to Descope as they authenticate during the cutover window.

> **Opportunistic Console/flows prompting (throughout all phases)**: Whenever you find server-side code that generates emails, initiates SSO, or manages user journeys, ask whether it could instead be handled by a Descope Flow or Console configuration. Flows can replace custom code for OTP delivery, magic links, password reset, SSO routing, MFA enrollment, and more. Ask before assuming code-based migration is required.

---

---

## Phase 1: Deep Codebase & Architecture Understanding

Build a complete picture of the system's architecture and understand how authentication is woven through every layer of the codebase — not just the auth files.

Use the grep and glob patterns in `references/detection-patterns.md` for all scanning steps. That file contains every pattern for Phases 1.1–1.9.

### What to produce

Consolidate findings into this internal architecture model before moving to Phase 2:

```
ARCHITECTURE MODEL (internal — feeds into migration-plan.md)

System type: [monolith / microservices / serverless / BFF+SPA / etc.]
Services: [list each deployable unit with its role]
Auth flow: [describe login → token → API call path in plain English]
Token storage: [localStorage / httpOnly cookie / memory / secure storage]
Session model: [stateless JWT / server-side sessions / hybrid]

Cognito patterns: [A-K with specific files]
Special behaviors: [client secret / Lambda triggers / device tracking / etc.]

Cross-cutting auth dependencies:
  - Authorization middleware: [files and what they check]
  - Database user scoping: [tables/columns using Cognito sub or username]
  - Frontend auth state: [how user context flows through components]
  - Service-to-service: [how identity propagates between services]
  - Third-party integrations: [external services receiving user identity]
  - Token claim assumptions: [specific claims accessed in code]

Risk surface:
  - HIGH: [things that break silently if token structure changes]
  - MEDIUM: [things requiring code changes beyond auth files]
  - LOW: [things with clear automated migration paths]
```

Read each file found by search patterns. Understand the pattern — do not just collect file names.

**Pattern reference**: `references/detection-patterns.md` — Patterns A–K with all grep commands, special behaviors, full project scan, Lambda trigger detection, env var files, API Gateway config, and cross-cutting dependency analysis.

---

## Phase 2: Cognito → Descope Concept Mapping

Query the Descope Docs MCP server for each concept found in Phase 1. Only include concepts actually present in this codebase — do not generate generic tables.

### Descope Tenant Model — Read Before Mapping Any Multi-Tenancy Pattern

This is the most commonly misunderstood concept in Cognito → Descope migrations. Internalize it before producing any concept mapping table.

**What a Descope Tenant is:**
A Tenant represents a customer organization inside a B2B multi-tenant application. Within a single Descope Project, each Tenant:
- Groups users who belong to the same organization
- Can carry its own SSO configuration (a per-tenant SAML or OIDC connection)
- Scopes roles and permissions per organization — a user can be `admin` in Tenant A and `viewer` in Tenant B simultaneously
- Appears in the validated JWT as `tenants: { "<tenantId>": { roles: [...], permissions: [...] } }`
- Enables per-org login flow customization and domain-based SSO routing

**Cognito has no direct equivalent.** The closest analog is a User Pool Group that is associated with an external IdP for a specific customer org — but even that is not a 1:1 mapping. Use this table to determine what to map to what:

| Cognito Pattern | What It Is | Descope Equivalent |
|---|---|---|
| User Pool | The entire auth namespace for the application | Descope **Project** (not a Tenant) |
| User Pool Group used for capabilities (`admin`, `editor`, `viewer`) | RBAC — describes what a user *can do* | Descope **Roles** |
| User Pool Group used for org identity (`acme-corp`, `tenant_123`, `org_456`) | Org isolation — describes *who the user belongs to* | Potentially a Descope **Tenant** — requires analysis |
| User Pool Group linked to a SAML/IdP for one customer org | Closest Cognito analog to a Descope Tenant | Descope **Tenant** with an SSO connection |
| Separate User Pool per customer org (Pool-per-tenant pattern) | Each pool is one org's namespace | One Descope **Tenant** per pool, all within a single Project |

**Decision rule — apply to every `cognito:groups` usage found in Phase 1:**

1. Group values are capability names (`admin`, `read-only`, `billing-admin`) → map to **Descope Roles**. Tenants are not involved.
2. Group values are organization identifiers (`acme`, `tenant_123`, a UUID, a company name) → analyze whether **Descope Tenants** are appropriate.
3. Multiple User Pools, one per customer org → map each pool to a **Descope Tenant** inside one Project.
4. A User Pool Group is linked to a per-customer SAML IdP → map to a **Descope Tenant** with an SSO connection configured.

**Signals in Phase 1 that indicate Descope Tenants are needed:**
- `cognito:groups` values that look like org names or IDs rather than permission levels
- Pre-signup or pre-auth Lambda that validates email domain to route to a per-org IdP
- `identity_provider=<orgName>` in Hosted UI redirect URLs
- Multiple `COGNITO_USER_POOL_ID` variants in env files (one per customer or environment)
- Adjacent code mapping group names to customer records in a database

**If none of these signals are present:** all `cognito:groups` usage is capability-based → map everything to Descope Roles. Skip any Tenant-related steps in the migration plan.

---

### What to Map

Map the following for each concept found:

- **Core identity concepts**: User Pool, App Client, User Pool Groups (resolve to Roles vs. Tenants using the decision rule above), custom attributes, `cognito:sub`, `cognito:username`, `cognito:groups`
- **Authentication methods**: Email+password, MFA (TOTP/SMS), Hosted UI, social providers, SAML (single and multi-tenant), custom auth challenges, client credentials (M2M), device tracking
- **Token and session model**: issuer change, audience change, claims that change / disappear / are added, validation SDK changes, session refresh
- **Lambda triggers → Descope equivalents**: query MCP for each trigger found in Phase 1; map to Flow conditions, webhooks, JWT Templates, or custom Flow steps
- **Infrastructure**: API Gateway authorizer, Identity Pools, Cognito as OIDC provider
- **System-level impact**: for each cross-cutting dependency from Phase 1.9, document what changes (middleware, DB scoping, frontend auth state, service-to-service, third-party integrations)

### SSO / Enterprise Federation — SSO Setup Suite First

> **Value prop**: Before mapping any SAML or OIDC SSO pattern to programmatic SDK calls (`management.sso.configureOIDCSettings()`, `management.sso.configureSAMLSettings()`, etc.), always present the **Descope SSO Setup Suite** as the recommended path.
>
> The SSO Setup Suite lets admins configure SAML/OIDC connections through a guided no-code UI in the Descope Console — no code deployment required. This is especially valuable for B2B apps where each customer org manages their own IdP.
>
> - **When to recommend SSO Setup Suite**: Any time Cognito SAML federation, Cognito Identity Platform OIDC, or `management.sso.*` calls are detected.
> - **When programmatic config is still needed**: If SSO connections must be created/updated via API (e.g., automated provisioning in a multi-tenant onboarding flow), document both options and let the user choose.
>
> In the migration plan, under every SSO-related section, lead with: *"Descope's SSO Setup Suite handles this configuration through the Console with no code changes required. If you need automated/programmatic SSO provisioning, the management SDK can also do this — see below."*

**Domain verification and org routing**: If the codebase reads `session.user.org_id` for domain-based routing, map this to `token.dct` (domain claim) in Descope JWTs. Flag this field change explicitly in the concept mapping table and in Section 6 (Code-Level Changes) of the migration plan.

### MFA Enrollment

When MFA is detected (TOTP, SMS, or device-based), do not default to mapping it as a separate standalone flow. Instead:

1. Ask the user (via **AskUserQuestion**): *"Your current setup has MFA as a separate step. Would you like to integrate MFA enrollment directly into the main sign-up/sign-in flow (recommended — fewer user journeys to maintain), or keep it as a separate enrollment flow or sub-flow?"*
2. If integrated: document MFA as a step inside the main "Sign-Up or In" flow in Descope.
3. If separate: document as a dedicated sub-flow that the main flow invokes after initial authentication.

> MFA enrollments (TOTP apps, SMS codes) **cannot be migrated**. All enrolled users must re-enroll after migration. Flag this prominently in Section 7 (Risk & Edge Cases).

**Reference**: `references/IMPLEMENTATION-NOTES-DIST.md` for framework-specific before/after patterns and additional context per integration type.

---

## Phase 3: Generate Migration Plan

Write `migration-plan.md` at the root of the repository. This is a distribution-quality document — usable by any engineer on the team without additional context.

The plan has 10 sections:

| Section | Content |
|---|---|
| 1. Executive Summary | Current state, target state, migration strategy, key risks |
| 2. Current Architecture Analysis | System architecture, auth flow diagram, integration points table, dependencies |
| 3. Concept Mapping | Tables from Phase 2 — tailored to what was actually found; token claims before/after |
| 4. System Impact Analysis | APIs/auth layers, frontend apps, backend services, data layer, third-party integrations |
| 5. Step-by-Step Migration Plan | Phases A–H: project setup, user migration, backend, frontend, auth layers, data, infra, cutover |
| 6. Code-Level Changes | Files-to-modify table (file:line, change, complexity); cross-cutting patterns with before/after |
| 7. Risk & Edge Cases | Risk register table (risk, severity, trigger, mitigation); hidden dependencies |
| 8. Testing Strategy | Unit tests, integration tests, manual auth flow checklist, regression areas |
| 9. Rollout Plan | Pre-cutover, cutover, post-cutover steps; monitoring; fallback |
| 10. Manual Steps Checklist | Console setup, connectors, attribute schema, Lambda triggers, JWT Templates, API Gateway, Identity Pools, M2M, email templates |

**Full template with all placeholder text and table structures**: `references/migration-plan-template.md`

After writing `migration-plan.md`, confirm its location to the user.

---

## Phase 4: Interactive Decision Point

After generating `migration-plan.md`, present this message to the user verbatim:

---

**Your migration plan is ready at `migration-plan.md`.**

It covers your full architecture, all Cognito patterns detected, concept mappings, code-level changes, risks, and a phased rollout plan.

**What would you like to do next?**

**Option 1 — Plan-Only Mode**
You review and execute the migration yourself using the plan as your guide. Suggested approach:
- Open `migration-plan.md` alongside the Descope Docs MCP server for reference
- Work through the phases in order — the manual steps checklist is your primary driver
- The plan includes exact file paths and before/after patterns for each code change

**Option 2 — Guided Migration Mode**
I implement the migration with you step-by-step:
- Each step is explained before any code is changed
- I show you diffs and ask for confirmation before proceeding
- We work through phases in order, never making large blind changes
- I reference your codebase patterns and the Descope Docs MCP server throughout

Which would you like?

---

Do not make any code changes until the user explicitly selects Option 2.

---

## Phase 5: Guided Execution Rules

Only enter this phase if the user selects Option 2.

### Pre-execution clarification questions

Before writing any code, use **AskUserQuestion** to resolve the following — ask all applicable questions in a single prompt based on what was detected in Phase 1:

```
Before we start making changes, I want to confirm a few things so the migration fits your preferences:

[Ask only the questions relevant to what was found in Phase 1]

1. **User management UI** (if management API calls detected — updateUser, updateAttributes, etc.):
   Would you prefer to handle user profile management through Descope's pre-built User Management Widget (no code), or keep it code-based?

2. **MFA enrollment** (if MFA patterns detected):
   Would you prefer MFA to be part of the main sign-up/sign-in flow, or remain as a separate enrollment step?

3. **Server-side auth operations** (if server-side email sending, SSO initiation, or user lifecycle calls detected):
   Some of these operations might be replaceable with a Descope Flow step — would you like me to flag those before migrating them to SDK calls?

4. **Unfamiliar files** (if bootstrap, init, or setup scripts with auth config were found — e.g., bootstrap.mjs):
   [Name the specific file(s)] — what does this file do? Understanding its purpose will help me migrate it correctly.
```

> **Never guess the intent of infrastructure or bootstrap files.** If a file like `bootstrap.mjs`, `seed.ts`, or `init-auth.js` contains auth configuration or management calls, ask what it does before migrating it.

> **SDK method accuracy**: Never hedge method names with phrases like "verify the exact method name in the SDK type declarations." Use the Descope Docs MCP server (`ask-question-about-descope`) to look up the correct method name before writing any code that calls a Descope SDK method.

### Execution principles

1. Never make large blind changes. One step at a time. One file at a time where possible.
2. Before each step: state what you are about to do, which file(s) are affected, and why.
3. After each step: show the diff. Ask "Does this look right? Should I continue to the next step?"
4. If a step fails or produces unexpected output: stop. Diagnose before proceeding.
5. Continuously reference the existing codebase patterns and Descope Docs MCP server.
6. Never skip the manual steps — flag them explicitly. They are not optional.

### Execution order

1. **Pre-flight**: Collect credentials (`DESCOPE_PROJECT_ID`, `DESCOPE_MANAGEMENT_KEY`, AWS keys, `COGNITO_USER_POOL_ID`). Back up all `.env` files.
2. **User migration**: Run descope-migration dry run → confirm → live run (or deploy JIT flow).
3. **Session cutover prep**: Deploy dual-validation middleware.
4. **Package replacement**: Remove Cognito packages, install Descope SDK.
5. **Environment variables**: Update `.env` files.
6. **Code transformation**: Work through files from `migration-plan.md` in order.
7. **Verification**: Re-scan for remaining Cognito references; produce final checklist.

### Step format

```
[Step N of M] Updating [file]

What this step does:
[plain English description]

Changes:
[show the specific edit — before/after or diff]

This affects:
[downstream impact if any — e.g., "req.user.id is still available after this change"]

Ready to apply? (yes / skip / show me more context)
```

### Completion format

```
## Migration Complete

Patterns migrated: [list each A-K with AUTOMATED / MANUAL / N/A]
Files transformed: [N]
Packages removed: [list]
Packages added: [list]
Env files updated: [list] (.cognito-backup files preserved)
Users imported: [result from migration tool, or "JIT — no bulk import"]

Remaining manual items (from migration-plan.md Section 10):
[repeat the checklist with any already-completed items checked off]

Re-scan for remaining Cognito references:
[list any found with file:line]
```

**Full code reference for all execution steps**: `references/execution-guide.md` — pre-flight questions, user migration commands, dual-validation middleware (Node.js + Python), package replacement, all code transformation patterns, env var handling, hosted UI/federation paths, and infrastructure changes.

---

## References

| File | Contents |
|---|---|
| `references/detection-patterns.md` | All Phase 1 grep/glob patterns: architecture globs, package detection, Patterns A–K, special behaviors, full project scan, Lambda triggers, env vars, API Gateway, cross-cutting dependency analysis |
| `references/migration-plan-template.md` | Full `migration-plan.md` template with all 10 sections, placeholder text, table structures, and agent instructions |
| `references/execution-guide.md` | Full execution code: pre-flight questions, user migration (full + JIT), dual-validation middleware, package replacement, all code transformation patterns, env var handling, hosted UI/federation patterns, infrastructure |
| `references/IMPLEMENTATION-NOTES-DIST.md` | Framework-specific before/after code examples for Amplify v5/v6, React, Next.js, Node.js/Express, and Python/Flask |
| `references/flows-widgets-console.md` | Cognito → Descope terminology mapping, Flows/Widgets/SSO Setup Suite overview, Lambda trigger → Flow step mapping, and Console-vs-code decision guide |
