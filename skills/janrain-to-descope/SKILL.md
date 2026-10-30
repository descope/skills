---
name: janrain-to-descope
description: >
  Use this skill whenever anyone asks about migrating from Janrain or
  Akamai Identity Cloud to Descope. Triggers on: "migrate from Janrain",
  "moving off Akamai Identity Cloud", "Janrain to Descope", "replace
  Janrain with Descope", "our app uses Hosted Login and we want to switch
  to Descope", or any question about Janrain features (Hosted Login,
  social login, two-factor authentication, custom providers) in the
  context of Descope. Always use this skill before giving migration
  guidance, do not rely on memory alone, since Janrain is an old, poorly
  documented, soon-to-be-shut-down platform and guessing is risky.
---

# Janrain (Akamai Identity Cloud) to Descope Migration Skill

Janrain was acquired by Akamai in 2019 and is officially called Akamai Identity Cloud, though most customers still call it Janrain. Akamai has announced Identity Cloud reaches end of life on December 31, 2027, and stopped adding new features at the end of 2024. This urgency matters, migrations should generally favor moving all users up front rather than waiting for them to log in gradually over time.

This skill guides self-service migrations from Janrain to Descope. It runs in four parts:

1. **Scope Check**, confirm this is actually Janrain, and which of its two products the customer is on.
2. **MCP Check**, confirm whether the Descope Docs MCP is available and suggest installing it if not.
3. **Migration Plan**, gather context via questions, look at the codebase, and produce a plain-language `MIGRATION-PLAN.md` for the user to review.
4. **Execution**, if the user confirms they want to proceed, execute the plan.

Do not skip ahead. The plan must be reviewed before any code changes begin.

**Primary references** (in this skill's directory):
- `references/implementation-nuances.md`, how Janrain actually works, its schema, passwords, multi-tenancy, MFA, and known gaps in what's documented. Read this before writing anything Janrain-specific.
- `references/flows-and-widgets.md`, terminology mapping and when to use the Descope Console instead of writing code.

This skill focuses on how Janrain works and how it differs from Descope, not on Descope's own API structure. For current Descope API shapes and method names, rely on the Descope Docs MCP or Descope's documentation, not on this skill.

## Guiding Principles

**Console-first.** Before recommending SDK code for any user-facing auth feature, check whether the Descope Console, a Flow, or a Widget already covers it.

**Ask, don't assume.** Janrain's setup varies a lot between customers, more than most providers, since its schema can be customized, and Akamai's own documentation leaves several real questions unanswered. Each section of `references/implementation-nuances.md` flags its own open questions inline, whenever one of those comes up, ask the customer directly rather than assuming the documented default applies to them.

**No single official Janrain SDK covers every situation.** Janrain's current login product, Hosted Login, has no official client library, integration there means pointing a standard, off-the-shelf sign-in library at Janrain's endpoints. However, an older product, the JavaScript SDK (also called Capture), is a real, still-supported official library some customers are still on. Which one applies changes the shape of the migration, see the Scope Check below.

## Part 1: Scope Check

Akamai has other, unrelated products (for example Akamai MFA, or Akamai's network security products). Confirm the customer means Akamai Identity Cloud, formerly Janrain, a customer login and identity platform, before proceeding. If they mean something else, stop and clarify.

**Then confirm which Janrain product they're actually using, since the rest of this skill assumes Hosted Login.** Janrain has two very different login products:

- **Hosted Login**, the current, standard product. Everything in `references/implementation-nuances.md` is written for this.
- **The JavaScript SDK, also called Capture**, an older product, still supported for existing customers but not offered to new ones. It works completely differently, embedded widgets and client-side session handling instead of a hosted login redirect.

Ask the customer directly which one they're on if it isn't obvious from their code (a JavaScript SDK integration will have files like `janrain-init.js` and calls like `janrain.capture.ui.renderScreen`). If they're on the JavaScript SDK, say so plainly: this skill's guidance is written for Hosted Login, and a JavaScript SDK migration follows a different pattern (see `references/implementation-nuances.md`).

**If neither description fits** (for example, a heavily customized older integration built directly against Janrain's raw data API with no standard login UI at all), say so plainly: this skill's guidance assumes one of the two standard products, and a fully custom integration needs its own direct assessment before this plan applies. Don't force it into one of the two categories just to proceed.

**On the March 2026 date below and elsewhere in this skill:** the same caution that applies to every other Janrain-side claim in this skill applies here too, this comes from Akamai's own documentation, not independent confirmation, and should be treated with the same "verify before relying on it" standard as everything else, not as settled fact.

**If they're on the JavaScript SDK and use social login, mention this, but don't overstate the urgency.** The dashboard used to manage that SDK's social login settings (called Engage) is documented as having stopped working March 31, 2026, but apps still actively in use are documented as continuing to work normally until the general shutdown at the end of 2027. Per Akamai's own documentation, customers with an Akamai contract can still request changes after that date by submitting a support ticket; customers without a contract can no longer make changes to their social apps at all. So the real login functionality is not on a separate, earlier deadline as far as current documentation shows, but the customer may have already lost the ability to reconfigure their social login setup since that date, worth confirming directly with them if this affects their plans.

## Part 2: MCP Check (BLOCKING)

Before doing anything else, check whether the Descope Docs MCP is available.

**If available:** proceed to Part 3.

**If not available**, show this message and ask whether they want to install it first:

> **Descope Docs MCP is not installed.**
>
> This skill uses it to look up current Descope API details while migrating. Without it, some answers may be based on older information.
>
> You can install it at https://docs.descope.com/mcp/mcp-server. Would you like to install it before we continue, or proceed without it?

If they proceed without it, flag any Descope-specific answers as worth double-checking against current documentation.

## Part 3: Migration Plan

### Step 1: Triage questions

Ask these together. Do not guess the answers from memory, Janrain setups vary too much customer to customer:

1. What language or framework does the app use?
2. Do you have a real sample of your Janrain user data (even a few records), or should we plan around Janrain's documented default fields?
3. Do your users log in with a password, a social login (like Google), an outside company login system (like SAML), or a mix?
4. Do you have two-factor authentication turned on? If so, do you know if you're on the older or newer version of Janrain's Hosted Login? This matters directly: two-factor authentication only works on the newer version at all, if they're on the older version, MFA isn't possible today regardless of what they've configured, and this changes what the plan needs to cover (see the MFA section of `references/implementation-nuances.md`).
5. Do all of your users share one Janrain account, or do you keep different groups of users (different brands, and so on) separate today?
6. Are your users all in one region, or spread across regions (for example, US, Europe, Asia)? Janrain treats each region as its own separate environment, so this affects how many times the export step needs to be run, not just how tenants might be structured.

Follow up based on the answers, for example if they mentioned an outside company login system, flag this clearly: whether that data can be migrated the same way as social logins is genuinely unclear from Janrain's own documentation, and needs to be checked directly against their account (see `references/implementation-nuances.md`).

### Step 1.5: Engineer Review Checkpoint

These questions surface blockers the triage answers don't expose. Ask even the ones you think you already know the answer to.

**Access and credentials**
- Do they have access to the Descope Console and a Project ID? If not, this needs to happen before anything else.
- Do they have an API client in Janrain's Console with `direct_read_access`, so an export can actually be run? If not, this needs to be created first (see the export steps in `references/implementation-nuances.md`).
- Do they have a Descope Management Key? Needed for user import and any custom attribute setup.

**Codebase scope**
- Are there places in the app that read a user's email, name, or picture directly from a token or session object? These will break silently after migration unless a Descope JWT Template is configured, since none of this is included by default.
- Does the app have its own session-management code already (cookies, server-side session store)? If it's on the JavaScript SDK, it almost certainly does, since Janrain gives that product no session mechanism at all.
- Are there multiple services validating a Janrain token or session independently? Each one needs to be updated separately.

**Deployment and risk**
- Do they have separate dev, staging, and production environments? Each needs its own Descope project.
- Is there a maintenance window available, or does this need to happen with no downtime?

**Gaps to flag proactively, don't wait to be asked:**
- If they mentioned enterprise SSO in Step 1: flag now that whether this data shares the same schema as social logins is unconfirmed, this affects the whole export plan for those users.
- If they're on the JavaScript SDK with social login: flag that they may have already lost the ability to reconfigure that setup since March 2026, even though it's still functioning.
- If they mentioned GDPR consent or a Salesforce Marketing Cloud sync: flag the specific gaps in `references/implementation-nuances.md` now, before codebase analysis, since these can change the shape of the plan.

Summarize any blockers found before moving to codebase analysis.

### Step 2: Look at the codebase

Run searches to find every place the app touches Janrain, adapting file extensions to the app's language.

**If the customer is on Hosted Login:**
```bash
# Find OIDC client configuration and calls to Janrain's endpoints
grep -rn "janrain\|janraincapture\|oauth2/v1\|oidc" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=venv \
  . 2>/dev/null

# Find where the app reads user claims from a token (these break silently
# without a JWT Template, since none of this is included by default)
grep -rn "\.email\|\.given_name\|\.family_name\|\.picture\|claims\." \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=venv \
  . 2>/dev/null

# Find protected route declarations
grep -rn "requireAuth\|isAuthenticated\|login_required\|authMiddleware" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=venv \
  . 2>/dev/null
```

**If the customer is on the JavaScript SDK instead:**
```bash
# Find the embedded widget files and their init config
find . -maxdepth 4 -iname "janrain-init.js" -o -iname "janrain-utils.js"

# Find widget calls and event handlers
grep -rn "janrain\.capture\.ui\.\|onCaptureSessionCreated\|onCaptureLoginSuccess\|onCaptureRegistrationSuccess\|janrainCaptureToken" \
  --include="*.html" --include="*.js" --include="*.php" \
  --exclude-dir=node_modules \
  . 2>/dev/null
```

For each hit, note the file, what it does, and whether it's a small (drop-in replacement), medium (needs rewriting), or large (no direct equivalent, needs a custom approach) change.

### Step 3: Write MIGRATION-PLAN.md

Write a plain-language plan covering:

- **Overview**, what's changing, and a short note that user-facing login and existing accounts are preserved.
- **What's changing and why**, in plain sentences, not jargon.
- **What the code review found**, every place in the app tied to Janrain.
- **Required Descope Console setup**, before any code runs, including turning on password sign-in if importing passwords, and creating any custom fields needed to hold data like a customer's original Janrain user ID.
- **How users will be moved over**, and whether it depends on anything unconfirmed (like whether their specific account's passwords can actually be read out, see the passwords section of `references/implementation-nuances.md`). If the customer has users in more than one region, note that each region needs its own separate export and import run.
- **Open questions specific to this customer**, anything from Step 1 that touched an item flagged as unconfirmed in `references/implementation-nuances.md`. Be explicit that these need to be checked against the customer's real account, not assumed.
- **Execution plan**, an ordered list of steps.

Stop here and ask the user to review the plan before proceeding.

## Part 4: Execution

### Keep track of progress

Create a `MIGRATION-STATE.md` file, and update it after each step: what's done, what's left, and any decisions made along the way. This way, if the conversation restarts partway through, whoever picks it up again knows exactly where things stand.

### Before writing any code, confirm

- Password sign-in is turned on in the Descope Console, if importing passwords. Without this, importing users with a password will fail outright.
- Any custom field needed to preserve data (like a customer's original Janrain user ID) has already been created in the Descope Console. If it hasn't been created first, that data will be silently dropped during import, with no error shown.
- Whether the customer's passwords and role assignments can actually be read out of their Janrain account has been checked, not assumed. See the passwords and roles sections of `references/implementation-nuances.md`.

### Moving users over

Since Janrain does not slow down as the number of users grows, there's no need to split this into a special process for very large customer bases the way some other providers require. Follow the export approach in `references/implementation-nuances.md`, "Exporting users in bulk."

Given Janrain's shutdown timeline, prefer moving all users over at once rather than waiting for each one to log in gradually. A gradual approach depends on every user logging in again before the shutdown date, which is a real risk this close to end of life.

### Framework-specific setup

See "Framework notes" in `references/implementation-nuances.md`. If the customer is on Hosted Login, this usually means removing whatever generic sign-in library the app was using and pointing it at Descope instead, plus building the app's own session handling if it doesn't already have it (Janrain never provided this). If the customer is on the JavaScript SDK, this instead means removing the embedded widget code and its client-side token handling, replacing it with a Descope Flow, see the JavaScript SDK section of `references/implementation-nuances.md` for what that involves.

For replacing the login screen itself, and terminology mapping, see `references/flows-and-widgets.md`.

### Check for other connected systems

Ask whether anything else depends on Janrain sending it real-time updates (marketing tools, CRMs, analytics). These break silently at cutover, separate from the user migration itself. Descope has a webhook equivalent, though it's not quite instant the way Janrain's is. If the customer syncs to Salesforce Marketing Cloud specifically, there is currently no ready-made Descope equivalent for that, this needs a custom solution, don't imply it's already covered.

### Critical things to get right

- **Passwords may or may not actually be exportable for this specific customer.** Confirm this before promising it. If they can't be exported, use a password reset flow, not a gradual sign-in based migration, since Janrain is shutting down soon.
- **Turn on password sign-in in the Descope Console first**, or importing passwords will fail.
- **Create any custom fields in the Console before importing**, or that data is silently lost.
- **If the customer uses an outside company login system (SAML or similar), check directly whether that data is stored the same way as social logins.** This is genuinely unclear from Janrain's documentation.
- **If the customer has two-factor authentication on, there's no simple "enrolled" flag to migrate.** Only the underlying phone number and email fields carry over, enrollment itself is decided fresh at each login.
- **Watch for duplicate accounts.** If a Janrain user signed up with a password and later also used a social login with the same email, Janrain treats those as one account. If this isn't handled, the migration could create two separate Descope accounts for the same person.
- **There's no single way to cancel every old Janrain login session at once.** If the customer wants to make sure old sessions stop working right after cutover, this has to be done one user at a time, and should be raised with them as a decision, not assumed away.
- **If the customer tracks GDPR-style consent (marketing opt-ins, terms of service acceptance), be careful with this data specifically.** There's no confirmed way to export a full consent history in bulk, only a current snapshot, and legal terms acceptance has no confirmed timestamp, only whether a version was accepted, not when. Whether to carry old consent forward or ask users to reconfirm it is a legal decision for the customer to make, not something to decide for them, see `references/implementation-nuances.md`.
- **If the customer syncs data to Salesforce Marketing Cloud, ask whether deletion syncing is turned on.** It's an optional setting, off by default. If it isn't on, past deletion requests in Janrain may not have actually removed that person's data from Salesforce.
- **Don't assume a full Janrain export batch fits into one Descope import call.** These are two separate limits, don't conflate them: for a batch where every user has a hashed password (the normal case), no exact limit is documented, so start with a smaller batch, around 100 to 250 users, and only scale up once testing confirms it works reliably. Separately, and unconditionally, any batch that includes even one user with a plaintext temporary password instead of a hash is hard-capped at 100 users total, regardless of the rest of the batch. Keep those users in their own dedicated batch rather than mixing them in, since one plaintext-password user pulls the whole batch down to that lower cap.

### Testing

Don't just hand over a checklist, actually verify.

**Phase 1: Stale reference sweep (do this first)**
```bash
grep -rn "janrain\|janraincapture\|janrain-init" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.go" \
  --exclude-dir=node_modules --exclude-dir=venv \
  .
```
If this returns anything, fix it before moving on.

**Phase 2: Compile and start**
Run the app's normal build/start commands and confirm no errors.

**Phase 3: Smoke test the sign-in flow**
- Confirm a migrated user can sign in with their existing password, if passwords were imported.
- Confirm their name, email, and any custom fields display correctly, this fails silently if a JWT Template wasn't configured, so check this specifically rather than assuming it works.
- Confirm signing out actually ends the session.

**Phase 4: Watch for these specific, known-misleading errors**
- "Incorrect username or password" showing up for every single user, even ones with correct passwords, is not a real credentials problem, it means the sign-in setup and the underlying data it's pointed at don't match up.
- A generic "forbidden" error on a setup or configuration call usually means an expired admin access token, not a permissions problem.
- A redirect that silently fails to come back to the app is almost always an exact-match mismatch between the configured redirect address and the one actually used.

Since very little of this has been tested against a real Janrain account before this skill was written, treat this phase as more important than usual, don't skip straight to "looks fine."

### Wrap-up

Summarize what was done, and clearly call out anything that still needs to be double-checked against the customer's real Janrain account rather than assumed from documentation. The Critical Gotchas list above and the open questions noted throughout `references/implementation-nuances.md` are the checklist for this.

## Reference Files

- `references/implementation-nuances.md`
- `references/flows-and-widgets.md`
