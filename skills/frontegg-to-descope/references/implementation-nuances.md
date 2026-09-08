# Descope Migration: Implementation Notes (Frontegg → Descope)

## Contents

**General Insights — Architecture & Flow**
- [Frontegg owns the ceremony; Descope validates tokens](#frontegg-owns-the-ceremony-descope-validates-tokens)
- [Hosted vs. embedded: the two starting points](#hosted-vs-embedded-the-two-starting-points)
- [No drop-in middleware](#no-drop-in-middleware)
- [What disappears entirely](#what-disappears-entirely)

**General Insights — Feature Mapping: Frontegg → Descope**
- [Migrating user and account data](#migrating-user-and-account-data)
- [Token claim mapping](#token-claim-mapping)
- [Multi-tenancy: Accounts → Tenants](#multi-tenancy-accounts--tenants)
- [RBAC: Frontegg → Descope](#rbac-frontegg--descope)
- [ReBAC migration](#rebac-migration)
- [Entitlements, plans, and feature flags](#entitlements-plans-and-feature-flags)
- [Prehooks → Flow steps, Connectors, and JWT Templates](#prehooks--flow-steps-connectors-and-jwt-templates)
- [Webhooks → Descope Audit Webhook and Connectors](#webhooks--descope-audit-webhook-and-connectors)
- [Security rules → Flow-based security](#security-rules--flow-based-security)
- [SSO and SCIM](#sso-and-scim)
- [M2M: Frontegg tokens → Inbound Apps or Access Keys](#m2m-frontegg-tokens--inbound-apps-or-access-keys)
- [Frontegg AI integrations → Descope Connections / Outbound Apps](#frontegg-ai-integrations--descope-connections--outbound-apps)
- [Management API mapping](#management-api-mapping)

**Framework Recipes**
- [Next.js](#nextjs)
- [React](#react)
- [Node.js backend](#nodejs-backend)
- [Python backend](#python-backend)
- [Go backend](#go-backend)
- [Java and .NET (no Frontegg SDK)](#java-and-net-no-frontegg-sdk)
- [Mobile](#mobile)

**General Insights — Common Gotchas**
- [Cookie names: DS and DSR](#cookie-names-ds-and-dsr)
- [Audience validation requires explicit setup](#audience-validation-requires-explicit-setup)
- [Logout requires two steps](#logout-requires-two-steps)
- [Env var reduction](#env-var-reduction)
- [Approved Domains: domain only](#approved-domains-domain-only)
- [Testing checklist](#testing-checklist)

> **See also:** `flows-and-widgets.md` in this directory — Frontegg→Descope lingo map, Flow structure and templates, the full self-service portal mapping table, Widget types, SSO Setup Suite, and the Console-vs-code decision guide. Read it before migrating any auth UI, MFA enrollment, admin/portal pages, or SSO configuration.

> **Source of truth:** for anything Frontegg-specific, verify against
> [developers.frontegg.com](https://developers.frontegg.com/ciam/guides/getting-started/home) — every
> page is fetchable as clean markdown by appending `.md` to the URL. For anything Descope-specific,
> use the Descope Docs MCP or [docs.descope.com](https://docs.descope.com).

---

## General Insights

**— Architecture & Flow —**

### Frontegg owns the ceremony; Descope validates tokens

Frontegg's SDKs own the whole authentication ceremony. The frontend SDKs (`@frontegg/react`,
`@frontegg/nextjs`, `@frontegg/vue`, `@frontegg/angular`, `@frontegg/js`) either redirect to the
hosted login box or inject `/account/login`, `/account/sign-up`, and `/account/logout` routes into
the app; they hold the session, refresh it at roughly 80% of the JWT's lifetime, and expose auth
state through hooks or observables. The backend SDKs (`@frontegg/client`, `frontegg` for Python,
`github.com/frontegg/go-sdk`) validate the resulting access token per request and attach the user to
the request context.

Descope splits the work the same way but with fewer moving parts. The frontend
([Descope Flows](https://docs.descope.com/flows) via
[web components](https://docs.descope.com/client-sdk/descope-components) or
[client SDKs](https://docs.descope.com/client-sdk/initialize-sdk)) runs the ceremony and stores JWTs
in `DS` (session) and `DSR` (refresh) cookies. The backend
[validates those JWTs](https://docs.descope.com/sessions/validation/backend).

The practical consequence: every Frontegg→Descope migration replaces the Frontegg provider plus
login entry point with a Descope provider plus Flow, and replaces the Frontegg middleware with a
~20-line session validator. Everything else — tenants, roles, SSO — is configuration.

### Hosted vs. embedded: the two starting points

This determines the shape of the frontend migration more than the framework does. Establish it first.
The signal is `hostedLoginBox` (in the app options) or `FRONTEGG_HOSTED_LOGIN` — note that the Next.js
SDK's **Pages Router** deprecates the `hostedLoginBox` prop in favor of the environment variable —
but the **App Router** quickstart still requires the prop alongside the env var, so check which
router is in play before assuming the prop is dead. Either way, a codebase may
carry both, and the env var wins.

| | Frontegg hosted | Frontegg embedded |
|---|---|---|
| Where login renders | `https://[frontegg-domain]/oauth/account/login` | Injected `/account/login`, `/account/sign-up`, `/account/logout` routes inside the app |
| Protocol | OAuth2/OIDC + PKCE, full redirect | Login component rendered in-app; the SDK still drives the OAuth flow |
| Trigger | `loginWithRedirect()` / `useLoginWithRedirect()` | Navigate to the injected `/account/login` route |
| Session refresh | `keepSessionAlive` in `authOptions` — **the same flag in both modes**, refreshing at ~80% of token lifetime | same |
| Logout | Navigate to `{baseUrl}/oauth/logout?post_logout_redirect_uri=…` | Navigate to `/account/logout` (or call `logout()`); clears `fe_refresh` |
| Descope target | **Auth Hosting** / hosted Flow | Embedded `<Descope flowId>` / `<descope-wc>` component |

Three traps. First, **logout in both modes is usually a navigation, not a method call** — often just
an anchor tag — so a grep for `logout()` will miss it. That link has to become real two-step logout
handling. Second, mobile SDKs are **always** hosted, so a project with an embedded web app and a
mobile app needs both targets. Third, do not treat `keepSessionAlive` or `useAuthUser()` as evidence
of either mode; both appear in hosted and embedded quickstarts alike. `hostedLoginBox` /
`FRONTEGG_HOSTED_LOGIN` is the only reliable signal, and the Console's Login method setting is the
authority if the code is ambiguous.

Match the existing model unless the user explicitly wants to change it. Switching models mid-migration
changes routing, redirect handling, and session bootstrapping simultaneously, which makes failures
hard to attribute.

### No drop-in middleware

Frontegg gives you a middleware or dependency per backend framework —
`withAuthentication()` (Node), `@with_authentication(...)` (Flask), `Depends(FronteggSecurity(...))`
(FastAPI), `frontegg.WithAuthentication(...)` (Go). Descope publishes an equivalent only for Next.js
(`authMiddleware` from `@descope/nextjs-sdk/server`). For Express, Flask, FastAPI, Go, and everything
else, each becomes custom code:

1. Read the `DS` cookie (or the `Authorization` header for API clients).
2. Call `validateSession()` / `validate_session()` / `ValidateSessionWithToken()`.
3. Attach the resulting claims to the request context.
4. Check roles/permissions with the SDK's validation helpers.

The [Descope blog](https://www.descope.com/blog/post/authentication-middleware) shows an Express
pattern; FastAPI has a documented
[JWT authorizer approach](https://docs.descope.com/sessions/validation/jwt-authorizers/python-fastapi-jwt-authorizer).
Both are tutorials, not packages.

**Semantics gotcha:** Frontegg's Go middleware treats its `Roles` and `Permissions` options as
**OR** — the request passes if *at least one* matches. Do not assume the Descope helper you reach for
has the same semantics. Verify, and where the check is genuinely "any of," write it explicitly.

### What disappears entirely

Worth calling out in the plan, because it is real scope *removal*:

- **Silent refresh plumbing** — `keepSessionAlive`, `disableSilentRefresh`, the `/silent` endpoint, and the 80%-of-lifetime refresh timer. The Descope SDK handles refresh.
- **Session cookie encryption** — `FRONTEGG_ENCRYPTION_PASSWORD` and `FRONTEGG_COOKIE_NAME` (`fe_session`) in Next.js.
- **Per-service endpoint overrides** — `FRONTEGG_IDENTITY_SERVICE_URL`, `FRONTEGG_ENTITLEMENTS_SERVICE_URL`, `FRONTEGG_AUDITS_SERVICE_URL`, `FRONTEGG_EVENT_SERVICE_URL`, `FRONTEGG_OAUTH_SERVICE_URL`, `FRONTEGG_VENDORS_SERVICE_URL`, `FRONTEGG_METADATA_SERVICE_URL`, `FRONTEGG_AUTHENTICATION_SERVICE_URL`, `FRONTEGG_API_GATEWAY_URL`.
- **Access-token caching config** — the Node SDK's `local` / `redis` / `ioredis` cache options.
- **The self-hosted entitlements engine**, if ReBAC was in use: SpiceDB, CockroachDB, the `frontegg/e10s-engine-sync` job, the docker-compose stack, and the `frontegg/entitlements-engine` Helm release. Descope's ReBAC is managed. Remember to delete the infrastructure, not just the client code.

**— Feature Mapping —**

### Migrating user and account data

**Check what exists before planning around it.** Descope's [migration index](https://docs.descope.com/migrate)
and the [descope-migration](https://github.com/descope/descope-migration) tool each cover a fixed set
of providers, and a Frontegg guide or tool module may or may not be published when you run this. Open
both and look. Prefer a tool if one exists; otherwise use the custom recipe below. **Never instruct
the user to run a tool or open a guide you have not confirmed exists.**

The three paths below are Descope's standard migration shapes — the same ones documented for
[Keycloak](https://docs.descope.com/migrate/keycloak), [Cognito](https://docs.descope.com/migrate/cognito),
and [Azure AD B2C](https://docs.descope.com/migrate/azure-ad-b2c) — applied to Frontegg.

#### The constraint that shapes everything

Frontegg documents a rich *inbound* migration API — bulk import of up to 1,000 users per batch, with
`passwordHashType` accepting at least `bcrypt`, `scrypt`, `firebase-scrypt`, `pbkdf2`, and `argon2`
(confirmed), plus `sha256` (confirmed) and possibly `sha1` (check the live API reference — it doesn't
consistently appear in current docs) — and **no bulk export endpoint and no password-hash export**. User *profiles* can be read out
via the paginated list endpoint, but nothing credential-shaped comes with them: `passwordHash` appears
only on the inbound migration request schema, and the only CSV export endpoints in the entire product
are for audit logs.

`GET /resources/users/v3` returns `id`, `email`, `name`, `profilePictureUrl`, `sub`, `verified`,
`mfaEnrolled`, `mfaBypass`, `phoneNumber`, `provider`, `tenantId`, `tenantIds`, `activatedForTenant`,
`isLocked`, `invisible`, `superUser`, `metadata`, `vendorMetadata`, `externalId`, `lastLogin`,
`createdAt`, `subAccountAccessAllowed`, `managedBy`, and a `tenants[]` array. Two shape details that
break naive export scripts: `temporaryExpirationDate` and `isDisabled` live **inside** `tenants[]`
(per tenant), not at the top level — miss them and you silently drop guest-user expiry and per-tenant
disable state. And `tenants[]` entries carry only `tenantId`, `roles`, `temporaryExpirationDate`, and
`isDisabled`; **permissions are not a sibling of `roles`** — each role object in `roles[]` carries its
own `permissions`, one level deeper.

So the password strategy is a decision, not a lookup. Make it in Step 0.5, before estimating anything.

#### Path 1 — Full migration (default)

Read accounts, roles, permissions, and users out of the Frontegg Management API and create the
matching objects in Descope in **dependency order: tenants → permissions → roles → users**. That
order is not optional — users cannot be created with tenant associations and role assignments that do
not exist yet.

If `descope-migration` ships a Frontegg module, use it and follow its README for the required
environment variables; it will need a Frontegg Client ID and API Key with read access to tenants,
permissions, roles, and users, plus a Descope Project ID and Management Key. If it does not, the
custom recipe below does the same work.

Either way: **pre-define every custom attribute in the Descope Console before importing.** Descope
rejects custom attributes that are not already in the project schema, so `fronteggId`,
`freshlyMigrated`, and anything derived from Frontegg `metadata` / `vendorMetadata` must be created
first. Then dry-run against a **dev** project, review the output, and only then run staging and
production.

Passwords do not come along. After import, set a `freshlyMigrated` custom attribute and branch on it
in the Flow to force a reset or onboard the user into a passwordless method. Set `verifiedEmail` and
`verifiedPhone` to `true` where Frontegg already marked them verified — otherwise every migrated user
gets re-verified, which looks like a bug to them. Note that `customAttributes` on the batch-create API
is string-valued, so model `freshlyMigrated` as a Console-defined boolean or a string, not an
arbitrary JSON type.

#### Path 2 — JIT migration with a Generic HTTP Connector (preserves passwords)

The only path that keeps existing passwords working:

1. The user enters email and password in the Descope Flow.
2. A [Generic HTTP Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http) step calls Frontegg's authenticate-local-user API to verify the credentials.
3. On success, the Flow creates or updates the Descope user, sets their password, and issues a Descope session.
4. Subsequent sign-ins authenticate directly against Descope.

Configure the connector with the Frontegg auth endpoint and a request body carrying email and
password, then map the response (user ID, email, tenant) onto Descope user attributes and flow
context. Add a Flow condition so already-migrated users skip the connector entirely.

One mechanic worth knowing before building this: there is **no separate "Set Password" action**. On a
successful connector response the Flow invokes the **Sign Up / Password** action, which creates the
user and sets the password in one step — an agent hunting for a set-password step will not find one.

Descope documents this exact pattern for [Keycloak](https://docs.descope.com/migrate/keycloak)
(submit credentials → Generic HTTP Connector POST → legacy IdP validates → on success, Sign Up /
Password), and comparable JIT flows for [Cognito](https://docs.descope.com/migrate/cognito) and
[Azure AD B2C](https://docs.descope.com/migrate/azure-ad-b2c). The Frontegg shape is identical; only
the validating endpoint changes. Read the Keycloak guide as the reference implementation, and confirm
the current Flow action names and dynamic values against the docs before building — this area has
moved before.

Frontegg must stay running until the active-user tail has signed in at least once. Instrument the
provisioning rate so the decommission date is driven by data rather than optimism.

#### Path 3 — JIT migration with Frontegg as a custom OIDC provider

For teams moving to passwordless anyway. Configure Frontegg as a
[custom OAuth/OIDC provider](https://docs.descope.com/auth-methods/oauth/providers/custom-providers)
in Descope using the Frontegg OIDC client ID, secret, and authorization/token endpoints, then add an
OAuth sign-in step to the Flow. Users authenticate through Frontegg's hosted login — MFA included —
and Descope provisions them from the returned ID token claims. Add a
[condition](https://docs.descope.com/flows/conditions) routing already-provisioned users to
Descope-native auth so they stop hitting Frontegg.

Note the Frontegg caveat that OIDC-as-IdP is hosted-login-only, and that in multi-app environments it
requires a default application because `aud` verification depends on it.

#### If a custom script is genuinely required

```bash
# 1. Mint an environment (vendor) token.
#    Region matters: EU api.frontegg.com (default), US api.us., AU api.au., CA api.ca.
curl -X POST https://api.frontegg.com/auth/vendor \
  -H 'Content-Type: application/json' \
  -d '{"clientId":"YOUR_CLIENT_ID","secret":"YOUR_API_KEY"}'

# 2. List accounts (tenants).
curl "https://api.frontegg.com/tenants/resources/tenants/v2" \
  -H "Authorization: Bearer $VENDOR_JWT"

# 3. Page users. _limit maxes out at 200.
#    IMPORTANT: _offset is a PAGE INDEX, not a record offset — 0, 1, 2, … not 0, 200, 400.
#    Loop until _metadata.totalPages. Incrementing by _limit silently truncates the export.
curl "https://api.frontegg.com/identity/resources/users/v3?_limit=200&_offset=0" \
  -H "Authorization: Bearer $VENDOR_JWT" \
  -H "frontegg-tenant-id: $TENANT_ID"        # optional, for tenant-scoped export
```

Verify the exact host and path prefixes against the Frontegg API reference before running anything —
management calls must hit the regional gateway, and `{"errors":["Failed to verify vendor JWT"]}` —
which Frontegg's troubleshooting docs attribute to misusing API contexts or hitting the wrong
gateway — is usually a host mistake, not a credential mistake. With an
environment token on a self-service route, add the `frontegg-user-id` and/or `frontegg-tenant-id`
headers.

Field mapping into Descope:

| Frontegg | Descope |
|---|---|
| `email` (or the primary identifier) | `loginIds` (required, unique) |
| `name` | `name`, or split into `givenName` / `familyName` |
| `phoneNumber` | `phone` |
| `tenantId` / `tenantIds` | Tenant association — create the tenants first |
| `tenants[].roles` | Tenant-scoped role assignment |
| `verified` | `verifiedEmail` |
| `metadata` | User custom attributes (define them in Descope first) |
| `vendorMetadata` | User custom attributes — often the pre-Frontegg internal user ID, and frequently the join key back to the application database |
| `externalId` | Custom attribute; use it as the dedupe key |
| `id` | Custom attribute (`fronteggId`) for the ID mapping table |

Import with `POST /v1/mgmt/user/create` or `POST /v1/mgmt/user/create/batch` (mind the
[rate limits](https://docs.descope.com/rate-limiting)), using the
[user format guide](https://docs.descope.com/migrate/custom/user-format-json).

#### Data-quality issues to expect

- **Duplicate users from SCIM email changes.** Frontegg's docs acknowledge that changing a user's email at the IdP creates a *new* Frontegg user rather than updating the existing one. Long-lived SCIM tenants accumulate orphans. Dedupe on `externalId` before import, and reconcile `lastLogin` to decide which record wins.
- **Unverified users from social/password merging.** Frontegg auto-merges users on email. If email verification was disabled in the environment, some records are unverified in ways the app never surfaced.
- **Users with no usable login method.** Passkey and TOTP enrollments do not transfer, and passwords do not export. A user whose only method was a passkey has nothing to sign in with post-cutover unless the Flow offers an alternative.
- **Multi-app assignment.** Frontegg does not support automatic migration into specific applications, so app assignment may be inconsistent in the source data too.

#### Dual token validation

Unless the cutover is a hard big-bang switch, the backend must validate **both** Descope and Frontegg
tokens during the transition: inspect the issuer or `kid` to determine the provider, then validate
accordingly. This is mandatory for both JIT paths. See
[session migration](https://docs.descope.com/migrate/session-migration) — currently in **beta**,
documented only for Auth0, Okta, or a custom-built solution, and it assumes the user already exists in
Descope (not a JIT mechanism), so confirm it covers the Frontegg case before relying on it; otherwise
hand-roll the issuer/`kid` check described above. Schedule the removal of the Frontegg branch as an
explicit follow-up — dual validation left in place is a permanent second attack surface.

### Token claim mapping

Frontegg's default access token is unusually rich; Descope's is deliberately lean. This table is the
one to work from when auditing claim reads.

| Field | Frontegg claim | Descope |
|---|---|---|
| User ID | `sub` | `sub` |
| Display name | `name` (`{{user.name}}`) | **Not in JWT by default.** Add via [JWT Templates](https://docs.descope.com/management/token/jwt-templates). |
| Email | `email` (`{{user.email}}`) | **Not in JWT by default.** Add via JWT Templates. |
| Email verified | `email_verified` (`{{user.verified}}`) | Not in JWT by default; available on the user object as `verifiedEmail`. |
| Profile picture | `profilePictureUrl` | **Not in JWT by default.** Add via JWT Templates. |
| User metadata | `metadata` (`{{user.metadata}}`) | Custom attributes; add to the JWT only if the app reads them at request time. |
| Vendor metadata | *(deliberately excluded from the JWT)* | Custom attributes. |
| Roles | `roles` (role **keys**, `{{user.tenant.roles}}`) | `roles` array (embedded by default with [RBAC](https://docs.descope.com/authorization/role-based-access-control)); per-tenant roles live under `tenants`. |
| Permissions | `permissions` (`{{user.tenant.permissions}}`) | `permissions` array; per-tenant under `tenants`. |
| Active tenant | `tenantId` (flat string) | `dct` — flat string, direct equivalent. |
| Tenant membership | `tenantIds` (array) | `tenants` — object keyed by tenant ID holding per-tenant `roles` and `permissions`. |
| Session ID | `sid` | Not present by default. |
| Token type | `type` | Not present by default. |
| Application | `applicationId` | Not present by default. |
| Audience | `aud` (clientId or appId) | **No `aud` by default.** Configure explicitly if the app validates it. |
| Auth methods | `amr` (protected in Frontegg) | `amr` (present by default). |
| Step-up | `acr` (single supported value) | `su` claim on the step-up Flow template. |
| — | — | `drn` (Descope-specific). |

Two migration-specific notes. First, if a `JWT_GENERATION` prehook injected custom claims, those
belong in the Descope JWT Template or a Flow custom-claims action — grep for the prehook, not just
for claim reads, because the claims may only be documented inside the prehook's code. Second,
Frontegg's protected internal claims (`act`, `amr`, `acr`) could not be overridden; if application
code special-cased that, the constraint no longer applies.

### Multi-tenancy: Accounts → Tenants

Frontegg's docs state that Accounts and Tenants are equivalent. The mapping is one Frontegg account →
one Descope tenant, and the code change is mostly mechanical:

- **Management code** (loading an account, updating settings, managing members, assigning roles, configuring SSO/SCIM) passes a `tenantId` to Frontegg APIs. It becomes a Descope tenant ID passed to `management.tenant.*` / `management.user.*`. By-ID work, no token parsing.
- **Request-time code** that read `tenantId` off the session reads `dct` instead; code that read `tenantIds` reads the keyed `tenants` object. Prefer SDK helpers (`validateTenantRoles(...)`, `validateTenantPermissions(...)`) over hand-parsing.

Tenant switching (`switchTenant({ tenantId })`, plus `silentReload` on newer SDKs, plus
`enableSessionPerTenant` for per-browser-tab tenancy) becomes Descope active-tenant selection.
Confirm the per-tab behavior explicitly if `enableSessionPerTenant` was enabled — that is a
deliberate product decision someone made, not a default.

**Sub-accounts map to Descope sub-tenants.** A Descope tenant can have multiple sub-tenants, those
can nest further, and each sub-tenant has exactly one parent. **Role inheritance** is configurable per
parent — Full (roles and users flow down), User only, or None — and sub-tenants can carry their own
SSO configuration, custom attributes, and RBAC. Two things are always inherited and cannot diverge:
**password settings and session management**. If a Frontegg sub-account had its own password policy,
that is a real behavior change to flag.

The other constraint is the token. The `tenants` JWT claim is **flat** — it lists tenant IDs with
their roles and permissions, and encodes nothing about parentage. Request-time code that needs
hierarchy has two options: add a `tenant.subtenant` claim via a JWT template, or call Load/Search
Tenant server-side and read `parent` / `successors`. Grep for hierarchy reads before assuming the
mapping is transparent.

Frontegg supports a third tenancy layer and beyond;
Descope tenants are flat. Options, in rough order of preference:

| If the hierarchy is… | Model it as… |
|---|---|
| A tenancy structure with admins acting across levels | **Sub-tenants** with Full role inheritance — the default choice |
| A tenancy structure where child admins are isolated | **Sub-tenants** with role inheritance set to None or User only |
| A reporting or rollup concept only | Flat tenants plus a parent-ID custom attribute — simpler than sub-tenants if nothing enforces it |
| A fine-grained authorization boundary beyond roles | ReBAC, layered on top of the tenant structure |
| A billing artifact | Out of scope for identity; keep it in the billing system |
| Genuinely separate customers that happened to be nested | Flatten into sibling tenants |

Decide before writing migration code — the choice affects the export mapping, not just the runtime.

### RBAC: Frontegg → Descope

| Frontegg | Descope | Notes |
|---|---|---|
| Role `Key` | Role name | Descope references roles **by name**. Migrate Frontegg role *keys*, since those are what appear in the `roles` claim — not display names. |
| Permission `Key` | Permission | Frontegg's own built-ins use an `fe.<domain>.<action>.<resource>` convention (e.g. `fe.secure.read.users`). |
| Wildcard permissions (`fe.secure.read.*`, `fe.secure.*`) | **No equivalent** | Descope has no wildcard matching on permission names, role names, Resource scopes, or Policy grants. Expand every wildcard into explicit permissions during the export. |
| Default role (auto-assigned at signup) | Flow-assigned role, or a tenant default | |
| System role (applies to all accounts) | Project-level role | |
| Role assigned to specific accounts | Tenant-level role assignment | |
| Custom roles created by end customers | Role Management Widget, or Management SDK behind your own UI | |
| Groups and group roles | Roles + SCIM/SSO group mapping | Frontegg groups are a first-class object with their own `fe.secure.*.groups` permissions. |
| Role `Level` (numeric hierarchy limiting assignment) | **No equivalent** | Enforce in application logic, or encode as permissions like `role.assign.admin`. |
| Permission classification type (`Never` / `Assignable` / `Always`) | **No equivalent** | Decide which permissions end customers may self-assign in the widget or your own UI. |
| Permission assigned to a user via a "feature" | A role containing exactly those permissions | Descope does not attach permissions to users outside a role. Expect a few narrow generated roles — that is the prescribed pattern. |

Two Frontegg behaviors worth fixing rather than porting. Frontegg's own docs note that **role changes
do not take effect until the current token expires**, and recommend shortening JWT lifetime to
compensate — so many apps carry forced refreshes, artificially short tokens, or client-side role
caches that may no longer be needed. And **group roles are calculated at login and appear in the JWT,
but are not visible from the management section of the Frontegg portal** (they are visible in the
self-service portal's Groups tab), so exported role assignments can disagree with what users actually
get at login. Reconcile against a decoded token, not just the API response.

Do not recreate the `fe.*` permission catalog wholesale. Those permissions exist to gate the Frontegg
self-service portal, which is being replaced by Widgets. Migrate them only where application code
reads them.

### ReBAC migration

**First, confirm it is actually in use.** Frontegg ReBAC must be enabled by Frontegg support, so some
environments have entity types configured and zero calls to `isEntitledTo`. Grep for
`@frontegg/e10s-client`, `EntitlementsClientFactory`, `isEntitledTo`, `lookupEntities`,
`lookupTargetEntities`, and `ENTITLEMENTS_ENGINE_TOKEN` before planning any of this.

**Decision guide — does this belong in Descope ReBAC at all?**

| The authorization model is… | Target |
|---|---|
| Roles and permissions, tenant-scoped | Descope RBAC — do not use ReBAC |
| Relationships between entities (document owner, folder hierarchy, project membership, shared/delegated access) | **Descope ReBAC/FGA** |
| Per-resource rules that depend on application data (status, dates, amounts) | Application database |
| Frontegg entity types that exist but are never checked | Drop them |

**Architecture change.** Frontegg stores the ReBAC model in Frontegg Cloud but evaluates in **SpiceDB
that the customer self-hosts**, fed by the `frontegg/e10s-engine-sync` job pulling roughly every 60
seconds, usually alongside CockroachDB, with the app calling `@frontegg/e10s-client` over gRPC.
Descope evaluates in-platform. That means the migration *removes* infrastructure — remember to
decommission the docker-compose stack and the `frontegg/entitlements-engine` Helm release, and to
delete any application logic that compensated for the 60-second write-visibility lag.

**Schema translation.** Frontegg has no text DSL; the model is assembled from entity types (`key`),
relations (`relationKey`, each declaring a subject entity type), and actions (`actionKey`, mapped to
the relations that grant them), with hierarchy expressed as a JSON `relationKeys` array mixing direct
relations and inherited paths.

```
# Frontegg
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

Descope DSL syntax:

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

**Exporting the data.** Relationship tuples are the part that has to move:

| Step | Frontegg | Descope |
|---|---|---|
| Read entity types | `GET /resources/entity-types/v1` | Author the DSL schema |
| Export assignments | `GET /resources/relations/v1/assignments` | — |
| Write relations | `POST /resources/relations/v1/assign` | `management.fga.createRelations([...])` |
| Remove relations | `POST /resources/relations/v1/unassign` | `management.fga.deleteRelations([...])` |
| Check | `e10sClient.isEntitledTo(...)` | `management.fga.check([...])` |
| List accessible resources | `lookupTargetEntities()` / `lookupEntities()` | Descope FGA resource/subject lookup |

A Frontegg assignment tuple looks like
`{ subjectEntityTypeKey, subjectKey, relationKey, targetEntityTypeKey, targetKey }` — map each field
onto the Descope relation shape and bulk-create. Frontegg's guide and API reference disagree on the
exact hierarchy endpoint path, so verify against the live API reference before scripting.

**Not carried over:** time-bound access implemented with SpiceDB's `active_at` caveat has no
automatic equivalent. If the app grants temporary access this way, design the replacement explicitly
(scheduled revocation, or an application-side expiry check) rather than discovering it in production.

**Effort: High.** Always a dedicated model review, never a mechanical port.

### Entitlements, plans, and feature flags

Frontegg's entitlements engine bundles **Features** into **Plans** assigned to accounts and users,
enforced with `isEntitledTo`, `useFeatureEntitlements`, and `usePermissionEntitlements`. Descope has
no plans or feature-flag product, so this splits along a clean line.

**The access-control half maps.** A feature that is really "may this user do X" becomes a Descope
permission. A plan that is really "which capabilities does this tenant have" becomes a tenant custom
attribute checked in Flows or application code, or a set of tenant-level roles. Frontegg's
`NotEntitledJustification` enum is a useful sorting key: `MISSING_PERMISSION` is an RBAC check,
`MISSING_FEATURE` and `BUNDLE_EXPIRED` are tenant-entitlement state.

Where a Frontegg feature effectively assigns permissions directly to a user, wrap them: create a
Descope role containing exactly those permissions and assign that role. Descope attaches permissions
to roles and never directly to users, so the wrapper role is the only route; the resulting narrow
roles are intended, not a smell.

**The commercial half does not map, and mostly should not.** Plan catalogs, trials, billing tiers,
and general feature flagging belong in the billing system, the application database, or a dedicated
vendor. Frontegg's advanced targeting (rules over `frontegg.*`, custom, and `jwt.*` attributes, with
hard caps of 100 plans and 500 flags per environment) has partial analogues in Flow conditions, but
rebuilding a flag platform inside an identity provider is the wrong shape.

Get an explicit scope decision recorded before estimating. This is the item most likely to double a
Frontegg migration's timeline if it is discovered late.

### Prehooks → Flow steps, Connectors, and JWT Templates

Frontegg prehooks are synchronous, blocking calls made before an event completes, with a **5-second
timeout**, a configurable fail-open/fail-close setting, and four verdicts (`allow` / `block` /
`challenge` / `lock`). There is no single Descope equivalent — each prehook maps to whichever Descope
mechanism matches what it does.

| Prehook event | Descope target |
|---|---|
| `AUTH_INITIATED` | Flow entry conditions; `externalRedirectUrl` becomes a Flow branch or redirect action |
| `USER_SIGNUP` | Flow step during sign-up (validation, enrichment, Connector call) |
| `USER_INVITE` | Invitation Flow logic |
| `USER_UPDATE` / `USER_DELETE` | Management SDK hooks in application code, or audit-event-driven sync |
| `CREATE_TENANT` / `UPDATE_TENANT` / `DELETE_TENANT` | Application-side tenant lifecycle via the Management SDK |
| `JWT_GENERATION` | **JWT Template**, and/or a Flow custom-claims action |
| `SOCIAL_LOGIN_AUTH` / `OIDC_AUTH` / `SAML_AUTH` | Flow conditions on the authentication method + attribute mapping |
| `SEND_SMS` | Messaging Connector (Frontegg SMS template types: `0` MFA, `1` sign-in, `2` phone verification, `3` reset password) |
| `SIGN_UP_USER_POOL` | See *user pools* in SKILL.md Step 3 |

Translation rules of thumb: an **API prehook** (HTTP call to your service) becomes a **Connector**
step; a **custom-code prehook** (a function on Frontegg's side) becomes a **Scriptlet**. Carry over
the fail-open/fail-close behavior — a Connector timeout should fail the way the prehook was
configured to.

Three things to establish per prehook:

1. **Does it block?** A blocking prehook is a security control, not enrichment. It needs a real terminal branch, not a best-effort call.
2. **What does it return?** The `JWT_GENERATION` response shape carries `claims.customClaims`, an optional `expiresIn` overriding token lifetime for that token type, and `mfaFactorUsed`, which can reject specific MFA factors at issuance. Each needs a different Descope home.
3. **Does it return `tenantId`?** A prehook returning `tenantId` **overrides Frontegg's default tenant resolution** — this is the documented way to do domain-based tenant assignment. Rebuild it deliberately as tenant self-provisioning domains or explicit Flow logic; it will not be obvious from the app code that tenant assignment was happening here.

Frontegg's docs warn against unwarmed AWS Lambda for prehooks because cold starts exceed the 5-second
budget. If the customer built around that constraint, note that Flow steps run in-platform and the
constraint disappears.

### Webhooks → Descope Audit Webhook and Connectors

Frontegg webhooks are per-environment, signed with an `x-webhook-secret` header verified as a JWT
against the dashboard secret, with `frontegg.*` event keys.

| Frontegg | Descope |
|---|---|
| Webhook endpoint + `x-webhook-secret` | Webhook / [HTTP Connector](https://docs.descope.com/connectors) + signature validation |
| `frontegg.user.*` (created, signedUp, deleted, activated, updated, authenticated, failedAuthentication, changedPassword, forgotPassword, invitedToTenant, removedFromTenant, enrolledMFA, disabledMFA) | Descope user / audit events |
| `frontegg.tenant.*` (created, deleted, updated, locked, unlocked) | Tenant events or app-side lifecycle sync |
| `frontegg.group.*` (created, deleted, updated, roles.updated, users.added, users.removed) | Group / role mapping events |
| `frontegg.scim.*` (user and group create/delete/update) | Descope SCIM provisioning events |
| Custom events (`POST /event/resources/triggers/v3`, `EventsClient`) | Application-owned events — not an identity concern |
| Static egress IP allowlist (published per region) | Confirm Descope's egress behavior with the customer's network team |

Two behaviors that change assumptions:

- **Frontegg never redelivers a failed event.** The retry mechanism operates on the *webhook*, not the delivery — the next triggering event is the retry. After five consecutive failures the webhook auto-disables and backs off up to about a week, then permanently disables. Applications built against this often carry reconciliation jobs that can be simplified once delivery is more reliable.
- **SCIM event payloads are shaped oddly.** For `frontegg.scim.*` events, `eventContext.userId` is the literal constant `"idp_provisioned"` and the real user lives at `body.user`. Any handler doing that unwrapping needs rewriting, not just repointing.

The live Frontegg docs also contain at least one typo'd event key (`ffrontegg.user.plan.unassigned`).
If a handler switches on that string, it has never fired — worth flagging.

### Security rules → Flow-based security

**Mechanism difference (read this first):** Frontegg's security rules are dashboard toggles layered
on the login box — nine built-in defenses, each with a configurable verdict, applied automatically
with no app code. Descope has **no single equivalent toggle**. You reproduce the behavior by adding
risk signals, fingerprinting, Flow conditions, and security Connectors to the Flow.

| Frontegg rule | Available verdicts | Descope approach |
|---|---|---|
| Bot detection | allow / challenge / block / lock | CAPTCHA or bot-detection Connector (Arkose, reCAPTCHA) as a Flow step |
| New device | allow / challenge | Fingerprinting + Flow condition on device recognition |
| Brute force protection | block / lock | Lockout policy + Flow conditions |
| Breached password | allow / challenge / block | Have I Been Pwned Connector in the password step |
| Impossible travel | allow / challenge / block | Risk signals + Flow condition |
| Suspicious IPs | allow / challenge / block / lock | IP reputation Connector (AbuseIPDB) + Flow branch |
| Stale users | allow / challenge / block | Application policy or a scheduled Management SDK job |
| Email credibility check | allow / block | Email-validation Connector at sign-up |
| Country restrictions | allow / block | Flow condition on geo signals |

Ask whether each enabled rule is monitoring-only or actually gates login. Rules set to "allow" are
telemetry and can be dropped or replaced with audit events; rules set to block or lock are production
security controls and need a real equivalent before cutover.

Frontegg also layers restrictions at five levels (environment domain, environment country,
account-level domain/IP/country, user-level domain/IP). Note two behavioral details when
reproducing them: domain restrictions apply at invite time and invite-link signup and **do not affect
existing users**, and country restrictions evaluate only at signup and login — already-authenticated
sessions are not re-evaluated. If the Descope equivalent evaluates more often, that is a behavior
change worth flagging rather than a silent improvement.

### SSO and SCIM

**SSO.** Frontegg SSO is configured per account, usually by the customer's own admin through the
self-service portal, supporting SAML 2.0 and OIDC with JIT provisioning on first login. Descope
configures SSO per tenant with the same capabilities, and the **SSO Setup Suite** preserves the
self-serve experience Frontegg customers' admins already expect. Existing connections can usually be
moved without making every admin reconfigure their IdP — see
[SSO migration](https://docs.descope.com/migrate/sso).

Treat **Frontegg-as-IdP** (`native-hosted`, `via-oidc`, `via-saml`) as a separate workstream: it maps
to Descope Federated Apps, and every downstream relying party needs new issuer, metadata, and client
credentials.

**SCIM.** Supports user and group create/update/deprovision and membership sync. Treat it as a
continuing pipeline, not a one-time import — enterprise directories keep pushing events after
cutover, so every connection must be re-pointed at Descope before go-live.

On the Descope side, SCIM is scoped to a **particular SSO configuration within** a tenant, not to the
tenant globally. The SSO Setup Suite generates the SCIM bearer token during configuration, but it is
not the only route — tokens can also be created manually in the Console (format
`Bearer __ProjectID__:<AccessKey>`), rotated from the tenant's SCIM Provisioning area, minted via the
SCIM Management API, or generated by a **"Create SCIM Access Key" Flow action**. That last option is
the practical one when re-pointing many tenants' SCIM connections programmatically during a
migration.

Role resolution order in Frontegg is worth capturing before migrating: a SCIM-created user gets the
environment default role, then the SSO connection's default role, then any SAML group-mapped roles at
first login. Reproduce that precedence deliberately in Descope rather than assuming a single source.
`managedBy` (`"frontegg" | "scim2" | "external"`) tells you which users are directory-managed — carry
it into a custom attribute so post-migration reconciliation can distinguish them.

### M2M: Frontegg tokens → Inbound Apps or Access Keys

Frontegg's M2M model is two dimensions crossed:

| | Client-credentials token | Access token |
|---|---|---|
| **User context** | `clientId` + secret exchanged for a bearer JWT; carries the user's roles on the active tenant; deleted with the user | Long-lived JWT used directly |
| **Tenant (account) context** | Same exchange; permissions from scopes granted at creation (`roleIds` required) | Long-lived JWT used directly |
| **Header** | `Authorization: Bearer` | **`X-API-KEY`** |

That header split is the detail most often missed. A service sending `X-API-KEY` does not start
working just because the token issuer changed — it needs a client-side change too.

**Default mapping** for scoped API access:

1. Create a **[Resource](https://docs.descope.com/resources)** per protected API with a scope catalog (its identifier becomes the token `aud`).
2. Register a **confidential [Inbound App](https://docs.descope.com/identity-federation/inbound-apps)** per M2M service.
3. Create a **[Policy](https://docs.descope.com/policies)** granting that client `client_credentials` access to the scopes it needs.

Use **[Access Keys](https://docs.descope.com/management/m2m-access-keys)** only when the service needs
a Descope-issued JWT without OAuth scope or audience enforcement — a simpler internal service-auth
pattern, and the natural target for Frontegg *user* tokens and personal tokens.

Other details to carry over: secrets are shown in plaintext exactly once at creation in both systems,
so plan the rotation window; Frontegg's 100-concurrent-refresh-token limit has no equivalent and can
be dropped; and client-credential expiry was a separate knob from the environment-wide JWT expiry, so
check both before setting Descope lifetimes.

Frontegg's access-token caps are worth surfacing during inventory: **10,000 per environment and 100
per tenant** by default. A customer near either ceiling has a token-sprawl problem, and the migration
is the moment to consolidate rather than recreate one Descope object per stale Frontegg token.

### Frontegg AI integrations → Descope Connections / Outbound Apps

Frontegg AI provides agent identity plus **managed third-party OAuth** to Atlassian, GitHub, Google
Workspace, HubSpot, Monday, Notion, and Slack, using the customer's own provider credentials with
per-action scope selection.

| Frontegg AI | Descope |
|---|---|
| Agent identity and credentials | Agentic Identity Hub agent identity |
| Agent acting with user context | Descope session + delegated access |
| Built-in tools (user context, tenants, entitlements) | Session claims + Management SDK reads |
| Managed third-party OAuth integrations | **Connections** (Agentic Identity Hub's token vault for agent/MCP workloads) — or **[Outbound Apps](https://docs.descope.com/identity-federation/outbound-apps)** for a non-agentic app |
| Slack "on behalf of user" vs. "app-to-app" | Connection/Outbound App user-scoped vs. tenant/app-scoped tokens |
| Per-action scope selection | Connection/Outbound App scope configuration |
| External clients calling your API on the agent's behalf | Resources (the MCP server) + Agentic Clients + Policies |

Descope has two objects that do the same job — broker and refresh third-party OAuth tokens — and
picking the right one matters: **Connections** is what Descope currently steers builders toward for
agent and MCP workloads, while **Outbound Apps** does the same thing but is positioned for traditional
(non-agentic) applications. Confirm which kind of app this is rather than defaulting to Outbound Apps
because it's the older, more familiar name.

**Stored third-party refresh tokens do not transfer.** Every user re-consents per integration after
cutover. Plan a re-consent path — usually the
[Outbound Applications Widget](https://docs.descope.com/widgets/users) plus an in-app prompt — rather
than a silent switch that quietly breaks agent actions.

**Frontegg exposes MCP in two places** — ask about both, because they map differently from the
managed OAuth integrations above. The Entitlements Agent can be deployed with an **MCP Server** that
exposes authorization tools over HTTP (`is-entitled-to-entity-action-tool`,
`entitlements-entities-tool`), and Frontegg's separate **AgentLink** product (self-hosted component:
**FrontMCP**) ships a hosted or self-hosted MCP gateway for SaaS-facing use cases — verify current
naming, Helm chart, and endpoint details against live docs before citing specifics, since this surface
is new and moves fast. Either maps to Descope's MCP server support — the MCP server itself is a
**Resource**, agents/clients that may call it register as what the docs call **Agentic Clients**
(Console: **Agentic Identity Hub → Clients**), and **Policies** govern
access — not to Outbound Apps or Connections. Flag for dedicated review.

Note that Frontegg's own docs are inconsistent on whether the MCP-enabled Entitlements Agent counts as
legacy: the general ReBAC setup guide describes the underlying PDP-container stack as superseded by
the newer SpiceDB/e10s engine, but the current AI-agent-authorization guide still uses this same
Entitlements Agent for MCP. Don't assert it's deprecated without checking the specific guide in use at
migration time — but if it turns out to be, that's usually an argument for migrating rather than a
loss.

### Management API mapping

| Operation | Frontegg | Descope |
|---|---|---|
| Authenticate as the vendor | `POST /auth/vendor` (clientId + API key) → short-lived JWT | Management Key sent directly |
| List tenants | `GET /resources/tenants/v2` | `management.tenant.loadAll()` |
| List users | `GET /resources/users/v3` (`_limit` max 200, `_offset`) | `management.user.search()` (Node; `SearchAll` / `search_all` in Go and Python) |
| Fuzzy user search | `GET /resources/users/v1/query/phrase` | `management.user.search()` (Node; `SearchAll` / `search_all` in Go and Python) with filters |
| Create user | `POST /resources/users/v2` (`expirationInSeconds` for guests) | `management.user.create()` / `createBatch()` |
| Roles / permissions config | `/api/identity/roles`, `/account-roles`, `/permissions` | `management.role.*`, `management.permission.*` |
| Tenant membership | `GET /resources/users/v2/me/tenants`, `/me/hierarchy` | `management.user.loadByUserId()` → user tenants |
| Audit export | `auditscontroller_exportcsv` and variants | Audit Webhook Connector / audit APIs |

**Host routing.** Management calls must hit the regional gateway — `api.frontegg.com` (EU, default),
`api.us.frontegg.com`, `api.au.frontegg.com`, `api.ca.frontegg.com` — while tenant-context calls go to
the environment subdomain or custom domain. With an environment token on a self-service route, add
`frontegg-user-id` and/or `frontegg-tenant-id` headers. Getting this wrong yields
`{"errors":["Failed to verify vendor JWT"]}` — which Frontegg's API overview attributes to misusing
API contexts or directing requests to the wrong gateway. It reads like a credential problem but is
not.

---

## Framework Recipes

> Verify every Descope method name and option shape against the Descope Docs MCP or local type
> declarations before generating code. These recipes name the Frontegg idioms that need mapping;
> they are not copy-paste implementations.

### Next.js

*`@frontegg/nextjs` → `@descope/nextjs-sdk` + `@descope/node-sdk`*

| Frontegg | Descope |
|---|---|
| `FronteggAppProvider` / `FronteggAppRouter` (`@frontegg/nextjs/app`) | `AuthProvider` with `NEXT_PUBLIC_DESCOPE_PROJECT_ID` |
| `withFronteggApp` / `FronteggRouter` (`@frontegg/nextjs/pages`) | `AuthProvider` + `session()` for server reads |
| `getAppUserSession()` / `getAppUserTokens()` / `getSession` / `withSSRSession` | `session()` from `@descope/nextjs-sdk/server` |
| `FronteggApiMiddleware` (`/middleware`) / `handleSessionOnEdge` (`/edge`) | `authMiddleware(options)` |
| `FRONTEGG_ENCRYPTION_PASSWORD` + `FRONTEGG_COOKIE_NAME` (`fe_session`) | Removed — Descope manages `DS`/`DSR` |
| `FRONTEGG_HOSTED_LOGIN` toggle | A one-time Console decision, not a per-request flag |
| `FRONTEGG_JWT_PUBLIC_KEY` (inlined JWK) | Removed — SDK validation or JWKS |

`session()` is server-only; `useSession()` / `useUser()` from `@descope/nextjs-sdk/client` are
client-only. Mixing them compiles and throws at runtime.

**Next.js 15:** `cookies()` and `headers()` from `next/headers` return a `Promise`. Check
`package.json` first, then `await` them and mark the containing function `async` — and trace every
caller, because the cascade routinely spans 10–20 files.

Frontegg's Next.js SDK requires SSR and does not support SSG. If the app was structured around that
constraint, re-evaluate after migration rather than preserving it by default.

### React

*`@frontegg/react` → `@descope/react-sdk`*

| Frontegg | Descope |
|---|---|
| `<FronteggProvider contextOptions={{ baseUrl, clientId, appId }}>` | `<AuthProvider projectId>` |
| `useLoginWithRedirect()` (hosted) | Redirect to Descope Auth Hosting |
| Injected `/account/login` routes (embedded) | `<Descope flowId="sign-up-or-in" onSuccess={...}>` |
| `useAuth()` / `useAuthUser()` / `useAuthUserOrNull()` | `useSession()` + `useUser()` |
| `useIsAuthenticated()` | `useSession()` authentication state |
| `useAuthActions()` → `requestAuthorize`, `switchTenant`, `loadEntitlements` | `useDescope()` actions; tenant selection for `switchTenant`; `loadEntitlements` has no equivalent |
| `useTenantsActions().loadTenants()` / `useAuth().tenantsState` | Read membership from the validated session (`tenants`) |
| `ContextHolder.for().getContext()` | Descope SDK session accessors — do **not** hand-parse the token |
| `AdminPortal.show()` / `.openHosted()` | Descope Widgets — see `flows-and-widgets.md` |
| `useFeatureEntitlements()` / `usePermissionEntitlements()` | Roles/permissions where it is access control; otherwise out of scope |

**Always read auth state through the hooks.** `ContextHolder` makes the raw token easy to reach in
Frontegg apps, and that habit should not carry over. Never call backend `validateSession()` from
client code.

Note the React-vs-others API difference in Frontegg: `ContextHolder.for().getContext()` in React,
`ContextHolder.getContext()` in Vue and Angular. Both become the same Descope pattern.

### Node.js backend

*`@frontegg/client` → `@descope/node-sdk`*

| Frontegg | Descope |
|---|---|
| `FronteggContext.init({ FRONTEGG_CLIENT_ID, FRONTEGG_API_KEY }, { accessTokensOptions })` | `DescopeClient({ projectId, managementKey })` |
| `withAuthentication()` (populates `req.frontegg.user`) | Custom middleware: read `DS` cookie → `descopeClient.validateSession(token)` → attach claims |
| `new IdentityClient({...})` + `validateIdentityOnToken(token, { roles, permissions })` | `validateSession()` + role/permission validation helpers |
| `FronteggAuthenticator` / `HttpClient` | Not needed |
| `AuditsClient` / `EventsClient` | Audit events and Connectors |
| Access-token cache (`local` / `redis` / `ioredis`) | Removed |

Express does not parse cookies by default — add `cookie-parser` before reading `DS`.

### Python backend

*`frontegg` → `descope`*

**Flask:** `frontegg.init_app(client_id, api_key)` plus
`@with_authentication(role_keys=[...], permission_keys=[...])` (user on `g.user`) becomes a Descope
client plus a decorator calling
`descope_client.validate_session(session_token=session_token)`.

**FastAPI:** `await frontegg.init_app(...)` plus
`Depends(FronteggSecurity(permissions=['my-permission']))` becomes a Descope dependency that reads
the `DS` cookie or `Authorization` header, validates, and checks permissions. Descope documents a
[JWT authorizer pattern](https://docs.descope.com/sessions/validation/jwt-authorizers/python-fastapi-jwt-authorizer)
for this.

`FRONTEGG_DEBUG` / `frontegg_logger` become the Descope SDK's own logging.

### Go backend

*`github.com/frontegg/go-sdk` → `github.com/descope/go-sdk`*

| Frontegg | Descope |
|---|---|
| `frontegg.Init(frontegg.Credentials{ClientID, APIKey})` / `frontegg.New(...)` | `client.New()` / `client.NewWithConfig(&client.Config{ProjectID: ...})` with the Project ID |
| `frontegg.WithAuthentication(middleware.Options{Roles, Permissions})` | Custom middleware calling `descopeClient.Auth.ValidateSessionWithToken(ctx, token)` → `(bool, *descope.Token, error)` |
| `middleware.UserFromContext(ctx)` | Claims off the returned `*descope.Token` |
| `ident.ValidateToken(ctx, token, &identity.ValidateTokenOptions{...}, identity.JWTHeader \| identity.AccessTokenHeader)` | `ValidateSessionWithToken` + role/permission helpers |
| `client.HostedLogin(redirectURI)` → `RequestAuthorize` / `CodeExchange` | Descope hosted flow or SDK login |
| `identity.ErrInsufficientRole` / `ErrInsufficientPermission` / `ErrFailedToAuthenticate` | Descope SDK errors — remap error handling explicitly |
| Frontegg `tenantId` | Tenant ID for management calls; `token.GetTenants()` or `dct` at request time |

**Roles and Permissions are OR in Frontegg** (at least one must match). Verify the Descope helper's
semantics rather than assuming parity.

**Split-origin (separate SPA + API) gotcha.** When the frontend and backend are different origins and
the backend SDK sets the session cookies, browsers often drop them silently, producing "no valid
session found" on the first authenticated request for every user. The Go SDK's `createCookie` emits
`Secure: true` (hardcoded) with `SameSite` defaulting to Strict, and only sets `DS` when
`SessionJWTViaCookie` is enabled. Over plain HTTP — and especially when login arrives via a
cross-site redirect — those cookies are withheld. The fix is to manage `DS`/`DSR` yourself:

```go
// Pass nil ResponseWriter so the SDK does NOT set its own (Strict/Secure) cookies;
// take the tokens off the returned AuthenticationInfo and set your own.
authInfo, err := descopeClient.Auth.OAuth().ExchangeToken(ctx, code, nil)
// set DS = authInfo.SessionToken.JWT and DSR = authInfo.RefreshToken.JWT with:
//   Path:"/", HttpOnly:true, SameSite: http.SameSiteLaxMode, Secure:false (HTTP localhost), no Domain
// Validation still works via ValidateSessionWithRequest(r) (it reads DS/DSR by name).
// Logout: LogoutWithToken(<DSR>, nil) then expire the DS/DSR cookies (MaxAge -1).
```

Use `descope.SessionCookieName` (`DS`) and `descope.RefreshCookieName` (`DSR`) so the SDK's
request-based validators find them. In production behind HTTPS, set `Secure=true`.

**Don't double-write the HTTP response.** Calling `w.WriteHeader(...)` and then a JSON responder that
also writes a status produces `http: superfluous response.WriteHeader call`. For SDK methods that
write a redirect to the `ResponseWriter`, on error just log — don't emit a second body.

### Java and .NET (no Frontegg SDK)

Frontegg publishes **no general-purpose Java SDK** (only `com.frontegg.sdk:entitlements-client*`,
which is entitlements/gRPC only) and **no .NET SDK at all**. These apps already hand-roll JWT
verification, which usually makes them the smallest migrations in a multi-service estate.

**.NET** typically configures:

```csharp
options.Authority = "https://[YOUR-FRONTEGG-DOMAIN].frontegg.com";
options.Audience  = "[my-client-id]";
options.TokenValidationParameters.NameClaimType = ClaimTypes.NameIdentifier;
// role checks read the "roles" claim type
```

Replace with `descope-dotnet` session validation, or repoint the JWT bearer configuration at
Descope's issuer and JWKS. Either way the **claim reads change even though the mechanism doesn't**:
no `email`/`name` by default, `dct`/`tenants` instead of `tenantId`/`tenantIds`, and **no `aud`
unless you configure one** — which silently disables an audience check that used to run.

**Java** apps use Spring Security resource-server config, a servlet filter, or direct `jwt.verify`
against the Frontegg public key. Replace with
`authenticationService.validateSessionWithToken(sessionToken)` returning a `Token`. If
`entitlements-client-spring-boot-starter` and `ENTITLEMENTS_ENGINE_TOKEN` are present, the app is
using the self-hosted entitlements engine — handle that under ReBAC, not here.

**Also check for API gateways.** Frontegg documents a Kong pattern using an RS256 JWT credential with
`key = https://{workspace-url}.frontegg.com/` — the `iss` value, **including the trailing slash**.
Gateway-level validation is easy to miss because it lives outside the application repo entirely.

### Mobile

All Frontegg mobile SDKs require **hosted** login, default `keepSessionAlive` to `true`, and do not
support the self-service portal, entitlements, impersonation, or idle-session management. Mobile
migrations are therefore narrower than their web counterparts.

| Platform | Frontegg | Descope |
|---|---|---|
| iOS | `FronteggSwift`, `Frontegg.plist` (`baseUrl`, `clientId`, `applicationId`, `embeddedMode`, `regions`), `FronteggApp.shared.auth`, `AbstractFronteggController` | [`descope-swift`](https://github.com/descope/swift-sdk) — run a Descope Flow |
| Android | `com.frontegg.sdk:android`, `FRONTEGG_DOMAIN` / `FRONTEGG_CLIENT_ID` / `FRONTEGG_APPLICATION_ID` buildConfigFields, `EmbeddedAuthActivity` / `HostedAuthActivity` | [`descope-kotlin`](https://github.com/descope/descope-kotlin) |
| React Native | `@frontegg/react-native` | [`@descope/react-native-sdk`](https://github.com/descope/descope-react-native) |
| Flutter | `frontegg_flutter`, `FronteggProvider`, `FronteggState` | [`descope-flutter`](https://github.com/descope/descope-flutter) |

**Callback URLs and deep links must be re-registered**, and this is the part that breaks silently in
QA rather than at compile time:

- iOS: `{{IOS_BUNDLE_IDENTIFIER}}://{{FRONTEGG_BASE_URL}}/ios/oauth/callback`
- Android: `{{ANDROID_PACKAGE_NAME}}://{{FRONTEGG_BASE_URL}}/android/oauth/callback`, plus `https://{{FRONTEGG_BASE_URL}}/oauth/account/redirect/android/{{ANDROID_PACKAGE_NAME}}`
- Android deep-link path prefixes: `/oauth/account/activate`, `/oauth/account/invitation/accept`, `/oauth/account/reset-password`, `/oauth/account/login/magic-link`

Associated domains registered via Frontegg's admin endpoints
(`/vendors/resources/associated-domains/v1/ios` and `/android`) also need Descope equivalents.

---

## Common Gotchas

### Cookie names: `DS` and `DSR`

Descope web components and client SDKs default to `DS` for the session JWT and `DSR` for the refresh
JWT. The [Node SDK](https://github.com/descope/node-sdk#session-validation-using-middleware) exposes
`DescopeClient.SessionTokenCookieName` and `DescopeClient.RefreshTokenCookieName`.

These names are configurable via the
[End action](https://docs.descope.com/flows/actions/end-action#session-cookie-name) in Flows — useful
when running multiple Descope projects on one root domain. Backend code must then read the custom
names.

The Frontegg side to clear out: **`fe_refresh`** (the refresh cookie in both hosted and embedded
modes) and **`fe_session`** (the Next.js stateless session cookie, named by `FRONTEGG_COOKIE_NAME`
and encrypted with `FRONTEGG_ENCRYPTION_PASSWORD`). Grep for both by name — code that clears them on
logout will otherwise silently keep clearing cookies that no longer exist.

**Third-party cookies.** Many Frontegg deployments added a custom domain specifically because
`/user/token/refresh` failed with 401s under third-party-cookie restrictions. If the app has a
Frontegg custom domain, find out whether it exists for branding or for cookie reasons — the answer
decides whether a Descope custom domain is a nice-to-have or a launch blocker.

### Audience validation requires explicit setup

Frontegg tokens carry `aud` (the client ID or app ID) by default, and backends validate it —
especially .NET apps using `AddJwtBearer` with `options.Audience`. Descope session tokens have **no
`aud` by default**. Apps relying on audience validation must configure a custom `aud` claim in a JWT
Template *and* pass `audience` to `validateSession()`. Otherwise validation either fails outright or,
worse, silently stops checking something it used to check.

### Logout requires two steps

1. `descopeClient.logout(refreshToken)` — invalidates server-side
2. Clear the `DS` and `DSR` cookies

Skipping either leaves a broken state. Remember that Frontegg's **hosted** logout was a navigation to
`{baseUrl}/oauth/logout?post_logout_redirect_uri=…`, so hosted-login apps may have no logout code to
find — just an anchor tag. Search the markup, not only the JavaScript.

### Env var reduction

A typical Frontegg app carries 6–12 Frontegg environment variables plus hardcoded `contextOptions`
values; the Descope equivalent is 2–3. Removals: `FRONTEGG_CLIENT_ID`, `FRONTEGG_API_KEY`,
`FRONTEGG_BASE_URL`, `FRONTEGG_APP_URL`, `FRONTEGG_APP_ID`, `FRONTEGG_COOKIE_NAME`,
`FRONTEGG_ENCRYPTION_PASSWORD`, `FRONTEGG_HOSTED_LOGIN`, `FRONTEGG_JWT_PUBLIC_KEY`,
`FRONTEGG_LOG_LEVEL`, every `FRONTEGG_*_SERVICE_URL`, `FRONTEGG_API_GATEWAY_URL`,
`DISABLE_INITIAL_PROPS_REFRESH_TOKEN`, and `ENTITLEMENTS_ENGINE_TOKEN`. Additions:
`DESCOPE_PROJECT_ID`, its `NEXT_PUBLIC_` twin where a browser needs it, and
`DESCOPE_MANAGEMENT_KEY` for server-side administration.

**Watch for hardcoded config.** React, Vue, Angular, and Vanilla JS quickstarts put `baseUrl`,
`clientId`, and `appId` inline in `contextOptions` rather than in env vars, and `VITE_FRONTEGG_*` /
`NEXT_PUBLIC_FRONTEGG_*` are community conventions rather than documented ones. An env-var grep
returning nothing does **not** mean Frontegg is unused — grep for `contextOptions` and
`FronteggProvider` too. Also check `Frontegg.plist`, Android `buildConfigField`s, Docker files, and
CI config, none of which break the build when left behind.

### Approved Domains: domain only

Frontegg registers full callback URLs (`http://localhost:3000/oauth/callback`) and allowed origins
with wildcard support (`https://*.acme.com`, propagating for up to two minutes). Descope uses
**Approved Domains** (Console → Project Settings → Security): domain only, no protocol, no path.

- Local dev: `localhost:3000` (include the port)
- Production: `myapp.com` or `app.myapp.com`

Do not carry over Frontegg callback URLs — embedded Descope Flows complete auth client-side, so there
is no `/oauth/callback` route to whitelist. Decide explicitly how any wildcard origin should be
represented rather than assuming a one-to-one copy.

### Testing checklist

Applies to every migration, in addition to the framework-specific checks:

- Zero `frontegg` hits in a case-insensitive repo-wide grep — including `.env*`, CI config, `build.gradle`, `Frontegg.plist`, and Docker files
- Compile passes with zero errors; no residual async-cascade gaps
- Unauthenticated protected routes return 302 or 401, not 500
- Login completes and profile data renders — proving the JWT Template is applied
- Decoded `DS` token contains `dct` and `tenants` matching what the app used to read from `tenantId` / `tenantIds`
- Tenant switching still lands the user in the right tenant context
- Logout invalidates server-side **and** clears `DS` / `DSR`
- If dual-token validation is in place: both a Descope token and a Frontegg token are accepted, and the Frontegg branch is tracked for removal
- If SCIM is in use: a provisioning event from the real IdP reaches Descope
- If M2M is in use: every client authenticates with the correct header, and downstream services still enforce `scope` and `aud`
- If ReBAC was in use: the self-hosted entitlements stack is decommissioned, not merely unused
