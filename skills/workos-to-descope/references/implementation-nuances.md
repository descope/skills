# Descope Migration: Implementation Notes

## Contents

**General Insights — Architecture & Flow**
- [AuthKit owns the flow; Descope validates tokens](#authkit-owns-the-flow-descope-validates-tokens)
- [OIDC compatibility path](#oidc-compatibility-path-alternative-to-full-migration)
- [No drop-in middleware for Express or Flask](#no-drop-in-middleware-for-express-or-flask)
- [Fewer network round-trips at login](#fewer-network-round-trips-at-login)
- [WorkOS vs Descope flow comparison](#workos-vs-descope-flow-comparison)

**General Insights — Feature Mapping: WorkOS → Descope**
- [Social login / connection mapping + SSO URLs](#social-login--connection-mapping)
- [RBAC: WorkOS → Descope](#rbac-workos--descope)
- [Multi-tenancy: WorkOS Organizations → Descope Tenants](#multi-tenancy-workos-organizations--descope-tenants)
- [Invitation model](#invitation-model-workos-invitations--descope-userinvite)
- [MFA enrollment and factor management](#mfa-enrollment-and-factor-management)
- [Directory Sync / SCIM: a lifecycle, not an import](#directory-sync--scim-a-lifecycle-not-an-import)
- [Session refresh after profile changes + sdk.refresh()](#session-refresh-after-profile-changes)
- [Management API mapping](#management-api-mapping)
- [FGA: WorkOS FGA (warrants) → Descope ReBAC](#fga-workos-fga-warrants--descope-rebac)
- [Pipes → Descope Outbound Apps](#pipes--descope-outbound-apps)
- [User migration: WorkOS export → Descope import](#user-migration-workos-export--descope-import)
- [M2M: WorkOS API keys → Descope Access Keys](#m2m-authentication-workos-api-keys--descope-access-keys)
- [Email templates](#email-templates-workos--descope-messaging-templates)
- [Webhooks / Audit Logs → Descope Audit Webhook](#webhooks--audit-logs-workos--descope-audit-webhook)
- [Custom domains](#custom-domains)
- [Radar → Descope Flow-based security](#radar--descope-flow-based-security)
- [Admin Portal → SSO Setup Suite / Widgets](#admin-portal--sso-setup-suite--widgets)
- [Testing checklist](#testing-checklist-applies-to-all-samples)

**General Insights — Common Gotchas**
- [Cookie names: DS and DSR](#cookie-names-ds-and-dsr-configurable)
- [User claims differ (dct, tenants, email not default)](#user-claims-differ)
- [Audience validation requires explicit setup](#audience-validation-requires-explicit-setup)
- [Sealed sessions become signed JWTs; one session token](#sealed-sessions-become-signed-jwts)
- [Logout requires two steps](#logout-requires-two-steps)
- [One env var instead of four](#one-env-var-instead-of-four)
- [WorkOS has no imperative actions → Flows + JWT Templates](#workos-has-no-imperative-actions--descope-flows--jwt-templates)
- [Public routes need manual replication](#public-routes-need-manual-replication)

**Framework Sections**
- [Express.js](#expressjs)
- [Flask / Python](#flask--python)
- [Next.js (standalone)](#nextjs-standalone)
- [Next.js (B2B): Migration Bug Catalog](#nextjs-b2b-migration-bug-catalog)
- [Next.js (with separate Express API server)](#nextjs-with-separate-express-api-server)
- [Go](#go)

> **See also:** `flows-and-widgets.md` in this directory — WorkOS→Descope lingo map, Flow structure and templates, Widget types, SSO Setup Suite, and the Console-vs-code decision guide. Read it before migrating any auth UI, MFA enrollment, user management pages, or SSO configuration.

---

## General Insights

**— Architecture & Flow —**

### AuthKit owns the flow; Descope validates tokens

WorkOS [AuthKit](https://workos.com/docs/authkit) and its framework SDKs ([authkit-nextjs](https://github.com/workos/authkit-nextjs), [authkit-js](https://github.com/workos/authkit-js), [authkit-react](https://github.com/workos/authkit-react)) own the login flow: AuthKit hosts (or embeds) the login UI, handles the redirect/callback code exchange, seals a server-managed session into an encrypted cookie, and provides middleware (`authkitMiddleware()`) and helpers (`withAuth()` / `getUser()`) that gate routes. Backend-SDK apps do the same work explicitly via `workos.userManagement.authenticateWithCode(...)` and `workos.userManagement.loadSealedSession(...)`. Developers never validate tokens themselves; the sealed cookie is unsealed with `WORKOS_COOKIE_PASSWORD`.

Descope splits the work. The frontend ([Descope Flows](https://docs.descope.com/flows) via [web components](https://docs.descope.com/client-sdk/descope-components) or [client SDKs](https://docs.descope.com/client-sdk/initialize-sdk)) runs the authentication ceremony and stores JWTs in `DS` (session) and `DSR` (refresh) cookies. The backend [validates those JWTs](https://docs.descope.com/authorization/session-management/session-validation/backend). No server-side OAuth callback, no authorization code exchange, no sealed server-managed session.

Every WorkOS→Descope migration adds a dedicated login page (or embeds the [`<descope-wc>` component](https://docs.descope.com/client-sdk/descope-components#descope-component)) and removes the AuthKit callback/redirect plumbing.

**Exception:** Descope can also act as a [standard OIDC provider](https://docs.descope.com/getting-started/oidc-endpoints). If the app authenticates through a **generic OIDC client** pointed at WorkOS's hosted AuthKit page, you can point that client at Descope's OIDC endpoints instead. See the "OIDC compatibility path" section below.

### OIDC compatibility path (alternative to full migration)

Descope exposes standard [OIDC endpoints](https://docs.descope.com/getting-started/oidc-endpoints):

| Endpoint | URL |
|---|---|
| Authorization | `https://api.descope.com/oauth2/v1/authorize` |
| Token | `https://api.descope.com/oauth2/v1/token` |
| UserInfo | `https://api.descope.com/oauth2/v1/userinfo` |
| JWKS | `https://api.descope.com/__ProjectID__/.well-known/jwks.json` |
| End Session | `https://api.descope.com/oauth2/v1/logout` |
| Revocation | `https://api.descope.com/oauth2/v1/revoke` |

**First classify the current integration — these endpoints only matter for the hosted-page case.** An app that uses a **generic OIDC/OAuth client library** redirected to a WorkOS-hosted AuthKit login URL can swap the issuer to `https://api.descope.com` and keep the existing client code largely intact. An app that uses **embedded AuthKit or the WorkOS SDKs directly** (`withAuth()`, AuthKit components, `userManagement.*`) cannot — that's a full migration to Descope-native SDKs + Flows.

Even for the hosted-page case, differences in claim shapes (`email_verified` vs `verifiedEmail`), token lifetimes, and configuration semantics mean the OIDC swap still requires testing and adjustments — and organization-scoped login, SSO, and SCIM must be rebuilt regardless of path. Still, it's a viable incremental step for the generic-client case: swap the IdP first, then refactor to Descope-native SDKs later. For B2B apps the savings are minimal, because management calls, org/tenant-scoped login, SSO/SCIM, and claim mapping all require full migration anyway.

**— Common Gotchas —**

### No drop-in middleware for Express or Flask

WorkOS's framework SDKs offer drop-in helpers — `authkit-nextjs` exposes `authkitMiddleware()`, and AuthKit-JS apps get `withAuth()` / `getUser()` that read and unseal the session cookie for you. Descope has no equivalent Express middleware package. You:

1. Add `cookie-parser` (Express doesn't parse cookies by default; AuthKit's helpers handled it internally).
2. Write custom middleware: read `DS` cookie → call [`descopeClient.validateSession()`](https://docs.descope.com/authorization/session-management/session-validation/backend#validate-session) → attach user claims to `req`.
3. Write your own `requiresAuth()` guard (3 lines, but manual).

The [Descope blog](https://www.descope.com/blog/post/authentication-middleware) shows an Express middleware pattern, but it's a tutorial example, not a published package.

Flask is the same story. WorkOS's [Python SDK](https://github.com/workos/workos-python) provides `userManagement` helpers for the code exchange and sealed-session access. Descope's Flask backend [validates tokens](https://docs.descope.com/getting-started/python) only; auth UI is client-side.

FastAPI follows the same pattern. The Descope approach is a [custom JWT authorizer using JWKS validation](https://docs.descope.com/authorization/session-management/session-validation/oidc-jwt-authorizers/python-fastapi-jwt-authorizer): a `TokenVerifier` class that reads the `Authorization` header, validates against Descope's JWKS, and attaches as a FastAPI `Security()` dependency. No auto-mounted routes, no sealed session store.

### Cookie names: `DS` and `DSR` (configurable)

Descope web components and client SDKs default to `DS` for the session JWT and `DSR` for the refresh JWT. The [Node SDK README](https://github.com/descope/node-sdk#session-validation-using-middleware) references `DescopeClient.SessionTokenCookieName` and `DescopeClient.RefreshTokenCookieName` as constants.

These names are configurable. The [End action in Descope Flows](https://docs.descope.com/flows/actions/end-action#session-cookie-name) has "Session Cookie Name" and "Refresh Cookie Name" fields that override the defaults. Use custom names when running multiple Descope projects on the same root domain to avoid cookie collisions. Backend code must then read the custom cookie name instead of `DS`/`DSR`.

The `sessionTokenViaCookie` parameter in [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#cookie-configuration-options) controls whether the session token is set as a cookie at all (vs. managed in-memory by the SDK).

### User claims differ

The default Descope session JWT ([structure ref](https://docs.descope.com/authorization/session-management#descope-session-jwt-structure)) contains `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions`, and `dct`. It does **not** include `email`, `name`, or `picture` unless you add them via [JWT Templates](https://docs.descope.com/management/jwt-templates) or [Flow actions > Custom Claims](https://docs.descope.com/flows/actions/custom-claims). WorkOS AuthKit's session may expose some profile fields directly, so code that reads them from the session will break after migration.

| Field | WorkOS | Descope |
|---|---|---|
| User ID | `user.id` (e.g., `user_01H...`) | `sub` in JWT, `userId` in SDK user objects |
| Display name | `user.firstName` / `user.lastName` | Not in JWT by default. Add via [JWT Templates](https://docs.descope.com/management/jwt-templates). |
| Email | `user.email` (on the AuthKit session) | Not in JWT by default. Add via JWT Templates. Available on user object via SDK management calls. |
| Profile picture | `user.profilePictureUrl` | Not in JWT by default. Add via JWT Templates. |
| Email verified | `user.emailVerified` | Not in JWT by default. Available on user object as `verifiedEmail`. Add to JWT via Custom Claims if needed. |
| Roles | `role` / `roleSlug` (organization membership role) | `roles` array in JWT (embedded by default with [RBAC](https://docs.descope.com/authorization/role-based-access-control)) |
| Permissions | `permissions` array (RBAC) | `permissions` array in JWT (embedded by default) |
| Tenant ID | `organizationId` (flat string, from `withAuth()`) | `dct` — flat string with active tenant ID, direct `organizationId` equivalent; `tenants` — object keyed by tenant ID containing per-tenant `roles` and `permissions`. Use `dct` when you only need the ID; use `tenants` when you need per-tenant roles ([ref](https://docs.descope.com/authorization/role-based-access-control#tenants-and-roles)) |

**Migration action item:** Before migrating, configure a JWT Template that includes `email`, `name`, and any other profile claims your app reads from the token. Without this, code that reads `token.email` or `token.name` after `validateSession()` will get `undefined`.

### Audience validation requires explicit setup

WorkOS access tokens carry the `aud`/client context tied to the AuthKit client. If the API server validates an audience today (via `express-jwt`, JWKS, etc.), you must replicate it.

Descope session tokens don't include an `aud` claim by default. To add audience validation:
1. Configure a custom `aud` claim in the Descope Console's [JWT Templates](https://docs.descope.com/management/jwt-templates).
2. Pass the `audience` parameter to [`validateSession()`](https://docs.descope.com/getting-started/nodejs#implement-session-validation) on the backend.

This is easy to miss during migration. Without it, any valid Descope session token from any project would pass validation. The audience check prevents cross-project token reuse.

### Sealed sessions become signed JWTs

WorkOS AuthKit uses an **encrypted/sealed** session cookie protected by `WORKOS_COOKIE_PASSWORD`. Code unseals it (`loadSealedSession()`, `withAuth()`) to read the user, and the access token is distinct from the sealed session.

Descope has one token: the signed session JWT (`DS` cookie), readable but verified by signature. The sealing password is gone. Any code that unseals or inspects the WorkOS cookie is replaced with `descopeClient.validateSession()`, which returns decoded JWT claims. When calling a backend API, forward the `DS` cookie value as `Authorization: Bearer <DS>`; the API server validates it with `descopeClient.validateSession(token)`. No separate access-token endpoint, no provider-specific token issuance. If you need audience differentiation, use [JWT Templates](https://docs.descope.com/management/jwt-templates).

### Logout requires two steps

WorkOS logout clears the sealed AuthKit session (and optionally redirects through a WorkOS logout URL).

Descope logout ([backend](https://docs.descope.com/authorization/session-management/session-validation/backend#logout-current-session-using-backend-sdk) / [client](https://docs.descope.com/client-sdk/auth-helpers#logout)):
1. Call `descopeClient.logout(refreshToken)` (server-side) or `sdk.logout()` (client-side) to invalidate the refresh token.
2. Clear the `DS` and `DSR` cookies.

Clear cookies without calling logout → the refresh token stays valid on Descope's servers. Call logout without clearing cookies → the client holds a dead session token that fails validation but confuses client-side state.

### One env var instead of four

WorkOS needs `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_REDIRECT_URI`, and `WORKOS_COOKIE_PASSWORD` (4+).

Descope needs `DESCOPE_PROJECT_ID` (or `NEXT_PUBLIC_DESCOPE_PROJECT_ID` for Next.js client-side). No client secret for frontend flows, and no cookie-sealing password. The web component authenticates against Descope's API using the project ID. Backend SDKs [fetch the public key](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation#finding-your-public-key) from Descope's JWKS endpoint (`https://api.descope.com/v2/keys/<project_id>`) using the same project ID. No secrets to rotate for the auth flow.

For management operations (user CRUD, role management, FGA), add `DESCOPE_MANAGEMENT_KEY`.

### WorkOS has no imperative actions → Descope Flows + JWT Templates

WorkOS does not run arbitrary developer code mid-authentication. Auth behavior is configured in the AuthKit dashboard (enabled methods, branding, Radar, RBAC) and read back through the session.

Descope's customization model:
- **Custom claims:** [JWT Templates](https://docs.descope.com/management/jwt-templates) to add static/dynamic claims to tokens, or [Flow actions > Custom Claims](https://docs.descope.com/flows/actions/custom-claims) for claims set during the auth flow.
- **Custom logic during auth:** [Descope Flows](https://docs.descope.com/flows) are visual, drag-and-drop pipelines. Conditional branching, connectors to external services, and custom JS actions run auth-time business logic on Descope's servers.
- **Webhook-style hooks:** Descope Flows can call external HTTP endpoints ([Connectors](https://docs.descope.com/customize/connectors)).

Where a WorkOS app encodes post-login business logic in application code that runs after `withAuth()`, decide whether it belongs in a Flow (auth-time) or stays in app code (post-validation). Logic that *must* happen before a session is issued moves into the Flow.

### Public routes need manual replication

`authkitMiddleware()` can be configured with unauthenticated/public paths so anonymous users browse freely while protected paths require a session. Descope equivalent: your session middleware catches validation errors and sets `req.isAuthenticated = false` (or skips the redirect) for public routes instead of returning 401.

**— Feature Mapping: WorkOS → Descope —**

### Social login / connection mapping

WorkOS social providers (Google, Microsoft, GitHub, etc.) are enabled in the WorkOS dashboard / AuthKit and appear automatically on the AuthKit login page.

Descope equivalent: configure [social auth methods](https://docs.descope.com/authentication/social) in the Descope Console, then add them to a [Flow](https://docs.descope.com/flows). The Descope web component renders the configured providers. No code changes needed; configuration only.

WorkOS enterprise SSO connections (SAML/OIDC, per Organization) map to Descope's [SSO configuration](https://docs.descope.com/sso) (per-tenant SSO for B2B). A WorkOS Organization's connection maps to that tenant's SSO configuration.

**SSO Setup Suite:** For apps that expose a self-service SSO settings page where tenant admins configure their IdP, the SSO Setup Suite (Console wizard) can replace `management.ssoApplication.*` calls entirely — tenant admins configure their own IdP through a guided wizard with no engineering involvement. Surface this before migrating any Management SDK SSO code. See `flows-and-widgets.md` → SSO Setup Suite.

**Runtime SSO login — always use `sso.start` / `sso.exchange`.** When code initiates an enterprise SSO login (the equivalent of WorkOS's `sso.getAuthorizationUrl()` + `sso.getProfileAndToken()`), call the Descope SDK's `sso.start(tenant, redirectUrl, ...)` and `sso.exchange(code)`. Use these **regardless of the IdP's underlying protocol** — `sso.start` resolves the tenant-level SSO configuration (correct IdP, domain-based routing, connection settings). Do **not** use the generic `oauth.start` / `oauth.exchange` for enterprise SSO; those drive project-level social/OAuth providers. Rule of thumb: tenant/enterprise SSO → `sso.*`; social or generic OAuth login → `oauth.*`.

**Don't rebuild per-provider SSO UI.** In Descope the IdP is defined as **tenant SSO configuration**, and a single `sso.start` call resolves it from the user's email domain or an explicit tenant ID/slug. Keep the login surface generic (collect an email or target a known tenant) and push provider-specific details into Console/tenant configuration — don't migrate separate "Sign in with Okta" / "Sign in with Azure AD" buttons.

**SSO callback and ACS URLs:**
- Social OAuth callback (Google, GitHub, etc.): `https://api.descope.com/v1/oauth/callback`
- SAML ACS URL (per-tenant enterprise SSO): found in Console → SSO → [tenant] → SP Settings — tenant-specific, not a global hardcoded URL
- OIDC authorization server endpoints (Descope acting as IdP): `/oauth2/v1/authorize`, `/oauth2/v1/token` — already in the OIDC compatibility table above

`https://api.descope.com/oauth2/v1/callback` does not exist — do not use it as a callback URL when configuring an IdP.

### RBAC: WorkOS → Descope

WorkOS roles come in two scopes: **environment-level roles** (available across all organizations) and **organization-scoped "custom roles"**. Permissions group under roles, and roles/permissions surface on the AuthKit session.

Descope RBAC ([docs](https://docs.descope.com/authorization/role-based-access-control)): same concept, with two matching scopes — project-level and tenant-level. Roles/permissions are embedded in the JWT by default (no extra step). SDK methods:
- `descopeClient.management.permission.create(name, description)` ([ref](https://docs.descope.com/authorization/role-based-access-control/with-sdks))
- `descopeClient.management.role.create(name, description, permissionNames, tenantId)` ([ref](https://docs.descope.com/authorization/role-based-access-control/with-sdks)) — pass `tenantId` for a **tenant-level** role (≈ WorkOS organization-scoped/custom role); omit it for a **project-level** role (≈ WorkOS environment-level role).

| WorkOS | Descope |
|---|---|
| `role` | `role` |
| `permission` | `permission` |
| Environment-level role | Project-level role |
| Organization-scoped role ("custom role") | Tenant-scoped role |
| `roleSlug` reference | Descope role **name** (not ID) |
| IdP group → role mapping | Group-to-role mapping (SSO Configuration / SCIM) |

Roles must exist in the Console before assignment. Backend code checking WorkOS's `permissions.includes('read:messages')` changes to reading the `permissions` array from Descope's validated JWT claims — ideally via `validateTenantRoles(authInfo, tenantId, [...])` rather than parsing claims by hand.

### Multi-tenancy: WorkOS Organizations → Descope Tenants

WorkOS [Organizations](https://workos.com/docs/user-management/organizations) group users by company and scope SSO, SCIM, roles, and domain policies. The `organizationId` identifies the organization.

Descope [Tenants](https://docs.descope.com/b2b#multi-tenancy) are the equivalent. Most code that handles organizations is management/admin code that passes a WorkOS `organizationId` to the API — that simply becomes a Descope **tenant ID** passed to `management.tenant.*` / `management.user.*` calls. Only request-time session reads change shape: the JWT includes a `tenants` object with per-tenant role/permission data ([ref](https://docs.descope.com/authorization/role-based-access-control#tenants-and-roles)), plus `dct` for the active tenant.

Key differences:
- WorkOS: `organizationId` is a flat string. Descope: `tenants` is a nested object (`{ "tenantId": { "roles": [...], "permissions": [...] } }`); `dct` is the flat active-tenant string (the direct `organizationId` equivalent).
- WorkOS routes by organization-scoped login. Descope uses **tenant routing** (home realm discovery) in two main ways: **domain-based** — an email domain on the tenant (non-SSO) or an SSO domain on the tenant's SSO config (SSO); or **explicit tenant slug** — tenant name/ID hardcoded in source ([ref](https://docs.descope.com/sso/multi-sso)).
- Descope supports tenant-level SSO enforcement (require SAML/OIDC for all users in a tenant) ([ref](https://docs.descope.com/management/tenant-management/tenant)).
- Users are project-level entities in Descope; they're associated with tenants, not created per-tenant.
- Organization `metadata` → tenant `customAttributes` (pre-define in the Console schema).
- **Finding a user's tenants**: use `management.user.load(loginId)` and read `.userTenants` — it lists only that user's tenants. Avoid `management.tenant.loadAll()` + client-side filter; it scans every tenant in the project (O(n)).
- WorkOS's org-scoped login issues a session with one `organizationId`. Descope's JWT contains **all** tenants the user belongs to at once. Switching tenants does not require re-authentication — implement it client-side (e.g. an `active_tenant` cookie) and read the active tenant from the `tenants` object in the JWT.
- When a tenant is created and the user is added via the Management SDK, the existing JWT is stale — the `tenants` claim was set at login and doesn't include the new tenant. The user must re-authenticate (clear `DS`/`DSR` cookies and redirect to login) to get a JWT with the updated tenant list. Without this, the app sees an empty `tenants` claim and may loop back to onboarding.

Confirm the one-Organization-to-one-Tenant mapping before writing code — it ripples into SSO, SCIM, RBAC, and domain routing.

### Invitation model: WorkOS invitations → Descope user.invite()

WorkOS has a dedicated invitation system (invitation objects with their own lifecycle and IDs); an invited user is tracked as a pending invitation.

Descope's `management.user.invite()` creates a user record immediately in `"invited"` status and sends an invitation email. There is no separate invitation object to list, update, or revoke independently. To list pending invitations for a tenant, filter users by `status === "invited"`. To revoke an invitation, delete the user. (Verify the WorkOS invitation API shape in use before mapping revoke/resend semantics.)

### MFA enrollment and factor management

WorkOS MFA is configured in AuthKit. In Descope, MFA enrollment is managed through Flows, not the Management SDK — add an MFA step to a Flow in the Console; users enroll in-browser through the Flow component.

**Factor deletion SDK support varies by type:**
- **Passkeys**: `descopeClient.management.user.removeAllPasskeys(loginId)` — SDK-supported
- **TOTP (authenticator apps)**: no SDK method; deletion is Console-only (User Management → [user] → Delete TOTP Seed)
- **SMS/OTP factors**: no documented SDK method — may require REST API calls

### Directory Sync / SCIM: a lifecycle, not an import

WorkOS [Directory Sync](https://workos.com/docs/directory-sync) provisions users and groups from enterprise directories over SCIM, emitting `dsync.*` events. Descope supports SCIM provisioning, scoped per tenant.

**Treat this as a continuing pipeline, not a one-time import** — enterprise directories keep pushing create/update/suspend/delete events after cutover, so every directory must be re-pointed at Descope before cutover or provisioning silently breaks.

| WorkOS Directory Sync | Descope |
|---|---|
| SCIM endpoint + bearer token per directory | Descope SCIM endpoint + token per tenant |
| Directory user create/update/deprovision | Tenant user provisioning lifecycle |
| Directory groups | Group → role mapping in Descope |
| `dsync.*` / directory webhooks | Descope provisioning events / connectors |

Identify every directory, whether groups are synced, and whether groups map to roles. Descope SCIM is exposed via the HTTP API (`https://api.descope.com/v1/mgmt/scim/*`) where SDK coverage is thin — verify request/response shapes against the current API.

### Session refresh after profile changes

If a WorkOS app reflects profile changes immediately in the session, note that Descope has no equivalent push — profile changes via the Management SDK don't update the JWT already in the browser.

To trigger an immediate client-side token refresh after a profile update:
```ts
// @descope/react-sdk, @descope/nextjs-sdk/client, or WebJS SDK
const { refresh } = useDescope()
await refresh()
```

The user can also wait for the next auto-refresh (default: ~5 min, driven by the DSR refresh token) or sign out and back in. Use the explicit `refresh()` call if the app has a profile editing page that expects immediate UI updates.

**Session change event listeners** — instead of calling `refresh()` imperatively, subscribe to auth state changes via [docs.descope.com/client-sdk/auth-helpers#handling-authentication-state-changes](https://docs.descope.com/client-sdk/auth-helpers#handling-authentication-state-changes). Use event listeners when the session can change from multiple places (profile update, admin role grant, tenant assignment) and the UI needs to react consistently.

**Update JWT endpoint** — for server-side custom claim updates without waiting for a client refresh: `POST /v1/mgmt/user/jwt/update`. This updates stored JWT custom claims for a specific user; the user's next token refresh picks up the new claims. Verify the current endpoint behavior against Descope docs.

**User Profile Widget** — if the app is building a profile edit page, the Widget handles profile updates and session refresh automatically with no custom SDK calls. See `flows-and-widgets.md` → Widgets.

### Management API mapping

WorkOS's Management is accessed through the backend SDKs (`workos.userManagement.*`, `workos.organizations.*`, `workos.sso.*`) authenticated with `WORKOS_API_KEY`.

Descope uses a Management SDK initialized with a `managementKey` ([Node SDK](https://github.com/descope/node-sdk), [Python SDK](https://github.com/descope/python-sdk), [Go SDK](https://github.com/descope/go-sdk)).

| Operation | WorkOS | Descope (Node.js) |
|---|---|---|
| Create user | `workos.userManagement.createUser(...)` | `descopeClient.management.user.create(...)` ([ref](https://docs.descope.com/management/user-management/sdks)) |
| Update user | `workos.userManagement.updateUser(...)` | `descopeClient.management.user.update(...)` |
| List/search users | `workos.userManagement.listUsers(...)` | `descopeClient.management.user.search(...)` |
| Delete user | `workos.userManagement.deleteUser(...)` | `descopeClient.management.user.delete(...)` |
| Load user | `workos.userManagement.getUser(...)` | `descopeClient.management.user.load(...)` / `.loadByUserId(...)` |
| Create organization | `workos.organizations.createOrganization(...)` | `descopeClient.management.tenant.create(...)` |
| Create role | (dashboard / RBAC API) | `descopeClient.management.role.create(name, description, permissions, tenantId)` |

(Verify exact WorkOS method names against current docs.) Descope management keys are long-lived (rotatable via the Console).

### FGA: WorkOS FGA (warrants) → Descope ReBAC

WorkOS [Fine-Grained Authorization](https://workos.com/docs/fga) models resource types, relationships, and permissions and stores relationships as **warrants**. Descope has its own [ReBAC](https://docs.descope.com/authorization/rebac) system with a similar model (types, relations, computed permissions) but a different API shape.

**Schema definition:**

WorkOS FGA defines resource types, relations, and permissions in its schema. Descope uses a [DSL](https://docs.descope.com/authorization/rebac/define-schema) saved via `descopeClient.management.fga.saveSchema(schema)` ([ref](https://docs.descope.com/authorization/rebac/implement-schema)).

Descope ReBAC schema DSL syntax:

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

Example translation:
```
# WorkOS FGA (resource types + relations + permissions)
type document
  relation owner
  relation viewer
  permission can_view = owner or viewer

# Descope ReBAC DSL
type document
  relation owner: user
  relation viewer: user
  permission can_view: owner | viewer
```

**Operation mapping:**

| Operation | WorkOS FGA | Descope ReBAC (Node SDK) |
|---|---|---|
| Write relation | `fga.writeWarrant({ ... })` | `descopeClient.management.fga.createRelations([{ resource, resourceType, relation, target, targetType }])` ([ref](https://docs.descope.com/authorization/rebac/create-relations)) |
| Delete relation | `fga.writeWarrant({ op: 'delete', ... })` | `descopeClient.management.fga.deleteRelations([...])` |
| Check | `fga.check({ ... })` | `descopeClient.management.fga.check([{ resource, resourceType, relation, target, targetType }])` ([ref](https://docs.descope.com/authorization/rebac/check-relations)) |
| Who has access | (FGA query) | `descopeClient.management.authz.whoCanAccess(resource, relation, namespace)` |

**Key differences:**
- WorkOS warrants use `subject`/`relation`/`resource`. Descope uses `target`/`targetType`/`relation`/`resource`/`resourceType`.
- WorkOS FGA uses the same `WORKOS_API_KEY`. Descope ReBAC uses `DESCOPE_PROJECT_ID` + `DESCOPE_MANAGEMENT_KEY`.
- The model translation requires a dedicated review — confirm resources, relationships/privileges, where checks run, and any hierarchical inheritance. (Verify exact WorkOS and Descope shapes against current docs.) **Effort: High.**

### Pipes → Descope Outbound Apps

WorkOS **Pipes** store third-party OAuth tokens (Google, Slack, GitHub, etc.) for connected accounts and refresh them on demand. Descope's equivalent is [Outbound Apps](https://docs.descope.com/identity-federation/outbound-apps), which store third-party OAuth tokens and static API keys.

Users connect accounts client-side:
```
sdk.outbound.connect(appId, { redirectURL, scopes })
```
([ref](https://docs.descope.com/identity-federation/outbound-apps/connect))

Tokens are retrieved via the Management API:

```
# Fetch token with specific scopes
POST https://api.descope.com/v1/mgmt/outbound/app/user/token
Authorization: Bearer {projectId}:{managementKey}
Body: { "appId": "google-calendar", "userId": "U2abc...", "scopes": [...] }

# Fetch latest token (no scope filter)
POST https://api.descope.com/v1/mgmt/outbound/app/user/token/latest
Body: { "appId": "google-calendar", "userId": "U2abc..." }
```
([ref](https://docs.descope.com/identity-federation/outbound-apps/using-outbound-apps#fetching-outbound-apps-tokens))

Ask which providers are connected, where tokens are used (including AI agents and background jobs), and whether users must reconnect accounts or tokens can be migrated. AI-agent token storage maps to Outbound Apps; if the app uses WorkOS for MCP authorization, flag it for dedicated review (it may map to Descope Inbound Apps / OAuth app patterns) before generating any implementation code.

### User migration: WorkOS export → Descope import

WorkOS users don't automatically carry over. For production apps with existing users, this is a critical migration step.

Descope has [migration guides](https://docs.descope.com/migrate) with two broad approaches:
- **Full migration:** Export all users and organizations from WorkOS, then import them into Descope using the [Create User API](https://docs.descope.com/api/management/users/create-user) or [Batch Create User API](https://docs.descope.com/api/management/users/batch-create-users). Where password hashes can be exported, Descope accepts bcrypt hashes so users keep their passwords without a reset; otherwise plan a reset/passwordless path. See the [user format JSON guide](https://docs.descope.com/migrate/custom/user-format-json) for the expected shape. **Verify WorkOS's current user-export capability before committing to a no-reset path.**
- **Phased migration:** Roll out per tenant/batch rather than all at once.

Key fields to map: WorkOS `user.id` → Descope `loginId` (or `userId`), `email`, name fields, password hash (if exportable), and any user metadata → `customAttributes`.

Map each WorkOS **Organization** to a Descope **Tenant** and reproduce membership and tenant-scoped roles — get this mapping right first, since it ripples into SSO, SCIM, and RBAC. **If Directory Sync is in use, re-point SCIM at Descope before cutover** — a one-time import leaves provisioning broken the moment the directory pushes its next change. Active WorkOS sessions become invalid at cutover; plan for forced re-login.

### M2M authentication: WorkOS API keys → Descope Access Keys

WorkOS uses API keys (and client-credentials-style machine auth) for service-to-service calls.

Descope's equivalent is [Access Keys](https://docs.descope.com/management/m2m-access-keys). An access key is exchanged for a JWT, which is then validated by the receiving service the same way a user session token is validated. Access keys can be scoped to tenants and roles, and can have IP restrictions and expiration times.

| WorkOS | Descope |
|---|---|
| Create API key in dashboard | Create Access Key in Console → [Access Keys tab](https://app.descope.com/accessKeys) |
| API key secret | Access Key ID + Secret (returned once at creation) |
| Authenticate machine call with API key | `descopeClient.auth.exchangeAccessKey(accessKey)` ([ref](https://docs.descope.com/management/m2m-access-keys)) |
| Token validated server-side | Token validated via `descopeClient.validateSession()` — same as user tokens |

Access keys can also be created programmatically via `descopeClient.management.accessKey.create()`.

### Email templates: WorkOS → Descope messaging templates

WorkOS email/branding (verification, magic auth, invitations) is configured in the WorkOS dashboard / AuthKit branding.

Descope uses [Messaging Templates](https://docs.descope.com/management/messaging-templates) configured per authentication method. Templates support HTML and dynamic content via `{{}}` placeholders.

| Email type | WorkOS location | Descope location |
|---|---|---|
| Magic Link / OTP | AuthKit branding / email settings | Console → Settings → Authentication Methods → [Magic Link](https://docs.descope.com/auth-methods/magic-link/settings) or OTP → select connector → + New Template |
| Password Reset | AuthKit email settings | Console → Settings → Authentication Methods → [Passwords](https://docs.descope.com/auth-methods/passwords/settings) → Reset Password Email |
| User Invitation | AuthKit / dashboard | Console → [Project Settings → Sign Ups and User Invitations](https://docs.descope.com/management/project-settings#general-settings) → select connector → + New Template |
| Verification | AuthKit email settings | Handled within Flows (email verification is a Flow step, not a standalone email) |

Descope also supports SMS and voice templates for OTP delivery, configured the same way via messaging connectors.

### Webhooks / Audit Logs: WorkOS → Descope Audit Webhook

WorkOS [Audit Logs](https://workos.com/docs/audit-logs) and [webhooks](https://workos.com/docs/events) forward events (`user.created`, `organization.*`, `dsync.*`, etc.) to external services or your own endpoint with a signing secret.

| WorkOS | Descope |
|---|---|
| Webhook endpoint + signing secret | Descope webhook/connector + signature validation |
| `user.created` / `organization.*` / `dsync.*` events | Corresponding Descope events / connector triggers |
| Audit Logs (compliance) | [Audit Webhook Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook) |

Descope's [Audit Webhook Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook) streams audit events to your HTTP endpoint (Bearer, API Key, or Basic Auth). Descope also has a built-in [Audit Trail](https://docs.descope.com/audit) in the Console and supports streaming to third-party services via connectors. Search the codebase for webhook handlers; update event names, signature/validation logic, and payload handling. For apps that rely on WorkOS events/audit logs for compliance or monitoring, set up Descope audit/event forwarding **before** cutover to avoid gaps.

### Custom domains

WorkOS supports custom domains and domain verification so login appears on your own domain (and so enterprise SSO can be discovered by email domain).

Descope supports [custom domains](https://docs.descope.com/how-to-deploy-to-production/custom-domain) as well:
1. Create a CNAME record (e.g. `auth.example.com`) pointing to `cname.descope.com` (US) or `CNAME.euc1.descope.com` (EU).
2. Set the App URL in Console → Project Settings → General.
3. Add and verify the custom domain in Console.
4. Pass the custom domain as `baseUrl` to the Descope SDK/component: `<AuthProvider projectId="..." baseUrl="https://auth.example.com">`.

Domain verification also drives tenant/domain routing — important for enterprise SSO discovery (routing a user to the right tenant's SSO connection by email domain). Plan this before cutover so cookies and redirects work correctly on the production domain.

### Radar → Descope Flow-based security

**Mechanism difference (read this first):** WorkOS [Radar](https://workos.com/docs/radar) is a dashboard toggle layered on top of AuthKit — it collects device-fingerprint signals and *automatically* blocks / challenges / notifies based on the actions you enable, with no app code. Descope has **no single equivalent toggle**. Instead you reproduce Radar's behavior by adding Descope's built-in fingerprinting/risk signals to your [Flow](https://docs.descope.com/flows) and branching on them. So "configuring Radar" becomes "designing the Flow."

Descope surfaces risk signals as `riskInfo` inside a Flow. `riskInfo.botDetected` and `riskInfo.riskScore` require adding a **Fingerprint / Assess** action immediately after the login/signup screen; `riskInfo.impossibleTravel` and `riskInfo.trustedDevice` do not. For stronger detection, layer in fraud/CAPTCHA connectors (reCAPTCHA Enterprise, Turnstile, Telesign, Fingerprint, Forter, Sardine).

| Radar action | What it does in WorkOS | Descope equivalent |
|---|---|---|
| **Block** | Auth fails even with valid credentials | Flow conditional after Fingerprint Assess: on high `riskInfo.riskScore` / `riskInfo.botDetected`, branch to a deny/failure screen and end the Flow without issuing a session |
| **Challenge** | Sends an email/SMS OTP step-up | Risk-based step-up in the Flow: branch the high-risk path into an OTP/MFA step or a CAPTCHA connector before continuing |
| **Notify** | Sends an informational email; sign-in still proceeds | On the risk branch, fire an email/messaging connector or an outbound webhook (or rely on Descope audit events) to alert the user/admin while letting the Flow continue |

**Detection mapping** (verify current signal names against docs):
- Bot detection → `riskInfo.botDetected` (needs Fingerprint Assess) + CAPTCHA connectors
- Impossible travel → `riskInfo.impossibleTravel`
- Unrecognized device → `riskInfo.trustedDevice` (invert: untrusted = unrecognized)
- Brute force / repeat sign-up / stale accounts / managed lists / custom allow-deny → no single built-in signal; reproduce via `riskInfo.riskScore` thresholds, connectors, or custom Flow conditions

Radar is toggle-based in WorkOS. Descope's is composable — you add detection steps to your Flow and configure the response (block, challenge with MFA, allow with logging). More powerful but not configured by default; the decisioning must be *rebuilt* in the Flow.

### Admin Portal → SSO Setup Suite / Widgets

WorkOS [Admin Portal](https://workos.com/docs/admin-portal) is a hosted self-serve UI where customer IT admins configure SSO, Directory Sync, and domain verification. Do not default to rebuilding it as custom code.

- Generated portal links (`portal.generateLink(...)`) → SSO Setup Suite hosted/embedded flow or Tenant Profile Widget
- SSO setup screens → SSO Setup Suite
- Directory Sync / domain setup → corresponding Widgets

Ask which admin workflows are hosted by WorkOS today before choosing a replacement. WorkOS Widgets (org switching, Directory Sync setup, SSO setup, domain verification, audit log streaming, API keys) should each be evaluated against Descope [Widgets](https://docs.descope.com/widgets) — if a Widget covers the workflow, prefer it over custom code. See `flows-and-widgets.md` → Widgets and SSO Setup Suite.

### Testing checklist (applies to all samples)

**Compile first — no env vars needed.** Run `npx tsc --noEmit` (or `go build ./...`, `dotnet build`, etc.) immediately after code changes, before setting up `.env` or starting the server. Do not treat the migration as done until this exits clean.

After migrating, verify:
- DS and DSR cookies are set after login (check browser DevTools → Application → Cookies)
- Protected routes redirect to /login when DS cookie is absent
- Protected routes render when DS cookie is present and valid
- Logout clears both DS and DSR cookies
- Logout invalidates the refresh token (logging in again requires re-authentication)
- User claims (name, email, picture) display correctly
- API routes return 401 when no token is provided
- Expired session tokens are rejected (test by waiting or manually expiring)
- If using RBAC: roles/permissions appear in validated JWT claims
- If using FGA/ReBAC: authorization checks pass for permitted resources and fail for unpermitted ones
- If using Outbound Apps: third-party tokens are retrievable after user connects

---

## Next.js (standalone)


**Changes:**
- [`authkit-nextjs`](https://github.com/workos/authkit-nextjs) → [`@descope/nextjs-sdk`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk).
- AuthKit `<AuthKitProvider>` → [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#auth-provider) (takes `projectId` prop with the `NEXT_PUBLIC_` prefix).
- `useAuth()` (user/session/loading combined) → [`useSession()`](https://docs.descope.com/client-sdk/auth-helpers#booleans) + [`useUser()`](https://docs.descope.com/client-sdk/auth-helpers#core-sdk-functions) (Descope separates session state from user data).
- Removed the AuthKit callback route — Descope has no server-side OIDC handling; verify the client-side replacement.
- Added `pages/login.tsx` with the [`<Descope>` component](https://docs.descope.com/client-sdk/descope-components#descope-component) rendering the `sign-up-or-in` flow.
  - **`onSuccess` is required for redirect** — the component does not auto-navigate after login. Without it, the user finishes auth and stays on the login page:
    ```tsx
    const router = useRouter()
    <Descope
      flowId="sign-up-or-in"
      onSuccess={() => router.push('/dashboard')}
      onError={(e) => console.error(e)}
    />
    ```
- `withAuth()` route protection (client) replaced by manual `useSession()` check + redirect to `/login`.
- Server-side protection replaced by [`session()`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#server-side) + manual 401 response.
- `authkitMiddleware()` → Descope [`authMiddleware()`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#middleware).
- Logout changed from the AuthKit logout route to a button calling [`sdk.logout()`](https://docs.descope.com/client-sdk/auth-helpers#logout) via [`useDescope()`](https://docs.descope.com/client-sdk/auth-helpers#core-sdk-functions) + cookie clearing (two-step).

**Notes:**
- AuthKit's `withAuth()` works on both server and client. Descope splits this: check `isAuthenticated` from `useSession()` in client components and redirect yourself; use `session()` server-side. More verbose, more explicit.
- `NEXT_PUBLIC_` prefix is required on the project ID because [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#auth-provider) runs client-side.
- **Client vs. server session access:** `session()` from `@descope/nextjs-sdk/server` is for server components, server actions, and API routes **only**. In React client components, use `useSession()` + `useUser()` from `@descope/nextjs-sdk/client`. Using `session()` in a client component compiles but throws at runtime (attempts to read cookies in a browser context). **Never hand-decode the session token in client code** — always read auth state through the hooks. Scan for this pattern before finishing any Next.js migration.
- `User` interface: map WorkOS `user.id` → `userId`; profile fields (`email`, `firstName`/`lastName`, `profilePictureUrl`) come from the JWT Template / `useUser()`, not the raw token.

---

## Next.js (B2B): Migration Bug Catalog


This section documents bugs discovered during a migration review of a reference Next.js B2B SaaS
app. Every error below traces to incorrect assumptions about the `@descope/nextjs-sdk` API surface.

**Root cause:** The migration generated code against an assumed API that doesn't match what
`@descope/nextjs-sdk` actually exports. Every error below stems from not verifying the SDK's
`.d.ts` before generating imports and wrapper types.

---

### Bug 1: `getServerSession` doesn't exist — correct export is `session`

The migration generated:
```ts
import { getServerSession } from "@descope/nextjs-sdk/server"
const session = await getServerSession()
```

`getServerSession` does not exist in `@descope/nextjs-sdk`. The server entry exports two functions:
- **`session(config?)`** — reads the session from request headers/cookies in a Next.js server component or server action. No arguments required. Returns `AuthenticationInfo | undefined`.
- **`getSession(req, config?)`** — reads from an explicit `NextApiRequest` object. Intended for API routes only.

The correct replacement for a server-component session read (no req argument) is `session`, not `getServerSession`. The name was invented by analogy, not verified.

**Fix:** Verify exports before writing any import. For this SDK:
```ts
// Server component / server action (no req argument needed):
import { session } from "@descope/nextjs-sdk/server"
const authInfo = await session()

// Or wrap it into the project's own session type:
import { session as sdkSession } from "@descope/nextjs-sdk/server"
```

---

### Bug 2: Return type is `AuthenticationInfo`, not an `{isAuthenticated, claims, token}` shape

The migration generated a `DescopeSession` interface shaped like the WorkOS `withAuth()` session object:
```ts
interface DescopeSession {
  isAuthenticated: boolean   // ← does not exist
  token: string              // ← misleading: this was meant to be the raw JWT
  claims: {                  // ← does not exist; decoded JWT lives under "token"
    sub: string
    email?: string
    tenants?: Record<string, { roles: string[] }>
    ...
  }
}
```

`session()` returns `AuthenticationInfo` from `@descope/node-sdk`, which is:
```ts
interface AuthenticationInfo {
  jwt: string          // raw session JWT string
  token: Token         // decoded JWT claims: { sub?, exp?, iss?, [claim: string]: unknown }
  cookies?: string[]
}
```

Key mismatches:
- `isAuthenticated` — not present. `undefined` return means unauthenticated; a non-null object means authenticated. (WorkOS's `withAuth()` exposes a boolean-ish shape; Descope does not.)
- `claims` — not present. Decoded claims are on `token`.
- `token` (as JWT string) — not present as `token`; the raw JWT is `jwt`.

Because the cast was `session as unknown as DescopeSession`, TypeScript didn't catch this. At runtime:
- Every `!session?.isAuthenticated` check would always be `true` (property doesn't exist), making every auth guard fail.
- Every `session.claims.sub` / `session.claims.email` would return `undefined`.

**Fix:** Create a typed adapter that maps `AuthenticationInfo` to a stable internal type:
```ts
import { session as sdkSession } from "@descope/nextjs-sdk/server"
import type { AuthenticationInfo } from "@descope/node-sdk"

export interface DescopeSession {
  isAuthenticated: boolean
  jwt: string
  token: {
    sub: string
    email?: string
    name?: string
    tenants?: Record<string, { roles: string[]; permissions: string[] }>
    [key: string]: unknown
  }
}

export async function getDescopeSession(): Promise<DescopeSession | null> {
  const authInfo = await sdkSession()
  if (!authInfo) return null
  return {
    isAuthenticated: true,
    jwt: authInfo.jwt,
    token: authInfo.token as DescopeSession["token"],
  }
}
```

---

### Bug 3: `cookies()` from `next/headers` is async in Next.js 15

The migration generated:
```ts
import { cookies } from "next/headers"

export function getActiveTenantId(session: DescopeSession): string | null {
  const cookieStore = cookies()   // ← synchronous call; wrong in Next.js 15
  ...
}
```

In Next.js 15, `cookies()` is async and returns `Promise<ReadonlyRequestCookies>`. The synchronous call compiles (TypeScript doesn't catch it because `cookies()` appears to return `ReadonlyRequestCookies` directly in older types) but throws at runtime.

**Fix:** Check the target project's Next.js version before generating cookie/header reads. For Next.js 15+:
```ts
export async function getActiveTenantId(session: DescopeSession): Promise<string | null> {
  const cookieStore = await cookies()
  ...
}
```

---

### Bug 4: Making a helper async cascades to all callers — trace the dependency chain

When `getActiveTenantId` became async, the following chain all needed `async`/`await`:
1. `getActiveTenantId` → async
2. `getActiveTenantRoles` (calls `getActiveTenantId`) → async
3. `getRole` in `lib/roles.ts` (calls `getActiveTenantRoles`) → async
4. All call sites in server components and server actions → add `await`

This affected 20+ call sites across the project. The migration generated none of them as async, so adding `await cookies()` would have broken the entire tenant-aware authorization layer silently (TypeScript accepts `await` on non-Promise values without error).

**Practice:** When making any shared helper async, immediately grep all call sites and propagate `async`/`await` before finishing the edit.

---

### Summary: what to verify before generating Next.js + `@descope/nextjs-sdk` code

1. **Export names:** Resolve `node_modules/@descope/nextjs-sdk/dist/types/server/*.d.ts` and confirm the exact function names before writing any import.
2. **Return type:** `session()` returns `AuthenticationInfo | undefined` from `@descope/node-sdk`, not a boolean-flagged WorkOS-style session object.
3. **isAuthenticated:** Does not exist on `AuthenticationInfo`. Unauthenticated = `undefined`; authenticated = non-null object.
4. **claims vs token:** Decoded JWT claims are under `.token` (a `Token` object), not `.claims`. Raw JWT string is under `.jwt`.
5. **Next.js version:** Check `package.json` for Next.js ≥ 15. If so, `cookies()` and `headers()` from `next/headers` are async — all consumers must be async.
6. **Async cascade:** Tracing async upward from `cookies()` may require updating 10+ files. Plan for it.

---

## Next.js (with separate Express API server)


**Changes:**
- [`authkit-nextjs`](https://github.com/workos/authkit-nextjs) → [`@descope/nextjs-sdk`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk) (frontend) + [`@descope/node-sdk`](https://github.com/descope/node-sdk) (API server).
- WorkOS backend client (`@workos-inc/node`) → singleton `getDescopeClient()` using `@descope/node-sdk`.
- Removed AuthKit's middleware-handled `/auth/*` routes. Replaced with Next.js middleware using Descope's [`authMiddleware()`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#middleware) to check the `DS` cookie and redirect unauthenticated users.
- Express API server (`api-server.js`): replaced WorkOS token validation (`express-jwt` + `jwks-rsa` against WorkOS JWKS) with `@descope/node-sdk` [`validateSession()`](https://docs.descope.com/authorization/session-management/session-validation/backend#validate-session).
- Added `/login` page with the [`<Descope>` React component](https://docs.descope.com/client-sdk/descope-components#descope-component).

**Token proxying changes:**
WorkOS's `getAccessToken()` returns an access token (distinct from the sealed session) passed to the external API as a Bearer token, validated against WorkOS's JWKS.

Descope has no separate access token. The session token (DS cookie) is the token you pass to the API server. The Next.js API route reads `DS` from cookies and forwards it as `Authorization: Bearer <DS>`. The API server validates it with `descopeClient.validateSession(token)`.

For audience validation with Descope, configure a custom `aud` claim in the Descope Console's [JWT Templates](https://docs.descope.com/management/jwt-templates) and pass the `audience` parameter to [`validateSession()`](https://docs.descope.com/getting-started/nodejs#implement-session-validation).

**Notes:**
- AuthKit manages OIDC discovery, token caching, and sealed session cookies. Descope's `DescopeClient` validates JWTs against [cached public keys](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation). The frontend ([Descope Flows](https://docs.descope.com/flows)) handles what AuthKit used to do.
- `jwks-rsa` fetches and caches JWKS from WorkOS's `/.well-known/jwks.json`. Descope's Node SDK does the same from `https://api.descope.com/v2/keys/<project_id>` ([ref](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation#finding-your-public-key)). No configuration needed.
- Removing `express-jwt` + `jwks-rsa` cuts 2 dependencies and ~15 lines of JWKS config. The Descope replacement is ~15 lines of middleware calling `validateSession()`.

**Limitation:**
- If the original API server validated the `audience` claim, replicate it: (1) configure `aud` in [Descope's JWT Templates](https://docs.descope.com/management/jwt-templates), (2) pass `audience` to `validateSession()` ([Node SDK docs](https://docs.descope.com/getting-started/nodejs#implement-session-validation)). Descope's `validateSession()` checks signature and expiry but skips audience by default. Easy to miss during migration.

---

## Go


**Changes:**
- WorkOS Go SDK ([`workos-go`](https://github.com/workos/workos-go)) → [Descope Go SDK](https://github.com/descope/go-sdk).
- Server-side auth endpoints that handled the AuthKit redirect/callback code exchange collapse to a single handler that validates `DS` session tokens.
- Frontend removes the AuthKit redirect/login/callback routes. Replaced with a `/login` page containing the [`<Descope>` component](https://docs.descope.com/client-sdk/descope-components#descope-component) and a client-side `LogoutButton` using [`useDescope().logout()`](https://docs.descope.com/client-sdk/auth-helpers#logout).
- Request handling reads the `DS` cookie instead of a sealed WorkOS session cookie, and passes it as the Bearer token.

**Notes:**
- Go SDK constructor: `client.NewWithConfig(&client.Config{ProjectID: "..."})`. Session validation: [`descopeClient.Auth.ValidateSessionWithToken(ctx, token)`](https://docs.descope.com/getting-started/go#implement-session-validation) returns `(bool, *descope.Token, error)`. `Token.Claims` is `map[string]interface{}`. Ref: [Descope Go SDK](https://github.com/descope/go-sdk).
- WorkOS `organizationId` → a Descope **tenant ID**: pass it to management calls (`descopeClient.Management.Tenant()` / user-tenant association); at request time read tenant context off the returned `*descope.Token` (`token.GetTenants()`, or the `dct` claim for the active tenant).
- Config: WorkOS `WORKOS_API_KEY` + `WORKOS_CLIENT_ID` + `WORKOS_REDIRECT_URI` + `WORKOS_COOKIE_PASSWORD` → `DESCOPE_PROJECT_ID` only (+ `DESCOPE_MANAGEMENT_KEY` for management ops).
- `go.mod`: `github.com/workos/workos-go` → [`github.com/descope/go-sdk`](https://github.com/descope/go-sdk). Fewer dependencies — no separate OIDC/OAuth2 libraries needed since auth is client-side.

**Limitation:**
- The Go SDK's exported type names (`client.DescopeClient`, `descope.Token`) aren't fully documented in Descope's official docs. The [Go quickstart](https://docs.descope.com/getting-started/go) shows usage patterns, not Go type signatures. Verify against [Go SDK README](https://github.com/descope/go-sdk#readme) examples and `go doc` output.
