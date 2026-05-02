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

This skill guides self-service migrations from Auth0 to Descope. It runs in three parts:

1. **MCP Check** — confirm whether the Descope Docs MCP is available and suggest installing it if not
2. **Migration Plan** — gather context via triage questions, analyze the codebase's auth touchpoints, and produce a human-readable `MIGRATION-PLAN.md` for the user to review
3. **Execution** — if the user confirms they want to proceed, execute the plan

Do not collapse these parts or skip ahead. The plan must be reviewed before code changes begin.

**Primary references** (both in this skill's directory):
- `references/implementation-nuances.md` — verified migration patterns for each framework, Auth0 feature-to-Descope mappings, and known gotchas
- `references/flows-and-widgets.md` — Descope terminology/lingo, Flow structure and templates, Widgets, SSO Setup Suite, Console-vs-code decision guide

---

## Guiding Principles

**Console-first.** Before recommending SDK code for any user-facing auth feature, check whether the Console, a Flow, or a Widget covers the use case. Engineers integrate once (SDK setup + session validation). All subsequent auth evolution — new methods, MFA changes, UI updates — should happen in the Console without code deployments. See `references/flows-and-widgets.md` → Console vs. Code.

**Ask, don't assume.** At any design decision point — embed Flows vs. OIDC compatibility, Flow vs. custom code, Widget vs. custom page, MFA inline vs. separate enrollment, programmatic SSO vs. SSO Setup Suite — use `AskUserQuestion` rather than proceeding with an assumption. The cost of a wrong assumption compounds across 20+ files. Uncertainty about architecture or intent is always worth a question.

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
   in the conversation (e.g., Express, Next.js, Flask/FastAPI, Go). The user can always
   pick "Other."
2. **Migration goal** — Full cut-over, incremental/phased migration, or just evaluating.
3. **Existing user base** — Are they migrating an app with active users in Auth0, or
   starting fresh? This determines whether user migration planning is needed (password
   hashes, bulk import, phased vs. big-bang cutover, forced re-login on cutover).
4. **Preferred migration style** — Do they want to embed Descope Flows/Widgets directly (full native migration), or preserve their existing OIDC client library and point it at Descope's OIDC endpoints (OIDC compatibility layer)? Note: B2B features (Organizations/SSO/SCIM management) have no OIDC-layer equivalent and require native SDK calls regardless of path.

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

After both calls, summarize findings and flag high-complexity items (CIBA, Token Vault, FGA)
before proceeding to Step 0.5.

---

### Step 0.5: Engineer Review Checkpoint (BLOCKING — requires `AskUserQuestion`)

These questions surface blockers the framework doesn't expose. Ask even the ones you think
you know. Use `AskUserQuestion` before proceeding to codebase analysis.

Batch into calls of up to 4 questions. Skip questions that are clearly inapplicable given
Step 0 answers (e.g., skip user migration planning if they said they're starting fresh).

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

**Console/Flow/Widget opportunities** (flag before codebase analysis, then ask):
- If the app has a custom SSO settings page: ask whether the SSO Setup Suite + Tenant Profile Widget replaces that code.
- If the app has a profile edit page or user management UI: ask whether a Descope Widget covers the use case.
- If the app has a separate MFA enrollment page: ask whether MFA should be integrated into the main sign-in Flow as a step or subflow instead (almost always cleaner in Descope).
- If any server-side code generates emails, initiates SSO, or runs logic during the auth journey: ask whether that logic can be a Flow step or Connector instead of server code.

Summarize any blockers and Console/Flow opportunities before proceeding to codebase analysis.

---

### Step 1: Codebase Analysis

Scan the codebase to map every auth touchpoint before writing the plan.

**Run these searches (adapt file extensions to the user's language):**

```bash
# Find all Auth0 import sites
grep -rn "auth0\|@auth0\|express-openid-connect\|nextjs-auth0\|auth0-fastapi\|go-oidc" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=venv \
  . 2>/dev/null

# Find all Auth0 env var references
grep -rn "AUTH0_\|auth0\." \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --include="*.env*" --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Find claim / token access patterns (things that may need JWT Template)
grep -rn "token\.\|claims\.\|req\.auth\.\|req\.oidc\.\|session()\." \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Find protected route declarations
grep -rn "requiresAuth\|withPageAuthRequired\|withApiAuthRequired\|require_session\|@login_required\|authMiddleware\|isAuthenticated" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=.next \
  . 2>/dev/null

# Check package.json / go.mod / requirements.txt for Auth0 dependencies
find . -maxdepth 3 \( -name "package.json" -o -name "go.mod" -o -name "requirements.txt" \) \
  ! -path "*/node_modules/*" -exec grep -l "auth0" {} \;
```

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
exists. Pair complexity labels with time estimates; skew toward the lower bound — SDK swaps and mechanical rewrites are usually faster than they look, and repetitive files in a group after the first go much faster. Group execution into phases so parallel vs. sequential work is clear.

The plan must include these sections, in this order:

#### Overview

2–3 sentences: what's being replaced, what replaces it, and the recommended approach with a
one-sentence rationale. Add one sentence on what doesn't change — user-facing login behavior,
sessions, and existing accounts are preserved.

Include a **Migration at a Glance** table:

| | |
|---|---|
| **Approach** | Full native migration / OIDC compatibility layer |
| **Files changing** | N source files across N areas |
| **Console setup** | N configuration steps before launch |
| **User impact** | No re-login required / Users will need to log in once after cutover |
| **Estimated engineering effort** | N–N hours |
| **Biggest risk** | One sentence naming the highest-complexity item |

---

#### What's Changing and Why

Prose (not a table) describing what each part of the system does today and what it does
after. Example:

> Today, Auth0 handles everything related to login: it shows the login UI, issues tokens,
> and validates them on every API request. After this migration, Descope takes over all of
> those responsibilities. The login UI becomes a Descope component embedded in the app.
> Token validation moves to the Descope SDK. The five Auth0 environment variables are
> replaced by a single Descope Project ID.
>
> Auth0 features in use that need to carry over: [list in plain English, one clause each].

Tailor to triage findings.

---

#### Auth Touchpoints: What the Code Analysis Found

Open with the scope count (e.g., "11 files across 4 areas"). Group by area, not file path.
Each group gets a sentence on what it does and what changes.

**Session handling (3 files)** — These files read and validate the current user's login
state. They'll be updated to use the Descope session SDK instead of Auth0's.

| File | What it does today | What changes |
|---|---|---|
| `lib/auth.ts:34` | Returns Auth0 session with `isAuthenticated`, `user`, `claims` | Rewritten to return Descope `AuthenticationInfo`; a thin adapter layer preserves the shape callers expect |
| `middleware.ts:12` | Blocks unauthenticated requests app-wide | Updated to call Descope session validation; logic is identical, SDK call changes |

**Login / logout routes (2 files)** — These handle the Auth0 redirect-based login flow.
Descope replaces this with an embedded UI component; no redirect cycle is needed.

| File | What it does today | What changes |
|---|---|---|
| `pages/api/auth/[...auth0].ts` | Catch-all handler for OAuth callback, logout, session refresh | Deleted — Descope handles this client-side; no server route needed |

Cover all functional groupings. End with: "Total: N files. Estimated code-change effort: N–N hours."

---

#### Feature Migration: Auth0 → Descope

For each Auth0 feature confirmed in triage, write a short paragraph: what it's trying to
accomplish, the best Descope approach for that goal, what's different, and what action is
required. The best approach may be a Flow, Widget, SSO Setup Suite, or Console configuration
rather than a direct SDK equivalent — reason about the intent, not just the API surface. Only
recommend SDK code when programmatic control is genuinely required. Example:

> **Multi-tenancy (Auth0 Organizations → Descope Tenants)**
> Auth0 Organizations group users by company and scope their permissions. Descope has the
> same concept, called Tenants, and the migration script transfers them automatically.
> The main difference is how tenant membership appears in the session token — Auth0 uses a
> flat `org_id` string, while Descope uses a nested `tenants` object that includes per-tenant
> roles. Any backend code that reads `req.auth.org_id` will need to be updated to read
> `token.tenants`. This is a predictable, mechanical change.
> **Effort: Medium (1–2 hours).** The migration script handles the data; code changes are
> localized to token-reading logic.

Only include confirmed features.

---

#### Before the Code Can Run: Required Configuration

Some Descope behavior is configured in the console, not in code. List every item that must
be set up before the app works, as checkboxes with a plain description of what it is, why
it's needed, and roughly how long it takes. Group into "Required before any testing" and
"Required before production":

**Required before any testing:**
- [ ] **Create a Descope project** — Takes 2 minutes. Produces a Project ID that replaces
  all Auth0 credentials in the app's environment variables.
- [ ] **Create an authentication flow** — Descope uses a visual "flow" to define the login
  experience (what methods are offered, in what order). The built-in `sign-up-or-in` flow
  works for most apps and requires no customization to start.
- [ ] **Configure a user profile token template** — By default, Descope session tokens don't
  include the user's name, email, or profile photo. This template needs to be configured so
  the app can display user profile information. Without it, any part of the UI that shows the
  user's name or email will show nothing after login. (~10 minutes)

**Required before production:**
- [ ] **Create roles: `admin`, `member`** (or whatever the codebase references) — Descope
  roles must exist in the console before code that assigns them will work.
- [ ] **Configure social login providers** (Google, GitHub, etc.) — OAuth credentials for
  each provider need to be entered in the console. (~15 minutes per provider)
- [ ] (continue for each item found in analysis)

---

#### Environment Variables

Diff table with plain-English notes for each removal and addition:

| Remove | Add | Why |
|---|---|---|
| `AUTH0_CLIENT_ID` | — | Auth0 identifies apps by client ID. Descope uses a Project ID instead — simpler, and shared across all apps in a project. |
| `AUTH0_CLIENT_SECRET` | — | Not needed. Descope's browser-side flow doesn't require a secret. |
| `AUTH0_ISSUER_BASE_URL` | — | The Auth0 tenant URL. Replaced by the Project ID. |
| `AUTH0_AUDIENCE` | — | Used by Auth0 for API access scoping. Can be replicated in Descope via token templates if needed. |
| `SECRET` | — | Used by Auth0's SDK to encrypt server-side sessions. Descope doesn't use server-side sessions. |
| — | `DESCOPE_PROJECT_ID` | The single identifier for the Descope project. Replaces all of the above. |
| — | `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value, exposed to the browser for the login component. |
| — | `DESCOPE_MANAGEMENT_KEY` | Only needed if the app manages users, roles, or tenants server-side. |

Follow with: "Net change: 5 variables removed, 1–3 added. No secrets need to be rotated
on the Auth0 side — those credentials stop being used."

---

#### User Migration (only if existing users need to be migrated)

Prose strategy first, then steps. Start with: "X existing users need to be in Descope before cutover." Describe:

- **The plan**: whether this is big-bang (all users moved before cutover) or phased, and why
- **What users will experience**: will they need to log in again? Will anything look different?
- **The biggest dependency**: if password migration requires an Auth0 support ticket, say so
  plainly and call out that this ticket should be opened immediately — it can take several days

End with a brief checklist of the migration steps at the level a PM can track:
- [ ] Open Auth0 support ticket to request password hash export (if applicable) — **start immediately**
- [ ] Export user list from Auth0 (if > 1,000 users)
- [ ] Do a dry run of the migration script against the Descope dev project
- [ ] Review dry-run output for errors
- [ ] Run live migration against staging, then production

---

#### Risks and Things to Decide

Things that could affect timeline, user experience, or scope. Write each in plain English
with three parts: **what it is**, **what breaks if it's ignored**, and **what to do**.
Format each as a named callout:

> **Risk: User profile data won't appear after login until a token template is configured**
> Descope session tokens don't include name, email, or profile photo by default. Any part of
> the app that displays user information — profile pages, nav bars, greeting text — will show
> blank values after migration until the token template is set up in the Descope console. This
> is a one-time configuration step, not a code change.
> **Action:** Configure the token template in the Descope console before running any tests.
> Estimated time: 10 minutes.

> **Risk: Password migration requires an Auth0 support request**
> If the app supports password-based login, users' hashed passwords must be exported from
> Auth0 and imported into Descope. Auth0 only releases these via a support ticket, which can
> take several days to fulfill.
> **Action:** Open the support ticket now, in parallel with development work. Without it,
> password users will need to reset their passwords after cutover.

Include only applicable risks.

---

#### Execution Plan

Open with one sentence: phases run in sequence; steps within a phase can run in parallel.
Then labeled phases, each with a time estimate:

---

**Phase 1 — Console Setup** (~30–45 minutes, no code required)
Can be done by any team member with Descope console access, in parallel with other work.

- [ ] Create Descope project, copy Project ID
- [ ] Create authentication flow (use the built-in `sign-up-or-in` to start)
- [ ] Configure user profile token template
- [ ] Create roles: (list actual roles found)
- [ ] Configure social login providers: (list actual providers found)

**Phase 2 — Code Changes** (~X–Y hours, 1 engineer)
Work through files in the order listed. Run a compile check after each group.

- [ ] Delete `pages/api/auth/[...auth0].ts` — no replacement needed (5 min)
- [ ] Update environment variables in `.env.example` and CI config (15 min)
- [ ] Rewrite `lib/auth.ts` session helper (30 min)
- [ ] Update `_app.tsx` — swap `UserProvider` for Descope `AuthProvider` (15 min)
- [ ] Update 8 protected route files to use new session check (45 min)
- [ ] Update `lib/logout.ts` — two-step logout (15 min)
- [ ] Compile check and fix any type errors before proceeding

**Phase 3 — User Migration** (~1–2 hours, includes dry run)
Run against dev/staging first. Do not run against production until Phase 4 passes.

- [ ] (steps from user migration section above)

**Phase 4 — Testing** (~30–45 minutes)
- [ ] Compile passes with zero errors
- [ ] Server starts, no crashes on startup
- [ ] Unauthenticated routes redirect to login correctly
- [ ] Login flow completes, user profile data appears (confirms token template is working)
- [ ] Logout invalidates session

**Phase 5 — Production Cutover**
- [ ] (cutover-specific steps based on their strategy — maintenance window, phased rollout, etc.)

---

Total estimated engineering effort: **N–N hours** across N engineers.
Blocking dependencies: (list anything on the critical path — support tickets, console access, etc.)

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

Execute the plan in `MIGRATION-PLAN.md` Section 8 order. Follow the detailed guidance below
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
- Password migration needed: [Yes / No]
- Auth0 features in use: [comma-separated list]
- Multiple environments: [Yes: dev/staging/prod / No]
- Zero-downtime required: [Yes / No]

## Files Inventory
_All files that need to change. Update status after each step._

| File | Change | Status |
|---|---|---|
| `pages/api/auth/[...auth0].ts` | Delete | ⬜ Pending |
| `lib/auth.ts` | Rewrite session helper | ⬜ Pending |
| `middleware.ts` | Update session check | ⬜ Pending |

## Console Setup Checklist
- [ ] Descope project created — Project ID: (fill in when done)
- [ ] JWT template configured
- [ ] Roles created: (list roles)
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
When the Docs MCP is available, use `ask-question-about-descope` to confirm the exact method name, option shape, and return type before writing any SDK call. This is faster and more reliable than reading type declarations. Do not write a method name and add a hedge like "verify the exact name" — just verify it.

When the Docs MCP is unavailable: resolve the package's type declarations (`node_modules/<pkg>/dist/types/` or its `package.json` `types` field) and confirm the exact exported name and signature. For Go, run `go doc`. For Python, check the SDK stubs.

**Prefer local `node_modules/` over GitHub** when reading type declarations. Installed packages reflect the exact version in use. If the Descope package isn't installed yet, install it first, then read local type declarations. Only fall back to GitHub if the package can't be installed in the current environment.

This applies to **every SDK call you write**, not just the first import. Field names on
option objects (`sendMail` vs `sendEmail`), hook return shapes (`useDescope()` returns the
SDK directly, not `{ sdk }`), and subpath exports (`/client` vs root) differ just as often.

**1a. After rewriting any module, grep for remaining imports of the removed package.**
```bash
grep -r "from '@/lib/auth0'\|from '@auth0/" --include="*.ts" --include="*.tsx" .
```
Add remaining hits to the work list.

**2. Derive wrapper types from the actual return type.**
Read the function's declared return type and build the wrapper to match. Auth0's field
names, nesting, and flags differ — don't infer from them.

**3. Check dependency versions before generating framework-specific code.**
For Next.js: `cookies()` and `headers()` from `next/headers` are synchronous in v14 and
async in v15. Read `package.json` (or `go.mod`, `requirements.txt`) first.

**4. When making a helper async, propagate to all callers immediately.**
In TypeScript, `async` on a shared utility silently breaks callers that omit `await`. Grep
for all call sites of the changed function and update them in the same pass. The cascade can
span 10–20 files.

**5. Verify published package versions before writing to `package.json` or running `npm install`.**
Don't reuse Auth0's version number or rely on training data for versions. Before writing any
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
- Your **Project ID** appears in the top-left project selector and under **Project → Settings**. It starts with `P` (e.g. `P2abc123...`).
- For Next.js client-side code, this becomes `NEXT_PUBLIC_DESCOPE_PROJECT_ID`. For all server-side SDKs, it's `DESCOPE_PROJECT_ID`.

### 2. Get a Management Key (if needed)
Required for: user management API, role/permission management, tenant operations, ReBAC
(FGA), Outbound Apps, SCIM configuration. If the app does any server-side user or tenant
management, they need this.
- Console → **Company → Management Keys → Generate Key**
- Store as `DESCOPE_MANAGEMENT_KEY`. Treat like a secret — never expose client-side.

### 3. Choose or create a Flow
A Flow is the auth UI sequence. Reference it by Flow ID in the web component.

- Console → **Authentication → Flows**
- The built-in **"sign-up-or-in"** flow handles email/password, OTP, and social login.
  Use it for most migrations.
- To customise: duplicate "sign-up-or-in", rename it, then edit in the visual builder.
- The Flow ID is in the URL when editing and in the flow list.
- There are 100+ Flow templates in the library — check for an existing template before building a custom flow. See `references/flows-and-widgets.md` → Flows.
- MFA: add an MFA step to the Flow or embed MFA as a subflow. Descope manages MFA enrollment through Flows, not the Management SDK — no equivalent to Auth0 Guardian enrollment tickets. For factor-deletion SDK support by type, see `references/implementation-nuances.md` → MFA section.

### 4. Configure authentication methods
- Console → **Authentication** → select methods (Email OTP, Magic Link, Social, SSO, etc.)
- For social providers (Google, GitHub, etc.): configure OAuth credentials here, then add
  the provider step to your Flow.
- For enterprise SSO (SAML/OIDC): Console → **SSO** → configure per tenant. For correct SSO callback and ACS URLs (social OAuth, SAML ACS, what NOT to use), see `references/implementation-nuances.md` → Social login / SSO section.

### 5. Configure a JWT Template (almost always needed)
Auth0 includes `email`, `name`, and `picture` in tokens by default. Descope does not.
- Console → **Authorization → JWT Templates → New Template**
- Add claims: `{"email": "{{user.email}}", "name": "{{user.name}}", "picture": "{{user.picture}}"}`
- Apply the template to your project. Without this step, any code reading `token.email`
  will get `undefined` after migration.

### 6. Create roles in the Console (if using RBAC)
Descope roles are referenced by **name**, not by ID. They must be created manually in the
Console before the code that assigns them will work.
- Console → **Authorization → RBAC → + Role**
- Create each role the app references (e.g. `admin`, `member`)

### 7. Define custom attributes (if using tenant/user metadata)
Auth0 Organization `metadata` and User `app_metadata` map to Descope `customAttributes`.
Pre-define them in the Console schema before setting them via the SDK.
- Console → **Project → Custom Attributes**

### 8. Env var summary
| Variable | Where to get it | Used by |
|---|---|---|
| `DESCOPE_PROJECT_ID` | Console → Project Settings | All server-side SDKs |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | Same value as above | Next.js `AuthProvider` (client-side) |
| `DESCOPE_MANAGEMENT_KEY` | Console → Company → Management Keys | Management SDK, Outbound Apps API |

### 9. Consider Widgets for management UI

Before migrating custom profile pages, user management pages, or role assignment UI, ask
whether a Descope Widget covers the use case. See `references/flows-and-widgets.md` → Widgets.

**After completing console setup:** Update `MIGRATION-STATE.md` — check off each completed
item in the Console Setup Checklist, record the Project ID in the file, and set Next Action
to the first code change step.

---

## Step 2: Framework-Specific Migration

Read `references/implementation-nuances.md` in two passes before writing any code:

1. **General Insights** (always) — covers architecture, feature mapping, and common gotchas that apply to every migration regardless of framework.
2. **Framework section** (use the file's ToC and `offset` to jump directly) — read only the section matching the user's stack:
   - Express.js → `## Express.js`
   - Flask / Python, FastAPI → `## Flask / Python` (FastAPI notes are in the "No drop-in middleware" subsection under General Insights)
   - Next.js (App Router, standalone) → `## Next.js (standalone)` + `## Next.js (B2B): Migration Bug Catalog`
   - Next.js + separate Express API server → `## Next.js (with separate Express API server)`
   - Go → `## Go + Encore`
   - LangChain / LangGraph / Vercel AI with FGA or Token Vault → `## Agentic AI Stacks`

When a new framework is added to the file, add it to this list.

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
  default — configure a JWT Template first.

### Next.js
- `@auth0/nextjs-auth0` → `@descope/nextjs-sdk` + `@descope/node-sdk`
- `UserProvider` → `AuthProvider` (takes `projectId` prop; must use `NEXT_PUBLIC_` prefix)
- `useUser()` → `useSession()` + `useUser()` (Descope separates session state from user data)
- Remove `pages/api/auth/[...auth0].tsx` catch-all — no server-side OIDC handling
- Add `/login` page with `<Descope>` component rendering `sign-up-or-in` flow; always wire `onSuccess` — the component does not auto-redirect (see `references/implementation-nuances.md` → Next.js section)
- `withPageAuthRequired` → manual `useSession()` check + redirect
- `withApiAuthRequired` → call `session()` at handler top, return 401 manually
- Logout: `sdk.logout()` via `useDescope()` hook (not a link to `/api/auth/logout`)

**Client vs. server session access — common source of errors:**
- `session()` from `@descope/nextjs-sdk/server` — server components, server actions, API routes **only**
- `useSession()` + `useUser()` from `@descope/nextjs-sdk/client` — React **client** components
  - `useSession()` returns `{ isAuthenticated, sessionToken, ... }`
  - `useUser()` returns the user object from the current session
- Using `session()` in a client component compiles but throws at runtime (attempts to read cookies in a browser context). Scan for this pattern before finishing any Next.js migration.

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
There is no `isAuthenticated`, no `claims` field, and no `user` wrapper. Write an adapter function instead:
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

### Path A: OIDC Compatibility (lower risk, incremental)

Descope exposes standard OIDC endpoints. If the app uses an OIDC client library
(`express-openid-connect`, `go-oidc`, `authlib`, `@auth0/nextjs-auth0` v4, etc.), it can
point at Descope's OIDC issuer instead of Auth0's with minimal code changes:

| Endpoint | Auth0 | Descope |
|---|---|---|
| Issuer | `https://YOUR_DOMAIN.auth0.com` | `https://api.descope.com` |
| Authorization | `https://YOUR_DOMAIN.auth0.com/authorize` | `https://api.descope.com/oauth2/v1/authorize` |
| Token | `https://YOUR_DOMAIN.auth0.com/oauth/token` | `https://api.descope.com/oauth2/v1/token` |
| UserInfo | `https://YOUR_DOMAIN.auth0.com/userinfo` | `https://api.descope.com/oauth2/v1/userinfo` |
| JWKS | `https://YOUR_DOMAIN.auth0.com/.well-known/jwks.json` | `https://api.descope.com/__ProjectID__/.well-known/jwks.json` |

**`@auth0/nextjs-auth0` v4 (`Auth0Client`) config for Descope:**

```typescript
new Auth0Client({
  domain: `https://api.descope.com/${DESCOPE_PROJECT_ID}`,
  clientId: DESCOPE_OIDC_CLIENT_ID,       // from Descope Console → Applications → OIDC App
  clientSecret: DESCOPE_OIDC_CLIENT_SECRET,
  logoutStrategy: "oidc",                 // prevents calling Auth0's /v2/logout
  secret: SESSION_ENCRYPTION_SECRET,      // still needed for server-side session encryption
})
```

Auth0-specific params that **do not carry over** to Descope via OIDC:
- `screen_hint: "signup"` — Auth0-specific, ignored by Descope
- `organization: orgId` — Auth0 org-scoped login has no OIDC equivalent in Descope
- `appClient.updateSession()` — no equivalent; session is read-only after login

**Good for:** Teams that want to swap the IdP first, then refactor to Descope-native SDKs
later. Preserves existing OIDC client code.

**Caveats:** Claim shapes differ, token lifetimes may differ, and Auth0 Actions must be
rebuilt in Descope Flows regardless of path.

> **For B2B apps using Auth0 Organizations:** Path A preserves roughly 20% of the work
> (middleware, `getSession()`, session routes); the remaining 80% (management SDK, org-scoped
> login, signup flow, claim mapping) requires full migration regardless. **Path A savings are
> minimal for B2B workloads** — account for this when estimating effort.

### Go
- Remove `go-oidc` + `golang.org/x/oauth2`; add `descope/go-sdk`
- Remove login/callback/logout backend endpoints (~150 lines) — only keep token validation
- Session validation: `descopeClient.Auth.ValidateSessionWithToken(ctx, token)` returns
  `(bool, *descope.Token, error)`. `Token.Claims` is `map[string]interface{}`
- `sub` claim maps directly to your auth handler's user ID
- Auth config: ClientID + ClientSecret + Domain + RedirectURL → ProjectID only

**After completing framework code changes:** Update `MIGRATION-STATE.md` — mark each
modified file as Done in the Files Inventory, update Current Phase and Next Action, and
log any non-obvious decisions made (adapter types kept, async cascade scope, etc.).

---

## Step 2.5: Non-Code File Updates

Scan for Auth0 references in non-code files after updating source files.

### `.env.example` / `.env.template` / `.env.sample`
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
Run `grep -r "AUTH0"` to find all env var references — `.env.example`, Docker, CI, shell scripts.

### README / docs
Search all `.md` files for Auth0 references. At minimum, update:
- **Setup section** — replace "create an Auth0 app" instructions with Descope Console setup steps
- **Environment variables section** — reflect the reduced env var set
- **Run instructions** — replace Auth0 tenant steps with Descope Console steps
- **Auth flow diagrams or descriptions** — update to reflect Descope's cookie-based approach

### Docker / CI files
Check `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, and any CI config for
`AUTH0_*` env var declarations. Update them to `DESCOPE_*`.

### Setup / bootstrap scripts

Auth0 CLI commands (`auth0 tenants patch`, `auth0 actions create/deploy`, `auth0 roles create`, etc.) have **no Descope CLI equivalent**. When the migration includes a setup or seed script (e.g., `scripts/bootstrap.mjs`, `scripts/seed.ts`), split it into two parts:

1. **Console setup** (cannot be scripted): Flows, email templates, MFA configuration, branding/Styles — configure these in the Descope Console. Represent them as a Phase 1 checklist in `MIGRATION-PLAN.md`.
2. **SDK automation** (can be scripted): role creation (`management.role.create()`), tenant creation, access key provisioning. Preserve these as a Node.js/Python script using the Descope Management SDK.

Auth0 Actions deployed by the script need to be re-evaluated: each Action's logic maps to a Flow step, Scriptlet, or Connector in the Console — not a code deployment. Use `AskUserQuestion` if the intent of any Action is ambiguous.

**After completing non-code file updates:** Update `MIGRATION-STATE.md` — mark env files,
README, and CI config done in the Files Inventory, and advance Next Action.

---

## Step 3: Feature Migration Mapping

### Auth0 Actions / Rules → Descope Flows + JWT Templates

| Auth0 pattern | Descope equivalent |
|---|---|
| Custom claims in tokens | [JWT Templates](https://docs.descope.com/management/jwt-templates) |
| Custom logic during auth | [Descope Flows](https://docs.descope.com/flows) |
| Post-login webhooks | Flows → [Connectors](https://docs.descope.com/customize/connectors) |
| Role assignment at login | Flow actions → RBAC role assignment steps |

### Social Login → Descope Social Auth
- Configure providers in the Descope Console under Authentication → Social
- Add them to a Flow (no code changes)
- The Descope web component renders configured providers automatically

### MFA Enrollment → Descope Flows

**Before migrating MFA enrollment:** Many Auth0 apps have a separate MFA enrollment page because Auth0 Guardian works via a server-generated enrollment ticket URL. That pattern has no Descope equivalent — and a separate page is rarely the right approach in Descope.

The Descope approach: add an MFA step directly to the sign-up/sign-in Flow — enrollment happens inline during the auth journey. Or embed MFA as a **subflow** (triggered by a condition: user is admin, risk score exceeds a threshold, etc.). Or use the `step-up` Flow template to gate sensitive operations.

**Action:** Before writing any MFA enrollment code, use `AskUserQuestion` to confirm whether MFA can be integrated into the main sign-in Flow. See `references/flows-and-widgets.md` → MFA enrollment section.

### RBAC: Auth0 Roles/Permissions → Descope RBAC

| Auth0 | Descope |
|---|---|
| `req.auth.permissions.includes('read:messages')` | `token.permissions.includes('read:messages')` |
| Role claim via namespace in Actions | `roles` array in JWT (built-in) |
| M2M token for Management API | `DESCOPE_MANAGEMENT_KEY` for management SDK |

SDK: `descopeClient.management.role.create(name, description, permissionNames, tenantId)`

### Multi-Tenancy: Auth0 Organizations → Descope Tenants
- Auth0 `org_id` (flat string) → Descope `tenants` (nested object: `{ tenantId: { roles, permissions } }`)
- Auth0 org-scoped login → Descope routes by email domain or tenant-specific URLs
- Users are project-level in Descope; associated with tenants, not created per-tenant

### Enterprise SSO → Descope Tenant SSO

**Preferred approach — SSO Setup Suite:** Before migrating management SDK SSO calls, ask whether the SSO Setup Suite removes the need for that code. The SSO Setup Suite is a no-code Console wizard that guides tenant admins through per-tenant SAML/OIDC configuration with step-by-step IdP-specific instructions (Okta, Azure AD, Google Workspace, etc.) — no engineering involvement needed for new tenant SSO onboarding.

Use `AskUserQuestion` to ask: does this app need **programmatic** SSO configuration (CI/CD provisioning, API-driven tenant onboarding), or do tenant admins configure SSO themselves through a settings page? If the latter, the SSO Setup Suite + Tenant Profile Widget may eliminate the need for `sso.configureSAMLByTenant()` / `configureOIDCByTenant()` calls entirely.

See `references/flows-and-widgets.md` → SSO Setup Suite.

**SDK path (when programmatic SSO is needed):**

| Auth0 | Descope |
|---|---|
| `connections.create({ strategy: "samlp" })` | `management.sso.configureSAMLByTenant(tenantId, settings)` |
| `connections.create({ strategy: "oidc" })` | `management.sso.configureOIDCByTenant(tenantId, settings)` |
| Per-org SAML connection | Per-tenant SSO (Console → SSO or Management SDK) |

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
- OpenFGA: `{ user, relation, object }` tuples
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

Descope has **no CIBA equivalent**. Recommended approach:
1. Agent creates a pending approval record in your database
2. Frontend polls for it (or uses WebSocket)
3. User approves via Descope Flow or custom UI
4. Agent receives approval signal and continues

This is the highest-complexity migration item.

### M2M / Client Credentials → Descope Access Keys
Auth0 M2M apps use the client credentials grant. Descope's equivalent is
[Access Keys](https://docs.descope.com/management/m2m-access-keys) — create one in
Console → Access Keys, exchange it for a JWT via `descopeClient.auth.exchangeAccessKey()`,
and validate the resulting token the same way as user tokens.

### User Migration → Descope Migration Script

Descope provides a Python CLI tool — [`descope/descope-migration`](https://github.com/descope/descope-migration) — that handles bulk import of users, roles, permissions, and Auth0 organizations (→ Descope tenants) in one run.

**Two import modes:**
- **Auth0 API** — use when fewer than 1,000 users
- **JSON export** — use when 1,000+ users; export via Auth0's User Import/Export extension

**Setup:**
```bash
git clone git@github.com:descope/descope-migration.git
cd descope-migration
python3 -m venv venv && source venv/bin/activate
pip3 install -r requirements.txt
cp .env.example .env
```

Required `.env` variables:
| Variable | Where to get it |
|---|---|
| `AUTH0_TOKEN` | Auth0 Management API → token explorer (24h token) |
| `AUTH0_TENANT_ID` | Your Auth0 dashboard URL |
| `DESCOPE_PROJECT_ID` | Descope Console → Project Settings |
| `DESCOPE_MANAGEMENT_KEY` | Descope Console → Company → Management Keys |

**Always dry-run first:**
```bash
python3 src/main.py auth0 --dry-run
python3 src/main.py auth0 --dry-run --from-json ./export.json --with-passwords ./password_hashes.json
```

**What gets migrated:** users, roles, permissions, Auth0 organizations → Descope tenants.

**Auto-created custom attributes:**
- `connection` (text) — the Auth0 connection type for each user
- `freshlyMigrated` (boolean) — set to `true` on import; use this in Flow conditionals to give newly migrated users a special first-login experience, then flip it to `false` once done

**Session migration (beta):** for zero-disruption cutovers, active Auth0 sessions can be
exchanged for Descope tokens without re-authenticating. Requires users to already exist in
Descope (import first). See [session migration docs](https://docs.descope.com/migrate/session-migration).

**Large user bases (10,000+) — just-in-time migration via Auth0 Action:**
For large populations where a bulk export/import would be disruptive, Auth0 supports creating an Action that forwards user data to Descope on each login during a cutover window — users migrate gradually, just-in-time, without a forced re-login. This approach requires coordination with the Descope Customer Success team. Flag this if the user wants zero-disruption cutover.

### Email Templates → Descope Messaging Templates
Auth0 email templates map to Descope [Messaging Templates](https://docs.descope.com/management/messaging-templates),
configured per authentication method in the Console.

### Log Streams → Descope Audit Webhook
Auth0 Log Streams map to Descope's
[Audit Webhook Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook).
Set this up before cutover to avoid gaps in event logging.

### Custom Domains
CNAME `auth.example.com` → `cname.descope.com`, verify in Console, then pass `baseUrl` to
the Descope SDK.

### Attack Protection → Descope Flow Security
Auth0 Attack Protection maps to Descope Flow steps using security connectors: Arkose Bot Manager,
Google reCAPTCHA, Fingerprint, Have I Been Pwned, AbuseIPDB. These are composable (add
detection steps to Flows) rather than toggle-based — not configured by default.

**After completing feature migration:** Update `MIGRATION-STATE.md` — record which features
were migrated, mark any that were deferred or require follow-up, and advance Next Action to
testing.

---

## Step 4: Critical Gotchas (Always Cover These)

### JWT Claims Are Not the Same
Descope session JWTs contain `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions`, and `dct` by
default. They do **not** contain `email`, `name`, or `picture`. Auth0 ID tokens include
these by default.

`dct` (Descope Current Tenant) is a flat string holding the active tenant ID — the direct equivalent of Auth0's `org_id`. For apps where a user is always in a single tenant context, `token.dct` is simpler to read than iterating `token.tenants`. Use `token.tenants` when you need per-tenant roles or permissions (it is a keyed object: `{ [tenantId]: { roles, permissions } }`); use `token.dct` when you only need the tenant ID.

**Action required:** Configure a JWT Template in the Descope Console to add `email`,
`name`, and any other profile fields the app reads from the token.

### Audience Validation Is Opt-In
Descope session tokens have no `aud` claim by default. Apps using `AUTH0_AUDIENCE` for
API access control must:
1. Configure a custom `aud` claim in JWT Templates
2. Pass `audience` to `validateSession()` on the backend

### Logout Is Two Steps
1. Call `descopeClient.logout(refreshToken)` to invalidate server-side
2. Clear `DS` and `DSR` cookies

Skipping either step leaves a broken state.

### Server-Side Profile Updates Don't Immediately Reflect in the Session Token

Auth0's `appClient.updateSession()` has no direct server-side equivalent in Descope. Profile changes via the Management SDK don't update the JWT already in the browser. Four options:

1. **Wait for auto-refresh** (~5 min default) — no code required; tolerable for most apps.
2. **`useDescope().refresh()` client-side** — triggers an immediate token refresh. Requires the profile form to be a client component with a `useDescope()` hook. Full code pattern in `references/implementation-nuances.md` → Session refresh section.
3. **Update JWT endpoint** (`POST /v1/mgmt/user/jwt/update`) — server-side; updates stored JWT custom claims for a specific user. Verify current behavior against Descope docs before using — this updates stored claims, not the live session token.
4. **User Profile Widget** — if the app is building a profile edit page, the Widget handles profile updates and session refresh automatically without custom code. See `references/flows-and-widgets.md` → Widgets.

**Session change event listeners:** Instead of calling `refresh()` imperatively, the Descope client SDK exposes auth state change events — use these to react to session updates across components. See [docs.descope.com/client-sdk/auth-helpers#handling-authentication-state-changes](https://docs.descope.com/client-sdk/auth-helpers#handling-authentication-state-changes).

### Cookie Names Are Configurable (And May Conflict)
Default: `DS` (session JWT), `DSR` (refresh JWT). Configure custom names in the Descope
Console under the Flow's End action when running multiple Descope projects on the same
root domain.

### One Token, Not Two
Auth0 issues separate ID tokens and access tokens. Descope has one token: the session JWT
(`DS` cookie). Forward it as `Authorization: Bearer <DS>` to API servers.

### No Drop-In Middleware
Descope has no `express-openid-connect` equivalent package. The middleware is ~20 lines
of custom code.

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

### Env Var Reduction
Auth0: `CLIENT_ID`, `CLIENT_SECRET`, `ISSUER_BASE_URL`, `SECRET`, `AUTH0_AUDIENCE` (5+).
Descope: `DESCOPE_PROJECT_ID` only (+ `DESCOPE_MANAGEMENT_KEY` for management ops).

---

## Step 5: Automated Testing

Run the app and verify it works — don't just hand over a checklist.

### Phase 0: Final stale-import sweep (BLOCKING)

```bash
grep -r "@auth0\|auth0\|express-openid-connect\|nextjs-auth0" \
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
- `Cannot find module '@auth0/...'` → stale import; re-run Phase 0
- `Property 'X' does not exist on type 'AuthenticationInfo'` → wrapper built against Auth0 shape; re-derive
- `'await' expression is not allowed in synchronous contexts` → async cascade gap
- `Object is possibly 'undefined'` on session fields → add null check or early return

```bash
npm run dev   # or: python main.py / go run . / flask run / etc.
```

### Phase 2: Run existing tests

```bash
npm test   # or: pytest / go test ./... / etc.
```

Auth-related test failures usually mean: a mock or fixture still uses Auth0 shapes, or a
test validates JWT claims that are now missing (e.g., `email` without a JWT Template).

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

Check that `email`, `name`, and any other expected claims are present.

### Phase 5: Report results

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

**Do not proceed to Step 6 until ALL of the following are true:**
- [ ] Phase 0 grep returns zero Auth0 references
- [ ] Phase 1 compilation passes with zero errors
- [ ] Phase 1 server starts and stays running
- [ ] Phase 3 root path returns 2xx or 3xx (not 5xx)
- [ ] Phase 3 protected routes return 302 or 401 (not 500)

---

## Step 6: Post-Migration Summary (Required)

Every migration produces a `MIGRATION-SUMMARY.md` covering what was done, manual setup
remaining, and behavioral differences that matter before production.

### MIGRATION-SUMMARY.md

1. **What was migrated** — a table mapping each Auth0 concept to its Descope replacement

2. **Behavioral differences and open questions** — numbered list of significant differences
   between the Auth0 and Descope implementations. For each item: Auth0 behavior, Descope
   behavior, action required.

3. **Pre-deploy checklist** — actionable checkbox items for everything that must happen
   before the migrated app can run. Prominently include all Console setup tasks — these
   are the things easiest to forget because the code compiles without them.

---

## Step 7: Output Format

Write a numbered migration guide in Markdown, scoped to the user's stack. Use code
snippets and direct doc links. Always include the MIGRATION-SUMMARY.md deliverable (Step 6).

For complex migrations (FGA, CIBA, AI tooling), flag the high-effort items explicitly
with estimated complexity (Low/Medium/High) so the user can plan.

---

## Reference Files

- `references/implementation-nuances.md` — Verified migration patterns, code-level diffs, and edge
  cases for several frameworks.
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
