---
name: workos-to-descope
description: >
  Use this skill whenever anyone asks about migrating from WorkOS to Descope — whether they're
  a developer doing it themselves or a technical lead evaluating the move. Triggers on: "how
  do I migrate from WorkOS", "replace WorkOS with Descope", "we're moving off WorkOS", "WorkOS to
  Descope", "switch from WorkOS", "our app uses @workos-inc/node / @workos-inc/authkit-nextjs / AuthKit / WorkOS SSO / Directory Sync / SCIM and we want to use Descope instead",
  or any question about WorkOS features (AuthKit, Organizations, Enterprise SSO, Directory Sync/SCIM,
  Admin Portal, RBAC, FGA, Audit Logs, Radar, Pipes) in the context of Descope. Works for any
  language or framework with a Descope SDK. Always use this skill before producing migration
  guidance — do not rely on memory alone.
---

# WorkOS → Descope Migration Skill

This skill guides self-service migrations from WorkOS to Descope. It runs in three parts:

1. **MCP Check** — confirm whether the Descope MCP Server is available and suggest installing it if not
2. **Migration Plan** — gather context via triage questions, analyze the codebase's auth touchpoints, and produce a human-readable `MIGRATION-PLAN.md` for the user to review
3. **Execution** — if the user confirms they want to proceed, execute the plan

Do not collapse these parts or skip ahead. The plan must be reviewed before code changes begin.

WorkOS is not only an authentication provider — it is a B2B/enterprise-readiness platform spanning
authentication, organizations, enterprise SSO, SCIM/directory sync, RBAC, FGA, audit logs, connected
accounts, admin setup flows, and security controls. A good migration first identifies which WorkOS
features are in use, then maps each one to the closest Descope feature or migration pattern. Expect
WorkOS migrations to be more B2B-enterprise heavy than a typical consumer-auth migration.

**Primary references** (both in this skill's directory):

- `references/implementation-nuances.md` — verified migration patterns for each framework, WorkOS feature-to-Descope mappings, and known gotchas
- `references/flows-and-widgets.md` — Descope terminology/lingo, Flow structure and templates, Widgets, SSO Setup Suite, Console-vs-code decision guide

---

## Guiding Principles

**Console-first.** Before recommending SDK code for any user-facing auth feature, check whether the Console, a Flow, a Widget, or the SSO Setup Suite covers the use case. Engineers integrate once (SDK setup + session validation). All subsequent auth evolution — new methods, MFA changes, UI updates, tenant SSO onboarding — should happen in the Console without code deployments. See `references/flows-and-widgets.md` → Console vs. Code.

**Ask, don't assume.** At any design decision point — embed Flows vs. OIDC compatibility, Flow vs. custom code, Widget vs. custom page, MFA inline vs. separate enrollment, programmatic SSO vs. SSO Setup Suite, one-Organization-to-one-Tenant mapping — use `AskUserQuestion` rather than proceeding with an assumption. The cost of a wrong assumption compounds across 20+ files, and the WorkOS Organization → Descope Tenant mapping in particular ripples into SSO, SCIM, RBAC, and domain routing. Uncertainty about architecture or intent is always worth a question.

**MCP over memory.** When the Descope MCP Server is available (confirmed in Part 1), use `docs_ask_question` to verify every SDK method name, option shape, and return type before writing it. Do not fall back to "verify the exact method name in the SDK type declarations" as a hedge — just verify it directly.

---

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
> migration output — especially for SDK lookups and flow-specific configuration.
>
> **Would you like to install the MCP before we continue, or proceed without it?**

- If they choose to install: pause and wait. Once they confirm it's installed, re-check by calling `docs_search` again before proceeding.
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
  in the conversation (e.g., Node.js, Go, Ruby, Python). The user can always
   pick "Other."
2. **Migration goal** — Full cut-over, incremental/phased migration, or just evaluating.
3. **Existing users and organizations** — Are they migrating an app with active users and
  organizations in WorkOS, staging/dev only, or starting fresh? This determines whether user
   and organization migration planning is needed (user export, org-to-tenant mapping, SCIM
   continuity, phased vs. big-bang cutover, forced re-login on cutover). 

**Second `AskUserQuestion` call — WorkOS feature usage (use `multiSelect: true`):**

1. **Which WorkOS features are in use?** Present the highest-impact categories:
  - **AuthKit** — WorkOS's hosted/embeddable login UI and session management (email/password, social login, passkeys, MFA, magic auth); which sign-in methods are enabled and whether the hosted or embedded flow is used.
  - **Organizations** — organization membership, organization switching, metadata, whether users can belong to multiple organizations.
  - **Enterprise SSO** — connections SAML, OIDC, or both; whether setup is handled by internal engineers or by customer admins; whether domain-based SSO routing is used.
  - **Directory Sync / SCIM** — which directories; group sync; group-to-role mapping; deprovisioning behavior; directory webhook handlers.
  - **Admin Portal / Widgets** — which customer-admin workflows are hosted by WorkOS today; whether the app generates portal links; whether Descope Widgets or the SSO Setup Suite can replace them.
  - **RBAC** — whether roles are global/environment or organization-scoped; where permission checks happen in code; whether roles/permissions are in tokens; whether IdP groups map to roles.
  - **FGA** — the authorization model (resources, relationships, privileges, hierarchy); where checks are performed. Flag as high complexity.
  - **Audit Logs** — whether logs are written to WorkOS, read back from WorkOS, shown to customers, or required for compliance.
  - **Radar** — whether it blocks, challenges, or only notifies about suspicious auth attempts; custom rules.
  - **Pipes** — which providers are connected; where connected-account tokens are used (AI agents, integrations, background jobs).
  - **Vault / Feature Flags** — flag as potentially outside the core Descope identity migration.
  - **MCP Auth / Connect** — flag for deeper review before implementation.
  - The user can add others via "Other."

After both calls, summarize findings and flag high-complexity items (Directory Sync/SCIM, FGA,
Pipes, MCP Auth/Connect, Vault) before proceeding to Step 0.5.

---

### Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

These questions surface blockers the framework doesn't expose. Ask even the ones you think
you know. Use `AskUserQuestion` before proceeding to codebase analysis.

Batch into calls of up to 4 questions. Skip questions that are clearly inapplicable given
Step 0 answers (e.g., skip user migration planning if they said they're starting fresh).

**Access and credentials**

- Do they have access to the Descope Console and a Project ID? (If not, see Step 1.5.)
- Do they need a Management Key? (Required for user CRUD, RBAC, ReBAC, tenant/SSO/SCIM configuration, Outbound Apps.)

**Codebase scope**

- Are there places in the app that read claims directly from the session token (e.g. `user.email`, `claims.organization_id`, `role`/`permissions`)? These need a JWT Template configured before they'll work.
- Does the app read WorkOS `organizationId`, `connectionId`, or `directoryId` in many places? The WorkOS Organization → Descope Tenant remap ripples through SSO, SCIM, RBAC, and membership checks — confirm the org model before writing code.
- Are there multiple services or microservices validating WorkOS tokens/sessions? Each needs to be updated to validate Descope JWTs.

**Deployment and risk**

- Do they have multiple environments (dev / staging / prod)? Each needs its own Descope project and Project ID.
- Is there a maintenance window, or does this need to be zero-downtime?

**User and organization migration** (if they indicated existing users/orgs in Step 0)

- How many users and organizations? This determines export approach and whether a phased cutover is warranted.
- Do they use passwords in AuthKit? WorkOS has **no API or dashboard export of password hashes** — hashes are released only on request to WorkOS support, as a CSV delivered by secure file transfer. Ask whether they have requested it, or will. That export (mostly bcrypt) lets users keep their passwords; without it, imported users go through a JIT password check against WorkOS (see Step 3 → Users, Organizations & Roles).
- Big-bang cutover or phased? By default, import everyone, switch the app in one step, and keep the WorkOS JIT connector in the Flow for a transition the user chooses. Map each WorkOS Organization to a Descope Tenant first; user membership and tenant-scoped roles depend on it.
- Do they use **multiple roles per membership** (`roles[]`) or **organization-scoped custom roles** (slugs starting with `org-`)? Both carry over, but the script must handle them explicitly.
- **SCIM is a lifecycle system, not a one-time import.** If Directory Sync is enabled, enterprise directories will keep pushing create/update/suspend/delete events after cutover. A single user import is not enough — every SCIM/directory workflow must be re-pointed at Descope before cutover, or provisioning silently breaks.
- Are they aware that active WorkOS sessions will be invalidated on cutover unless a session-bridging approach is used? Plan for a forced re-login or phased rollout.

**Gaps to flag immediately** (don't ask — flag these proactively based on Step 0 answers)

- If they're using **Vault** or **Feature Flags**: these may have no direct Descope identity equivalent. Flag separately; do not pretend they are Descope SDK swaps. Ask whether they're in scope.
- If they're using **MCP Auth / Connect**: flag for deeper review before any implementation — likely maps to Descope Inbound Apps / OAuth app patterns, but needs dedicated mapping.
- If they're using **Audit Logs**: set up Descope's Audit Webhook Connector before cutover to avoid gaps in compliance/event logging. Missing this can break compliance visibility even though the app still runs.
- If they're using **Pipes / connected accounts**: connected third-party tokens may power integrations or background jobs. Identify provider connections and whether users must reconnect accounts.

**Console/Flow/Widget opportunities** (flag before codebase analysis, then ask):

- If the app uses the **WorkOS Admin Portal** or generates portal links: ask whether the SSO Setup Suite + Tenant Profile Widget replaces that workflow instead of rebuilding it as custom code. Do not default to building custom admin setup screens.
- If the app has a profile edit page or user management UI: ask whether a Descope Widget covers the use case.
- If the app has a separate MFA enrollment page: ask whether MFA should be integrated into the main sign-in Flow as a step or subflow instead (almost always cleaner in Descope).
- If any server-side code initiates SSO, generates emails, or runs logic during the auth journey: ask whether that logic can be a Flow step or Connector instead of server code.

Summarize any blockers and Console/Flow opportunities before proceeding to codebase analysis.

---

### Step 1: Codebase Analysis

Scan the codebase to map every auth touchpoint before writing the plan.

**Run these searches (adapt file extensions to the user's language):**

```bash
# Find all WorkOS / AuthKit import sites.
grep -rni "workos\|authkit" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.mjs" --include="*.cjs" --include="*.py" --include="*.go" \
  --include="*.rb" --include="*.php" --include="*.java" --include="*.kt" \
  --include="*.cs" --include="*.ex" --include="*.exs" --include="*.rs" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=venv \
  . 2>/dev/null

# Find all WorkOS env var references
grep -rn "WORKOS_\|workos\." \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --include="*.env*" --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Find WorkOS SDK surface + claim / token / org access patterns (things that may need a JWT Template or org→tenant remap)
grep -rn "workos.userManagement\|workos.organizations\|workos.sso\|workos.directorySync\|workos.auditLogs\|workos.fga\|workos.widgets\|workos.events\|workos.webhooks\|workos.pipes\|workos.portal\|workos.organizationDomains\|workos.featureFlags\|workos.types\|workos.mfa\|workos.authorization\|workos.vault\|organizationId\|organization_id\|orgId\|connectionId\|connection_id\|directoryId\|directory_id\|roleSlug\|permission" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Find protected route / session access declarations
grep -rn "authkitMiddleware\|withAuth\|getUser\|ensureSignedIn\|getSignInUrl\|getSession\|isAuthenticated\|require_session\|@login_required\|authMiddleware" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Find B2B / enterprise feature usage (SSO, SCIM, audit, admin portal, security)
grep -rn "scim\|saml\|sso\|auditLog\|audit_log\|adminPortal\|portalLink\|radar\|pipes" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Check package.json / go.mod / requirements.txt for WorkOS dependencies
find . -maxdepth 3 \( -name "package.json" -o -name "go.mod" -o -name "requirements.txt" \) \
  ! -path "*/node_modules/*" -exec grep -l "workos" {} \;
```

For each hit, record:

- **File path and line** — where the change happens
- **What it does** — import, route protection, claim access, org/tenant read, SSO/SCIM config, webhook handler, logout handler, etc.
- **Complexity** — Low (drop-in replacement), Medium (logic rewrite), High (no equivalent)

Read `package.json` (or equivalent) for the exact framework version — this affects async
behavior (Next.js 15 vs 14) and SDK compatibility.

If the Descope Docs MCP is available, use `docs_search` or `docs_ask_question`
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

> Today, WorkOS handles everything related to login: AuthKit shows the login UI, issues tokens
> and sealed sessions, validates them on every request, and routes enterprise users to the right
> SSO connection. After this migration, Descope takes over all of those responsibilities. The
> login UI becomes a Descope Flow embedded in the app. Session validation moves to the Descope
> SDK. WorkOS Organizations become Descope Tenants. The WorkOS API key, client ID, redirect URI,
> and cookie password are replaced by a single Descope Project ID.
>
> WorkOS features in use that need to carry over: [list in plain English, one clause each].

Tailor to triage findings.

---

#### Client SDK vs. Backend SDK: A Specific 1-to-1 Mapping

For every WorkOS touchpoint found in triage, produce a concrete, one-to-one mapping — WorkOS construct → the exact Descope SDK and method that replaces it —
and state explicitly whether that replacement runs in the **client SDK** or the **backend SDK**, and
why. Use this division of responsibility:

- **Client SDK** (`@descope/web-js-sdk`, `@descope/react-sdk`, `@descope/nextjs-sdk` client
  components, or the `<descope-wc>` web component) — everything the user's browser/app does:
  rendering the login/sign-up UI (a Descope Flow replaces AuthKit's hosted or redirect login),
  initiating authentication, holding the session on the client, refreshing the token, and reading
  the current user for UI purposes. This replaces AuthKit's UI, the redirect cycle, and any
  client-side session access. It uses only the public Project ID — never a Management Key.
- **Backend SDK** (`@descope/node-sdk`, `descope` (Python), `github.com/descope/go-sdk`, etc.) —
  everything the server does: validating the session JWT on every request (replacing WorkOS
  server-side `withAuth()` / middleware), checking roles and permissions, and — with a Management
  Key — all administrative operations done by ID (user and tenant CRUD, role/permission definitions,
  SSO/SCIM configuration, ReBAC). This replaces WorkOS server-side validation and every WorkOS
  Management API call.

For each file or area, name the WorkOS call, the Descope SDK that replaces it, which side it runs on,
and the reason (e.g. "session validation must stay server-side because the validation/Management key
cannot ship to the browser"). When one WorkOS feature spans both sides — for example AuthKit login
(now a client Flow) plus per-request `withAuth()` validation (now the backend SDK) — split it into
its client half and its backend half so the reader sees exactly what moves where, and why each piece
belongs on that side.

---

#### Auth Touchpoints: What the Code Analysis Found

Open with the scope count (e.g., "11 files across 4 areas"). Group by area, not file path.
Each group gets a sentence on what it does and what changes.

**Session handling (3 files)** — These files read and validate the current user's login
state. They'll be updated to use the Descope session SDK instead of WorkOS AuthKit. 


| File               | What it does today                                                            | What changes                                                                                              |
| ------------------ | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `lib/auth.ts:34`   | Returns WorkOS session via `withAuth()` with `user`, `organizationId`, `role` | Rewritten to return Descope `authInfo`; a thin adapter layer preserves the shape callers expect |
| `middleware.ts:12` | `authkitMiddleware()` blocks unauthenticated requests app-wide                | Updated to call Descope session validation; logic is identical, SDK call changes                          |


**Login / logout routes (2 files)** — These handle the AuthKit redirect-based login flow.
Descope replaces this with an embedded UI component (or hosted Flow); the redirect cycle changes.


| File                    | What it does today             | What changes                                                                                                  |
| ----------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `app/callback/route.ts` | AuthKit OAuth callback handler | Deleted or rewritten — Descope handles this client-side; verify the replacement against the framework section |


Cover all functional groupings. End with: "Total: N files. Estimated code-change effort: N–N hours."

---

#### Feature Migration: WorkOS → Descope

For each WorkOS feature confirmed in triage, write a short paragraph: what it's trying to
accomplish, the best Descope approach for that goal, what's different, and what action is
required. The best approach may be a Flow, Widget, SSO Setup Suite, or Console configuration
rather than a direct SDK equivalent — reason about the intent, not just the API surface. Only
recommend SDK code when programmatic control is genuinely required. Example:

> **Multi-tenancy (WorkOS Organizations → Descope Tenants)**
> WorkOS Organizations group users by company and scope SSO, SCIM, roles, and domain policies.
> Descope has the same concept, called Tenants. Most code that handles organizations is
> management/admin code that passes a WorkOS `organizationId` to the API — that simply becomes a
> Descope **tenant ID** passed to `descopeClient.management.tenant.*` / `management.user.*` calls
> (load a tenant, create one, add/remove membership, scope roles). This is by-ID work, not token
> parsing. The only place a tenant shows up as a claim is request-time session reads: WorkOS's flat
> `organizationId` (from `withAuth()`) becomes Descope's nested `tenants` object (plus `dct` for the
> active tenant), which you read off the validated session — ideally via SDK helpers like
> `validateTenantRoles(authInfo, tenantId, [...])` rather than parsing claims by hand. Confirm the
> org→tenant mapping first, since it ripples into SSO, SCIM, and RBAC.
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
all WorkOS credentials in the app's environment variables.
- **Create an authentication flow** — Descope uses a visual "flow" to define the login
experience (what methods are offered, in what order). The built-in `sign-up-or-in` flow
works for most apps and requires no customization to start.
- **Configure a user profile token template** — By default, Descope session tokens don't
include the user's name, email, or profile photo. This template needs to be configured so
the app can display user profile information. Without it, any part of the UI that shows the
user's name or email will show nothing after login. (~10 minutes)

**Required before production:**

- **Create tenants for each WorkOS Organization** — Descope Tenants must exist before
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


| Remove                   | Add                              | Why                                                                                                                                 |
| ------------------------ | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `WORKOS_API_KEY`         | —                                | WorkOS authenticates server-side calls with a secret API key. Descope uses a Project ID (+ optional Management Key) instead.        |
| `WORKOS_CLIENT_ID`       | —                                | WorkOS identifies the AuthKit client. Descope uses a Project ID.                                                                    |
| `WORKOS_REDIRECT_URI`    | —                                | AuthKit's OAuth callback URL, configured in console. Descope's embedded Flow doesn't require a server redirect URI in the same way. |
| `WORKOS_COOKIE_PASSWORD` | —                                | Used by AuthKit to encrypt/seal the session cookie. Descope issues a signed session JWT instead; no sealing password needed.        |
| —                        | `DESCOPE_PROJECT_ID`             | The single identifier for the Descope project. Replaces all of the above.                                                           |
| —                        | `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value, exposed to the browser for the login component (Next.js only).                                                          |
| —                        | `DESCOPE_MANAGEMENT_KEY`         | Only needed if the app manages users, roles, tenants, or SSO/SCIM server-side.                                                      |


Follow with: "Net change: 4 variables removed, 1–3 added. No secrets need to be rotated
on the WorkOS side — those credentials stop being used."

---

#### User & Organization Migration (only if existing users/orgs need to be migrated)

Prose strategy first, then steps. Start with: "X existing users across Y organizations need to be in Descope before cutover." Describe:

- **The plan**: by default, import everyone, switch the app in one step, and keep WorkOS behind the Flow for a JIT transition of a length the user chooses (a few months recommended when some users have no exportable hash). Say why if the plan differs
- **Org→tenant mapping**: each WorkOS Organization becomes a Descope Tenant (keep the WorkOS `org_…` ID as the tenant ID, so the app's stored organization IDs still match); membership and tenant-scoped roles depend on this mapping being correct first
- **What users will experience**: they sign in once more. Users whose bcrypt hash was imported keep their password. Users without one keep it if they sign in during the transition; after WorkOS is off they verify their email, then reset their password or go passwordless
- **The biggest dependency**: whether the WorkOS password-hash export has been requested from WorkOS support, and whether SCIM directories must be re-pointed at Descope (a continuing pipeline, not a one-time import)

End with a brief checklist of the migration steps at the level a PM can track. The agent writes
the export/import script (Step 3 → Users, Organizations & Roles has the endpoints and mapping):

- Get a WorkOS API key (`sk_…`) for each environment to migrate, and request the password-hash export from WorkOS support if passwords are in use
- Define the user custom attributes the script sets (at least `workosId` and `freshlyMigrated`, plus any `metadata` keys) and tenant custom attributes (organization `metadata`, `external_id`) in the Descope Console before the first run
- Write the script with a dry-run mode, and run it against a Descope **dev** project first
- Verify permission, role, and tenant creation before user creation
- Decide what to do with `inactive` and `pending` memberships and open invitations
- Re-point SCIM/Directory Sync at Descope (if Directory Sync is in use), and recreate SSO connections per tenant
- Run against staging, then production; set `freshlyMigrated` on users who have a WorkOS password but no usable hash (not on SSO-, social- or Magic Auth-only users)
- Add the Generic HTTP Connector (WorkOS password check) to the sign-in Flow: `freshlyMigrated` users and users new to Descope go straight to it; other existing users try the Descope password first and fall back to the connector only if that check fails
- Request the hash export as close to the switch as possible, and switch the app to Descope in one step; no freeze is needed, because the connector covers passwords changed in WorkOS after the export
- Re-sync organizations, memberships and roles once right after the switch, since JIT does not update roles of users already imported
- Turn WorkOS off at the end of the chosen transition, then send remaining `freshlyMigrated` users to email verification plus password reset or passwordless

---

#### Trade-offs and considerations

Things that could affect timeline, user experience, or scope. Write each in plain English
with three parts: **what it is**, **what breaks if it's ignored**, and **what to do**.
Format each as a named callout:

> **Consideration: Organization-to-tenant mapping affects almost every B2B feature**
> WorkOS Organizations should usually map to Descope Tenants. If this mapping is wrong, SSO, SCIM,
> roles, permissions, domain routing, and user membership checks may all break.
> **Action:** Confirm the organization model before writing migration code.

> **Consideration: SCIM is a lifecycle system, not just a user import**
> Directory Sync may create, update, suspend, and delete users or group memberships continuously.
> A one-time import is not enough if enterprise directories keep syncing after cutover.
> **Action:** Identify every SCIM/directory workflow and re-point it at Descope before cutover.

> **Consideration: Password hashes come only from WorkOS support**
> WorkOS has no API or dashboard export of password hashes; support sends them as a CSV on request.
> If the request is made late, the import runs without hashes and every password user depends on the
> JIT connector, so users who don't sign in during the transition must reset their password.
> **Action:** Request the hash export at the start of the project. Import bcrypt hashes directly and
> keep the JIT connector for users whose hash is missing or in an unsupported format.

> **Consideration: Admin Portal workflows should not automatically become custom code**
> If the app uses the WorkOS Admin Portal, the Descope equivalent may be the SSO Setup Suite or a
> Widget rather than a custom settings page.
> **Action:** Ask whether tenant admins currently self-configure SSO/SCIM/domain verification.

> **Consideration: Audit logs can silently disappear**
> The app may keep working after migration even if audit logging is broken — creating compliance
> and enterprise-customer issues.
> **Action:** Set up Descope audit/event forwarding before production cutover.

> **Consideration: User profile data won't appear after login until a token template is configured**
> Descope session tokens don't include name, email, or profile photo by default. Any UI that
> displays user information will show blank values after migration until the token template is set
> up in the Descope console. This is a one-time configuration step, not a code change.
> **Action:** Configure the token template before running any tests. Estimated time: 10 minutes.

Include only applicable trade-offs and considerations.

---

#### Execution Plan

Open with one sentence: phases run in sequence; steps within a phase can run in parallel.
Then labeled phases, each with a time estimate:

---

**Phase 1 — Console Setup** (~30–60 minutes, no code required)
Can be done by any team member with Descope console access, in parallel with other work.

- Create Descope project, copy Project ID
- Create authentication flow (use the built-in `sign-up-or-in` to start)
- Configure user profile token template
- Create tenants for each WorkOS Organization (list actual orgs found)
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

**Phase 3 — User & Organization Migration** (~2–4 hours for the script and dry run; the WorkOS hash export is a manual support request, so make it in Phase 1)
Run against dev/staging first. Do not run against production until Phase 4 passes.

- (steps from user & organization migration section above)
- Compare counts after the dry run and the live run: organizations → tenants, environment and organization roles → roles, active memberships → `userTenants`, users → users

**Phase 4 — Testing** (~30–45 minutes)

- Compile passes with zero errors
- Server starts, no crashes on startup
- Unauthenticated routes redirect to login correctly
- Login flow completes, user profile data appears (confirms token template is working)
- Tenant/SSO routing works for at least one organization
- Logout invalidates session

**Phase 5 — Production Cutover**

- Final production import, then switch the app to Descope with the WorkOS JIT connector live in the Flow
- Re-sync organizations, memberships and roles once right after the switch
- Re-point SCIM directories and confirm the first provisioning event lands in Descope
- At the end of the transition, turn WorkOS off and route remaining `freshlyMigrated` users to verification plus password reset or passwordless
- (other cutover-specific steps based on their strategy)

---

Total estimated engineering effort: **N–N hours** across N engineers.
Blocking dependencies: (list anything on the critical path — console access, SCIM re-point, etc.)

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
- Migration path: [Path A: OIDC compat / Path B: Full native]
- Migration goal: [Full cutover / Phased / Evaluating]

## Triage Answers
- Existing users: [Yes — N users / No — greenfield]
- Existing organizations: [Yes — N orgs → tenants / No]
- Password migration needed: [Yes / No]
- WorkOS features in use: [comma-separated list]
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
- [ ] JWT template configured
- [ ] Tenants created for each WorkOS Organization: (list)
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

> `Migration context: Next.js 14 · Path B · Phase 2, step 3/8 · Next: rewrite lib/auth.ts`

If this line can't be filled in accurately, re-read the files first.

**Rule 3 — Update `MIGRATION-STATE.md` immediately after each step.**

Mark the file done in the Files Inventory, update "Current Phase" and "Next Action", and
append any non-obvious decision to the Decisions Log. Do this before the next step.

---

## Pre-Generation Protocol (apply before writing any code)

Run before generating any import, wrapper type, or helper. Skipping produces code that
compiles but fails at runtime.

**1. Verify SDK exports before writing any import.**
When the Descope MCP server is available, use `docs_ask_question` to confirm the exact method name, option shape, and return type before writing any SDK call. This is faster and more reliable than reading type declarations. Do not write a method name and add a hedge like "verify the exact name" — just verify it.

When the Descope MCP server is unavailable: resolve the package's type declarations (`node_modules/<pkg>/dist/types/` or its `package.json` `types` field) and confirm the exact exported name and signature. For Go, run `go doc`. For Python, check the SDK stubs.

**Prefer local `node_modules/` over GitHub** when reading type declarations. Installed packages reflect the exact version in use. If the Descope package isn't installed yet, install it first, then read local type declarations. Only fall back to GitHub if the package can't be installed in the current environment.

This applies to **every SDK call you write**, not just the first import. Field names on
option objects, hook return shapes (`useDescope()` returns the SDK directly, not `{ sdk }`),
and subpath exports (`/client` vs root) differ just as often.

**1a. After rewriting any module, grep for remaining imports of the removed package.**

```bash
grep -r "from '@workos-inc/" --include="*.ts" --include="*.tsx" .
```

Add remaining hits to the work list.

**2. Derive wrapper types from the actual return type.**
Read the function's declared return type and build the wrapper to match. WorkOS's field
names, nesting, and flags differ — don't infer from them.

**3. Check dependency versions before generating framework-specific code.**
For Next.js: `cookies()` and `headers()` from `next/headers` are synchronous in v14 and
async in v15. Read `package.json` (or `go.mod`, `requirements.txt`) first.

**4. When making a helper async, propagate to all callers immediately.**
In TypeScript, `async` on a shared utility silently breaks callers that omit `await`. Grep
for all call sites of the changed function and update them in the same pass. The cascade can
span 10–20 files.

**5. Verify published package versions before writing to `package.json` or running `npm install`.**
Don't reuse WorkOS's version number or rely on training data for versions. Before writing any
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
yes, skip to verifying items 5–7 — these are easy to miss even for existing projects.

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

### 5. Configure a JWT Template (almost always needed)

WorkOS AuthKit tokens may include profile fields; Descope tokens do not by default.

- Console → **Project → JWT Templates**
- Add claims: `{"email": "{{user.email}}", "name": "{{user.name}}", "picture": "{{user.picture}}"}`
- Apply the template to your project. Without this step, any code reading `token.email`
will get `undefined` after migration.

### 6. Create roles in the Console (if using RBAC)

Descope roles are referenced by **name**, not by ID. They must be created manually in the
Console before the code that assigns them will work.

- Console → **Authorization → RBAC → + Role**
- Create each role the app references (e.g. `admin`, `member`)

### 7. Define custom attributes (if using tenant/user metadata)

WorkOS Organization `metadata` and User metadata map to Descope `customAttributes`.
Pre-define them in the Console schema before setting them via the SDK.

- **Tenant** custom attributes (the equivalent of WorkOS Organization `metadata`): Console → **Tenants → Custom Attributes** tab → **Create Attribute**
- **User** custom attributes: Console → **Project → Custom Attributes**
- For an entity migration, also create `workosId` (text) and `freshlyMigrated` (boolean) before the first import run. Descope silently drops custom attributes that are not in the schema (the import still reports success), and values must match the declared type (send `true`, not `"true"`). They can also be created with `POST /v1/mgmt/user/customattribute/create` (`type` 1 = text, 3 = boolean).

### 8. Env var summary


| Variable                         | Where to get it                     | Used by                                     |
| -------------------------------- | ----------------------------------- | ------------------------------------------- |
| `DESCOPE_PROJECT_ID`             | Console → Project Settings          | All server-side SDKs                        |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value as above                 | Next.js `AuthProvider` (client-side)        |
| `DESCOPE_MANAGEMENT_KEY`         | Console → Company → Management Keys | Management SDK, SSO/SCIM, Outbound Apps API |


### 9. Consider Widgets for management UI

Before migrating custom profile pages, user management pages, role assignment UI, or admin
SSO/SCIM setup pages, ask whether a Descope Widget or the SSO Setup Suite covers the use case.
See `references/flows-and-widgets.md` → Widgets.

**After completing console setup:** Update `MIGRATION-STATE.md` — check off each completed
item in the Console Setup Checklist, record the Project ID in the file, and set Next Action
to the first code change step.

---

## Step 2: Framework-Specific Migration

WorkOS publishes exactly two SDK families (per the [WorkOS SDKs page](https://workos.com/docs/sdks)):

- **Backend SDKs** (one per language): `workos-node`, `workos-go`, `workos-ruby`, `workos-rust`, `workos-python`, `workos-php`, `workos-php-laravel`, `workos-kotlin` (Java), `workos-dotnet` (.NET). These call the WorkOS API and hold server-side session helpers.
- **AuthKit SDKs** (one per JS framework): `authkit-js`, `authkit-react`, `authkit-nextjs`, `authkit-remix`, `authkit-react-router`, `authkit-tanstack-start`. These handle the login UI + session.

The recipes below cover exactly these SDKs — one section each — annotated with the matching Descope target. Do not infer other frameworks (e.g. Express, Flask, FastAPI); a WorkOS app using those is using the underlying language Backend SDK (`workos-node`, `workos-python`, etc.), so map it via that SDK's section.

> The framework recipes below are stubs listing the WorkOS idioms that need mapping. Confirm the exact WorkOS SDK surface for the user's stack and the matching Descope SDK calls via the Descope MCP or local type declarations before generating any code. Do not ship code from these stubs without verification.

Read `references/implementation-nuances.md` in two passes before writing any code:

1. **General Insights** (always) — covers architecture, feature mapping, and common gotchas that apply to every migration regardless of framework.
2. **Framework section** (use the file's ToC and `offset` to jump directly) — read only the section matching the user's stack.

When a new framework is added to the file, add it to this list.

### Common WorkOS idioms to map (all frameworks)

These idioms are **AuthKit-JS-specific**. Backend-SDK apps (Python, Go, Ruby, PHP, Java, .NET) don't
have these helpers — they instead call the SDK directly (e.g. `workos.userManagement.authenticateWithCode(...)`
for the code exchange and `workos.userManagement.loadSealedSession(...)` for session access), which map
to Descope session validation + the hosted/embedded Flow the same way.

- `withAuth()` / `getUser()` (AuthKit session access) → Descope session validation + an adapter returning the shape callers expect
- `authkitMiddleware()` → Descope session-validation middleware
- AuthKit sealed-session cookie (`WORKOS_COOKIE_PASSWORD`) → Descope signed session JWT in `DS`/`DSR` cookies
- `getSignInUrl()` / hosted AuthKit redirect → embedded Descope Flow component (or hosted Flow), wiring `onSuccess`
- WorkOS callback route (code exchange) → removed/rewritten; Descope handles auth client-side

### Backend SDKs

#### Node.js

*WorkOS SDK: `workos-node` (`@workos-inc/node`) → Descope `@descope/node-sdk`*

- Remove `@workos-inc/node` auth/session usage; add `@descope/node-sdk`
- Validate the `DS` session token via custom middleware calling `descopeClient.validateSession()` (parse the cookie yourself)

#### Go

#### *WorkOS SDK: `workos-go` → Descope Go SDK `github.com/descope/go-sdk`*

- Remove the WorkOS Go SDK; add `descope/go-sdk`
- Session validation: `descopeClient.Auth.ValidateSessionWithToken(ctx, token)` returns `(bool, *descope.Token, error)`
- WorkOS `organizationId` → a Descope **tenant ID**: pass it to management calls (`descopeClient.Management.Tenant()` / user-tenant association); at request time read tenant context off the returned `*descope.Token` (`token.GetTenants()`, or the `dct` claim for the active tenant)

#### Ruby

*WorkOS SDK: `workos-ruby` → Descope Ruby SDK*

- Remove the WorkOS Ruby SDK; add the Descope Ruby SDK
- Validate the `DS` session token via the Descope Ruby SDK in your request lifecycle
- No dedicated recipe in `implementation-nuances.md` yet — follow the Node.js / Python backend patterns and verify against the [Descope Ruby SDK](https://github.com/descope/descope-ruby-sdk).

#### Rust

*WorkOS SDK: `workos-rust` → **No Descope Rust SDK**; validate via Descope JWKS + Management REST API*

- There is no official Descope Rust SDK. Validate the `DS` session JWT directly against Descope's JWKS endpoint (`https://api.descope.com/v2/keys/<project_id>`) using a standard JWT library.
- Management operations (users, tenants, roles, SSO) → call the Descope Management REST API directly.

#### Python

*WorkOS SDK: `workos-python` → Descope `descope` Python SDK*

- Remove the WorkOS Python SDK auth/session usage; add the `descope` Python SDK
- Validate the `DS` session token with `descope_client.validate_session(session_token)` (or validate against Descope's JWKS for a custom authorizer)

#### PHP

*WorkOS SDK: `workos-php` → Descope PHP SDK*

- Remove the WorkOS PHP SDK; add the Descope PHP SDK
- Validate the `DS` token via the Descope PHP SDK in your request lifecycle
- No dedicated recipe yet — follow the Node.js / Python backend patterns and verify against the Descope PHP SDK.

#### Laravel

*WorkOS SDK: `workos-php-laravel` → Descope PHP SDK (no Descope Laravel-specific SDK)*

- Remove the WorkOS Laravel package; use the Descope PHP SDK
- Validate the `DS` token in Laravel middleware
- No dedicated recipe yet — follow the PHP backend patterns and verify.

#### Java

*WorkOS SDK: `workos-kotlin` (Java/Kotlin) → Descope `descope-java`*

- Remove the WorkOS Java/Kotlin SDK; add `descope-java`
- Validate the `DS` token via a filter/interceptor
- No dedicated recipe yet — follow the backend patterns and verify against the [Descope Java SDK](https://github.com/descope/descope-java).

#### .NET

*WorkOS SDK: `workos-dotnet` → Descope `descope-dotnet`*

- Remove the WorkOS .NET SDK; add `descope-dotnet`
- Validate the `DS` token in middleware / a custom auth handler
- No dedicated recipe yet — follow the backend patterns and verify against the [Descope .NET SDK](https://github.com/descope/descope-dotnet).

### AuthKit SDKs

> **Read the session the framework-native way — never hand-parse the JWT on the client.** On
> front-end pages and components, get auth state from the Descope hooks: `useSession()` for the
> session token and auth status, `useUser()` for the user profile, and `useDescope()` for actions
> like `logout()`. Do **not** manually decode the session token or pull claims out of it in client
> code. Server-side session *validation* — `session()` in `@descope/nextjs-sdk/server`,
> `validateSession()` in `@descope/node-sdk` (or the other backend SDKs) — belongs only in backend
> routes, loaders, middleware, and API handlers, never in a rendered client component. This matters
> most with the **React SDK**, where it's tempting to crack open the raw token in a component instead
> of calling `useUser()` / `useSession()`.

#### JavaScript

*WorkOS SDK: `authkit-js` → Descope `@descope/web-js-sdk` + `@descope/web-component`*

- `createClient()` / `authkit.getUser()` / `getAccessToken()` → `@descope/web-js-sdk` (`getSessionToken()`, `isJwtExpired()`, `refresh()`)
- Login UI → `<descope-wc project-id flow-id>` web component, listening for `success` / `error` events
- Logout: `sdk.logout()` + clear stored tokens/cookies

#### React

*WorkOS SDK: `authkit-react` → Descope `@descope/react-sdk`*

- `<AuthKitProvider>` → Descope `<AuthProvider projectId>`
- `useAuth()` (user/session/loading) → `useSession()` + `useUser()` hooks
- **Always read auth state through the hooks** — `useSession()` (token + `isAuthenticated`) and `useUser()` (profile), with `useDescope()` for actions. Never decode the session token by hand in a component, and never call backend `validateSession()` from client code; that runs only on the server.
- `signIn()` / hosted redirect → embedded `<Descope flowId>` component, wiring `onSuccess`
- Logout: `sdk.logout()` via `useDescope()` hook
- No dedicated recipe yet — follow the Next.js client-side patterns and verify each method against docs.

#### Next.js

*WorkOS SDK: `authkit-nextjs` → Descope `@descope/nextjs-sdk` + `@descope/node-sdk`*

- `authkit-nextjs` → `@descope/nextjs-sdk` + `@descope/node-sdk`
- AuthKit `<AuthKitProvider>` → Descope `AuthProvider` (takes `projectId`; must use `NEXT_PUBLIC_` prefix)
- `withAuth()` / `useAuth()` → `session()` (server) + `useSession()` / `useUser()` (client)
- Remove the AuthKit callback route — verify Descope's client-side handling
- `authkitMiddleware()` → Descope `authMiddleware(options)`
- Logout: `sdk.logout()` via `useDescope()` hook + clear cookies (two-step)
- **Client vs. server session access** — `session()` from `@descope/nextjs-sdk/server` is server-only; `useSession()`/`useUser()` from `@descope/nextjs-sdk/client` are client-only. Using `session()` in a client component compiles but throws at runtime. Verify exact exports before writing imports.

#### Remix

*WorkOS SDK: `authkit-remix` → Descope `@descope/react-sdk` + `@descope/web-js-sdk` (no Descope Remix SDK)*

- `authkitLoader` / `authLoader()` loaders → custom Remix loaders that validate the session token (`@descope/web-js-sdk` / `@descope/node-sdk`) and gate routes
- `getSignInUrl()` → embedded Descope component (`@descope/react-sdk`) or hosted Flow
- Logout: clear `DS`/`DSR` cookies in an action + `sdk.logout()`
- No dedicated recipe yet — follow the Next.js (server + client split) patterns and verify.

#### React Router

*WorkOS SDK: `authkit-react-router` → Descope `@descope/react-sdk`*

- Same shape as Remix (`authkit-react-router` is the React Router 7+ port): loader-based session checks → custom loaders + Descope session validation
- Login via embedded Descope component; logout via `sdk.logout()` + cookie clear
- No dedicated recipe yet — follow the React / Remix patterns and verify.

#### TanStack Start

*WorkOS SDK: `authkit-tanstack-start` → Descope `@descope/react-sdk` / `@descope/web-js-sdk` (no Descope TanStack SDK)*

- Server-route session helpers → TanStack server functions validating the Descope session token
- Login via embedded Descope component; logout via `sdk.logout()` + cookie clear
- No dedicated recipe yet — follow the Next.js / React patterns and verify.

### Path A: OIDC Compatibility (lower risk, incremental)

Descope exposes standard OIDC endpoints. If the app uses a **generic OIDC client library**
pointed at WorkOS, it can point at Descope's OIDC issuer instead with minimal code changes.

**First classify the current integration — the OIDC endpoints only matter for the hosted-page case.**
Before considering Path A, determine how the app authenticates today:
- **Hosted AuthKit page** (users are redirected to a WorkOS-hosted login URL through a generic
  OIDC/OAuth client) → the Descope OIDC endpoints below are directly relevant; re-point the OIDC
  client at Descope's issuer.
- **Embedded AuthKit** (AuthKit's own SDK/components rendering login inside the app) **or custom code**
  against the WorkOS SDK → the OIDC endpoints are largely irrelevant; this is a Descope-native SDK +
  Flow migration (Path B), not an issuer swap.

Don't recommend Path A until you've confirmed the app uses a standard OIDC/OAuth client against the
hosted page.

> Many WorkOS apps use AuthKit's own SDK rather than a generic OIDC client, in which case Path A may not apply cleanly. Confirm whether the app uses a standard OIDC client before recommending this path. Verify the Descope OIDC endpoint table below against current docs.


| Endpoint      | Descope                                                       |
| ------------- | ------------------------------------------------------------- |
| Issuer        | `https://api.descope.com`                                     |
| Authorization | `https://api.descope.com/oauth2/v1/authorize`                 |
| Token         | `https://api.descope.com/oauth2/v1/token`                     |
| UserInfo      | `https://api.descope.com/oauth2/v1/userinfo`                  |
| JWKS          | `https://api.descope.com/__ProjectID__/.well-known/jwks.json` |


**Good for:** Teams that want to swap the IdP first, then refactor to Descope-native SDKs
later. Preserves existing OIDC client code.

**Caveats:** Claim shapes differ, token lifetimes may differ, and WorkOS organization-scoped
login / SSO must be rebuilt in Descope regardless of path.

> **For B2B apps using WorkOS Organizations:** Path A preserves only a fraction of the work;
> the management SDK, org/tenant-scoped login, SSO/SCIM setup, and claim mapping require full
> migration regardless. **Path A savings are minimal for B2B workloads** — account for this
> when estimating effort.

**After completing framework code changes:** Update `MIGRATION-STATE.md` — mark each
modified file as Done in the Files Inventory, update Current Phase and Next Action, and
log any non-obvious decisions made (adapter types kept, async cascade scope, etc.).

---

## Step 2.5: Non-Code File Updates

Scan for WorkOS references in non-code files after updating source files.

### `.env.example` / `.env.template` / `.env.sample`

```
# REMOVE
WORKOS_API_KEY=
WORKOS_CLIENT_ID=
WORKOS_REDIRECT_URI=
WORKOS_COOKIE_PASSWORD=

# ADD
DESCOPE_PROJECT_ID=             # Console → Project Settings
NEXT_PUBLIC_DESCOPE_PROJECT_ID= # Next.js only — same value as above
DESCOPE_MANAGEMENT_KEY=         # Console → Company → Management Keys (only if using management SDK)
```

Run `grep -r "WORKOS"` to find all env var references — `.env.example`, Docker, CI, shell scripts.

### README / docs

Search all `.md` files for WorkOS references. At minimum, update:

- **Setup section** — replace "create a WorkOS app / AuthKit setup" instructions with Descope Console setup steps
- **Environment variables section** — reflect the reduced env var set
- **Run instructions** — replace WorkOS dashboard steps with Descope Console steps
- **Auth flow diagrams or descriptions** — update to reflect Descope's cookie-based approach

### Docker / CI files

Check `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, and any CI config for
`WORKOS_`* env var declarations. Update them to `DESCOPE_`*.

### Setup / bootstrap scripts

When the migration includes a setup or seed script (e.g., `scripts/bootstrap.mjs`, `scripts/seed.ts`), split it into two parts:

1. **Console setup** (cannot be scripted): Flows, email templates, MFA configuration, branding/Styles, SSO Setup Suite — configure these in the Descope Console. Represent them as a Phase 1 checklist in `MIGRATION-PLAN.md`.
2. **SDK automation** (can be scripted): role creation (`management.role.create()`), tenant creation, access key provisioning, SSO/SCIM config. Preserve these as a Node.js/Python script using the Descope Management SDK.

**After completing non-code file updates:** Update `MIGRATION-STATE.md` — mark env files,
README, and CI config done in the Files Inventory, and advance Next Action.

---

## Step 3: Feature Migration Mapping

For each WorkOS feature confirmed in triage, write a short paragraph: what it accomplishes, the
best Descope approach for that goal, what's different, and what action is required. Reason about
intent, not just the API surface — the best approach may be a Flow, Widget, SSO Setup Suite, or
Console configuration rather than a direct SDK equivalent. Only recommend SDK/API code when
programmatic control is genuinely required, and verify every method name against the Descope MCP server
before writing it. Include only confirmed features.

### Users, Organizations & Roles → Descope Migration Script + JIT Provisioning

This is usually the first thing to settle, because it drives the cutover plan. **The agent writes
the migration script** for the user's setup, from the endpoints and mapping below; there is no
WorkOS module in the [descope-migration](https://github.com/descope/descope-migration) repo, but its
other modules (e.g. `src/frontegg_migration.py`) show the Descope request shapes. A WorkOS page in
Descope's [migration docs](https://docs.descope.com/migrate) may or may not be published when you
run this — check before linking to it. **Never tell the user to open a guide you have not confirmed exists.**

**Recommend Path 1 with Path 2 as its cutover:** import everyone (with password hashes where
WorkOS support has provided them), switch the app in one step, and keep the Path 2 connector in the
Flow for a transition period. That avoids a freeze, a final re-export, and downtime.

**Path 1 — Full migration (recommended default).** Export permissions, roles, organizations,
memberships, and users from the WorkOS API, then create the matching objects in Descope in
dependency order: **permissions → project roles → tenants → tenant roles → users**. Users cannot be
created with tenant and role assignments that do not exist yet.

Things the script must get right:

- **Pagination is cursor-based.** Pass `limit=100&order=asc` and follow `list_metadata.after` until it is `null`. Several endpoints default to `order=desc`, where the cursor semantics are reversed.
- **Memberships need a filter.** `GET /user_management/organization_memberships` requires `organization_id` or `user_id`, and returns only `active` memberships unless you pass `statuses[]=active&statuses[]=inactive&statuses[]=pending`. Loop per organization.
- **Roles live under `/authorization`.** `GET /authorization/roles` returns environment roles; `GET /authorization/organizations/{id}/roles` returns environment **and** organization roles, so keep only `type: "OrganizationRole"` from it and create those as tenant-scoped Descope roles. Each role's `permissions` is an array of permission slugs.
- **Skip `system: true` permissions.** Every WorkOS environment lists built-in `widgets:*` permissions (for WorkOS's own Widgets) with `system: true`, and the default `admin` role carries one. They mean nothing in Descope — don't create them, and strip them from role `permissionNames`.
- **Read `roles[]`, not just `role`.** A membership carries `role` (one) and `roles[]` (several, when Multiple Roles is on). Map every slug to `userTenants[].roleNames`; the WorkOS role **slug** becomes the Descope role **name**.
- **Keep the WorkOS organization ID as the Descope tenant ID** (`org_…`), so the app's database rows keyed by `organization_id` still match. Store the user's WorkOS ID in a `workosId` custom attribute for the same reason.
- **Descope fails quietly, so verify after every run.** Batch create reports success but drops a role name that doesn't exist yet, and drops custom attributes not defined in the project schema. Reload a sample of users and compare tenants, roles and custom attributes against the plan.
- **Re-running batch create is not a re-sync.** For a user that already exists it still reports the user as created and adds new tenant memberships, but leaves `name` and custom attributes unchanged and removes nothing. The post-switch re-sync uses the user update and tenant-role APIs instead.
- Use the email as `loginId`, set `verifiedEmail` from `email_verified`, and import verified organization domains as tenant `selfProvisioningDomains` only if the app wants domain-based tenant routing.

**Passwords come from WorkOS support, not the API.** WorkOS deliberately has no API or dashboard
export of password hashes. The user emails WorkOS support for the environment(s) they need and gets a
CSV (`email`, `password_hash`, `first_name`, `last_name`) by secure file transfer; parse it with a
real CSV parser, since some hashes contain commas. Passwords set in WorkOS are **bcrypt**
(`$2b$10$…`) and import as-is with `hashedPassword: { bcrypt: { hash } }`. Hashes WorkOS itself
imported keep their original format: argon2, pbkdf2 and firebase-scrypt PHC strings must be split
into Descope's `argon2` / `pbkdf2` / `firebase` fields; plain scrypt and WorkOS's
`$bcrypt-pbkdf2-*` / `$bcrypt-ssha*` wrappers have no Descope equivalent, so treat those users as
hashless. SSO-, social- and Magic Auth-only users have no hash and need none.

The CSV is a snapshot. A user who changes or resets their password in WorkOS after the export
still has the **old** hash in Descope, so the old password works and the new one fails. Request the
export as close to the switch as possible, and during the transition route a failed Descope password
check for an imported-hash user to the Path 2 connector, then **Update Password** on success. If
password changes between export and switch can't be bounded, force a reset for the affected users.

Set a `freshlyMigrated` custom attribute only on users who **have a WorkOS password but no usable
hash**. Users missing from the support CSV have no WorkOS password (SSO-, social- or Magic Auth-only;
`GET /user_management/users/{id}/identities` and the organization's connections confirm it) — don't
flag them, or the Flow sends them to a password check they can't pass and later to a forced reset.
If there is no CSV at all, you can't tell who has a password: flag everyone without an OAuth
identity or an SSO-only organization. During
the transition, the Flow sends those users through the Path 2 connector so WorkOS checks their
password. Because they already exist in Descope, the Flow signs them in with OTP or magic link and
stores the password with **Update Password** (not Sign Up / Password), then clears the flag. After
WorkOS is turned off, remaining `freshlyMigrated` users verify their email, then reset their password
or go passwordless. JIT creates missing users but doesn't update roles of imported users, so
re-sync organizations, memberships and roles once right after the switch. Imported users show status `invited` until their first sign-in; that is expected, not a failed import.

**Path 2 — JIT migration with a Generic HTTP Connector.** Keeps passwords for users without an
exported hash, either as the cutover for Path 1 or on its own. The Descope Flow collects email and
password, and a
[Generic HTTP Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http)
calls `POST https://api.workos.com/user_management/authenticate` with `grant_type: "password"`,
`client_id`, `client_secret` (the `sk_` API key — keep it in the connector, never in the Flow
screen), `email` and `password`. A success returns `user`, `organization_id` and tokens. WorkOS can
also answer with `email_verification_required`, `mfa_challenge`, `mfa_enrollment` or
`organization_selection_required`: those mean **the password was correct** and WorkOS wants another
step, so treat them as a successful check rather than a failure. **But `mfa_challenge` and
`mfa_enrollment` mean the account needed MFA in WorkOS**, and TOTP doesn't transfer: the Flow must
enroll or challenge a Descope MFA factor for these users before it issues a session, or they end up
with password-only access. The endpoint is rate limited to
10 requests per minute per email. Later sign-ins skip WorkOS entirely.

The JIT path keeps WorkOS running for a transition period the user chooses, and needs **dual token
validation** in the backend only if WorkOS sessions must stay valid after the switch (see Step 4).

The script's shape:

```text
GET /authorization/permissions                          → POST /v1/mgmt/permission/create {name, description}
GET /authorization/roles                                → POST /v1/mgmt/role/create {name, description, permissionNames}
GET /organizations                                      → POST /v1/mgmt/tenant/create {id, name, customAttributes}
GET /authorization/organizations/{id}/roles (org-only)  → POST /v1/mgmt/role/create {…, tenantId}
GET /user_management/organization_memberships (per org) ┐
GET /user_management/users                              ┴→ POST /v1/mgmt/user/create/batch {users: [...], invite: false}
```

WorkOS calls use `Authorization: Bearer sk_…`; Descope management calls use
`Authorization: Bearer <ProjectID>:<ManagementKey>`. See `references/implementation-nuances.md` →
**User migration: WorkOS export → Descope import** for the field mapping, hash conversion, and
data-quality issues.

**Effort: Low–Medium** for the scripted export on a clean data set; **Medium–High** with the JIT
connector, which is Flow engineering rather than a one-off script.

### AuthKit → Descope Flows + JWT Templates

WorkOS AuthKit handles login UI, authentication methods, users, sessions, and enterprise login
routing. Descope splits these responsibilities across a Flow (UI + methods), session validation
(SDK), Users/Tenants, and JWT Templates (profile claims).


| WorkOS                                                           | Descope                                                          |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| Hosted AuthKit login UI                                          | [Descope Flows](https://docs.descope.com/flows)                  |
| `withAuth()` / `getUser()` session access                        | `validateSession()` + adapter returning the shape callers expect |
| AuthKit user object                                              | Descope User (profile fields via JWT Template)                   |
| Auth method config (password, social, passkeys, MFA, magic auth) | Methods toggled in Console + added as Flow steps                 |


Use Flows for the user-facing journey whenever possible; write custom SDK calls only when Flows
cannot express the requirement. Ask which auth methods are enabled before recommending details.
**Effort: Low–Medium** (mostly SDK/UI/session swap; token differences matter).

### Organizations → Descope Tenants

- WorkOS `organizationId` → a Descope **tenant ID** (the argument you pass to `management.tenant.*` / `management.user.*` calls). At request time the tenant also appears in the session as the nested `tenants` object (`{ tenantId: { roles, permissions } }`) plus `dct` for the active tenant.
- WorkOS org-scoped login → Descope **tenant routing** (also called **home realm discovery**). Two
  main approaches:
  1. **Domain-based routing** — set an email domain on the tenant (when not using SSO) or an SSO
     domain on the tenant's SSO configuration (when using SSO). Descope resolves the tenant/IdP from
     the user's email domain at login.
  2. **Explicit tenant slug** — pass a tenant name, ID, or slug hardcoded in the app (e.g.
     per-customer login URL or `sso.start(tenantId, ...)` for a known tenant). Use when each customer
     has a dedicated login path rather than a shared email-entry screen.
- Users are project-level in Descope; associated with tenants, not created per-tenant
- Organization `metadata` → tenant `customAttributes` (pre-define in the Console schema)

Confirm the one-Organization-to-one-Tenant mapping before writing code — it ripples into SSO, SCIM,
RBAC, and domain routing. **Effort: Medium** (clean conceptually; most `organizationId` usage is
management calls that take a tenant ID, with a smaller set of session reads that change shape).

### Enterprise SSO → Descope Tenant SSO

**Preferred approach — SSO Setup Suite:** before migrating any management-SDK SSO calls, ask whether
the no-code SSO Setup Suite removes the need for that code. It guides tenant admins through per-tenant
SAML/OIDC setup with IdP-specific instructions (Okta, Microsoft Entra ID (formerly Azure AD), Google Workspace, etc.) — no
engineering involvement for new tenant onboarding.

**Multiple SSO configurations per tenant.** Descope supports more than one SSO/IdP configuration on a
single tenant: each tenant has a **Default SSO Configuration** plus optional **additional named SSO
configurations** (Console or API/SDK). At login, Descope selects the right IdP by **domain-based
routing** (e.g. `@acme.com` → Acme's Okta, `@globex.com` → Globex's Microsoft Entra ID), a **tenant-specific
login URL**, an explicit SSO configuration ID, or Flow logic. SCIM provisioning can be scoped per SSO
configuration, and each configuration can have its own SSO Setup Suite link. See
`references/flows-and-widgets.md` and [Descope Multi-SSO](https://docs.descope.com/sso/multi-sso).

Use `AskUserQuestion` to ask **two** things here:
1. Does any single customer use **multiple IdPs** (or did they create multiple WorkOS Organizations for
   the same customer to handle different SSO connections/domains)? If yes, plan to consolidate into one
   Descope Tenant with multiple SSO configurations rather than multiple tenants.
2. Does the app need **programmatic** SSO configuration (CI/CD provisioning, API-driven onboarding), or
   do tenant admins configure SSO themselves? If the latter, the SSO Setup Suite + Tenant Profile
   Widget may eliminate the SDK calls entirely. See `references/flows-and-widgets.md` → SSO Setup Suite.

**SDK path (when programmatic SSO is needed):**


| WorkOS                      | Descope                                           |
| --------------------------- | ------------------------------------------------- |
| SAML connection (`sso.`*)   | `management.ssoApplication.createSamlApplication` |
| OIDC connection             | `management.ssoApplication.createOidcApplication` |
| Per-Organization connection | Per-tenant SSO (Console → SSO or Management SDK)  |


(Verify exact method names against the Descope MCP server.) Ask whether SSO is configured by internal
engineers or by customer admins. **Effort: Medium** — setup recreated per tenant.

**Runtime login calls — always use `sso.start` / `sso.exchange`, never the OAuth flow.** When code
initiates an enterprise SSO login (the equivalent of WorkOS's `sso.getAuthorizationUrl()` +
`sso.getProfileAndToken()`), call the Descope SDK's `sso.start(tenant, redirectUrl, ...)` to begin
the flow and `sso.exchange(code)` to complete it. Use these **regardless of the IdP's underlying
protocol** — even when the tenant's SSO is configured in Descope as OIDC/OAuth — because `sso.start`
resolves the **tenant-level SSO configuration** (the correct IdP, domain-based routing, and
connection settings) for you. Do **not** reach for the generic `oauth.start` / `oauth.exchange`
functions for enterprise SSO: those drive project-level social/OAuth providers and will not apply a
tenant's SSO config. Rule of thumb: tenant/enterprise SSO → `sso.*`; social or generic OAuth login →
`oauth.*`.

**Don't rebuild provider-specific SSO UI — let tenant config do the routing.** Especially when the
app uses the **backend SDKs**, do not migrate or recreate any per-IdP login UI (separate "Sign in
with Okta" / "Sign in with Microsoft Entra ID" buttons, provider-picker screens, etc.), regardless of which
SSO provider the WorkOS code names. In Descope the IdP is defined as **tenant SSO configuration**,
and a single `sso.start` call resolves it automatically via **home realm discovery** — either
**domain-based routing** (email domain or SSO domain on the tenant config) or an **explicit tenant
slug** (tenant ID/name hardcoded in source). So the login surface just collects an email (or targets a
known tenant) and calls
`sso.start`; Descope selects the correct IdP from config. Keep the UI generic and push all
provider-specific details into Console/tenant configuration.

### Directory Sync / SCIM → Descope SCIM / Tenant Provisioning

WorkOS Directory Sync maps to Descope SCIM provisioning. **Treat this as a continuing pipeline, not
a one-time import** — enterprise directories keep pushing create/update/suspend/delete events after
cutover, so every directory must be re-pointed at Descope before cutover or provisioning silently
breaks.


| WorkOS Directory Sync                      | Descope                                  |
| ------------------------------------------ | ---------------------------------------- |
| SCIM endpoint + bearer token per directory | Descope SCIM endpoint + token per tenant |
| Directory user create/update/deprovision   | Tenant user provisioning lifecycle       |
| Directory groups                           | Group → role mapping in Descope          |
| `dsync.`* / directory webhooks             | Descope provisioning events / connectors |


Identify every directory, whether groups are synced, and whether groups map to roles.
**Effort: Medium–High** (lifecycle, groups, deprovisioning, and role mapping can be subtle).

### Admin Portal → Descope SSO Setup Suite / Widgets

WorkOS Admin Portal is a hosted self-serve UI where customer IT admins configure SSO, Directory Sync,
and domain verification. Do not default to rebuilding it as custom code.

- Generated portal links (`portal.generateLink(...)`) → SSO Setup Suite hosted/embedded flow or Tenant Profile Widget
- SSO setup screens → SSO Setup Suite
- Directory Sync / domain setup → corresponding Widgets

Ask which admin workflows are hosted by WorkOS today before choosing a replacement. **Effort: Medium**
— may remove custom code, but portal-link workflows need replacement.

### RBAC → Descope RBAC

WorkOS roles come in two scopes, and they map to Descope's two scopes:

- **Environment-level role** (defined on the WorkOS environment, available across all organizations) → **Descope project-level role** (applies across all tenants).
- **Organization-scoped role** (a WorkOS "custom role", defined for a specific organization) → **Descope tenant-level role**, created by passing a `tenantId` to `management.role.create(...)` (it surfaces per-tenant when you check roles on the session, e.g. `validateTenantRoles`).


| WorkOS                                                    | Descope                                          |
| --------------------------------------------------------- | ------------------------------------------------ |
| `role`                                                    | `role`                                           |
| `permission`                                              | `permission`                                     |
| Environment-level role (applies across all organizations) | Project-level role (applies across all tenants)  |
| Organization-scoped role ("custom role")                  | Tenant-scoped role                               |
| `roleSlug` reference                                      | Descope role **name** (not ID)                   |
| IdP group → role mapping                                  | Group-to-role mapping (SSO Configuration / SCIM) |


SDK: `descopeClient.management.role.create(name, description, permissionNames, tenantId)` (verify
the exact function name depending on the language sdk). Pass `tenantId` to create a **tenant-level**
role (the equivalent of a WorkOS organization-scoped/custom role); omit it for a **project-level**
role (the equivalent of a WorkOS environment-level role). Roles must exist in the Console before
assignment. Check whether each WorkOS role is environment- or organization-scoped and where checks
happen (middleware, API routes, DB queries, frontend). **Effort: Medium.**

### Fine-Grained Authorization (FGA) → Descope ReBAC / AuthZ

Authorization model must be translated and validated. Schema translation example:

```
# WorkOS FGA
Resource type: project
Parent: workspace

Permissions:
- project:view
- project:edit
- project:delete

Roles:
- project-viewer
  - project:view

- project-editor
  - project:view
  - project:edit

# Descope ReBAC DSL
type document
  relation owner: user
  relation viewer: user
  permission can_view: owner | viewer
```

**Descope ReBAC schema DSL** — use this syntax to author the Descope ReBAC schema:

```
Syntax                             Description          Example
---------------------------------  -------------------  ----------------------------
type <name>                        Define a type        type user
relation <name>: <type>            Define a relation    relation owner: user
|                                  Union (OR) operator  user | group
#                                  Relation reference   Group#member
.                                  Traverse relation    parent.owner
permission <name>: <expression>    Define a permission  permission can_edit: owner
```


| Operation      | WorkOS FGA                | Descope ReBAC                                         |
| -------------- | ------------------------- | ----------------------------------------------------- |
| Write relation | `fga.writeWarrant({...})` | `descopeClient.management.fga.createRelations([...])` |
| Check          | `fga.check({...})`        | `descopeClient.management.fga.check([...])`           |


(Verify exact WorkOS and Descope shapes against current docs.) Identify resources,
relationships/privileges, where checks run, and any hierarchical inheritance. **Effort: High** —
require a dedicated model review.

### Audit Logs → Descope Audit Webhook / Events

WorkOS Audit Logs map to Descope audit events, the Audit Webhook Connector, or other connectors
depending on the use case. Determine whether the app writes events to WorkOS, reads them back, shows
them to customer admins, or requires them for compliance. **Effort: Medium.**

### Radar → Descope Fingerprinting + Flow Security

**Mechanism difference (read this first):** WorkOS Radar is a dashboard toggle layered on top of
AuthKit — it collects device-fingerprint signals and *automatically* blocks / challenges / notifies
based on the actions you enable, with no app code. Descope has **no single equivalent toggle**.
Instead you reproduce Radar's behavior by adding Descope's built-in fingerprinting/risk signals to
your **Flow** and branching on them. So "configuring Radar" becomes "designing the Flow."

Descope surfaces risk signals as `riskInfo` inside a Flow. `riskInfo.botDetected` and
`riskInfo.riskScore` require adding a **Fingerprint / Assess** action immediately after the
login/signup screen; `riskInfo.impossibleTravel` and `riskInfo.trustedDevice` do not. For stronger
detection, layer in fraud/CAPTCHA connectors (reCAPTCHA Enterprise, Turnstile, Telesign,
Fingerprint, Forter, Sardine).


| Radar action  | What it does in WorkOS                                             | Descope equivalent                                                                                                                                                                  |
| ------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Block**     | Auth fails even with valid credentials                             | Flow conditional after Fingerprint Assess: on high `riskInfo.riskScore` / `riskInfo.botDetected`, branch to a deny/failure screen and end the Flow without issuing a session        |
| **Challenge** | Sends an email (or SMS) OTP step-up                                | Risk-based step-up in the Flow: branch the high-risk path into an OTP/MFA step or a CAPTCHA connector (reCAPTCHA / Turnstile) before continuing                                     |
| **Notify**    | Sends an informational email to user/admin; sign-in still proceeds | Compose it: on the risk branch, fire an email/messaging connector or an outbound webhook (or rely on Descope audit events) to alert the user/admin, while letting the Flow continue |


**Detection mapping** (verify current signal names against docs):

- Bot detection → `riskInfo.botDetected` (needs Fingerprint Assess) + CAPTCHA connectors
- Impossible travel → `riskInfo.impossibleTravel`
- Unrecognized device → `riskInfo.trustedDevice` (invert: untrusted = unrecognized)
- Brute force / repeat sign-up / stale accounts / managed lists (disposable email, sanctioned countries) / custom allow-deny restrictions → no single built-in signal; reproduce via `riskInfo.riskScore` thresholds, connectors, or custom Flow conditions. Flag any of these in use for dedicated design.

Ask whether each Radar detection is set to **block, challenge, or notify**, and whether app logic
depends on its decisions (vs. pure config). **Effort: Medium** — Console/Flow configuration rather
than app code, but the decisioning must be *rebuilt* in the Flow, not simply toggled on.

### Pipes → Descope Outbound Apps

WorkOS Pipes (connected third-party accounts with OAuth token storage/refresh) maps to Descope
Outbound Apps.

Users connect accounts client-side:

```
sdk.outbound.connect(appId, { redirectURL, scopes })
```

Fetch stored tokens server-side:

```
POST https://api.descope.com/v1/mgmt/outbound/app/user/token
Authorization: Bearer {projectId}:{managementKey}
Body: { "appId": "google-calendar", "userId": "U2abc...", "scopes": [...] }
```

Ask which providers are connected, where tokens are used (including AI agents / background jobs), and
whether users must reconnect accounts or tokens can be migrated. **Effort: Medium.**

### Webhooks / Events → Descope Webhooks / Connectors / Events


| WorkOS                                               | Descope                                           |
| ---------------------------------------------------- | ------------------------------------------------- |
| Webhook endpoint + signing secret                    | Descope webhook/connector + signature validation  |
| `user.created` / `organization.`* / `dsync.`* events | Corresponding Descope events / connector triggers |


Search the codebase for webhook handlers; update event names, signature/validation logic, and
payload handling. Identify which event types are business-critical. **Effort: Medium.**

### Domain Verification / Custom Domains → Descope Custom Domains and Tenant Routing

WorkOS Domain Verification maps most closely to Descope’s tenant SSO domain verification, where the customer proves ownership of their email domain with a DNS TXT record. Descope Custom Domains are separate: they configure a CNAME such as auth.example.com so Descope authentication endpoints, cookies, OAuth callbacks, and related URLs can use your own domain.
a custom auth domain. **Effort: Low–Medium.**

### Widgets → Descope Widgets

WorkOS Widgets (org switching, Directory Sync setup, SSO setup, domain verification, audit log
streaming, API keys) should be evaluated against Descope Widgets. If a Descope Widget covers the
workflow, prefer it over custom migration code. See `references/flows-and-widgets.md` → Widgets.

### MCP Auth / Connect → Deeper Review Required

May map to Descope Inbound Apps, OAuth app patterns, or custom MCP authorization. **Do not generate
implementation code until the exact WorkOS usage is understood.** Determine whether WorkOS is acting
as an OAuth provider, an OAuth client, or both. **Effort: Medium–High — flag for dedicated review.**

### Vault → Possibly Out of Scope

WorkOS Vault and EKM (encrypting/storing/controlling access to sensitive data) may have no direct Descope
identity equivalent. Flag it separately and ask whether it is part of the identity migration or a
separate secrets/data-security effort. **Do not present it as an SDK swap.**

### Feature Flags → Usually Out of Scope

WorkOS Feature Flags are usually not part of an auth migration. If they are used for access control,
some behavior may map to Descope roles/permissions, but general feature flagging should be treated as
out of scope.

---

## Step 4: Critical Gotchas (Always Cover These)

### JWT Claims Are Not the Same

Descope session JWTs contain `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions`, and `dct` by
default. They do **not** contain `email`, `name`, or `picture`. WorkOS AuthKit tokens may expose
some profile fields, so code that reads them directly will break after migration.

`dct` and `tenants` only matter when you read a user's tenant context **from their session at
request time** — not for tenant administration, which is done by tenant ID through
`management.tenant.*` / `management.user.*`. When you do read the session, `dct` (Descope Current
Tenant) is a flat string holding the active tenant ID — the direct equivalent of WorkOS's
`organizationId` — and `tenants` is a keyed object (`{ [tenantId]: { roles, permissions } }`) for
per-tenant roles/permissions. Prefer the SDK's role/permission helpers (e.g.
`validateTenantRoles(authInfo, tenantId, [...])`) over reading these claims by hand; reach for `dct`
when you only need the active tenant ID.

**Action required:** Configure a JWT Template in the Descope Console to add `email`,
`name`, and any other profile fields the app reads from the token.

### Plan Dual Token Validation for Any Phased Cutover

If WorkOS sessions must stay valid after the switch (a phased rollout, or services that move at
different times), the backend validates **both** tokens during the transition: read `iss` / `kid`
from the unverified token **only to choose a verifier**, then verify the signature against that
provider's own JWKS and pin the issuer. Never read claims before verification, and never fall
through from a failed Descope check to the WorkOS branch without full verification there. A
one-step switch with a forced re-login doesn't need this. Remove the WorkOS branch as a scheduled
follow-up after cutover.

### Sealed Sessions Become Signed JWTs

WorkOS AuthKit uses an encrypted/sealed session cookie protected by `WORKOS_COOKIE_PASSWORD`.
Descope issues a signed session JWT in the `DS` cookie (refresh in `DSR`). The sealing password is
no longer needed, and code that unseals/inspects the WorkOS cookie must be replaced with Descope
session validation (`validateSession()`), which returns decoded JWT claims.

### Logout Is Two Steps

1. Call `descopeClient.logout(refreshToken)` to invalidate server-side
2. Clear `DS` and `DSR` cookies

Skipping either step leaves a broken state.

### Audience Validation Is Opt-In

Descope session tokens have no `aud` claim by default. Apps that rely on audience-scoped API access
must (1) configure a custom `aud` claim in JWT Templates and (2) pass `audience` to
`validateSession()` on the backend.

### Organization Handling: Tenant IDs, Not Token Parsing

Most code that references a WorkOS `organizationId` (and `connectionId` / `directoryId`) is
management/admin code — it becomes a Descope **tenant ID** passed to `management.tenant.*` /
`management.user.*` calls. Only request-time code that read the org off the WorkOS session changes
shape: Descope exposes the active tenant as `dct` and membership as the nested `tenants` object,
read off the validated session (ideally via SDK helpers). Grep for all `organizationId` reads and
sort them into these two buckets — by-ID management calls vs. session reads — before updating.

### One Token, Not Provider-Specific Access Tokens

Forward the Descope session JWT (`DS` cookie) as `Authorization: Bearer <DS>` to API servers. There
is one session token; downstream services validate it with `validateSession()`.

### No Drop-In Middleware

Descope has no `authkitMiddleware()` equivalent package. The middleware is ~20 lines of custom code
that reads the `DS` cookie and calls `validateSession()`.

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

### Env Var Reduction

WorkOS: `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_REDIRECT_URI`, `WORKOS_COOKIE_PASSWORD` (4+).
Descope: `DESCOPE_PROJECT_ID` only (+ `DESCOPE_MANAGEMENT_KEY` for management ops).

---

## Step 5: Automated Testing

Run the app and verify it works — don't just hand over a checklist.

### Phase 0: Final stale-import sweep (BLOCKING)

```bash
grep -r "@workos-inc\|workos\|authkit" \
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
mvn compile -q      # Java/Maven
./gradlew compileJava compileKotlin  # Java/Gradle
dotnet build        # .NET
```

**Do not proceed until compilation exits with zero errors.**

**If compilation fails, diagnose by error message:**

- `Cannot find module '@workos-inc/...'` → stale import; re-run Phase 0
- `Property 'X' does not exist on type 'AuthenticationInfo'` → wrapper built against WorkOS shape; re-derive
- `'await' expression is not allowed in synchronous contexts` → async cascade gap
- `Object is possibly 'undefined'` on session fields → add null check or early return

```bash
npm run dev   # or: python main.py / go run . / flask run / etc.
```

### Phase 2: Run existing tests

```bash
npm test   # or: pytest / go test ./... / etc.
```

Auth-related test failures usually mean: a mock or fixture still uses WorkOS shapes, or a
test validates JWT claims that are now missing (e.g., `email` without a JWT Template), or a test
still uses `organizationId` where the code now passes a Descope tenant ID (management calls) or
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

- Phase 0 grep returns zero WorkOS references
- Phase 1 compilation passes with zero errors
- Phase 1 server starts and stays running
- Phase 3 root path returns 2xx or 3xx (not 5xx)
- Phase 3 protected routes return 302 or 401 (not 500)

---

## Step 6: Post-Migration Summary (Required)

Every migration produces a `MIGRATION-SUMMARY.md` covering what was done, manual setup
remaining, and behavioral differences that matter before production.

### MIGRATION-SUMMARY.md

1. **What was migrated** — a table mapping each WorkOS concept to its Descope replacement
2. **Behavioral differences and open questions** — numbered list of significant differences
  between the WorkOS and Descope implementations. For each item: WorkOS behavior, Descope
   behavior, action required.
3. **Pre-deploy checklist** — actionable checkbox items for everything that must happen
  before the migrated app can run. Prominently include all Console setup tasks (project, Flow,
   JWT template, tenants, SSO/SCIM) and the SCIM re-point — these are the things easiest to
   forget because the code compiles without them.

---

## Step 7: Output Format

Write a numbered migration guide in Markdown, scoped to the user's stack. Use code
snippets and direct doc links. Always include the MIGRATION-SUMMARY.md deliverable (Step 6).

For complex migrations (Directory Sync/SCIM, FGA, Pipes, MCP Auth), flag the high-effort items
explicitly with estimated complexity (Low/Medium/High) so the user can plan.

---

## Reference Files

- `references/implementation-nuances.md` — Verified migration patterns, code-level diffs, and edge
cases for several frameworks.
- Descope Docs: [https://docs.descope.com](https://docs.descope.com)
- WorkOS Migration Guide: [https://docs.descope.com/migrate](https://docs.descope.com/migrate)  
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

