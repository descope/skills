---
name: fusionauth-to-descope
description: >
  Use this skill whenever anyone asks about migrating from FusionAuth to Descope — whether they're
  a developer doing it themselves or a technical lead evaluating the move. Triggers on: "how do I
  migrate from FusionAuth", "replace FusionAuth with Descope", "we're moving off FusionAuth",
  "FusionAuth to Descope", "switch from FusionAuth", "our app uses @fusionauth/react-sdk /
  @fusionauth/typescript-client / next-auth with the FusionAuth provider / a self-hosted FusionAuth
  instance / FusionAuth Cloud and we want to use Descope instead", or any question about FusionAuth
  features (tenants, applications, registrations, application roles, groups, hosted login pages and
  themes, lambdas, webhooks, identity providers, connectors, entity management, MFA, passkeys, SCIM,
  Kickstart, password hash export) in the context of Descope. Works for any language or framework
  with a Descope SDK. Always use this skill before producing migration guidance — do not rely on
  memory alone.
---

# FusionAuth → Descope Migration Skill

This skill guides self-service migrations from FusionAuth to Descope, in order:

1. **Part 1 — MCP Check** and **Part 1.5 — Scope Guard** (confirm the app actually uses FusionAuth)
2. **Part 2 — Migration Plan** — gather context via triage questions, analyze the codebase's auth touchpoints, and produce a human-readable `MIGRATION-PLAN.md` for the user to review
3. **Part 3 — Execution** — only after the user approves the plan

Do not collapse these parts or skip ahead. The plan must be reviewed before code changes begin. If the file view is truncated, partial, or cut off, continue reading with the appropriate offset until all lines have been loaded; do not proceed based on a partial read.

FusionAuth is an OAuth 2.0 / OIDC identity server that teams either **run themselves** (Docker,
Kubernetes, a VM — backed by PostgreSQL or MySQL and an optional Elasticsearch/OpenSearch) or rent as
**FusionAuth Cloud**. Its model is built from **tenants** (hard isolation boundaries with their own
user pool, keys, and policies), **applications** (OAuth clients that define their own roles),
**registrations** (which user may use which application, with which roles), and **groups** (bundles
of application roles). Around that sit hosted login pages styled with FreeMarker **themes**,
JavaScript **lambdas** that run at fixed points, **webhooks**, **identity providers** for social and
enterprise SSO, **connectors** for pulling users in from a legacy store, **entity management** for
machine-to-machine access, MFA, passkeys, and SCIM.

Two things make FusionAuth migrations different from most others, and the plan should lead with both:

- **Password hashes can come along.** FusionAuth's API never returns hashes, but self-hosted teams own
  the database, and FusionAuth Cloud customers can get a database export through a support ticket. The
  default scheme (`salted-pbkdf2-hmac-sha256`) imports into Descope directly, so most users keep their
  passwords and nobody notices the switch.
- **Many apps have no FusionAuth SDK at all.** FusionAuth is OIDC-first, so the app may integrate
  through `next-auth`, `openid-client`, Spring Security, ASP.NET `AddOpenIdConnect`, or AppAuth. Those
  apps can often keep their OIDC library and just point it at Descope.

**Primary references** (all in this skill's directory):

- `references/implementation-nuances.md` — verified migration patterns for each framework, FusionAuth feature-to-Descope mappings, the export and password-hash recipe, and known gotchas
- `references/flows-and-widgets.md` — Descope terminology/lingo, Flow structure and templates, Widgets, SSO Setup Suite, Console-vs-code decision guide
- `references/fusionauth-detection-patterns.md` — codebase search commands for every FusionAuth SDK, generic-OIDC integration, self-hosted infrastructure, lambda, and webhook surface, plus common env vars

---

## Guiding Principles

**Console-first.** Before recommending SDK code for any user-facing auth feature, check whether the Console, a Flow, a Widget, or the SSO Setup Suite covers the use case. Engineers integrate once (SDK setup + session validation). All subsequent auth evolution — new methods, MFA changes, UI updates, tenant SSO onboarding — should happen in the Console without code deployments. See `references/flows-and-widgets.md` → Console vs. Code.

In a FusionAuth migration this applies to three things the team may think of as code: **FreeMarker
themes** (become a Flow plus Styles), **lambdas** (mostly become JWT Templates, Flow steps, or
Connectors), and **app-built admin screens** written against the FusionAuth API because FusionAuth has
no end-customer admin portal by default (often become Widgets or the SSO Setup Suite).

**Match first, then enhance.** Rebuild what FusionAuth does today 1:1 — same sign-in methods, same
login model, same tenants and roles — so every test has one question: does the app behave the same
as before? Passkeys, adaptive MFA, or a redesigned login are post-cutover improvements: list them in
`MIGRATION-SUMMARY.md`, don't build them into the migration.

**Ask, don't assume.** At every design decision — what a FusionAuth tenant becomes, what an
Application becomes, how registrations and groups flatten into roles, password strategy, keep the OIDC
library vs. adopt the Descope SDK, Widget vs. custom page — use `AskUserQuestion` rather than
proceeding with an assumption. A wrong assumption compounds across 20+ files.

**MCP over memory.** When a Descope MCP is connected (confirmed in Part 1), use
`docs_ask_question` (Descope MCP Server) or `ask-question-about-descope` (Docs MCP) to verify every
SDK method name, option shape, and return type before writing it. Do not write a method name and add
a hedge like "verify the exact name" — verify it.

**Verify FusionAuth usage before you map it.** FusionAuth apps integrate in at least four ways — the
React/Vue/Angular SDKs (with a Hosted Backend or DPoP), a generic OIDC library, the
`FusionAuthClient` Management API client, and direct calls to `/api/login` — and many use more than
one. Confirm what the app actually does before mapping anything.

**Settle the tenant question first.** A FusionAuth tenant can be an environment, a B2B customer, or a
separate product. Each becomes something different in Descope (a Project or a Tenant), and that choice
shapes the user import, roles, SSO, and every claim read. Decide it in triage.

**FusionAuth configuration often lives outside the repo.** Tenants, applications, roles, lambdas,
themes, identity providers, and webhooks are configured in the FusionAuth admin UI, through
Kickstart, or with the FusionAuth Terraform provider. Ask for them, export them, or read
`kickstart.json`, rather than inferring the auth experience from code alone.

---

## DO NOT

- **Do not assume passwords are lost.** Check where FusionAuth runs and which hash schemes the users
  carry first. Most users can keep their password (see Step 0.5 → password strategy).
- **Do not assume every hash imports.** `salted-hmac-sha256`, `salted-md5`, and iterated
  `salted-sha256` have no documented Descope equivalent. Count users per scheme before committing to
  a plan, and give those users a JIT or reset path.
- **Do not merge same-email users from different FusionAuth tenants silently.** They are separate
  users with separate passwords in FusionAuth and become one Descope user if the tenants become
  Descope tenants. Get an explicit rule.
- **Do not port app-built admin screens as-is.** Code that lists, invites, or assigns roles through a
  FusionAuth API key becomes a server endpoint with a Descope Management Key, or a Widget. A Descope
  Management Key never ships to a client.
- **Do not trust an unverified token in dual validation.** Route on `iss`/`kid` only to pick the
  verifier; each branch verifies the signature against that provider's keys.
- **Do not carry over HMAC secrets or hardcoded FusionAuth public keys** — they reject every Descope
  token without an obvious error.
- **Do not expose `DESCOPE_MANAGEMENT_KEY` or Inbound App client secrets client-side.**
- **Do not import users into production before dev/staging imports and sign-in tests pass**, including
  a real password sign-in for at least one user of each hash scheme.
- **Do not treat a database export as ordinary data.** It holds password hashes and MFA secrets. Keep
  it off shared drives and out of the repo, and delete it when the migration is done.

---

## Part 1: MCP Check (BLOCKING)

First run Part 1.5's quick grep (no questions). If it already says stop, stop there without
asking about the MCP. Otherwise check which Descope MCP is connected:
- **Descope MCP Server** — call `docs_search` with a simple query (e.g., "session validation").
  It searches the docs and can also read and change the Descope project.
- **Descope Docs MCP** (docs only) — call `search-descope-docs`.

**If the Descope MCP Server is connected:** proceed to Part 1.5.

**If it isn't**, show this message and use `AskUserQuestion`:

> **Connect the Descope MCP Server.** This skill uses it to check current SDK methods and
> features, and it can read your Descope project and make management changes to it with your
> approval. Without it, guidance may be stale. Server URL `https://mcp.descope.com` (other
> regions and client setup: https://docs.descope.com/mcp/mcp-server).
>
> For docs lookups only, you can connect the Descope Docs MCP instead:
> `https://docs-mcp.descope.com/mcp`.
>
> **Connect it before we continue, or proceed without it?**

- Connect: pause and wait. Once they confirm, re-check by calling `docs_search`, then
  `search-descope-docs` if that fails. If only the Docs MCP responds, continue as "Proceed with
  only the Docs MCP" below.
- Proceed with only the Docs MCP: use it for doc lookups; the Console setup stays manual.
- Proceed with neither: flag any SDK-specific answers as "based on last known documentation —
  verify against the current SDK."

**Changes through the Descope MCP Server.** Before any change to the project, select it
(`session` → `selectProject`) and confirm its ID matches the Project ID the user confirmed for this
migration (recorded in `MIGRATION-STATE.md`, and the app's `DESCOPE_PROJECT_ID` once set), get the
user's approval for that change, then elevate (`session` → `elevate`). If the user declines, skip
the change. If any other step fails, leave it in the Console Setup Checklist for the user to do.

Do not proceed to Part 1.5 until this step is resolved.

---

## Part 1.5: Scope Guard (BLOCKING)

Before triage, confirm the app uses FusionAuth. Quick check (case-insensitive): grep the repo for
`fusionauth` (packages, imports, `FUSIONAUTH_` env vars, `fusionauth/fusionauth-app` images,
`kickstart.json`, `next-auth/providers/fusionauth`).

| What the repo shows | Result |
|---|---|
| Any FusionAuth package, import, env var, Docker image, Kickstart file, or Auth.js FusionAuth provider | FusionAuth — proceed |
| A generic OIDC library whose issuer/authority is a FusionAuth host (`*.fusionauth.io`, or a self-hosted host serving `/oauth2/authorize` and `/api/` paths) | FusionAuth — proceed, and note "no FusionAuth SDK" |
| Another identity provider (Auth0, Okta, Frontegg, WorkOS, Stytch, PingOne, Azure AD B2C, Cognito, Keycloak, Clerk) | Stop and name the matching skill if one exists (`auth0-to-descope`, `okta-cis-to-descope`, `frontegg-to-descope`, `workos-to-descope`, `stytch-to-descope`, `pingone-to-descope`, `azure-ad-b2c-to-descope`); otherwise point to [docs.descope.com/migrate](https://docs.descope.com/migrate) |
| A generic OIDC library with the issuer only in a secrets store, app settings, or a pipeline | Ask |

When asking, use `AskUserQuestion`: "Which service does this app sign in with?" — FusionAuth / Other
(name it). Proceed only on an explicit "FusionAuth". The code wins over the request: if the user says
"FusionAuth" but the repo shows another provider, ask.

When stopping, say what you found and where to go:
> This skill covers FusionAuth only. This app signs in with <provider> (`<file>:<line>`).
> <Use the `<skill-name>` skill | See docs.descope.com/migrate>. No code was changed.

---

## Part 2: Migration Plan

Part 2 has two sub-steps:

1. **Triage** — ask the questions needed to understand scope (migration questions go here since answers shape the plan)
2. **Codebase Analysis + Plan File** — scan the project, produce `MIGRATION-PLAN.md`, and pause for review

**Scan before you ask.** If there's a codebase available, run Step 1's searches (or at minimum the
broad sweep, search 1, plus searches 4 and 5 for generic-OIDC apps) *before* Step 0's
`AskUserQuestion` calls — silently, as a normal tool call, not as something that needs permission.
Scanning is free, non-destructive, and turns generic multiple-choice questions into specific,
pre-filled ones: naming the actual framework and integration style found rather than offering a menu,
presenting a detected self-hosted deployment as a confirmation, reading tenants and roles straight out
of a `kickstart.json`, and skipping questions for categories the scan found zero evidence of. Triage
then does two things: **confirms** what the scan found and **asks only what code cannot reveal** —
production user counts, what each FusionAuth tenant represents, where FusionAuth runs, which hash
schemes exist, migration goal, and whether lambdas or webhooks live only in the admin UI. This still
requires `AskUserQuestion` for both calls below; it changes what the questions contain and how many
are asked, not whether the step happens.

**Scale the question count to the project.** A single-tenant app with one Application and a handful
of components does not need the same triage volume as a multi-tenant B2B platform with groups,
lambdas, and enterprise SSO. If the scan shows no evidence of a feature category (entities, SCIM,
connectors, consents, families, gaming IdPs, etc.), it's reasonable to state "no evidence found for X
— confirm out of scope?" as a single grouped question rather than working through the full catalogue.

### Step 0: Triage (BLOCKING — requires `AskUserQuestion`)

**Use the `AskUserQuestion` tool to gather the information below, informed by whatever the codebase
scan already found. Do not infer answers from memory, prior conversations, or assumptions the scan
didn't actually confirm — even if you think you know.**
The migration path differs based on these answers; getting them wrong wastes the user's
time and produces incorrect guidance.

Do not proceed to Step 0.5 until the user has answered.

**First `AskUserQuestion` call (up to 4 questions):**

1. **Backend language / framework and integration style** — Present what the scan found (e.g.
   "Next.js with next-auth's FusionAuth provider", "Express + `@fusionauth/typescript-client`",
   "Spring Boot OAuth2 client"). The integration style matters more than the language here:
   - **FusionAuth SDK** (React/Vue/Angular) with a Hosted Backend → swap to the Descope SDK.
   - **Generic OIDC library** (`next-auth`, `openid-client`, Spring Security, ASP.NET, `authlib`,
     AppAuth) → either keep the library and repoint it at Descope as the OIDC provider, or adopt the
     Descope SDK. Ask which they prefer (see Step 1.5 item 3).
   - **Direct Login API** (`POST /api/login` from the app's own login form) → the app owns its login
     UI today; Descope replaces it with a Flow, or the Descope SDK's password method if they insist on
     keeping the custom form.
2. **Where does FusionAuth run?** — **Self-hosted** (their own Docker/Kubernetes/VM, own database) or
   **FusionAuth Cloud**. This decides how password hashes get out: self-hosted teams query their own
   database; Cloud customers open a support ticket for a database export (free for customers leaving
   FusionAuth, on any plan). The scan signal is a `fusionauth/fusionauth-app` image, Helm chart, or
   `FUSIONAUTH_APP_*` server variables (self-hosted) vs. a `*.fusionauth.io` URL (Cloud).
3. **Migration goal** — Full cut-over, incremental/phased migration, or just evaluating.
4. **Existing users** — Are they migrating an app with active users in FusionAuth, staging/dev only,
   or starting fresh? This determines whether user migration planning is needed (export, hash
   compatibility, tenant mapping, SCIM continuity, phased vs. big-bang cutover, forced re-login on
   cutover).

**Second `AskUserQuestion` call — FusionAuth feature usage (use `multiSelect: true`):**

1. **Which FusionAuth features are in use?** Present the highest-impact categories:

* **Tenants** — how many, and **what each represents**: an environment (dev/staging/prod on one instance), a B2B customer, or a separate product. Whether the same person can exist in several tenants. This is the most important answer in the triage — see Step 3 → *Tenants*.
* **Applications** — how many, whether they are separate products or surfaces of one product, which OAuth grants each uses (authorization code, refresh, client credentials, device, password), and whether the app checks `applicationId` / `aud`.
* **Registrations and application roles** — whether users must be registered for an Application to use it; which roles each Application defines; whether two Applications define roles with the same name; whether `superRole` / default roles are used.
* **Groups** — whether groups are used to grant application roles, and whether group membership itself is read anywhere (`memberships`, a lambda putting groups into the token).
* **Login methods** — password, passwordless magic link / code, passkeys (WebAuthn), MFA (TOTP authenticator, email, SMS), social providers (Google, Apple, Facebook, Microsoft, GitHub/OpenID Connect, LinkedIn, Twitter, and the gaming providers Steam, Twitch, Xbox, Epic, Nintendo, Sony PSN), and which identifiers users sign in with (email, username, phone).
* **Hosted login pages and themes** — whether login runs on FusionAuth's hosted pages, how heavily the theme's FreeMarker templates are customized, localization, and **Advanced Registration Forms**.
* **Lambdas** — which types: JWT populate, Id Token / UserInfo populate, client-credentials JWT populate, SAML v2 populate, reconcile (OIDC, SAML, social, LDAP, External JWT), login validation, MFA requirement, self-service registration validation, SCIM converters. Whether any lambda calls out over HTTP. Flag as high complexity when a lambda *rejects* logins.
* **Webhooks** — which events the app consumes, whether any are **transactional** (FusionAuth waits for the response and fails the event if the webhook fails), and whether they keep the app's own database in sync.
* **Enterprise SSO** — OIDC or SAML v2 identity providers, how each is scoped (managed domains, tenant restrictions, `idp_hint`), whether FusionAuth is itself the IdP for downstream apps (SAML v2 IdP or OIDC), and whether reconcile lambdas map roles from IdP claims.
* **SCIM** — whether FusionAuth's SCIM server (Enterprise) receives users and groups from customer directories. Flag as high complexity.
* **Connectors** — whether a Generic or LDAP connector is pulling users in from a legacy store (meaning the team is *still* mid-migration into FusionAuth, and some users live elsewhere). Flag as high complexity.
* **Entity Management / M2M** — entity types, entities, grants, and the client-credentials grant; also plain API keys handed to services. Which audiences and permissions downstream services check.
* **Sessions and tokens** — access-token and refresh-token lifetimes, refresh-token policy (sliding, one-time use), whether the React/Vue/Angular SDK uses the **Hosted Backend** (`app.at` / `app.rt` cookies) or **DPoP**, whether a `next-auth` session wraps everything, which signing key type (RSA/EC vs. HMAC) the tenant uses, and how backends validate tokens.
* **Self-service account management / Tenant Manager** — whether users are sent to FusionAuth's `/account` pages (`manageAccount()`), and whether tenant admins use Tenant Manager.
* **Security features** — breached password detection, Advanced Threat Detection (rate limits, CAPTCHA, IP access control lists, impossible travel), user actions (temporary locks), and password policies (history, expiration, complexity).
* **Consents and Families** — whether either is used (usually for child accounts / COPPA). Neither has a Descope equivalent.
* The user can add others via **"Other."**

After both calls, summarize findings and flag high-complexity items before proceeding to Step 0.5.
The main high-complexity FusionAuth areas are typically **what tenants become, hash schemes Descope
can't import, same-email users across tenants, registrations and per-application roles, lambdas that
reject or reshape logins, SCIM, enterprise SSO with reconcile lambdas, connectors still pulling users
in, and HMAC-signed tokens in backends**.

---

### Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

These questions surface blockers the framework doesn't expose. Ask even the ones you think
you know. Use `AskUserQuestion` before proceeding to codebase analysis.

**Read `references/flows-and-widgets.md` first** — especially the terminology table and the
self-service mapping table. The last group of questions below asks which screens a Descope Widget or
the SSO Setup Suite can absorb; you cannot ask that usefully without knowing the catalog. The
*High-Complexity FusionAuth Areas* checklist in Step 3 is also worth skimming now; it is the list you
are flagging against.

Batch into calls of up to 4 questions. Skip questions that are clearly inapplicable given
Step 0 answers (e.g., skip user migration planning if they said they're starting fresh).

**Access and credentials**

* Do they have access to the Descope Console and a Project ID? (If not, see Step 1.5.)
* Do they need a Management Key? Required for user import, user CRUD, tenant management, RBAC, SSO/SCIM configuration, access keys, Inbound Apps, and other management operations.
* Do they have a FusionAuth **API key** that can read tenants, applications, users, groups, identity providers, lambdas, and webhooks? It goes in the `Authorization` header **as-is, with no `Bearer` prefix**. A tenant-scoped key sees only one tenant; with several tenants, a global key plus the `X-FusionAuth-TenantId` header is easier.
* **Self-hosted:** do they have read access to the FusionAuth database (PostgreSQL or MySQL)? That is where password hashes and TOTP secrets live. **Cloud:** have they opened (or can they open) a support ticket for a database export? It takes time — start it now, not at cutover.

**Codebase scope**

* Is login on FusionAuth's **hosted pages** (redirect to `/oauth2/authorize`) or a **custom form** calling `/api/login`? Hosted maps to Descope-hosted login or an embedded Flow; a custom form maps to an embedded Flow (recommended) or the Descope SDK's password API.
* Does the app use a **generic OIDC library**? If yes, ask whether they want to keep it and repoint it at Descope (smallest change; Descope acts as the OIDC provider through a Federated App) or adopt the Descope SDK (gives Flows, Widgets, and session helpers directly). See Step 1.5 item 3.
* Are there places that read claims off the FusionAuth token — `roles`, `applicationId`, `aud`, `tid`, `email`, `email_verified`, `preferred_username`, `authenticationType`, `sid` — or custom claims added by a **JWT populate lambda**? These need a Descope JWT Template before equivalent reads work.
* How do backends validate tokens? **JWKS** (RSA/EC keys), a **hardcoded public key**, or an **HMAC secret** (`HS256`; the default for Kickstart and pre-1.50 installs)? The last two break silently at cutover.
* Are there multiple services validating FusionAuth tokens? Each needs updating.
* Does the app call the FusionAuth Management API (`FusionAuthClient`) at runtime — creating users, registrations, groups, or identity providers? Each call becomes a Descope Management SDK call behind a server endpoint, or a Widget.
* Does the app depend on FusionAuth **webhooks** to keep its own database in sync? Search for handlers before changing user, registration, or group behavior.
* Are there **lambdas** that exist only in the FusionAuth admin UI? Export them (`GET /api/lambda`) — they are part of the auth behavior even though no file in the repo shows them.

**Deployment and risk**

* How many FusionAuth **instances** and **tenants** exist, and which ones are environments? Each environment becomes its own Descope Project with its own Project ID, Approved Domains, and secrets.
* Is there a maintenance window, or does this need to be zero-downtime?
* Are any external customers, enterprise IdPs, SCIM directories, or machine-to-machine clients integrated with the production FusionAuth? If yes, plan customer-facing cutover steps, not just code changes.
* Is FusionAuth behind a **custom domain** (e.g. `auth.myapp.com`)? With the Hosted Backend this is often required, because the Hosted Backend's cookies don't work cross-site. Plan the equivalent Descope custom domain before cutover.
* Is FusionAuth an **IdP for other applications** (SAML v2 IdP, or OIDC for third-party apps)? Those relying parties need new metadata and issuer URLs — a separate workstream.
* Are login URLs, issuer URLs, or JWKS URLs contractually or technically expected to stay stable? Flag early — they affect SSO, sessions, and token validation.

**User migration** (if they indicated existing users in Step 0)

* How many users, across how many tenants? With the Elasticsearch search engine on FusionAuth before 1.48.0, `POST /api/user/search` stops at 10,000 results, so large exports need the database route or query slicing.
* **Password credentials: confirm the strategy explicitly.** FusionAuth's API never returns hashes; the database does. Count users per `encryption_scheme` (one query, below) before picking:
  1. **Full migration with password hashes (recommended default).** Export users with their hash, salt, scheme, and factor from the database (self-hosted) or a support-provided export (Cloud), and import them with Descope's `hashedPassword` field. Users keep their passwords with no extra step. Supported mapping:
     - `salted-pbkdf2-hmac-sha256` (FusionAuth's default) → `pbkdf2` with `type: "sha256"`, `iterations` = factor
     - `salted-pbkdf2-hmac-sha512-512` → `pbkdf2` with `type: "sha512"`
     - `salted-pbkdf2-hmac-sha256-512` → `pbkdf2` with `type: "sha256"` — **test with a real sign-in first**; FusionAuth uses a 512-bit key here and Descope takes no key-length field
     - `bcrypt` → `bcrypt` with the full `$2a$<factor>$<salt><hash>` string rebuilt from FusionAuth's separate columns
     - `phpass-md5` / `phpass-sha512` → `phpass` — test with a real sign-in first
     - `salted-md5`, `salted-sha256` with factor > 1, `salted-hmac-sha256`, and any custom plugin scheme → **not importable**; use option 2 for those users
  2. **Full migration plus JIT for the users whose hashes don't import.** Import everyone; set `freshlyMigrated` on users without an importable hash. During a transition, the sign-in Flow sends those users through a Generic HTTP Connector that calls FusionAuth's Login API (`POST /api/login`) so FusionAuth checks the password and Descope stores it (imported users need one OTP or magic-link step first, because storing a password on an existing user uses **Update Password**). Also the right choice when the hash export is delayed: import profiles now, add hashes later, and let JIT cover the gap.
  3. **Full migration without passwords** — the same import with no hashes and no JIT. Everyone verifies their email or phone at first sign-in, then goes passwordless or resets their password. Choose only when no export is possible and FusionAuth must be turned off at the switch.
  4. **JIT-only via FusionAuth as a custom OIDC provider** — users sign in through FusionAuth's hosted login (MFA included) and are provisioned into Descope from the ID token. Good when moving to passwordless anyway.

  Any option that uses JIT keeps FusionAuth running for a transition period. Ask how long the user can keep it on, and recommend at least a few months when passwords matter. See `references/implementation-nuances.md` → **Migrating users and tenants**.
* **Does the same email exist in more than one FusionAuth tenant?** If those tenants become Descope tenants in one project, those records merge into one Descope user. Decide which record's password, name, and verification status win (usually the most recent `last_login_instant`), and tell affected users. Run the duplicate-count query in the export recipe before estimating.
* **Which identifier do users sign in with?** Email, username, or both. Descope takes one `loginId` plus additional login IDs; users with both need a rule for which is primary.
* Is `user.data` (free-form JSON) in use? Each field the app reads becomes a Descope custom attribute, defined in the Console first. Registration-level `data` needs a decision too.
* Are **TOTP authenticators** enrolled? Descope's import accepts a base32 TOTP `seed`, so authenticator-app MFA can carry over if the secret is in the export — confirm the secret's encoding in the export before promising it. **Passkeys, email MFA, and SMS MFA enrollments do not carry over**; users re-enroll.
* Big-bang cutover or phased? Map each FusionAuth tenant to its Descope target first — user import, roles, SSO, and SCIM all depend on it.
* **SCIM is a lifecycle system, not a one-time import.** If FusionAuth's SCIM server is in use, customer directories keep pushing create/update/deactivate events after cutover. Re-point every SCIM client at Descope before cutover, or provisioning silently breaks.
* Are they aware that active FusionAuth sessions end at cutover unless dual token validation is used? Plan for forced re-login or a phased rollout.
* Does the app store FusionAuth user IDs (UUIDs), tenant IDs, application IDs, or group IDs in its own database? If yes, keep the FusionAuth user ID as a custom attribute (`fusionauthId`) and plan an ID mapping table.

**Gaps to flag immediately** (don't ask — flag these proactively based on Step 0 answers)

* If they're on **FusionAuth Cloud with production users**: flag that the hash export goes through FusionAuth support and should be requested now. It is the longest-lead item in the plan.
* If any users carry a **hash scheme Descope can't import**: flag the count and plan JIT (option 2) for them.
* If **FusionAuth tenants are B2B customers**: flag the same-email merge question and the per-tenant settings (password policy, MFA policy, themes, email templates) that become tenant settings or Flow conditions in Descope.
* If **several Applications define roles**: flag that Descope roles are project-wide. Same-named roles across Applications must be merged deliberately or renamed (e.g. `billing:admin`).
* If **registrations gate access** (users exist but aren't registered for every Application): flag that Descope has no registration object. Model "may use app X" as a role, a tenant, a custom attribute, or a separate project.
* If **lambdas reject logins** (login validation, registration validation, MFA requirement): flag for dedicated review. They become Flow conditions and Connectors, and their failure behavior must be preserved.
* If **reconcile lambdas** map IdP claims to roles or user data: flag that the mapping becomes Descope SSO/OAuth attribute and group mapping, and must be re-tested per IdP.
* If a **Connector** is still migrating users *into* FusionAuth: flag as high complexity — some users' real credentials may still live in a third system.
* If backends verify **HS256** tokens with a shared secret: flag that every such backend must switch to Descope's JWKS-based validation.
* If they use **Entity Management / client credentials**: inventory every client, its permissions, and the audiences downstream services check.
* If they use **Consents or Families**: flag that neither has a Descope equivalent; plan where that data lives.

**Console/Flow/Widget opportunities** (flag before codebase analysis, then ask):

* If the app sends users to FusionAuth's **`/account`** pages: ask whether the User Profile Widget replaces them.
* If the app has a **team/user management page** built on `/api/user`, `/api/user/registration`, or `/api/group/member`: ask whether the User Management or Role Management Widget covers it.
* If the app creates **Identity Providers** per customer (script or admin screen): ask whether the SSO Setup Suite lets tenant admins do it themselves.
* If the **theme** is heavily customized: ask whether a Descope Flow with Styles can match it, or whether the user wants Descope's Bring Your Own Screen (BYOS) to keep their own components.
* If the app has a separate **MFA enrollment** page: ask whether MFA should become a step or subflow in the main sign-in Flow.
* If **lambdas** run custom checks during login or registration: ask whether each can become a Flow step, condition, or Connector rather than code.

Summarize any blockers and Console/Flow/Widget opportunities before proceeding to codebase analysis.

---

### Step 1: Codebase Analysis

Scan the codebase to map every auth touchpoint before writing the plan.

FusionAuth apps integrate through some mix of:

- **Frontend SDKs** — `@fusionauth/react-sdk` (`FusionAuthProvider`, `useFusionAuth()`, `RequireAuth`, `Unauthenticated`, login/logout/register/account buttons), `@fusionauth/vue-sdk` (`FusionAuthVuePlugin` / `createFusionAuth`, `useFusionAuth()`, `RequireAuth`, `RequireAnonymous`), `@fusionauth/angular-sdk` (`FusionAuthModule.forRoot`, `FusionAuthService`, `<fa-login>`). By default they call a **Hosted Backend** (`/app/login`, `/app/callback`, `/app/refresh`, `/app/me`, `/app/logout`) that keeps tokens in `app.at` / `app.rt` / `app.idt` / `app.at_exp` cookies; with `useDpop: true` they call FusionAuth's OAuth endpoints directly.
- **Next.js** — almost always `next-auth` with `next-auth/providers/fusionauth` (or Auth.js `@auth/core/providers/fusionauth`). There is no official FusionAuth Next.js SDK.
- **Generic OIDC libraries** — `openid-client`, `passport-openidconnect`, Spring Security OAuth2 client/resource server, ASP.NET `AddOpenIdConnect` / `AddJwtBearer`, `authlib`, `golang.org/x/oauth2` + `go-oidc`, AppAuth on mobile, `flutter_appauth`, `react-native-app-auth`.
- **Management API clients** — `@fusionauth/typescript-client`, `fusionauth-client` (Python), `github.com/FusionAuth/go-client`, `io.fusionauth:fusionauth-java-client`, `FusionAuth.Client` (.NET), `fusionauth_client` (Ruby), `fusionauth/fusionauth-client` (PHP).
- **Mobile SDKs** — `fusionauth-swift-sdk` (iOS) and `io.fusionauth:fusionauth-android-sdk`, both built around `AuthorizationManager`. Flutter and React Native use AppAuth wrappers.

Run the searches in `references/fusionauth-detection-patterns.md` (broad sweep, frontend SDKs,
backend clients, token claims and OAuth endpoints, env vars, self-hosted infrastructure, mobile,
dependency manifests, webhooks and lambdas). Read the notes beside each search: several exist to catch
a case the obvious grep misses (generic-OIDC apps with no FusionAuth package; HMAC verification;
`kickstart.json` and `.ftl` theme files; lambdas kept as `.js` files).

For each hit, record:

- **File path and line** — where the change happens
- **What it does** — import, provider setup, route protection, claim access, Management API call, registration/role check, webhook handler, logout handler, etc.
- **Complexity** — Low (drop-in replacement), Medium (logic rewrite), High (no equivalent)

Read `package.json` (or equivalent) for the exact framework and SDK versions. For `next-auth`, note
v4 vs. Auth.js v5 — the config file shape and env var names differ. Next.js version also affects async
behavior (15 vs. 14). If a `kickstart.json` exists, read it fully: it is an inventory of tenants,
applications, roles, lambdas, keys, and webhooks.

If a Descope MCP is connected, use `docs_search` or `docs_ask_question` (Descope MCP Server) or
`search-descope-docs` or `ask-question-about-descope` (Docs MCP) to verify current SDK method names for anything you plan to reference in the plan.

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
one-sentence rationale. Add one sentence on what doesn't change — the login model, sign-in methods,
tenants, roles, and (with a hash import) passwords carry over — and one on what does: active
FusionAuth sessions end at cutover, so users sign in once more.

Include a **Migration at a Glance** table:


|                                  |                                                                     |
| -------------------------------- | ------------------------------------------------------------------- |
| **Approach**                     | Full migration with password hashes (+ JIT for N users on unsupported schemes) |
| **FusionAuth tenants become**    | Descope Projects (environments) / Descope Tenants (customers)       |
| **Login model**                  | FusionAuth hosted pages → Descope-hosted login / embedded Flow; OIDC library kept or replaced |
| **Files changing**               | N source files across N areas                                       |
| **Console setup**                | N configuration steps before launch                                 |
| **User impact**                  | Users sign in once after cutover with their existing password; passkeys and SMS/email MFA re-enroll |
| **Estimated engineering effort** | N–N hours                                                           |
| **Biggest risk**                 | One sentence naming the highest-complexity item                     |


---

#### What's Changing and Why

Prose (not a table) describing what each part of the system does today and what it does
after. Example:

> Today, FusionAuth handles everything related to login. The React app wraps itself in
> `FusionAuthProvider` and sends users to FusionAuth's hosted login page; FusionAuth's Hosted Backend
> stores the access and refresh tokens in `app.at` and `app.rt` cookies, and the Express API reads
> `app.at`, verifies it against FusionAuth's JWKS, and checks the `roles` claim for the `admin` role
> on the `applicationId` it expects. After this migration, Descope takes over all of those
> responsibilities. The login UI becomes a Descope Flow on a Descope-hosted page. Session validation
> moves to the Descope SDK, reading the `DS` cookie. FusionAuth application roles become Descope
> roles. `FUSIONAUTH_URL`, `FUSIONAUTH_CLIENT_ID`, and `FUSIONAUTH_API_KEY` are replaced by
> `DESCOPE_PROJECT_ID` (plus a Management Key for server-side administration), and the FusionAuth
> server, database, and search cluster can be shut down after the transition.
>
> FusionAuth features in use that need to carry over: [list in plain English, one clause each].

Tailor to triage findings.

---

#### Client SDK vs. Backend SDK: A Specific 1-to-1 Mapping

For every FusionAuth touchpoint found in triage, produce a concrete, one-to-one mapping — FusionAuth
construct → the exact Descope SDK and method that replaces it — and state explicitly whether that
replacement runs in the **client SDK** or the **backend SDK**, and why. Use this division of
responsibility:

- **Client SDK** (`@descope/web-js-sdk`, `@descope/react-sdk`, `@descope/vue-sdk`,
  `@descope/angular-sdk`, `@descope/nextjs-sdk` client components, or the `<descope-wc>` web
  component) — everything the user's browser or mobile app does: rendering the login/sign-up UI (a
  Descope Flow replaces FusionAuth's hosted pages or the app's custom login form), initiating
  authentication, holding the session, refreshing the token, and reading the current user for UI
  purposes. This replaces `FusionAuthProvider` / `FusionAuthVuePlugin` / `FusionAuthModule`,
  `useFusionAuth()` (`isLoggedIn`, `userInfo`, `startLogin`, `startLogout`, `refreshToken`),
  `RequireAuth` / `Unauthenticated`, and the Hosted Backend round-trips. It uses only the public
  Project ID — never a Management Key.
- **Backend SDK** (`@descope/node-sdk`, `descope` (Python), `github.com/descope/go-sdk`, etc.) —
  everything the server does: validating the session JWT on every request (replacing JWKS or HMAC
  verification of `app.at` / Bearer tokens, `validateJWT`, Spring resource-server config, `AddJwtBearer`),
  checking roles and permissions, and — with a Management Key — all administrative operations by ID
  (user, tenant, role, SSO/SCIM, access-key management). This replaces every `FusionAuthClient` call.

For each file or area, name the FusionAuth call, the Descope SDK that replaces it, which side it runs
on, and the reason (e.g. "role assignment must stay server-side because the Management Key cannot
ship to the browser"). When one FusionAuth feature spans both sides — for example `RequireAuth
withRole="admin"` (client gate) plus a backend `roles` check — split it into its client half and its
backend half so the reader sees exactly what moves where, and why.

If the user chose to **keep a generic OIDC library**, say so here: the library stays, its issuer,
client ID, and secret change, and the claim reads still change because Descope's token shape differs.

---

#### Auth Touchpoints: What the Code Analysis Found

Open with the scope count (e.g., "14 files across 5 areas"). Group by area, not file path.
Each group gets a sentence on what it does and what changes.

**Session handling (3 files)** — These files read and validate the current user's login state.
They'll be updated to use the Descope session SDK instead of FusionAuth token validation.


| File               | What it does today                                                                                    | What changes                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `server/auth.ts:34`   | Reads the `app.at` cookie and verifies it with `jose` against FusionAuth's JWKS; checks `aud` = application ID | Rewritten to call Descope `validateSession()` on the `DS` cookie; a thin adapter preserves the shape callers expect |
| `server/roles.ts:12` | Checks `claims.roles.includes('admin')` | Uses the Descope SDK's role validation helper; role names carried over from FusionAuth |


**Login / auth UI (2 files)** — These mount the FusionAuth provider and start the hosted login.
Descope replaces this with the Descope provider plus hosted login or an embedded Flow.


| File                         | What it does today                                      | What changes                                                                                                  |
| ---------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `src/main.tsx`             | Wraps the app in `FusionAuthProvider` with `serverUrl`, `clientId`, `redirectUri` | Replaced with Descope `AuthProvider projectId={...}` (with `oidcConfig` for hosted login)   |
| `src/Login.tsx`         | Renders `FusionAuthLoginButton` | Calls `sdk.oidc.loginWithRedirect()`, or renders `<Descope flowId="sign-up-or-in">` |


Cover all functional groupings found — Management API calls, registration checks, webhook handlers,
M2M token issuance, mobile auth, `/account` links. End with:
"Total: N files. Estimated code-change effort: N–N hours."

---

#### Feature Migration: FusionAuth → Descope

For each FusionAuth feature confirmed in triage, write a short paragraph: what it's trying to
accomplish, the best Descope approach for that goal, what's different, and what action is
required. The best approach may be a Flow, Widget, SSO Setup Suite, or Console configuration
rather than a direct SDK equivalent — reason about the intent, not just the API surface. Only
recommend SDK code when programmatic control is genuinely required. Example:

> **Application roles and registrations → Descope roles**
> In FusionAuth, each Application defines its own roles, and a user gets roles through a
> *registration* — the record that says "this user may use this application." The access token's
> `roles` claim holds the roles from the registration for the application that requested the token,
> plus roles from any groups the user belongs to.
>
> Descope has no per-application registration. Roles are defined once per project and assigned to a
> user either project-wide or within a tenant. This app has one Application, so its roles (`admin`,
> `editor`, `viewer`) become Descope roles with the same names, and each user's registration roles
> plus group roles are flattened onto the user at import.
>
> The request-time change is small: the code that checked `claims.roles` uses the Descope SDK's role
> helper instead. Users who existed in FusionAuth but had no registration for this Application
> (FusionAuth's "authenticated but not authorized" state) are not imported, unless the team decides
> otherwise.

> **Effort: Low (under 1 hour of code changes).** Confirm the role list against `kickstart.json` or the admin UI.

Only include confirmed features.

---

#### Before the Code Can Run: Required Configuration

Some Descope behavior is configured in the console, not in code. List every item that must
be set up before the app works, as checkboxes with a plain description of what it is, why
it's needed, and roughly how long it takes. Group into "Required before any testing" and
"Required before production":

**Required before any testing:**

- **Create a Descope project** — Takes 2 minutes. Produces a Project ID that replaces
  `FUSIONAUTH_URL` and `FUSIONAUTH_CLIENT_ID` in the app's environment variables.
- **Configure Approved Domains** — Descope validates redirect targets against a domain list.
  Enter domain only (`localhost:3000`, `app.myapp.com`) — not the full authorized redirect URLs
  FusionAuth's application OAuth settings hold, like `http://localhost:3000/app/callback`.
- **Create an authentication flow** — Descope uses a visual "flow" to define the login
  experience. The built-in `sign-up-or-in` flow works for most apps and requires no
  customization to start. Set it to the same methods FusionAuth offers today.
- **Configure a JWT Template** — By default, Descope session tokens don't include the user's
  email or name, and FusionAuth's access tokens include `email`, `email_verified`, and
  `preferred_username`. Any code reading those off the token gets nothing until this is configured.
  (~10 minutes)

**Required before production:**

- **Create roles and permissions** — Descope roles are referenced by name and must exist before
  the import assigns them.
- **Create tenants** (if FusionAuth tenants or another customer concept map to Descope Tenants).
- **Define custom attributes** for `fusionauthId`, `freshlyMigrated` (if JIT is used), and every
  `user.data` field the app reads.
- **Configure SSO connections per tenant** (or enable the SSO Setup Suite for self-serve).
- **Configure social login providers** — copy the client ID and secret from each FusionAuth Identity
  Provider into Descope, and add Descope's callback URL in each provider's developer console.
  (~15 minutes per provider)
- (continue for each item found in analysis)

---

#### Environment Variables

Diff table with plain-English notes for each removal and addition:


| Remove                              | Add                              | Why                                                                                                                                 |
| ----------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `FUSIONAUTH_URL` / `FUSIONAUTH_ISSUER` / `FUSIONAUTH_SERVER_URL` | *(none)* | FusionAuth's host and issuer. Descope SDKs resolve the endpoint from the Project ID; a custom domain is set in the SDK only if configured. |
| `FUSIONAUTH_CLIENT_ID` / `FUSIONAUTH_APPLICATION_ID` | `DESCOPE_PROJECT_ID` | The FusionAuth Application ID doubled as the OAuth client ID. Descope uses the Project ID. |
| `FUSIONAUTH_CLIENT_SECRET` | *(none)*, or a Descope Access Key / Inbound App secret | Needed only if the app keeps a confidential OIDC client (generic OIDC library, `next-auth`). |
| `FUSIONAUTH_API_KEY` | `DESCOPE_MANAGEMENT_KEY` | Used for Management API calls. Needed only if the app does server-side user/tenant/role administration. |
| `FUSIONAUTH_TENANT_ID` | *(none)* or a Descope tenant ID | Only if the code scopes requests to one tenant. |
| `AUTH_FUSIONAUTH_*` (Auth.js) | `AUTH_DESCOPE_*` or none | Depends on whether `next-auth` stays (see Step 2 → Next.js). |
| *(frontend)* `serverUrl` / `clientId` / `redirectUri` in `FusionAuthProvider` | `NEXT_PUBLIC_DESCOPE_PROJECT_ID` / `VITE_DESCOPE_PROJECT_ID` or framework equivalent | Often hardcoded inline rather than read from env vars. |


Follow with: "Net change: N variables removed, 1–3 added. No FusionAuth secrets need rotating — they
stop being used — though FusionAuth should stay running, read-only, until the migration is verified
(and for the whole JIT transition if one is used)." If the team self-hosts, add a line that the
FusionAuth server variables (`FUSIONAUTH_APP_*`, `DATABASE_*`, `SEARCH_*`) belong to infrastructure
being retired, not to the app.

---

#### User & Tenant Migration (only if existing users need to be migrated)

Prose strategy first, then steps. Start with: "X existing users across Y FusionAuth tenants need to
be in Descope before cutover." Describe:

- **The plan**: by default, export users with password hashes, import them, and switch the app in one step. Say how many users are on each hash scheme and how the ones that can't import are handled
- **Tenant mapping**: what each FusionAuth tenant becomes (Descope Project or Tenant), and how same-email users across tenants are merged
- **Role mapping**: how application roles, registrations, and group roles become Descope roles
- **What users will experience**: they sign in once more with their existing password. Passkey and SMS/email MFA users re-enroll; TOTP users keep their authenticator if seeds were exported
- **The biggest dependency**: getting the hashes out — a database query (self-hosted) or a FusionAuth support ticket (Cloud)
- **SCIM continuity**: whether customer directories must be re-pointed at Descope

End with a brief checklist of the migration steps at the level a PM can track. The agent writes the
export/import script (Step 3 → User & Tenant Data has the queries, endpoints, and mapping):

- Get read access to the FusionAuth database (self-hosted) or request the database export from FusionAuth support (Cloud)
- Count users per hash scheme and per tenant, and count same-email duplicates across tenants
- Define the custom attributes the script will set (`fusionauthId`, `freshlyMigrated`, and `user.data` fields) in the Descope Console before the first run
- Create tenants, permissions, and roles in Descope (in that order) before users
- Write the script with a dry-run mode, and run it against a Descope **dev** project first
- Sign in as at least one imported user per hash scheme with their real password before going further
- Decide whether to copy SAML/OIDC Identity Provider settings into Descope tenant SSO, and list the IdP entity IDs and certificates to fill in
- Re-point SCIM at Descope (if SCIM is in use)
- Run against staging, then production
- If JIT is in use: add the Generic HTTP Connector to the sign-in Flow for `freshlyMigrated` and brand-new users, keep FusionAuth running for the chosen transition, then turn it off and send remaining `freshlyMigrated` users to reset or passwordless
- Run a final delta import of users created or changed in FusionAuth after the export (by `insert_instant` / `last_update_instant`), or freeze sign-ups during the switch

---

#### Trade-offs and considerations

Things that could affect timeline, user experience, or scope. Write each in plain English
with three parts: **what it is**, **what breaks if it's ignored**, and **what to do**.
Format each as a named callout:

> **Consideration: password hashes come from the database, not the API**
> FusionAuth's API never returns password hashes. Self-hosted teams read them from their own
> database; FusionAuth Cloud customers need FusionAuth support to provide a database export. If the
> plan assumes an API export, the hashes never arrive and every user has to reset.
> **Action:** Start the export path in week one. Count users per scheme so the JIT fallback is sized
> before cutover.

> **Consideration: a FusionAuth tenant is not a Descope tenant**
> FusionAuth tenants are separate user pools; Descope tenants are groups of users in one pool. If
> customer tenants become Descope tenants, the same email in two tenants becomes one Descope user. If
> environment tenants are mapped to Descope tenants by mistake, dev and prod users end up in one
> project.
> **Action:** Record what each FusionAuth tenant becomes in the plan, and agree the merge rule for
> duplicate emails before writing the import.

> **Consideration: roles were per application; Descope roles are per project**
> Two FusionAuth Applications can both define `admin` with different meanings. Importing both as one
> Descope `admin` role grants access the user never had.
> **Action:** List roles by Application, and merge or prefix them deliberately.

> **Consideration: user profile data won't appear in the token until a JWT Template is configured**
> FusionAuth's access token carries `email`, `email_verified`, and `preferred_username`; Descope's
> does not. Code reading them from the token gets nothing.
> **Action:** Configure the JWT Template before running any tests. Estimated time: 10 minutes.

> **Consideration: backends that verify with an HMAC secret break silently**
> Installs set up through Kickstart (or before FusionAuth 1.50) sign tokens with HS256. Backends
> verifying with that shared secret reject every Descope token as "invalid signature", which looks
> like a Descope problem.
> **Action:** Find every `HS256` / `jwt.verify(token, secret)` and replace it with Descope session
> validation.

> **Consideration: SCIM is a lifecycle system, not just a user import**
> Customer directories keep creating, updating, and deprovisioning users after cutover.
> **Action:** Identify every SCIM client and re-point it at Descope before cutover.

Include only applicable trade-offs and considerations.

---

#### Execution Plan

Open with one sentence: phases run in sequence; steps within a phase can run in parallel.
Then labeled phases, each with a time estimate:

---

**Phase 0 — Start the export path** (day one, mostly waiting)

- Self-hosted: confirm database read access and the FusionAuth version (the schema varies by version)
- Cloud: open the FusionAuth support ticket for a database export

**Phase 1 — Console Setup** (~30–60 minutes, no code required)
Can be done by any team member with Descope console access, in parallel with other work.

- Create a Descope project per environment, copy each Project ID
- Configure Approved Domains (domain only — e.g. `localhost:3000`, not `http://localhost:3000/app/callback`)
- Create the authentication flow (start from `sign-up-or-in`, set to today's methods)
- Configure the JWT Template for profile claims
- Create tenants (list actual tenants found)
- Create roles and permissions (list actual roles found, per Application)
- Define custom attributes (`fusionauthId`, `freshlyMigrated`, `user.data` fields)
- Configure SSO connections per tenant or enable the SSO Setup Suite (if SSO in use)
- Configure social login providers (list actual providers found)

**Phase 2 — Code Changes** (~X–Y hours, 1 engineer)
Work through files in the order listed. Run a compile check after each group.

- Update environment variables in `.env.example` and CI config (15 min)
- Replace the FusionAuth provider / OIDC config with Descope and swap the login entry point (30 min)
- Rewrite the session helper / middleware to validate the `DS` cookie (30 min)
- Update protected routes and role checks (45 min)
- Replace Management API calls with Descope Management SDK calls behind server endpoints, or Widgets (varies)
- Update logout (15 min)
- Compile check and fix any type errors before proceeding

**Phase 3 — User Migration** (~1–3 hours, includes dry run)
Run against dev/staging first. Do not run against production until Phase 4 passes.

- (steps from the user & tenant migration section above)

**Phase 4 — Testing** (~30–45 minutes)

- Compile passes with zero errors
- Server starts, no crashes on startup
- Unauthenticated routes redirect to login correctly
- An imported user signs in with their existing password (one per hash scheme)
- User profile data appears (confirms the JWT Template is working)
- Role checks pass and fail as before
- Tenant/SSO routing works for at least one tenant
- Logout invalidates the session

**Phase 5 — Production Cutover**

- Run the production import, then a delta import of users changed since the export
- Switch the app to Descope in one step
- Re-point SCIM and any OIDC/SAML relying parties that used FusionAuth as their IdP
- Keep FusionAuth read-only (or live behind the JIT connector) for the agreed transition, then decommission the server, database, and search cluster — and delete the export

---

Total estimated engineering effort: **N–N hours** across N engineers.
Blocking dependencies: (list anything on the critical path — Descope console access, FusionAuth database access or support export, SCIM re-point, MFA re-enrollment comms.)

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
- Framework: [e.g., Next.js 15 + next-auth v4, Express + React]
- Language: [TypeScript / Python / Go / Java / C#]
- Package manager: [npm / yarn / pnpm / pip / etc.]
- FusionAuth integration style: [FusionAuth SDK + Hosted Backend / DPoP / generic OIDC library (kept or replaced) / custom form on /api/login]
- FusionAuth hosting: [Self-hosted vX.Y / FusionAuth Cloud]
- Migration goal: [Full cutover / Phased / Evaluating]

## Triage Answers
- Existing users: [Yes — N users / No — greenfield]
- FusionAuth tenants → Descope: [e.g. "Default → project; acme, globex → tenants"]
- Same-email duplicates across tenants: [N — merge rule: ...]
- Hash schemes: [e.g. salted-pbkdf2-hmac-sha256: N, bcrypt: N, salted-md5: N]
- Password strategy: [Import hashes / Import hashes + JIT for unsupported / Import without passwords / JIT via OIDC only]
- JIT transition length: [e.g. 3 months / none]
- Applications → Descope: [e.g. "one app → project"]
- Role mapping notes: [merged / prefixed]
- FusionAuth features in use: [comma-separated list]
- Zero-downtime required: [Yes / No]

## Files Inventory
_All files that need to change. Update status after each step._

| File | Change | Status |
|---|---|---|
| `src/main.tsx` | Replace FusionAuthProvider | ⬜ Pending |
| `server/auth.ts` | Rewrite session helper | ⬜ Pending |
| `server/roles.ts` | Update role checks | ⬜ Pending |

## Console Setup Checklist
- [ ] Descope project created — Project ID: (fill in when done)
- [ ] Approved Domains configured (domain only — e.g. `localhost:3000`, not `http://localhost:3000/app/callback`)
- [ ] Flow configured with today's sign-in methods
- [ ] JWT Template configured
- [ ] Tenants created: (list)
- [ ] Roles and permissions created: (list)
- [ ] Custom attributes defined: (list)
- [ ] SSO connections / SSO Setup Suite configured: (list)
- [ ] Social providers configured: (list providers)

## Decisions Log
_Non-obvious decisions made during migration — preserves rationale if context is lost._

_(none yet)_

## Current Phase
Phase 0 — Start the export path (not started)

## Next Action
Confirm database access or open the FusionAuth support ticket, then complete console setup per MIGRATION-PLAN.md before making any code changes.

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

> `Migration context: Next.js 15 + next-auth · Phase 2, step 3/8 · Next: rewrite server/auth.ts`

If this line can't be filled in accurately, re-read the files first.

**Rule 3 — Update `MIGRATION-STATE.md` immediately after each step.**

Mark the file done in the Files Inventory, update "Current Phase" and "Next Action", and
append any non-obvious decision to the Decisions Log. Do this before the next step.

---

## Pre-Generation Protocol (apply before writing any code)

Run before generating any import, wrapper type, or helper. Skipping produces code that
compiles but fails at runtime.

**1. Verify SDK exports before writing any import.**
When a Descope MCP is connected, use `docs_ask_question` (Descope MCP Server) or `ask-question-about-descope` (Docs MCP) to confirm the exact method name, option shape, and return type before writing any SDK call. This is faster and more reliable than reading type declarations. Do not write a method name and add a hedge like "verify the exact name" — just verify it.

When neither Descope MCP is connected: resolve the package's type declarations (`node_modules/<pkg>/dist/types/` or its `package.json` `types` field) and confirm the exact exported name and signature. For Go, run `go doc`. For Python, check the SDK stubs.

**Prefer local `node_modules/` over GitHub** when reading type declarations. Installed packages reflect the exact version in use. If the Descope package isn't installed yet, install it first, then read local type declarations. Only fall back to GitHub if the package can't be installed in the current environment.

This applies to **every SDK call you write**, not just the first import. Field names on
option objects, hook return shapes (`useDescope()` returns the SDK directly, not `{ sdk }`),
and subpath exports (`/client` vs root) differ just as often.

**1a. After rewriting any module, grep for remaining imports of the removed package.**

```bash
grep -rn "@fusionauth/\|fusionauth-client\|fusionauth_client\|FusionAuth/go-client\|io\.fusionauth\|FusionAuth\.Client\|providers/fusionauth\|FusionAuthClient" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.vue" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.php" --include="*.kt" \
  --include="*.java" --include="*.cs" --include="*.swift" .
```

Add remaining hits to the work list.

**2. Derive wrapper types from the actual return type.**
Read the function's declared return type and build the wrapper to match. FusionAuth's `userInfo`
(OIDC userinfo: `sub`, `email`, `given_name`, `roles`, …) and decoded access-token claims are flat;
Descope's `authInfo` and `useUser()` shapes differ and nest tenant data. Don't infer one from the
other.

**3. Check dependency versions before generating framework-specific code.**
For Next.js: `cookies()` and `headers()` from `next/headers` are synchronous in v14 and
async in v15. For `next-auth`: v4 and v5 (Auth.js) configure providers differently. Read
`package.json` (or `go.mod`, `requirements.txt`) first.

**4. When making a helper async, propagate to all callers immediately.**
In TypeScript, `async` on a shared utility silently breaks callers that omit `await`. Grep
for all call sites of the changed function and update them in the same pass. The cascade can
span 10–20 files.

**5. Verify published package versions before writing to `package.json` or running `npm install`.**
Don't reuse FusionAuth's version number or rely on training data for versions. Before writing any
install command:

```bash
npm view @descope/node-sdk version
npm view @descope/react-sdk version
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
- **Create one Descope project per environment.** If the team runs one FusionAuth instance per environment, or one tenant per environment, each environment becomes its own Descope project. Descope projects are configured independently; script repeatable setup with the Management SDK or the Descope Terraform provider (the natural successor to `kickstart.json`).

### 2. Get a Management Key (if needed)

Required for: user import, user management API, role/permission management, tenant operations,
SSO/SCIM configuration, access keys, Inbound Apps. Any migration with existing users needs one.

- Console → **Company Settings → Management Keys → + Management Key**
- Store as `DESCOPE_MANAGEMENT_KEY`. Treat like a secret — never expose client-side.

### 3. Choose or create a Flow, and pick the integration style

A Flow is the auth UI sequence. Reference it by Flow ID in the web component.

- Console → **Flows**
- The built-in **"sign-up-or-in"** flow handles email/password, OTP, and social login. Use it for most migrations, edited to match the methods FusionAuth offers today (if FusionAuth was password-first, make the Flow password-first).
- To customise: duplicate "sign-up-or-in", rename it, then edit in the visual builder.
- The Flow ID is in the URL when editing and in the flow list.
- There's a large Flow template library — check for an existing template before building a custom flow. See `references/flows-and-widgets.md` → Flows.
- MFA: add an MFA step to the Flow or embed MFA as a subflow. Descope manages MFA enrollment through Flows.

**Match the existing login model.** Use `AskUserQuestion` to confirm, then follow this tree:

```
How does the app sign in with FusionAuth today?
├── FusionAuth React/Vue/Angular SDK → hosted pages (startLogin / FusionAuthLoginButton)
│     → Descope-hosted login: Descope SDK with oidcConfig
│       (<AuthProvider projectId oidcConfig> + sdk.oidc.loginWithRedirect())
│     → or, if they want in-page login: embedded <Descope flowId="..."/>
├── Generic OIDC library (next-auth, openid-client, Spring, ASP.NET, authlib, AppAuth)
│     Keep the library  → repoint it at Descope as the OIDC provider (Federated OIDC App):
│                          issuer https://api.descope.com/<ProjectID>, client_id = Project ID,
│                          client_secret = a Descope Access Key
│     Adopt Descope SDK → Descope-hosted login (oidcConfig) or embedded Flow, plus SDK session validation
├── Custom login form posting to /api/login
│     → embedded <Descope flowId="..."/> (recommended), or the SDK's password API if the
│       form must stay exactly as is (consider Bring Your Own Screen first)
└── Mobile (AppAuth / FusionAuth Swift or Android SDK)
      → Descope Flow through the native SDK, or keep AppAuth pointed at Descope's OIDC endpoints
```

**Keeping the OIDC library** is the smallest code change for generic-OIDC apps: the redirect
round-trip, callback route, and session handling stay; only the issuer, client ID, secret, and claim
reads change. Verify the current Federated App setup and endpoints with the MCP
([OIDC Federated Applications](https://docs.descope.com/identity-federation/applications/oidc-apps)).
If the app's frontend calls its own API with scoped access tokens, use an Inbound App and Resource
instead. The trade-off: the app does not get Descope's client SDK helpers (`useSession`, Widgets) for
free; those can be added later.

**Adopting the Descope SDK** with `oidcConfig` keeps the same redirect UX FusionAuth's hosted pages
gave: the SDK redirects to the Descope-hosted page and back, and `sdk.oidc.logout({
post_logout_redirect_uri })` replaces FusionAuth's `/oauth2/logout`. Verify the `oidcConfig` options for
the user's SDK via the MCP ([React guide](https://docs.descope.com/getting-started/react/react-oidc)).

Ask whether FusionAuth runs behind a **custom domain**. With FusionAuth's Hosted Backend this is usually
a requirement (its cookies don't work cross-site); either way, plan the Descope custom domain before
cutover. Switching login models mid-migration changes routing, redirect handling, and session
bootstrapping all at once, so change the model only when the user explicitly asks.

### 4. Configure authentication methods

- Console → **Authentication** → select methods (Passwords, Email OTP, Magic Link, Social, SSO, Passkeys, etc.)
- **Passwords:** set the Descope password policy no stricter than FusionAuth's tenant policy, or imported users whose passwords don't meet it are pushed into a reset on change.
- For social providers: copy the client ID and secret from each FusionAuth Identity Provider (`GET /api/identity-provider`) into Descope, then add Descope's redirect URL in the provider's developer console. Check FusionAuth's gaming providers (Steam, Twitch, Xbox, Epic, Nintendo, Sony PSN) and HYPR against Descope's provider list before promising them — use a custom OAuth provider where Descope has no built-in one.
- For enterprise SSO (SAML/OIDC): to configure SSO for a specific tenant or to enable the SSO Setup Suite for tenant-admin self-serve, go to Console → **Tenants**, select the tenant, and click **Tenant Settings**.

### 5. Configure Approved Domains (local dev and production)

Console → **Project Settings → General → Security → Approved Domains**.

Descope validates redirect URLs against this domain list — **not** full redirect URIs the way
FusionAuth's application "Authorized redirect URLs" do. Enter **domain only**: no `http://` or
`https://`, no path.

- Local dev: `localhost:3000` (include port)
- Production: `myapp.com` or `app.myapp.com`

**Do not** carry over FusionAuth redirect URLs like `http://localhost:3000/app/callback` or
`http://localhost:3000/api/auth/callback/fusionauth`. If the app keeps a generic OIDC library, its
callback URL is registered on the Descope Federated App instead. Note that FusionAuth supports
wildcard redirect URLs — confirm how any wildcard entry should be represented before assuming a
one-to-one copy.

### 6. Configure a JWT Template (almost always needed)

FusionAuth's access token carries `email`, `email_verified`, and `preferred_username`, plus whatever a
JWT populate lambda adds. Descope's session token carries none of those by default.

- Console → **Project Settings → JWT Templates**
- Add claims: `{"email": "{{user.email}}", "name": "{{user.name}}"}` and any others the app reads.
  To confirm the exact placeholder syntax in any given project rather than trusting memory, read the
  built-in **"Default OIDC compliant User JWT"** template that ships with every project — it already
  uses `{{user.email}}`.
- **Set `authSchema: "default"` on the template.** Without it, the `tenants`/`roles`/`permissions`
  claims are omitted from the token even if the app otherwise looks correctly configured.
- Before saving, validate the template with the `ValidateJwtTemplate` operation (dry-run) — either via
  the Descope MCP if available, or the equivalent Console preview.
- Apply the template to your project. Without this step, any code reading `token.email` gets
  `undefined` after migration.
- Port each **JWT populate lambda** claim here (or into a Flow custom-claims action). Read the lambda
  source — `jwt.someClaim = user.data.someField` becomes a template claim reading the matching custom
  attribute. See Step 3 → *Lambdas*.

### 7. Create roles and permissions in the Console (if using RBAC)

Descope roles are referenced by **name**, not by ID. They must be created before the import assigns
them.

- Console → **Authorization → RBAC → + Role**
- List roles per FusionAuth Application (`GET /api/application` returns each Application's `roles`).
  If two Applications define the same role name with different meanings, prefix or rename before
  creating (e.g. `billing:admin`). Record the mapping in the Decisions Log.
- FusionAuth roles have no permissions underneath them. If the app only checks role names, create
  roles alone; add Descope permissions only if the team wants finer-grained checks later.
- FusionAuth's `superRole` flag and default roles (`isDefault`, assigned on registration) become a
  documentation note and a Flow step that assigns the default role on sign-up.

### 8. Define custom attributes

- User custom attributes: Console → **Users → Custom Attributes tab**
- Tenant custom attributes: Console → **Tenants → Custom Attributes tab → Create Attribute**
- Attributes must exist in the Console schema **before** any import or SDK call sets them. Define at
  least `fusionauthId` (string) and, if JIT is used, `freshlyMigrated` (boolean), plus one attribute
  per `user.data` field the app reads. Nested `user.data` objects need a flattening decision.
- Values must match the declared type: send `true`, not `"true"`, for a boolean.

### 9. Env var summary


| Variable                         | Where to get it                     | Used by                                     |
| -------------------------------- | ----------------------------------- | ------------------------------------------- |
| `DESCOPE_PROJECT_ID`             | Console → Project Settings          | All server-side SDKs                        |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value as above                 | Next.js `AuthProvider` (client-side)        |
| `DESCOPE_MANAGEMENT_KEY`         | Console → Company Settings → Management Keys | Management SDK, user import, SSO/SCIM |
| *(OIDC library kept)* client secret | Console → Access Keys, or the Inbound App | The app's OIDC client configuration |


### 10. Consider Widgets for management UI

Before migrating any app-built screen that calls the FusionAuth Management API, or any link to
FusionAuth's `/account` pages, ask whether a Descope Widget or the SSO Setup Suite covers the use
case. See `references/flows-and-widgets.md` → *Mapping FusionAuth's Self-Service and Admin Surfaces*.

**Enumerate the project's actual widgets before referencing any `widgetId` in code.** Not every
widget is provisioned by default in a fresh project, and the SDK exports and types every widget
component regardless — so a missing widget is invisible to TypeScript and shows up only at runtime.
See Step 4 → *A widgetId with no widget behind it fails as an authorization error*.

### 11. If the Descope MCP Server is connected, let it do the console setup it can — and read state first

The Descope MCP server automates a real share of this checklist, but not all of it, and writes require
explicit elevation. Before manually clicking through the Console:

- **Read current state before creating anything.** A project may already have the built-in
  `sign-up-or-in` flow, a `Tenant Admin` role, and several default widgets. Use the read operations
  first (listing flows, widgets, roles, permissions, users) so planned "create" steps don't duplicate
  what already exists.
- **Automatable:** JWT templates (create, plus a dry-run validate operation before saving), tenants
  (including custom attributes), roles and permissions, and reading current project state.
- **Not exposed via the management API/MCP:** Approved Domains, and attaching a JWT Template to
  Session Management's Token Format setting. These stay Console-only clicks.
- **Writes require elevation.** Every mutating operation needs an explicit user confirmation naming
  the exact operation and target before it runs — batch related confirmations together (e.g. "create
  these 4 roles") rather than asking once per call. Follow Part 1 → *Changes through the Descope MCP
  Server* for every write.
- **The bulk user import is not an MCP job.** Run it as a script with the Management Key, with
  dry-run mode, so it can be re-run and audited. Never paste password hashes into a chat or an MCP call.
- **Permissions may gate this entirely.** The Management Key or role connected to the MCP may not have
  write access to everything — confirm what's actually writable before promising to automate a step.

**After completing console setup:** Update `MIGRATION-STATE.md` — check off each completed
item in the Console Setup Checklist, record the Project ID in the file, and set Next Action
to the first code change step.

---

## Step 2: Framework-Specific Migration

FusionAuth apps fall into four integration families:

- **FusionAuth frontend SDKs**: `@fusionauth/react-sdk`, `@fusionauth/vue-sdk`, `@fusionauth/angular-sdk`. They hold auth state, start the hosted login, and (by default) rely on a Hosted Backend that keeps tokens in `app.*` cookies.
- **Generic OIDC libraries**: `next-auth` / Auth.js, `openid-client`, Passport, Spring Security, ASP.NET, `authlib`, `go-oidc`, AppAuth. Configured with FusionAuth's issuer, client ID, and secret.
- **Management API clients**: `FusionAuthClient` in TypeScript, Python, Go, Java, .NET, Ruby, PHP. Used for admin operations, and sometimes for login (`client.login(...)`) or token validation (`validateJWT`).
- **Mobile**: FusionAuth's Swift and Android SDKs (`AuthorizationManager`), or AppAuth-based libraries.

The recipes below map each to its Descope target.

> The framework recipes below list the FusionAuth idioms that need mapping. Confirm the exact Descope SDK calls via the Descope MCP or local type declarations before generating any code. Do not ship code from these lists without verification.

Read `references/implementation-nuances.md` in two passes before writing any code:

1. **General Insights** (always) — covers architecture, feature mapping, user export, and common gotchas that apply to every migration regardless of framework.
2. **Framework section** (use the file's ToC and `offset` to jump directly) — read only the section matching the user's stack.

When a new framework is added to the file, add it to this list.

### Common FusionAuth idioms to map (all frameworks)

- `FusionAuthProvider` / `app.use(FusionAuthVuePlugin, …)` / `FusionAuthModule.forRoot()` → Descope `AuthProvider` (or the framework's equivalent provider), configured with the Project ID instead of `serverUrl` + `clientId` + `redirectUri`
- `startLogin()` / `FusionAuthLoginButton` / `<fa-login>` → `sdk.oidc.loginWithRedirect()` with `oidcConfig` (hosted), or an embedded `<Descope flowId>` route
- `startRegister()` / `FusionAuthRegisterButton` → the same Flow (`sign-up-or-in`), or a sign-up Flow
- `startLogout()` / `FusionAuthLogoutButton` / navigation to `/oauth2/logout` → `sdk.oidc.logout(...)` (hosted) or `sdk.logout()` — see Step 4 → *Logout*
- `manageAccount()` / `FusionAuthAccountButton` / links to `/account/` → User Profile Widget page
- `useFusionAuth().isLoggedIn` / `RequireAuth` / `Unauthenticated` / `RequireAnonymous` → `useSession()`'s `isAuthenticated`, with conditional rendering
- `RequireAuth withRole="admin"` → a role check against the Descope session (client-side gating only; always re-check on the server)
- `useFusionAuth().userInfo` / `fetchUserInfo()` / `/app/me` → `useUser()`
- `refreshToken()` / `shouldAutoRefresh` / `/app/refresh` → Descope SDK auto-refresh (remove the plumbing)
- `useDpop` / `dpopFetch` → normal `fetch` with the Descope session token in `Authorization: Bearer`, or rely on the `DS` cookie for same-site APIs
- Hosted Backend routes in the app's own server (`/app/login`, `/app/callback`, `/app/refresh`, `/app/me`, `/app/logout`, e.g. from `fusionauth-javascript-sdk-express`) → removed
- Backend reads of the `app.at` cookie or `Authorization: Bearer` + JWKS / HMAC verification → Descope `validateSession()` on the `DS` cookie (or Bearer token)
- `claims.roles.includes(...)` → the SDK's role validation helpers; `claims.applicationId` / `aud` checks → removed, or a JWT Template `aud` claim plus `audience` validation
- `FusionAuthClient` admin calls (`createUser`, `register`, `updateRegistration`, `searchUsersByQuery`, `createGroupMembers`, `createIdentityProvider`, …) → Descope Management SDK calls behind server endpoints, or a Widget
- `client.login({ loginId, password, applicationId })` from a custom form → embedded Flow (recommended), or the Descope SDK's password sign-in
- **App code that let the browser hit admin endpoints through a proxy** — some apps expose thin routes that forward to `FusionAuthClient` with the API key. Audit each one: a Descope Management Key gets the same server-only treatment, and many of these routes are better replaced by a Widget acting as the logged-in user.

### Frontend SDKs

> **Read the session the framework-native way — never hand-parse the JWT on the client.** On
> front-end pages and components, get auth state from the Descope hooks: `useSession()` for the
> session token and auth status, `useUser()` for the user profile, and `useDescope()` for actions
> like `logout()`. Do **not** manually decode the session token in client code. FusionAuth apps often
> read the JavaScript-visible `app.idt` cookie to show the user's name — that habit should not carry
> over. Server-side session *validation* belongs only in backend routes, middleware, and API handlers.

#### React

*FusionAuth SDK: `@fusionauth/react-sdk` → Descope `@descope/react-sdk`*

- `<FusionAuthProvider serverUrl clientId redirectUri scope shouldAutoRefresh shouldAutoFetchUserInfo>` → `<AuthProvider projectId>` (add `oidcConfig` for hosted login)
- `useFusionAuth()` → `useSession()` (`isAuthenticated`, `isSessionLoading`, `sessionToken`) + `useUser()` (`user`, `isUserLoading`) + `useDescope()` (actions)
- `startLogin()` → `useDescope().oidc.loginWithRedirect({ redirect_uri })`, or route to an embedded `<Descope flowId="sign-up-or-in" onSuccess>`
- `RequireAuth` / `Unauthenticated` → conditional rendering on `isAuthenticated`; `withRole` → a role check helper over the session
- `withFusionAuth` HOC → a small wrapper using the Descope hooks
- `onRedirect(state)` → handle the post-login destination in the Flow's `onSuccess` or after `oidc` callback handling
- **Descope's hooks return a new object identity every render.** Deriving a value from `useUser()`/`useSession()` inline into a `useEffect` dependency array causes an infinite render loop. Depend on primitives, not the object.
- See `references/implementation-nuances.md` → React.

#### Next.js

*FusionAuth integration: `next-auth` (`next-auth/providers/fusionauth`) or the React SDK with `nextCookieAdapter` → Descope `@descope/nextjs-sdk` + `@descope/node-sdk`, or keep `next-auth` with Descope as the OIDC provider*

Ask which way first — it is the biggest fork for Next.js:

- **Keep `next-auth`** (smallest change): replace the FusionAuth provider in `[...nextauth]` with a generic OIDC provider (or a Descope provider, if the installed Auth.js version ships one — check `node_modules`) pointed at `https://api.descope.com/<ProjectID>`, with the Project ID as client ID and a Descope Access Key as the secret. `getServerSession()` / `auth()` / `useSession()` from `next-auth` stay. Update the `jwt` and `session` callbacks, which usually copy `roles` and `tid` off the FusionAuth token. Sessions still live in the `next-auth` cookie, not `DS`.
- **Adopt `@descope/nextjs-sdk`**: `SessionProvider` from `next-auth/react` → Descope `AuthProvider` (needs `NEXT_PUBLIC_` Project ID); `getServerSession(authOptions)` / `auth()` → `session()` from `@descope/nextjs-sdk/server`; `withAuth` / `middleware.ts` from `next-auth` → Descope `authMiddleware(options)`; `signIn('fusionauth')` → hosted login or an embedded Flow page; `signOut()` → Descope logout. Remove `NEXTAUTH_SECRET` / `AUTH_SECRET` and the `[...nextauth]` route.
- **Exclude API routes from Descope's middleware matcher.** Descope's documented matcher includes `/(api|trpc)(.*)`; an unauthenticated `fetch()` to a matched API route gets a 307 redirect to sign-in instead of a 401. Let route handlers validate `session()` and return their own 401.
- **Client vs. server session access** — `session()` from `@descope/nextjs-sdk/server` is server-only; `useSession()`/`useUser()` from `@descope/nextjs-sdk/client` are client-only.
- **The middleware gates routes; it doesn't guarantee a session.** Always null-check `session()` and redirect.
- See `references/implementation-nuances.md` → Next.js.

#### Vue

*FusionAuth SDK: `@fusionauth/vue-sdk` → Descope `@descope/vue-sdk`*

- `app.use(FusionAuthVuePlugin, config)` / `createFusionAuth(config)` → Descope Vue plugin with `projectId`
- `useFusionAuth()` (`isLoggedIn`, `userInfo`, `startLogin`, `startLogout`) → Descope Vue composables for session and user
- `RequireAuth` (`:with-role`) / `RequireAnonymous` → `v-if` on the Descope session state, plus a role check
- Nuxt (`nuxtUseCookie`) → verify Descope's current Nuxt guidance via the MCP
- Remove `@fusionauth/vue-sdk/dist/style.css`
- No dedicated recipe yet — follow the React patterns and verify each method against docs

#### Angular

*FusionAuth SDK: `@fusionauth/angular-sdk` → Descope `@descope/angular-sdk`*

- `FusionAuthModule.forRoot({...})` → Descope Angular module/provider with the Project ID
- `FusionAuthService` (`isLoggedIn()`, `getUserInfoObservable()`, `startLogin()`, `logout()`) → Descope Angular SDK session/user services
- `<fa-login>` / `<fa-logout>` / `<fa-register>` → Descope login (hosted or the Flow component) and logout
- No dedicated recipe yet — follow the React patterns and verify each method against docs

#### Vanilla JS / other SPAs with a generic OIDC client

*FusionAuth: `oidc-client-ts`, `@auth0/auth0-spa-js`-style PKCE helpers, or hand-rolled PKCE → Descope `@descope/web-js-sdk` + `@descope/web-component`, or keep the OIDC client pointed at Descope*

- Keep the client: change `authority`, `client_id`, and scopes; verify the Descope issuer and discovery URL via the MCP
- Or adopt `@descope/web-js-sdk` (`getSessionToken()`, `refresh()`, `logout()`) with `<descope-wc project-id flow-id>` for login

### Backend SDKs

#### Node.js

*FusionAuth: `@fusionauth/typescript-client`, `jose` / `jsonwebtoken` against FusionAuth JWKS, Passport/openid-client → Descope `@descope/node-sdk`*

- Token validation (`jwtVerify(token, createRemoteJWKSet(...))`, `jwt.verify(token, secret)`, `client.validateJWT(token)`) → `descopeClient.validateSession(sessionToken)` against the `DS` cookie or Bearer token; parse the cookie yourself in Express
- Role checks on `payload.roles` → `descopeClient.validateRoles(authInfo, [...])` (or the tenant variant); confirm any-of vs. all-of semantics — FusionAuth SDK's `withRole` is any-of
- `new FusionAuthClient(apiKey, url)` admin calls → `DescopeClient({ projectId, managementKey })` + `management.user.*`, `management.tenant.*`, `management.role.*`
- Passport `OIDCStrategy` / `openid-client` → keep and repoint at Descope, or replace with the Descope SDK
- Hosted Backend routes (`fusionauth-javascript-sdk-express`) → delete

#### Python

*FusionAuth: `fusionauth-client` (`FusionAuthClient`), `authlib` / `PyJWT` → Descope `descope` Python SDK*

- `PyJWT` / `authlib` JWKS validation → `descope_client.validate_session(session_token=...)` in a Flask decorator, FastAPI dependency, or Django middleware
- `FusionAuthClient(api_key, url)` → `DescopeClient(project_id=..., management_key=...)` + `descope_client.mgmt.user.*`
- `authlib` OAuth client registered against FusionAuth → keep and repoint, or replace

#### Go

*FusionAuth: `github.com/FusionAuth/go-client/pkg/fusionauth`, `go-oidc` / `golang-jwt` → Descope `github.com/descope/go-sdk`*

- `fusionauth.NewClient(httpClient, baseURL, apiKey)` → `client.NewWithConfig(&client.Config{ProjectID: ..., ManagementKey: ...})`
- `go-oidc` verifier / `golang-jwt` parsing → `descopeClient.Auth.ValidateSessionWithToken(ctx, token)`, which returns `(bool, *descope.Token, error)`
- Role checks → Descope role validation helpers on the returned token

#### Java / Kotlin (JVM)

*FusionAuth: `io.fusionauth:fusionauth-java-client`, Spring Security OAuth2 → Descope `descope-java`, or Spring Security pointed at Descope*

- Spring Boot apps usually configure `spring.security.oauth2.client.provider.fusionauth.issuer-uri` and/or `spring.security.oauth2.resourceserver.jwt.issuer-uri`. Keeping Spring Security is a config change: point `issuer-uri` at Descope, update the client registration, and change the role mapping (Spring's `JwtGrantedAuthoritiesConverter` reading `roles`; Descope nests tenant roles under `tenants`)
- Or replace with `authenticationService.validateSessionWithToken(sessionToken)` from `descope-java`
- `io.fusionauth.client.FusionAuthClient` admin calls → Descope Java management services
- Verify against the [Descope Java SDK](https://github.com/descope/descope-java)

#### .NET / C#

*FusionAuth: `FusionAuth.Client`, ASP.NET `AddOpenIdConnect` / `AddJwtBearer` → Descope `descope-dotnet`, or ASP.NET pointed at Descope*

- `options.Authority = "https://auth.example.com"` (FusionAuth) with `options.Audience = "<application id>"` → Descope's issuer; drop `Audience` unless a JWT Template adds `aud`
- `RoleClaimType = "roles"` → Descope's role claim shape (top-level for project roles, under `tenants` for tenant roles)
- `FusionAuthSyncClient` / `FusionAuthClient` admin calls → Descope .NET management APIs
- Verify against the [Descope .NET SDK](https://github.com/descope/descope-dotnet)

#### Ruby / PHP

*FusionAuth: `fusionauth_client` gem, `fusionauth/fusionauth-client` package, OmniAuth / League OAuth2 → Descope Ruby SDK, or keep the OAuth library pointed at Descope*

- Descope has a [Ruby SDK](https://github.com/descope/descope-ruby-sdk). For PHP, verify current SDK support via the MCP; a standards-based JWT library validating against Descope's JWKS is the fallback
- OmniAuth / League OAuth2 configured for FusionAuth → repoint at Descope's issuer

### Mobile SDKs

#### iOS (Swift)

*FusionAuth: `fusionauth-swift-sdk` (`AuthorizationManager`) or AppAuth-iOS → Descope `descope-swift`*

- `AuthorizationManager.instance.initialize(...)` and its login/logout/refresh calls → Descope Swift SDK flows and session APIs
- AppAuth configured with the FusionAuth issuer → keep and repoint at Descope's OIDC endpoints, or adopt the Descope SDK
- Redirect URI schemes registered on the FusionAuth Application must be re-registered for Descope
- Verify against the [Descope Swift SDK](https://github.com/descope/swift-sdk)

#### Android (Kotlin)

*FusionAuth: `io.fusionauth:fusionauth-android-sdk` (`AuthorizationManager.initialize(AuthorizationConfiguration(...))`) or AppAuth-Android → Descope `descope-kotlin`*

- `AuthorizationManager` login/logout/fresh-token calls → Descope Kotlin SDK flows and session APIs
- Manifest redirect intent filters for the FusionAuth redirect URI → Descope's
- Verify against the [Descope Android/Kotlin SDK](https://github.com/descope/descope-kotlin)

#### React Native / Flutter

*FusionAuth: `react-native-app-auth` / `flutter_appauth` → Descope `@descope/react-native-sdk` / `descope-flutter`*

- FusionAuth has no React Native or Flutter SDK; its quickstarts use AppAuth wrappers. Repoint them at Descope's OIDC endpoints, or adopt the Descope SDK to run Flows natively
- Verify against the [Descope React Native SDK](https://github.com/descope/descope-react-native) / [Descope Flutter SDK](https://github.com/descope/descope-flutter)

**After completing framework code changes:** Update `MIGRATION-STATE.md` — mark each
modified file as Done in the Files Inventory, update Current Phase and Next Action, and
log any non-obvious decisions made.

---

## Step 2.5: Non-Code File Updates

Scan for FusionAuth references in non-code files after updating source files.

### `.env.example` / `.env.template` / `.env.sample`

```
# REMOVE (names vary by app — use what search 5 found)
FUSIONAUTH_URL=
FUSIONAUTH_ISSUER=
FUSIONAUTH_CLIENT_ID=
FUSIONAUTH_CLIENT_SECRET=
FUSIONAUTH_API_KEY=
FUSIONAUTH_TENANT_ID=
FUSIONAUTH_REDIRECT_URI=
AUTH_FUSIONAUTH_ID=
AUTH_FUSIONAUTH_SECRET=
AUTH_FUSIONAUTH_ISSUER=

# ADD
DESCOPE_PROJECT_ID=             # Console → Project Settings
NEXT_PUBLIC_DESCOPE_PROJECT_ID= # Next.js / frontend — same value as above
DESCOPE_MANAGEMENT_KEY=         # Console → Company Settings → Management Keys (replaces FUSIONAUTH_API_KEY for admin APIs)
```

Run `grep -ri "FUSIONAUTH"` to find all env var references — `.env.example`, Docker, CI, shell
scripts, Helm values, `appsettings*.json`, `application.yml`.

### README / docs

Search all `.md` files for FusionAuth references. At minimum, update:

- **Setup section** — replace "start FusionAuth with docker compose / run kickstart" with Descope Console setup steps
- **Environment variables section** — reflect the reduced env var set
- **Run instructions** — the local FusionAuth container (port 9011) is no longer needed
- **Auth flow diagrams or descriptions** — update to reflect Descope

### Docker / CI / infrastructure

- `docker-compose.yml`: remove the `fusionauth` service (`fusionauth/fusionauth-app`), its database
  and search containers if they existed only for FusionAuth, and the `kickstart` volume — **after**
  the export is complete and FusionAuth is no longer needed for JIT
- Helm charts / Kubernetes manifests for FusionAuth: schedule removal for decommission, not for the
  code change
- `.github/workflows/` and other CI: remove FusionAuth service containers used by integration tests,
  and replace them with a Descope test project or mocked session validation

### Kickstart / Terraform

`kickstart.json` and FusionAuth Terraform (`FusionAuth/fusionauth` provider) describe the
configuration being migrated. Use them as the inventory for Console setup, then retire them. If the
team wants configuration as code going forward, the
[Descope Terraform provider](https://registry.terraform.io/providers/descope/descope) is the
replacement (see the `descope-terraform` skill). Leaving FusionAuth Terraform in place means the next
`terraform apply` recreates what the migration retired.

### Themes and email templates

`.ftl` FreeMarker templates in the repo (exported themes, email templates) are not code to port. Use
them as the visual and copy reference for Descope Flow screens, Styles, and Messaging Templates, then
delete them.

### Mobile project files

- iOS: update URL schemes and associated domains for the Descope redirect
- Android: replace the FusionAuth redirect intent filters and any `fusionauth` config resources

### Setup / bootstrap scripts

When the migration includes a setup or seed script, split it into two parts:

1. **Console setup** (cannot be scripted): Flows, email templates, MFA configuration, branding/Styles, SSO Setup Suite — configure these in the Descope Console. Represent them as a Phase 1 checklist in `MIGRATION-PLAN.md`.
2. **SDK automation** (can be scripted): role creation (`management.role.create()`), tenant creation, access key provisioning, SSO/SCIM config. Preserve these as a script using the Descope Management SDK, or as Terraform.

**After completing non-code file updates:** Update `MIGRATION-STATE.md` — mark env files,
README, CI config, and infrastructure files done in the Files Inventory, and advance Next Action.

---

## Step 3: Feature Migration Mapping

For each FusionAuth feature confirmed in triage, write a short paragraph: what it accomplishes, the
best Descope approach for that goal, what's different, and what action is required. Reason about
intent, not just the API surface — the best approach may be a Flow, Widget, SSO Setup Suite, Inbound
App, Console configuration, or tenant configuration rather than a direct SDK equivalent.
Only recommend SDK/API code when programmatic control is genuinely required, and verify every method
name against the Descope MCP server before writing it. Include only confirmed features.

### User & Tenant Data → Import with Password Hashes (plus JIT where needed)

This is usually the first thing to settle, because it drives the cutover plan. Write the migration
script for the user's setup rather than handing them a generic tool. Descope's
[descope-migration](https://github.com/descope/descope-migration) repo has **no FusionAuth module**;
its other providers are a reference for request shapes only. There is no FusionAuth page in Descope's
[migration docs](https://docs.descope.com/migrate) at the time of writing — check before linking to
one. **Never tell the user to open a guide you have not confirmed exists.** The Descope
[custom migration guide](https://docs.descope.com/migrate/custom) documents the import format,
including password hashes.

**Path 1 — Full migration with password hashes (recommended default).** Export from the FusionAuth
database (self-hosted) or a support-provided database export (Cloud), and create the matching objects
in Descope in dependency order: **tenants → permissions → roles → users**. Users carry their hash in
`hashedPassword`, so they keep their password. Things the script must get right:

- Read the hash from the **`identities`** table (current schema), joined to `users`, per user — each row has its own `encryption_scheme`, `factor`, `salt`, and `password`.
- Map each scheme to Descope's format (see the table in `references/implementation-nuances.md` → *Password hash mapping*). Skip `hashedPassword` for schemes with no Descope equivalent and set `freshlyMigrated` instead.
- Build each user's roles from **registrations** for the Application(s) being migrated (`user_registrations` + `user_registrations_application_roles`) **plus** roles granted through **groups** (`group_members` + `group_application_roles`) — group roles count only for Applications the user is registered for.
- Map FusionAuth tenants per the triage decision. For B2B tenant → Descope tenant, merge same-email users by the agreed rule and give the merged user one membership per tenant.
- Import inactive (`active = false`) users as disabled; skip phone numbers that aren't E.164; set `verifiedEmail` from FusionAuth's `verified` flag.
- Include the TOTP `seed` (base32) for users with an authenticator method, once the export's secret encoding is confirmed.
- Use `createdTime` to preserve `insert_instant` where the batch endpoint supports it.

**Path 2 — JIT migration with a Generic HTTP Connector.** For users whose hashes didn't import, or
when the export is delayed, or as the whole strategy if the team prefers. The Descope Flow collects
email and password, a
[Generic HTTP Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http)
calls FusionAuth's Login API (`POST {FUSIONAUTH_URL}/api/login` with `loginId`, `password`, and
`applicationId`, authenticated with an API key limited to that endpoint), and on success the Flow
creates or updates the Descope user and stores the password. Treat **200** as success; **202** (not
registered for the application), **203** (password change required), **212** (email not verified),
**213** (registration not verified), and **242** (MFA required) also mean the password was correct —
decide per code whether to accept it. **404** means unknown user or wrong password. For users already
imported (`freshlyMigrated`), the Flow signs them in with OTP or magic link and stores the password
with **Update Password** (not Sign Up / Password), then clears the flag.

**Path 3 — JIT migration with FusionAuth as a custom OIDC provider.** Configure FusionAuth as a
[custom OAuth/OIDC provider](https://docs.descope.com/auth-methods/oauth/providers/custom-provider)
in Descope using a FusionAuth Application's client ID, secret, and the tenant's discovery endpoints,
then add an OAuth sign-in step to the Flow. Users authenticate through FusionAuth's hosted login —
MFA included — and Descope provisions them from the returned ID token claims. Add a Flow
[condition](https://docs.descope.com/flows/conditions) that routes already-provisioned users to
Descope-native auth.

Both JIT paths keep FusionAuth running for a transition period the user chooses (recommend at least a
few months when passwords matter), and both require **dual token validation** in the backend if
FusionAuth sessions must keep working during the transition (see Step 4).

The API side of the export (tenants, applications and their roles, groups, identity providers,
lambdas, webhooks) goes through the Management API with the raw API key in `Authorization` (no
`Bearer`) and `X-FusionAuth-TenantId` where needed. User *profiles* can also come from
`POST /api/user/search`, but hashes cannot, so for most migrations the database is the single source
for users. Import with `POST /v1/mgmt/user/create/batch`. See
`references/implementation-nuances.md` → **Migrating users and tenants** for the queries, endpoints,
field mapping, and data-quality checks.

**Effort: Low–Medium** for a single-tenant hash import on a clean data set; **Medium–High** with
multi-tenant merges, mixed schemes, or JIT, which adds Flow engineering and a transition period.

### Tenants → Descope Projects or Tenants

A FusionAuth tenant is an isolated user pool with its own issuer, keys, password and MFA policy,
email settings, and themes. Decide what each one becomes before anything else:

| FusionAuth tenant used as | Descope | What moves with it |
| --- | --- | --- |
| An environment | **Project** | Everything; repeat Console setup per project |
| A B2B customer | **Tenant** | Name, custom attributes, SSO, email domains; tenant-level password and session settings; per-tenant MFA becomes a Flow condition on a tenant attribute |
| A separate product/brand | **Project** | Everything; users don't overlap |

For B2B tenants, compare what FusionAuth let each tenant customize with what a Descope tenant
supports. Per-tenant **themes** and **email templates** become Flow conditions or separate Flows
keyed on the tenant; per-tenant **issuer and signing keys** have no equivalent (one project, one
issuer); per-tenant **connectors** and **identity providers** become tenant SSO configuration.

The request-time difference: FusionAuth puts the tenant ID in the `tid` claim and the token is only
ever for one tenant. Descope exposes the active tenant as `dct` and all memberships under `tenants`.
Prefer SDK helpers such as `validateTenantRoles(...)` over reading claims by hand.

**Effort: Low** when tenants are environments; **Medium–High** when they are customers, because of
the merge rule and per-tenant settings.

### Applications → Project, Federated Apps, Inbound Apps, or Nothing

A FusionAuth Application is an OAuth client: it has a client ID (the Application ID), a secret,
redirect URLs, enabled grants, its own roles, and optionally its own login theme, MFA policy, and
JWT settings. The `aud` and `applicationId` claims identify it.

| What the Applications represent | Descope approach |
| --- | --- |
| One app (the common case) | The Descope **Project** itself; nothing to create |
| Several surfaces of one product sharing users (web, admin, mobile) | One project; a role or custom attribute for any per-surface access rule; **Federated Apps** for those that keep a generic OIDC client |
| Separate products with separate users | Separate **Projects** |
| Third-party or partner clients needing scoped API access | **Inbound Apps** + Resources |
| Applications used only for client credentials | See *Entities and M2M* |

**Registrations** are the part that needs a decision. In FusionAuth a user can exist without being
registered for an Application, and FusionAuth then authenticates them without authorizing them (the
Login API returns 202, the token has no roles). If the app relies on that — "only users registered
for the admin app may sign in to it" — model it as a role (`admin-app-user`), a tenant, or a Flow
condition that denies sign-in without it. If every user is registered for the one Application, there
is nothing to model.

**Effort: Low** for one Application; **Medium** for several, mostly in the decision.

### Roles and Groups → Descope RBAC

| FusionAuth | Descope |
| --- | --- |
| Application role (`name`, `isDefault`, `isSuperRole`) | Role (referenced by name) |
| Same role name in two Applications | Merge, or prefix (`billing:admin`) — Descope role names are project-wide |
| Default role on registration | Flow step assigning the role on sign-up, or tenant default roles |
| Registration roles | Project-level roles (single tenant) or tenant roles (B2B) |
| Group with application roles | Roles assigned to the user directly (flatten at import) |
| Group membership read by the app or put in the token by a lambda | Roles, or a custom attribute holding group names |
| `roles` claim | `roles` (project-level) or `tenants.<id>.roles` |
| Fine-grained permissions | FusionAuth has none on roles (Entity Types have permissions — see *Entities*); create Descope permissions only if wanted |

FusionAuth groups have one more behavior to preserve: group roles apply only to Applications the user
is registered for. Flatten with that rule, not by giving every member every group role.

**Effort: Low–Medium.**

### Hosted Login Pages and Themes → Descope Flows + Styles

| FusionAuth | Descope |
| --- | --- |
| Hosted login page (`/oauth2/authorize`) | Descope-hosted login (`oidcConfig`) or embedded Flow |
| Theme (FreeMarker templates + CSS) | Flow Screens + **Styles** |
| Simple theme editor | Styles |
| Basic self-service registration | Sign-up Flow |
| Advanced Registration Forms (multi-step, custom fields) | Flow Screens + custom attributes |
| Password, magic link (passwordless), passkeys | Passwords, Magic Link / OTP, Passkeys |
| Social IdPs | Descope OAuth providers (custom OAuth for any Descope lacks) |
| Localization (`messages` properties per locale) | Flow localization |
| Email templates (FreeMarker) | Messaging Templates |
| Custom login form on `/api/login` | Embedded Flow (recommended), or SDK password methods / BYOS |

Two notes. First, a heavily customized FreeMarker theme can be matched closely with Styles, but if
the brand requires pixel-level control, Descope's Bring Your Own Screen (BYOS) lets the app render its
own components while the Flow runs the logic. Second, check the tenant's **login identifier** setting:
if users sign in with a **username**, the Descope `loginId` must be the username (email can be stored
alongside).

**Effort: Low–Medium**, higher with Advanced Registration Forms or a theme the brand team cares about.

### Lambdas → JWT Templates, Flow Steps, Connectors, and Attribute Mapping

Lambdas are FusionAuth's extension point. Read each lambda's source (`GET /api/lambda`) before
mapping it — the type says *when* it runs, the body says *what* it does.

| FusionAuth lambda | Descope approach |
| --- | --- |
| JWT populate / Id Token populate / UserInfo populate | **JWT Template** claims, or a Flow custom-claims action |
| Client credentials JWT populate | JWT Template on the M2M token / Inbound App |
| OIDC / SAML v2 reconcile | SSO attribute mapping and group-to-role mapping on the tenant; Flow step after SSO for anything else |
| Social provider reconcile (Google, Apple, Facebook, …) | OAuth provider attribute mapping; Flow step for anything else |
| External JWT / LDAP connector reconcile | Generic HTTP Connector step |
| Login validation (Enterprise) | Condition or Connector after authentication, with a deny branch |
| MFA requirement | Flow condition deciding whether the MFA step runs |
| Self-service registration validation | Scriptlet or Connector + Condition before user creation |
| SAML v2 response populate (FusionAuth as SAML IdP) | Federated SAML App attribute mapping |
| SCIM request/response converters | Descope SCIM mapping — confirm coverage per attribute |

Three things to pin down for each lambda: whether it **rejects** (that's a security control),
whether it calls out over HTTP (that becomes a Connector with a timeout and fail behavior), and which
claims or user fields it writes (each must reappear in a JWT Template or a custom attribute).

**Effort: Low** for populate lambdas that copy fields; **Medium–High** for validation lambdas.

### Identity Providers → Descope Tenant SSO and OAuth Providers

| FusionAuth | Descope |
| --- | --- |
| OpenID Connect IdP (enterprise) | Tenant OIDC SSO |
| SAML v2 IdP | Tenant SAML SSO |
| Managed domains on an IdP | Tenant email domains (SSO routing) |
| `idp_hint` | Tenant-based SSO routing or `ssoId`-style hints in the SDK — verify the current option |
| Tenant restrictions on an IdP | Tenant SSO configuration |
| IdP-initiated SAML | Descope IdP-initiated SSO — confirm support per tenant |
| Social IdPs (Google, Apple, Facebook, Microsoft, LinkedIn, Twitter, GitHub via OIDC) | OAuth providers |
| Gaming IdPs (Steam, Twitch, Xbox, Epic, Nintendo, Sony PSN), HYPR | Check Descope's provider list; custom OAuth provider otherwise; flag any with no OAuth/OIDC path |
| Identity provider links (user ↔ external ID) | Descope links on first SSO sign-in by email; confirm matching rules |
| FusionAuth as SAML v2 IdP / OIDC provider for other apps | **Federated Apps** — separate workstream |
| Customer-managed IdP setup (Tenant Manager or app screens) | **SSO Setup Suite** |

Existing SAML/OIDC connections can be moved without making every customer admin reconfigure their
IdP. Follow [SSO migration](https://docs.descope.com/migrate/sso) for the tenant setup, redirect, and
testing sequence.

**Effort: Medium** — higher if FusionAuth is also an IdP for downstream apps.

### SCIM → Descope SCIM

FusionAuth's SCIM server (Enterprise) accepts users and groups from customer directories through
client-credentials-authenticated endpoints, shaped by SCIM converter lambdas. **Treat it as a
continuing pipeline, not a one-time import.** Each customer directory must get Descope's SCIM endpoint
and token for its tenant before cutover, and group-to-role mapping must reproduce what the converter
lambdas and group roles did.

**Effort: Medium–High.**

### Entities and M2M → Inbound Apps, Resources, Policies, or Access Keys

FusionAuth's Entity Management models machines: **Entity Types** define permissions, **Entities** are
clients with a client ID and secret, and **Grants** give one entity permissions on another. Services
use the client credentials grant to get a token whose scopes reflect those grants.

| FusionAuth | Descope |
| --- | --- |
| Entity (client ID + secret) calling an API | Confidential **Inbound App** with a **Policy** granting `client_credentials` access to a **Resource**'s scopes |
| Entity Type permissions | Resource scopes |
| Grant (entity → entity, with permissions) | Policy granting scopes; or **FGA** relations if grants model data-level authorization |
| Simple internal service auth | **Access Keys** |
| User-to-entity grants (users granted access to things) | FGA relations — use the `descope-fga-schema` skill |
| API keys given to services for the Management API | Descope Management Keys (server-only) |

Inventory every client, the permissions it holds, and the audience downstream services check.
Secrets don't transfer; plan a rotation window. **Effort: Medium.**

### Webhooks → Descope Audit Webhook / Connectors

FusionAuth webhooks deliver events (`user.create`, `user.login.success`, `user.registration.create`,
`group.member.add`, `jwt.refresh`, …) signed with a JWT in `X-FusionAuth-Signature-JWT`. Some are
**transactional**: FusionAuth waits for a 2xx and fails the action if the webhook fails.

| FusionAuth | Descope |
| --- | --- |
| Non-transactional webhook keeping an app DB in sync | Audit Webhook / Connector on the matching audit events |
| Transactional webhook that can block an action | Flow step (Connector + Condition) in the Flow that performs the action |
| `user.registration.*` events | Role / tenant assignment events, or app-side sync |
| Signature verification (`X-FusionAuth-Signature-JWT`) | Descope webhook signature validation — rewrite the verifier |

Identify which handlers are business-critical before cutover. **Effort: Medium.**

### MFA, Passkeys, and Security Features

| FusionAuth | Descope |
| --- | --- |
| TOTP authenticator | TOTP in the Flow; **seeds can be imported** (`seed`, base32) |
| Email / SMS MFA | OTP steps in the Flow; users re-enroll their phone if it wasn't a verified phone |
| Recovery codes | Descope recovery options — recovery codes don't transfer |
| Tenant / application MFA policy | Flow conditions (on tenant attributes or the starting app) |
| WebAuthn / passkeys | Descope Passkeys — **do not transfer**; users re-enroll |
| Breached password detection | Breached-password check in the password step (verify current option) |
| Advanced Threat Detection (rate limits, CAPTCHA, IP ACLs, impossible travel) | Connector steps (reCAPTCHA, Arkose, Fingerprint, AbuseIPDB) + Flow conditions |
| User actions (temporary lock, prevent login) | Disable/enable user via Management SDK; Flow condition on a custom attribute for timed locks |
| Password history, expiration, complexity | Descope password policy — confirm each setting |

Ask whether each security feature is monitoring-only or actually gates login. **Effort: Medium** when
they gate production logins.

### Sessions and Tokens → Descope Session Management + JWT Templates

| FusionAuth | Descope |
| --- | --- |
| Access token (RS256/ES256, or HS256 on Kickstart/older installs) | Descope session JWT (`DS` cookie), verified via JWKS |
| Refresh token (`offline_access`; sliding / one-time-use policies) | `DSR` refresh cookie; confirm rotation behavior |
| Hosted Backend cookies `app.at`, `app.rt`, `app.idt`, `app.at_exp` | `DS` / `DSR`, managed by the SDK |
| `next-auth` session cookie | Stays (if `next-auth` is kept) or replaced by `DS`/`DSR` |
| DPoP-bound tokens | Bearer session tokens (DPoP not part of the default Descope SDK flow) |
| Access / refresh token lifetimes (tenant, overridable per application) | Project session/refresh token lifetimes |
| `aud` = Application ID | **No `aud` by default** — configure via JWT Template if validated |
| `tid`, `applicationId`, `authenticationType`, `sid` claims | Not present by default — add via JWT Template only if the app reads them |
| JWKS at `/.well-known/jwks.json` | Descope JWKS endpoint |

**Effort: Medium** — token differences ripple through middleware, API routes, and frontend.

### Connectors → Descope Generic HTTP Connector (if still migrating in)

If a Generic or LDAP Connector is still pulling users into FusionAuth from a legacy system, some
users have never signed in to FusionAuth and have no FusionAuth password. Establish which:
connector-migrated users (FusionAuth holds a hash), connector-authenticated-every-time users (the
legacy system holds the credential), and users still only in the legacy system. Then either finish
that migration first, or point a Descope Generic HTTP Connector at the same legacy endpoint so Descope
takes over the role FusionAuth was playing. **Effort: High** — flag for dedicated review.

### Consents and Families → No Direct Equivalent

FusionAuth Consents (with consent status per user, often COPPA-related) and Families (parent/child
accounts) have no Descope object. Store consent state in custom attributes (with a Flow screen to
collect it) and family relationships in the application database or FGA relations. Get an explicit
decision; these often carry legal requirements. **Effort: Medium.**

### High-Complexity FusionAuth Areas — Reference Checklist

This list is used **twice**: during Step 0 / Step 0.5 triage, to decide what to flag before the plan
is written, and again here, to sanity-check that nothing high-complexity slipped through the feature
mapping. The main high-complexity FusionAuth areas are:

* **Tenant mapping** — environment vs. customer vs. product; drives everything else.
* **Same-email users across tenants** — merge rule, passwords, profile conflicts.
* **Password hash export and compatibility** — database or support export; unsupported schemes need JIT.
* **Registrations and per-application roles** — role-name collisions; "authenticated but not authorized" users.
* **Groups** — flattening rules tied to registrations.
* **Lambdas** — especially validation lambdas that reject logins and reconcile lambdas that map IdP data.
* **Transactional webhooks** — blocking behavior must move into Flows.
* **Enterprise SSO** — per-customer IdPs, managed domains, plus FusionAuth-as-IdP if configured.
* **SCIM** — lifecycle, converters, group mapping, directory cutover.
* **Connectors still migrating users in** — a third source of truth.
* **HMAC-signed tokens** — shared-secret verification in backends.
* **Entities and grants** — M2M rotation and any data-level authorization in grants.
* **Consents and families** — compliance requirements with no Descope object.
* **Custom domains and issuer URLs** — DNS, cookies, callbacks, token validation impact.

---

## Step 4: Critical Gotchas (Always Cover These)

### JWT Claims Are Not the Same

FusionAuth's access token carries `sub`, `iss`, `aud` (the Application ID), `applicationId`, `roles`,
`tid`, `email`, `email_verified`, `preferred_username`, `authenticationType`, `auth_time`, `sid`,
`jti`, `scope`, `gty`, `tty`, plus anything a JWT populate lambda adds. Descope session JWTs always
carry `sub`, `iss`, `iat`, `exp`, `drn`, and `amr`. The rest are conditional:

- `tenants` — present when the user has tenant associations **and** the JWT template uses the default authorization format.
- `dct` — auto-set when the user belongs to exactly one tenant, or after tenant selection in a Flow.
- `roles` / `permissions` — can be **project-level**, in which case they appear with no tenant association at all.

Descope tokens carry **no `email`, `name`, or `preferred_username`**, and `sub` is the Descope user ID,
not the FusionAuth UUID. Any code that joins on `sub` to an application table keyed by the FusionAuth
user ID needs the `fusionauthId` custom attribute (in the token via JWT Template, or looked up
server-side) or a migration of those foreign keys.

**Action required:** Configure a JWT Template to add `email` and any other fields the app reads —
including everything JWT populate lambdas used to inject.

### `sub` Changes

FusionAuth user IDs are UUIDs and appear as `sub`. Descope assigns its own user IDs. Grep for every
place the app stores or compares the token's `sub` (orders, audit rows, ownership checks). Either keep
`fusionauthId` as a custom attribute and expose it as a claim during a transition, or migrate those
references to the Descope user ID. This is the most common silent data bug after cutover.

### Email Uniqueness Across Tenants

FusionAuth emails are unique per tenant; Descope login IDs are unique per project. When FusionAuth
tenants become Descope tenants, `jane@acme.com` in tenants A and B becomes one Descope user with two
memberships — but she had two passwords, two profiles, and maybe two MFA setups. Count duplicates
before planning, agree the rule (most recent sign-in wins is the usual default), and tell affected
users which password still works.

### HMAC Secrets and Hardcoded Keys Fail Silently

Kickstart and pre-1.50 FusionAuth installs sign tokens with HMAC (HS256), and HMAC keys are never in
JWKS, so backends verify with a shared secret. Others paste an RSA public key from the admin UI. Both
produce valid-looking code that rejects every Descope token. Grep for `HS256`, `jwt.verify(token,
<secret>)`, and inlined PEM keys; replace with Descope session validation.

### Hosted Backend Cookies Become `DS` and `DSR`

The FusionAuth SDKs' Hosted Backend stores `app.at` (access token, HttpOnly), `app.rt` (refresh
token, HttpOnly), `app.idt` (ID token, JS-readable), and `app.at_exp` (expiry, JS-readable). Code that
reads `app.at` on the server, `app.idt` in the browser, or `app.at_exp` to schedule refresh must be
replaced. The Descope SDK manages `DS` (session) and `DSR` (refresh).

### Logout Is Two Steps

1. Call `descopeClient.logout(refreshToken)` (or the client SDK's `logout()`) to invalidate server-side
2. Clear the `DS` and `DSR` cookies

Skipping either step leaves a broken state. FusionAuth logout was usually a navigation to
`/app/logout/{client_id}` or `/oauth2/logout?client_id=…&post_logout_redirect_uri=…`, often a plain
link, so a grep for `logout()` misses it. With Descope-hosted login, use `sdk.oidc.logout({
post_logout_redirect_uri })`.

### Audience Validation Is Opt-In

FusionAuth tokens carry `aud` = the Application ID, and backends — especially ASP.NET with
`options.Audience`, Spring with an audience validator, and `jose` with `audience` — often check it.
Descope session tokens have **no `aud` claim by default**. Apps relying on audience validation must
(1) configure a custom `aud` claim in a JWT Template and (2) pass `audience` to `validateSession()`.
Otherwise validation either fails or silently stops checking something it used to check.

### Plan Dual Token Validation for Any Phased Cutover

Unless the cutover is a hard big-bang switch, some users will hold Descope tokens and others
FusionAuth tokens for a while. The backend must validate **both**: inspect the issuer or `kid` to pick
the verifier, then verify the signature against that provider's keys and pin the issuer (and audience
where used) before any claim is trusted. For an HS256 FusionAuth install, the FusionAuth branch
verifies with the shared secret; route on `iss`, never on `alg`. See
[Descope session migration](https://docs.descope.com/migrate/session-migration) — currently **beta**,
documented for Auth0, Okta, or a custom-built solution; confirm it still applies before leaning on it,
and fall back to hand-rolled dual validation otherwise. Plan the removal of the FusionAuth branch as an
explicit follow-up task — dual validation left in place becomes a permanent second attack surface.

### Tenant Handling: `tid` Becomes `dct` / `tenants`

Most code passing a FusionAuth tenant ID is management code (`X-FusionAuth-TenantId`, `tenantId` on
API calls) — it becomes a Descope tenant ID passed to `management.*` calls, or disappears if tenants
became projects. Request-time code that read `tid` reads `dct` (active tenant) or `tenants`
(memberships). Sort every hit into these buckets before updating.

**On the web client, check null-handling before using claim helpers.** `@descope/web-js-sdk`'s
`getTenants()`, `getJwtRoles()`, and `getCurrentTenant()` read the `tenants` claim without guarding
against it being absent — a user with no tenant has no `tenants` claim, and `getTenants()` throws.
Prefer `useUser().userTenants` for display, or guard (`Object.keys(claims?.tenants ?? {})`).

### Claim Freshness: Roles Are Stamped at Issue Time

FusionAuth role changes on a registration appear only in the next token (after refresh or re-login).
**Descope behaves the same way** — `tenants`, `roles`, `permissions`, and `dct` are set when the token
is issued. During migration testing, roles assigned in the Console to an already-signed-in user won't
show up until a new token. For display, prefer `useUser()` (fetched live); for authorization, repair
the token (refresh, or `selectTenant()` for `dct`) rather than working around it in the UI.

### A `widgetId` With No Widget Behind It Fails as an Authorization Error

Every Widget referenced in code must correspond to a widget actually provisioned in the Console for
that project — referencing one that isn't fails at runtime with **"Unauthorized user: Operation not
allowed for management request,"** which reads like an RBAC problem. If a widget call fails with that
error, check whether the widget exists before touching permissions. TypeScript gives no warning.

### No Drop-In Middleware

Outside Next.js — which ships `authMiddleware` in `@descope/nextjs-sdk/server` — Descope has no
drop-in auth-middleware package. Hand-written FusionAuth JWKS middleware, Passport strategies, and
resource-server configs become roughly 20 lines of custom code that reads the `DS` cookie (or Bearer
token) and calls `validateSession()` — unless the team keeps a standards-based resource server and
repoints it at Descope's issuer.

### `cookies()` and `headers()` Are Async in Next.js 15

`cookies()` and `headers()` from `next/headers` return a `Promise` in Next.js 15+. Check the version;
if ≥ 15, `await cookies()` and mark the containing function `async`, then trace callers.

### Async Cascade: Trace All Callers Before Finishing

In TypeScript, marking a shared session helper `async` silently breaks every caller that omits
`await`. Grep for all call sites in the same pass; the cascade routinely spans 10–20 files.

### Approved Domains Are Domain-Only

FusionAuth Applications register full "Authorized redirect URLs" (and optionally wildcards) and
"Authorized request origin URLs". Descope uses **Approved Domains** — domain only, no protocol, no
path. For local dev: `localhost:3000`, **not** `http://localhost:3000/app/callback`. A kept OIDC
library registers its callback on the Descope Federated App instead.

### Password Policy Mismatches Push Users Into Resets

Imported hashes are accepted as-is, but if the Descope password policy is stricter than the FusionAuth
tenant's, users who later change their password (or JIT users whose password is stored on first
sign-in) hit validation errors. Set the Descope policy to match FusionAuth's at cutover; tighten later.

### The User Search 10,000-Result Limit

On the Elasticsearch search engine before FusionAuth 1.48.0, `POST /api/user/search` returns at most
10,000 users regardless of paging. From 1.48.0, use the `nextResults` token. The database search
engine pages with `startRow` / `numberOfResults`. Export from the database when you need hashes
anyway, and compare the exported count against `SELECT COUNT(*)` before importing.

### The Database Export Holds Secrets

The export contains password hashes and MFA secrets. Keep it encrypted at rest, out of the repo and
out of chat, run the import from a trusted machine, and delete it (and any intermediate JSON) after
the production import is verified.

### SCIM Is a Lifecycle, Not a One-Time Import

If FusionAuth's SCIM server is in use, re-point every customer directory at Descope before cutover.
Interactive login keeps working while provisioning silently stops — the failure shows up days later.

### Passkey, Email-MFA, and SMS-MFA Enrollments Do Not Transfer

Passkeys are bound to the relying party (FusionAuth's domain), so they cannot move. Email and SMS MFA
re-enroll naturally if the email/phone is verified. TOTP can move via the `seed` field if the secret is
in the export. Communicate re-enrollment before the cutover date, not after.

---

## Step 5: Automated Testing

Run the app and verify it works — don't just hand over a checklist.

### Phase 0: Final stale-import sweep (BLOCKING)

```bash
grep -rni "fusionauth\|app\.at\b\|app\.rt\b\|app\.idt\|/oauth2/\|/app/callback" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.vue" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.php" --include="*.java" --include="*.kt" \
  --include="*.cs" --include="*.swift" --include="*.dart" --include="*.gradle" \
  --include="*.plist" --include="*.xml" --include="*.env*" --include="*.yml" --include="*.yaml" \
  --include="*.properties" --include="appsettings*.json" --include="*.json" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=Pods \
  .
```

**Triage the hits — don't treat every match as a failure.** Imports, package names, env vars, config
files, CI workflows, Docker services, and issuer URLs referencing FusionAuth must be zero (except
infrastructure deliberately kept for the JIT transition, recorded in the Decisions Log). Comments
explaining what a construct *used to be* are expected and should stay. `/oauth2/` hits can be
legitimate if a kept OIDC library now points at Descope — read each one. Pay particular attention to
non-source files — `.env*`, CI workflows, `docker-compose.yml`, `application.yml`,
`appsettings.json` — since none of these break compilation and are the most commonly missed.

### Phase 1: Install, compile, and start

```bash
npm install   # or: pip install -r requirements.txt / go mod tidy / bundle / composer install
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

- `Cannot find module '@fusionauth/...'` → stale import; re-run Phase 0
- `Property 'roles' does not exist on type '...'` → wrapper built against FusionAuth's flat claims; re-derive from the Descope `authInfo` shape
- `'await' expression is not allowed in synchronous contexts` → async cascade gap
- `Object is possibly 'undefined'` on session fields → add null check or early return

```bash
npm run dev   # or: python main.py / go run . / flask run / etc.
```

### Phase 2: Run existing tests

```bash
npm test   # or: pytest / go test ./... / etc.
```

Auth-related test failures usually mean: a fixture still mints FusionAuth-shaped tokens (with
`applicationId`, `tid`, `aud`); a test asserts on `email` without a JWT Template; a test still spins
up a FusionAuth container; or a mock still stubs `FusionAuthClient`.

### Phase 3: Smoke test the running app

```bash
# Root path
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/

# Unauthenticated protected route (expect 3xx or 401)
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/dashboard

# Login page loads Descope component (embedded Flow) or redirects to Descope (hosted)
curl -s -i http://localhost:<port>/login | grep -i "descope"

# Invalid token → 401
curl -s -H "Cookie: DS=invalid_token" http://localhost:<port>/api/me

# No FusionAuth endpoints are still being called
curl -s http://localhost:<port>/ | grep -i "fusionauth\|:9011" && echo "STALE FUSIONAUTH REFERENCE"
```

### Phase 4: Verify sign-in and JWT claims

- Sign in as an imported user **with their existing password**, once per hash scheme present (these must be test users in a dev project — never real user credentials)
- Decode the session token:

```bash
echo "<DS_cookie_value>" | cut -d'.' -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

Check that `email` and any other expected claims are present, that roles match what the user had in
FusionAuth, and that `dct` / `tenants` hold the tenant context the app used to read from `tid`.

### Phase 5: Report results

```
## Test Results

**Server startup:** ✅ Started successfully on port 3000
**Existing tests:** ✅ 12 passed / ❌ 2 failed (list failures)
**Unauthenticated /dashboard:** ✅ 302 → /login
**Unauthenticated /api/protected:** ✅ 401
**Login page loads Descope:** ✅
**Imported-user password sign-in:** ✅ pbkdf2-sha256 / ✅ bcrypt / ⚠️ salted-md5 → JIT path
**JWT claims (email, roles, dct):** ✅ Present / ❌ Missing — JWT Template not yet configured
**No residual FusionAuth references:** ✅

**Blockers before going live:**
- [ ] (list anything that failed or needs manual action)
```

**Do not proceed to Step 6 until ALL of the following are true:**

- Phase 0 grep returns no FusionAuth references except deliberate comments and recorded transition infrastructure
- Phase 1 compilation passes with zero errors
- Phase 1 server starts and stays running
- Phase 3 root path returns 2xx or 3xx (not 5xx)
- Phase 3 protected routes return 3xx or 401 (not 500)

---

## Step 6: Post-Migration Summary (Required)

Every migration produces a `MIGRATION-SUMMARY.md` covering what was done, manual setup
remaining, and behavioral differences that matter before production.

### MIGRATION-SUMMARY.md

1. **What was migrated** — a table mapping each FusionAuth concept to its Descope replacement (tenants, applications, roles, groups, lambdas, IdPs, webhooks)
2. **Behavioral differences and open questions** — numbered list of significant differences. For each item: FusionAuth behavior, Descope behavior, action required. At minimum cover claim shape, `sub` change, cookies, logout, audience validation, role-change propagation, tenant merge results, users on unsupported hash schemes, MFA re-enrollment, and anything with no equivalent (registrations, families, consents, per-tenant issuers)
3. **Pre-deploy checklist** — actionable checkbox items for everything that must happen before the migrated app can run. Prominently include all Console setup tasks (project, Flow, JWT Template, Approved Domains, tenants, roles, custom attributes, SSO/SCIM, social provider credentials), the production import plus delta import, the SCIM re-point, the JIT transition length (if any), FusionAuth decommission (server, database, search, Kickstart, Terraform), and **deleting the database export**. These are the things easiest to forget because the code compiles without them.
4. **Post-cutover improvements** — things deliberately not done during the migration (passkeys, adaptive MFA, Widgets for app-built screens that were ported as-is)

---

## Step 7: Output Format

Write a numbered migration guide in Markdown, scoped to the user's stack. Use code
snippets and direct doc links. Always include the MIGRATION-SUMMARY.md deliverable (Step 6).

For complex migrations, flag the high-effort items explicitly with estimated complexity
(Low/Medium/High) so the user can plan.

---

## Reference Files

- `references/implementation-nuances.md` — Verified migration patterns, export queries and endpoints, password hash mapping, framework recipes, and edge cases.
- `references/flows-and-widgets.md` — Descope terminology, Flows, Widgets, SSO Setup Suite, and the Console-vs-code decision guide.
- `references/fusionauth-detection-patterns.md` — Codebase search commands and common env vars.
- Descope Docs: [https://docs.descope.com](https://docs.descope.com)
- **Migration index (check for a FusionAuth page): [https://docs.descope.com/migrate](https://docs.descope.com/migrate)**
- User Import (Custom), including password hash formats and TOTP seeds: [https://docs.descope.com/migrate/custom](https://docs.descope.com/migrate/custom)
- Batch Create Users API: [https://docs.descope.com/api/management/users/batch-create-users](https://docs.descope.com/api/management/users/batch-create-users)
- Comparable JIT-migration patterns, documented for other providers: [Keycloak](https://docs.descope.com/migrate/guides/keycloak), [Cognito](https://docs.descope.com/migrate/guides/cognito), [Azure AD B2C](https://docs.descope.com/migrate/guides/azure-ad-b2c)
- Session migration / dual token validation: [https://docs.descope.com/migrate/session-migration](https://docs.descope.com/migrate/session-migration)
- SSO migration: [https://docs.descope.com/migrate/sso](https://docs.descope.com/migrate/sso)
- OIDC Federated Applications (keep a generic OIDC client): [https://docs.descope.com/identity-federation/applications/oidc-apps](https://docs.descope.com/identity-federation/applications/oidc-apps)
- Generic HTTP Connector: [https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http](https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http)
- Custom OAuth/OIDC providers: [https://docs.descope.com/auth-methods/oauth/providers/custom-provider](https://docs.descope.com/auth-methods/oauth/providers/custom-provider)
- Descope OIDC Endpoints: [https://docs.descope.com/getting-started/oidc-endpoints](https://docs.descope.com/getting-started/oidc-endpoints)
- Descope Flows: [https://docs.descope.com/flows](https://docs.descope.com/flows)
- JWT Templates: [https://docs.descope.com/management/token/jwt-templates](https://docs.descope.com/management/token/jwt-templates)
- Resources: [https://docs.descope.com/resources](https://docs.descope.com/resources)
- Policies: [https://docs.descope.com/policies](https://docs.descope.com/policies)
- Inbound Apps: [https://docs.descope.com/identity-federation/inbound-apps](https://docs.descope.com/identity-federation/inbound-apps)
- Access Keys (M2M — simple cases only): [https://docs.descope.com/management/m2m-access-keys](https://docs.descope.com/management/m2m-access-keys)
- Messaging Templates: [https://docs.descope.com/management/messaging-templates](https://docs.descope.com/management/messaging-templates)
- Audit Webhook: [https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook)
- Custom Domains: [https://docs.descope.com/how-to-deploy-to-production/custom-domain](https://docs.descope.com/how-to-deploy-to-production/custom-domain)
- ReBAC / FGA: [https://docs.descope.com/authorization/rebac](https://docs.descope.com/authorization/rebac)
- FusionAuth source of truth: [fusionauth.io/docs](https://fusionauth.io/docs) — especially [export](https://fusionauth.io/docs/migrate/export), [password hash algorithms](https://fusionauth.io/docs/migrate/password-hashes/algorithms), [API authentication](https://fusionauth.io/docs/apis/authentication), [user search](https://fusionauth.io/docs/apis/users/search), and [Login API](https://fusionauth.io/docs/apis/login)

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
