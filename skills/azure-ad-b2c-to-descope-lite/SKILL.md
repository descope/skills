---
name: azure-ad-b2c-to-descope-lite
description: >
  Non-interactive Azure AD B2C → Descope migration for agents running without a person to answer
  questions (background or autonomous runs). Follows Descope's general migration strategy, makes
  each design decision itself from the codebase, and records the decision and its reasoning in
  MIGRATION-PLAN.md instead of asking. Use when asked for a non-interactive, unattended, or "lite"
  migration from Azure AD B2C to Descope. For a guided migration that asks the user at each
  decision, use azure-ad-b2c-to-descope instead.
---

# Azure AD B2C → Descope Migration (Non-Interactive)

This skill runs a B2C migration start to finish without asking the user questions. Where the
guided `azure-ad-b2c-to-descope` skill asks, this one applies the defaults below, records each
choice in `MIGRATION-PLAN.md`, and leaves open questions for a person in `MIGRATION-SUMMARY.md`.

Steps, in order: **1. MCP check → 2. Scope check → 3. Discovery → 4. Decisions →
5. `MIGRATION-PLAN.md` → 6. Code changes → 7. Checks → 8. `MIGRATION-SUMMARY.md`**.

Depth on any topic: [docs.descope.com/migrate/azure-ad-b2c](https://docs.descope.com/migrate/azure-ad-b2c),
and the guided skill's `references/` when it is installed.

---

## Strategy

Follow Descope's migration strategy ([docs.descope.com/migrate/strategy](https://docs.descope.com/migrate/strategy)):

- **Match first, then enhance.** Rebuild what B2C does today: same sign-in methods, screens,
  tenants and roles. Passkeys, adaptive MFA or a redesigned login go in the summary as after-cutover
  ideas, not into the migration.
- **Console-first.** The sign-in journey (screens, MFA, password reset) moves into Descope Flows
  configured in the Console. The code only changes in two places: the frontend points its sign-in
  library at Descope or renders an embedded Descope Flow, and the backend verifies Descope tokens
  instead of B2C tokens.
- **One app at a time, tests first.** Move apps one at a time, each with sign-in tests.

---

## Hard stops (apply even without a person)

- **Never write to the B2C tenant.** Read code and any policy XML in the repo. Anything the
  migration needs in the tenant (an ROPC policy, an app registration for Descope) is a customer
  task in the plan, with an owner.
- **Never import users.** Write the B2C export and Descope import scripts, but don't run them. The
  team runs them: dev first, then staging after dev sign-in tests pass, then production.
- **Never put `DESCOPE_MANAGEMENT_KEY` or an Inbound App client secret in client-side code**, and
  never print or commit their values.
- **Change a Descope project only when the request names it as non-production.** Make Console
  changes through the Descope MCP Server only for a project ID given in the user's request and
  described there as dev or otherwise not production (Step 6). Otherwise, use the MCP for docs and
  reads only, and list Console setup as steps in the plan.
- **Stop if the app doesn't use Azure AD B2C** (step 2).

---

## Key differences: Azure AD B2C vs. Descope

These hold for every B2C migration. Don't plan around them.

- **No password hash export.** B2C doesn't export hashes; password users reset, go passwordless,
  or move just in time (JIT).
- **No secret or key export.** B2C client secrets, IdP secrets and policy keys can't be read back.
  Plan new credentials (social provider client IDs, OIDC client secrets, SAML certificates).
- **No passkey or TOTP migration.** Users re-enroll.
- **User IDs change.** Descope assigns its own user IDs. B2C's object ID (`oid`) is imported as the
  `azureObjectId` custom attribute, and a JWT Template can emit it as `oid`.
- **MSAL is not the end state.** MSAL can be pointed at Descope, but Microsoft calls that mode
  limited support. This skill keeps MSAL and reconfigures it; replacing it with the Descope SDK or
  a standard OIDC library is a required step before production.
- **Policies become Flows.** Each user flow or custom policy journey (`B2C_1_…`, `B2C_1A_…`) maps
  to a Descope Flow. Sign-up / sign-in and password reset can be one Flow (reset is a branch of
  sign-in). Profile edit becomes the User Profile Widget or an embedded Flow in the app, not a
  second hosted login. Both need a Descope session in the browser; a server-rendered app on hosted
  login has none, so it signs the user in again inside an embedded profile Flow, or changes simple
  fields (name) from the server with the Management API. API connectors and REST technical profiles become Flow HTTP Connectors.
- **Claims differ.** `scp` → `scope` (same space-separated scope names), `emails` array → `email`
  (add it in the JWT Template), `tfp` / `acr` policy checks become dead code.
- **Enterprise SSO cutover isn't free.** Customer IdPs keep working without reconfiguration only
  for connections on a hostname the customer controls. Connections on `*.b2clogin.com` need the
  customer's IdP admin to update them. OIDC connections also need the original client secret.

---

## Step 1: MCP check (non-blocking)

Check which Descope MCP is connected, without asking:

1. **Descope MCP Server** (`https://mcp.descope.com`): call `docs_search` with a simple query
   (for example "session validation").
2. If that fails, **Descope Docs MCP** (`https://docs-mcp.descope.com/mcp`): call
   `search-descope-docs`.
3. If neither responds, continue, and mark every SDK method name, option shape and return type you
   write as **"verify: based on last known documentation"** in the plan and summary.

With an MCP, verify each SDK method before writing it. Record which MCP was used in the plan.
Only the Descope MCP Server can make Console changes (Step 6); the Docs MCP can't.

---

## Step 2: Scope check

Grep the repo (case-insensitive) for `b2clogin.com`, `B2C_1`, `/tfp/`, `AzureAdB2C`,
`WithB2CAuthority`.

| Repo shows | Result |
|---|---|
| Any of the markers, on any host (including a custom domain) | Azure AD B2C: continue |
| `*.ciamlogin.com` (Entra External ID), or `login.microsoftonline.com/<tenant>` with no B2C policy (workforce Entra ID) | Stop |
| Another provider (Auth0, Okta, Stytch, WorkOS, PingOne, others) | Stop and name the matching `<provider>-to-descope` skill if one exists |
| No provider visible | Stop: a person must confirm the provider |

When stopping, write only this, and change no code:
> This skill covers Azure AD B2C only. This app signs in with <provider> (`<file>:<line>`). No code was changed.

---

## Step 3: Discovery (code only)

Record every hit as `file:line`:

- **Libraries:** `@azure/msal-browser`, `@azure/msal-react`, `@azure/msal-angular`,
  `@azure/msal-node`, `Microsoft.Identity.Web`, `Microsoft.Identity.Client`, `passport-azure-ad`,
  NextAuth's Azure AD B2C provider, native MSAL, and other OIDC / OAuth clients pointed at B2C
  (`oidc-client-ts`, `angular-auth-oidc-client`, `angular-oauth2-oidc`, hello.js, AppAuth, OWIN
  or ASP.NET Core OpenID Connect, Spring Security).
- **Login mode:** `loginRedirect` / `loginPopup` (SPA), OIDC middleware (server-side web app),
  an iframe with a custom policy (embedded sign-in), a password grant (ROPC).
- **Policies:** each `B2C_1_…` / `B2C_1A_…` name and the app that calls it; custom policy XML in
  the repo.
- **API scopes:** scopes requested from the frontend; `scp`, `[RequiredScope]`,
  `VerifyUserHasAnyAcceptedScope` in the backend; client-credentials (`.default`) callers.
- **Claims read:** `oid`, `sub`, `emails`, `tfp`, `acr`, `extension_*`, roles or groups.
- **User IDs:** where `oid` / `sub` is stored as a key, and anything that parses it as a GUID.
- **Organizations:** `domain_hint`, tenant or organization claims, per-customer IdPs.
- **Config:** `appsettings*.json`, `.env*`, CI and IaC files with B2C values.

User flows, identity providers, API connectors and Conditional Access live in the Azure portal, not
the repo. Don't infer them from code: list them under **Open questions** for a person to confirm.

---

## Step 4: Decisions

Make each decision from the discovery evidence. Where the evidence doesn't settle it, use the
default. Record every row in the plan's **Decisions** table: decision, choice, evidence
(`file:line` or "no evidence: default"), and what would change it.

| Decision | Rule | Default |
|---|---|---|
| **Login** | MSAL redirect or popup, or server-side OIDC → Descope-hosted login (B2C users already redirect, so it's the smallest UX change). Embedded sign-in (B2C in an iframe, a custom policy with `JourneyFraming`) → embedded Descope Flow, never the hosted page, whatever library the app uses today. ROPC native app → Descope native SDK. Popup moves to redirect. | Descope-hosted login |
| **MSAL** | Redirect login: keep it and point it at Descope (Step 6). Embedded sign-in: remove it; the embedded Flow replaces it. `Microsoft.Identity.Web` can't point at Descope → the standard ASP.NET Core OpenID Connect or JwtBearer handler. Native MSAL isn't verified against Descope → Descope native SDK. Put replacing MSAL under **Before production** in the summary. | Keep MSAL, reconfigured |
| **Other OIDC libraries** | Redirect login: keep the library and point its configuration at the Inbound App or Federated App (Step 6). Unlike MSAL, it can stay after cutover. Embedded sign-in: remove it, as with MSAL. Only the MSAL setup has been tested, so mark sign-in with this library "untested: verify" in the summary. | Keep the library, reconfigured |
| **Descope app** | Frontend requests B2C scopes and the API checks them → Inbound App for the frontend + Resource for the API, same scope names. Client-credentials callers → confidential Inbound App. No API scopes → Federated App (server-side OIDC) or plain SDK session. Embedded Flow → Descope session token (`aud` = project ID, no `scope` claim): it can't mint Inbound App access tokens, so map the API's scope checks to roles or permissions in the session token. | Inbound App + Resource when any scope check exists |
| **Projects and tenants** | Separate B2C directories for dev / staging / prod → one Descope project per environment. Customer organizations inside one directory (per-customer IdPs, `domain_hint`, an org claim) → Descope tenants in one project. | One project per environment, no tenants |
| **User ID** | Keep the B2C ID: import `oid` as `azureObjectId`, emit it as `oid` in the JWT Template (and override `sub` if the code keys on `sub`). The sign-up Flow fills `azureObjectId` for new users with their Descope user ID (`U…`, not a GUID), so GUID-only code must accept strings: `Guid.Parse` / `UUID.fromString`, `{id:guid}` routes, GUID regexes and DTOs (change them), and `uniqueidentifier` / `uuid` columns and downstream systems (list them as team tasks before cutover). If those can't take a string before cutover, choose **Remap on first login** instead and record why. | Keep the B2C ID |
| **Passwords** | Full import without passwords, with a reset or passwordless step on first login. It needs no change in the B2C tenant and lets B2C shut down soonest. List JIT via ROPC (keeps passwords, needs an ROPC policy in the tenant) as the alternative. | Import without passwords |
| **Roles** | Recreate in Descope RBAC the roles the code reads, with the same names. | Same role names |
| **Cutover** | No enterprise IdPs → direct, one app at a time. Enterprise IdPs or many apps → two-stage broker: Descope in front of B2C, then move B2C's custom-domain hostname to Descope through the SSO migration Worker ([docs.descope.com/migrate/sso](https://docs.descope.com/migrate/sso)). A CNAME alone breaks SSO, because Descope doesn't serve B2C's paths that customer IdPs still post to. | Direct, per app |
| **Enterprise SSO** | One Descope tenant per customer connection. Mark every connection whose hostname is unknown as "IdP admin may need to act". | Admin action assumed |

---

## Step 5: Write MIGRATION-PLAN.md

Write it to the working directory, in plain English, with these sections:

1. **Overview** — what's replaced, the login mode, the Descope app type, files changing, user
   impact, biggest risk.
2. **Decisions** — the Step 4 table, one row per decision with its evidence and reasoning.
3. **Auth touchpoints** — file, what it does today, what changes.
4. **Journeys** — each B2C policy → Descope Flow.
5. **Console setup** — checklist (applied in Step 6 when allowed, otherwise for a person): project per environment (in the region matching the
   B2C directory; fixed at creation), Flows, auth methods, Resource + Inbound App + access policy
   (Allow, subject = Inbound App, target = Resource with all scopes, grant type User access), the
   Inbound App's sign-in Flow running **Update User Consent** with **Scopes auto approval** (without
   the action the Flow fails; without auto approval the token has no scopes and the API returns
   403), a JWT Template with every claim the code reads (for example `email`, `name`,
   `given_name`, `family_name`, `oid`, custom attributes), roles, custom attributes including
   `azureObjectId`, tenants + SSO before importing their users, audit connector. Select the JWT
   Template as the project's **User JWT Token Format** (Project Settings → Session Management) for
   session tokens, or on the Inbound App (Session Management → Custom → User JWT template) for its
   access tokens. Until then, those claims are missing and the app shows empty user fields.
6. **Environment variables** — remove the B2C ones, add `DESCOPE_PROJECT_ID` and the app's
   client ID / issuer / Resource identifier. `DESCOPE_MANAGEMENT_KEY` server-side only.
7. **User migration** — the password and user ID choices; Graph export; dev → staging → production
   order, run by the team.
8. **Customer tasks in B2C** — anything needed in the tenant, with an owner.
9. **Open questions** — everything discovery couldn't see (portal configuration, enterprise
   connection hostnames, user counts, data residency).

Then continue to Step 6. Don't wait for a review.

---

## Step 6: Code changes

**Console setup through the Descope MCP Server.** Only when the Descope MCP Server is connected
and the user's request names a project ID as dev or otherwise not production:
1. Select that project (`session` → `selectProject`) and check that its ID matches the one in the
   request. If it doesn't, stop the Console setup and leave the checklist for a person.
2. Elevate (`session` → `elevate`).
3. Apply the plan's Console setup checklist. Add what is missing; don't delete or overwrite
   existing Flows, apps or settings — list each conflict under **Open questions**. For the JWT
   Template, select it on the Inbound App for its access tokens. Set the project-wide **User JWT
   Token Format** only for embedded-Flow or SDK session tokens, since it applies to every app in
   the project. Never apply a template that overrides `sub` project-wide: users without
   `azureObjectId` then fail at the token endpoint (`E063305`). List it under **Open questions**.
4. Mark each item in the plan as done, with what was changed. Leave any step that fails in the
   checklist for a person.

Without a named non-production project, change nothing in Descope.

Before each code change, verify the SDK method with the MCP, or read the installed package's type
declarations. Verify package versions (`npm view @descope/react-sdk version`,
`dotnet package search Descope --exact-match`).

- **MSAL:** change its configuration, not its calls:
  - `clientId` → the Inbound App client ID; `authority` → the Inbound App issuer;
    `knownAuthorities` → the Descope host; `redirectUri` → a URL registered on the Inbound App.
  - `system.protocolMode: "OIDC"` (msal-browser, msal-react, msal-angular, msal-node). MSAL.NET:
    `WithOidcAuthority(<issuer>)`, version 4.60.0 or later.
  - MSAL lowercases the authority, and the project ID in the discovery URL is case-sensitive. Fetch
    `<issuer>/.well-known/openid-configuration` yourself and pass it as `authorityMetadata`, then
    create the MSAL instance.
  - Send the Resource on both requests: msal-browser 5.x, the request's `resource` option; 2.x and
    3.x, `extraQueryParameters: { resource }` and `tokenBodyParameters: { resource }`. msal-node:
    send `resource` as a form field in the token request body. MSAL.NET:
    `.WithExtraQueryParameters(new Dictionary<string, string> { ["resource"] = "<Resource>" })`
    (untested: check the token's `aud`).
  - Popup calls (`loginPopup`, `acquireTokenPopup`) move to redirect.
- **Other OIDC libraries:** change their configuration: issuer / authority, client ID and redirect
  URI from the Inbound App or Federated App, and the Resource when calling a scoped API. Most
  libraries send `resource` only on `/authorize`, and Descope also needs it in the token request
  body; add the small hook that does this (ASP.NET Core: `OnAuthorizationCodeReceived` sets
  `TokenEndpointRequest.Resource`). If discovery returns 404, the library changed the issuer's
  casing; give it the discovery URL directly (for example `MetadataAddress` in .NET).
- **Scopes (MSAL and other libraries):** replace full App ID URI scopes
  (`https://<tenant>.onmicrosoft.com/<api>/tasks.read`) with the Resource's short names
  (`tasks.read`), and keep `openid profile offline_access`.
- **Embedded sign-in:** remove the iframe, the sign-in route that ran inside it, the
  `window.top.location.reload()` / `postMessage` glue. Leave the custom policy XML as it is, for
  rollback.
  Render the Flow in the page:
  - React: `<Descope flowId="sign-up-or-in" onSuccess={…} />`.
  - Server-rendered pages (Express + EJS, ASP.NET MVC): `@descope/web-js-sdk` and
    `@descope/web-component`, `<descope-wc project-id="…" flow-id="sign-up-or-in">`, and
    `sdk.refresh()` in the `success` handler and at the top of every authenticated page. The server
    validates the session on every request with the backend SDK. For the session cookie, use
    **Manage in cookies** in production (needs a custom domain on the app's site) and
    `sessionTokenViaCookie: true` on `localhost`.
  - Logout: `sdk.logout()`, then end the app's own session.
- **Backend:** validate Descope tokens. Check `iss` against the issuer taken from discovery (never
  hardcode it) and `aud` against the Resource identifier for Inbound App tokens. Read `scope`
  instead of `scp`; in .NET, replace `[RequiredScope]` with a policy that reads `scope`. Embedded
  Flow: the API validates the session token (`aud` = project ID) and replaces each scope check with
  a role or permission check.
- **Claims:** `emails[0]` → `email`. Keep the API's `oid` reads from the access token when the JWT
  Template emits `oid`. Move frontend reads of `oid` from the ID token (for example an `owner`
  field) to the API: in testing, JWT Template custom claims reached the access token but not the
  ID token.
- **Dead code:** remove per-policy authorities, `AADB2C90118` password-reset redirects, `tfp` /
  `acr` checks, per-policy metadata URLs.
- **Config:** remove `AzureAdB2C` sections and `B2C_*` / `MSAL_*` variables; add the Descope
  values. Keep custom policy XML until cutover, for rollback.
- **User migration:** write the Graph export and transform scripts (import `oid` as
  `azureObjectId`, social users with `verifiedEmail: true`, each enterprise SSO user into exactly
  one tenant). Don't run them.

---

## Step 7: Checks

1. Stale-reference sweep of app code and config (not `MIGRATION-*.md` or rollback policy XML):
   ```bash
   grep -rnI "@azure/msal\|Microsoft.Identity.Web\|passport-azure-ad\|b2clogin.com\|B2C_1\|AzureAdB2C\|\"scp\"\|emails\[0\]\|AADB2C" \
     --exclude="MIGRATION-*.md" --exclude="*.lock" --exclude="package-lock.json" \
     --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=bin --exclude-dir=obj --exclude-dir=.git .
   ```
   Fix every hit, except hits in the custom policy XML kept for rollback. In apps that keep MSAL
   for redirect login, `@azure/msal` stays until MSAL is replaced.
2. Install and run the project's build or type check with zero errors (`npx tsc --noEmit`,
   `dotnet build`, …).
3. Run the existing tests. Failures usually mean fixtures still use B2C claim shapes.
4. A protected API returns 401 with no token and with a malformed token, never 500. In a
   server-side web app, a protected page opened while signed out redirects (302) to the Descope
   host, not to `b2clogin.com`.

---

## Step 8: Write MIGRATION-SUMMARY.md

1. **What changed** — B2C concept → Descope replacement, files touched.
2. **Decisions made without a person** — the Step 4 table, so a reviewer can overturn any row.
3. **Open questions** — from the plan, plus anything marked "verify".
4. **Not yet verified, needs a person** — sign-in on the Descope page (or in the embedded Flow)
   returns to the app; API call succeeds with the new token and returns 403 without the scope
   (embedded Flow: without the role); logout clears the session; token claims for one migrated and
   one new user (Inbound App tokens: `iss`, `aud` = Resource, `scope`; embedded Flow session token:
   `aud` = project ID, roles; both: `email`, `oid`); silent token renewal works; after a dev import, one local, one social and one enterprise SSO user each
   land on their imported account.
5. **Before production** — replace MSAL, if it was kept, with the Descope SDK or a standard OIDC
   library; Console setup, customer IdP admin notices, the user import order, the cutover steps.
6. **After cutover** — improvements left out on purpose (passkeys, adaptive MFA).

---

## External docs

- Azure AD B2C migration guide: https://docs.descope.com/migrate/azure-ad-b2c
- Migration strategy: https://docs.descope.com/migrate/strategy
- SSO migration: https://docs.descope.com/migrate/sso
- Inbound Apps: https://docs.descope.com/identity-federation/inbound-apps
- Resources: https://docs.descope.com/resources
- Auth Hosting: https://docs.descope.com/identity-federation/auth-hosting
- Descope MCP Server: https://docs.descope.com/mcp/mcp-server
