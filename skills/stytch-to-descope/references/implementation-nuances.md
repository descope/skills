# Descope Migration: Implementation Notes (Stytch → Descope)

## Contents

**General Insights — Architecture & Flow**
- [Stytch owns the flow; Descope validates tokens](#stytch-owns-the-flow-descope-validates-tokens)
- [No drop-in middleware for Express or Flask](#no-drop-in-middleware-for-express-or-flask)
- [Fewer network round-trips at login](#fewer-network-round-trips-at-login)
- [Stytch vs Descope flow comparison](#stytch-vs-descope-flow-comparison)

**General Insights — Feature Mapping: Stytch → Descope**
- [Social login / connection mapping + SSO URLs](#social-login--connection-mapping)
- [RBAC: Stytch → Descope](#rbac-stytch--descope)
- [Multi-tenancy: Stytch Organizations → Descope Tenants](#multi-tenancy-stytch-organizations--descope-tenants)
- [Invitation model](#invitation-model-stytch-invitations--descope-userinvite)
- [MFA enrollment and factor management](#mfa-enrollment-and-factor-management)
- [SCIM: HTTP API only, not in SDK](#scim-http-api-only-not-in-sdk)
- [Session refresh after profile changes + sdk.refresh()](#session-refresh-after-profile-changes)
- [Management API mapping](#management-api-mapping)
- [Authorization beyond RBAC → Descope ReBAC](#authorization-beyond-rbac--descope-rebac)
- [Third-party provider tokens → Descope Outbound Apps](#third-party-provider-tokens--descope-outbound-apps)
- [User migration: Stytch export → Descope import](#user-migration-stytch-export--descope-import)
- [M2M: Stytch client credentials → Descope Access Keys](#m2m-authentication-stytch-client-credentials--descope-access-keys)
- [Email templates](#email-templates-stytch--descope-messaging-templates)
- [Webhooks / Events → Descope Audit Webhook](#webhooks--events-stytch--descope-audit-webhook)
- [Custom domains](#custom-domains)
- [Attack protection](#attack-protection-stytch-fraud--risk--descope-flow-based-security)
- [Testing checklist](#testing-checklist-applies-to-all-samples)

**General Insights — Common Gotchas**
- [Cookie names: DS and DSR](#cookie-names-ds-and-dsr-configurable)
- [User claims differ (dct, tenants, email not default)](#user-claims-differ)
- [Audience validation requires explicit setup](#audience-validation-requires-explicit-setup)
- [One session token, not two](#stytch-session-tokens--one-descope-session-token)
- [Logout requires two steps](#logout-requires-two-steps)
- [One env var instead of several](#one-env-var-instead-of-several)
- [Approved Domains: domain only, no protocol or path](#approved-domains-domain-only-no-protocol-or-path)

**Framework Sections**
- [Express.js](#expressjs)
- [Flask / Python](#flask--python)
- [Next.js (standalone)](#nextjs-standalone)
- [Next.js (B2B): Migration Bug Catalog](#nextjs-b2b-migration-bug-catalog)
- [Next.js (with separate Express API server)](#nextjs-with-separate-express-api-server)
- [Go + Encore](#go--encore)

> **See also:** `flows-and-widgets.md` in this directory — Stytch→Descope lingo map, Flow structure and templates, Widget types, SSO Setup Suite, and the Console-vs-code decision guide. Read it before migrating any auth UI, MFA enrollment, user management pages, or SSO configuration.

---

## General Insights

**— Architecture & Flow —**

### Stytch owns the flow; Descope validates tokens

Stytch's SDKs own the authentication ceremony. The frontend SDKs (`@stytch/react`, `@stytch/nextjs`, `@stytch/vanilla-js`) render prebuilt UI or drive headless calls (magic links, OTP, OAuth, passkeys, B2B discovery); the backend SDKs (`stytch` for Node/Python, `stytch-go`, `stytch-java`) authenticate the resulting session via `sessions.authenticate()` / `sessions.authenticateJwt()` and work with an opaque `session_token` plus a `session_jwt`.

Descope splits the work. The frontend ([Descope Flows](https://docs.descope.com/flows) via [web components](https://docs.descope.com/client-sdk/descope-components) or [client SDKs](https://docs.descope.com/client-sdk/initialize-sdk)) runs the authentication ceremony and stores JWTs in `DS` (session) and `DSR` (refresh) cookies. The backend [validates those JWTs](https://docs.descope.com/authorization/session-management/session-validation/backend). No server-side OAuth callback, no authorization code exchange, no server-managed session store.

Every Stytch→Descope migration adds a dedicated login page (or embeds the [`<descope-wc>` component](https://docs.descope.com/client-sdk/descope-components#descope-component)) in place of the Stytch UI/headless flow, and reads the Descope session instead of authenticating a Stytch session token.

**— Common Gotchas —**

### No drop-in middleware for Express or Flask

Stytch's backend SDKs give you `sessions.authenticate()` / `sessions.authenticateJwt()` to validate a session, but you still write your own route protection — Stytch doesn't auto-mount `/login`, `/logout`, or a callback route. Descope is the same; there is no Express middleware package. You:

1. Add `cookie-parser` (Express doesn't parse cookies by default).
2. Write custom middleware: read `DS` cookie → call [`descopeClient.validateSession()`](https://docs.descope.com/authorization/session-management/session-validation/backend#validate-session) → attach user claims to `req`.
3. Write your own `requiresAuth()` guard (3 lines, but manual).

The [Descope blog](https://www.descope.com/blog/post/authentication-middleware) shows an Express middleware pattern, but it's a tutorial example, not a published package.

Flask is the same story. Where you'd validate a Stytch session in your request lifecycle, Descope's Flask backend [validates tokens](https://docs.descope.com/getting-started/python) only; auth UI is client-side.

FastAPI follows the same pattern. Descope's approach is a [custom JWT authorizer using JWKS validation](https://docs.descope.com/authorization/session-management/session-validation/oidc-jwt-authorizers/python-fastapi-jwt-authorizer): a `TokenVerifier` class that reads the `Authorization` header, validates against Descope's JWKS, and attaches as a FastAPI `Security()` dependency. No auto-mounted routes, no session store.

### Cookie names: `DS` and `DSR` (configurable)

Descope web components and client SDKs default to `DS` for the session JWT and `DSR` for the refresh JWT. The [Node SDK README](https://github.com/descope/node-sdk#session-validation-using-middleware) references `DescopeClient.SessionTokenCookieName` and `DescopeClient.RefreshTokenCookieName` as constants.

These names are configurable. The [End action in Descope Flows](https://docs.descope.com/flows/actions/end-action#session-cookie-name) has "Session Cookie Name" and "Refresh Cookie Name" fields that override the defaults. Use custom names when running multiple Descope projects on the same root domain to avoid cookie collisions. Backend code must then read the custom cookie name instead of `DS`/`DSR`.

The `sessionTokenViaCookie` parameter in [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#cookie-configuration-options) controls whether the session token is set as a cookie at all (vs. managed in-memory by the SDK).

### User claims differ

The default Descope session JWT ([structure ref](https://docs.descope.com/authorization/session-management#descope-session-jwt-structure)) contains `sub`, `amr`, `drn`, `tenants`, `roles`, and `permissions`. It does **not** include `email`, `name`, or `picture` unless you add them via [JWT Templates](https://docs.descope.com/management/jwt-templates) or [Flow actions > Custom Claims](https://docs.descope.com/flows/actions/custom-claims). Stytch exposes these profile fields on the `member`/`user` object (and may carry them as custom claims in the `session_jwt`), so code that reads them off the token will break after migration.

| Field | Stytch | Descope |
|---|---|---|
| User ID | `user_id` (B2C) / `member_id` (B2B) | `sub` in JWT, `userId` in SDK user objects |
| Display name | `name` (with `first_name` / `last_name`) on the member/user object | Not in JWT by default. Add via [JWT Templates](https://docs.descope.com/management/jwt-templates). |
| Email | `email` / `email_address` on the member/user object | Not in JWT by default. Add via JWT Templates. Available on user object via SDK management calls. |
| Profile picture | `profile_picture_url` (from OAuth providers) | Not in JWT by default. Add via JWT Templates. |
| Email verified | `email_address_verified` (B2B) / verification status on the user object | Not in JWT by default. Available on user object as `verifiedEmail`. Add to JWT via Custom Claims if needed. |
| Roles | Stytch B2B RBAC roles (carried in the session) | `roles` array in JWT (embedded by default with [RBAC](https://docs.descope.com/authorization/role-based-access-control)) |
| Permissions | Derived from Stytch B2B roles (`resource_id` + `action`) | `permissions` array in JWT (embedded by default) |
| Tenant ID | `organization_id` (flat string, B2B) | `dct` — flat string with active tenant ID, direct `organization_id` equivalent; `tenants` — object keyed by tenant ID containing per-tenant `roles` and `permissions`. Use `dct` when you only need the ID; use `tenants` when you need per-tenant roles ([ref](https://docs.descope.com/authorization/role-based-access-control#tenants-and-roles)) |

**Migration action item:** Before migrating, configure a JWT Template that includes `email`, `name`, and any other profile claims your app reads from the token. Without this, code that reads `token.email` or `token.name` after `validateSession()` will get `undefined`.

### Audience validation requires explicit setup

Stytch `session_jwt`s include an `aud` claim (your Stytch project ID), and apps validating it scope tokens to that project.

Descope session tokens don't include an `aud` claim by default. To replicate that audience validation:
1. Configure a custom `aud` claim in the Descope Console's [JWT Templates](https://docs.descope.com/management/jwt-templates).
2. Pass the `audience` parameter to [`validateSession()`](https://docs.descope.com/getting-started/nodejs#implement-session-validation) on the backend.

This is easy to miss during migration. Without it, any valid Descope session token from any project would pass validation. The audience check prevents cross-project token reuse.

### Stytch session tokens → one Descope session token

Stytch issues two representations of a session: an opaque `session_token` (validated by a network call to Stytch) and a `session_jwt` (validated locally). Both represent the same session.

Descope has one token: the session JWT (`DS` cookie). When calling a backend API, you forward the `DS` cookie value as `Authorization: Bearer <DS>`. The API server validates it with `descopeClient.validateSession(token)`. No opaque-vs-JWT distinction to maintain. If you need audience differentiation, use [JWT Templates](https://docs.descope.com/management/jwt-templates).

### Logout requires two steps

Stytch logout revokes the session server-side (`sessions.revoke()` on the backend, or the client SDK's logout).

Descope logout ([backend](https://docs.descope.com/authorization/session-management/session-validation/backend#logout-current-session-using-backend-sdk) / [client](https://docs.descope.com/client-sdk/auth-helpers#logout)):
1. Call `descopeClient.logout(refreshToken)` (server-side) or `sdk.logout()` (client-side) to invalidate the refresh token.
2. Clear the `DS` and `DSR` cookies.

Clear cookies without calling logout → the refresh token stays valid on Descope's servers. Call logout without clearing cookies → the client holds a dead session token that fails validation but confuses client-side state.

### One env var instead of several

Stytch needs `STYTCH_PROJECT_ID` and `STYTCH_SECRET` on the backend, plus a public token (`STYTCH_PUBLIC_TOKEN` / `NEXT_PUBLIC_STYTCH_PUBLIC_TOKEN`) for the frontend SDK.

Descope needs `DESCOPE_PROJECT_ID` (or `NEXT_PUBLIC_DESCOPE_PROJECT_ID` for Next.js client-side). No client secret for frontend flows. The web component authenticates against Descope's API using the project ID. Backend SDKs [fetch the public key](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation#finding-your-public-key) from Descope's JWKS endpoint (`https://api.descope.com/v2/keys/<project_id>`) using the same project ID. No secrets to rotate for the auth flow.

For management operations (user CRUD, role management, ReBAC), add `DESCOPE_MANAGEMENT_KEY`.

### Approved Domains: domain only, no protocol or path

Stytch apps often register full callback URLs — e.g. `http://localhost:3000/authenticate` for OAuth or magic-link token exchange. During migration, agents routinely tell users to add the same URL to Descope. That format does not work.

Descope validates redirect URLs against **Approved Domains** (Console → Project Settings → Security → Approved Domains), not a list of full redirect URIs. Per [project settings docs](https://docs.descope.com/management/project-settings#approved-domains), web domains are **domain only — no protocol, no path**:

- **Correct**: `localhost:3000`, `myapp.com`, `staging.myapp.com`
- **Wrong**: `http://localhost:3000/authenticate`, `https://localhost:3000`, `http://localhost:3000`

For local development, include the port (`localhost:3000`) but omit `http://`/`https://` and any path like `/authenticate`. Descope embedded Flows complete auth client-side — there is no Stytch-style `/authenticate` callback to whitelist. If OAuth via SDK/API passes a `redirectURL`, only the URL's host (and port, for localhost) must match an approved domain; paths do not get their own entries.

**Symptom:** OAuth or redirect-based flows fail with domain/redirect validation errors after adding what looks like a correct Stytch callback URL.

**— Feature Mapping: Stytch → Descope —**

### Social login / connection mapping

Stytch OAuth / social login (Google, GitHub, Microsoft, etc.) is configured per project and surfaced through the Stytch UI or headless OAuth start calls.

Descope equivalent: configure [social auth methods](https://docs.descope.com/authentication/social) in the Descope Console, then add them to a [Flow](https://docs.descope.com/flows). The Descope web component renders the configured providers. No code changes needed; configuration only.

Stytch enterprise **SSO Connections** (SAML/OIDC, configured per Organization) map to Descope's [SSO configuration](https://docs.descope.com/sso) (per-tenant SSO for B2B). A Stytch Organization's SSO connections map to Descope's per-tenant SSO settings.

**SSO Setup Suite:** For apps that expose a self-service SSO settings page where tenant admins configure their IdP, the SSO Setup Suite (Console wizard) can replace `sso.configureSAMLByTenant()` / `configureOIDCByTenant()` calls entirely — tenant admins configure their own IdP through a guided wizard with no engineering involvement. Surface this before migrating any Management SDK SSO code. See `flows-and-widgets.md` → SSO Setup Suite.

**SSO callback and ACS URLs:**
- Social OAuth callback (Google, GitHub, etc.): `https://api.descope.com/v1/oauth/callback`
- SAML ACS URL (per-tenant enterprise SSO): found in Console → SSO → [tenant] → SP Settings — tenant-specific, not a global hardcoded URL
- OIDC authorization server endpoints (Descope acting as IdP): `/oauth2/v1/authorize`, `/oauth2/v1/token` — used only if you run Descope as an OIDC provider for external clients (Inbound Apps)

`https://api.descope.com/oauth2/v1/callback` does not exist — do not use it as a callback URL when configuring an IdP.

### RBAC: Stytch → Descope

Stytch B2B RBAC is built from Resources, Actions, Permissions, and Roles: a permission is a `resource_id` + `action` (e.g. `documents:read`), and roles are collections of permissions assigned to Members. Stytch evaluates these via frontend authorization helpers or backend session authentication that includes `organization_id`, `resource_id`, and `action`.

Descope RBAC ([docs](https://docs.descope.com/authorization/role-based-access-control)): same concept, but permissions are strings grouped into roles, and roles can be project-level or tenant-level. Encode each Stytch `resource_id + action` pair as a Descope permission string (e.g. `documents.read`). Roles/permissions are embedded in the JWT by default. Descope SDK methods:
- `descopeClient.management.permission.create(name, description)` ([ref](https://docs.descope.com/authorization/role-based-access-control/with-sdks))
- `descopeClient.management.role.create(name, description, permissionNames, tenantId)` ([ref](https://docs.descope.com/authorization/role-based-access-control/with-sdks))
- Roles appear in the JWT `roles` array; permissions in `permissions` array.

Backend code performing a Stytch authorization check (`organization_id` + `resource_id` + `action`) changes to reading the `roles`/`permissions` arrays from Descope's validated JWT claims.

### Multi-tenancy: Stytch Organizations → Descope Tenants

Stytch [Organizations](https://stytch.com/docs/b2b) group members by company. The `organization_id` identifies the organization.

Descope [Tenants](https://docs.descope.com/b2b#multi-tenancy) are the equivalent. Users can belong to multiple tenants with different roles per tenant. The JWT includes a `tenants` object with per-tenant role/permission data ([ref](https://docs.descope.com/authorization/role-based-access-control#tenants-and-roles)).

Key differences:
- Stytch: `organization_id` is a flat string. Descope: `tenants` is a nested object (`{ "tenantId": { "roles": [...], "permissions": [...] } }`).
- Stytch scopes login to a single Organization (`organization_id` on the auth call). Descope routes by email domain or tenant-specific login URLs ([ref](https://docs.descope.com/sso/multi-sso)).
- Descope supports tenant-level SSO enforcement (require SAML/OIDC for all users in a tenant) ([ref](https://docs.descope.com/management/tenant-management/tenant)).
- Users are project-level entities in Descope; they're associated with tenants, not created per-tenant.
- **Finding a user's tenants**: use `management.user.load(loginId)` and read `.userTenants` — it lists only that user's tenants. Avoid `management.tenant.loadAll()` + client-side filter; it scans every tenant in the project (O(n)).
- Stytch's org-scoped session is tied to one Organization. Descope's JWT contains **all** tenants the user belongs to at once. Switching tenants does not require re-authentication — implement it client-side (e.g. an `active_tenant` cookie) and read the active tenant from the `tenants` object in the JWT.
- When a tenant is created and the user is added via the Management SDK, the existing JWT is stale — the `tenants` claim was set at login and doesn't include the new tenant. The user must re-authenticate (clear `DS`/`DSR` cookies and redirect to login) to get a JWT with the updated tenant list. Without this, the app sees an empty `tenants` claim and may loop back to onboarding.

### Invitation model: Stytch invitations → Descope user.invite()

Stytch B2B invites a member through a dedicated invitation flow (e.g. `organizations.members.create` with an invite, or a magic-link invite) that emails the invitee.

Descope's `management.user.invite()` creates a user record immediately in `"invited"` status and sends an invitation email. There is no separate invitation object to list, update, or revoke independently. To list pending invitations for a tenant, filter users by `status === "invited"`. To revoke an invitation, delete the user.

### MFA enrollment and factor management

MFA enrollment is managed through Flows, not the Management SDK — there is no equivalent to a Stytch server-side MFA enrollment call. Add an MFA step to a Flow in the Console; users enroll in-browser through the Flow component.

**Factor deletion SDK support varies by type:**
- **Passkeys**: `descopeClient.management.user.removeAllPasskeys(loginId)` — SDK-supported
- **TOTP (authenticator apps)**: no SDK method; deletion is Console-only (User Management → [user] → Delete TOTP Seed)
- **SMS/OTP factors**: no documented SDK method — may require REST API calls

### SCIM: HTTP API only, not in SDK

Stytch exposes SCIM directory connections for B2B Organizations (managed via the Stytch API/dashboard). Descope supports SCIM but only via the HTTP API (`https://api.descope.com/v1/mgmt/scim/*`), not the Node.js or Python SDKs. Implement with raw `fetch()` calls. Verify the request/response shapes against the current API — the endpoints are documented but not SDK-wrapped.

### Session refresh after profile changes

A Stytch `session_jwt` is short-lived and refreshes from the session; profile changes made via the Stytch API don't retroactively update a JWT already in the browser. Descope behaves the same way — profile changes via the Management SDK don't update the JWT already in the browser, and there is no server call that pushes an update to an active browser session.

To trigger an immediate client-side token refresh after a profile update:
```ts
// @descope/react-sdk, @descope/nextjs-sdk/client, or WebJS SDK
const { refresh } = useDescope()
await refresh()
```

The user can also wait for the next auto-refresh (default: ~5 min, driven by the DSR refresh token) or sign out and back in. Use the explicit `refresh()` call if the app has a profile editing page that expects immediate UI updates.

**Session change event listeners** — instead of calling `refresh()` imperatively, subscribe to auth state changes via [docs.descope.com/client-sdk/auth-helpers#handling-authentication-state-changes](https://docs.descope.com/client-sdk/auth-helpers#handling-authentication-state-changes). Use event listeners when the session can change from multiple places (profile update, admin role grant, tenant assignment) and the UI needs to react consistently.

**Update JWT endpoint** — for server-side custom claim updates without waiting for a client refresh: `POST /v1/mgmt/user/jwt/update`. This updates stored JWT custom claims for a specific user; it is not a session mutation and does not push an update to the browser. The user's next token refresh picks up the new claims. Verify the current endpoint behavior against Descope docs — this endpoint is less documented than the Management SDK methods.

**User Profile Widget** — if the app is building a profile edit page, the Widget handles profile updates and session refresh automatically with no custom SDK calls. See `flows-and-widgets.md` → Widgets.

### Management API mapping

Stytch's backend API is accessed with your `project_id` + `secret` (Basic auth) via the backend SDKs (`stytch` for Node/Python, `stytch-go`, `stytch-java`).

Descope uses a Management SDK initialized with a `managementKey` ([Node SDK](https://github.com/descope/node-sdk), [Python SDK](https://github.com/descope/python-sdk), [Go SDK](https://github.com/descope/go-sdk)).

| Operation | Stytch (Node) | Descope (Node.js) |
|---|---|---|
| Create user | `client.users.create(...)` (B2C) / `client.organizations.members.create(...)` (B2B) | `descopeClient.management.user.create(...)` ([ref](https://docs.descope.com/management/user-management/sdks)) |
| Update user | `client.users.update(...)` / `organizations.members.update(...)` | `descopeClient.management.user.update(...)` |
| Search users | `client.users.search(...)` / `organizations.members.search(...)` | `descopeClient.management.user.search(...)` |
| Delete user | `client.users.delete(...)` / `organizations.members.delete(...)` | `descopeClient.management.user.delete(...)` |
| Load user | `client.users.get(...)` / `organizations.members.get(...)` | `descopeClient.management.user.load(...)` / `.loadByUserId(...)` |
| List permissions | (Stytch RBAC policy) | `descopeClient.management.permission.loadAll()` |
| Create role | (Stytch RBAC policy, dashboard/API) | `descopeClient.management.role.create(name, description, permissions, tenantId)` |

Stytch authenticates every backend call with the project secret; Descope management keys are long-lived (rotatable via the Console).

### Authorization beyond RBAC → Descope ReBAC

Stytch is RBAC-oriented and has no fine-grained / relationship-based authorization product. If your Stytch app implements **app-side** fine-grained authorization — project membership, document ownership, workspace hierarchy, shared resources, delegated access, or other relationship-based checks — do not assume this is covered by a simple RBAC migration. Descope [ReBAC](https://docs.descope.com/authorization/rebac) can model it: define a schema in the [DSL](https://docs.descope.com/authorization/rebac/define-schema) via `descopeClient.management.fga.saveSchema(schema)`, then create and check relations (`management.fga.createRelations([...])`, `management.fga.check([...])`).

Use Descope ReBAC/FGA **only** when the authorization model truly depends on relationships between entities. Otherwise, keep app-specific authorization in the application database and use Descope for identity, roles, tenant membership, and token claims.

Example relationship-style model:

```
# App-side authorization concept
Resource type: document
Relations:
- owner
- editor
- viewer

Permissions:
- can_view
- can_edit
- can_delete

# Descope ReBAC-style model
type user

type document
  relation owner: user
  relation editor: user
  relation viewer: user
  permission can_view: owner | editor | viewer
  permission can_edit: owner | editor
  permission can_delete: owner
```

| Authorization need              | Recommended Descope approach                         |
| ------------------------------- | ---------------------------------------------------- |
| Tenant-wide roles               | Descope RBAC                                         |
| Project-wide/global roles       | Descope project-level roles                          |
| Per-tenant roles                | Descope tenant-level roles                           |
| Relationship-based permissions  | Descope ReBAC / FGA                                  |
| App database ownership checks   | Keep in app unless migration to ReBAC is intentional |
| OAuth scopes for Connected Apps | Descope Inbound App scopes / resource scopes         |

Flag this as high complexity only if the application has relationship-based or resource-instance-level checks. Identify resources, relationships, inheritance, where checks run, and whether the current model is stored in Stytch, in the app database, or both. **Effort: Medium–High** if migrating to ReBAC/FGA.

### Third-party provider tokens → Descope Outbound Apps

Stytch OAuth is primarily for authentication, but if your app stores or uses third-party provider tokens beyond login (e.g. to call Google, Microsoft, GitHub, or Slack APIs on a user's behalf), Descope [Outbound Apps](https://docs.descope.com/identity-federation/outbound-apps) store and refresh those tokens. Users connect accounts via `sdk.outbound.connect(appId, { redirectURL, scopes })` on the client; backends fetch tokens via the Management API:

```
POST https://api.descope.com/v1/mgmt/outbound/app/user/token
Authorization: Bearer {projectId}:{managementKey}
Body: { "appId": "google-calendar", "userId": "U2abc...", "scopes": [...] }
```
([ref](https://docs.descope.com/identity-federation/outbound-apps/using-outbound-apps#fetching-outbound-apps-tokens))

If the app only uses social login for sign-in and never calls provider APIs afterward, no Outbound Apps work is needed.

### Fewer network round-trips at login

Both Stytch and Descope authenticate client-side, so neither requires server-side redirect round-trips for the auth ceremony. Descope's [web component](https://docs.descope.com/client-sdk/descope-components#descope-component) handles sign-in in one step: the component loads in the browser, the user authenticates against Descope's API, and the component sets `DS`/`DSR` cookies. The backend is contacted only for subsequent API calls that need [token validation](https://docs.descope.com/authorization/session-management/session-validation/backend).

### Stytch vs Descope flow comparison

```
Stytch (embedded SDK):
  Browser → Stytch UI / headless client → Stytch API authenticates → session_token / session_jwt stored → app reads session

Descope (all variants):
  Browser → /login page → Descope web component renders → user authenticates → DS/DSR cookies set → redirect
  (Backend participates only when validating tokens on subsequent requests)
```

### User migration: Stytch export → Descope import

Stytch users don't automatically carry over. For production apps with existing users, this is a critical migration step.

**Export from Stytch first.** See Stytch's [Exporting from Stytch](https://stytch.com/docs/resources/migrations/exporting-from-stytch#consumer-auth) guide: Consumer projects use the [Search users](https://stytch.com/docs/api-reference/consumer/api/users/search-users) API (or the [stytch-node-export-users](https://github.com/stytchauth/stytch-node-export-users) utility for CSV/JSON export); B2B projects use [Search Organizations](https://stytch.com/docs/api-reference/b2b/api/organizations/search-organizations) and [Search Members](https://stytch.com/docs/api-reference/b2b/api/members/search-members). For password hashes or biometric public keys, contact [support@stytch.com](mailto:support@stytch.com) — Stytch does not expose hashed passwords through self-serve export.

Descope has a general [migration guide](https://docs.descope.com/migrate) with two approaches:
- **Full migration:** Import the Stytch export into Descope using the [Create User API](https://docs.descope.com/api/management/users/create-user) or [Batch Create User API](https://docs.descope.com/api/management/users/batch-create-users). See the [user format JSON guide](https://docs.descope.com/migrate/custom/user-format-json) for the expected shape. Descope can import bcrypt, Argon2, PBKDF2, Firebase, Django, PHPass, and MD5 password hashes — confirm what Stytch provides before committing to a password-carryover plan. If hashes aren't available, plan a password reset on first login or use the JIT approach below.
- **Hybrid migration (just-in-time):** Keep Stytch running alongside Descope during a transition period. New logins go through Descope; existing users are migrated on first login (verify their credentials against Stytch via a connector/API, then create the user in Descope). This avoids a big-bang cutover but requires both systems running simultaneously.

Key fields to map: Stytch `user_id` / `member_id` → Descope `loginId` (or `userId`), `email`, `name`, `trusted_metadata` / `untrusted_metadata` → `customAttributes`.

If the Stytch app uses Organizations, map each organization's member list to Descope tenant associations during import. See also [session migration](https://docs.descope.com/migrate/session-migration) to avoid forcing re-login at cutover.

### M2M authentication: Stytch client credentials → Descope Access Keys

Stytch [M2M](https://stytch.com/docs/api/m2m-overview) authentication uses M2M clients: a backend service authenticates with a `client_id` + `client_secret` (client credentials) and receives a scoped access token.

Descope's equivalent is [Access Keys](https://docs.descope.com/management/m2m-access-keys). An access key is exchanged for a JWT, which is then validated by the receiving service the same way a user session token is validated. Access keys can be scoped to tenants and roles, and can have IP restrictions and expiration times.

| Stytch | Descope |
|---|---|
| Create M2M client in dashboard/API | Create Access Key in Console → [Access Keys tab](https://app.descope.com/accessKeys) |
| `client_id` + `client_secret` | Access Key ID + Secret (returned once at creation) |
| Token endpoint with `grant_type=client_credentials` | `descopeClient.auth.exchangeAccessKey(accessKey)` ([ref](https://docs.descope.com/management/m2m-access-keys)) |
| Token scoped via M2M scopes | JWT with tenant/role claims (configure via Access Key settings) |
| Token validated via Stytch / JWKS | Token validated via `descopeClient.validateSession()` — same as user tokens |

Access keys can also be created programmatically via `descopeClient.management.accessKey.create()`.

### Email templates: Stytch → Descope messaging templates

Stytch email templates (magic link, OTP, password reset, invitation) are configured and customized in the Stytch dashboard.

Descope uses [Messaging Templates](https://docs.descope.com/management/messaging-templates) configured per authentication method. Templates support HTML and dynamic content via `{{}}` placeholders.

| Email type | Stytch location | Descope location |
|---|---|---|
| Magic Link / OTP | Stytch Dashboard → email customization | Console → Settings → Authentication Methods → [Magic Link](https://docs.descope.com/auth-methods/magic-link/settings) or OTP → select connector → + New Template |
| Password Reset | Stytch Dashboard → email customization | Console → Settings → Authentication Methods → [Passwords](https://docs.descope.com/auth-methods/passwords/settings) → Reset Password Email |
| Member Invitation | Stytch Dashboard → email customization | Console → [Project Settings → Sign Ups and User Invitations](https://docs.descope.com/management/project-settings#general-settings) → select connector → + New Template |
| Verification | Stytch Dashboard → email customization | Handled within Flows (email verification is a Flow step, not a standalone email) |

Descope also supports SMS and voice templates for OTP delivery, configured the same way via messaging connectors.

### Webhooks / events: Stytch → Descope Audit Webhook

Stytch [webhooks](https://stytch.com/docs/workspace-management/webhooks) forward events (user/member create, session changes, etc.) to your endpoints.

Descope's equivalent is the [Audit Webhook Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook). It streams audit events to your own HTTP endpoint. Configure it in the Console under Connectors → Audit Webhook with a base URL and authentication (Bearer, API Key, or Basic Auth).

Descope also has a built-in [Audit Trail](https://docs.descope.com/audit) in the Console for viewing events, and supports streaming to third-party services via connectors.

For apps that rely on Stytch webhooks for compliance, monitoring, or downstream sync, set up the Audit Webhook Connector before cutover to avoid gaps in event logging.

### Custom domains

Stytch supports custom domains for login and email/magic-link URLs instead of Stytch-hosted defaults.

Descope supports [custom domains](https://docs.descope.com/how-to-deploy-to-production/custom-domain) as well:
1. Create a CNAME record (e.g. `auth.example.com`) pointing to `cname.descope.com` (US) or `CNAME.euc1.descope.com` (EU).
2. Set the App URL in Console → Project Settings → General.
3. Add and verify the custom domain in Console.
4. Pass the custom domain as `baseUrl` to the Descope SDK/component: `<AuthProvider projectId="..." baseUrl="https://auth.example.com">`.

If the Stytch app uses a custom domain, plan this before cutover so cookies and redirects work correctly on the production domain.

### Attack protection: Stytch Fraud & Risk → Descope Flow-based security

Stytch [Device Fingerprinting / Fraud & Risk](https://stytch.com/docs/fraud) provides bot detection and verdict-based decisioning (allow, challenge, block, monitor) embedded in auth calls.

Descope handles these through [Flows](https://docs.descope.com/flows) and security connectors, giving more granular control but requiring explicit configuration:

| Stytch capability | Descope equivalent |
|---|---|
| Device Fingerprinting / bot detection | Flow step using [Arkose Bot Manager connector](https://www.descope.com/blog/post/arkose-labs-connector), [Google reCAPTCHA Enterprise](https://docs.descope.com/connectors), or [Fingerprint](https://docs.descope.com/connectors) |
| Credential-stuffing / brute-force defense | Flow conditional logic + connector-based risk signals; rate limiting on Descope's infrastructure |
| Breached-password detection | [Have I Been Pwned integration](https://docs.descope.com/connectors) — blocks credentials found in known breaches |
| IP / geo restrictions | Flow step using [AbuseIPDB connector](https://docs.descope.com/connectors) or IP-based conditional logic |

Stytch attaches verdicts to SDK auth calls. Descope's is composable — you add detection steps to your Flow and configure the response (block, challenge with MFA, allow with logging). Recreate Stytch's verdict-driven decisions as Flow branches.

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

## Express.js


**Changes:**
- Removed the [`stytch`](https://github.com/stytchauth/stytch-node) (stytch-node) session-authentication code. Added [`@descope/node-sdk`](https://github.com/descope/node-sdk) and `cookie-parser`.
- Replaced custom middleware calling `client.sessions.authenticateJwt()` with ~20 lines that validate the `DS` cookie via [`validateSession()`](https://docs.descope.com/getting-started/nodejs#implement-session-validation).
- Added `/login` route rendering an EJS page with [`<descope-wc>`](https://docs.descope.com/client-sdk/descope-components#descope-component).
- Logout changed from a route calling Stytch `sessions.revoke()` to a POST calling [`descopeClient.logout()`](https://docs.descope.com/authorization/session-management/session-validation/backend#logout-current-session-using-backend-sdk) + cookie clearing.
- `requiresAuth()` is a custom 3-line function.

**Notes:**
- Descope needs no server-side OAuth/callback config since there's no server-side OAuth flow.
- Stytch's authenticated-session response (`member` / `session` objects) becomes Descope's `authInfo.token` after [`validateSession()`](https://docs.descope.com/authorization/session-management/session-validation/backend#validate-session), which holds decoded JWT claims of the session token.

**Limitation:**
- The Descope web component requires JavaScript (as does Stytch's embedded UI).

---

## Flask / Python


**Changes:**
- Removed the [`stytch`](https://github.com/stytchauth/stytch-python) (stytch-python) auth/session usage; added [`descope`](https://github.com/descope/python-sdk).
- Removed Stytch OAuth/magic-link start + authenticate calls and any redirect-based flow code.
- Removed the token/callback route. No code exchange needed.
- `/login` renders a template with the [Descope web component](https://docs.descope.com/client-sdk/descope-components#descope-component) instead of the Stytch UI/headless flow.
- `/logout` changed from Stytch session revocation to [`descope_client.logout(refresh_token)`](https://docs.descope.com/authorization/session-management/session-validation/backend#logout-current-session-using-backend-sdk) + cookie deletion.
- Home route reads `DS` cookie from `request.cookies`, validates with [`descope_client.validate_session()`](https://docs.descope.com/getting-started/python#implement-session-validation).

**Notes:**
- If the app stored Stytch session state in Flask's server-side `session`, Descope doesn't use it — state lives in client-side cookies. You can drop `session` from Flask imports; `APP_SECRET_KEY` becomes optional.
- `validate_session` returns a dict-like object. JWT standard claims (`sub`, `name`, `email`) are present. Custom claims from [Descope's JWT Templates](https://docs.descope.com/management/jwt-templates) also appear here.
- The `descope` Python SDK requires Python 3.7+.

**Limitation:**
- Descope's Python SDK docs don't detail `validate_session()`'s return type beyond "jwt_response." It's a dict with JWT claims in practice, but official type annotations lag behind. Ref: [Descope Python SDK](https://github.com/descope/python-sdk), [Python quickstart](https://docs.descope.com/getting-started/python).

---

## Next.js (standalone)


**Changes:**
- [`@stytch/nextjs`](https://www.npmjs.com/package/@stytch/nextjs) → [`@descope/nextjs-sdk`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk).
- `StytchProvider` → [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#auth-provider) (takes `projectId` prop; must use the `NEXT_PUBLIC_` prefix).
- `useStytchUser()` / `useStytchSession()` → [`useSession()`](https://docs.descope.com/client-sdk/auth-helpers#booleans) + [`useUser()`](https://docs.descope.com/client-sdk/auth-helpers#core-sdk-functions) (Descope separates session state from user data).
- Removed the Stytch magic-link / OAuth token callback handling. With Descope there's no server-side OIDC handling at all.
- Added `pages/login.tsx` with [`<Descope>` component](https://docs.descope.com/client-sdk/descope-components#descope-component) rendering the `sign-up-or-in` flow.
  - **`onSuccess` is required for redirect** — the component does not auto-navigate after login. Without it, the user finishes auth and stays on the login page:
    ```tsx
    const router = useRouter()
    <Descope
      flowId="sign-up-or-in"
      onSuccess={() => router.push('/dashboard')}
      onError={(e) => console.error(e)}
    />
    ```
- Client-side route protection: a manual `useSession()` check + redirect to `/login` (no HOC).
- Server-side route protection: server-side `session()` + manual 401 response. Descope's Next.js SDK exposes [`session()`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#server-side) for this.
- Logout changed from the Stytch client logout to a button calling [`sdk.logout()`](https://docs.descope.com/client-sdk/auth-helpers#logout) via [`useDescope()`](https://docs.descope.com/client-sdk/auth-helpers#core-sdk-functions).

**Notes:**
- Descope's Next.js SDK has no route-protection HOC. You check `isAuthenticated` from `useSession()` and redirect yourself. More verbose, more explicit.
- `NEXT_PUBLIC_` prefix is required on the project ID because [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#auth-provider) runs client-side.
- **Client vs. server session access:** `session()` from `@descope/nextjs-sdk/server` is for server components, server actions, and API routes **only**. In React client components, use `useSession()` + `useUser()` from `@descope/nextjs-sdk/client`. Using `session()` in a client component compiles but throws at runtime (attempts to read cookies in a browser context). Scan for this pattern before finishing any Next.js migration.
- Both CSR and SSR protected pages are preserved: client-side uses `useSession()`, server-side uses `session()` from the [Next.js SDK server helpers](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#server-side).
- For API routes, call `session()` at handler top and return 401 yourself.
- User shape: Stytch's `member` / `user` object fields (`member_id`, `email_address`, etc.) become Descope JWT claims; `member_id` / `user_id` → `userId`.

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

The correct replacement for a server-side session read (server component, no req argument) is `session`, not `getServerSession`. The name was invented by analogy, not verified.

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

The migration generated a `DescopeSession` interface shaped like a Stytch-style session object:
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
- `isAuthenticated` — not present. `undefined` return means unauthenticated; a non-null object means authenticated.
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
2. **Return type:** `session()` returns `AuthenticationInfo | undefined` from `@descope/node-sdk`, not a boolean-flagged session object.
3. **isAuthenticated:** Does not exist on `AuthenticationInfo`. Unauthenticated = `undefined`; authenticated = non-null object.
4. **claims vs token:** Decoded JWT claims are under `.token` (a `Token` object), not `.claims`. Raw JWT string is under `.jwt`.
5. **Next.js version:** Check `package.json` for Next.js ≥ 15. If so, `cookies()` and `headers()` from `next/headers` are async — all consumers must be async.
6. **Async cascade:** Tracing async upward from `cookies()` may require updating 10+ files. Plan for it.

---

## Next.js (with separate Express API server)


**Changes:**
- [`@stytch/nextjs`](https://www.npmjs.com/package/@stytch/nextjs) + [`stytch`](https://github.com/stytchauth/stytch-node) (node) → [`@descope/nextjs-sdk`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk) + [`@descope/node-sdk`](https://github.com/descope/node-sdk) (two packages: client SDK for Next.js, node SDK for the API server).
- The Stytch backend client → singleton `getDescopeClient()` using `@descope/node-sdk`.
- Stytch frontend provider/session → Descope `AuthProvider` + Next.js middleware using Descope's [`authMiddleware()`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#middleware) to check the `DS` cookie and redirect unauthenticated users.
- Express API server (`api-server.js`): replaced Stytch `session_jwt` validation (Stytch JWKS / `sessions.authenticateJwt()`) with `@descope/node-sdk` [`validateSession()`](https://docs.descope.com/authorization/session-management/session-validation/backend#validate-session).
- Added `/login` page with [`<Descope>` React component](https://docs.descope.com/client-sdk/descope-components#descope-component).

**Token forwarding changes:**
Where the app forwarded a Stytch `session_jwt` to the external API as a Bearer token, it now forwards the Descope `DS` session token. The Next.js API route reads `DS` from cookies and forwards it as `Authorization: Bearer <DS>`. The API server validates it with `descopeClient.validateSession(token)`.

For audience validation with Descope, configure a custom `aud` claim in the Descope Console's [JWT Templates](https://docs.descope.com/management/jwt-templates) and pass the `audience` parameter to [`validateSession()`](https://docs.descope.com/getting-started/nodejs#implement-session-validation).

**Notes:**
- The Stytch frontend SDK handled the auth ceremony and session; in Descope that moves to [Descope Flows](https://docs.descope.com/flows), and `DescopeClient` on the server just validates JWTs against [cached public keys](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation).
- Descope's Node SDK fetches and caches JWKS from `https://api.descope.com/v2/keys/<project_id>` ([ref](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation#finding-your-public-key)). No configuration needed.
- The Descope API-server validation is ~15 lines of middleware calling `validateSession()`.

**Limitation:**
- If the original API server validated an `audience` claim (ensuring the token targeted this API), replicate it: (1) configure `aud` in [Descope's JWT Templates](https://docs.descope.com/management/jwt-templates), (2) pass `audience` to `validateSession()` ([Node SDK docs](https://docs.descope.com/getting-started/nodejs#implement-session-validation)). Descope's `validateSession()` skips audience by default. Easy to miss during migration.

---

## Go + Encore


**Changes:**
- Backend simplified: the Stytch session-authentication endpoints → 1 endpoint (AuthHandler, ~25 lines) validating DS session tokens with the [Descope Go SDK](https://github.com/descope/go-sdk).
- Removed the Stytch Go session/auth setup. Not needed.
- Frontend removed its Stytch auth routes. Replaced with a `/login` page containing the [`<Descope>` component](https://docs.descope.com/client-sdk/descope-components#descope-component) and a client-side `LogoutButton` using [`useDescope().logout()`](https://docs.descope.com/client-sdk/auth-helpers#logout).
- `getRequestClient.ts` reads the `DS` cookie instead of a custom `auth-token` cookie.
- Generated Encore client (`client.ts`) simplified: the Stytch auth service methods are removed since those backend endpoints are gone.

**Two-process architecture:**
With Descope, auth is client-side. The Go backend validates tokens only — a pure API; the frontend owns auth UX (the Descope Flow).

Cookie name changed from `auth-token` (custom) to `DS` (Descope standard). `getRequestClient.ts` extracts this and passes it as a Bearer token in the `Authorization` header. Encore's [`//encore:authhandler`](https://encore.dev/docs/go/primitives/defining-apis#access-controls) intercepts it.

**Notes:**
- Go SDK constructor: `client.NewWithConfig(&client.Config{ProjectID: "..."})`. Session validation: [`descopeClient.Auth.ValidateSessionWithToken(ctx, token)`](https://docs.descope.com/getting-started/go#implement-session-validation) returns `(bool, *descope.Token, error)`. `Token.Claims` is `map[string]interface{}`. Ref: [Descope Go SDK](https://github.com/descope/go-sdk).
- Encore's `//encore:authhandler` expects `(auth.UID, error)`. Descope's JWT `sub` claim maps to `auth.UID`.
- `encore.cue` config: Stytch `project_id` + `secret` → Descope `ProjectID` only.
- `go.mod`: [`stytch-go`](https://github.com/stytchauth/stytch-go) → [`descope/go-sdk`](https://github.com/descope/go-sdk).

**Limitation:**
- The Go SDK's exported type names (`client.DescopeClient`, `descope.Token`) aren't documented in Descope's official docs. The [Go quickstart](https://docs.descope.com/getting-started/go) shows usage patterns, not Go type signatures. Types in this migration are inferred from [Go SDK README](https://github.com/descope/go-sdk#readme) examples; verify against `go doc` output.
- Encore's `//encore:service` init pattern (`initService()`) creates the Descope client at service startup. If Encore's lifecycle skips `initService`, the client won't exist.
