---
name: frontegg-to-descope
description: >
  Use this skill whenever anyone asks about migrating from Frontegg to Descope — whether they're
  a developer doing it themselves or a technical lead evaluating the move. Triggers on: "how do I
  migrate from Frontegg", "replace Frontegg with Descope", "we're moving off Frontegg", "Frontegg to
  Descope", "switch from Frontegg", "our app uses frontegg / @frontegg/react / @frontegg/nextjs /
  FronteggProvider / the Frontegg admin portal / Frontegg entitlements and we want to use Descope
  instead", or any question about Frontegg features (hosted or embedded login box, Accounts/Tenants,
  Environments, Applications, self-service portal, RBAC, ReBAC, Entitlements, feature flags, security
  rules, step-up, MFA, SCIM, enterprise SSO, prehooks, webhooks, Flows, M2M tokens, user pools,
  Frontegg AI agents) in the context of Descope. Works for any language or framework with a Descope
  SDK. Always use this skill before producing migration guidance — do not rely on memory alone.
---

# Frontegg → Descope Migration Skill

This skill guides self-service migrations from Frontegg to Descope. It runs in three parts:

1. **MCP Check** — confirm whether the Descope Docs MCP Server is available and suggest installing it if not
2. **Migration Plan** — gather context via triage questions, analyze the codebase's auth touchpoints, and produce a human-readable `MIGRATION-PLAN.md` for the user to review
3. **Execution** — if the user confirms they want to proceed, execute the plan

Do not collapse these parts or skip ahead. The plan must be reviewed before code changes begin. If the file view is truncated, partial, or cut off, continue reading with the appropriate offset until all lines have been loaded; do not proceed based on a partial read.

Frontegg is not only an authentication provider — it is a B2B SaaS identity platform spanning hosted and embedded login, multi-tenant Accounts, isolated Environments, multiple Applications per environment, a broad end-customer self-service portal, RBAC with role levels, ReBAC, an entitlements engine (features, plans, feature flags), security rules, step-up authentication, MFA, SCIM, enterprise SSO, prehooks, webhooks, no-code Flows, machine-to-machine tokens, user pools that federate an existing user store, and AI-agent identity with managed third-party OAuth. A good migration first identifies which Frontegg product surfaces are actually in use, then maps each one to the closest Descope feature or migration pattern. Expect Frontegg migrations to vary widely: two Frontegg apps can share the same SDK and have almost nothing else in common.

**Primary references** (both in this skill's directory):

- `references/implementation-nuances.md` — verified migration patterns for each framework, Frontegg feature-to-Descope mappings, user export patterns, and known gotchas
- `references/flows-and-widgets.md` — Descope terminology/lingo, Flow structure and templates, Widgets, SSO Setup Suite, Console-vs-code decision guide

---

## Guiding Principles

**Console-first.** Before recommending SDK code for any user-facing auth feature, check whether the Console, a Flow, a Widget, or the SSO Setup Suite covers the use case. Engineers integrate once (SDK setup + session validation). All subsequent auth evolution — new methods, MFA changes, UI updates, tenant SSO onboarding — should happen in the Console without code deployments. See `references/flows-and-widgets.md` → Console vs. Code.

This matters more in a Frontegg migration than in most others. Frontegg's **self-service portal** is unusually broad — users, groups, roles, security policy, SSO, SCIM, audit logs, webhooks, and API tokens are all end-customer-facing screens the customer never wrote. If those workflows get rebuilt as custom code, the migration balloons. Map them to Descope Widgets and the SSO Setup Suite first, and only write code for what genuinely isn't covered.

**Verify before you write.** Frontegg ships fourteen SDKs across web, backend, and mobile, and several of them (Java, .NET) either don't exist or cover only entitlements — meaning those apps hand-rolled JWT verification. Confirm what the app actually uses before mapping anything.

**Don't assume the whole platform is in scope.** Entitlements, feature flags, and the AI-agent tooling are adjacent products that happen to live in the same dashboard. Establish scope in triage rather than discovering it mid-migration.

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

**Scan before you ask.** If there's a codebase available, run Step 1's searches (or at minimum the
broad sweep, search 1) *before* Step 0's `AskUserQuestion` calls — silently, as a normal tool call,
not as something that needs permission. Scanning is free, non-destructive, and turns generic
multiple-choice questions into specific, pre-filled ones: naming the actual framework and SDK version
found rather than offering a menu of every framework Frontegg supports, presenting the detected login
mode as a confirmation rather than an open question, and skipping questions in the feature-usage call
entirely for categories the scan found zero evidence of. Triage then does two things: **confirms**
what the scan found (cheap to get wrong if assumed silently, cheap to confirm explicitly) and **asks
only what code cannot reveal** — production user/account counts, migration goal, password strategy,
whether prehooks live in another service, which portal modules are actually enabled versus merely
available. This still requires `AskUserQuestion` for both calls below; it changes what the questions
contain and how many are asked, not whether the step happens.

**Scale the question count to the project.** A small app with a handful of components and one env
file does not need the same triage volume as a multi-tenant platform with prehooks and SSO. If the
scan shows no evidence of a feature category (ReBAC, SCIM, M2M, entitlements, user pools, AI agents,
etc.), it's reasonable to state "no evidence found for X — confirm out of scope?" as a single grouped
question rather than working through the full second-call catalogue item by item.

### Step 0: Triage (BLOCKING — requires `AskUserQuestion`)

**Use the `AskUserQuestion` tool to gather the information below, informed by whatever the codebase
scan already found. Do not infer answers from memory, prior conversations, or assumptions the scan
didn't actually confirm — even if you think you know.**
The migration path differs based on these answers; getting them wrong wastes the user's
time and produces incorrect guidance.

Do not proceed to Step 0.5 until the user has answered.

**First `AskUserQuestion` call (up to 4 questions):**

1. **Backend language / framework** — Present the most likely options based on any cues in the
   conversation (e.g., Node.js, Python, Go, Java, .NET). The user can always pick "Other." Note
   that Frontegg has **no official .NET SDK** and its Java package covers **entitlements only**,
   so those backends already hand-roll JWT verification — usually the easiest migrations.
2. **Hosted or embedded login?** — Frontegg's biggest branch point. **Hosted** means users are
   redirected to `https://[frontegg-domain]/oauth/account/login` and the app calls
   `loginWithRedirect()`. **Embedded** means the Frontegg SDK injects `/account/login`,
   `/account/sign-up`, and `/account/logout` routes into the app itself. Embedded apps map cleanly to
   an embedded Descope Flow component. Hosted apps are a real decision, not a mechanical swap — Auth
   Hosting is built for Descope acting as an IdP to a Federated/Inbound/Agentic App, not as a generic
   redirect page for an arbitrary first-party origin, so a hosted app may end up embedded, on Auth
   Hosting behind a custom domain, or modeled as an OIDC client — see Step 1.5 item 3 for the decision
   framework. Mobile apps are always hosted, and there embedded isn't an option at all. If they don't
   know, the signal is
   `hostedLoginBox` / `FRONTEGG_HOSTED_LOGIN` (for the Next.js **Pages Router**, the SDK deprecates
   the prop in favor of the env var; the **App Router** quickstart still requires the `hostedLoginBox`
   prop alongside the env var, so check which router is in use before assuming the prop is dead), or
   the Console's Login method setting. Do **not** infer the mode from `keepSessionAlive`,
   `useAuthUser()`, or the mobile `embeddedMode` / `EmbeddedAuthActivity` settings — none of those
   distinguish the two.
3. **Migration goal** — Full cut-over, incremental/phased migration, or just evaluating.
4. **Existing users and accounts** — Are they migrating an app with active users and accounts
   in Frontegg, staging/dev only, or starting fresh? This determines whether user and account
   migration planning is needed (user export, account→tenant mapping, SCIM continuity, phased
   vs. big-bang cutover, forced re-login on cutover). **Flag immediately if they have production
   users:** Frontegg documents no outbound password-hash export — see Step 0.5.

**Second `AskUserQuestion` call — Frontegg feature usage (use `multiSelect: true`):**

1. **Which Frontegg features are in use?** Present the highest-impact categories:

* **Login box and authentication methods** — which sign-in methods are enabled: password, magic link, magic code, SMS OTP, passkeys/WebAuthn, device flow, social logins (Google, Microsoft, GitHub, Facebook, Apple, LinkedIn, Slack, or a custom OAuth provider), enterprise SSO; which login identifiers are allowed (email, username, phone number); whether the login box is hosted or embedded; whether it is customized via `customLoginBox`, localizations, or theme options.
* **Accounts / tenants** — how Frontegg Accounts (tenants) are modeled; whether users belong to multiple accounts; whether `switchTenant` / tenant switching is used; whether **sub-accounts** (account hierarchies) are enabled. Descope has native **sub-tenants**, so this maps — but confirm how deep the nesting goes and whether role inheritance is expected.
* **Environments** — how many Frontegg environments exist (Development, Staging, QA, Production; up to four). Each has its own Client ID, API Key, and Frontegg domain, and each becomes a separate Descope Project.
* **Applications (multi-app)** — whether more than one Frontegg Application exists under an environment, whether `appId` is passed in `contextOptions` / `FRONTEGG_APP_ID` / `applicationId`, whether per-application MFA or auto-assign rules are configured, and whether the `applicationId` JWT claim is read anywhere.
* **Self-service portal** — which modules are enabled and actually used: profile settings, privacy & security, personal tokens, account details, users/invites, guest (temporary) users, groups, custom roles, security policy (MFA, lockout, password history, sessions, IP and domain restrictions), SSO setup, SCIM provisioning, audit logs, webhooks, account API tokens. Whether it is embedded (`AdminPortal.show()`) or hosted (`AdminPortal.openHosted()` / `/oauth/portal`).
* **RBAC** — how roles and permissions are defined; whether **role levels** (the numeric hierarchy that limits which roles a user may assign) are relied on; whether permission **classification types** (`Never` / `Assignable` / `Always`) gate what end customers can build into custom roles; whether end customers create their own custom roles; whether **groups** and group roles are used; whether built-in `fe.*` permissions are referenced in application code.
* **ReBAC** — whether relationship-based authorization is enabled (entity types, relations, actions, assignments) and whether the app runs the self-hosted entitlements engine (`@frontegg/e10s-client` against SpiceDB). Flag as high complexity.
* **Entitlements — features, plans, feature flags** — whether `isEntitledTo`, `useFeatureEntitlements`, or `usePermissionEntitlements` gate application behavior; whether plans map to billing tiers; whether feature flags are used for release management. Ask whether entitlements are part of the identity migration or a separate effort — see Step 3.
* **Enterprise SSO** — whether SAML, OIDC, or both are used; which identity providers are connected; whether tenant admins configure SSO themselves through the self-service portal; whether SSO drives JIT provisioning or role assignment; whether Frontegg acts as an IdP (`native-hosted`, `via-oidc`, `via-saml`).
* **SCIM provisioning** — which workforce directories are connected; whether user and group provisioning, deprovisioning, group-to-role mapping, or downstream webhook handlers depend on SCIM behavior. Flag as high complexity.
* **Security rules and MFA** — which of Frontegg's nine built-in defenses are enabled (bot detection, new device, brute force, breached password, impossible travel, suspicious IPs, stale users, email credibility, country restrictions) and what verdict each is set to (allow / challenge / block / lock); whether MFA is enforced per environment, per account, or per application; whether remember-device is used.
* **Step-up authentication** — whether the app requests step-up via `acr` / `amr` / `max_age`, and for which sensitive actions.
* **Domain, IP, and country restrictions** — which of the five enforcement levels are configured (environment domain, environment country, account domain/IP/country, user-level).
* **Sessions and tokens** — JWT expiration settings, `keepSessionAlive` / silent refresh, refresh-token rotation, `enableSessionPerTenant`, custom token templates and targeting rules, which claims the application reads, and how backends verify tokens (Frontegg SDK, JWKS, or a hardcoded public key).
* **Prehooks** — which of the thirteen prehook events are implemented (`AUTH_INITIATED`, `USER_SIGNUP`, `USER_INVITE`, `USER_UPDATE`, `USER_DELETE`, `CREATE_TENANT`, `UPDATE_TENANT`, `DELETE_TENANT`, `JWT_GENERATION`, `SOCIAL_LOGIN_AUTH`, `OIDC_AUTH`, `SAML_AUTH`, `SEND_SMS`, `SIGN_UP_USER_POOL`), whether they are API prehooks or custom-code prehooks, and whether any of them block, challenge, or lock. Flag as high complexity — prehooks are synchronous decision points in the auth path.
* **Webhooks and events** — which `frontegg.*` events the application consumes and whether any of them keep an application database in sync.
* **Flows (Frontegg's no-code orchestration)** — whether visual flows compose prehooks, webhooks, and sub-flows, and what decisions they make.
* **M2M authentication** — whether user tokens or tenant (account) tokens are used; whether they are client-credentials tokens (sent in `Authorization`) or access tokens (sent in `X-API-KEY`); which scopes, roles, and audiences are enforced.
* **User pools** — whether Frontegg federates an existing external user store (Auth0, Cognito, Firebase, or custom-code Get User / Login hooks) rather than owning the user data. Flag as high complexity: it changes where the source of truth lives.
* **Frontegg AI agents** — whether AI agents are defined with the Frontegg AI SDK, whether the built-in tools (get user context, get user tenants, get user entitlements) are used, and whether managed third-party OAuth integrations (Atlassian, GitHub, Google Workspace, HubSpot, Monday, Notion, Slack) broker access to external APIs on a user's behalf.
* **MCP** — whether the Entitlements Agent is deployed with its **MCP Server** (exposing `is-entitled-to-entity-action-tool` and `entitlements-entities-tool` over HTTP), or whether Frontegg's separate **AgentLink** product (self-hosted component: **FrontMCP**) is in use as a hosted or self-hosted MCP gateway. These map to Descope's MCP server support (an MCP server is modeled as a **Resource**, with what the docs call **Agentic Clients** — Console: **Agentic Identity Hub → Clients** — registering agent/MCP access), not to Outbound Apps.
* **AgentLink / Agen for Work** — Frontegg now ships two agentic product lines alongside CIAM: **AgentLink** (SaaS-facing MCP/agent access) and **Agen for Work** (governing employee access to internal AI agents). If either is in use, confirm scope explicitly rather than assuming the migration is CIAM-only.
* **API access control** — whether Frontegg's entitlements-based API access control (distinct from plain SDK JWT verification, and dependent on the Entitlements Agent) gates backend routes. Maps to Descope Resources, scopes, and Policies.
* The user can add others via **"Other."**

After both calls, summarize findings and flag high-complexity items before proceeding to Step 0.5. The main high-complexity Frontegg areas are typically **user/password export, the self-service portal surface, prehooks, ReBAC on the self-hosted engine, entitlements and feature flags, SCIM, enterprise SSO with JIT, sub-accounts, user pools, M2M, and AI-agent OAuth integrations**.

---

## Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

These questions surface blockers the framework doesn't expose. Ask even the ones you think
you know. Use `AskUserQuestion` before proceeding to codebase analysis.

**Read `references/flows-and-widgets.md` first.** The last group of questions below asks which
workflows a Descope Widget or the SSO Setup Suite can absorb — you cannot ask that usefully without
knowing the widget catalog and the self-service portal mapping table. This is the single largest
lever on scope in a Frontegg migration, and asking it vaguely wastes the checkpoint. The
*High-Complexity Frontegg Areas* checklist in Step 3 is also worth skimming now; it is the list you
are flagging against.

Batch into calls of up to 4 questions. Skip questions that are clearly inapplicable given
Step 0 answers (e.g., skip user migration planning if they said they're starting fresh).

**Access and credentials**

* Do they have access to the Descope Console and a Project ID? (If not, see Step 1.5.)
* Do they need a Management Key? Required for user CRUD, tenant management, RBAC, SSO/SCIM configuration, access keys, Inbound Apps, Outbound Apps, and other management operations.
* Do they have the Frontegg **Client ID and API Key** for each environment (Portal → Keys & domains)? These are needed to mint an environment token (`POST https://api.frontegg.com/auth/vendor`) for any export work. Without them, no user data can be extracted.
* Which **region** is their Frontegg environment in? The management gateway differs: `api.frontegg.com` (EU, the default), `api.us.frontegg.com`, `api.au.frontegg.com`, `api.ca.frontegg.com`. Export scripts pointed at the wrong host fail with a vendor-JWT verification error.

**Codebase scope**

* Is the login box **hosted or embedded**? Confirm against `hostedLoginBox` in `contextOptions` / `authOptions`, or `FRONTEGG_HOSTED_LOGIN` in Next.js. This determines whether the Descope target is Auth Hosting or an embedded Flow component, and which client hooks were in use (`useLoginWithRedirect` implies hosted; `useAuthUser` implies embedded).
* Are there places in the app that read claims directly off the Frontegg access token — `sub`, `tenantId`, `tenantIds`, `roles`, `permissions`, `type`, `applicationId`, `sid`, `metadata`, `profilePictureUrl`, `email_verified` — or custom claims injected by a `JWT_GENERATION` prehook? These need a Descope JWT Template or Flow custom claims configured before equivalent reads will work.
* Does the app read Frontegg `tenantId` in many places? The Account → Tenant remap ripples through SSO, SCIM, RBAC, the self-service portal replacement, M2M tokens, and membership checks. Confirm the account model before writing code.
* Are there multiple services or microservices validating Frontegg tokens? Each needs to be updated. Ask specifically whether any of them verify with a **hardcoded public key** (`FRONTEGG_JWT_PUBLIC_KEY`) rather than JWKS — those break silently at cutover rather than loudly.
* Does the app use Frontegg frontend SDK hooks, backend SDK middleware, direct REST calls to `api.frontegg.com`, mobile SDKs, or all of the above?
* Does the app depend on Frontegg **webhooks** to keep its own database in sync? Search for handlers before changing user, tenant, group, SCIM, or plan behavior.
* Does the app implement **prehooks**? These are HTTP endpoints or custom-code functions Frontegg calls synchronously during auth. They are easy to miss in a codebase scan because they may live in a separate service — ask directly.

**Deployment and risk**

* How many Frontegg **environments** exist? Each becomes its own Descope Project with its own Project ID, Approved Domains, SSO/SCIM configuration, and environment-specific secrets. Frontegg allows publishing a login box between environments; Descope Projects are configured independently.
* Is there a maintenance window, or does this need to be zero-downtime?
* Are any external customers, enterprise IdPs, SCIM directories, or machine-to-machine clients already integrated with the Frontegg production environment? If yes, plan customer-facing cutover steps, not just code changes.
* Is a **custom domain** in front of Frontegg today? If yes, note that it was likely added to avoid third-party-cookie failures on the refresh endpoint, and plan the equivalent Descope custom domain before cutover.
* Are login URLs, callback URLs, OAuth issuer URLs, or JWKS URLs contractually or technically expected to stay stable? Flag early — they affect SSO, sessions, and token validation.

**User and account migration** (if they indicated existing users/accounts in Step 0)

* How many users and accounts exist? `GET /resources/users/v3` caps at **200 users per page**, so this determines how long the export takes and whether it needs to be checkpointed.
* **Password credentials: confirm the strategy explicitly.** Frontegg documents a rich *inbound* migration API (bulk import with `bcrypt`, `scrypt`, `firebase-scrypt`, `pbkdf2`, `argon2`, and `sha256` hashes — verify against the live API reference whether `sha1` is also accepted, since it does not consistently appear in current docs) but **no bulk export endpoint and no password-hash export**. User profiles can be paged out of the list API; credentials cannot — no response schema in the identity API returns a credential field. Three paths handle this — pick one now, because it determines the cutover plan:
  1. **Full migration without passwords** — export users, import into Descope, then move everyone to passwordless (magic link, OTP, passkeys) or force a reset on first sign-in using a `freshlyMigrated` custom attribute in the Flow. This is the default recommendation.
  2. **JIT migration with a Generic HTTP Connector** — the only path that **keeps existing passwords working**. The Descope Flow collects email and password, a Generic HTTP Connector calls Frontegg's authenticate-local-user API to verify them, and on success the Flow creates the user in Descope and sets the password. Subsequent sign-ins are Descope-native.
  3. **JIT migration with Frontegg as a custom OIDC provider** — users sign in through Frontegg's hosted login (MFA included) and are provisioned into Descope from the returned ID token. Good when moving to passwordless anyway.

  Both JIT paths require **keeping Frontegg running until every active user has signed in at least once**. Ask whether that is acceptable before recommending one. See `references/implementation-nuances.md` → **Migrating user and account data**.
* Do users belong to multiple Accounts? If yes, preserve tenant membership and per-tenant role assignment when mapping to Descope Tenants.
* Is `vendorMetadata` in use? Frontegg recommends it for storing a pre-Frontegg internal user ID, and it is excluded from the JWT. Export it — it is often the join key back to the application's own database.
* Are **sub-accounts** in use? Descope supports **sub-tenants** natively — a tenant can have multiple sub-tenants, those can nest further, and each has exactly one parent. Confirm two things: what **role inheritance** mode the hierarchy needs (Full Inheritance, User only, or None), and whether any code reads the hierarchy from the token — the `tenants` JWT claim is flat and does not encode parentage, so hierarchy-aware request-time logic needs a `tenant.subtenant` JWT-template claim or a Load/Search Tenant call returning `parent` / `successors`. Note also that password settings and session management are always inherited from the parent in Descope.
* Which authentication methods are in use? Passkeys and TOTP enrollments do not transfer; users re-enroll. Confirm this is acceptable before committing to a cutover date.
* Big-bang cutover or phased? Map each Frontegg Account to a Descope Tenant first — user migration, membership, SSO, SCIM, JIT, and tenant-scoped roles all depend on it.
* **SCIM is a lifecycle system, not a one-time import.** If SCIM is enabled, enterprise directories will keep pushing create/update/deactivate/group events after cutover. Every SCIM workflow must be re-pointed at Descope before cutover, or provisioning silently breaks.
* Are they aware that active Frontegg sessions will be invalidated on cutover unless a session-bridging approach is used? Plan for forced re-login or a phased rollout.
* Does the app store Frontegg IDs in its own database? If yes, plan an ID mapping table for Frontegg user IDs, `tenantId`, role IDs, permission keys, group IDs, and application IDs.

**Gaps to flag immediately** (don't ask — flag these proactively based on Step 0 answers)

* If they have **production users with passwords**: flag the export gap as the single biggest schedule risk in the migration, before any code discussion. It determines the cutover strategy.
* If they use the **self-service portal**: flag that this should not automatically become custom code. Inventory which modules are enabled, then map to Descope Widgets and the SSO Setup Suite. Some modules (audit log export, end-customer webhook subscriptions, personal tokens) may have no direct widget equivalent and need an explicit decision.
* If they use **prehooks**: flag for dedicated review. Each prehook is a synchronous decision point with a 5-second budget and a fail-open/fail-close setting. In Descope these become Flow steps, Connectors, conditions, or JWT Template logic — not a single mechanism.
* If they use **ReBAC**: flag that Frontegg's implementation requires the customer to self-host SpiceDB plus CockroachDB plus a sync job, and that relation writes take up to 60 seconds to become enforceable. Descope's ReBAC is managed. Also confirm it is genuinely in use — ReBAC must be enabled by Frontegg support, so some environments have it configured but unused.
* If they use **entitlements, plans, or feature flags**: flag that Descope has no plan or feature-flag product. Ask whether these belong in the identity migration at all. See Step 3 → *Entitlements*.
* If they use **user pools**: flag as high complexity. The source of truth for user data may live outside Frontegg entirely, which changes what "migrating users" means. Note that Frontegg's JIT migration is irreversible — some users may already have been absorbed into Frontegg while others still live in the external store.
* If they use **SCIM**: set up Descope SCIM and customer IdP cutover before production migration. Missing this breaks provisioning even though interactive login appears to work.
* If they use **Frontegg AI agents with third-party OAuth integrations**: flag that this maps to the Agentic Identity Hub — specifically **Connections** for agent/MCP workloads, or Outbound Apps if the app isn't agentic — and that stored third-party refresh tokens do not transfer — users re-consent per integration.
* If they use **M2M tokens**: inventory every client, note whether each uses the `Authorization` header (client-credentials) or `X-API-KEY` (access tokens), and identify what scopes and audiences downstream services enforce.

**Console/Flow/Widget opportunities** (flag before codebase analysis, then ask):

* If the app embeds or hosts the **Frontegg self-service portal**: ask whether Descope Widgets and the SSO Setup Suite can replace those workflows instead of rebuilding them. Do not default to building custom admin screens.
* If the app has a profile edit page, user management page, account settings page, or tenant-admin UI: ask whether a Descope Widget covers the use case.
* If the app has a separate MFA enrollment page: ask whether MFA should be integrated into the main sign-in Flow as a step or subflow instead.
* If **prehooks** run custom checks, initiate SSO, or make decisions during the auth journey: ask whether that logic can become a Descope Flow step, condition, or Connector rather than a synchronous external service.
* If **Frontegg Flows** orchestrate the auth journey: ask whether the same journey can be expressed directly in a Descope Flow, which is the same idea with a different execution model.
* If the app uses `customLoginBox` or heavily customized Frontegg login screens: ask whether Descope Flows can replace the custom UI or whether the customer requires headless SDK integration.
* If security rules block, challenge, or lock users: ask whether these should become Flow branches using Descope risk signals, fingerprinting, and security Connectors.

Summarize any blockers and Console/Flow/Widget opportunities before proceeding to codebase analysis.

---

### Step 1: Codebase Analysis

Scan the codebase to map every auth touchpoint before writing the plan.

Frontegg ships **frontend SDKs** (`@frontegg/react`, `@frontegg/nextjs`, `@frontegg/vue`,
`@frontegg/angular`, `@frontegg/js`), **backend SDKs** (`@frontegg/client` for Node, `frontegg`
for Python/Flask/FastAPI, `github.com/frontegg/go-sdk`, and a Java package that covers
**entitlements only**), and **mobile SDKs** (iOS `FronteggSwift`, Android `com.frontegg.android`,
React Native, Flutter `frontegg_flutter`, Ionic Capacitor (`@frontegg/ionic-capacitor`)). There is **no official .NET SDK** — .NET
apps use `Microsoft.AspNetCore.Authentication.JwtBearer` pointed at the Frontegg domain as the
authority. Adapt the file extensions below to whichever surfaces appear in the project.

**Run these searches (adapt file extensions to the user's language and platform):**

> **Portability note.** These use POSIX basic regex so they work with both GNU and BSD `grep` (macOS
> ships BSD grep, where GNU extensions like `\b` silently fail to match). If `rg` is available it is
> faster, but translate the alternations to `rg -e` syntax rather than pasting these verbatim.

```bash
# 1. Broad sweep — every Frontegg package, import, config, and domain reference
grep -rni "frontegg" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.mjs" --include="*.cjs" --include="*.vue" --include="*.html" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.java" \
  --include="*.kt" --include="*.kts" --include="*.cs" --include="*.swift" \
  --include="*.dart" --include="*.gradle" --include="*.plist" --include="*.xml" \
  --include="*.json" --include="*.toml" --include="*.properties" \
  --include="*.entitlements" --include="*.pbxproj" --include="*.podspec" \
  --include="*.tf" --include="*.tfvars" --include="*.yml" --include="*.yaml" \
  --include="*.env*" --include="Dockerfile" --include="Podfile" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=venv \
  --exclude-dir=build --exclude-dir=.gradle --exclude-dir=Pods \
  . 2>/dev/null
```

```bash
# 2. Frontend SDK surface — providers, hooks, portal, entitlements, step-up
grep -rn "FronteggProvider\|FronteggAppProvider\|FronteggAppRouter\|FronteggRouter\|withFronteggApp\|FronteggApiMiddleware\|handleSessionOnEdge\|FronteggAppModule\|FronteggAuthService\|FronteggAppService\|useFrontegg\|useAuth(\|useAuthUser\|useAuthUserOrNull\|useAuthActions\|useLoginWithRedirect\|useIsAuthenticated\|useTenantsActions\|tenantsState\|ContextHolder\|AdminPortal\|useEntitlements\|useFeatureEntitlements\|usePermissionEntitlements\|NotEntitledJustification\|useStepUp\|useIsSteppedUp\|SteppedUpContent\|AuthorizedContent\|switchTenant\|requestAuthorize\|loginWithRedirect\|getAppUserSession\|getAppUserTokens\|withSSRSession\|contextOptions\|hostedLoginBox\|authOptions\|keepSessionAlive\|enableSessionPerTenant\|disableSilentRefresh\|customLoginBox" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.mjs" --include="*.cjs" --include="*.vue" --include="*.html" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
  . 2>/dev/null
```

Step-up symbols matter here: step-up is a Step 0 triage question, and Frontegg ships step-up
quickstarts for React, Angular, Vue, and Vanilla JS. Without those patterns a step-up app is
invisible to codebase analysis.

```bash
# 3. Backend SDK surface — middleware, token validation, entitlements client
grep -rn "FronteggContext\|withAuthentication\|IdentityClient\|validateIdentityOnToken\|FronteggAuthenticator\|AuditsClient\|EventsClient\|frontegg.flask\|frontegg.fastapi\|FronteggSecurity\|with_authentication\|frontegg/go-sdk\|frontegg.Init\|WithAuthentication\|UserFromContext\|ValidateToken\|HostedLogin\|CodeExchange\|EntitlementsClientFactory\|engineEndpoint\|engineToken\|isEntitledTo\|lookupTargetEntities\|lookupEntities\|entitlements-client" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.go" \
  --include="*.java" --include="*.kt" --include="*.cs" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=build \
  . 2>/dev/null
```

```bash
# 3b. Entitlements-engine INFRASTRUCTURE — lives in compose/Helm/env files, not source.
#     Both generations show up in the wild; detect either.
grep -rni "e10s\|e10s-engine-sync\|authzed/spicedb\|spicedb\|entitlements-engine\|entitlements-agent\|SPICEDB_ADDRESS\|SPICEDB_GRPC_PRESHARED_KEY\|ENTITLEMENTS_ENGINE_TOKEN\|FRONTEGG_CLIENT_CREDENTIALS_OAUTH\|POLLING_MIN_DELAY\|charts.frontegg.com" \
  --include="*.yml" --include="*.yaml" --include="*.env*" --include="*.tf" \
  --include="*.tpl" --include="Dockerfile" --include="Makefile" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.go" --include="*.java" \
  --exclude-dir=node_modules --exclude-dir=build \
  . 2>/dev/null
```

The current stack is `e10s-engine-sync` + SpiceDB + `@frontegg/e10s-client`; the older, now-deprecated
one is the `frontegg/entitlements-agent` PDP container. A real estate often runs both, so match either.
Note these tokens live in `docker-compose.yml`, Helm values, and `.env` files — greping only source
extensions for them finds nothing.

```bash
# 4. Token claims, cookies, headers, and hand-rolled verification
#    (.NET and Java apps have no Frontegg SDK — they show up only here)
grep -rn "tenantId\|tenantIds\|applicationId\|profilePictureUrl\|email_verified\|vendorMetadata\|fe_refresh\|fe_session\|X-API-KEY\|acr_values\|amr\|auth_time\|max_age\|jwks\|JwtBearer\|jwt.verify\|jwt.decode\|Authority.*frontegg\|\.frontegg\.com" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" \
  --include="*.go" --include="*.java" --include="*.kt" --include="*.cs" \
  --include="*.json" --include="*.yml" --include="*.yaml" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null
```

```bash
# 5. Environment variables and configuration files
grep -rn "FRONTEGG_" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
  --include="*.cs" --include="*.swift" --include="*.dart" --include="*.gradle" \
  --include="*.env*" --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null

# Known Frontegg env vars to expect:
#
# Core (all stacks):
#   FRONTEGG_CLIENT_ID, FRONTEGG_API_KEY, FRONTEGG_BASE_URL, FRONTEGG_APP_URL,
#   FRONTEGG_APP_ID, FRONTEGG_CLIENT_SECRET, FRONTEGG_LOG_LEVEL
# Next.js specific:
#   FRONTEGG_COOKIE_NAME, FRONTEGG_ENCRYPTION_PASSWORD, FRONTEGG_HOSTED_LOGIN,
#   FRONTEGG_JWT_PUBLIC_KEY, FRONTEGG_SHARED_SECRET, FRONTEGG_COOKIE_DOMAIN,
#   FRONTEGG_COOKIE_SAME_SITE, FRONTEGG_SECURE_JWT_ENABLED,
#   FRONTEGG_REWRITE_COOKIE_BY_APP_ID, FRONTEGG_FORWARD_IP, FRONTEGG_SSG_EXPORT,
#   FRONTEGG_TEST_URL, DISABLE_INITIAL_PROPS_REFRESH_TOKEN
# Service endpoint overrides (backend SDKs):
#   FRONTEGG_API_GATEWAY_URL, FRONTEGG_IDENTITY_SERVICE_URL,
#   FRONTEGG_ENTITLEMENTS_SERVICE_URL, FRONTEGG_AUDITS_SERVICE_URL,
#   FRONTEGG_EVENT_SERVICE_URL, FRONTEGG_OAUTH_SERVICE_URL,
#   FRONTEGG_VENDORS_SERVICE_URL, FRONTEGG_METADATA_SERVICE_URL,
#   FRONTEGG_AUTHENTICATION_SERVICE_URL
# Mobile:
#   FRONTEGG_DOMAIN / FRONTEGG_CLIENT_ID / FRONTEGG_APPLICATION_ID (Android buildConfigField)
#
# NOTE: FRONTEGG_CLIENT_SECRET is a CORE Next.js variable as well as an entitlements-engine
# one. Seeing it does NOT imply ReBAC is in use — check search 3b before concluding that.
#
# NOTE: React, Vue, Angular, and Vanilla JS quickstarts hardcode baseUrl/clientId/appId
# inline in `contextOptions` rather than reading env vars. VITE_FRONTEGG_* and
# NEXT_PUBLIC_FRONTEGG_* are community conventions, not official — if search 5 returns
# nothing, rely on search 2 (`contextOptions`) instead of concluding Frontegg is unused.
```

```bash
# 6. Mobile SDK configuration and URL patterns
grep -rn "FronteggSwift\|FronteggWrapper\|FronteggApp\|FronteggAuth\|AbstractFronteggController\|com.frontegg.android\|EmbeddedAuthActivity\|HostedAuthActivity\|AuthenticationActivity\|frontegg_flutter\|FronteggProvider\|frontegg_domain\|frontegg_client_id\|oauth/account/login\|oauth/account/redirect\|oauth/callback\|oauth/logout\|user/token/refresh\|account/login\|account/sign-up\|account/logout\|oauth/portal" \
  --include="*.swift" --include="*.kt" --include="*.java" --include="*.dart" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.xml" \
  --include="*.plist" --include="*.gradle" \
  --exclude-dir=node_modules --exclude-dir=Pods --exclude-dir=build \
  . 2>/dev/null

find . -maxdepth 4 -name "Frontegg.plist" ! -path "*/Pods/*" 2>/dev/null
```

```bash
# 7. Dependency manifests
find . -maxdepth 4 \( \
  -name "package.json" -o -name "go.mod" -o -name "requirements.txt" -o \
  -name "pyproject.toml" -o -name "pom.xml" -o -name "build.gradle" -o \
  -name "build.gradle.kts" -o -name "Package.swift" -o -name "Podfile" -o \
  -name "pubspec.yaml" -o -name "*.csproj" -o -name "Podfile.lock" -o \
  -name "libs.versions.toml" -o -name "settings.gradle" \
\) ! -path "*/node_modules/*" ! -path "*/build/*" \
  -exec grep -il "frontegg" {} \;
```

`grep -il`, not `-l`: a `Podfile` contains `pod 'FronteggSwift'` with a capital F, so a
case-sensitive search silently skips every CocoaPods project.

```bash
# 8. Prehook and webhook handlers (often a separate service — ask if nothing is found)
#    All 13 prehook events, and webhook prefixes that "frontegg.user." alone would miss.
grep -rni "prehook\|pre-hook\|AUTH_INITIATED\|USER_SIGNUP\|USER_INVITE\|USER_UPDATE\|USER_DELETE\|CREATE_TENANT\|UPDATE_TENANT\|DELETE_TENANT\|JWT_GENERATION\|SOCIAL_LOGIN_AUTH\|OIDC_AUTH\|SAML_AUTH\|SEND_SMS\|SIGN_UP_USER_POOL\|x-webhook-secret\|frontegg\.user\|frontegg\.tenant\|frontegg\.group\|frontegg\.scim\|frontegg\.account" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.go" \
  --include="*.java" --include="*.kt" --include="*.cs" \
  --exclude-dir=node_modules --exclude-dir=build \
  . 2>/dev/null
```

Note the webhook prefixes drop the trailing dot: `frontegg\.user\.` does **not** match
`frontegg.userApiToken.created`, and `frontegg\.tenant\.` misses `frontegg.tenantApiToken.*`.

For each hit, record:

- **File path and line** — where the change happens
- **What it does** — import, provider setup, route protection, claim access, tenant read, portal embed, entitlement check, prehook handler, webhook handler, logout handler, etc.
- **Complexity** — Low (drop-in replacement), Medium (logic rewrite), High (no equivalent)

Read `package.json` (or equivalent) for the exact framework and SDK versions. Frontegg gates several
behaviors on minimum SDK versions (multi-app support, `enableSessionPerTenant`, `silentReload` on
`switchTenant`, entitlements, `AdminPortal.openHosted()`), so the installed version tells you which
features could have been in use. Next.js version also affects async behavior (15 vs. 14).

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
sessions, accounts, and existing user records are preserved.

Include a **Migration at a Glance** table:


|                                  |                                                                     |
| -------------------------------- | ------------------------------------------------------------------- |
| **Approach**                     | Full native migration                                               |
| **Login model**                  | Frontegg hosted → Descope Auth Hosting / Frontegg embedded → embedded Flow |
| **Files changing**               | N source files across N areas                                       |
| **Console setup**                | N configuration steps before launch                                 |
| **User impact**                  | Users will need to log in once after cutover; passwords must be reset / users move to passwordless |
| **Estimated engineering effort** | N–N hours                                                           |
| **Biggest risk**                 | One sentence naming the highest-complexity item                     |


---

#### What's Changing and Why

Prose (not a table) describing what each part of the system does today and what it does
after. Example:

> Today, Frontegg handles everything related to login: the Frontegg login box (hosted at
> `[subdomain].frontegg.com` or embedded via injected `/account/login` routes) renders the sign-in
> experience, issues an access token plus a `fe_refresh` cookie, and the backend SDK's
> `withAuthentication` middleware validates the token on every request — reading `tenantId`,
> `roles`, and `permissions` off the JWT. After this migration, Descope takes over all of those
> responsibilities. The login UI becomes a Descope Flow. Session validation moves to the Descope
> SDK, reading the `DS` cookie. Frontegg Accounts become Descope Tenants. `FRONTEGG_CLIENT_ID`,
> `FRONTEGG_API_KEY`, and `FRONTEGG_BASE_URL` are replaced by `DESCOPE_PROJECT_ID` (plus a
> Management Key for server-side administration).
>
> Frontegg features in use that need to carry over: [list in plain English, one clause each].

Tailor to triage findings.

---

#### Client SDK vs. Backend SDK: A Specific 1-to-1 Mapping

For every Frontegg touchpoint found in triage, produce a concrete, one-to-one mapping — Frontegg
construct → the exact Descope SDK and method that replaces it — and state explicitly whether that
replacement runs in the **client SDK** or the **backend SDK**, and why. Use this division of
responsibility:

- **Client SDK** (`@descope/web-js-sdk`, `@descope/react-sdk`, `@descope/nextjs-sdk` client
  components, or the `<descope-wc>` web component) — everything the user's browser or mobile app
  does: rendering the login/sign-up UI (a Descope Flow replaces the Frontegg login box, whether
  hosted or embedded), initiating authentication, holding the session on the client, refreshing
  the token, and reading the current user for UI purposes. This replaces `FronteggProvider` /
  `FronteggAppProvider`, `useAuth()`, `useAuthUser()`, `useLoginWithRedirect()`,
  `useIsAuthenticated()`, `useTenantsActions()`, and `ContextHolder`. It uses only the public
  Project ID — never a Management Key.
- **Backend SDK** (`@descope/node-sdk`, `descope` (Python), `github.com/descope/go-sdk`, etc.) —
  everything the server does: validating the session JWT on every request (replacing
  `withAuthentication()`, `IdentityClient.validateIdentityOnToken()`, `FronteggSecurity(...)`,
  `frontegg.WithAuthentication(...)`, or a hand-rolled `jwt.verify` against
  `FRONTEGG_JWT_PUBLIC_KEY`), checking roles and permissions, and — with a Management Key — all
  administrative operations done by ID (user and tenant CRUD, role/permission definitions,
  SSO/SCIM configuration, ReBAC). This also replaces every direct call to `api.frontegg.com`.

For each file or area, name the Frontegg call, the Descope SDK that replaces it, which side it runs
on, and the reason (e.g. "session validation must stay server-side because the Management Key cannot
ship to the browser"). When one Frontegg feature spans both sides — for example the login box (now a
client Flow) plus per-request `withAuthentication` validation (now the backend SDK) — split it into
its client half and its backend half so the reader sees exactly what moves where, and why.

---

#### Auth Touchpoints: What the Code Analysis Found

Open with the scope count (e.g., "14 files across 5 areas"). Group by area, not file path.
Each group gets a sentence on what it does and what changes.

**Session handling (3 files)** — These files read and validate the current user's login state.
They'll be updated to use the Descope session SDK instead of Frontegg token validation.


| File               | What it does today                                                                                    | What changes                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `lib/auth.ts:34`   | Calls `identityClient.validateIdentityOnToken()`; returns `sub`, `tenantId`, `roles`, `permissions` | Rewritten to return Descope `authInfo`; a thin adapter layer preserves the shape callers expect |
| `middleware.ts:12` | Runs `withAuthentication()` and blocks unauthenticated requests app-wide                              | Updated to validate the Descope `DS` cookie via `validateSession()`; logic is identical, SDK call changes |


**Login / auth UI (2 files)** — These mount the Frontegg provider and trigger the login box.
Descope replaces this with an embedded Flow component (or hosted Flow).


| File                         | What it does today                                      | What changes                                                                                                  |
| ---------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `app/layout.tsx`             | Wraps the app in `FronteggAppProvider` with `contextOptions` | Replaced with Descope `AuthProvider projectId={...}`   |
| `app/login/page.tsx`         | Calls `loginWithRedirect()` (hosted) or relies on injected `/account/login` (embedded) | Replaced with `<Descope flowId="sign-up-or-in">`, or a redirect to Descope Auth Hosting for the hosted model |


Cover all functional groupings found — tenant switching, self-service portal embeds, entitlement
checks, prehook handlers, webhook handlers, M2M token issuance, mobile SDK auth. End with:
"Total: N files. Estimated code-change effort: N–N hours."

---

#### Feature Migration: Frontegg → Descope

For each Frontegg feature confirmed in triage, write a short paragraph: what it's trying to
accomplish, the best Descope approach for that goal, what's different, and what action is
required. The best approach may be a Flow, Widget, SSO Setup Suite, or Console configuration
rather than a direct SDK equivalent — reason about the intent, not just the API surface. Only
recommend SDK code when programmatic control is genuinely required. Example:

> **Multi-tenancy (Frontegg Accounts → Descope Tenants)**
> Frontegg calls the top-level customer object an **Account**, and the docs state that Accounts and
> Tenants are the same thing — the JWT carries `tenantId` for the active account and `tenantIds` for
> every account the user belongs to. Descope has the same concept, called **Tenants**. In most
> migrations, map one Frontegg account to one Descope tenant ID.
>
> Most code that handles Frontegg accounts is management code that passes a `tenantId` to the
> Frontegg API — loading an account, updating settings, managing users, assigning roles, configuring
> SSO or SCIM. That becomes Descope tenant/user management code that passes a Descope tenant ID to
> the relevant operation. This is mostly by-ID management work, not token parsing.
>
> The main request-time difference is the session shape. Frontegg puts the active account in a flat
> `tenantId` claim and the full membership list in `tenantIds`. Descope exposes the active tenant as
> `dct` and per-tenant roles and permissions as a keyed `tenants` object. Prefer SDK helpers such as
> `validateTenantRoles(...)` or `validateTenantPermissions(...)` over reading claims by hand.
>
> Confirm the account→tenant mapping first, since it ripples into SSO, SCIM, RBAC, the self-service
> portal replacement, M2M tokens, and any application tables storing `tenantId`. If **sub-accounts**
> are in use, they map to Descope sub-tenants — decide the role-inheritance mode explicitly, and check
> whether any code reads hierarchy from the token, since the `tenants` claim is flat.

> **Effort: Medium (1–2 hours of code changes).** Confirm the account data migration path first.

Only include confirmed features.

---

#### Before the Code Can Run: Required Configuration

Some Descope behavior is configured in the console, not in code. List every item that must
be set up before the app works, as checkboxes with a plain description of what it is, why
it's needed, and roughly how long it takes. Group into "Required before any testing" and
"Required before production":

**Required before any testing:**

- **Create a Descope project** — Takes 2 minutes. Produces a Project ID that replaces
  `FRONTEGG_CLIENT_ID` and `FRONTEGG_BASE_URL` in the app's environment variables.
- **Configure Approved Domains** — Descope validates redirect targets against a domain list.
  Enter domain only (`localhost:3000`, `app.myapp.com`) — not the Frontegg-style full callback
  URLs like `http://localhost:3000/oauth/callback`.
- **Create an authentication flow** — Descope uses a visual "flow" to define the login
  experience. The built-in `sign-up-or-in` flow works for most apps and requires no
  customization to start.
- **Configure a JWT Template** — By default, Descope session tokens don't include the user's
  name, email, or profile photo, and Frontegg's tokens do. Any UI reading `email`, `name`, or
  `profilePictureUrl` off the token shows nothing after login until this is configured.
  (~10 minutes)

**Required before production:**

- **Create tenants for each Frontegg Account** — Descope Tenants must exist before
  tenant-scoped code (SSO, roles, membership) will work.
- **Create roles and permissions** — Descope roles are referenced by name and must exist in the
  Console before code that assigns them will work.
- **Configure SSO connections per tenant** (or enable the SSO Setup Suite for self-serve).
- **Configure social login providers** — OAuth credentials for each provider must be entered in
  the Console. Note that Frontegg ships shared development credentials for most social providers;
  if the app was relying on those, real OAuth credentials must be created for the first time.
  (~15 minutes per provider)
- (continue for each item found in analysis)

---

#### Environment Variables

Diff table with plain-English notes for each removal and addition:


| Remove                              | Add                              | Why                                                                                                                                 |
| ----------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `FRONTEGG_CLIENT_ID`                | `DESCOPE_PROJECT_ID`             | Frontegg's per-environment client identifier. Descope uses a Project ID for the same purpose. |
| `FRONTEGG_API_KEY`                  | `DESCOPE_MANAGEMENT_KEY`         | Frontegg's environment secret, used to mint a vendor token for management APIs. Descope session validation needs only the Project ID; a Management Key is required only for server-side user/tenant/SSO/SCIM administration. |
| `FRONTEGG_BASE_URL`                 | *(none)*                         | Frontegg's per-environment domain. Descope SDKs resolve the endpoint from the Project ID, so no base URL is needed unless a custom domain is configured. |
| `FRONTEGG_APP_URL`                  | *(none)*                         | Used by Frontegg to build redirect URLs. Descope uses Approved Domains configured in the Console instead. |
| `FRONTEGG_APP_ID`                   | *(depends)*                      | Only if multi-app is in use. Decide whether each Frontegg Application becomes its own Descope Project or a Federated/Inbound App. |
| `FRONTEGG_ENCRYPTION_PASSWORD`, `FRONTEGG_COOKIE_NAME`, `FRONTEGG_HOSTED_LOGIN`, `FRONTEGG_JWT_PUBLIC_KEY` | *(none)* | Next.js session-cookie encryption, cookie naming, login-mode toggle, and the inlined signing key. Descope manages the `DS`/`DSR` cookies and key rotation itself. |
| `FRONTEGG_*_SERVICE_URL`, `FRONTEGG_API_GATEWAY_URL` | *(none)* | Per-service and regional endpoint overrides. Not needed. |
| *(frontend, if present)* `contextOptions` hardcoded `baseUrl` / `clientId` | `NEXT_PUBLIC_DESCOPE_PROJECT_ID` or framework equivalent | Frontegg quickstarts often hardcode these inline rather than using env vars. Replace with the Descope Project ID exposed to the browser. |


Follow with: "Net change: 4–8 variables removed, 2–3 added. No secrets need to be rotated on the
Frontegg side — those credentials stop being used, though the Frontegg environment should be
retained read-only until the migration is verified."

---

#### User & Account Migration (only if existing users/accounts need to be migrated)

Prose strategy first, then steps. Start with: "X existing users across Y accounts need to be in
Descope before cutover." Describe:

- **The plan**: whether this is big-bang (all users/accounts moved before cutover) or phased, and why
- **Account→tenant mapping**: each Frontegg Account becomes a Descope Tenant; note how sub-accounts are handled
- **What users will experience**: they will need to log in again, and — unless a lazy migration is built — set a new password or move to a passwordless method
- **The biggest dependency**: how password credentials carry over. State plainly that Frontegg has no documented password-hash export, and name the chosen strategy
- **SCIM continuity**: whether enterprise directories must be re-pointed at Descope (a continuing pipeline, not a one-time import)

End with a brief checklist of the migration steps at the level a PM can track. For a **full
migration**, prefer Descope's [migration tool](https://github.com/descope/descope-migration) over a
hand-written script — but confirm it ships a Frontegg module before committing the plan to it, and
fall back to a custom export/import script if it does not:

- Obtain a Frontegg Client ID and API Key with read access to tenants, permissions, roles, and users
- Configure the migration tool's `.env` (`FRONTEGG_CLIENT_ID`, `FRONTEGG_API_KEY`, `FRONTEGG_BASE_URL`, `DESCOPE_PROJECT_ID`, `DESCOPE_MANAGEMENT_KEY`)
- Run a dry run against a Descope **dev** project and review the output
- Review discovered custom attributes and confirm the Descope attribute schema
- Verify tenant, role, and permission creation before user creation
- Reconcile duplicates (SCIM email changes create orphaned Frontegg users)
- Re-point SCIM at Descope (if SCIM is in use)
- Run against staging, then production
- Set `freshlyMigrated` and drive the password-reset or passwordless onboarding campaign

For a **JIT migration**, the checklist is different — there is no bulk export:

- Configure the JIT path in the Descope Flow (Generic HTTP Connector to Frontegg, or Frontegg as a custom OIDC provider)
- Enable dual-token validation in the backend so both Descope and Frontegg sessions work during the transition
- Roll out, monitor provisioning rate, and add a Flow condition routing already-provisioned users to Descope-native auth
- Keep Frontegg running until the active-user tail has signed in, then decommission

---

#### Trade-offs and considerations

Things that could affect timeline, user experience, or scope. Write each in plain English
with three parts: **what it is**, **what breaks if it's ignored**, and **what to do**.
Format each as a named callout:

> **Consideration: Frontegg does not export password hashes**
> Frontegg's documented migration API is inbound only, and no user-management endpoint returns a
> credential field. If the plan assumes passwords transfer, the cutover date is wrong.
> **Action:** Pick one of Descope's three supported paths now — full migration plus forced reset or
> passwordless onboarding, JIT migration through a Generic HTTP Connector (the only way to keep
> passwords working), or JIT through Frontegg as a custom OIDC provider. The two JIT paths require
> keeping Frontegg running until the active-user tail has signed in.

> **Consideration: the self-service portal is a large surface, not a component**
> Frontegg's portal gives end customers screens for users, groups, custom roles, security policy,
> SSO, SCIM, audit logs, webhooks, and API tokens. Rebuilding all of it as custom code can cost more
> than the rest of the migration combined.
> **Action:** Inventory which modules are actually enabled and used, map them to Descope Widgets and
> the SSO Setup Suite, and get an explicit decision on anything with no widget equivalent.

> **Consideration: account-to-tenant mapping affects almost every B2B feature**
> If this mapping is wrong, SSO, SCIM, roles, permissions, domain routing, and membership checks
> may all break.
> **Action:** Confirm the account model — including sub-accounts — before writing migration code.

> **Consideration: SCIM is a lifecycle system, not just a user import**
> Enterprise directories keep creating, updating, and deprovisioning users after cutover.
> **Action:** Identify every SCIM connection and re-point it at Descope before cutover.

> **Consideration: user profile data won't appear after login until a JWT Template is configured**
> Frontegg's access token carries `name`, `email`, `email_verified`, and `profilePictureUrl` by
> default; Descope's does not. Any UI displaying user information shows blank values until the
> template is configured. This is a one-time Console step, not a code change.
> **Action:** Configure the JWT Template before running any tests. Estimated time: 10 minutes.

> **Consideration: entitlements and feature flags are not part of Descope**
> If `isEntitledTo` or feature flags gate application behavior, that logic needs a home.
> **Action:** Decide whether the access-control portion maps to Descope roles/permissions and tenant
> custom attributes, and treat general feature flagging as a separate workstream.

Include only applicable trade-offs and considerations.

---

#### Execution Plan

Open with one sentence: phases run in sequence; steps within a phase can run in parallel.
Then labeled phases, each with a time estimate:

---

**Phase 1 — Console Setup** (~30–60 minutes, no code required)
Can be done by any team member with Descope console access, in parallel with other work.

- Create a Descope project per Frontegg environment, copy each Project ID
- Configure Approved Domains (domain only — e.g. `localhost:3000`, not `http://localhost:3000/oauth/callback`)
- Create the authentication flow (use the built-in `sign-up-or-in` to start)
- Configure the JWT Template for profile claims
- Create tenants for each Frontegg Account (list actual accounts found)
- Create roles and permissions (list actual roles found)
- Configure SSO connections per tenant or enable the SSO Setup Suite (if SSO in use)
- Configure social login providers with real OAuth credentials (list actual providers found)

**Phase 2 — Code Changes** (~X–Y hours, 1 engineer)
Work through files in the order listed. Run a compile check after each group.

- Update environment variables in `.env.example` and CI config (15 min)
- Replace the Frontegg provider with the Descope provider and swap the login entry point (30 min)
- Rewrite the session helper / middleware to validate the `DS` cookie (30 min)
- Update protected route files to use the new session check (45 min)
- Repoint tenant handling — management calls pass a `tenantId`; request-time reads use `dct`/`tenants` (varies)
- Replace self-service portal embeds with Descope Widgets (varies)
- Update logout — two-step logout (15 min)
- Compile check and fix any type errors before proceeding

**Phase 3 — User & Account Migration** (~1–2 hours, includes dry run)
Run against dev/staging first. Do not run against production until Phase 4 passes.

- (steps from the user & account migration section above)

**Phase 4 — Testing** (~30–45 minutes)

- Compile passes with zero errors
- Server starts, no crashes on startup
- Unauthenticated routes redirect to login correctly
- Login flow completes, user profile data appears (confirms the JWT Template is working)
- Tenant/SSO routing works for at least one account
- Logout invalidates the session

**Phase 5 — Production Cutover**

- (cutover-specific steps based on their strategy — maintenance window, phased rollout, SCIM re-point, password reset campaign, etc.)

---

Total estimated engineering effort: **N–N hours** across N engineers.
Blocking dependencies: (list anything on the critical path — console access, Frontegg API key for export, SCIM re-point, password reset comms.)

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
- Frontegg login model: [Hosted / Embedded]
- Migration goal: [Full cutover / Phased / Evaluating]

## Triage Answers
- Existing users: [Yes — N users / No — greenfield]
- Existing accounts: [Yes — N accounts → tenants / No]
- Sub-accounts in use: [Yes / No]
- Password strategy: [Forced reset / Passwordless / Lazy migration / Support-assisted export]
- Frontegg features in use: [comma-separated list]
- Frontegg environments: [Dev / Staging / QA / Prod — how many]
- Frontegg region: [EU / US / AU / CA]
- Zero-downtime required: [Yes / No]

## Files Inventory
_All files that need to change. Update status after each step._

| File | Change | Status |
|---|---|---|
| `app/layout.tsx` | Replace FronteggAppProvider | ⬜ Pending |
| `lib/auth.ts` | Rewrite session helper | ⬜ Pending |
| `middleware.ts` | Update session check | ⬜ Pending |

## Console Setup Checklist
- [ ] Descope project created — Project ID: (fill in when done)
- [ ] Approved Domains configured (domain only — e.g. `localhost:3000`, not `http://localhost:3000/oauth/callback`)
- [ ] JWT Template configured
- [ ] Tenants created for each Frontegg Account: (list)
- [ ] Roles and permissions created: (list)
- [ ] SSO connections / SSO Setup Suite configured: (list)
- [ ] Social providers configured with real OAuth credentials: (list providers)

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
grep -rn "from '@frontegg/\|from \"@frontegg/\|require('@frontegg/\|import frontegg\|from frontegg\|frontegg/go-sdk\|com\.frontegg" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.kt" --include="*.java" .
```

Add remaining hits to the work list.

**2. Derive wrapper types from the actual return type.**
Read the function's declared return type and build the wrapper to match. Frontegg's user object
is flat and carries `tenantId` / `tenantIds` / `roles` / `permissions` at the top level; Descope's
`authInfo` nests tenant data differently. Don't infer one from the other.

**3. Check dependency versions before generating framework-specific code.**
For Next.js: `cookies()` and `headers()` from `next/headers` are synchronous in v14 and
async in v15. Read `package.json` (or `go.mod`, `requirements.txt`) first.

**4. When making a helper async, propagate to all callers immediately.**
In TypeScript, `async` on a shared utility silently breaks callers that omit `await`. Grep
for all call sites of the changed function and update them in the same pass. The cascade can
span 10–20 files.

**5. Verify published package versions before writing to `package.json` or running `npm install`.**
Don't reuse Frontegg's version number or rely on training data for versions. Before writing any
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
yes, skip to verifying items 5–9 — these are easy to miss even for existing projects.

### 1. Create a project and get your Project ID

- Sign in at [console.descope.com](https://console.descope.com)
- Your **Project ID** appears in the top-left project selector and under **Project → General**. It starts with `P` (e.g. `P2abc123...`).
- For Next.js client-side code, this becomes `NEXT_PUBLIC_DESCOPE_PROJECT_ID`. For all server-side SDKs, it's `DESCOPE_PROJECT_ID`.
- **Create one Descope project per Frontegg environment.** Frontegg environments are fully isolated (separate Client ID, API Key, and domain), and Descope projects work the same way. Frontegg lets you publish a login box between environments; Descope projects are configured independently, so plan to repeat Console setup per environment or script it with the Management SDK.

### 2. Get a Management Key (if needed)

Required for: user management API, role/permission management, tenant operations, SSO/SCIM
configuration, ReBAC (FGA), Outbound Apps. If the app does any server-side user, tenant, SSO,
or SCIM management — or if you are running a user import — they need this.

- Console → **Company Settings → Management Keys → + Management Key**
- Store as `DESCOPE_MANAGEMENT_KEY`. Treat like a secret — never expose client-side.

### 3. Choose or create a Flow

A Flow is the auth UI sequence. Reference it by Flow ID in the web component.

- Console → **Flows**
- The built-in **"sign-up-or-in"** flow handles email/password, OTP, and social login. Use it for most migrations.
- To customise: duplicate "sign-up-or-in", rename it, then edit in the visual builder.
- The Flow ID is in the URL when editing and in the flow list.
- There's a large Flow template library — check for an existing template before building a custom flow. See `references/flows-and-widgets.md` → Flows.
- MFA: add an MFA step to the Flow or embed MFA as a subflow. Descope manages MFA enrollment through Flows.

**Hosted vs. embedded matters here — and hosted has no drop-in equivalent for a first-party app.**
Descope's **Auth Hosting** looks like the obvious match for Frontegg's hosted login box
(`loginWithRedirect()`, `/oauth/account/login`), but Auth Hosting is built for cases where Descope
itself is acting as an OIDC/SAML **identity provider** to something else — a Federated App, an Inbound
App, or an MCP/Agentic Client — not as a generic redirect-and-come-back page for an arbitrary
first-party origin. Its session is established against the Descope-hosted page itself; there's no
documented `redirect_uri` round-trip back to your own domain unless your app is actually configured
as one of those OIDC-client object types. Treating "hosted → Auth Hosting" as a mechanical swap can
produce an app where login appears to complete and the user is still signed out. Present this as a
decision with real trade-offs rather than assuming the mapping transfers for free:

- **Embedded `<Descope flowId>` component** (the well-trodden path for web apps) — same Flows, same
  session tokens, no DNS work. The natural choice even for an app that used to be hosted-mode, unless
  something specifically requires the redirect model.
- **Auth Hosting behind a custom domain (CNAME)** — preserves a redirect-based UX. Required if the app
  needs to manage refresh tokens in first-party cookies, or if branding/URL stability matters. Ask
  whether the Frontegg app had a **custom domain**, and if so, whether it existed for branding or to
  dodge third-party-cookie failures on the refresh endpoint (see Step 4) — either reason argues for a
  Descope custom domain too.
- **Model the app as an OIDC client of a Descope Inbound/Federated App** — the case where Auth
  Hosting's documented `redirect_uri` handling genuinely applies as designed.

Ask which of these fits before writing code — it changes routing, redirect handling, and session
bootstrapping together, and reversing the decision later touches all three. **Mobile is the one case
where this isn't a real choice**: Frontegg mobile SDKs are always hosted, embedded doesn't exist as a
concept there, and a mobile migration runs a Descope Flow through the native SDK regardless. Match
the existing embedded/hosted model unless the user explicitly wants to change it on a web app;
switching models mid-migration changes routing, redirect handling, and session bootstrapping all at
once.

### 4. Configure authentication methods

- Console → **Authentication** → select methods (Email OTP, Magic Link, Social, SSO, Passkeys, etc.)
- For social providers: configure OAuth credentials here, then add the provider step to your Flow.
  **Frontegg ships shared development credentials for most social providers** (all except LinkedIn),
  so an app that "had Google login working" may never have registered its own OAuth app. Budget time
  to create real credentials with each provider.
- For enterprise SSO (SAML/OIDC): to configure SSO for a specific tenant or to enable the SSO Setup Suite for tenant-admin self-serve, go to Console → **Tenants**, select the tenant, and click **Tenant Settings**.

### 5. Configure Approved Domains (local dev and production)

Console → **Project Settings → General → Security → Approved Domains**.

Descope validates redirect URLs against this domain list — **not** full redirect URIs the way
Frontegg's allowed-origins and callback registrations do. Enter **domain only**: no `http://` or
`https://`, no path.

- Local dev: `localhost:3000` (include port)
- Production: `myapp.com` or `app.myapp.com`

**Do not** carry over Frontegg callback URLs like `http://localhost:3000/oauth/callback`. Descope
embedded Flows complete auth client-side; there is no `/oauth/callback` route to whitelist. Note
also that Frontegg's allowed origins support wildcards (`https://*.acme.com`) — confirm how any
wildcard entry should be represented before assuming a one-to-one copy.

### 6. Configure a JWT Template (almost always needed)

Frontegg's access token carries profile claims by default; Descope's does not.

- Console → **Project Settings → JWT Templates**
- Add claims: `{"email": "{{user.email}}", "name": "{{user.name}}", "picture": "{{user.picture}}"}`.
  To confirm the exact placeholder syntax in any given project rather than trusting memory, read the
  built-in **"Default OIDC compliant User JWT"** template that ships with every project — it already
  uses `{{user.email}}`.
- **Set `authSchema: "default"` on the template.** Without it, the `tenants`/`roles`/`permissions`
  claims are omitted from the token even if the app otherwise looks correctly configured — this is a
  common way to "do everything right" and still get no tenant/role data at request time.
- Before saving, validate the template with the `ValidateJwtTemplate` operation (dry-run; a
  `CreateJwtTemplate` call with bad shape fails validation up front rather than saving something
  broken) — either via the Descope MCP if available, or the equivalent Console preview.
- Apply the template to your project. Without this step, any code reading `token.email`,
  `token.name`, or `token.profilePictureUrl` will get `undefined` after migration.
- If the app relies on custom claims injected by a Frontegg `JWT_GENERATION` prehook, those belong
  here too (or in a Flow custom-claims action). See Step 3 → *Prehooks*.

### 7. Create roles and permissions in the Console (if using RBAC)

Descope roles are referenced by **name**, not by ID. They must be created before the code that
assigns them will work.

- Console → **Authorization → RBAC → + Role**
- Create each role the app references. Frontegg role **keys** (not display names) are what appear in
  the `roles` JWT claim, so migrate the keys.
- Frontegg's built-in `fe.*` permissions (e.g. `fe.secure.read.users`) exist to gate the Frontegg
  self-service portal. Do **not** recreate them wholesale — they only matter if application code
  reads them. Recreate the customer's own permission keys instead.

### 8. Define custom attributes (if using Frontegg metadata)

Frontegg has two metadata fields with different semantics: `metadata` is included in the JWT, and
`vendorMetadata` is deliberately excluded from it and is often where a pre-Frontegg internal user ID
was stored. Both map to Descope custom attributes, which should be pre-defined in the Console schema
before being set via the SDK.

- User custom attributes: Console → **Users → Custom Attributes tab**
- Tenant custom attributes: Console → **Tenants → Custom Attributes tab → Create Attribute**
- Attributes must exist in the Console schema **before** any import or SDK call sets them. You cannot
  invent `freshlyMigrated` or `fronteggId` at import time — define them first.
- If sub-accounts are in use, create the corresponding Descope **sub-tenants** rather than flattening,
  and set the role-inheritance mode on each parent. Note that `tenant.subtenant` is a **boolean for
  the currently selected tenant only** — it says whether that tenant has a parent, not which parent,
  and nothing about the user's other tenants. Anything richer needs a server-side Load/Search Tenant
  call reading `parent` / `successors`.

### 9. Env var summary


| Variable                         | Where to get it                     | Used by                                     |
| -------------------------------- | ----------------------------------- | ------------------------------------------- |
| `DESCOPE_PROJECT_ID`             | Console → Project Settings          | All server-side SDKs                        |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value as above                 | Next.js `AuthProvider` (client-side)        |
| `DESCOPE_MANAGEMENT_KEY`         | Console → Company Settings → Management Keys | Management SDK, SSO/SCIM, user import, Outbound Apps API |


### 10. Consider Widgets for management UI

Before migrating anything the Frontegg self-service portal used to handle, ask whether a Descope
Widget or the SSO Setup Suite covers the use case. This is the single largest opportunity to avoid
writing code in a Frontegg migration. See `references/flows-and-widgets.md` → Widgets and
Step 3 → *Self-service portal*.

**Enumerate the project's actual widgets before referencing any `widgetId` in code.** Not every
widget is provisioned by default in a fresh project, and the SDK exports and types every widget
component regardless of whether it's actually provisioned — so a missing widget is invisible to
TypeScript and shows up only at runtime. See Step 4 → *A widgetId with no widget behind it fails as
an authorization error*.

### 11. If the Descope MCP is available, let it do the console setup it can — and read state first

The Descope MCP server automates a real share of this checklist, but not all of it, and writes require
explicit elevation. Before manually clicking through the Console:

- **Read current state before creating anything.** A project may already have what you're about to
  "create" — the built-in `sign-up-or-in` flow, a `Tenant Admin` role, and several default widgets
  (profile, user management, role management, access keys) typically ship with every project. Use the
  read operations first (listing flows, widgets, roles, permissions, users) so planned "create" steps
  don't duplicate what already exists.
- **Automatable:** JWT templates (create, plus a dry-run validate operation before saving), tenants
  (including custom attributes), roles and permissions, and reading current project state.
- **Not exposed via the management API/MCP:** Approved Domains, and attaching a JWT Template to
  Session Management's Token Format setting. These are project-settings changes that stay
  Console-only clicks regardless of MCP availability.
- **Writes require elevation.** Every mutating operation needs an explicit user confirmation naming
  the exact operation and target before it runs — batch related confirmations together (e.g. "create
  these 4 tenants") rather than asking once per call.
- **Permissions may gate this entirely.** The Management Key or role connected to the MCP may not have
  write access to everything (user creation and role assignment are common gaps) — confirm what's
  actually writable before promising to automate a step.

**After completing console setup:** Update `MIGRATION-STATE.md` — check off each completed
item in the Console Setup Checklist, record the Project ID in the file, and set Next Action
to the first code change step.

---

## Step 2: Framework-Specific Migration

Frontegg publishes three SDK families:

- **Frontend SDKs**: `@frontegg/react`, `@frontegg/nextjs`, `@frontegg/vue`, `@frontegg/angular`, `@frontegg/js` (plus the shared `@frontegg/types` and `@frontegg/rest-api`). These render the login box, hold the client session, and expose auth state through hooks or observables.
- **Backend SDKs**: `@frontegg/client` (Node), `frontegg` (Python — Flask and FastAPI), `github.com/frontegg/go-sdk`. The Java packages (`com.frontegg.sdk:entitlements-client*`) cover **entitlements only**, and there is **no official .NET SDK** — .NET apps use `Microsoft.AspNetCore.Authentication.JwtBearer` with the Frontegg domain as the authority.
- **Mobile SDKs**: iOS (`FronteggSwift`), Android (`com.frontegg.sdk:android`), React Native, Flutter (`frontegg_flutter`), Ionic Capacitor (`@frontegg/ionic-capacitor`). Mobile always uses hosted login.

The recipes below map each Frontegg SDK to its Descope target — one section each.

> The framework recipes below are stubs listing the Frontegg idioms that need mapping. Confirm the exact Frontegg SDK surface for the user's stack and the matching Descope SDK calls via the Descope MCP or local type declarations before generating any code. Do not ship code from these stubs without verification.

Read `references/implementation-nuances.md` in two passes before writing any code:

1. **General Insights** (always) — covers architecture, feature mapping, user export, and common gotchas that apply to every migration regardless of framework.
2. **Framework section** (use the file's ToC and `offset` to jump directly) — read only the section matching the user's stack.

When a new framework is added to the file, add it to this list.

### Common Frontegg idioms to map (all frameworks)

- `FronteggProvider` / `FronteggAppProvider` / `FronteggAppModule.forRoot()` / `app.use(Frontegg, …)` / `initialize({...})` → Descope `AuthProvider` (or the framework's equivalent provider), configured with the Project ID instead of `baseUrl` + `clientId` + `appId`
- Hosted login `loginWithRedirect()` → redirect to Descope Auth Hosting (or a Flow-hosted URL)
- Embedded login (injected `/account/login`, `/account/sign-up` routes) → an embedded `<Descope flowId>` / `<descope-wc>` component on the app's own login route
- `useAuth()` / `useAuthUser()` / `authState$` / `app.store.getState().auth` → Descope `useSession()` + `useUser()` hooks (or the framework equivalent)
- `useIsAuthenticated()` → `useSession()`'s authentication state
- `useTenantsActions().loadTenants()` / `switchTenant({ tenantId })` → Descope tenant selection; read membership from the validated session (`tenants`) and the active tenant from `dct`
- `ContextHolder.getContext()` (reading `baseUrl`, tokens) → Descope SDK session accessors; do not hand-parse the token
- `AdminPortal.show()` / `AdminPortal.openHosted()` → Descope Widgets and the SSO Setup Suite (see Step 3)
- `useFeatureEntitlements()` / `usePermissionEntitlements()` / `isEntitledTo()` → Descope roles/permissions where the check is access control; otherwise out of scope (see Step 3)
- Backend `withAuthentication()` / `validateIdentityOnToken()` / `FronteggSecurity(...)` / `frontegg.WithAuthentication(...)` → custom middleware calling the Descope SDK's `validateSession()` against the `DS` cookie
- Frontegg access token in `Authorization: Bearer`, refresh in the `fe_refresh` cookie → Descope signed session JWT in `DS`, refresh in `DSR`
- Hosted logout navigation to `{baseUrl}/oauth/logout?post_logout_redirect_uri=…` or embedded `logout()` → Descope two-step logout (see Step 4)
- **Frontegg let client code do things Descope treats as management operations** — several Frontegg frontend SDKs expose tenant-user listing, invites, and role assignment directly to the browser, gated only by `fe.*` permissions on the client's token. The Descope equivalents require a Management Key, which must never ship to a client. Audit every such call explicitly: it becomes a server endpoint the client calls, or a Descope Widget acting as the logged-in user — never a like-for-like client-side port. This is the kind of code most likely to get carried over verbatim into a credential leak, because it looks like ordinary client code and worked fine on the Frontegg side.

### Frontend SDKs

> **Read the session the framework-native way — never hand-parse the JWT on the client.** On
> front-end pages and components, get auth state from the Descope hooks: `useSession()` for the
> session token and auth status, `useUser()` for the user profile, and `useDescope()` for actions
> like `logout()`. Do **not** manually decode the session token or pull claims out of it in client
> code. This is a common Frontegg habit — `ContextHolder` makes the raw token easy to reach — and it
> should not carry over. Server-side session *validation* belongs only in backend routes,
> middleware, and API handlers, never in a rendered client component.

#### React

*Frontegg SDK: `@frontegg/react` → Descope `@descope/react-sdk`*

- `<FronteggProvider contextOptions={{ baseUrl, clientId, appId }}>` → `<AuthProvider projectId>`
- Hosted `useLoginWithRedirect()` → not a direct swap, see Step 1.5 item 3; embedded login routes → `<Descope flowId>` component, wiring `onSuccess`
- `useAuth()` / `useAuthUser()` / `useAuthUserOrNull()` / `useIsAuthenticated()` → `useSession()` + `useUser()`
- `useAuthActions()` (`requestAuthorize`, `switchTenant`, `loadEntitlements`) → Descope SDK actions via `useDescope()`; tenant switching is modeled through Descope tenant context, and `loadEntitlements` has no equivalent
- `useTeamState()` / `useTeamActions().loadUsers()` (tenant-user listing/invites/roles, client-side in Frontegg) → **server-side only**: a route handler using a Management Key, or the User Management Widget — never port this to client code as-is
- `AdminPortal.show()` → Descope Widgets (see Step 3)
- Logout: `sdk.logout()` via `useDescope()`
- **Descope's hooks return a new object identity every render** (Frontegg's store-backed hooks don't). Deriving a value from `useUser()`/`useSession()` inline into a `useEffect` dependency array causes an infinite render loop. Depend on primitives, not the object.
- See `references/implementation-nuances.md` → React for the fuller version of these gotchas, plus the claim-helper null-handling caveat.

#### Next.js

*Frontegg SDK: `@frontegg/nextjs` → Descope `@descope/nextjs-sdk` + `@descope/node-sdk`*

- App Router: `FronteggAppProvider` / `FronteggAppRouter` (`@frontegg/nextjs/app`) → Descope `AuthProvider` (takes `projectId`; must use the `NEXT_PUBLIC_` prefix)
- Pages Router: `withFronteggApp` / `FronteggRouter` / `getSession` / `withSSRSession` (`@frontegg/nextjs/pages`) → Descope `session()` from `@descope/nextjs-sdk/server` for server-side reads
- `getAppUserSession()` / `getAppUserTokens()` → `session()` (server-side only)
- `FronteggApiMiddleware` (`@frontegg/nextjs/middleware`) / `handleSessionOnEdge` (`@frontegg/nextjs/edge`) → Descope `authMiddleware(options)` — **exclude API routes from the matcher.** Descope's documented matcher includes `/(api|trpc)(.*)` by default; an unauthenticated `fetch()` to a matched API route gets a 307 redirect to the sign-in page instead of a 401, breaking client code expecting JSON. Let route handlers validate `session()` and return their own 401.
- `FRONTEGG_ENCRYPTION_PASSWORD` + `FRONTEGG_COOKIE_NAME` (`fe_session` stateless cookie) → removed; Descope manages `DS`/`DSR`
- `FRONTEGG_HOSTED_LOGIN` toggle → decided once, in Console configuration, not per-request
- **Client vs. server session access** — `session()` from `@descope/nextjs-sdk/server` is server-only; `useSession()`/`useUser()` from `@descope/nextjs-sdk/client` are client-only. Using `session()` in a client component compiles but throws at runtime.
- **The middleware gates routes; it doesn't guarantee a session.** It can admit a request on a still-valid refresh token without refreshing it, so `session()` can still come back `undefined` on a page reached through `authMiddleware`. Always null-check `session()` and redirect — don't treat "the middleware let it through" as proof of a valid session.
- Frontegg's Next.js SDK requires SSR and does not support SSG — if the app was structured around that constraint, re-check whether it still applies after migration.
- See `references/implementation-nuances.md` → Next.js for the fuller version of these gotchas.

#### Angular

*Frontegg SDK: `@frontegg/angular` → Descope `@descope/angular-sdk`*

- `FronteggAppModule.forRoot(config)` + `<frontegg-app>` element → Descope Angular module/provider + Flow component
- `FronteggAppService.isLoading$` and `FronteggAuthService` observables (`user$`, `authState$`, `tenantsState$`, `teamState$`) → Descope Angular SDK session/user accessors
- `loginWithRedirect()` / `requestAuthorize()` / `loadTenants()` / `switchTenant({tenantId})` → Descope login flow + tenant context
- Note: Frontegg's Angular SDK has no SSR support; Descope's does not carry the same constraint
- No dedicated recipe yet — follow the React patterns and verify each method against docs

#### Vue

*Frontegg SDK: `@frontegg/vue` → Descope `@descope/vue-sdk`*

- `app.use(Frontegg, { contextOptions, authOptions, hostedLoginBox, router })` → Descope Vue plugin with `projectId`
- `useFrontegg()` (`fronteggLoaded`, `authState`, `loginWithRedirect`), `useFronteggAuthGuard()`, `mapLoginActions()`, `mapAuthState()` → Descope Vue composables for session and user
- `this.fronteggAuth.tenantsActions.switchTenant(...)` → Descope tenant context
- No dedicated recipe yet — follow the React patterns and verify each method against docs

#### Vanilla JS

*Frontegg SDK: `@frontegg/js` → Descope `@descope/web-js-sdk` + `@descope/web-component`*

- `initialize({ contextOptions, authOptions, hostedLoginBox })` → `@descope/web-js-sdk` client created with the Project ID
- `app.ready()` / `app.store.subscribe()` / `app.store.getState().auth` → `getSessionToken()`, `isJwtExpired()`, `refresh()` and the SDK's session events
- `app.loginWithRedirect()` / `app.logout()` / `app.switchTenant(...)` → Descope login (hosted or `<descope-wc project-id flow-id>`), `logout()`, tenant context
- `fe-state="isAuthenticated"` / `fe-mode="hosted"` HTML attributes → conditional rendering driven by the Descope SDK's session state
- `FRONTEGG_AFTER_AUTH_REDIRECT_URL` in localStorage → handle post-login redirect in app code or via Flow configuration

### Backend SDKs

#### Node.js

*Frontegg SDK: `@frontegg/client` → Descope `@descope/node-sdk`*

- Remove `FronteggContext.init({ FRONTEGG_CLIENT_ID, FRONTEGG_API_KEY })`; add the Descope client created with the Project ID (plus Management Key for admin calls)
- Replace `withAuthentication()` middleware (which populates `req.frontegg.user`) with custom middleware calling `descopeClient.validateSession(sessionToken)` against the `DS` cookie (parse the cookie yourself)
- Replace `new IdentityClient({...})` + `identityClient.validateIdentityOnToken(token, { roles, permissions })` with `validateSession()` plus the SDK's role/permission validation helpers
- `AuditsClient` / `EventsClient` → Descope audit events and connectors (see Step 3)
- Access-token cache configuration (`local` / `redis` / `ioredis`) has no equivalent and can be removed

#### Python

*Frontegg SDK: `frontegg` (`frontegg.flask` / `frontegg.fastapi`) → Descope `descope` Python SDK*

- Flask: `frontegg.init_app(client_id, api_key)` + `@with_authentication(role_keys=[...], permission_keys=[...])` (user on `g.user`) → Descope client + a decorator calling `descope_client.validate_session(session_token=session_token)`
- FastAPI: `await frontegg.init_app(...)` + `Depends(FronteggSecurity(permissions=['...']))` → a Descope dependency that validates the `DS` token and checks permissions
- `FRONTEGG_DEBUG` / `frontegg_logger` → the Descope SDK's own logging

#### Go

*Frontegg SDK: `github.com/frontegg/go-sdk` → Descope `github.com/descope/go-sdk`*

- `frontegg.Init(frontegg.Credentials{ClientID, APIKey})` / `frontegg.New(...)` → `client.New()` / `client.NewWithConfig(&client.Config{ProjectID: ...})` configured with the Project ID
- `frontegg.WithAuthentication(middleware.Options{Roles, Permissions})` + `middleware.UserFromContext(ctx)` → custom middleware calling `descopeClient.Auth.ValidateSessionWithToken(ctx, token)`, which returns `(bool, *descope.Token, error)`
- `ident.ValidateToken(ctx, token, &identity.ValidateTokenOptions{...}, identity.JWTHeader | identity.AccessTokenHeader)` → `ValidateSessionWithToken` plus Descope role/permission helpers
- **Semantics gotcha:** Frontegg's `Roles` and `Permissions` options are **OR** (at least one must match). Confirm the equivalent Descope helper's semantics rather than assuming they match
- `client.HostedLogin(redirectURI)` → `RequestAuthorize` / `CodeExchange` (OAuth 2.1 + PKCE) → Descope hosted flow or SDK login
- Frontegg `tenantId` → a Descope **tenant ID**: pass it to management calls; at request time read tenant context off the returned `*descope.Token` (`token.GetTenants()`, or the `dct` claim for the active tenant)

#### Java / Kotlin (JVM)

*Frontegg: entitlements-only packages (`com.frontegg.sdk:entitlements-client*`) → Descope `descope-java`*

- There is no general-purpose Frontegg Java SDK, so JVM apps almost always verify the Frontegg JWT manually (Spring Security resource server, a servlet filter, or `jwt` library calls against the Frontegg public key). Replace that with `authenticationService.validateSessionWithToken(sessionToken)` returning a `Token`
- If `entitlements-client` / `entitlements-client-spring-boot-starter` and `ENTITLEMENTS_ENGINE_TOKEN` are present, the app is using the self-hosted entitlements engine — handle that under Step 3 → *ReBAC* and *Entitlements*, not here
- No dedicated recipe yet — verify against the [Descope Java SDK](https://github.com/descope/descope-java)

#### .NET / C#

*Frontegg: no official SDK → Descope `descope-dotnet`*

- .NET apps configure `AddJwtBearer` with `options.Authority = "https://[frontegg-domain].frontegg.com"`, `options.Audience = "[client-id]"`, `NameClaimType = ClaimTypes.NameIdentifier`, and role checks against the `"roles"` claim type. This is a config-level change, usually the smallest migration of any stack
- Replace with Descope session validation via `descope-dotnet`, or repoint the JWT bearer configuration at Descope's issuer and JWKS if staying with standards-based validation
- Remember that Descope tokens carry no `email`/`name` by default and expose tenants as `dct`/`tenants` rather than `tenantId`/`tenantIds` — the claim reads change even when the validation mechanism doesn't
- No dedicated recipe yet — verify against the [Descope .NET SDK](https://github.com/descope/descope-dotnet)

### Mobile SDKs

All Frontegg mobile SDKs require **hosted** login and default `keepSessionAlive` to `true`. Frontegg
mobile does not support the self-service portal, entitlements, impersonation, or idle-session
management — so mobile migrations are usually narrower than their web counterparts.

> **Naming trap:** `embeddedMode` in `Frontegg.plist` and `EmbeddedAuthActivity` on Android select an
> embedded **webview** for the *hosted* login page. They do **not** indicate an embedded login box.
> A codebase scan that treats them as evidence of embedded login will invert the Step 0 answer for a
> mobile app.

#### iOS (Swift)

*Frontegg SDK: `FronteggSwift` → Descope `descope-swift`*

- `Frontegg.plist` (`baseUrl`, `clientId`, `applicationId`, `embeddedMode`, `regions`) → Descope SDK initialization with the Project ID
- `FronteggApp.shared.auth` / `FronteggAuth.shared` / `@EnvironmentObject var fronteggAuth` / `fronteggAuth.isAuthenticated` → Descope Swift SDK session APIs
- `.login()` / `.loginWithPopup(...)` / `.logout()` / `handleOpenUrl(url)` / `AbstractFronteggController` → run a Descope Flow via the Swift SDK, or use hosted auth
- Associated-domain callback URLs (`{{IOS_BUNDLE_IDENTIFIER}}://{{FRONTEGG_BASE_URL}}/ios/oauth/callback`) must be replaced with the Descope equivalent and re-registered
- No dedicated recipe yet — verify against the [Descope Swift SDK](https://github.com/descope/swift-sdk)

#### Android (Kotlin)

*Frontegg SDK: `com.frontegg.sdk:android` → Descope `descope-kotlin`*

- `buildConfigField`s `FRONTEGG_DOMAIN`, `FRONTEGG_CLIENT_ID`, `FRONTEGG_APPLICATION_ID` and manifest placeholders (`package_name`, `frontegg_domain`, `frontegg_client_id`) → Descope SDK configuration with the Project ID
- `FronteggApp.init(...)` / `FronteggAuth.instance.login/logout/switchTenant` → Descope Kotlin SDK session and flow APIs
- Activities `EmbeddedAuthActivity` / `HostedAuthActivity` / `AuthenticationActivity` and the deep-link path prefixes (`/oauth/account/activate`, `/oauth/account/invitation/accept`, `/oauth/account/reset-password`, `/oauth/account/login/magic-link`) must be replaced with the Descope equivalents
- No dedicated recipe yet — verify against the [Descope Android/Kotlin SDK](https://github.com/descope/descope-kotlin)

#### React Native

*Frontegg SDK: `@frontegg/react-native` → Descope `@descope/react-native-sdk`*

- Frontegg hosted login → run a Descope Flow via the React Native SDK
- Session access/storage → Descope React Native SDK session management
- No dedicated recipe yet — verify against the [Descope React Native SDK](https://github.com/descope/descope-react-native)

#### Flutter

*Frontegg SDK: `frontegg_flutter` → Descope `descope-flutter`*

- `FronteggProvider` / `context.frontegg` / `FronteggState` (`accessToken`, `refreshToken`, `user`, `isAuthenticated`) → Descope Flutter SDK session state
- `login` / `logout` / `refreshToken` / `switchTenant` / `directLoginAction` → Descope Flutter SDK equivalents
- No dedicated recipe yet — verify against the [Descope Flutter SDK](https://github.com/descope/descope-flutter)

**After completing framework code changes:** Update `MIGRATION-STATE.md` — mark each
modified file as Done in the Files Inventory, update Current Phase and Next Action, and
log any non-obvious decisions made.

---

## Step 2.5: Non-Code File Updates

Scan for Frontegg references in non-code files after updating source files.

### `.env.example` / `.env.template` / `.env.sample`

```
# REMOVE
FRONTEGG_CLIENT_ID=
FRONTEGG_API_KEY=
FRONTEGG_BASE_URL=
FRONTEGG_APP_URL=
FRONTEGG_APP_ID=
FRONTEGG_CLIENT_SECRET=
FRONTEGG_COOKIE_NAME=
FRONTEGG_ENCRYPTION_PASSWORD=
FRONTEGG_HOSTED_LOGIN=
FRONTEGG_JWT_PUBLIC_KEY=
FRONTEGG_SHARED_SECRET=
FRONTEGG_COOKIE_DOMAIN=
FRONTEGG_COOKIE_SAME_SITE=
FRONTEGG_SECURE_JWT_ENABLED=
FRONTEGG_REWRITE_COOKIE_BY_APP_ID=
FRONTEGG_FORWARD_IP=
FRONTEGG_SSG_EXPORT=
DISABLE_INITIAL_PROPS_REFRESH_TOKEN=

# ADD
DESCOPE_PROJECT_ID=             # Console → Project Settings
NEXT_PUBLIC_DESCOPE_PROJECT_ID= # Next.js / frontend — same value as above
DESCOPE_MANAGEMENT_KEY=         # Console → Company Settings → Management Keys (replaces FRONTEGG_API_KEY for admin APIs)
```

Run `grep -ir "FRONTEGG"` to find all env var references — `.env.example`, Docker, CI, shell
scripts, Android `build.gradle`, iOS `Frontegg.plist`.

### README / docs

Search all `.md` files for Frontegg references. At minimum, update:

- **Setup section** — replace "create a Frontegg environment" instructions with Descope Console setup steps
- **Environment variables section** — reflect the reduced env var set
- **Run instructions** — replace Frontegg portal steps with Descope Console steps
- **Auth flow diagrams or descriptions** — update to reflect Descope's cookie-based approach

### Docker / CI files

Check `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, and any CI config for `FRONTEGG_`*
env var declarations. **If ReBAC was in use, also remove the entitlements-engine stack** — the
docker-compose services for SpiceDB, CockroachDB, and the `frontegg/e10s-engine-sync` job, any Helm
values referencing `frontegg/entitlements-engine`, and, on older deployments, the legacy
`frontegg/entitlements-agent` PDP container. Descope's ReBAC is managed, so this infrastructure goes
away entirely.

### Terraform / infrastructure-as-code

Frontegg publishes a Terraform provider, so some or all of the configuration being migrated may live
in `.tf` / `.tfvars` rather than the portal. Search for it — IaC-managed Frontegg config is invisible
to a source-code scan, and leaving it in place means the next `terraform apply` recreates what the
migration just retired. Descope has its own Terraform provider if the customer wants to stay
declarative.

### Mobile project files

- iOS: delete `Frontegg.plist`, update associated-domain entitlements and URL schemes
- Android: remove `FRONTEGG_*` `buildConfigField`s and manifest placeholders, remove the Frontegg activities and deep-link intent filters

### Web app manifests

Check `public/manifest.json`-style PWA/web-app manifests for Frontegg references (icons, start URLs,
or scope tied to a Frontegg-hosted domain). These don't break compilation, aren't source files, and
are easy to skip in a code-focused review.

### Setup / bootstrap scripts

When the migration includes a setup or seed script, split it into two parts:

1. **Console setup** (cannot be scripted): Flows, email templates, MFA configuration, branding/Styles, SSO Setup Suite — configure these in the Descope Console. Represent them as a Phase 1 checklist in `MIGRATION-PLAN.md`.
2. **SDK automation** (can be scripted): role creation (`management.role.create()`), tenant creation, access key provisioning, SSO/SCIM config. Preserve these as a Node.js/Python script using the Descope Management SDK.

**After completing non-code file updates:** Update `MIGRATION-STATE.md` — mark env files,
README, CI config, and mobile project files done in the Files Inventory, and advance Next Action.

---

## Step 3: Feature Migration Mapping

For each Frontegg feature confirmed in triage, write a short paragraph: what it accomplishes, the
best Descope approach for that goal, what's different, and what action is required. Reason about
intent, not just the API surface — the best approach may be a Flow, Widget, SSO Setup Suite, Inbound
App, Console configuration, or tenant configuration rather than a direct SDK equivalent.
Only recommend SDK/API code when programmatic control is genuinely required, and verify every method
name against the Descope MCP server before writing it. Include only confirmed features.

### User & Account Data → Descope Migration Tool or JIT Provisioning

This is usually the first thing to settle, because it drives the cutover plan. **Check what exists before planning around it.** Descope's [migration index](https://docs.descope.com/migrate)
and the [descope-migration](https://github.com/descope/descope-migration) tool both cover a fixed set
of providers. A Frontegg-specific guide and tool module may or may not be published at the time you
run this — open both and look. If a Frontegg module exists, prefer it over a hand-written script. If
it does not, use the custom path below; it produces the same result with more work. **Never tell the
user to run a tool or open a guide you have not confirmed exists.**

The three paths below are Descope's standard migration shapes — the same ones documented for
Keycloak, Cognito, and Azure AD B2C — applied to Frontegg. They hold regardless of whether a
Frontegg-specific page exists.

**Path 1 — Full migration (recommended default).** Export accounts, roles, permissions, and users from
Frontegg, then create the matching objects in Descope in dependency order: **tenants → permissions →
roles → users**. Whether a tool does this or you script it, the order matters — users cannot be
created with tenant and role assignments that do not exist yet.

Check `descope-migration` for a Frontegg module first. If one exists, follow its README for the
required environment variables and dry-run procedure rather than assuming a shape. If not, use the
custom-script recipe below.

Passwords do not come along. After import, set a `freshlyMigrated` custom attribute and branch on it
in the Flow to force a reset or onboard the user into a passwordless method. Set `verifiedEmail` /
`verifiedPhone` where Frontegg already marked them verified.

**Path 2 — JIT migration with a Generic HTTP Connector.** The only path that preserves existing
passwords. The Descope Flow collects email and password, a
[Generic HTTP Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http)
calls Frontegg's authenticate-local-user API, and on success the Flow creates or updates the Descope
user, sets their password, and issues a Descope session. Later sign-ins skip Frontegg entirely.

**Path 3 — JIT migration with Frontegg as a custom OIDC provider.** Configure Frontegg as a
[custom OAuth/OIDC provider](https://docs.descope.com/auth-methods/oauth/providers/custom-providers)
in Descope using the Frontegg OIDC client credentials and endpoints, then add an OAuth sign-in step
to the Flow. Users authenticate through Frontegg's hosted login — MFA included — and Descope
provisions them from the returned ID token claims. Add a Flow
[condition](https://docs.descope.com/flows/conditions) that routes already-provisioned users to
Descope-native auth so they stop hitting Frontegg.

Both JIT paths require Frontegg to stay running until the active-user tail has signed in at least
once, and both require **dual token validation** in the backend during the transition (see Step 4).

If a custom script is genuinely required, the shape is: mint an environment token
(`POST https://api.frontegg.com/auth/vendor` with the Client ID and API Key), list accounts via
`GET /resources/tenants/v2`, create the matching Descope tenants, then page users with
`GET /resources/users/v3` (`_limit` max **200**; note `_offset` is a **page index**, not a record
offset — pass 0, 1, 2… and loop until `_metadata.totalPages`, not `_offset += 200`, or the export
truncates silently; add the `frontegg-tenant-id` header for tenant-scoped export). Map `email` → Descope `loginIds`, `name` → `name`, `phoneNumber` → `phone`, `tenantId` →
the Descope tenant, and metadata → custom attributes defined in Descope first. Import with
`POST /v1/mgmt/user/create` or `POST /v1/mgmt/user/create/batch`. See
`references/implementation-nuances.md` → **Migrating user and account data**.

**Effort: Low** with the migration tool on a clean data set; **Medium–High** for JIT paths, which are
Flow engineering plus a dual-validation rollout rather than a one-off script.

### Login Box → Descope Flows + Auth Methods

Frontegg's login box handles sign-in and sign-up, in hosted or embedded mode, across a fixed set of
identifiers (email, username, phone number) and credential types. Descope maps these to **Flows**,
authentication methods, and Console configuration.

| Frontegg | Descope |
| --- | --- |
| Hosted login box (`/oauth/account/login`) | A decision, not a swap — embedded Flow (most common), [Auth Hosting](https://docs.descope.com/identity-federation/auth-hosting) behind a custom domain, or an OIDC-client model. See Step 1.5 item 3. |
| Embedded login box (injected `/account/login`, `/account/sign-up`) | Embedded `<Descope flowId>` / `<descope-wc>` component |
| `customLoginBox` / custom login screens | Custom Flow in the visual builder, or headless SDK |
| Login identifiers: email / username / phone | Descope login identifiers configured per method |
| Password | Descope Passwords |
| Magic link | Descope Magic Link / Enchanted Link |
| Magic code / Email OTP / SMS OTP | Descope OTP methods |
| Passkeys / WebAuthn | Descope Passkeys |
| Device flow | Device-code style Flow — confirm support before promising it |
| Social logins (Google, Microsoft, GitHub, Facebook, Apple, LinkedIn, Slack, custom OAuth) | Descope OAuth/social providers |
| Localizations / theme options | Descope Flow localization and **Styles** |
| Email templates | Descope Messaging Templates |

Two Frontegg-specific notes. First, **Frontegg supplies shared development OAuth credentials** for
every social provider except LinkedIn — so an app with working Google login may never have registered
its own OAuth application. Descope requires real provider credentials, so budget setup time per
provider. Second, Frontegg **auto-merges users across login methods on email**, and if email
verification was disabled, a user who signed up socially and later used a password is forced through
a reset. Check the environment's verification setting before assuming the exported user set is clean.

**Effort: Low–Medium** for straightforward auth; higher with heavy login-box customization.

### Accounts / Tenants → Descope Tenants

Frontegg calls the customer-level object an **Account**, and its docs state that Accounts and Tenants
are the same thing. A user belongs to one or more accounts; the JWT carries `tenantId` (active) and
`tenantIds` (all). Descope models this as **Tenants** and users associated with tenants.

| Frontegg | Descope |
| --- | --- |
| Account / Tenant | Tenant |
| `tenantId` (active account claim) | `dct` claim (Descope Current Tenant) |
| `tenantIds` (membership claim) | `tenants` claim (keyed object with per-tenant roles/permissions) |
| `switchTenant({ tenantId })` | Descope tenant selection / active tenant handling |
| `enableSessionPerTenant` (per-tab tenant) | Tenant context handled per session — confirm the equivalent behavior explicitly |
| Account details (name, address, website, timezone, currency) | Tenant name + tenant custom attributes |
| Account plan assignment | See *Entitlements* below |
| Account-level security policy | Tenant settings + Flow conditions |
| Custom login per account | Tenant-specific Flow / tenant routing |
| Account lock | Tenant-level access control — confirm the equivalent |
| **Sub-accounts (hierarchy)** | **Sub-tenants** — one parent per tenant, nesting supported, with configurable role inheritance |

Sub-accounts map to Descope **sub-tenants**: a tenant can have multiple sub-tenants, those can nest
further, and each sub-tenant has exactly one parent. Role inheritance is configurable (Full, User
only, or None), and sub-tenants can carry their own SSO configuration, custom attributes, and RBAC.
Two constraints to plan around: password settings and session management are **always** inherited
from the parent, and the `tenants` JWT claim is **flat** — it does not encode parentage. Code that
needs hierarchy at request time uses a `tenant.subtenant` JWT-template claim, or a Load/Search Tenant
call returning `parent` and `successors`.

**Effort: Medium** — conceptually clean, but application code often assumes Frontegg's flat
`tenantId`/`tenantIds` claim shape. **Medium–High** with sub-accounts, mostly because role
inheritance and hierarchy-aware token reads need explicit decisions.

### Environments / Workspace → Descope Projects

Frontegg supports up to four environments (Development, Staging, QA, Production) under a workspace,
each fully isolated with its own Client ID, API Key, and Frontegg domain. Each becomes a separate
**Descope Project** with its own Project ID.

One behavioral difference worth calling out: Frontegg lets you **publish** a login box and
self-service portal configuration from one environment to another. Descope projects are configured
independently. For teams that relied on publishing, recommend scripting environment setup with the
Management SDK (roles, tenants, SSO configuration) so that promoting configuration stays repeatable,
and keep Flow changes as a deliberate per-project step.

**Effort: Low** per environment, but multiply the Console setup checklist by the number of
environments.

### Applications (multi-app) → Projects or Federated / Inbound Apps

Frontegg's **Applications** let several apps share one environment, one login box, and one credential
set, distinguished by `appId` in `contextOptions`, `FRONTEGG_APP_ID`, `applicationId` in
`Frontegg.plist`, `FRONTEGG_APPLICATION_ID` on Android, and the `appId` query parameter on
`/oauth/authorize`. The `applicationId` JWT claim identifies which app a session belongs to.

There is no single Descope equivalent — pick based on what the Applications were doing:

| What Frontegg Applications were used for | Descope approach |
| --- | --- |
| Genuinely separate products with separate users | Separate Descope **Projects** |
| One product, multiple surfaces, shared users, single sign-on between them | **Federated Apps** (Descope as IdP across apps you own) |
| Third-party or external clients needing scoped access | **Inbound Apps** |
| Per-application MFA / auto-assign rules | Flow conditions and tenant/user attributes |
| Reading `applicationId` for feature gating | Roles/permissions or a JWT Template claim |

Ask which of these the Applications actually represent before choosing. Note the Frontegg quirk that
the query parameter is `appId`, **not** `app_id` — useful when grepping for usage.

**Effort: Medium** — the decision matters more than the code.

### Self-Service Portal → Descope Widgets + SSO Setup Suite

This is usually the largest single item in a Frontegg migration. Frontegg's self-service portal is a
broad end-customer-facing surface — embedded via `AdminPortal.show()` or hosted at
`/oauth/portal` — covering workflows the customer never wrote. Do not default to rebuilding these
screens as custom code.

| Frontegg portal module | Descope replacement |
| --- | --- |
| Profile settings | User Profile Widget |
| Privacy & Security (password, MFA enrollment) | Flow-driven MFA/password management, or profile widget |
| Personal (user) API tokens | Access Keys, or an Inbound App per client — see *M2M* |
| Account details (name, address, timezone, currency) | Tenant Profile Widget + tenant custom attributes |
| Users: invite, enable/disable, revoke sessions, resend activation | User Management Widget |
| Invite links (invitee inherits inviter's roles) | Invitation Flow — confirm role-inheritance behavior explicitly |
| Guest / temporary users with an access period | No direct equivalent — model with a custom attribute plus expiry logic, or a scheduled deprovisioning job |
| Groups and group roles | Roles + tenant membership; SCIM/SSO group mapping where groups come from an IdP |
| Custom roles created by end customers ("copy permissions from") | Role Management Widget where available; otherwise Management SDK behind your own UI |
| Security policy: MFA, lockout, password history, session settings | Console project/tenant settings + Flow conditions |
| IP and domain restrictions (allowlist/denylist, CIDR) | Flow conditions and Connectors — confirm coverage per restriction type |
| SSO self-serve setup | **SSO Setup Suite** |
| SCIM provisioning setup | SSO Setup Suite SCIM configuration |
| Audit logs (with end-user CSV export) | Audit events + Audit Widget; export via Audit Webhook / connectors |
| Webhooks subscribed by end customers | No direct equivalent — this is an application feature, not an identity one; plan to own it |

Inventory which modules are **enabled in Builder and actually used**, not which exist. Frontegg gates
portal visibility on both a Builder toggle and an `fe.*` permission, so the enabled set is often much
smaller than the full catalog. For each module with no widget equivalent — guest users, end-customer
webhook subscriptions, customer-managed audit export — get an explicit decision: build it, drop it,
or defer it.

**Effort: Medium–High** — it can *remove* code if widgets cover the workflows, or become the biggest
line item if the portal was heavily used.

### RBAC → Descope RBAC

Frontegg roles carry a `Name`, `Description`, `Key` (what lands in the `roles` JWT claim), a numeric
`Level`, a permission list, and assigned accounts. Permissions have a `Key`, a `Category`, and a
**classification type** (`Never` / `Assignable` / `Always`) governing whether end customers may use
them in custom roles. Descope has Roles and Permissions with the same core semantics, at project and
tenant level.

| Frontegg | Descope |
| --- | --- |
| Role key | Role name (referenced by name, not ID) |
| Permission key | Permission |
| Wildcard permissions (`fe.secure.read.*`, `fe.secure.*`) | **No equivalent** — Descope has no wildcard permission matching. Expand each wildcard into explicit permissions |
| Default role (auto-assigned on signup) | Flow-assigned role / tenant default |
| System role (applies to all accounts) | Project-level role |
| Role assigned to specific accounts | Tenant-level role assignment |
| Custom roles created by end customers | Role Management Widget or Management SDK |
| `roles` / `permissions` JWT claims | `roles` / `permissions` claims (nested per tenant under `tenants`) |
| Group roles (computed at login) | SCIM/SSO group-to-role mapping |
| **Role `Level`** (numeric hierarchy limiting who can assign what) | **No equivalent** — enforce in application logic or via permission design |
| **Permission classification type** | **No equivalent** — decide which permissions end customers may self-assign in application/widget logic |
| Built-in `fe.*` permissions | Do not recreate wholesale — they gate the Frontegg portal, which is being replaced |

Two Frontegg behaviors to check for and, ideally, fix during the migration. Frontegg's own docs note
that **role changes do not take effect until the current token expires** — apps often shortened JWT
lifetime to compensate, and that workaround may no longer be needed. And **group roles appear in the
JWT but are not visible from the management section of the Frontegg portal**, so the exported role assignments may not match what
users actually get at login; reconcile against a decoded token, not just the API.

**Effort: Medium** for normal RBAC; higher if role levels or classification types encode real policy.

### ReBAC → Descope ReBAC / FGA

Frontegg's ReBAC is not a hosted service. Entity types, relations, actions, and assignments are
stored in Frontegg Cloud, but evaluation happens in **SpiceDB that the customer self-hosts**, fed by
a sync job (`frontegg/e10s-engine-sync`) that pulls from Frontegg roughly every 60 seconds, typically
alongside CockroachDB, with the app calling `@frontegg/e10s-client` over gRPC. Descope's ReBAC is
managed, so this migration removes infrastructure rather than adding it.

Frontegg does not use a text DSL. The schema is assembled from discrete objects — an **entity type**
(`key`), **relations** (`relationKey`, each declaring a subject entity type), and **actions**
(`actionKey`, mapped to the relations that grant them) — with hierarchy expressed as a JSON
`relationKeys` array mixing direct relations and inherited paths. Schema translation example:

```
# Frontegg ReBAC (assembled via UI / REST)
Entity type: document
  Relations:  reader (subject: user), editor (subject: user), parent (subject: folder)
  Actions:    read  → [ "reader", { "fromRelation": "parent", "toAction": "read_folder" } ]
              write → [ "editor" ]

# Descope ReBAC DSL
model AuthZ 1.0

type folder
  relation viewer: user
  permission read_folder: viewer

type document
  relation reader: user
  relation editor: user
  relation parent: folder
  permission read: reader | parent.read_folder
  permission write: editor
```

**Descope ReBAC schema DSL** — use this syntax to author the Descope ReBAC schema:

```
Syntax                             Description          Example
---------------------------------  -------------------  ----------------------------
model AuthZ 1.0                    Schema header (required)  model AuthZ 1.0
type <name>                        Define a type        type user
relation <name>: <type>            Define a relation    relation owner: user
|                                  Union (OR) operator  user | group
#                                  Relation reference   Group#member
.                                  Traverse relation    parent.owner
permission <name>: <expression>    Define a permission  permission can_edit: owner
```

| Operation | Frontegg | Descope |
| --- | --- | --- |
| Read the schema | `GET /resources/entity-types/v1` | Descope ReBAC schema (Console or Management SDK) |
| Export assignments | `GET /resources/relations/v1/assignments` | — |
| Write relation | `POST /resources/relations/v1/assign` | `descopeClient.management.fga.createRelations([...])` |
| Remove relation | `POST /resources/relations/v1/unassign` | `descopeClient.management.fga.deleteRelations([...])` |
| Check | `e10sClient.isEntitledTo(subject, { type: RequestContextType.Entity, ... })` | `descopeClient.management.fga.check([...])` |
| List accessible resources | `lookupTargetEntities()` / `lookupEntities()` | Descope FGA resource/subject lookup |

(Verify exact Frontegg and Descope shapes against current docs.) Three Frontegg specifics to
confirm before planning: ReBAC must be **enabled by Frontegg support**, so some environments have it
configured but unused — check whether `isEntitledTo` is actually called; relation writes take **up to
60 seconds** to become enforceable, so any application logic that compensates for that lag can be
removed; and time-bound access implemented with SpiceDB's `active_at` caveat has no automatic
equivalent and needs an explicit design decision.

Identify entity types, relations, actions, where checks run, and any hierarchical inheritance.
**Effort: High** — requires a dedicated model review. See
`references/implementation-nuances.md` → **ReBAC migration** for the decision guide and the
assignment-export pattern.

### Entitlements: Features and Plans → Partial Mapping

Frontegg's entitlements engine bundles **Features** (named resources, optionally linked to
permissions) into **Plans** assigned to accounts and users, enforced through `isEntitledTo`,
`useFeatureEntitlements`, and `usePermissionEntitlements`. Descope has no plans product, so this
splits in two.

The **access-control half** maps cleanly: a feature that is really "may this user do X" becomes a
Descope permission, and a plan that is really "which capabilities does this tenant have" becomes a
tenant custom attribute checked in Flows or application code, or a set of tenant-level roles.
Frontegg's `NotEntitledJustification` values map roughly onto these: `MISSING_PERMISSION` is an RBAC
check, `MISSING_FEATURE` and `BUNDLE_EXPIRED` are tenant-entitlement state.

**Where a Frontegg feature effectively assigns permissions directly to a user**, note that Descope
attaches permissions to roles and never directly to users. The workaround is to create a Descope role
containing exactly those permissions and assign that role to the user. Expect a small number of
narrow, generated-looking roles as a result — that is the intended outcome, not a modeling smell.

| Frontegg | Descope |
| --- | --- |
| Feature linked to a permission | Permission |
| Feature gating UI only | Tenant custom attribute or role, read by the app |
| Plan assigned to an account | Tenant custom attribute (e.g. `plan: "enterprise"`) or tenant roles |
| Plan expiration / time-bound plan | Tenant custom attribute with an expiry the app enforces |
| "Grant to all new accounts" | Flow step or tenant-creation default |
| Advanced targeting on `frontegg.*` / custom / `jwt.*` attributes | Flow conditions on user/tenant attributes and JWT claims |

The **commercial half** — plan catalogs, trials, billing tiers — is not an identity concern and
generally should not be recreated in Descope. Ask where it belongs: the billing system, the
application's own database, or a dedicated entitlements vendor.

**Effort: Medium**, and highly variable. Establish scope before estimating.

### Feature Flags → Usually Out of Scope

Frontegg feature flags (up to 500 per environment, one flag per feature, with attribute-based
targeting rules) are release-management tooling that happens to live in the identity dashboard. They
are usually not part of an auth migration. If a flag is genuinely doing access control, map that
specific case to Descope roles, permissions, or tenant attributes; general feature flagging should be
treated as out of scope and moved to a dedicated tool. **Do not present this as an SDK swap** — flag
it separately and ask whether it belongs in the identity migration at all.

### Enterprise SSO → Descope Tenant SSO

Frontegg SSO is configured per account, typically by the customer's own admin through the
self-service portal, with SAML 2.0 and OIDC support and JIT provisioning on first SSO login. Descope
configures SSO per **Tenant** with the same capabilities.

**Preferred approach — SSO Setup Suite:** before migrating any SSO management code, ask whether the
no-code SSO Setup Suite removes the need for it. It guides tenant admins through per-tenant SAML/OIDC
setup with IdP-specific instructions (Okta, Microsoft Entra ID, Google Workspace, etc.). Frontegg
customers are usually already used to self-serve SSO setup, so this maps directly onto an expectation
their end customers already have.

| Frontegg | Descope |
| --- | --- |
| Account SSO configuration | Tenant SSO configuration |
| SAML 2.0 | Descope SAML SSO |
| OIDC | Descope OIDC SSO |
| Customer-admin SSO setup in the portal | SSO Setup Suite |
| SSO JIT provisioning | Tenant JIT provisioning / tenant association |
| SAML/OIDC prehooks for extra IdP attributes | Flow steps / attribute mapping / custom claims |
| SSO group → role mapping | SSO attribute / group-to-role mapping |
| Frontegg as IdP (`native-hosted`, `via-oidc`, `via-saml`) | Federated Apps / Descope as IdP |
| Programmatic SSO management | Descope Management API / SDK |

Existing per-account SSO connections can be moved without making every customer admin reconfigure
their IdP — Descope consumes the existing IdP response and completes authentication, so end users see
no change. Follow [SSO migration](https://docs.descope.com/migrate/sso) for the tenant setup, DNS
redirect, and testing sequence.

If Frontegg was acting as an **IdP** for downstream applications, treat that as a separate workstream
from inbound SSO — it maps to Descope Federated Apps, and every downstream relying party needs its
issuer, metadata, and client credentials updated. Note the Frontegg caveat that OIDC-as-IdP requires a
default application in multi-app setups because `aud` verification depends on it; the equivalent
audience decision has to be made explicitly in Descope.

**Effort: Medium** — higher if Frontegg is an IdP as well as an SP.

### SCIM → Descope SCIM / Tenant Provisioning

Frontegg SCIM supports user and group create/update/deprovision and user↔group membership. **Treat
this as a continuing provisioning pipeline, not a one-time import** — enterprise directories keep
pushing events after cutover.

| Frontegg SCIM | Descope |
| --- | --- |
| SCIM configuration per account | Descope SCIM endpoint / token per tenant |
| User create/update/deactivate | Tenant user provisioning lifecycle |
| Group create/update/delete | External groups / group-to-role mapping |
| Group membership sync | Group-to-role mapping |
| Default role on SCIM creation, then SSO connection role, then SAML group roles | Tenant default role + SSO/SCIM group mapping |
| `managedBy: "frontegg" \| "scim2" \| "external"` | Track provisioning source in the app or a custom attribute |
| SCIM lifecycle webhooks (`frontegg.scim.*`) | Descope events, audit logs, webhooks, or app sync code |

One export-affecting quirk: Frontegg's docs acknowledge that **changing a user's email at the IdP
creates a brand-new Frontegg user** rather than updating the existing one. Long-lived SCIM tenants
therefore accumulate orphaned records. Expect duplicates in the export and plan a reconciliation pass
keyed on `externalId` before importing into Descope.

**Effort: Medium–High** — lifecycle, groups, deprovisioning, and role mapping are all subtle.

### Prehooks → Descope Flow Steps, Conditions, and Connectors

Frontegg prehooks are synchronous, blocking calls made *before* an event completes — either an API
call to the customer's service or custom code running on Frontegg's side. Each returns a verdict
(`allow` / `block` / `challenge` / `lock`), has a **5-second timeout**, and is configured fail-open or
fail-close. There is no single Descope equivalent; each prehook maps to a different Descope mechanism
depending on what it does.

| Frontegg prehook event | Descope approach |
| --- | --- |
| `AUTH_INITIATED` | Flow entry conditions; the `externalRedirectUrl` pattern becomes a Flow branch or redirect action |
| `USER_SIGNUP` | Flow step during sign-up (validation, enrichment, Connector call) |
| `USER_INVITE` | Invitation Flow logic |
| `USER_UPDATE` / `USER_DELETE` | Management SDK hooks in application code, or audit-event-driven sync |
| `CREATE_TENANT` / `UPDATE_TENANT` / `DELETE_TENANT` | Application-side tenant lifecycle via the Management SDK |
| `JWT_GENERATION` (custom claims, `expiresIn`, `mfaFactorUsed` rejection) | **JWT Template** and/or a Flow custom-claims action |
| `SOCIAL_LOGIN_AUTH` / `OIDC_AUTH` / `SAML_AUTH` | Flow conditions on the authentication method, plus attribute mapping |
| `SEND_SMS` | Messaging Connector / custom SMS Connector |
| `SIGN_UP_USER_POOL` | See *User Pools* below |

Three things to pin down for each prehook: whether it **blocks** (a blocking prehook is a security
control, not an enrichment step), whether it is fail-open or fail-close (that determines what happens
when the equivalent Descope Connector times out), and whether it returns a `tenantId` — because a
prehook returning `tenantId` **overrides Frontegg's default tenant resolution**, which is the
documented way to do domain-based tenant assignment. That behavior must be rebuilt deliberately as
Flow logic or tenant self-provisioning domains, not inferred.

**Effort: Medium–High** — flag for dedicated review whenever a prehook blocks, challenges, or locks.

### Security Rules and MFA → Descope Flow Security + MFA

Frontegg ships nine built-in defenses, each with a configurable verdict. Descope has **no single
equivalent toggle**; you reproduce the behavior with fingerprinting, risk signals, Flow conditions,
and security Connectors.

| Frontegg security rule | Descope approach |
| --- | --- |
| Bot detection (allow / challenge / block / lock) | CAPTCHA / bot-detection Connector as a Flow step |
| New device (allow / challenge) | Fingerprinting + Flow condition on device recognition |
| Brute force protection (block / lock) | Lockout policy + Flow conditions |
| Breached password (allow / challenge / block) | Have I Been Pwned–style Connector in the password step |
| Impossible travel (allow / challenge / block) | Risk signals + Flow condition |
| Suspicious IPs (allow / challenge / block / lock) | IP reputation Connector (e.g. AbuseIPDB) + Flow branch |
| Stale users (allow / challenge / block) | Application-side policy or scheduled Management SDK job |
| Email credibility check (allow / block) | Email-validation Connector at sign-up |
| Country restrictions (allow / block) | Flow condition on geo signals |

MFA maps across three axes in Frontegg — policy (required or not), methods, and per-application
enforcement with remember-device. In Descope, MFA lives inside the Flow: add an MFA step, branch on
tenant or user attributes for per-customer policy, and use a subflow for enrollment. Note that
Frontegg lets an **account admin set a stricter policy than the environment** (e.g. environment
"Don't Force" → account "Force"); that per-tenant override needs to become an explicit Flow condition
on a tenant attribute.

Ask whether each rule is monitoring-only or actually gates login. **Effort: Medium–High** only when
verdicts affect production login outcomes.

### Step-up Authentication → Descope Step-up Flows

Frontegg's step-up is standards-based, driven by `acr` (only one supported value:
`http://schemas.openid.net/pape/policies/2007/06/multi-factor`), `amr` (the method used), and
`auth_time` compared against `max_age`. AMR values map as: email OTP → `[mfa, otp]`, SMS →
`[mfa, sms]`, authenticator app → `[mfa, otp]`, WebAuthn → `[mfa, hwk]`.

| Frontegg | Descope |
| --- | --- |
| `acr_values` request for step-up | Step-up Flow / re-authentication Flow |
| `max_age` / `auth_time` freshness check | Flow condition on session age, or a fresh authentication requirement |
| `amr` inspection after step-up | `amr` claim on the Descope session token |
| `unenrolledmfapolicy` (`ALLOW_SKIP` / `FORCE_ENROLL`) | Flow branch for unenrolled users: skip, or enroll inline |
| Embedded re-auth redirect to `/account/re-authenticate?...&acr_values=` | Step-up Flow route in the app |

Frontegg's refresh tokens do not carry `amr`/`acr`, so a step-up always forces re-authentication.
Confirm whether the application depends on that behavior before changing it, and check what the app
does when a user cancels — in Frontegg the JWT comes back with no `acr_values` claim, which
applications sometimes fail to handle.

**Effort: Low–Medium.**

### Sessions and Tokens → Descope Session Management + JWT Templates

Frontegg issues an access token plus a refresh cookie, with token templates and targeting rules
configurable per token type, user, email, application, tenant, or role.

| Frontegg | Descope |
| --- | --- |
| Access token (JWT, RS256 or HS256) | Descope session JWT (`DS` cookie) |
| `fe_refresh` browser cookie | `DSR` refresh cookie |
| `fe_session` (Next.js stateless session cookie) | Managed by the Descope SDK; `FRONTEGG_ENCRYPTION_PASSWORD` goes away |
| `keepSessionAlive` (refresh at ~80% of lifetime) | Descope SDK auto-refresh |
| `disableSilentRefresh` / `/silent` endpoint | Not applicable — Descope handles refresh directly |
| Refresh-token rotation (on by default; `rotateRefreshTokens: false`) | Descope refresh-token handling — confirm rotation behavior |
| Token expiration (environment-level setting) | Descope session/refresh token lifetimes |
| Token templates + targeting rules | JWT Templates |
| `aud` = clientId or appId | Descope has **no `aud` by default** — configure explicitly if needed |
| JWKS / public key from the portal | Descope JWKS endpoint |
| `type`, `sid`, `applicationId` claims | Not present by default — add via JWT Template only if the app reads them |

**Effort: Medium** — token differences ripple through middleware, API routes, and frontend hydration.

### M2M Authentication → Access Keys or Resources + Inbound Apps + Policies

Frontegg's M2M model is two dimensions crossed: **context** (user tokens, which inherit the user's
roles on the active tenant and are deleted with the user; or tenant/account tokens, whose permissions
come from scopes granted at creation) and **type** (client-credentials tokens exchanged for a bearer
JWT and sent in `Authorization`, or access tokens used directly and sent in **`X-API-KEY`**).

That header split is the detail most often missed during migration: a service sending `X-API-KEY`
will not start working just because the token issuer changed.

| Frontegg M2M | Descope |
| --- | --- |
| Tenant (account) client-credentials token | Confidential **Inbound App** + **Policy** granting `client_credentials` access to a **Resource**'s scopes |
| Tenant access token (`X-API-KEY`) | Same as above, plus a client-side change to send `Authorization: Bearer` |
| User client-credentials / personal token | **Access Key** scoped to the user's tenant and roles, or an Inbound App if OAuth scopes are needed |
| Scopes granted at token creation | Resource scopes granted by Policy |
| Token audience | Resource identifier (`aud`) |
| Custom claims on M2M tokens | JWT Template |
| Secret shown once at creation, hashed thereafter | Same model — plan the rotation window |
| Up to 100 concurrent refresh tokens per client | Not applicable |

**Default mapping:** for scoped API access, use **Resources + Inbound Apps + Policies**. Use
**Access Keys** only when the service needs a Descope-issued JWT without OAuth scope or audience
enforcement — a simpler internal service-auth pattern.

Inventory every client, which header it uses, what scopes and audiences downstream services enforce,
and the rotation plan. Note the Frontegg caps while inventorying — access tokens are limited per
tenant and per environment, so a client count near those limits signals a token-sprawl problem worth
fixing during the migration rather than reproducing. **Effort: Medium** — straightforward in design,
careful in rollout.

### Webhooks and Events → Descope Webhooks / Connectors / Audit Events

Frontegg webhooks are configured per environment and signed with an `x-webhook-secret` header
verified as a JWT against the dashboard secret. Event keys are namespaced `frontegg.*` — for example
`frontegg.user.created`, `frontegg.user.authenticated`, `frontegg.tenant.created`,
`frontegg.group.users.added`, `frontegg.scim.user.created`.

| Frontegg | Descope |
| --- | --- |
| Webhook endpoint + `x-webhook-secret` | Descope webhook / HTTP Connector + signature validation |
| `frontegg.user.*` events | Descope user / audit events |
| `frontegg.tenant.*` events | Tenant events or app-side lifecycle sync |
| `frontegg.group.*` events | Group / role mapping events |
| `frontegg.scim.*` events | Descope SCIM provisioning events |
| Custom events (`POST /event/resources/triggers/v3`) | Application-owned events; not an identity concern |
| Static egress IP allowlisting | Confirm Descope's egress behavior with the customer's network team |

Two Frontegg-specific behaviors that change assumptions. Delivery semantics are unusual: **a failed
event is never redelivered** — the retry operates on the webhook, not the delivery, and after five
consecutive failures the webhook auto-disables with backoff up to about a week, then permanently.
Applications built against Frontegg may therefore have compensating reconciliation logic that can be
simplified. And for SCIM events, `eventContext.userId` is the literal constant `"idp_provisioned"`
with the real user under `body.user` — any handler doing that unwrapping needs rewriting, not
repointing.

Identify which handlers are business-critical before cutover. **Effort: Medium.**

### Frontegg Flows → Descope Flows

Frontegg Flows are a no-code visual orchestrator composing webhooks, prehooks, and reusable
sub-flows, with an NLP generator for authoring. Descope Flows are the same idea with a different
execution model: rather than orchestrating external calls around the auth event, the Flow *is* the
auth journey, with steps, conditions, actions, and Connectors inline.

Most Frontegg Flow use cases translate directly — conditional MFA, location-based terms acceptance,
anomaly-triggered step-up, restricting sign-up origin, A/B testing across verification vendors. Map
each Frontegg flow to a Descope Flow branch rather than to code. Where a Frontegg flow called an
external service, that becomes a Descope Connector step.

**Effort: Medium** — usually a re-authoring exercise, not a rewrite.

### User Pools → Flow-Based Federation or Full Migration

Frontegg **user pools** let Frontegg sit in front of an existing user store rather than owning the
data. Two kinds: **external pools** (Auth0, Cognito, Firebase, or custom code, with sync-on-login or
JIT migration) and **IdP federation pools** (the IdP owns the data; no JIT, and no OTC, SSO, or SMS
login). Custom-code pools expose a **Get User** hook (`getUserCodePayload`, fired on SSO/passwordless/
social) and a **Login** hook (`codePayload`, fired on email+password).

This changes what "migrating users" means, so establish the actual state first:

- Which users have already been JIT-migrated into Frontegg (**this is irreversible** in Frontegg) and which still live in the external store?
- If sync is enabled, Frontegg holds a read-only copy — the external store is still the source of truth.
- What is the `tenantId` resolution rule (derived from user properties, fixed value, or auto-create per user)? It applies only to new users, not retroactively, so historical tenant assignment may be inconsistent.

Descope has no drop-in equivalent to user pools. The realistic targets are: migrate everything into
Descope and retire the external store; or keep the external store and use Descope Flow steps with a
Connector to validate against it during a transition period, which reproduces the custom-code Login
hook pattern.

**Effort: High** — flag for dedicated review. The data-ownership question has to be settled before
any code is written.

### Frontegg AI Agents → Descope Agentic Identity Hub + Connections / Outbound Apps

Frontegg AI provides identity for AI agents: agent definition in the dashboard, three built-in tools
added automatically (get user context, get user tenants, get user entitlements), TypeScript and
Python SDKs, and **managed third-party OAuth integrations** (Atlassian, GitHub, Google Workspace,
HubSpot, Monday, Notion, Slack) with per-action scope selection using the customer's own provider
credentials.

| Frontegg AI | Descope |
| --- | --- |
| Agent identity and credentials | Agentic Identity Hub agent identity |
| Agent acting with user context / session | Descope session + delegated access patterns |
| Built-in tools (user context, tenants, entitlements) | Session claims + Management SDK reads |
| Managed third-party OAuth integrations | **Connections** (Agentic Identity Hub's token vault for agent/MCP workloads), or **Outbound Apps** for non-agentic apps |
| Slack "on behalf of user" vs. "app-to-app" | Connection/Outbound App user-scoped vs. tenant/app-scoped token model |
| Per-action scope selection | Connection/Outbound App scope configuration |
| External clients calling your API on an agent's behalf | Resources (the MCP server) + Agentic Clients + Policies |

The strongest mapping here is Descope's third-party token vault — same problem (brokering and
refreshing OAuth tokens for external SaaS APIs), same shape, but Descope has **two** objects that do
this and picking the right one matters: **Connections**, under Agentic Identity Hub, is what Descope
currently steers builders toward for agent and MCP workloads; **Outbound Apps** does the same job but
is positioned for traditional (non-agentic) applications. Ask which kind of app this is before
defaulting to Outbound Apps just because it existed first. The important caveat either way: **stored
third-party refresh tokens do not transfer**. Every user re-consents per integration after cutover,
so plan a re-consent path rather than a silent switch.

**Frontegg does expose MCP in two places**, so ask about both. The Entitlements Agent can be deployed
with an **MCP Server** that exposes authorization tools over HTTP (`is-entitled-to-entity-action-tool`
and `entitlements-entities-tool`), and Frontegg's separate **AgentLink** product (self-hosted
component: **FrontMCP**) ships a hosted or self-hosted MCP gateway for SaaS-facing use cases. If either
is in use, the migration target is Descope's MCP server support — an MCP server is modeled as a
**Resource**, with what the docs call **Agentic Clients** (Console: **Agentic Identity Hub → Clients**
— not Inbound Apps) registering which agents/clients may call it, governed by **Policies** — rather
than Outbound Apps or Connections. This is a different mapping
from the OAuth-brokering case above, and both AgentLink and Frontegg's Entitlements-Agent MCP server
are recent, fast-moving surfaces — verify current naming and capabilities against live docs before
committing to specifics in the plan.

**Effort: Medium–High — flag for dedicated review.**

### High-Complexity Frontegg Areas — Reference Checklist

This list is used **twice**: during Step 0 / Step 0.5 triage, to decide what to flag before the plan
is written, and again here, to sanity-check that nothing high-complexity slipped through the feature
mapping. The main high-complexity Frontegg areas are:

* **User and password export** — no documented outbound hash export; determines the cutover strategy.
* **Self-service portal** — breadth of end-customer workflows; risk of accidental custom rebuild.
* **Prehooks** — synchronous blocking decision points spread across several Descope mechanisms.
* **ReBAC** — self-hosted engine teardown, schema translation, assignment export, 60-second lag logic.
* **Entitlements, plans, and feature flags** — no Descope product; scope decision required.
* **Sub-accounts** — map to Descope sub-tenants, but role inheritance and hierarchy-aware token reads need explicit decisions.
* **SCIM** — lifecycle, group sync, deprovisioning, role mapping, IdP cutover, duplicate records.
* **Enterprise SSO with JIT** — routing, tenant mapping, domain behavior, claim mapping; plus Frontegg-as-IdP if configured.
* **User pools** — data ownership and irreversible partial JIT migration.
* **M2M** — `Authorization` vs. `X-API-KEY`, scopes, audiences, secret rotation.
* **Frontegg AI integrations** — re-consent for every third-party OAuth connection.
* **Multi-app / `applicationId`** — Project vs. Federated App vs. Inbound App decision.
* **Custom domains and issuer URLs** — DNS, cookies, callbacks, token validation impact.

---

## Step 4: Critical Gotchas (Always Cover These)

### JWT Claims Are Not the Same

Frontegg's access token carries a rich default claim set: `sub`, `name`, `email`, `email_verified`,
`metadata`, `roles`, `permissions`, `tenantId`, `tenantIds`, `profilePictureUrl`, `sid`, `type`,
`applicationId`, plus `aud`, `iss`, `iat`, `exp`. Descope session JWTs always carry `sub`, `iss`,
`iat`, `exp`, `drn`, and `amr`. The rest are conditional, each for a different reason:

- `tenants` — present when the user has tenant associations **and** the JWT template uses the default authorization format. Other template formats put roles and permissions at the token root instead.
- `dct` — auto-set when the user belongs to exactly one tenant, or after tenant selection in a Flow. It is **not** gated on the template format.
- `roles` / `permissions` — can be **project-level**, in which case they appear with no tenant association at all.

Descope tokens carry **no `email`, `name`, or `picture`**, so any code reading profile fields off the
token breaks after migration.

The tenant claims also change shape. Frontegg uses a flat `tenantId` (active) plus a `tenantIds`
array (membership). Descope uses `dct` (Descope Current Tenant — a flat string, the direct equivalent
of `tenantId`) and `tenants`, a keyed object (`{ [tenantId]: { roles, permissions } }`) holding
per-tenant roles and permissions. Prefer the SDK's helpers (e.g.
`validateTenantRoles(authInfo, tenantId, [...])`) over reading claims by hand; reach for `dct` when
you only need the active tenant ID.

**Action required:** Configure a JWT Template in the Descope Console to add `email`, `name`, and any
other fields the app reads — including anything a `JWT_GENERATION` prehook used to inject.

### Frontegg's Two Cookies Become `DS` and `DSR`

Frontegg stores its refresh token in the **`fe_refresh`** cookie, and the Next.js SDK adds a stateless
session cookie named by `FRONTEGG_COOKIE_NAME` (default **`fe_session`**), encrypted with
`FRONTEGG_ENCRYPTION_PASSWORD`. Descope collapses this into a signed session JWT in the **`DS`**
cookie with refresh in **`DSR`**, managed by the SDK. All three Frontegg environment variables go
away. Any code reading, writing, or clearing `fe_refresh` / `fe_session` must be replaced.

### Silent Refresh and Third-Party Cookies

Frontegg refreshes at roughly 80% of JWT lifetime via `/user/token/refresh` (embedded) or
`/oauth/token` (hosted). Many Frontegg deployments added a **custom domain specifically to avoid
third-party-cookie 401s on that refresh call**. If the app has a Frontegg custom domain, find out
whether it exists for branding or for cookie reasons — the answer determines whether a Descope custom
domain is a nice-to-have or a launch blocker.

### Logout Is Two Steps

1. Call `descopeClient.logout(refreshToken)` to invalidate server-side
2. Clear the `DS` and `DSR` cookies

Skipping either step leaves a broken state. Note that Frontegg's hosted logout was a **navigation**
to `{baseUrl}/oauth/logout?post_logout_redirect_uri=…`, not a method call — so hosted-login apps
often have no logout code at all, just a link. That link must be replaced with real logout handling.

### Audience Validation Is Opt-In

Frontegg tokens carry an `aud` claim (the client ID or app ID) by default, and backends — especially
.NET apps using `AddJwtBearer` with `options.Audience` — often validate it. Descope session tokens
have **no `aud` claim by default**. Apps relying on audience validation must (1) configure a custom
`aud` claim in a JWT Template and (2) pass `audience` to `validateSession()` on the backend.
Otherwise validation either fails or silently stops checking something it used to check.

### Plan Dual Token Validation for Any Phased Cutover

Unless the cutover is a hard big-bang switch, there will be a window where some users hold Descope
session JWTs and others still hold Frontegg tokens. The backend must validate **both** during that
window: inspect the token's issuer or `kid` to determine which provider issued it, then validate
accordingly. This is mandatory for either JIT migration path and strongly advisable for a phased full
migration. See [Descope session migration](https://docs.descope.com/migrate/session-migration) —
note this specific doc is currently in **beta**, documented only for Auth0, Okta, or a custom-built
solution, and assumes the user already exists in Descope (it is not a JIT mechanism); confirm it still
applies before leaning on it, and fall back to hand-rolled dual validation (issuer/`kid` inspection) if
it doesn't cover a Frontegg-specific case. Plan the removal of the Frontegg branch as an explicit
follow-up task — dual validation left in place becomes a permanent second attack surface.

### Hardcoded Public Keys Fail Silently

Frontegg's Next.js SDK supports inlining a single JWK as `FRONTEGG_JWT_PUBLIC_KEY`, and some backends
paste the public key from the portal rather than fetching JWKS. Grep for that pattern specifically:
it does not produce an import error after migration, it produces valid-looking code that rejects
every Descope token. Replace with the Descope SDK's validation or Descope's JWKS endpoint.

### Account Handling: Tenant IDs, Not Token Parsing

Most code referencing a Frontegg `tenantId` is management code — it becomes a Descope **tenant ID**
passed to `management.tenant.*` / `management.user.*` calls. Only request-time code that read the
account off the session changes shape: Descope exposes the active tenant as `dct` and membership as
the nested `tenants` object. Grep for all `tenantId` / `tenantIds` reads and sort them into these two
buckets — by-ID management calls vs. session reads — before updating.

**On the web client, don't reach for the claim-reading helpers without checking their null-handling
first.** `@descope/web-js-sdk`'s `getTenants()`, `getJwtRoles()`, and `getCurrentTenant()` read the
`tenants` claim without guarding against it being absent — a user who belongs to no tenant yet (the
normal state right after signup) has no `tenants` claim at all, and `getTenants()` throws
(`Cannot convert undefined or null to object`) instead of returning `[]`. A tenant-less user is a
valid, renderable state, not an error state — the migrated app needs to handle it. This was verified
in the browser client SDK specifically; if a backend SDK's equivalent helper is in play, check its
null-handling too rather than assuming the same behavior. Prefer `useUser().userTenants` for display
purposes (it's fetched fresh from the API — see the claim-freshness gotcha below) or guard the claim
read defensively (`Object.keys(claims?.tenants ?? {})`).

### Claim Freshness: Both Providers Stamp Authorization Claims at Issue Time

Frontegg's own docs note that role changes only apply once the current token expires, and recommend
shortening JWT lifetime to compensate. **Descope behaves the same way, for the same reason** — a
user's `tenants`, `roles`, `permissions`, and `dct` claims are set when the token is issued and do not
update themselves. Someone added to a tenant, or granted a new role, after their last sign-in holds a
token with the old claim set (or none at all) until they get a new one. This is easy to miss because
it's invisible in normal production use — JIT provisioning assigns the tenant *before* the first token
is ever issued — but very visible during migration testing, where tenants and roles get assigned by
hand in the Console against users who are already signed in from an earlier step. Symptoms show up as
several seemingly unrelated bugs ("no tenant" here, "no active tenant" there) before the shared cause
is obvious.

Apps migrating off Frontegg often already carry workarounds for this on the Frontegg side — forced
refreshes after role assignment, artificially short token lifetimes, client-side role caches. Identify
them and decide deliberately whether to keep them; don't assume Descope makes them unnecessary.

Two consequences for code, on the Descope side:
- **For display, prefer the live user object over token claims.** `useUser()` (or the equivalent
  SDK call) returns tenant/role data fetched from the API, so Console changes show up on reload;
  reading the same data out of the JWT gives you whatever was true at issue time.
- **For authorization, repair the token rather than working around it in the UI.** If a user has
  tenant memberships but the current token has no `dct`, call `selectTenant()` (client SDK) to
  re-issue the token with the claim populated. Falling back to "just use the first tenant" in the UI
  leaves the backend still seeing no active tenant, since the token itself never changed.

### A `widgetId` With No Widget Behind It Fails as an Authorization Error

Every Widget referenced in code (e.g. `<TenantProfile widgetId="...">`) must correspond to a widget
actually provisioned in the Console for that project — referencing an ID that isn't provisioned fails
at runtime with **"Unauthorized user: Operation not allowed for management request,"** which reads
like an RBAC problem and sends you chasing role and permission assignments that are actually fine.
**If a widget call fails with that specific error, check whether the widget exists before touching
permissions.** The SDK exports and types every widget component regardless of whether the backing
widget is provisioned in a given project, so TypeScript gives false confidence — a type existing is
not evidence the widget is live. Not all widgets ship provisioned by default; verify what's actually
in Console → Widgets for the project in hand rather than assuming the full catalog is present.

### No Drop-In Middleware

Outside Next.js — which ships `authMiddleware` in `@descope/nextjs-sdk/server` — Descope has no
drop-in auth-middleware package. Frontegg's `withAuthentication()`, `FronteggSecurity(...)`,
`frontegg.WithAuthentication(...)`, and `@with_authentication(...)` all
become roughly 20 lines of custom code that reads the `DS` cookie and calls `validateSession()`. Also
note the semantics: Frontegg's Go middleware treats `Roles` and `Permissions` as **OR** (at least one
must match). Do not assume the Descope helper you pick has the same semantics — verify it.

### `cookies()` and `headers()` Are Async in Next.js 15

`cookies()` and `headers()` from `next/headers` return a `Promise` in Next.js 15+. Before
generating any server-side helper that reads cookies:

1. Check the project's `package.json` for the Next.js version.
2. If ≥ 15: write `await cookies()` and mark the containing function `async`.
3. Trace upward — making a cookie-reading helper async cascades to every caller.

### Async Cascade: Trace All Callers Before Finishing

In TypeScript, marking a shared session helper `async` silently breaks every caller that omits
`await`. Grep for all call sites in the same pass; the cascade routinely spans 10–20 files.

### Approved Domains Are Domain-Only

Frontegg registers full callback URLs (`http://localhost:3000/oauth/callback`) and allowed origins
with wildcard support (`https://*.acme.com`). Descope uses **Approved Domains** (Console → Project
Settings → Security) — domain only, no protocol, no path. For local dev: `localhost:3000`, **not**
`http://localhost:3000/oauth/callback`. Confirm explicitly how any wildcard origin should be
represented rather than copying it across.

### SCIM Is a Lifecycle, Not a One-Time Import

If SCIM is in use, re-point every SCIM connection at Descope before cutover. Also expect duplicate
user records in the export: Frontegg creates a new user when an IdP changes a user's email, so
long-lived SCIM tenants accumulate orphans. Reconcile on `externalId` before importing.

### Management Calls Go to `api.frontegg.com`, Not the Subdomain

During export work, management API calls must hit the regional gateway (`api.frontegg.com` for EU,
or `api.us` / `api.au` / `api.ca`), while tenant-context calls go to the environment subdomain or
custom domain. Getting this wrong produces `{"errors":["Failed to verify vendor JWT"]}`, which
Frontegg's troubleshooting docs attribute to misusing API contexts or directing requests to the wrong
gateway — it reads like a credential problem but is not. With an environment token on a self-service
route, add the `frontegg-user-id` and/or `frontegg-tenant-id` headers.

### `X-API-KEY` vs. `Authorization` for M2M

Frontegg client-credentials tokens go in `Authorization`; Frontegg access tokens go in **`X-API-KEY`**.
Any service using the latter needs a client-side change, not just a new credential. Inventory both
before cutover.

### Passkey and TOTP Enrollments Do Not Transfer

Frontegg's inbound migration supports carrying an authenticator secret *into* Frontegg — as an
`authenticatorAppMfaSecret` field on the migration API, or via the `SIGN_UP_USER_POOL` prehook, in
both cases Base32 — but there is no outbound equivalent, and passkeys are bound to the relying party
in any case. Users re-enroll their second factor after cutover. Communicate this before
the cutover date, not after.

### Frontegg's Social Login May Be Using Shared Dev Credentials

Frontegg provides shared development OAuth credentials for every social provider except LinkedIn. An
app whose Google login "just worked" may have no OAuth application of its own. Creating real
credentials with each provider — including verification and consent-screen review where required —
can take longer than the code change it accompanies.

---

## Step 5: Automated Testing

Run the app and verify it works — don't just hand over a checklist.

### Phase 0: Final stale-import sweep (BLOCKING)

```bash
grep -rni "frontegg" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
  --include="*.cs" --include="*.swift" --include="*.dart" --include="*.gradle" \
  --include="*.plist" --include="*.xml" --include="*.env*" --include="*.yml" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=Pods \
  .
```

**Triage the hits — don't treat every match as a failure.** Imports, package names, env vars, config
files, CI workflows, and manifests referencing Frontegg must be zero. Comments and migration
documentation that explain what a construct *used to be* (`// Replaces Frontegg's
handleSessionOnEdge`) are expected and should stay — they're valuable, not stale. Pay particular
attention to non-source files — `.env*`, CI workflows, `build.gradle`, `Frontegg.plist`, and web-app
manifests (`public/manifest.json`-style files) — since none of these break compilation and are the
most commonly missed. A real migration commonly turns up a handful of hits that are all deliberate
comments alongside one or two real stragglers (an auto-update CI job pointed at Frontegg, a stale
manifest entry); read each hit rather than gating on the raw count.

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

- `Cannot find module '@frontegg/...'` → stale import; re-run Phase 0
- `Property 'tenantId' does not exist on type '...'` → wrapper built against Frontegg's flat user shape; re-derive from the Descope `authInfo` shape (`dct` / `tenants`)
- `'await' expression is not allowed in synchronous contexts` → async cascade gap
- `Object is possibly 'undefined'` on session fields → add null check or early return

```bash
npm run dev   # or: python main.py / go run . / flask run / etc.
```

### Phase 2: Run existing tests

```bash
npm test   # or: pytest / go test ./... / etc.
```

Auth-related test failures usually mean: a mock or fixture still uses Frontegg's token shape; a test
asserts on claims that are now missing (`email` without a JWT Template, or `tenantId` where the code
now reads `dct`); or a test still stubs `withAuthentication` / `FronteggSecurity`.

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

# No Frontegg endpoints are still being called
curl -s http://localhost:<port>/ | grep -i "frontegg.com" && echo "STALE FRONTEGG REFERENCE"
```

### Phase 4: Verify JWT claims (if JWT Template is configured)

```bash
echo "<DS_cookie_value>" | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

Check that `email`, `name`, and any other expected claims are present, and that `dct` / `tenants`
hold the tenant context the app used to read from `tenantId` / `tenantIds`.

### Phase 5: Report results

```
## Test Results

**Server startup:** ✅ Started successfully on port 3000
**Existing tests:** ✅ 12 passed / ❌ 2 failed (list failures)
**Unauthenticated /dashboard:** ✅ 302 → /login
**Unauthenticated /api/protected:** ✅ 401
**Login page loads Descope component:** ✅
**JWT claims (email, name, dct):** ✅ Present / ❌ Missing — JWT Template not yet configured
**No residual Frontegg references:** ✅

**Blockers before going live:**
- [ ] (list anything that failed or needs manual action)
```

**Do not proceed to Step 6 until ALL of the following are true:**

- Phase 0 grep returns zero Frontegg references
- Phase 1 compilation passes with zero errors
- Phase 1 server starts and stays running
- Phase 3 root path returns 2xx or 3xx (not 5xx)
- Phase 3 protected routes return 302 or 401 (not 500)

---

## Step 6: Post-Migration Summary (Required)

Every migration produces a `MIGRATION-SUMMARY.md` covering what was done, manual setup
remaining, and behavioral differences that matter before production.

### MIGRATION-SUMMARY.md

1. **What was migrated** — a table mapping each Frontegg concept to its Descope replacement
2. **Behavioral differences and open questions** — numbered list of significant differences between
   the Frontegg and Descope implementations. For each item: Frontegg behavior, Descope behavior,
   action required. At minimum cover claim shape, cookies, logout, audience validation, role-change
   propagation, sub-tenant role inheritance, and anything with no equivalent (role levels, permission
   classification types, plans, feature flags).
3. **Pre-deploy checklist** — actionable checkbox items for everything that must happen before the
   migrated app can run. Prominently include all Console setup tasks (project, Flow, JWT Template,
   Approved Domains, tenants, roles, SSO/SCIM, social provider credentials), the SCIM re-point, the
   password-reset or passwordless onboarding campaign, and — if ReBAC was in use — decommissioning
   the self-hosted entitlements engine. These are the things easiest to forget because the code
   compiles without them.

---

## Step 7: Output Format

Write a numbered migration guide in Markdown, scoped to the user's stack. Use code
snippets and direct doc links. Always include the MIGRATION-SUMMARY.md deliverable (Step 6).

For complex migrations, flag the high-effort items explicitly with estimated complexity
(Low/Medium/High) so the user can plan.

---

## Reference Files

- `references/implementation-nuances.md` — Verified migration patterns, code-level diffs, Frontegg export patterns, and edge cases.
- `references/flows-and-widgets.md` — Descope terminology, Flows, Widgets, SSO Setup Suite, and the Console-vs-code decision guide.
- Descope Docs: [https://docs.descope.com](https://docs.descope.com)
- **Migration index (check for a Frontegg page): [https://docs.descope.com/migrate](https://docs.descope.com/migrate)**
- **Descope migration tool (check for a Frontegg module): [https://github.com/descope/descope-migration](https://github.com/descope/descope-migration)**
- Comparable JIT-migration patterns, documented for other providers: [Keycloak](https://docs.descope.com/migrate/keycloak), [Cognito](https://docs.descope.com/migrate/cognito), [Azure AD B2C](https://docs.descope.com/migrate/azure-ad-b2c)
- Migration Guide: [https://docs.descope.com/migrate](https://docs.descope.com/migrate)
- User Import (Custom): [https://docs.descope.com/migrate/custom](https://docs.descope.com/migrate/custom)
- User format JSON: [https://docs.descope.com/migrate/custom/user-format-json](https://docs.descope.com/migrate/custom/user-format-json)
- Session migration / dual token validation: [https://docs.descope.com/migrate/session-migration](https://docs.descope.com/migrate/session-migration)
- SSO migration: [https://docs.descope.com/migrate/sso](https://docs.descope.com/migrate/sso)
- Generic HTTP Connector: [https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http](https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http)
- Custom OAuth/OIDC providers: [https://docs.descope.com/auth-methods/oauth/providers/custom-providers](https://docs.descope.com/auth-methods/oauth/providers/custom-providers)
- Descope OIDC Endpoints: [https://docs.descope.com/getting-started/oidc-endpoints](https://docs.descope.com/getting-started/oidc-endpoints)
- Descope Flows: [https://docs.descope.com/flows](https://docs.descope.com/flows)
- JWT Templates: [https://docs.descope.com/management/token/jwt-templates](https://docs.descope.com/management/token/jwt-templates)
- Resources: [https://docs.descope.com/resources](https://docs.descope.com/resources)
- Policies: [https://docs.descope.com/policies](https://docs.descope.com/policies)
- Inbound Apps: [https://docs.descope.com/identity-federation/inbound-apps](https://docs.descope.com/identity-federation/inbound-apps)
- Outbound Apps: [https://docs.descope.com/identity-federation/outbound-apps](https://docs.descope.com/identity-federation/outbound-apps)
- Access Keys (M2M — simple cases only): [https://docs.descope.com/management/m2m-access-keys](https://docs.descope.com/management/m2m-access-keys)
- Messaging Templates: [https://docs.descope.com/management/messaging-templates](https://docs.descope.com/management/messaging-templates)
- Audit Webhook: [https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook)
- Custom Domains: [https://docs.descope.com/how-to-deploy-to-production/custom-domain](https://docs.descope.com/how-to-deploy-to-production/custom-domain)
- ReBAC: [https://docs.descope.com/authorization/rebac](https://docs.descope.com/authorization/rebac)

### Session Validation by Language

- Node.js: [https://docs.descope.com/getting-started/nodejs#implement-session-validation](https://docs.descope.com/getting-started/nodejs#implement-session-validation)
- Python: [https://docs.descope.com/getting-started/python#implement-session-validation](https://docs.descope.com/getting-started/python#implement-session-validation)
- Go: [https://docs.descope.com/getting-started/go#implement-session-validation](https://docs.descope.com/getting-started/go#implement-session-validation)
- Ruby: [https://docs.descope.com/getting-started/ruby#implement-session-validation](https://docs.descope.com/getting-started/ruby#implement-session-validation)
- Java / Kotlin: [https://docs.descope.com/getting-started/java#implement-session-validation](https://docs.descope.com/getting-started/java#implement-session-validation)
- .NET / C#: [https://docs.descope.com/getting-started/dotnet#implement-session-validation](https://docs.descope.com/getting-started/dotnet#implement-session-validation)
- Next.js: [https://docs.descope.com/getting-started/nextjs](https://docs.descope.com/getting-started/nextjs)
- React: [https://docs.descope.com/getting-started/react](https://docs.descope.com/getting-started/react)
- Angular: [https://docs.descope.com/getting-started/angular](https://docs.descope.com/getting-started/angular)
- Vue: [https://docs.descope.com/getting-started/vue.js](https://docs.descope.com/getting-started/vue.js)
- Swift / iOS: [https://docs.descope.com/getting-started/swift](https://docs.descope.com/getting-started/swift)
- Kotlin / Android: [https://docs.descope.com/getting-started/kotlin](https://docs.descope.com/getting-started/kotlin)
- Flutter: [https://docs.descope.com/getting-started/flutter](https://docs.descope.com/getting-started/flutter)
- Sub-tenants: [https://docs.descope.com/management/tenant-management/sub-tenants](https://docs.descope.com/management/tenant-management/sub-tenants)
- ReBAC schema DSL: [https://docs.descope.com/authorization/rebac/define-schema](https://docs.descope.com/authorization/rebac/define-schema)

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
- React Native SDK: [https://github.com/descope/descope-react-native](https://github.com/descope/descope-react-native)
- JS/TS monorepo (React, Angular, Vue, Next.js, Web Component, Web JS): [https://github.com/descope/descope-js](https://github.com/descope/descope-js)



