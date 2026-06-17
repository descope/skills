---
name: stytch-to-descope
description: >
  Use this skill whenever anyone asks about migrating from Stytch to Descope — whether they're
  a developer doing it themselves or a technical lead evaluating the move. Triggers on: "how
  do I migrate from Stytch", "replace Stytch with Descope", "we're moving off Stytch", "Stytch to
  Descope", "switch from Stytch", "our app uses stytch / @stytch/nextjs / Stytch UI / Stytch SSO / Connected Apps / SCIM and we want to use Descope instead",
  or any question about Stytch features (Consumer authentication, Multi-tenant / B2B Authentication, Enterprise SSO, SCIM, Admin Portal, M2M Authentication, Connected Apps, Session Management, Fraud & Risk) in the context of Descope. Works for any
  language or framework with a Descope SDK. Always use this skill before producing migration
  guidance — do not rely on memory alone.
---

# Stytch → Descope Migration Skill

This skill guides self-service migrations from Stytch to Descope. It runs in three parts:

1. **MCP Check** — confirm whether the Descope MCP Server is available and suggest installing it if not
2. **Migration Plan** — gather context via triage questions, analyze the codebase's auth touchpoints, and produce a human-readable `MIGRATION-PLAN.md` for the user to review
3. **Execution** — if the user confirms they want to proceed, execute the plan

Do not collapse these parts or skip ahead. The plan must be reviewed before code changes begin.

Stytch is not only an authentication provider — it is a broader identity platform spanning consumer authentication, multi-tenant/B2B authentication, organizations and members, enterprise SSO, SCIM/directory sync, RBAC, JIT provisioning, MFA, session management, Admin Portal flows, fraud and risk protection, device fingerprinting, Protected Auth, machine-to-machine authentication, trusted auth tokens, and Connected Apps for OAuth/OIDC-based integrations and AI-agent access. A good migration first identifies which Stytch product surfaces are in use, then maps each one to the closest target feature or migration pattern. Expect Stytch migrations to vary more widely than a purely B2B auth migration, since a Stytch implementation may include consumer passwordless auth, enterprise-readiness features, fraud/risk infrastructure, and OAuth/OIDC connected-app workflows.

**Primary references** (both in this skill's directory):

- `references/implementation-nuances.md` — verified migration patterns for each framework, Stytch feature-to-Descope mappings, and known gotchas
- `references/flows-and-widgets.md` — Descope terminology/lingo, Flow structure and templates, Widgets, SSO Setup Suite, Console-vs-code decision guide

---

## Guiding Principles

**Console-first.** Before recommending SDK code for any user-facing auth feature, check whether the Console, a Flow, a Widget, or the SSO Setup Suite covers the use case. Engineers integrate once (SDK setup + session validation). All subsequent auth evolution — new methods, MFA changes, UI updates, tenant SSO onboarding — should happen in the Console without code deployments. See `references/flows-and-widgets.md` → Console vs. Code.

**Ask, don't assume.** At any design decision point — Flow vs. custom code, Widget vs. custom page, MFA inline vs. separate enrollment, programmatic SSO vs. SSO Setup Suite, one-Organization-to-one-Tenant mapping — use `AskUserQuestion` rather than proceeding with an assumption. The cost of a wrong assumption compounds across 20+ files, and the Stytch Organization → Descope Tenant mapping in particular ripples into SSO, SCIM, RBAC, and domain routing. Uncertainty about architecture or intent is always worth a question.

**MCP over memory.** When the Descope MCP Server is available (confirmed in Part 1), use `docs_ask_question` to verify every SDK method name, option shape, and return type before writing it. Do not fall back to "verify the exact method name in the SDK type declarations" as a hedge — just verify it directly.

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

1. **Triage** — ask the questions needed to understand scope (migration questions go here since answers shape the plan)
2. **Codebase Analysis + Plan File** — scan the project, produce `MIGRATION-PLAN.md`, and pause for review

### Step 0: Triage (BLOCKING — requires `AskUserQuestion`)

**Use the `AskUserQuestion` tool to gather the information below. Do not infer answers
from memory, prior conversations, or assumptions — even if you think you know.**
The migration path differs based on these answers; getting them wrong wastes the user's
time and produces incorrect guidance.

Do not proceed to Step 0.5 until the user has answered.

**First `AskUserQuestion` call (up to 4 questions):**

1. **Backend language / framework** — Present the most likely options based on any cues
  in the conversation (e.g., Node.js, Go, Ruby, Python, Java). The user can always
   pick "Other."
2. **Migration goal** — Full cut-over, incremental/phased migration, or just evaluating.
3. **Existing users and organizations** — Are they migrating an app with active users and
  organizations in Stytch, staging/dev only, or starting fresh? This determines whether user
   and organization migration planning is needed (user export, org-to-tenant mapping, SCIM
   continuity, phased vs. big-bang cutover, forced re-login on cutover). 

**Second `AskUserQuestion` call — Stytch feature usage (use `multiSelect: true`):**

1. **Which Stytch features are in use?** Present the highest-impact categories:

* **Consumer Authentication** — which sign-in methods are enabled, such as OAuth/social login, email magic links, OTPs, passwords, passkeys, WebAuthn, mobile biometrics, MFA, TOTP, crypto wallet auth, or new-device notifications; whether the app uses Stytch UI, frontend SDKs, backend SDKs, or direct API calls.
* **Multi-tenant / B2B Authentication** — whether the Stytch B2B model is used; how Organizations and Members are modeled; whether members can belong to multiple organizations; whether org discovery, org-specific login, or organization switching/session exchange is used.
* **Organizations and Members** — organization metadata, member metadata, membership lifecycle, invitations, member search/update flows, deactivation behavior, and whether organization-specific auth policies are configured.
* **Enterprise SSO** — whether SAML, OIDC, or both are used; which identity providers are connected; whether setup is handled internally or by customer admins; whether SSO is organization-specific, multi-organization, or standalone; whether role assignment or JIT provisioning depends on SSO claims.
* **SCIM / Directory Sync** — which workforce directories are connected; whether member provisioning, deprovisioning, group sync, group-to-role mapping, session revocation, or webhook handlers depend on SCIM behavior. Flag as high complexity.
* **RBAC** — how Stytch resources, actions, permissions, and roles are defined; whether roles are consumer-level or organization/member-level; where permission checks happen in code; whether roles or permissions are included in session tokens; whether SSO or SCIM maps groups/claims to roles.
* **JIT Provisioning** — which provisioning sources are allowed; whether users/members are automatically added to organizations after SSO, email-domain matching, discovery, invitations, or trusted token flows.
* **MFA and Step-up Authentication** — which second factors are used, such as SMS OTP, email OTP, TOTP, passkeys, WebAuthn, or other factors; whether MFA is globally required, organization-specific, risk-based, or used only for sensitive actions.
* **Sessions and Tokens** — how session tokens, session JWTs, intermediate sessions, custom claims, cookies, expiration, refresh, revocation, and frontend/backend session validation are implemented.
* **Admin Portal UI** — which customer-admin workflows are handled by Stytch today, such as member management, organization settings, SSO setup, SCIM setup, or RBAC management; whether the application generates Admin Portal links or embeds Stytch-provided admin flows.
* **Fraud & Risk / Device Fingerprinting (including Protected Auth)** — whether Device Fingerprinting is used for bot detection, credential stuffing protection, account takeover prevention, toll fraud prevention, free-trial abuse, remembered devices, trusted/unrecognized device detection, IP-geo restrictions, new-device notifications, or to enable **Protected Auth** mechanisms (which can block, challenge, add friction, or monitor suspicious attempts). Flag as high complexity if Stytch verdicts or Protected Auth flows influence authentication decisions or require custom enforcement logic.
* **Connected Apps** — whether the application uses Stytch to act as an OAuth/OIDC authorization server; which first-party, third-party, public, or confidential clients exist; which authorization code, PKCE, consent, token, refresh token, revocation, custom scope, or RBAC-backed scope flows are implemented. Flag as high complexity.
* **AI Agent / MCP Authentication** — whether Connected Apps are used for AI agents, MCP clients, CLI tools, external integrations, or agentic access to application data; review scopes, consent, dynamic client registration, token lifetimes, and organization-level controls before implementation. Flag for deeper review.
* **Machine-to-Machine Authentication** — whether M2M clients, client credentials, client secrets, JWT access tokens, scopes, custom claims, or secret rotation are used for service-to-service authentication.
* **Trusted Auth Tokens / External Identity Bridging** — whether external JWTs are exchanged for Stytch sessions; which external IdPs, custom auth factors, claim mappings, JIT provisioning behavior, or role assignments depend on this flow. Flag as high complexity.
* **Webhooks, Event Logs, and Event Streaming** — which Stytch events are consumed by the application; whether event logs are shown to customers, streamed to external systems, used for compliance, or used to trigger internal user/org synchronization.
* The user can add others via **“Other.”**

After both calls, summarize findings and flag high-complexity items before proceeding to Step 0.5. The main high-complexity Stytch areas are typically **SCIM/Directory Sync, Enterprise SSO with JIT provisioning, RBAC tied to SSO or SCIM, Fraud & Risk/Device Fingerprinting, Protected Auth, Connected Apps, AI Agent/MCP authentication, Machine-to-Machine authentication, and Trusted Auth Tokens**.

---

## Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

These questions surface blockers the framework doesn't expose. Ask even the ones you think
you know. Use `AskUserQuestion` before proceeding to codebase analysis.

Batch into calls of up to 4 questions. Skip questions that are clearly inapplicable given
Step 0 answers (e.g., skip user migration planning if they said they're starting fresh).

**Access and credentials**

* Do they have access to the Descope Console and a Project ID? (If not, see Step 1.5.)
* Do they need a Management Key? Required for user CRUD, tenant management, RBAC, SSO/SCIM configuration, access keys, Inbound Apps, Outbound Apps, and other management operations.
* Do they have access to the Stytch Dashboard/API keys needed to inspect or export the current configuration, including Consumer Auth, B2B Organizations/Members, SSO, SCIM, RBAC, Connected Apps, Fraud & Risk, and Admin Portal settings?

**Codebase scope**

* Is this a Stytch Consumer Auth app, a Stytch Multi-tenant/B2B Auth app, or a hybrid app using both? This determines whether the migration centers on Users only or on Organizations/Members → Tenants/Users.
* Are there places in the app that read claims or session fields directly from Stytch tokens or session responses, such as `user_id`, `member_id`, `organization_id`, `organization_slug`, `roles`, `permissions`, `trusted_metadata`, `untrusted_metadata`, or custom claims? These need a Descope JWT Template or Flow Custom Claims configured before equivalent reads will work.
* Does the app read Stytch `organization_id`, `member_id`, `sso_connection_id`, `scim_group_id`, Connected App client IDs, or RBAC `role_id` / `resource_id` / `action` values in many places? The Stytch Organization → Descope Tenant remap ripples through SSO, SCIM, RBAC, JIT provisioning, Admin Portal replacement, Connected Apps, and membership checks — confirm the organization model before writing code.
* Are there multiple services or microservices validating Stytch session tokens, session JWTs, access tokens, or Connected Apps tokens? Each service needs to be updated to validate the correct Descope-issued JWTs or OAuth/OIDC tokens.
* Does the application use Stytch frontend SDK helpers, backend API calls, direct REST calls, Stytch UI components, or all of the above? This determines whether the migration is mostly Flow/UI replacement, backend SDK replacement, or both.
* Does the app depend on Stytch webhooks to keep its own database in sync? Search for webhook handlers before changing user, organization, member, SCIM, RBAC, fraud, or Connected Apps behavior.

**Deployment and risk**

* Do they have multiple environments (dev / staging / prod)? Each needs its own Descope project and Project ID, with matching redirect URLs, auth domains, SSO/SCIM configuration, Connected Apps, and environment-specific secrets.
* Is there a maintenance window, or does this need to be zero-downtime?
* Are any external customers, enterprise IdPs, SCIM directories, OAuth clients, MCP clients, or machine-to-machine clients already integrated with the Stytch production project? If yes, plan customer-facing cutover steps, not just code changes.
* Are login URLs, callback URLs, custom auth domains, email domains, OAuth issuer URLs, or JWKS URLs contractually or technically expected to stay stable? If yes, flag early because they affect SSO, sessions, Connected Apps, and token validation.

**User, organization, and member migration** (if they indicated existing users/orgs in Step 0)

* How many users, Organizations, and Members exist? This determines export approach and whether a phased cutover is warranted.
* Are they using Stytch Consumer Auth users, Stytch B2B Members, or both? Consumer users and B2B Members have different object shapes and should not be collapsed without confirming the target model.
* Do Stytch Members belong to multiple Organizations? If yes, preserve tenant membership and role assignment per organization when mapping to Descope Tenants.
* Do they use passwords in Stytch? Plan how password credentials carry over: import if supported, force reset, staged password migration, or replacement with passwordless methods. Verify the current Stytch export capability and Descope import path before committing to an approach.
* Which Stytch authentication methods are in use: OAuth/social login, OTP, magic links, passwords, passkeys/WebAuthn, mobile biometrics, TOTP, MFA, crypto wallets, or custom auth factors? Confirm migration feasibility for each method before writing implementation instructions.
* Big-bang cutover or phased? Map each Stytch Organization to a Descope Tenant first; user/member migration, tenant membership, SSO, SCIM, JIT provisioning, and tenant-scoped roles depend on it.
* **SCIM is a lifecycle system, not a one-time import.** If Stytch SCIM is enabled, enterprise directories will keep pushing create/update/deactivate/group events after cutover. A single user import is not enough — every SCIM workflow must be re-pointed at Descope before cutover, or provisioning silently breaks.
* Are they aware that active Stytch sessions will be invalidated on cutover unless a session-bridging approach is used? Plan for forced re-login, phased rollout, or a temporary compatibility layer.
* Does the app store Stytch IDs in its own database? If yes, plan an ID mapping table for Stytch `user_id`, `member_id`, `organization_id`, `role_id`, Connected App client IDs, and any other persisted identifiers.

**Gaps to flag immediately** (don't ask — flag these proactively based on Step 0 answers)

* If they're using **Fraud & Risk / Device Fingerprinting**: flag for security-flow review. Stytch verdicts, device IDs, trusted device logic, IP-geo restrictions, new-device notifications, and abuse-prevention decisions may need to be recreated with Descope Fingerprinting, Flow conditions, connectors, audit events, or app-side policy.
* If they're using **Protected Auth**: flag that this is not a direct SDK toggle migration. Protected Auth behavior should be redesigned as Descope Flow-based risk handling: allow, challenge, block, or notify based on risk signals and policy.
* If they're using **Connected Apps**: flag for deeper OAuth/OIDC review before implementation. Inventory clients, redirect URIs, public vs. confidential clients, PKCE, scopes, consent records, access token lifetimes, refresh token behavior, issuer/JWKS dependencies, and resource-server validation. This usually maps to Descope Inbound Apps, but it must be designed carefully.
* If they're using **AI agent / MCP authentication** through Stytch Connected Apps: flag for dedicated review. This may map to Descope Inbound Apps, Agentic Identity Hub, MCP server authorization, DCR/CIMD, resource scopes, or tenant-aware policies.
* If they're using **Machine-to-Machine authentication**: identify all M2M clients, secrets, scopes, token audiences, and rotation requirements. This may map to Descope Access Keys, client credentials, or Inbound Apps depending on how the tokens are consumed.
* If they're using **Trusted Auth Tokens** or external JWT exchange: flag as high complexity. Confirm issuers, JWKS URLs, audiences, subject mapping, claim mapping, JIT behavior, and whether the exchange creates a user session or only API access.
* If they're using **SCIM**: set up Descope SCIM and customer IdP cutover before production migration. Missing this can break provisioning/deprovisioning even though interactive login may still appear to work.
* If they're using **webhooks or event logs**: identify business-critical handlers and configure Descope webhooks, audit connectors, or event streaming before cutover to avoid gaps in compliance, sync, or customer-visible activity.
* If the app depends on **third-party provider tokens** obtained during OAuth/social login: determine whether those tokens are only used for login or also used to call provider APIs. If they power integrations or background jobs, evaluate Descope Outbound Apps or app-side token storage; do not assume normal login migration preserves provider API access.

**Console/Flow/Widget opportunities** (flag before codebase analysis, then ask):

* If the app uses the **Stytch Admin Portal UI** or Stytch Admin Portal components for member management, organization settings, SSO setup, or SCIM setup: ask whether Descope SSO Setup Suite and Admin Widgets can replace that workflow instead of rebuilding it as custom code. Do not default to building custom admin setup screens.
* If the app has a profile edit page, member management page, organization settings page, or tenant-admin UI: ask whether a Descope Widget covers the use case.
* If the app has a separate MFA enrollment page: ask whether MFA should be integrated into the main sign-in Flow as a step or subflow instead.
* If any server-side code initiates SSO, generates emails, runs custom checks, calls fraud APIs, or makes decisions during the auth journey: ask whether that logic can become a Descope Flow step, condition, or Connector instead of server code.
* If the app uses custom Stytch UI built with frontend SDKs: ask whether Descope Flows can replace the custom UI or whether the customer requires a headless SDK migration.
* If the app uses Stytch Connected Apps and hosts its own OAuth authorization endpoint UI: ask whether Descope Inbound Apps can own more of the OAuth/OIDC authorization-server behavior, consent, token issuance, and client configuration.
* If the app has risk-based auth, remembered-device behavior, new-device notifications, or custom fraud challenges: ask whether these should be modeled as Flow branches using Descope risk signals and messaging/connectors.

Summarize any blockers and Console/Flow/Widget opportunities before proceeding to codebase analysis.

---

### Step 1: Codebase Analysis

Scan the codebase to map every auth touchpoint before writing the plan.

Stytch ships **backend SDKs** (Python, Go, Node, Ruby, Java/Kotlin/JVM), **frontend SDKs**
(React, Next.js, Vanilla JS), and **mobile SDKs** (React Native, iOS Swift, Android Consumer SDK —
a headless Kotlin Multiplatform library targeting Android). Adapt the file extensions below to
whichever surfaces appear in the project.

**Run these searches (adapt file extensions to the user's language and platform):**

```bash
# Find all Stytch import / package sites (backend, frontend, mobile)
grep -rni "stytch\|@stytch\|stytchauth\|com\.stytch" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.mjs" --include="*.cjs" --include="*.py" --include="*.go" \
  --include="*.rb" --include="*.java" --include="*.kt" --include="*.kts" \
  --include="*.swift" --include="*.gradle" --include="*.gradle.kts" \
  --include="Podfile" --include="Gemfile" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=venv \
  --exclude-dir=build --exclude-dir=.gradle \
  . 2>/dev/null

# Find all Stytch env var references
grep -rn "STYTCH_\|stytch\." \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.java" --include="*.kt" \
  --include="*.swift" --include="*.env*" --include="*.yml" --include="*.yaml" \
  --include="Dockerfile" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null

# Find Stytch SDK surface + session / claim / org access patterns
# (things that may need a JWT Template or org→tenant remap)
# We match on ".sessions" etc to catch any variable name (e.g. stytch.sessions, stytchClient.sessions)
grep -rni "\.sessions\|\.b2b\|\.b2c_client\|\.otps\|\.magicLinks\|\.magic_links\|\.passwords\|\.oauth\|\.webauthn\|\.totps\|\.mfa\|\.m2m\|\.scim\|\.connected\|\.idp\|\.rbac\|\.discovery\|\.impersonation\|\.users\|\.organizations\|session_token\|session_jwt\|intermediate_session_token\|organization_id\|organization_slug\|member_id\|trusted_auth\|external_token\|custom_claims\|authenticateJwt\|authenticate(" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.java" --include="*.kt" \
  --include="*.swift" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.java" --include="*.kt" \
  --include="*.swift" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null

# Find frontend / mobile session hooks and providers
grep -rn "StytchProvider\|StytchB2BProvider\|Products\|StytchB2B\|StytchLogin\|StytchHeadlessClient\|useStytch\|useStytchUser\|useStytchSession\|createStytchUIClient\|StytchConsumerSDK\|StytchClient\|StytchUI\|@stytch/nextjs\|@stytch/react\|@stytch/vanilla-js\|@stytch/react-native" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.swift" --include="*.kt" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null

# Find B2B / enterprise / fraud / connected-app feature usage
grep -rn "scim\|saml\|sso\|adminPortal\|admin_portal\|discovery\|jit_provision\|connectedApp\|connected_app\|m2m\|client_credentials\|deviceFingerprint\|device_fingerprint\|protectedAuth\|protected_auth\|dfp\|webhook" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.java" --include="*.kt" \
  --include="*.swift" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null

# Check dependency manifests for Stytch packages
find . -maxdepth 4 \( \
  -name "package.json" -o -name "go.mod" -o -name "requirements.txt" -o \
  -name "Gemfile" -o -name "pom.xml" -o -name "build.gradle" -o -name "build.gradle.kts" -o \
  -name "Podfile" -o -name "Podfile.lock" \
\) ! -path "*/node_modules/*" ! -path "*/build/*" \
  -exec grep -l "stytch\|@stytch\|stytchauth\|com\.stytch" {} \;
```

For each hit, record:

- **File path and line** — where the change happens
- **What it does** — import, route protection, claim access, org/tenant read, SSO/SCIM config, webhook handler, logout handler, etc.
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
exists. Pair complexity labels with time estimates; skew toward the lower bound — SDK swaps and mechanical rewrites are usually faster than they look, and repetitive files in a group after the first go much faster. Group execution into phases so parallel vs. sequential work is clear.

The plan must include these sections, in this order:

#### Overview

2–3 sentences: what's being replaced, what replaces it, and the recommended approach with a
one-sentence rationale. Add one sentence on what doesn't change — user-facing login behavior,
sessions, organizations, and existing accounts are preserved.

Include a **Migration at a Glance** table:


|                                  |                                                                     |
| -------------------------------- | ------------------------------------------------------------------- |
| **Approach**                     | Full native migration                                               |
| **Files changing**               | N source files across N areas                                       |
| **Console setup**                | N configuration steps before launch                                 |
| **User impact**                  | No re-login required / Users will need to log in once after cutover |
| **Estimated engineering effort** | N–N hours                                                           |
| **Biggest risk**                 | One sentence naming the highest-complexity item                     |


---

#### What's Changing and Why

Prose (not a table) describing what each part of the system does today and what it does
after. Example:

> Today, Stytch handles everything related to login: Stytch UI or frontend/mobile SDKs render
> the login experience, issue `session_token` / `session_jwt`, and the backend SDK validates
> sessions on every request — routing B2B users to the right organization SSO connection when
> applicable. After this migration, Descope takes over all of those responsibilities. The login
> UI becomes a Descope Flow embedded in the app. Session validation moves to the Descope SDK.
> Stytch Organizations become Descope Tenants. `STYTCH_PROJECT_ID`, `STYTCH_SECRET`, and the
> public token are replaced by `DESCOPE_PROJECT_ID` (and `NEXT_PUBLIC_DESCOPE_PROJECT_ID` for
> the browser).
>
> Stytch features in use that need to carry over: [list in plain English, one clause each].

Tailor to triage findings.

---

#### Client SDK vs. Backend SDK: A Specific 1-to-1 Mapping

For every Stytch touchpoint found in triage, produce a concrete, one-to-one mapping — Stytch construct → the exact Descope SDK and method that replaces it —
and state explicitly whether that replacement runs in the **client SDK** or the **backend SDK**, and
why. Use this division of responsibility:

- **Client SDK** (`@descope/web-js-sdk`, `@descope/react-sdk`, `@descope/nextjs-sdk` client
  components, or the `<descope-wc>` web component) — everything the user's browser or mobile app
  does: rendering the login/sign-up UI (a Descope Flow replaces Stytch UI, `@stytch/react`,
  `@stytch/nextjs`, `@stytch/vanilla-js`, or mobile SDK login flows), initiating authentication,
  holding the session on the client, refreshing the token, and reading the current user for UI
  purposes. This replaces Stytch frontend/mobile providers (`StytchProvider`, `useStytch`,
  `useStytchUser`, `useStytchSession`), headless client calls, and any client-side session access.
  It uses only the public Project ID — never a Management Key.
- **Backend SDK** (`@descope/node-sdk`, `descope` (Python), `github.com/descope/go-sdk`, etc.) —
  everything the server does: validating the session JWT on every request (replacing Stytch
  server-side `sessions.authenticate()` / `sessions.authenticateJwt()` and route middleware),
  checking roles and permissions, and — with a Management Key — all administrative operations done by
  ID (user and tenant CRUD, role/permission definitions, SSO/SCIM configuration, ReBAC). This
  replaces Stytch backend SDK calls (`stytch.sessions`, `stytch.b2b.*`, `stytch.m2m`, etc.) and
  every Stytch Management API call.

For each file or area, name the Stytch call, the Descope SDK that replaces it, which side it runs on,
and the reason (e.g. "session validation must stay server-side because the validation/Management key
cannot ship to the browser"). When one Stytch feature spans both sides — for example a Stytch UI or
mobile login flow (now a client Flow) plus per-request `sessions.authenticateJwt()` validation (now
the backend SDK) — split it into its client half and its backend half so the reader sees exactly what
moves where, and why each piece belongs on that side.

---

#### Auth Touchpoints: What the Code Analysis Found

Open with the scope count (e.g., "11 files across 4 areas"). Group by area, not file path.
Each group gets a sentence on what it does and what changes.

**Session handling (3 files)** — These files read and validate the current user's login
state. They'll be updated to use the Descope session SDK instead of Stytch session
authentication (`sessions.authenticateJwt()`, `sessions.authenticate()`, or frontend
`useStytchSession()`).


| File               | What it does today                                                                                    | What changes                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `lib/auth.ts:34`   | Validates `session_jwt` via `stytch.sessions.authenticateJwt()`; returns `user_id`, `organization_id`, roles | Rewritten to return Descope `authInfo`; a thin adapter layer preserves the shape callers expect |
| `middleware.ts:12` | Reads `stytch_session` cookie and blocks unauthenticated requests app-wide                            | Updated to validate Descope `DS`/`DSR` cookies via Descope session validation; logic is identical, SDK call changes |


**Login / auth UI (2 files)** — These render Stytch UI or run headless Stytch client
flows (magic links, OTP, OAuth, passkeys, B2B discovery). Descope replaces this with an
embedded Flow component (or hosted Flow); token exchange and callback routes change shape.


| File                         | What it does today                                      | What changes                                                                                                  |
| ---------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `app/login/page.tsx`         | Renders `<StytchLogin>` or `useStytch()` headless flow  | Replaced with `<Descope flowId="...">` (or hosted Flow); `onSuccess` wires the Descope session client-side   |
| `app/api/authenticate/route.ts` | Exchanges `token` / `session_token` from Stytch callback | Deleted or rewritten — most flows complete client-side in Descope; verify any server-side exchange against the framework section |


Cover all functional groupings (B2B org/member management, SCIM webhooks, M2M token issuance,
Connected Apps, mobile SDK auth, etc., when present). End with: "Total: N files. Estimated
code-change effort: N–N hours."

---

#### Feature Migration: Stytch → Descope

For each Stytch feature confirmed in triage, write a short paragraph: what it's trying to
accomplish, the best Descope approach for that goal, what's different, and what action is
required. The best approach may be a Flow, Widget, SSO Setup Suite, or Console configuration
rather than a direct SDK equivalent — reason about the intent, not just the API surface. Only
recommend SDK code when programmatic control is genuinely required. Example:

> **Multi-tenancy (Stytch Organizations → Descope Tenants)**
> Stytch multi-tenant auth is built around **Organizations** and **Members**. A Stytch
> Organization represents a tenant/customer in the application, and a Member is a user's account
> within that Organization. Organization-scoped configuration can include SSO connections, SCIM,
> JIT provisioning, approved auth methods, MFA policies, RBAC behavior, custom metadata, and
> Connected Apps settings. Descope has the same core concept, called **Tenants**. In most migrations,
> map one Stytch `organization_id` to one Descope **tenant ID**.
>
> Most code that handles Stytch Organizations is management/admin code that passes a Stytch
> `organization_id` to B2B APIs — for example, loading an organization, updating organization
> settings, managing members, assigning roles, configuring SSO, or configuring SCIM. That becomes
> Descope tenant/user management code that passes a Descope **tenant ID** to the relevant tenant,
> user, SSO, SCIM, or RBAC operation. This is mostly by-ID management work, not token parsing.
>
> The main request-time difference is the session shape. In Stytch B2B, the authenticated session is
> tied to a specific Organization and returns fields such as `member_session.organization_id`,
> `member_session.organization_slug`, `member_session.roles`, the `member` object, and the
> `organization` object. In Descope, tenant membership and tenant-scoped roles/permissions are read
> from the validated session/JWT and should ideally be checked with SDK helpers such as
> `validateTenantRoles(...)` or `validateTenantPermissions(...)` rather than by manually parsing
> claims.
>
> Confirm the Organization→Tenant mapping first, since it ripples into SSO, SCIM, JIT provisioning,
> RBAC, Admin Portal replacement, Connected Apps, and any application database tables that store
> `organization_id`. Also confirm whether Stytch Members can belong to multiple Organizations and
> whether the app supports organization switching, because that determines whether the Descope
> migration needs tenant selection, active-tenant handling, or separate tenant-scoped login routes.

> **Effort: Medium (1–2 hours of code changes).** Confirm the data migration path for orgs first.

Only include confirmed features.

---

#### Before the Code Can Run: Required Configuration

Some Descope behavior is configured in the console, not in code. List every item that must
be set up before the app works, as checkboxes with a plain description of what it is, why
it's needed, and roughly how long it takes. Group into "Required before any testing" and
"Required before production":

**Required before any testing:**

- **Create a Descope project** — Takes 2 minutes. Produces a Project ID that replaces
the STYTCH_PROJECT_ID in the app's environment variables.
- **Create an authentication flow** — Descope uses a visual "flow" to define the login
experience (what methods are offered, in what order). The built-in `sign-up-or-in` flow
works for most apps and requires no customization to start.
- **Configure a user profile token template** — By default, Descope session tokens don't
include the user's name, email, or profile photo. This template needs to be configured so
the app can display user profile information. Without it, any part of the UI that shows the
user's name or email will show nothing after login. (~10 minutes)

**Required before production:**

- **Create tenants for each Stytch Organization** — Descope Tenants must exist before
tenant-scoped code (SSO, roles, membership) will work.
- **Create roles** (or whatever the codebase references) — Descope roles must exist in the
console before code that assigns them will work.
- **Configure SSO connections per tenant** (or enable the SSO Setup Suite for self-serve) — SAML/OIDC connections need to be recreated.
- **Configure social login providers** (Google, GitHub, etc.) — OAuth credentials for
each provider need to be entered in the console. (~15 minutes per provider)
- (continue for each item found in analysis)

---

#### Environment Variables

Diff table with plain-English notes for each removal and addition:


| Remove                              | Add                              | Why                                                                                                                                 |
| ----------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `STYTCH_PROJECT_ID`                 | `DESCOPE_PROJECT_ID`             | Your unique Stytch project ID. Descope uses a Project ID for the same purpose.                                                      |
| `STYTCH_SECRET`                     | `DESCOPE_MANAGEMENT_KEY`         | Backend secret used to securely authenticate Stytch API requests. Descope session validation uses only the Project ID; a Management Key is needed only for server-side user/tenant/SSO/SCIM administration. |
| `NEXT_PUBLIC_STYTCH_PUBLIC_TOKEN` | `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Stytch's frontend-facing token for initializing client SDKs. Descope uses the same value as `DESCOPE_PROJECT_ID`, exposed to the browser for the login Flow component (Next.js and other frontend frameworks).    |


Follow with: "Net change: 2-3 variables removed, 1–3 added. No secrets need to be rotated
on the Stytch side — those credentials stop being used."

---

#### User & Organization Migration (only if existing users/orgs need to be migrated)

Prose strategy first, then steps. Start with: "X existing users across Y organizations need to be in Descope before cutover." Describe:

- **The plan**: whether this is big-bang (all users/orgs moved before cutover) or phased, and why
- **Org→tenant mapping**: each Stytch Organization becomes a Descope Tenant; 
- **What users will experience**: will they need to log in again? Will anything look different?
- **The biggest dependency**: how password credentials carry over, and whether SCIM directories must be re-pointed at Descope (a continuing pipeline, not a one-time import)

End with a brief checklist of the migration steps at the level a PM can track:

- Export users and organizations from Stytch
- Map each Stytch Organization to a Descope Tenant
- Re-point SCIM\ at Descope (if Stytch SCIM is in use)
- Do a dry run of the import against the Descope dev project
- Review dry-run output for errors
- Run live migration against staging, then production

---

#### Risks and Things to Decide

Things that could affect timeline, user experience, or scope. Write each in plain English
with three parts: **what it is**, **what breaks if it's ignored**, and **what to do**.
Format each as a named callout:

> **Risk: Organization-to-tenant mapping affects almost every B2B feature**
> Stytch Organizations should usually map to Descope Tenants. If this mapping is wrong, SSO, SCIM,
> roles, permissions, domain routing, and user membership checks may all break.
> **Action:** Confirm the organization model before writing migration code.

> **Risk: SCIM is a lifecycle system, not just a user import**
> Stytch's SCIM may create, update, suspend, and delete users or group memberships continuously.
> A one-time import is not enough if enterprise directories keep syncing after cutover.
> **Action:** Identify every SCIM/directory workflow and re-point it at Descope before cutover.

> **Risk: Admin Portal UI should not automatically become custom code**
> If the app uses the Stytch Admin Portal UI, the Descope equivalent may be the SSO Setup Suite or a
> Widget rather than a custom settings page.
> **Action:** Ask whether tenant admins currently self-configure SSO/SCIM/domain verification.

> **Risk: User profile data won't appear after login until a token template is configured**
> Descope session tokens don't include name, email, or profile photo by default. Any UI that
> displays user information will show blank values after migration until the token template is set
> up in the Descope console. This is a one-time configuration step, not a code change.
> **Action:** Configure the token template before running any tests. Estimated time: 10 minutes.

Include only applicable risks.

---

#### Execution Plan

Open with one sentence: phases run in sequence; steps within a phase can run in parallel.
Then labeled phases, each with a time estimate:

---

**Phase 1 — Console Setup** (~30–60 minutes, no code required)
Can be done by any team member with Descope console access, in parallel with other work.

- Create Descope project, copy Project ID
- Configure Approved Domains (domain only — e.g. `localhost:3000`, not `http://localhost:3000/authenticate`)
- Create authentication flow (use the built-in `sign-up-or-in` to start)
- Configure user profile token template
- Create tenants for each Stytch Organization (list actual orgs found)
- Create roles: (list actual roles found)
- Configure SSO connections per tenant or enable the SSO Setup Suite (if SSO in use)
- Configure social login providers: (list actual providers found)

**Phase 2 — Code Changes** (~X–Y hours, 1 engineer)
Work through files in the order listed. Run a compile check after each group.

- Update environment variables in `.env.example` and CI config (15 min)
- Rewrite session helper / `withAuth()` usage (30 min)
- Swap AuthKit provider/middleware for Descope equivalents (15 min)
- Update protected route files to use new session check (45 min)
- Repoint org handling to tenant IDs — management calls pass a `tenantId`; request-time session reads use `tenants`/`dct` (varies)
- Update logout — two-step logout (15 min)
- Compile check and fix any type errors before proceeding

**Phase 3 — User & Organization Migration** (~1–2 hours, includes dry run)
Run against dev/staging first. Do not run against production until Phase 4 passes.

- (steps from user & organization migration section above)

**Phase 4 — Testing** (~30–45 minutes)

- Compile passes with zero errors
- Server starts, no crashes on startup
- Unauthenticated routes redirect to login correctly
- Login flow completes, user profile data appears (confirms token template is working)
- Tenant/SSO routing works for at least one organization
- Logout invalidates session

**Phase 5 — Production Cutover**

- (cutover-specific steps based on their strategy — maintenance window, phased rollout, SCIM re-point, etc.)

---

Total estimated engineering effort: **N–N hours** across N engineers.
Blocking dependencies: (list anything on the critical path — console access, SCIM re-point, etc.)

---

After writing `MIGRATION-PLAN.md`, **stop and tell the user:**

> `MIGRATION-PLAN.md` has been written to your working directory. It maps every auth
> touchpoint found, lists what needs Console setup before the first test, and calls out
> risks that could affect the timeline.
>
> Take a look before we start making changes. When you're ready to proceed, say so.

Do not proceed to Part 3 unless the user confirms.

---

## Part 3: Execution

Execute the plan in `MIGRATION-PLAN.md` Execution Plan order. Follow the detailed guidance below
for each step.

---

### Context Continuity Protocol

Context can be lost between turns. These rules keep the migration coherent.

**Step 3.0 — Create `MIGRATION-STATE.md` before touching any code.**

Write `MIGRATION-STATE.md` to the working directory from the template below. It's the
source of truth for migration state — keep it current throughout execution.

```markdown
# Migration State

_Last updated: [timestamp of last completed step]_

## Project Context
- Framework: [e.g., Next.js 14, Express + React]
- Language: [TypeScript / Python / Go]
- Package manager: [npm / yarn / pnpm / pip / etc.]
- Migration goal: [Full cutover / Phased / Evaluating]

## Triage Answers
- Existing users: [Yes — N users / No — greenfield]
- Existing organizations: [Yes — N orgs → tenants / No]
- Password migration needed: [Yes / No]
- Stytch features in use: [comma-separated list]
- Multiple environments: [Yes: dev/staging/prod / No]
- Zero-downtime required: [Yes / No]

## Files Inventory
_All files that need to change. Update status after each step._

| File | Change | Status |
|---|---|---|
| `app/callback/route.ts` | Delete/rewrite | ⬜ Pending |
| `lib/auth.ts` | Rewrite session helper | ⬜ Pending |
| `middleware.ts` | Update session check | ⬜ Pending |

## Console Setup Checklist
- [ ] Descope project created — Project ID: (fill in when done)
- [ ] Approved Domains configured (domain only — e.g. `localhost:3000`, not `http://localhost:3000/authenticate`)
- [ ] JWT template configured
- [ ] Tenants created for each Stytch Organization: (list)
- [ ] Roles created: (list roles)
- [ ] SSO connections / SSO Setup Suite configured: (list)
- [ ] Social providers configured: (list providers)

## Decisions Log
_Non-obvious decisions made during migration — preserves rationale if context is lost._

_(none yet)_

## Current Phase
Phase 1 — Console Setup (not started)

## Next Action
Complete console setup per MIGRATION-PLAN.md before making any code changes.

## Blockers
_(none)_
```

---

**Rule 1 — Re-read before every turn.**

At the start of every execution turn, re-read `MIGRATION-PLAN.md` and `MIGRATION-STATE.md`
before writing any code or making any decision.

**Rule 2 — Verify context before every code change.**

If the framework, migration path, triage answers, or next step aren't clear from the
conversation, re-read both files before proceeding. Then output a context line:

> `Migration context: Next.js 14 · Phase 2, step 3/8 · Next: rewrite lib/auth.ts`

If this line can't be filled in accurately, re-read the files first.

**Rule 3 — Update `MIGRATION-STATE.md` immediately after each step.**

Mark the file done in the Files Inventory, update "Current Phase" and "Next Action", and
append any non-obvious decision to the Decisions Log. Do this before the next step.

---

## Pre-Generation Protocol (apply before writing any code)

Run before generating any import, wrapper type, or helper. Skipping produces code that
compiles but fails at runtime.

**1. Verify SDK exports before writing any import.**
When the Docs MCP is available, use `ask-question-about-descope` to confirm the exact method name, option shape, and return type before writing any SDK call. This is faster and more reliable than reading type declarations. Do not write a method name and add a hedge like "verify the exact name" — just verify it.

When the Descope MCP server is unavailable: resolve the package's type declarations (`node_modules/<pkg>/dist/types/` or its `package.json` `types` field) and confirm the exact exported name and signature. For Go, run `go doc`. For Python, check the SDK stubs.

**Prefer local `node_modules/` over GitHub** when reading type declarations. Installed packages reflect the exact version in use. If the Descope package isn't installed yet, install it first, then read local type declarations. Only fall back to GitHub if the package can't be installed in the current environment.

This applies to **every SDK call you write**, not just the first import. Field names on
option objects, hook return shapes (`useDescope()` returns the SDK directly, not `{ sdk }`),
and subpath exports (`/client` vs root) differ just as often.

**1a. After rewriting any module, grep for remaining imports of the removed package.**

```bash
grep -r "from '@stytch/\|from 'stytch'\|from \"stytch\"" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" .
```

Add remaining hits to the work list.

**2. Derive wrapper types from the actual return type.**
Read the function's declared return type and build the wrapper to match. Stytch's field
names, nesting, and flags differ — don't infer from them.

**3. Check dependency versions before generating framework-specific code.**
For Next.js: `cookies()` and `headers()` from `next/headers` are synchronous in v14 and
async in v15. Read `package.json` (or `go.mod`, `requirements.txt`) first.

**4. When making a helper async, propagate to all callers immediately.**
In TypeScript, `async` on a shared utility silently breaks callers that omit `await`. Grep
for all call sites of the changed function and update them in the same pass. The cascade can
span 10–20 files.

**5. Verify published package versions before writing to `package.json` or running `npm install`.**
Don't reuse Stytch's version number or rely on training data for versions. Before writing any
install command:

```bash
npm view @descope/node-sdk version
npm view @descope/nextjs-sdk version
```

If npm is unavailable, leave the version as `"latest"` and flag it.

---

## Step 1.5: Descope Project Setup & Console Configuration

Several steps require Descope Console setup that can't be done in code. The app compiles
without them but won't work at runtime.

Use `AskUserQuestion` to ask whether they already have a Project ID and working Flow. If
yes, skip to verifying items 5–8 — these are easy to miss even for existing projects.

### 1. Create a project and get your Project ID

- Sign in at [console.descope.com](https://console.descope.com)
- Your **Project ID** appears in the top-left project selector and under **Project → General**. It starts with `P` (e.g. `P2abc123...`).
- For Next.js client-side code, this becomes `NEXT_PUBLIC_DESCOPE_PROJECT_ID`. For all server-side SDKs, it's `DESCOPE_PROJECT_ID`.

### 2. Get a Management Key (if needed)

Required for: user management API, role/permission management, tenant operations, SSO/SCIM
configuration, ReBAC (FGA), Outbound Apps. If the app does any server-side user, tenant, SSO,
or SCIM management, they need this.

- Console → **Company → Management Keys → + Management Key**
- Store as `DESCOPE_MANAGEMENT_KEY`. Treat like a secret — never expose client-side.

### 3. Choose or create a Flow

A Flow is the auth UI sequence. Reference it by Flow ID in the web component.

- Console → **Flows**
- The built-in **"sign-up-or-in"** flow handles email/password, OTP, and social login.
Use it for most migrations.
- To customise: duplicate "sign-up-or-in", rename it, then edit in the visual builder.
- The Flow ID is in the URL when editing and in the flow list.
- There are 100+ Flow templates in the library — check for an existing template before building a custom flow. See `references/flows-and-widgets.md` → Flows.
- MFA: add an MFA step to the Flow or embed MFA as a subflow. Descope manages MFA enrollment through Flows. For factor-deletion SDK support by type, see `references/implementation-nuances.md` → MFA section.

### 4. Configure authentication methods

- Console → **Authentication** → select methods (Email OTP, Magic Link, Social, SSO, Passkeys, etc.)
- For social providers (Google, GitHub, etc.): configure OAuth credentials here, then add
the provider step to your Flow.
- For enterprise SSO (SAML/OIDC): To configure SSO for a specific tenant or to enable the SSO Setup Suite for tenant-admin self-serve, go to Console → **Tenants**, select the desired tenant, and click **Tenant Settings**. For correct SSO callback and ACS URLs (social OAuth, SAML ACS, what NOT to use), see `references/implementation-nuances.md` → Social login / SSO section.

### 5. Configure Approved Domains (local dev and production)

Console → **Project Settings → Security → Approved Domains**.

Descope validates redirect URLs against this domain list — **not** full redirect URIs like Stytch.
Enter **domain only**: no `http://`/`https://`, no path.

- Local dev: `localhost:3000` (include port)
- Production: `myapp.com` or `app.myapp.com`

**Do not** carry over Stytch callback URLs like `http://localhost:3000/authenticate`. Descope
embedded Flows complete auth client-side; there is no `/authenticate` route to whitelist. See
`references/implementation-nuances.md` → Approved Domains gotcha.

### 6. Configure a JWT Template (almost always needed)

Stytch tokens may include profile fields; Descope tokens do not by default.

- Console → **Project → JWT Templates**
- Add claims: `{"email": "{{user.email}}", "name": "{{user.name}}", "picture": "{{user.picture}}"}`
- Apply the template to your project. Without this step, any code reading `token.email`
will get `undefined` after migration.

### 7. Create roles in the Console (if using RBAC)

Descope roles are referenced by **name**, not by ID. They must be created manually in the
Console before the code that assigns them will work.

- Console → **Authorization → RBAC → + Role**
- Create each role the app references (e.g. `admin`, `member`)

### 8. Define custom attributes (if using Stytch metadata)

Stytch metadata maps to Descope customAttributes, but the models are slightly different. Stytch
stores arbitrary JSON in metadata fields, while Descope custom attributes should be pre-defined in the
Console schema before setting them via the SDK.

Tenant custom attributes: map Stytch Organization trusted_metadata to Descope tenant
customAttributes. Configure these in Console → Tenants → Custom Attributes tab → Create
Attribute. 
User custom attributes: map Stytch Consumer User trusted_metadata and safe B2B Member
trusted_metadata to Descope user custom attributes. Configure these in Console → Project →
Custom Attributes.

### 9. Env var summary


| Variable                         | Where to get it                     | Used by                                     |
| -------------------------------- | ----------------------------------- | ------------------------------------------- |
| `DESCOPE_PROJECT_ID`             | Console → Project Settings          | All server-side SDKs                        |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value as above                 | Next.js `AuthProvider` (client-side)        |
| `DESCOPE_MANAGEMENT_KEY`         | Console → Company → Management Keys | Management SDK, SSO/SCIM, Outbound Apps API |


### 10. Consider Widgets for management UI

Before migrating custom profile pages, user management pages, role assignment UI, or admin
SSO/SCIM setup pages, ask whether a Descope Widget or the SSO Setup Suite covers the use case.
See `references/flows-and-widgets.md` → Widgets.

**After completing console setup:** Update `MIGRATION-STATE.md` — check off each completed
item in the Console Setup Checklist, record the Project ID in the file, and set Next Action
to the first code change step.

---

## Step 2: Framework-Specific Migration

Stytch publishes three SDK families:

- **Backend SDKs** (one per language): `stytch-node` (`stytch`), `stytch-python` (`stytch`), `stytch-go`, `stytch-ruby`, `stytch-java` (Java/Kotlin/JVM). These call the Stytch API and authenticate sessions server-side.
- **Frontend SDKs** (per JS framework): `@stytch/react`, `@stytch/nextjs`, `@stytch/vanilla-js`. These render the login UI (Stytch UI or headless) and hold the client session.
- **Mobile SDKs**: `@stytch/react-native`, the iOS Swift SDK, and the Android Consumer SDK (a headless Kotlin Multiplatform library targeting Android).

The recipes below map each Stytch SDK to its Descope target — one section each. A Stytch app on a server framework not listed (Express, Flask, FastAPI, Rails, Spring) is using the underlying language Backend SDK (`stytch-node`, `stytch-python`, etc.), so map it via that SDK's section.

> The framework recipes below are stubs listing the Stytch idioms that need mapping. Confirm the exact Stytch SDK surface for the user's stack and the matching Descope SDK calls via the Descope MCP or local type declarations before generating any code. Do not ship code from these stubs without verification.

Read `references/implementation-nuances.md` in two passes before writing any code:

1. **General Insights** (always) — covers architecture, feature mapping, and common gotchas that apply to every migration regardless of framework.
2. **Framework section** (use the file's ToC and `offset` to jump directly) — read only the section matching the user's stack.

When a new framework is added to the file, add it to this list.

### Common Stytch idioms to map (all frameworks)

Frontend Stytch SDKs expose UI components and client session hooks; backend SDKs authenticate the
session server-side. The mappings below apply across stacks:

- Stytch UI (`<StytchLogin>` / `<StytchB2B>`) or headless `useStytch()` login → embedded Descope Flow (`<Descope flowId>` / `<descope-wc>`) or hosted Flow, wiring `onSuccess`
- `useStytchSession()` / `useStytchUser()` (client session access) → Descope `useSession()` / `useUser()` hooks, with `useDescope()` for actions
- Backend `client.sessions.authenticate()` / `client.sessions.authenticateJwt()` → Descope backend `validateSession()` + an adapter returning the shape callers expect
- Stytch session cookies (`stytch_session`, `stytch_session_jwt`) → Descope signed session JWT in `DS` / `DSR` cookies
- Stytch magic-link / OAuth callback route (`client.magicLinks.authenticate()` / `client.oauth.authenticate()`) → removed/rewritten; Descope completes auth client-side

### Backend SDKs

#### Node.js

*Stytch SDK: `stytch` (`stytch-node`) → Descope `@descope/node-sdk`*

- Remove `stytch` auth/session usage; add `@descope/node-sdk`
- Replace `client.sessions.authenticateJwt()` / `client.sessions.authenticate()` with custom middleware calling `descopeClient.validateSession(sessionToken)` against the `DS` cookie (parse the cookie yourself)

#### Python

*Stytch SDK: `stytch` (`stytch-python`) → Descope `descope` Python SDK*

- Remove the Stytch Python SDK auth/session usage; add the `descope` Python SDK
- Validate the `DS` session token with `descope_client.validate_session(session_token=session_token)` (or validate against Descope's JWKS for a custom authorizer)

#### Go

*Stytch SDK: `stytch-go` → Descope Go SDK `github.com/descope/go-sdk`*

- Remove the Stytch Go SDK; add `descope/go-sdk`
- Session validation: `descopeClient.Auth.ValidateSessionWithToken(ctx, token)` returns `(bool, *descope.Token, error)`
- Stytch `organization_id` → a Descope **tenant ID**: pass it to management calls (`descopeClient.Management.Tenant()` / user-tenant association); at request time read tenant context off the returned `*descope.Token` (`token.GetTenants()`, or the `dct` claim for the active tenant)

#### Ruby

*Stytch SDK: `stytch-ruby` → Descope Ruby SDK*

- Remove the Stytch Ruby SDK; add the Descope Ruby SDK
- Validate the `DS` session token with `descope_client.validate_session(session_token: session_token)` in your request lifecycle
- No dedicated recipe in `implementation-nuances.md` yet — follow the Node.js / Python backend patterns and verify against the [Descope Ruby SDK](https://github.com/descope/descope-ruby-sdk).

#### Java / Kotlin (JVM)

*Stytch SDK: `stytch-java` (Java/Kotlin/JVM) → Descope `descope-java`*

- Remove the Stytch Java SDK; add `descope-java`
- Validate the `DS` token via a filter/interceptor: `authenticationService.validateSessionWithToken(sessionToken)` returns a `Token`
- No dedicated recipe yet — follow the backend patterns and verify against the [Descope Java SDK](https://github.com/descope/descope-java).



### Frontend SDKs

> **Read the session the framework-native way — never hand-parse the JWT on the client.** On
> front-end pages and components, get auth state from the Descope hooks: `useSession()` for the
> session token and auth status, `useUser()` for the user profile, and `useDescope()` for actions
> like `logout()`. Do **not** manually decode the session token or pull claims out of it in client
> code. Server-side session *validation* — `session()` in `@descope/nextjs-sdk/server`,
> `validateSession()` in `@descope/node-sdk` (or the other backend SDKs) — belongs only in backend
> routes, middleware, and API handlers, never in a rendered client component. This matters
> most with the **React SDK**, where it's tempting to crack open the raw token in a component instead
> of calling `useUser()` / `useSession()`.

#### Vanilla JS

*Stytch SDK: `@stytch/vanilla-js` → Descope `@descope/web-js-sdk` + `@descope/web-component`*

- Stytch headless client (`createStytchUIClient` / `StytchHeadlessClient`) session access → `@descope/web-js-sdk` (`getSessionToken()`, `isJwtExpired()`, `refresh()`)
- Stytch UI login → `<descope-wc project-id flow-id>` web component, listening for `success` / `error` events
- Logout: `sdk.logout()` + clear stored tokens/cookies

#### React

*Stytch SDK: `@stytch/react` → Descope `@descope/react-sdk`*

- `<StytchProvider>` → Descope `<AuthProvider projectId>`
- Stytch UI (`<StytchLogin>`) / headless `useStytch()` login → embedded `<Descope flowId>` component, wiring `onSuccess`
- `useStytchSession()` / `useStytchUser()` → Descope `useSession()` + `useUser()` hooks, with `useDescope()` for actions
- **Always read auth state through the hooks** — never decode the session token by hand in a component, and never call backend `validateSession()` from client code; that runs only on the server.
- Logout: `sdk.logout()` via `useDescope()` hook
- No dedicated recipe yet — follow the Next.js client-side patterns and verify each method against docs.

#### Next.js

*Stytch SDK: `@stytch/nextjs` → Descope `@descope/nextjs-sdk` + `@descope/node-sdk`*

- `@stytch/nextjs` → `@descope/nextjs-sdk` + `@descope/node-sdk`
- `<StytchProvider>` → Descope `AuthProvider` (takes `projectId`; must use `NEXT_PUBLIC_` prefix)
- Server `client.sessions.authenticateJwt()` → `session()` (server); client `useStytchSession()` / `useStytchUser()` → `useSession()` / `useUser()`
- Remove the Stytch magic-link / OAuth callback route — verify Descope's client-side handling
- Stytch session middleware → Descope `authMiddleware(options)`
- Logout: `sdk.logout()` via `useDescope()` hook + clear cookies (two-step)
- **Client vs. server session access** — `session()` from `@descope/nextjs-sdk/server` is server-only; `useSession()`/`useUser()` from `@descope/nextjs-sdk/client` are client-only. Using `session()` in a client component compiles but throws at runtime. Verify exact exports before writing imports.

### Mobile SDKs

#### React Native

*Stytch SDK: `@stytch/react-native` → Descope `@descope/react-native-sdk`*

- Stytch UI / headless client login → run a Descope Flow via the React Native SDK (or hosted Flow)
- Stytch session access/storage → Descope React Native SDK session management
- Logout: Descope SDK logout + clear the stored session
- No dedicated recipe yet — verify methods against the [Descope React Native SDK](https://github.com/descope/descope-react-native-sdk).

#### iOS (Swift)

*Stytch iOS Swift SDK → Descope `descope-swift`*

- Stytch login (UI or headless) → run a Descope Flow via the Swift SDK, or hosted Flow
- Stytch session validation/refresh → Descope Swift SDK session APIs
- No dedicated recipe yet — verify against the [Descope Swift SDK](https://github.com/descope/swift-sdk).

#### Android (Kotlin)

*Stytch Android Consumer SDK (headless Kotlin Multiplatform) → Descope `descope-kotlin`*

- Headless Stytch client login → run a Descope Flow via the Android/Kotlin SDK, or hosted Flow
- Stytch session validation/refresh → Descope Kotlin SDK session APIs
- No dedicated recipe yet — verify against the [Descope Android/Kotlin SDK](https://github.com/descope/descope-kotlin).

**After completing framework code changes:** Update `MIGRATION-STATE.md` — mark each
modified file as Done in the Files Inventory, update Current Phase and Next Action, and
log any non-obvious decisions made (adapter types kept, async cascade scope, etc.).

---

## Step 2.5: Non-Code File Updates

Scan for Stytch references in non-code files after updating source files.

### `.env.example` / `.env.template` / `.env.sample`

```
# REMOVE
STYTCH_PROJECT_ID=
STYTCH_SECRET=
STYTCH_PUBLIC_TOKEN=
NEXT_PUBLIC_STYTCH_PUBLIC_TOKEN=

# ADD
DESCOPE_PROJECT_ID=             # Console → Project Settings
NEXT_PUBLIC_DESCOPE_PROJECT_ID= # Next.js / frontend — same value as above
DESCOPE_MANAGEMENT_KEY=         # Console → Company → Management Keys (replaces STYTCH_SECRET for admin APIs)
```

Run `grep -ir "STYTCH"` to find all env var references — `.env.example`, Docker, CI, shell scripts.

### README / docs

Search all `.md` files for Stytch references. At minimum, update:

- **Setup section** — replace "create a Stytch app" instructions with Descope Console setup steps
- **Environment variables section** — reflect the reduced env var set
- **Run instructions** — replace Stytch dashboard steps with Descope Console steps
- **Auth flow diagrams or descriptions** — update to reflect Descope's cookie-based approach

### Docker / CI files

Check `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, and any CI config for
`STYTCH_`* env var declarations. Update them to `DESCOPE_`*.

### Setup / bootstrap scripts

When the migration includes a setup or seed script (e.g., `scripts/bootstrap.mjs`, `scripts/seed.ts`), split it into two parts:

1. **Console setup** (cannot be scripted): Flows, email templates, MFA configuration, branding/Styles, SSO Setup Suite — configure these in the Descope Console. Represent them as a Phase 1 checklist in `MIGRATION-PLAN.md`.
2. **SDK automation** (can be scripted): role creation (`management.role.create()`), tenant creation, access key provisioning, SSO/SCIM config. Preserve these as a Node.js/Python script using the Descope Management SDK.

**After completing non-code file updates:** Update `MIGRATION-STATE.md` — mark env files,
README, and CI config done in the Files Inventory, and advance Next Action.

---

## Step 3: Feature Migration Mapping

For each Stytch feature confirmed in triage, write a short paragraph: what it accomplishes, the
best Descope approach for that goal, what's different, and what action is required. Reason about
intent, not just the API surface — the best approach may be a Flow, Widget, SSO Setup Suite, Inbound
App, Outbound App, Console configuration, or tenant configuration rather than a direct SDK equivalent.
Only recommend SDK/API code when programmatic control is genuinely required, and verify every method
name against the Descope MCP server before writing it. Include only confirmed features.

### Consumer Authentication → Descope Flows + Auth Methods + JWT Templates

Stytch Consumer Authentication handles user-facing authentication for B2C applications, including
hosted/prebuilt UI, frontend SDK flows, backend API flows, users, sessions, and sign-in methods such as
OAuth/social login, email magic links, OTPs, passwords, passkeys/WebAuthn, mobile biometrics, MFA,
TOTP, and crypto wallet auth. Descope splits these responsibilities across **Flows** for the user
journey, Descope authentication methods, Users, session validation, and JWT Templates / custom claims
for token shaping.

| Stytch                                  | Descope                                                              |
| --------------------------------------- | -------------------------------------------------------------------- |
| Stytch UI / prebuilt login UI           | [Descope Flows](https://docs.descope.com/flows)                      |
| Frontend SDK auth flows                 | Descope frontend SDK + Flow component                                |
| Backend API-driven auth                 | Descope backend SDK / API auth methods when Flows are not sufficient |
| OAuth/social login                      | Descope OAuth/social login methods                                   |
| Email magic links                       | Descope Magic Link / Enchanted Link                                  |
| Email/SMS/WhatsApp OTP                  | Descope OTP methods                                                  |
| Passwords                               | Descope Passwords                                                    |
| Passkeys / WebAuthn                     | Descope Passkeys                                                     |
| TOTP / MFA                              | Descope MFA / TOTP / Flow conditions                                 |
| Stytch User object                      | Descope User                                                         |
| Stytch session token / session JWT      | Descope session token / JWT + backend session validation             |
| Stytch custom claims / session metadata | Descope JWT Templates or Custom Claims action                        |

Use Flows for the user-facing journey whenever possible; write custom SDK calls only when Flows
cannot express the requirement. Ask which Stytch auth methods are enabled, whether Stytch UI or custom
UI is used, and whether any backend routes call Stytch APIs directly. **Effort: Low–Medium** for
straightforward B2C auth, higher if custom session claims, MFA branching, or nonstandard auth factors
are involved.

### Multi-tenant / B2B Authentication → Descope Tenants + Users

Stytch B2B authentication is built around **Organizations** and **Members**. Descope maps this model
most closely to **Tenants** and **Users associated with tenants**. A Stytch Organization usually
becomes a Descope Tenant, while a Stytch Member usually becomes a Descope User with tenant membership,
roles, permissions, and tenant-specific attributes.

| Stytch                                        | Descope                                                        |
| --------------------------------------------- | -------------------------------------------------------------- |
| Organization                                  | Tenant                                                         |
| Member                                        | User associated with a tenant                                  |
| Organization ID                               | Tenant ID                                                      |
| Organization metadata                         | Tenant `customAttributes`                                      |
| Member metadata                               | User custom attributes or tenant-specific user metadata        |
| Organization-specific auth settings           | Tenant settings + Flow logic + SSO configuration               |
| Member invitations                            | Invitation Flow / management SDK flow                          |
| Organization discovery                        | Tenant discovery / tenant selection / domain-based routing     |
| Org-specific login                            | Tenant-specific login route, tenant slug, or tenant Flow input |
| Organization session exchange / org switching | Active tenant selection and tenant-aware session claims        |
| Members belonging to multiple Organizations   | Users belonging to multiple tenants                            |

Confirm the one-Stytch-Organization-to-one-Descope-Tenant mapping before writing code. This mapping
ripples into SSO, SCIM, RBAC, JIT provisioning, sessions, custom claims, and domain routing. Also
check whether the application treats `organization_id` as an authorization boundary, a billing
boundary, a data partition key, or all three. **Effort: Medium** — conceptually clean, but application
code often assumes Stytch's Organization/Member object shapes.

### Organizations and Members → Descope Tenant and Users

Stytch Organizations and Members are not just data objects; they may drive onboarding, invitations,
membership updates, deactivation, organization switching, metadata, and tenant-specific access
controls. In Descope, model these workflows using Tenants, Users, tenant membership, roles,
permissions, and optionally Flows or management SDK calls for lifecycle operations.

| Stytch                            | Descope                                                   |
| --------------------------------- | --------------------------------------------------------- |
| Create/update Organization        | Create/update Tenant                                      |
| Create/update Member              | Create/update User and tenant association                 |
| Organization metadata             | Tenant custom attributes                                  |
| Member metadata                   | User custom attributes / tenant-specific user attributes  |
| Member invite                     | Invite/onboarding Flow or management SDK                  |
| Member deactivate/delete          | User deactivation, tenant removal, or tenant-role removal |
| Organization allowed auth methods | Tenant settings + Flow conditions                         |
| Organization-specific MFA policy  | Tenant-aware MFA logic in Flows                           |

Ask whether Organization and Member data is synchronized into the app database, whether the app reads
Stytch as the source of truth, and whether lifecycle changes trigger webhooks. **Effort: Medium** —
especially if membership state is mirrored in the application database.

### Enterprise SSO → Descope Tenant SSO

Stytch Enterprise SSO maps to Descope tenant-level SSO. In Stytch, SSO connections are associated
with Organizations. In Descope, SSO is configured per Tenant, with support for SAML/OIDC providers,
domain-based routing, SSO Setup Suite, and multiple SSO providers per tenant when needed.

**Preferred approach — SSO Setup Suite:** before migrating any Stytch SSO management code, ask whether
the no-code SSO Setup Suite removes the need for that code. It guides tenant admins through per-tenant
SAML/OIDC setup with IdP-specific instructions (Okta, Microsoft Entra ID, Google Workspace, etc.) and can reduce engineering involvement for new
enterprise customer onboarding.

**Multiple SSO configurations per tenant.** If a single Stytch customer has multiple SSO connections,
or if the old Stytch model used multiple Organizations to represent one customer with multiple IdPs,
do not blindly create multiple Descope Tenants. First decide whether the customer should become one
Descope Tenant with multiple SSO configurations.

| Stytch                                 | Descope                                                   |
| -------------------------------------- | --------------------------------------------------------- |
| Organization SSO connection            | Tenant SSO configuration                                  |
| SAML SSO                               | Descope SAML SSO                                          |
| OIDC SSO                               | Descope OIDC SSO                                          |
| Organization-specific SSO routing      | Tenant routing / SSO domain routing                       |
| Multi-Organization SSO behavior        | Tenant design + active tenant/session model review        |
| Customer-admin SSO setup               | SSO Setup Suite                                           |
| SSO claim/group role assignment        | SSO attribute mapping / group-to-role mapping             |
| Programmatic SSO connection management | Descope Management API / SDK, if self-service is not used |

Use `AskUserQuestion` to ask **two** things here:

1. Does any single customer use **multiple IdPs** or multiple Stytch Organizations to represent the
   same real-world customer?
2. Does the app need **programmatic** SSO configuration, or do customer admins configure SSO
   themselves?

For runtime login, prefer Descope's SSO-specific login path rather than generic social OAuth logic.
The exact SDK method names differ by language/framework, so verify against the Descope MCP server
before writing implementation code. Rule of thumb: tenant/enterprise SSO should use Descope's
tenant-level SSO configuration; social login should use OAuth/social auth methods. **Effort: Medium**

### SCIM / Directory Sync → Descope SCIM / Tenant Provisioning

Stytch SCIM / Directory Sync maps to Descope SCIM provisioning. **Treat this as a continuing
provisioning pipeline, not a one-time import** — enterprise directories keep pushing create, update,
group, and deprovisioning events after cutover. Every customer directory must be re-pointed from
Stytch to Descope before cutover, or provisioning will silently break.

| Stytch SCIM / Directory Sync             | Descope                                                |
| ---------------------------------------- | ------------------------------------------------------ |
| SCIM endpoint per Organization           | Descope SCIM endpoint / token per tenant               |
| Directory user create/update/deactivate  | Tenant user provisioning lifecycle                     |
| Directory groups                         | External groups / group-to-role mapping                |
| SCIM group-to-role assignment            | SCIM or SSO group mapping to Descope roles             |
| Directory deprovisioning                 | User deactivation / tenant access removal behavior     |
| SCIM tokens                              | Tenant-scoped SCIM-compatible access keys              |
| SCIM webhooks / downstream sync handlers | Descope events, audit logs, webhooks, or app sync code |

Identify every connected directory, which IdPs are used, whether groups are synced, whether groups map
to roles, and what happens when a user is removed from a directory group. Pay special attention to
whether Stytch deprovisioning revoked sessions immediately, removed membership, changed roles, or only
updated status. **Effort: Medium–High** — lifecycle, groups, deprovisioning, and role mapping can be
subtle.

### Admin Portal → Descope SSO Setup Suite / Admin Widgets

Stytch Admin Portal provides customer-admin workflows for managing enterprise configuration such as
SSO, SCIM, organization settings, members, and related admin tasks. Do not default to rebuilding these
screens as custom code.

* Stytch Admin Portal link generation → SSO Setup Suite link or Descope Admin Widget link
* SSO setup screens → SSO Setup Suite
* SCIM setup screens → SSO Setup Suite SCIM setup or tenant SCIM configuration
* Member management screens → Tenant Profile Widget / Admin Widgets, if applicable
* Organization settings screens → Tenant Profile Widget / custom admin UI backed by Descope tenant APIs
* RBAC/role management screens → Descope Console, Admin Widgets, or custom UI depending on requirements

Ask which Stytch Admin Portal workflows are actually used today. If a Descope Widget or SSO Setup
Suite covers the workflow, prefer that over custom migration code. **Effort: Medium** — may remove
custom code, but generated portal-link workflows need replacement.

### RBAC → Descope RBAC


Stytch RBAC is a structured role-based model built from Resources, Actions, Permissions, and Roles.
A Stytch Permission is the combination of a `resource_id` and an `action` — for example,
`documents:read` or `employees:update` — and Roles are collections of those permissions assigned to
Members. Stytch evaluates these permissions using its RBAC policy, either through frontend SDK helpers
such as resource/action authorization checks or backend session/JWT authentication calls that include
an `organization_id`, `resource_id`, and `action`. Descope RBAC is flatter. Descope has Roles and Permissions, 
but permissions are strings rather than first-class Resource + Action objects. When migrating Stytch RBAC to Descope RBAC,  
encode each Stytch `resource_id + action` pair as a Descope permission string using a consistent naming convention such
as `resource.action` or `resource:action`.

In Descope, roles and permissions can be created and assigned at both the project and tenant levels.
For most Stytch migrations, start by mapping Stytch role definitions to Descope project-level roles,
then assign those roles to users in the relevant tenant context. Only create Descope tenant-level role
definitions when the source application has tenant-specific role definitions or tenant-specific
permission sets, rather than merely tenant-specific role assignments.

| Stytch                           | Descope                                        |
| -------------------------------- | ---------------------------------------------- |
| Resource                         | Encoded in permission string          |
| Action                           | Encoded in permission string            |
| Permission = Resource + Action   | Permission                                     |
| Role                             | Role                                           |
| Project-level RBAC policy | Project-level role/permission catalog |
| Role definition in RBAC policy | Usually project-level role |
| Member role assignment inside an Organization | User role assignment in a tenant |
| Same user has different roles in different Organizations | Same user has different roles in different tenants |
| Tenant-specific/custom role catalog | Use Descope tenant-level roles only if this behavior actually exists in the app |

Check whether Stytch roles are used only for UI gating or also for backend authorization. Also check
whether roles/permissions are expected in tokens, whether the app stores role assignments in its own
database, and whether SSO/SCIM mappings are the source of truth. **Effort: Medium** for normal RBAC;
higher if RBAC is mixed with Connected Apps scopes or app-defined resource authorization.

### Authorization Beyond RBAC

If the Stytch app has authorization **beyond RBAC** — relationship-based or per-resource checks such
as project membership, document ownership, workspace hierarchy, or shared/delegated access — do not
assume a plain RBAC migration covers it. This maps to Descope ReBAC/FGA (only when the model truly
depends on relationships between entities) or stays in the application database.

See `references/implementation-nuances.md` → **Authorization beyond RBAC → Descope ReBAC** for the
decision guide, an example schema, the recommended-approach table, and effort estimate.

### JIT Provisioning → Descope JIT Provisioning / Tenant Association

Stytch supports JIT provisioning for adding users or Members to Organizations based on login context,
email domains, SSO, or other allowed provisioning sources. Descope supports tenant association,
domain-based routing, SSO-driven provisioning, SCIM, and Flow-based tenant/user logic.

**Important:** decide whether the source of truth is JIT, SCIM, or pre-created membership. Mixing all
three without clear precedence can produce duplicate accounts, unexpected tenant access, or confusing
role assignment behavior.

| Stytch                              | Descope                                       |
| ----------------------------------- | --------------------------------------------- |
| Email-domain JIT provisioning       | Tenant self-provisioning domains / Flow logic |
| SSO JIT provisioning                | SSO JIT provisioning / tenant association     |
| Organization allowed domains        | Tenant domains / self-provisioning domains    |
| Member created on first login       | User association with tenant during login     |
| JIT role assignment from SSO claims | SSO group/attribute mapping to roles          |
| JIT plus SCIM                       | Explicit SCIM-vs-JIT design decision          |

Ask which provisioning sources are enabled in Stytch and what happens if a user signs in before SCIM
has provisioned them. **Effort: Medium** — low if only email-domain JIT is used, higher if SSO/SCIM
role assignment also depends on JIT.

### MFA and Step-up Authentication → Descope MFA / Flow Conditions

Stytch MFA and step-up authentication can involve OTPs, TOTP, passkeys/WebAuthn, passwords, OAuth,
magic links, and organization-specific MFA requirements. Descope maps this to MFA methods and
conditional Flow logic.

Use Flows for MFA whenever possible because MFA is usually part of the user journey, not just a backend
API call. Flow conditions can branch based on user state, tenant context, risk signals, completed auth
methods, or sensitive actions.

| Stytch                             | Descope                                            |
| ---------------------------------- | -------------------------------------------------- |
| SMS/email OTP MFA                  | Descope OTP MFA                                    |
| TOTP MFA                           | Descope Authenticator Apps / TOTP                  |
| Passkey/WebAuthn as MFA or step-up | Descope Passkeys / WebAuthn                        |
| Organization-specific MFA policy   | Tenant-aware Flow condition                        |
| Step-up for sensitive actions      | Step-up Flow or backend-triggered reauth pattern   |
| Risk-based MFA                     | Flow condition using risk signals / fingerprinting |
| Recovery codes / fallback behavior | Confirm support and design fallback explicitly     |

Ask whether MFA is required globally, per organization, per role, per risk level, or only for sensitive
actions. **Effort: Low–Medium** unless MFA is deeply customized or risk-based.

### Sessions and Tokens → Descope Session Management + JWT Templates

Stytch sessions may use `session_token`, `session_jwt`, intermediate sessions, cookies, custom claims,
organization context, and session revocation. Descope sessions should be validated with the appropriate
backend SDK/session validation path, and claims should be shaped with JWT Templates or Flow Custom
Claims where appropriate.

| Stytch                          | Descope                                                 |
| ------------------------------- | ------------------------------------------------------- |
| `session_token`                 | Descope session token                                   |
| `session_jwt`                   | Descope JWT                                             |
| Intermediate sessions           | Flow-driven intermediate state / MFA / step-up handling |
| Organization context in session | Tenant claims / active tenant context                   |
| Custom claims                   | JWT Templates or Custom Claims action                   |
| Session revocation              | Descope session/user logout or revocation pattern       |
| Cookie-based sessions           | Descope SDK cookie/session configuration                |
| Backend session authentication  | Descope backend session validation                      |

Search the codebase for direct reads of Stytch session fields, token claims, organization/session
exchange calls, and middleware that assumes Stytch-specific token shapes. **Effort: Medium** — token
differences often affect middleware, API routes, and frontend hydration.

### Fraud & Risk / Device Fingerprinting → Descope Fingerprinting + Flow Security

Stytch Fraud & Risk centers on Device Fingerprinting, verdicts, decisioning, bot prevention,
credential stuffing defense, account takeover prevention, toll fraud reduction, new-device detection,
remembered devices, IP-geo restrictions, and abuse prevention. Descope supports built-in
fingerprinting and risk signals that can be used inside Flows, and can be combined with CAPTCHA or
fraud connectors when needed.

**Mechanism difference:** Stytch Device Fingerprinting and **Protected Auth** (a frontend/mobile SDK
layer that automatically attaches fingerprint telemetry to login/signup calls and enforces allow,
challenge, block, or monitor-only outcomes) can be embedded directly in Stytch SDK auth calls. In
Descope, there is no equivalent SDK toggle — recreate both with Flow-based risk handling: collect
risk signals, branch on the result, and decide whether to allow, challenge, block, or notify.

| Stytch Fraud & Risk            | Descope                                                  |
| ------------------------------ | -------------------------------------------------------- |
| Device Fingerprinting          | Descope Fingerprinting                                   |
| Protected Auth on SDK calls    | Fingerprint / risk step in the Flow + conditional branch |
| Fingerprint verdict            | `riskInfo` signals / Flow conditional logic              |
| Bot detection                  | `riskInfo.botDetected`, risk score, Bot Trap, CAPTCHA    |
| Credential stuffing protection | Flow risk branch + MFA/CAPTCHA/block behavior            |
| Account takeover risk          | Risk-based MFA / step-up / notification                  |
| Toll fraud prevention          | OTP/channel restrictions + risk checks + connector logic |
| New device notification        | Trusted/unrecognized device logic + messaging connector  |
| IP-geo restrictions            | Flow condition / connector / app-side policy             |
| Custom decisioning             | Flow conditions, connectors, or backend policy checks    |

Ask whether Stytch Fraud & Risk or Protected Auth is only monitoring or actually making access
decisions. If it blocks or challenges users, treat the migration as a security-flow redesign, not a
configuration copy. **Effort: Medium–High** — especially if verdicts affect production login outcomes.

### Connected Apps → Descope Inbound Apps

Stytch Connected Apps enables a Stytch-powered application to act as an OAuth/OIDC Authorization
Server for first-party apps, third-party integrations, desktop apps, CLI tools, AI agents, MCP
clients, and other clients that need scoped access to user data. Descope maps this most closely to
**Inbound Apps**, where Descope acts as the OAuth/OIDC authorization server and issues scoped tokens
to external clients.

| Stytch Connected Apps           | Descope Inbound Apps                                      |
| ------------------------------- | --------------------------------------------------------- |
| OAuth/OIDC Authorization Server | Descope Inbound Apps authorization server                 |
| First-party client              | First-party Inbound App / known client                    |
| Third-party client              | Third-party Inbound App                                   |
| Public client + PKCE            | Public Inbound App / PKCE-capable flow                    |
| Confidential client             | Confidential Inbound App with client secret               |
| Authorization Code flow         | Inbound App Authorization Code flow                       |
| Refresh tokens                  | Inbound App refresh token support                         |
| ID tokens                       | OIDC ID tokens                                            |
| Access tokens                   | Descope-issued scoped access tokens                       |
| Consent screen                  | Inbound App consent / consent management                  |
| Custom scopes                   | Resources and scopes                                      |
| RBAC-backed scopes              | Role/scope/resource mapping review                        |
| Token revocation                | Inbound App token revocation                              |
| Dynamic Client Registration     | DCR / Agentic Identity Hub client registration, if needed |

This is a high-complexity migration if real external clients depend on the current Stytch issuer,
JWKS, token claims, scopes, refresh token lifetimes, consent records, or callback URLs. Inventory every
client, redirect URI, grant type, scope, token audience, and resource server before writing code.
**Effort: High** when third-party clients or AI agents are already in production.

### AI Agent / MCP Authentication → Descope Agentic Identity Hub / MCP Servers / Inbound Apps

Stytch can use Connected Apps for AI agents, MCP clients, CLI tools, and agentic integrations that
need delegated OAuth/OIDC access. Descope has Agentic Identity Hub, MCP server configuration, Inbound
Apps, resources/scopes, client registration, and token issuance patterns for these use cases.

Do not treat AI/MCP auth as a generic OAuth migration without review. Agentic flows often require
clear resource scopes, dynamic client registration, token lifetimes, consent design, and
organization-level controls.

| Stytch AI / MCP pattern          | Descope                                      |
| -------------------------------- | -------------------------------------------- |
| Connected App for AI agent       | Inbound App / Agentic Identity Hub client    |
| MCP client authorization         | MCP Server authorization / Inbound App       |
| Dynamic Client Registration      | DCR / CIMD / known client registration       |
| Agent scopes                     | Resource scopes / policies                   |
| Agent consent                    | Inbound App consent                          |
| CLI or desktop app client        | Public client + PKCE                         |
| Organization-level agent control | Tenant-aware policy / scope / consent design |

Ask whether Stytch is acting as the OAuth provider for agents, whether the app exposes MCP tools, and
whether external agents already store refresh tokens. **Effort: Medium–High — flag for dedicated
review.**

### Machine-to-Machine Authentication → Descope Access Keys / Client Credentials

Stytch M2M authentication uses M2M clients, client credentials, access tokens, scopes, custom claims,
and secret rotation for service-to-service authentication. In Descope, map this to Access Keys or
client credentials patterns depending on whether the service needs Descope-issued JWTs for your own
APIs or OAuth-style scoped access through an Inbound App.

| Stytch M2M                | Descope                                                  |
| ------------------------- | -------------------------------------------------------- |
| M2M client                | Access Key or Inbound App confidential client            |
| Client ID / client secret | Access Key or OAuth client credentials                   |
| Client credentials flow   | Descope client credentials flow / Inbound App flow       |
| JWT access token          | Descope-issued JWT                                       |
| M2M scopes                | Access key claims, roles/permissions, or resource scopes |
| Custom claims             | Access key custom claims / JWT Templates                 |
| Secret rotation           | Access key rotation / client secret rotation             |

Ask which services use M2M credentials, which APIs they call, what scopes they require, and whether
tokens are validated by internal services or external resource servers. **Effort: Medium** — often
straightforward, but production services require careful secret rotation and rollout.


### Third-party Provider Tokens / Connected External Accounts → Descope Outbound Apps

Stytch OAuth/social login is primarily for authentication, but some applications also depend on
provider access tokens to call third-party APIs such as Google, Microsoft, GitHub, Slack, HubSpot, or
other services. If the Stytch implementation stores or uses third-party provider tokens beyond login,
evaluate Descope **Outbound Apps**.

Do not confuse this with Connected Apps:

* **Connected Apps / Inbound Apps**: external clients call your application using tokens your app
  issues.
* **Outbound Apps**: your application stores/uses tokens for external providers on behalf of users or
  tenants.

| Stytch / App behavior                       | Descope                                            |
| ------------------------------------------- | -------------------------------------------------- |
| User connects Google/Microsoft/etc. account | Outbound App user connection                       |
| Tenant connects external provider account   | Outbound App tenant connection                     |
| App stores provider access/refresh tokens   | Descope token vault for Outbound Apps              |
| Backend calls third-party API               | Fetch Outbound App token server-side               |
| AI agent uses external provider token       | Outbound App token made available to backend/agent |

Ask which providers are connected, where tokens are used, whether users must reconnect accounts, and
whether tokens can legally/technically be migrated. **Effort: Medium** if providers are few; high if
external integrations are core product functionality.


### Webhooks / Events / Event Logs → Descope Webhooks / Connectors / Audit Events

Stytch webhooks and event logs may be used to synchronize users, organizations, members, sessions,
SCIM lifecycle events, fraud decisions, or Connected Apps consent/token events into the application.
Descope can use audit events, webhook connectors, generic HTTP connectors, and audit/troubleshooting
connectors depending on the use case.

| Stytch                             | Descope                                               |
| ---------------------------------- | ----------------------------------------------------- |
| Webhook endpoint + signing secret  | Descope webhook/HTTP connector + signature validation |
| User events                        | Descope user/audit events                             |
| Organization/Member events         | Tenant/user events or app-side lifecycle sync         |
| SCIM lifecycle events              | Descope SCIM provisioning events / audit events       |
| Fraud/Risk events                  | Flow branch + audit/webhook/logging connector         |
| Connected App consent/token events | Inbound App consent/token event review                |
| Event log streaming                | Audit & Troubleshooting connectors                    |
| Compliance logs                    | Audit Webhook Connector / log destination connector   |

Search the codebase for Stytch webhook handlers and event-name switches. Update event names,
signature validation, payload parsing, retry behavior, and downstream side effects. Identify which
events are business-critical before cutover. **Effort: Medium.**

### Features Usually Outside the Core Identity Migration

Some Stytch-adjacent behavior may not map cleanly to Descope or may actually belong to the
application layer.

* **Application-specific authorization data** — keep in the application database unless intentionally
  migrating to Descope ReBAC/FGA.
* **Billing/customer lifecycle logic attached to Organizations** — map identity objects carefully, but
  billing logic may remain outside Descope.
* **Product analytics built from Stytch events** — rebuild using Descope events, app analytics, or data
  warehouse pipelines.
* **Custom fraud models outside Stytch** — integrate via Flow connectors or keep in backend risk
  service.
* **General feature flags** — usually out of scope unless they are actually access-control decisions.
* **Custom token broker logic** — review separately; may map to Inbound Apps, External Token
  Management, Access Keys, or app-side federation.

Do not present these as direct SDK swaps. Flag them separately and ask whether they are part of the
identity migration or a separate application/platform migration.

### High-Complexity Stytch Areas to Flag Before Step 0.5

After mapping confirmed Stytch features, summarize findings and flag high-complexity items before
proceeding to Step 0.5. The main high-complexity Stytch areas are:

* **SCIM / Directory Sync** — lifecycle, group sync, deprovisioning, role mapping, IdP cutover.
* **Enterprise SSO with JIT provisioning** — routing, tenant mapping, domain behavior, SSO claim
  mapping.
* **RBAC tied to SSO or SCIM** — group-to-role mapping and token/permission enforcement.
* **Authorization beyond RBAC** — possible ReBAC/FGA or app-side authorization model review.
* **Fraud & Risk / Device Fingerprinting** — especially if verdicts block or challenge users.
* **Protected Auth** — must be redesigned as Flow-based risk handling.
* **Connected Apps** — OAuth/OIDC issuer, clients, scopes, consent, tokens, refresh tokens, resource
  servers.
* **AI Agent / MCP Authentication** — scopes, DCR/CIMD, MCP server authorization, token lifetimes,
  tenant controls.
* **Machine-to-Machine Authentication** — client credentials, access keys, secrets, rotation, scopes.
* **Trusted Auth Tokens** — external issuers, JWKS, JWT bearer exchange, claim mapping, provisioning.
* **Provider token storage / external account connections** — possible Outbound Apps migration.
* **Webhooks/Event Streaming** — event names, payloads, signing, retries, downstream sync.
* **Custom domains and OAuth/OIDC issuer URLs** — DNS, cookies, callbacks, token validation impact.




## Step 4: Critical Gotchas (Always Cover These)

### JWT Claims Are Not the Same

Descope session JWTs contain `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions`, and `dct` by
default. They do **not** contain `email`, `name`, or `picture`. Stytch returns profile fields on the
`member`/`user` object (and may carry them as custom claims in the `session_jwt`), so code that reads
those fields off the token or session response will break after migration.

`dct` and `tenants` only matter when you read a user's tenant context **from their session at
request time** — not for tenant administration, which is done by tenant ID through
`management.tenant.*` / `management.user.*`. When you do read the session, `dct` (Descope Current
Tenant) is a flat string holding the active tenant ID — the direct equivalent of Stytch's
`organization_id` — and `tenants` is a keyed object (`{ [tenantId]: { roles, permissions } }`) for
per-tenant roles/permissions. Prefer the SDK's role/permission helpers (e.g.
`validateTenantRoles(authInfo, tenantId, [...])`) over reading these claims by hand; reach for `dct`
when you only need the active tenant ID.

**Action required:** Configure a JWT Template in the Descope Console to add `email`,
`name`, and any other profile fields the app reads from the token.

### Stytch Session Tokens Become a Single Descope Signed JWT

Stytch issues two session representations — an opaque `session_token` (validated by a network call
to Stytch) and a `session_jwt` (a short-lived JWT validated locally), typically stored in the
`stytch_session` and `stytch_session_jwt` cookies. Descope collapses this into one signed session
JWT in the `DS` cookie (refresh in `DSR`). Code that stores, reads, or validates either Stytch
session cookie must be replaced with Descope session validation (`validateSession()`), which returns
decoded JWT claims. There is no opaque-token-vs-JWT distinction to maintain in Descope.

### Logout Is Two Steps

1. Call `descopeClient.logout(refreshToken)` to invalidate server-side
2. Clear `DS` and `DSR` cookies

Skipping either step leaves a broken state.

### Audience Validation Is Opt-In

Descope session tokens have no `aud` claim by default. Apps that rely on audience-scoped API access
must (1) configure a custom `aud` claim in JWT Templates and (2) pass `audience` to
`validateSession()` on the backend.

### Organization Handling: Tenant IDs, Not Token Parsing

Most code that references a Stytch `organization_id` (and an SSO `connection_id`) is
management/admin code — it becomes a Descope **tenant ID** passed to `management.tenant.*` /
`management.user.*` calls. Only request-time code that read the organization off the Stytch session
changes shape: Descope exposes the active tenant as `dct` and membership as the nested `tenants`
object, read off the validated session (ideally via SDK helpers). Grep for all `organization_id`
reads and sort them into these two buckets — by-ID management calls vs. session reads — before
updating.

### One Token: The Descope Session JWT

Stytch apps may juggle an opaque `session_token` and a `session_jwt`. With Descope there is one
token: forward the Descope session JWT (`DS` cookie) as `Authorization: Bearer <DS>` to API servers;
downstream services validate it with `validateSession()`.

### No Drop-In Middleware

Descope ships no drop-in auth-middleware package. Whatever validates Stytch sessions today — e.g. a
Next.js `middleware.ts` calling `sessions.authenticateJwt()`, or Stytch's session helpers — becomes
~20 lines of custom code that reads the `DS` cookie and calls `validateSession()`.

### `cookies()` and `headers()` Are Async in Next.js 15

`cookies()` and `headers()` from `next/headers` return a `Promise` in Next.js 15+. Before
generating any server-side helper that reads cookies:

1. Check the project's `package.json` for the Next.js version.
2. If ≥ 15: write `await cookies()` and mark the containing function `async`.
3. Trace upward — making a cookie-reading helper async cascades to every caller.

### Async Cascade: Trace All Callers Before Finishing

When a shared utility becomes async, TypeScript accepts `await` on non-Promises without
error — so callers that forget `await` silently return a Promise object. Always grep for
all call sites of any utility you make async and update them in the same pass.

### SCIM Is a Lifecycle, Not a One-Time Import

If Directory Sync is in use, re-point the SCIM pipeline at Descope before cutover. A one-time user
import leaves provisioning broken the moment the directory pushes its next change.

### Approved Domains Are Domain-Only (Not Stytch Callback URLs)

Stytch apps register full callback URLs (e.g. `http://localhost:3000/authenticate`). Descope uses
**Approved Domains** (Console → Project Settings → Security) — domain only, no protocol, no path.
For local dev: `localhost:3000`, **not** `http://localhost:3000/authenticate`. Descope embedded
Flows complete auth client-side; there is no `/authenticate` route to whitelist.

### Env Var Reduction

Stytch: `STYTCH_PROJECT_ID`, `STYTCH_SECRET`, and a public token (`STYTCH_PUBLIC_TOKEN` /
`NEXT_PUBLIC_STYTCH_PUBLIC_TOKEN`) (3+). Descope: `DESCOPE_PROJECT_ID` for server-side use, plus
`NEXT_PUBLIC_DESCOPE_PROJECT_ID` when the frontend SDK or embedded Flow runs in the browser (same
value as `DESCOPE_PROJECT_ID` — the `NEXT_PUBLIC_` prefix exposes it to client components in
Next.js and similar frameworks), and `DESCOPE_MANAGEMENT_KEY` only when using management APIs.

---

## Step 5: Automated Testing

Run the app and verify it works — don't just hand over a checklist.

### Phase 0: Final stale-import sweep (BLOCKING)

```bash
grep -rni "@stytch\|stytch\|com\.stytch" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --include="*.rb" --include="*.java" --include="*.kt" --include="*.swift" \
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
mvn compile -q      # Java/Maven
./gradlew compileJava compileKotlin  # Java/Gradle
dotnet build        # .NET
```

**Do not proceed until compilation exits with zero errors.**

**If compilation fails, diagnose by error message:**

- `Cannot find module '@stytch/...'` (or `stytch`) → stale import; re-run Phase 0
- `Property 'X' does not exist on type '...'` → wrapper built against the Stytch session/member response shape; re-derive from the Descope `authInfo` shape
- `'await' expression is not allowed in synchronous contexts` → async cascade gap
- `Object is possibly 'undefined'` on session fields → add null check or early return

```bash
npm run dev   # or: python main.py / go run . / flask run / etc.
```

### Phase 2: Run existing tests

```bash
npm test   # or: pytest / go test ./... / etc.
```

Auth-related test failures usually mean: a mock or fixture still uses Stytch shapes, or a
test validates JWT claims that are now missing (e.g., `email` without a JWT Template), or a test
still uses `organization_id` where the code now passes a Descope tenant ID (management calls) or
reads `dct`/`tenants` off the validated session.

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

### Phase 4: Verify JWT claims (if JWT Template is configured)

```bash
echo "<DS_cookie_value>" | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

Check that `email`, `name`, and any other expected claims (including `dct`/`tenants` for B2B) are present.

### Phase 5: Report results

```
## Test Results

**Server startup:** ✅ Started successfully on port 3000
**Existing tests:** ✅ 12 passed / ❌ 2 failed (list failures)
**Unauthenticated /dashboard:** ✅ 302 → /login
**Unauthenticated /api/protected:** ✅ 401
**Login page loads Descope component:** ✅
**JWT claims (email, name, dct):** ✅ Present / ❌ Missing — JWT Template not yet configured

**Blockers before going live:**
- [ ] (list anything that failed or needs manual action)
```

**Do not proceed to Step 6 until ALL of the following are true:**

- Phase 0 grep returns zero Stytch references
- Phase 1 compilation passes with zero errors
- Phase 1 server starts and stays running
- Phase 3 root path returns 2xx or 3xx (not 5xx)
- Phase 3 protected routes return 302 or 401 (not 500)

---

## Step 6: Post-Migration Summary (Required)

Every migration produces a `MIGRATION-SUMMARY.md` covering what was done, manual setup
remaining, and behavioral differences that matter before production.

### MIGRATION-SUMMARY.md

1. **What was migrated** — a table mapping each Stytch concept to its Descope replacement
2. **Behavioral differences and open questions** — numbered list of significant differences
  between the Stytch and Descope implementations. For each item: Stytch behavior, Descope
   behavior, action required.
3. **Pre-deploy checklist** — actionable checkbox items for everything that must happen
  before the migrated app can run. Prominently include all Console setup tasks (project, Flow,
   JWT template, tenants, SSO/SCIM) and the SCIM re-point — these are the things easiest to
   forget because the code compiles without them.

---

## Step 7: Output Format

Write a numbered migration guide in Markdown, scoped to the user's stack. Use code
snippets and direct doc links. Always include the MIGRATION-SUMMARY.md deliverable (Step 6).

For complex migrations, flag the high-effort items
explicitly with estimated complexity (Low/Medium/High) so the user can plan.

---

## Reference Files

- `references/implementation-nuances.md` — Verified migration patterns, code-level diffs, and edge
cases for several frameworks.
- Descope Docs: [https://docs.descope.com](https://docs.descope.com)
- Migration Guide: [https://docs.descope.com/migrate](https://docs.descope.com/migrate)  
- User Import (Custom): [https://docs.descope.com/migrate/custom](https://docs.descope.com/migrate/custom)
- Descope OIDC Endpoints: [https://docs.descope.com/getting-started/oidc-endpoints](https://docs.descope.com/getting-started/oidc-endpoints)
- Descope Flows: [https://docs.descope.com/flows](https://docs.descope.com/flows)
- JWT Templates: [https://docs.descope.com/management/jwt-templates](https://docs.descope.com/management/jwt-templates)
- Access Keys (M2M): [https://docs.descope.com/management/m2m-access-keys](https://docs.descope.com/management/m2m-access-keys)
- Messaging Templates: [https://docs.descope.com/management/messaging-templates](https://docs.descope.com/management/messaging-templates)
- Audit Webhook: [https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook)
- Custom Domains: [https://docs.descope.com/how-to-deploy-to-production/custom-domain](https://docs.descope.com/how-to-deploy-to-production/custom-domain)
- ReBAC: [https://docs.descope.com/authorization/rebac](https://docs.descope.com/authorization/rebac)
- Outbound Apps: [https://docs.descope.com/identity-federation/outbound-apps](https://docs.descope.com/identity-federation/outbound-apps)

### Session Validation by Language

- Node.js: [https://docs.descope.com/getting-started/nodejs#implement-session-validation](https://docs.descope.com/getting-started/nodejs#implement-session-validation)
- Python: [https://docs.descope.com/getting-started/python#implement-session-validation](https://docs.descope.com/getting-started/python#implement-session-validation)
- Go: [https://docs.descope.com/getting-started/golang#implement-session-validation](https://docs.descope.com/getting-started/golang#implement-session-validation)
- Ruby: [https://docs.descope.com/getting-started/ruby#implement-session-validation](https://docs.descope.com/getting-started/ruby#implement-session-validation)
- Java / Kotlin: [https://docs.descope.com/getting-started/java#implement-session-validation](https://docs.descope.com/getting-started/java#implement-session-validation)
- .NET / C#: [https://docs.descope.com/getting-started/dotnet#implement-session-validation](https://docs.descope.com/getting-started/dotnet#implement-session-validation)
- Next.js: [https://docs.descope.com/getting-started/nextjs#implement-session-validation](https://docs.descope.com/getting-started/nextjs#implement-session-validation)
- React: [https://docs.descope.com/getting-started/react#implement-session-validation](https://docs.descope.com/getting-started/react#implement-session-validation)
- Angular: [https://docs.descope.com/getting-started/angular#implement-session-validation](https://docs.descope.com/getting-started/angular#implement-session-validation)
- Vue: [https://docs.descope.com/getting-started/vue#implement-session-validation](https://docs.descope.com/getting-started/vue#implement-session-validation)
- Swift / iOS: [https://docs.descope.com/getting-started/swift#implement-session-validation](https://docs.descope.com/getting-started/swift#implement-session-validation)
- Kotlin / Android: [https://docs.descope.com/getting-started/android#implement-session-validation](https://docs.descope.com/getting-started/android#implement-session-validation)
- Flutter: [https://docs.descope.com/getting-started/flutter#implement-session-validation](https://docs.descope.com/getting-started/flutter#implement-session-validation)

### SDKs (GitHub)

- Node SDK: [https://github.com/descope/node-sdk](https://github.com/descope/node-sdk)
- Python SDK: [https://github.com/descope/python-sdk](https://github.com/descope/python-sdk)
- Go SDK: [https://github.com/descope/go-sdk](https://github.com/descope/go-sdk)
- Ruby SDK: [https://github.com/descope/descope-ruby-sdk](https://github.com/descope/descope-ruby-sdk)
- Java SDK: [https://github.com/descope/descope-java](https://github.com/descope/descope-java)
- .NET SDK: [https://github.com/descope/descope-dotnet](https://github.com/descope/descope-dotnet)
- Swift SDK: [https://github.com/descope/swift-sdk](https://github.com/descope/swift-sdk)
- Kotlin SDK: [https://github.com/descope/descope-kotlin](https://github.com/descope/descope-kotlin)
- Flutter SDK: [https://github.com/descope/descope-flutter](https://github.com/descope/descope-flutter)
- JS/TS monorepo (React, Angular, Vue, Next.js, Web Component, Web JS): [https://github.com/descope/descope-js](https://github.com/descope/descope-js)

