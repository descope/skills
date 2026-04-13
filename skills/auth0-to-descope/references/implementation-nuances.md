# Descope Migration: Implementation Notes

## General Insights

### Auth0 owns the flow; Descope validates tokens

Auth0's server-side SDKs ([express-openid-connect](https://github.com/auth0/express-openid-connect), [@auth0/nextjs-auth0](https://github.com/auth0/nextjs-auth0), [authlib](https://docs.authlib.org/en/latest/client/flask.html)) own the OIDC flow: they mount callback routes, handle code exchange, create server-managed sessions, and provide middleware that gates routes. Developers never touch tokens.

Descope splits the work. The frontend ([Descope Flows](https://docs.descope.com/flows) via [web components](https://docs.descope.com/client-sdk/descope-components) or [client SDKs](https://docs.descope.com/client-sdk/initialize-sdk)) runs the authentication ceremony and stores JWTs in `DS` (session) and `DSR` (refresh) cookies. The backend [validates those JWTs](https://docs.descope.com/authorization/session-management/session-validation/backend). No server-side OAuth callback, no authorization code exchange, no server-managed session store.

Every Auth0→Descope migration adds a dedicated login page (or embeds the [`<descope-wc>` component](https://docs.descope.com/client-sdk/descope-components#descope-component)) and removes callback/redirect plumbing.

**Exception:** Descope can also act as a [standard OIDC provider](https://docs.descope.com/getting-started/oidc-endpoints). If you want to keep your existing OIDC client code (e.g., `express-openid-connect`, `go-oidc`, `authlib`), you can point it at Descope's OIDC endpoints instead of Auth0's. See the "OIDC compatibility path" section below.

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

An app using `express-openid-connect` could swap `ISSUER_BASE_URL` from `https://YOUR_AUTH0_DOMAIN` to `https://api.descope.com` and keep the existing OIDC client code intact. Differences in claim shapes (`nickname`, `email_verified` vs `verifiedEmail`), token lifetimes, and configuration semantics mean the OIDC swap still requires testing and adjustments. Still, it's a viable incremental path: swap the IdP first, then refactor to Descope-native SDKs later.

### No drop-in middleware for Express or Flask

Auth0 offers [`express-openid-connect`](https://github.com/auth0/express-openid-connect), a single `app.use(auth(config))` that [auto-mounts `/login`, `/logout`, `/callback`](https://github.com/auth0/express-openid-connect#readme) and attaches `req.oidc`. Descope has no Express middleware package. You:

1. Add `cookie-parser` (Express doesn't parse cookies by default; Auth0's middleware handled it internally).
2. Write custom middleware: read `DS` cookie → call [`descopeClient.validateSession()`](https://docs.descope.com/authorization/session-management/session-validation/backend#validate-session) → attach user claims to `req`.
3. Write your own `requiresAuth()` guard (3 lines, but manual).

The [Descope blog](https://www.descope.com/blog/post/authentication-middleware) shows an Express middleware pattern, but it's a tutorial example, not a published package.

Flask is the same story. Auth0's [authlib Flask integration](https://docs.authlib.org/en/latest/client/flask.html) registers an OAuth client with `authorize_redirect` / `authorize_access_token` helpers. Descope's Flask backend [validates tokens](https://docs.descope.com/getting-started/python) only; auth UI is client-side.

FastAPI follows the same pattern. Auth0 has [`auth0-fastapi`](https://github.com/auth0/auth0-fastapi), which provides `AuthConfig`, session middleware, auto-mounted `/auth/*` routes, a `require_session` dependency, and Token Vault / Connected Accounts support. Descope's equivalent is a [custom JWT authorizer using JWKS validation](https://docs.descope.com/authorization/session-management/session-validation/oidc-jwt-authorizers/python-fastapi-jwt-authorizer): a `TokenVerifier` class that reads the `Authorization` header, validates against Descope's JWKS, and attaches as a FastAPI `Security()` dependency. No auto-mounted routes, no session store.

### Cookie names: `DS` and `DSR` (configurable)

Descope web components and client SDKs default to `DS` for the session JWT and `DSR` for the refresh JWT. The [Node SDK README](https://github.com/descope/node-sdk#session-validation-using-middleware) references `DescopeClient.SessionTokenCookieName` and `DescopeClient.RefreshTokenCookieName` as constants.

These names are configurable. The [End action in Descope Flows](https://docs.descope.com/flows/actions/end-action#session-cookie-name) has "Session Cookie Name" and "Refresh Cookie Name" fields that override the defaults. Use custom names when running multiple Descope projects on the same root domain to avoid cookie collisions. Backend code must then read the custom cookie name instead of `DS`/`DSR`.

The `sessionTokenViaCookie` parameter in [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#cookie-configuration-options) controls whether the session token is set as a cookie at all (vs. managed in-memory by the SDK).

### User claims differ

The default Descope session JWT ([structure ref](https://docs.descope.com/authorization/session-management#descope-session-jwt-structure)) contains `sub`, `amr`, `drn`, `tenants`, `roles`, and `permissions`. It does **not** include `email`, `name`, or `picture` unless you add them via [JWT Templates](https://docs.descope.com/management/jwt-templates) or [Flow actions > Custom Claims](https://docs.descope.com/flows/actions/custom-claims). Auth0 ID tokens include these by default.

| Field | Auth0 | Descope |
|---|---|---|
| User ID | `sub` (e.g., `auth0\|abc123`) | `sub` in JWT, `userId` in SDK user objects |
| Display name | `name`, `nickname` | Not in JWT by default. Add via [JWT Templates](https://docs.descope.com/management/jwt-templates). No `nickname` equivalent. |
| Email | `email` | Not in JWT by default. Add via JWT Templates. Available on user object via SDK management calls. |
| Profile picture | `picture` | Not in JWT by default. Add via JWT Templates. |
| Email verified | `email_verified` | Not in JWT by default. Available on user object as `verifiedEmail`. Add to JWT via Custom Claims if needed. |
| Roles | Via `https://DOMAIN/roles` namespace claim (added by Auth0 Actions) | `roles` array in JWT (embedded by default with [RBAC](https://docs.descope.com/authorization/role-based-access-control)) |
| Permissions | Via namespace claim or `permissions` array (added by Actions) | `permissions` array in JWT (embedded by default) |
| Tenant | `org_id` (Auth0 Organizations) | `tenants` object with per-tenant roles ([ref](https://docs.descope.com/authorization/role-based-access-control#tenants-and-roles)) |

`nickname` is Auth0-specific (derived from the email prefix). Descope lacks it. Fall back to `name`.

**Migration action item:** Before migrating, configure a JWT Template that includes `email`, `name`, and any other profile claims your app reads from the token. Without this, code that reads `token.email` or `token.name` after `validateSession()` will get `undefined`.

### Audience validation requires explicit setup

Auth0 projects commonly set `AUTH0_AUDIENCE` to scope access tokens to a specific API. The access token's `aud` claim is validated by the API server (via `express-jwt`, `go-oidc`, etc.).

Descope session tokens don't include an `aud` claim by default. To replicate Auth0's audience validation:
1. Configure a custom `aud` claim in the Descope Console's [JWT Templates](https://docs.descope.com/management/jwt-templates).
2. Pass the `audience` parameter to [`validateSession()`](https://docs.descope.com/getting-started/nodejs#implement-session-validation) on the backend.

This is easy to miss during migration. Without it, any valid Descope session token from any project would pass validation. The audience check prevents cross-project token reuse.

### Auth0 separate access tokens → Descope session token reuse

Auth0's architecture issues separate access tokens (scoped to an `audience`) distinct from the ID token. The Next.js SDK's `getAccessToken()` returns this access token for API calls.

Descope has one token: the session JWT (`DS` cookie). When calling a backend API, you forward the `DS` cookie value as `Authorization: Bearer <DS>`. The API server validates it with `descopeClient.validateSession(token)`. No separate token endpoint, no audience-scoped token issuance. If you need audience differentiation, use [JWT Templates](https://docs.descope.com/management/jwt-templates).

### Logout requires two steps

Auth0's `express-openid-connect` [redirects to Auth0's `/v2/logout`](https://github.com/auth0/express-openid-connect#readme) (clears the Auth0 session), then back to the app. `@auth0/nextjs-auth0` does the same via its API route.

Descope logout ([backend](https://docs.descope.com/authorization/session-management/session-validation/backend#logout-current-session-using-backend-sdk) / [client](https://docs.descope.com/client-sdk/auth-helpers#logout)):
1. Call `descopeClient.logout(refreshToken)` (server-side) or `sdk.logout()` (client-side) to invalidate the refresh token.
2. Clear the `DS` and `DSR` cookies.

Clear cookies without calling logout → the refresh token stays valid on Descope's servers. Call logout without clearing cookies → the client holds a dead session token that fails validation but confuses client-side state.

### One env var instead of five

Auth0 needs `CLIENT_ID`, `CLIENT_SECRET`, `ISSUER_BASE_URL`/`AUTH0_DOMAIN`, `SECRET`, and sometimes `AUTH0_AUDIENCE`. See the [express-openid-connect configuration](https://github.com/auth0/express-openid-connect#readme) for the full list.

Descope needs `DESCOPE_PROJECT_ID` (or `NEXT_PUBLIC_DESCOPE_PROJECT_ID` for Next.js client-side). No client secret for frontend flows. The web component authenticates against Descope's API using the project ID. Backend SDKs [fetch the public key](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation#finding-your-public-key) from Descope's JWKS endpoint (`https://api.descope.com/v2/keys/<project_id>`) using the same project ID. No secrets to rotate for the auth flow.

For management operations (user CRUD, role management, FGA), add `DESCOPE_MANAGEMENT_KEY`.

### Auth0 Actions/Rules → Descope Flows + JWT Templates

Auth0 uses [Actions](https://auth0.com/docs/customize/actions) (and legacy Rules/Hooks) to run custom code at specific points in the authentication pipeline: post-login, pre-registration, and others. Common uses include enriching tokens with custom claims, blocking logins based on business logic, and assigning roles.

Descope equivalent:
- **Custom claims:** [JWT Templates](https://docs.descope.com/management/jwt-templates) to add static/dynamic claims to tokens, or [Flow actions > Custom Claims](https://docs.descope.com/flows/actions/custom-claims) for claims set during the auth flow.
- **Custom logic during auth:** [Descope Flows](https://docs.descope.com/flows) are visual, drag-and-drop pipelines. Conditional branching, connectors to external services, and custom JS actions replace Auth0 Actions. Flows run on Descope's servers, not as arbitrary Node.js code.
- **Post-login hooks:** Descope Flows can call external HTTP endpoints ([Connectors](https://docs.descope.com/customize/connectors)) for webhook-style behavior.

Auth0 Actions are imperative Node.js code. Descope Flows are declarative and visual, with escape hatches to custom code via Connectors and JS actions. You'll need to restructure auth-time business logic around the visual pipeline model.

### `authRequired: false` needs manual replication

Auth0's `express-openid-connect` supports [`authRequired: false`](https://github.com/auth0/express-openid-connect#readme) globally: unauthenticated users browse freely, the middleware skips populating `req.oidc.user`. Descope equivalent: your session middleware catches validation errors and sets `req.isAuthenticated = false` instead of returning 401.

### Social login / connection mapping

Auth0 [Social Connections](https://auth0.com/docs/authenticate/identity-providers/social-identity-providers) (Google, GitHub, Facebook, etc.) are configured in the Auth0 dashboard and appear automatically on the Universal Login page.

Descope equivalent: configure [social auth methods](https://docs.descope.com/authentication/social) in the Descope Console, then add them to a [Flow](https://docs.descope.com/flows). The Descope web component renders the configured providers. No code changes needed; configuration only.

SAML/OIDC enterprise connections in Auth0 map to Descope's [SSO configuration](https://docs.descope.com/sso) (per-tenant SSO for B2B). Auth0 Organizations' per-org connections map to Descope's per-tenant SSO settings.

### RBAC: Auth0 → Descope

Auth0 RBAC: create permissions, create roles, assign roles to users. Roles/permissions can be added to access tokens via Auth0 Actions or the Authorization Extension.

Descope RBAC ([docs](https://docs.descope.com/authorization/role-based-access-control)): same concept, but permissions are always grouped into roles, and roles can be project-level or tenant-level. Roles/permissions are embedded in the JWT by default (no Action required). Descope SDK methods:
- `descopeClient.management.permission.create(name, description)` ([ref](https://docs.descope.com/authorization/role-based-access-control/with-sdks))
- `descopeClient.management.role.create(name, description, permissionNames, tenantId)` ([ref](https://docs.descope.com/authorization/role-based-access-control/with-sdks))
- Roles appear in the JWT `roles` array; permissions in `permissions` array.

Backend code checking Auth0's `req.auth.permissions.includes('read:messages')` changes to reading the `permissions` array from Descope's validated JWT claims.

### Multi-tenancy: Auth0 Organizations → Descope Tenants

Auth0 [Organizations](https://auth0.com/docs/manage-users/organizations) group users by company. The `org_id` claim identifies the organization.

Descope [Tenants](https://docs.descope.com/b2b#multi-tenancy) are the equivalent. Users can belong to multiple tenants with different roles per tenant. The JWT includes a `tenants` object with per-tenant role/permission data ([ref](https://docs.descope.com/authorization/role-based-access-control#tenants-and-roles)).

Key differences:
- Auth0: `org_id` is a flat string claim. Descope: `tenants` is a nested object (`{ "tenantId": { "roles": [...], "permissions": [...] } }`).
- Auth0 requires organization-scoped login via `organization` parameter. Descope routes by email domain or tenant-specific login URLs ([ref](https://docs.descope.com/sso/multi-sso)).
- Descope supports tenant-level SSO enforcement (require SAML/OIDC for all users in a tenant) ([ref](https://docs.descope.com/management/tenant-management/tenant)).
- Users are project-level entities in Descope; they're associated with tenants, not created per-tenant.
- Auth0's org-scoped login issues a JWT with one `org_id`. Descope's JWT contains **all** tenants the user belongs to at once. Switching tenants does not require re-authentication — implement it client-side (e.g. an `active_tenant` cookie) and read the active tenant from the `tenants` object in the JWT.
- When a tenant is created and the user is added via the Management SDK, the existing JWT is stale — the `tenants` claim was set at login and doesn't include the new tenant. The user must re-authenticate (clear `DS`/`DSR` cookies and redirect to login) to get a JWT with the updated tenant list. Without this, the app sees an empty `tenants` claim and may loop back to onboarding.

### Invitation model: Auth0 invitations → Descope user.invite()

Auth0 Organizations have a dedicated invitation system with invitation objects, URLs, and CRUD operations. An invited user doesn't exist until they accept.

Descope's `management.user.invite()` creates a user record immediately in `"invited"` status and sends an invitation email. There is no separate invitation object to list, update, or revoke independently. To list pending invitations for a tenant, filter users by `status === "invited"`. To revoke an invitation, delete the user.

### SCIM: HTTP API only, not in SDK

Auth0 exposes SCIM configuration via the Management SDK (`managementClient.connections.createScimConfiguration()`, etc.). Descope supports SCIM but only via the HTTP API (`https://api.descope.com/v1/mgmt/scim/*`), not the Node.js or Python SDKs. Implement with raw `fetch()` calls. Verify the request/response shapes against the current API — the endpoints are documented but not SDK-wrapped.

### Session refresh after profile changes

Auth0's `appClient.updateSession()` lets you immediately reflect profile changes (e.g. display name) in the cached session without re-authentication. Descope has no equivalent — profile changes via the Management SDK don't update the JWT. The user must wait for token refresh (if using DSR), sign out and back in, or call `refresh()` from the client SDK. Plan for this if the app has a profile editing flow that expects immediate UI updates.

### Management API mapping

Auth0's [Management API](https://auth0.com/docs/api/management/v2) is REST-based, accessed with an M2M token.

Descope uses a Management SDK initialized with a `managementKey` ([Node SDK](https://github.com/descope/node-sdk), [Python SDK](https://github.com/descope/python-sdk), [Go SDK](https://github.com/descope/go-sdk)).

| Operation | Auth0 | Descope (Node.js) |
|---|---|---|
| Create user | `POST /api/v2/users` | `descopeClient.management.user.create(...)` ([ref](https://docs.descope.com/management/user-management/sdks)) |
| Update user | `PATCH /api/v2/users/{id}` | `descopeClient.management.user.update(...)` |
| Search users | `POST /api/v2/users` (with q param) | `descopeClient.management.user.search(...)` |
| Delete user | `DELETE /api/v2/users/{id}` | `descopeClient.management.user.delete(...)` |
| Load user | `GET /api/v2/users/{id}` | `descopeClient.management.user.load(...)` / `.loadByUserId(...)` |
| List permissions | `GET /api/v2/resource-servers/{id}` | `descopeClient.management.permission.loadAll()` |
| Create role | `POST /api/v2/roles` | `descopeClient.management.role.create(name, description, permissions, tenantId)` |

Auth0 M2M tokens expire and must be rotated. Descope management keys are long-lived (rotatable via the Console).

### FGA: Auth0 FGA (OpenFGA) → Descope ReBAC

Auth0 [Fine-Grained Authorization](https://fga.dev/) is built on [OpenFGA](https://openfga.dev/). Descope has its own [ReBAC](https://docs.descope.com/authorization/rebac) system with a similar model (types, relations, computed permissions) but a different API shape.

**Schema definition:**

OpenFGA uses a YAML/JSON model with `type_definitions`. Descope uses a [DSL](https://docs.descope.com/authorization/rebac/define-schema) saved via `descopeClient.management.fga.saveSchema(schema)` ([ref](https://docs.descope.com/authorization/rebac/implement-schema)).

**Operation mapping:**

| Operation | Auth0 FGA (OpenFGA SDK) | Descope ReBAC (Node SDK) |
|---|---|---|
| Write tuple | `fgaClient.write({ writes: [{ user, relation, object }] })` | `descopeClient.management.fga.createRelations([{ resource, resourceType, relation, target, targetType }])` ([ref](https://docs.descope.com/authorization/rebac/create-relations)) |
| Delete tuple | `fgaClient.write({ deletes: [...] })` | `descopeClient.management.fga.deleteRelations([...])` |
| Check | `fgaClient.check({ user, relation, object })` | `descopeClient.management.fga.check([{ resource, resourceType, relation, target, targetType }])` ([ref](https://docs.descope.com/authorization/rebac/check-relations)) |
| List objects | `fgaClient.listObjects({ user, relation, type })` | `descopeClient.management.authz.whatCanTargetAccessWithRelation(target, relation, namespace)` ([ref](https://docs.descope.com/authorization/rebac/check-relations)) |
| Who has access | `fgaClient.listUsers({ object, relation })` | `descopeClient.management.authz.whoCanAccess(resource, relation, namespace)` |

**Key differences:**
- OpenFGA tuples use `user`/`relation`/`object` (e.g., `user:alice`, `owner`, `doc:123`). Descope uses `target`/`targetType`/`relation`/`resource`/`resourceType`.
- OpenFGA's `buildOpenFgaClient()` (from `@auth0/ai`) uses separate FGA credentials (`FGA_STORE_ID`, `FGA_CLIENT_ID`, `FGA_CLIENT_SECRET`, `FGA_API_URL`). Descope ReBAC uses the same `DESCOPE_PROJECT_ID` + `DESCOPE_MANAGEMENT_KEY`.
- Auth0 FGA runs as a hosted OpenFGA instance. Descope ReBAC is integrated into the Descope platform.
- The `@auth0/ai-langchain` package provides `FGARetriever` that wraps a LangChain retriever with FGA batch-check filtering. No Descope equivalent exists. Build a custom retriever that calls `descopeClient.management.fga.check()` for each candidate document.

### Token Vault / Connected Accounts → Descope Outbound Apps

Auth0's [Token Vault](https://auth0.com/docs/secure/tokens/token-vault) stores third-party OAuth tokens (Google, GitHub, Slack) and exchanges them on demand. The `@auth0/ai-langchain` package wraps this with `withTokenVault()` for LangGraph tools. The `@auth0/nextjs-auth0` SDK's `enableConnectAccountEndpoint` auto-mounts `/auth/connect` for linking accounts.

Descope's equivalent: [Outbound Apps](https://docs.descope.com/identity-federation/outbound-apps). These store third-party OAuth tokens and static API keys. Tokens are retrieved via the Management API:

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

Users connect accounts via `sdk.outbound.connect(appId, { redirectURL, scopes })` on the client side ([ref](https://docs.descope.com/identity-federation/outbound-apps/connect)).

**Key differences:**
- Auth0 wraps token exchange into LangGraph tools via `@auth0/ai-langchain` with interrupt-based consent UI. Descope has no AI-framework SDK. You call the Outbound Apps API directly from your tool function.
- Auth0's Token Vault uses `subjectTokenType` for federated token exchange. Descope's API uses `appId` + `userId` lookup.
- Auth0's connected account management is scoped to `https://DOMAIN/me/` audience. Descope's is part of the Management API.

### CIBA / Rich Authorization Requests (no Descope equivalent)

Auth0 supports [CIBA](https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-initiated-backchannel-authentication-flow) (Client-Initiated Backchannel Authentication) for async authorization. The agent sends a push notification to the user's device, waits for approval, then receives a scoped token. The `@auth0/ai` SDK wraps this via `withAsyncAuthorization()`.

Descope does not offer CIBA or Rich Authorization Requests (RAR) as a product feature. Migrations that use `withAsyncAuthorization()` require a custom approval mechanism. One option: the agent creates a pending approval record, the frontend polls for it, and the user approves via a Descope Flow or custom UI.

### @auth0/ai SDK (no Descope equivalent)

Auth0 publishes [`@auth0/ai`](https://github.com/auth0/ai-sdks), [`@auth0/ai-langchain`](https://github.com/auth0/ai-sdks), and [`@auth0/ai-vercel`](https://github.com/auth0/ai-sdks). These SDKs wrap AI agent tools with:
- Token Vault credential injection (`withTokenVault()`)
- CIBA async authorization (`withAsyncAuthorization()`)
- FGA-aware RAG retrieval (`FGARetriever`, `FGAFilter`)
- Interrupt-based consent UI (`TokenVaultInterrupt`, `AccessDeniedInterrupt`)

Descope has no AI-framework SDKs. Descope's agentic offerings focus on [MCP server authentication](https://www.descope.com/press-release/agentic-identity-hub) (OAuth 2.1, tool-level scopes, client registration) rather than LangChain/Vercel AI tool wrapping.

For migration, each `@auth0/ai` wrapper must be reimplemented:
- `withTokenVault()` → custom wrapper calling Descope Outbound Apps API
- `withAsyncAuthorization()` → custom approval mechanism (see CIBA section above)
- `FGARetriever` → custom retriever calling `descopeClient.management.fga.check()` per document
- `TokenVaultInterrupt` → custom interrupt using LangGraph's `interrupt()` + frontend consent UI calling `sdk.outbound.connect()`

### Fewer network round-trips at login

Auth0's [authorization code flow](https://github.com/auth0/express-openid-connect#readme) (for server-rendered apps) requires at minimum 3 round-trips: browser to backend (get auth URL), browser to Auth0 (user signs in), Auth0 to backend callback (exchange code for tokens). The Encore sample added a fourth hop between the frontend and Go backend.

Descope's [web component](https://docs.descope.com/client-sdk/descope-components#descope-component) handles sign-in in one step: the component loads in the browser, the user authenticates against Descope's API, and the component sets `DS`/`DSR` cookies. No backend round-trips for the auth ceremony. The backend is contacted only for subsequent API calls that need [token validation](https://docs.descope.com/authorization/session-management/session-validation/backend).

### Auth0 vs Descope flow comparison

```
Auth0 (server-rendered):
  Browser → /login → Auth0 hosted page → /callback → code exchange → session created → redirect

Auth0 (Encore two-process):
  Browser → Next.js /auth/login → Go backend Login → Auth0 URL
  Browser → Auth0 hosted page → Next.js /callback → Go backend Callback → token exchange → cookie set

Descope (all variants):
  Browser → /login page → Descope web component renders → user authenticates → DS/DSR cookies set → redirect
  (Backend participates only when validating tokens on subsequent requests)
```

### User migration: Auth0 export → Descope import

Auth0 users don't automatically carry over. For production apps with existing users, this is a critical migration step.

Descope has a dedicated [Auth0 migration guide](https://docs.descope.com/migrate/auth0) with two approaches:
- **Full migration:** Export all users from Auth0 (via the Auth0 Management API or Dashboard export), then import them into Descope using the [Create User API](https://docs.descope.com/api/management/users/create-user) or [Batch Create User API](https://docs.descope.com/api/management/users/batch-create-users). Descope accepts bcrypt password hashes, so users can keep their existing passwords without a reset. Export as CSV or JSON; see the [user format JSON guide](https://docs.descope.com/migrate/custom/user-format-json) for the expected shape.
- **Hybrid migration (just-in-time):** Keep Auth0 running alongside Descope during a transition period. New logins go through Descope; existing users are migrated on first login. This avoids a big-bang cutover but requires both systems running simultaneously.

Key fields to map: Auth0 `user_id` → Descope `loginId` (or `userId`), `email`, `name`, `password` (as hash), `app_metadata` → `customAttributes`, `user_metadata` → `customAttributes`.

If the Auth0 app uses Organizations, map each organization's member list to Descope tenant associations during import.

### M2M authentication: Auth0 client credentials → Descope Access Keys

Auth0's [Client Credentials Grant](https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow) is used for machine-to-machine auth: a backend service authenticates with `CLIENT_ID` + `CLIENT_SECRET` and receives an access token scoped to an `audience`.

Descope's equivalent is [Access Keys](https://docs.descope.com/management/m2m-access-keys). An access key is exchanged for a JWT, which is then validated by the receiving service the same way a user session token is validated. Access keys can be scoped to tenants and roles, and can have IP restrictions and expiration times.

| Auth0 | Descope |
|---|---|
| Create M2M app in Dashboard | Create Access Key in Console → [Access Keys tab](https://app.descope.com/accessKeys) |
| `CLIENT_ID` + `CLIENT_SECRET` | Access Key ID + Secret (returned once at creation) |
| `POST /oauth/token` with `grant_type=client_credentials` | `descopeClient.auth.exchangeAccessKey(accessKey)` ([ref](https://docs.descope.com/management/m2m-access-keys)) |
| Token scoped to `audience` | JWT with tenant/role claims (configure via Access Key settings) |
| Token validated via `express-jwt` / JWKS | Token validated via `descopeClient.validateSession()` — same as user tokens |

Access keys can also be created programmatically via `descopeClient.management.accessKey.create()`.

### Email templates: Auth0 → Descope messaging templates

Auth0 email templates (verification, password reset, invitation, blocked account) are configured in the Auth0 Dashboard under Branding → Email Templates.

Descope uses [Messaging Templates](https://docs.descope.com/management/messaging-templates) configured per authentication method. Templates support HTML and dynamic content via `{{}}` placeholders.

| Email type | Auth0 location | Descope location |
|---|---|---|
| Magic Link / OTP | Dashboard → Branding → Email Templates | Console → Settings → Authentication Methods → [Magic Link](https://docs.descope.com/auth-methods/magic-link/settings) or OTP → select connector → + New Template |
| Password Reset | Dashboard → Branding → Email Templates | Console → Settings → Authentication Methods → [Passwords](https://docs.descope.com/auth-methods/passwords/settings) → Reset Password Email |
| User Invitation | Dashboard → Branding → Email Templates | Console → [Project Settings → Sign Ups and User Invitations](https://docs.descope.com/management/project-settings#general-settings) → select connector → + New Template |
| Verification | Dashboard → Branding → Email Templates | Handled within Flows (email verification is a Flow step, not a standalone email) |

Descope also supports SMS and voice templates for OTP delivery, configured the same way via messaging connectors.

### Webhooks / event streams: Auth0 Log Streams → Descope Audit Webhook

Auth0 [Log Streams](https://auth0.com/docs/customize/log-streams) forward authentication events (login, failed login, signup, password change, etc.) to external services like Datadog, Splunk, or a custom webhook.

Descope's equivalent is the [Audit Webhook Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/audit-webhook). It streams audit events to your own HTTP endpoint. Configure it in the Console under Connectors → Audit Webhook with a base URL and authentication (Bearer, API Key, or Basic Auth).

Descope also has a built-in [Audit Trail](https://docs.descope.com/audit) in the Console for viewing events, and supports streaming to third-party services via connectors.

For Auth0 apps that rely on Log Streams for compliance or monitoring, set up the Audit Webhook Connector before cutover to avoid gaps in event logging.

### Custom domains

Auth0 supports [custom domains](https://auth0.com/docs/customize/custom-domains) so the login page appears on your own domain instead of `your-tenant.auth0.com`.

Descope supports [custom domains](https://docs.descope.com/how-to-deploy-to-production/custom-domain) as well:
1. Create a CNAME record (e.g. `auth.example.com`) pointing to `cname.descope.com` (US) or `CNAME.euc1.descope.com` (EU).
2. Set the App URL in Console → Project Settings → General.
3. Add and verify the custom domain in Console.
4. Pass the custom domain as `baseUrl` to the Descope SDK/component: `<AuthProvider projectId="..." baseUrl="https://auth.example.com">`.

If the Auth0 app uses a custom domain, plan this before cutover so cookies and redirects work correctly on the production domain.

### Attack protection: Auth0 Attack Protection → Descope Flow-based security

Auth0's [Attack Protection](https://auth0.com/docs/secure/attack-protection) includes bot detection, brute force protection, breached password detection, and suspicious IP throttling as built-in toggles.

Descope handles these through [Flows](https://docs.descope.com/flows) and security connectors, giving more granular control but requiring explicit configuration:

| Auth0 feature | Descope equivalent |
|---|---|
| Bot Detection | Flow step using [Arkose Bot Manager connector](https://www.descope.com/blog/post/arkose-labs-connector), [Google reCAPTCHA Enterprise](https://docs.descope.com/connectors), or [Fingerprint](https://docs.descope.com/connectors) |
| Brute Force Protection | Flow conditional logic + connector-based risk signals; rate limiting on Descope's infrastructure |
| Breached Password Detection | [Have I Been Pwned integration](https://docs.descope.com/connectors) — blocks credentials found in known breaches |
| Suspicious IP Throttling | Flow step using [AbuseIPDB connector](https://docs.descope.com/connectors) or IP-based conditional logic |

Auth0's attack protection is toggle-based (on/off in Dashboard). Descope's is composable — you add detection steps to your Flow and configure the response (block, challenge with MFA, allow with logging). More powerful but not configured by default.

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
- Removed [`express-openid-connect`](https://github.com/auth0/express-openid-connect). Added [`@descope/node-sdk`](https://github.com/descope/node-sdk) and `cookie-parser`.
- Replaced `app.use(auth(config))` with custom middleware (~20 lines) that validates the `DS` cookie via [`validateSession()`](https://docs.descope.com/getting-started/nodejs#implement-session-validation).
- Added `/login` route rendering an EJS page with [`<descope-wc>`](https://docs.descope.com/client-sdk/descope-components#descope-component).
- Logout changed from GET redirect to Auth0's `/v2/logout` to POST calling [`descopeClient.logout()`](https://docs.descope.com/authorization/session-management/session-validation/backend#logout-current-session-using-backend-sdk) + cookie clearing.
- `requiresAuth()` is a custom 3-line function instead of an [Auth0 SDK import](https://github.com/auth0/express-openid-connect#readme).

**Notes:**
- `express-openid-connect` auto-configured `baseURL` from env vars and handled CSRF for the callback. Descope needs none of that since there's no server-side OAuth flow.
- Auth0's `req.oidc.user` comes from ID token claims. Descope's `authInfo.token` after [`validateSession()`](https://docs.descope.com/authorization/session-management/session-validation/backend#validate-session) holds decoded JWT claims of the session token.

**Limitation:**
- The Descope web component requires JavaScript. Auth0's redirect flow worked without client-side JS. For JS-free auth, use [Descope as an OIDC provider](https://docs.descope.com/getting-started/oidc-endpoints) and implement the redirect flow manually.

---

## Flask / Python


**Changes:**
- Removed [`authlib`](https://docs.authlib.org/en/latest/client/flask.html); added [`descope`](https://github.com/descope/python-sdk).
- Removed OAuth client registration (`oauth.register("auth0", ...)`) and redirect-based flow code.
- Removed `/callback` route. No code exchange needed.
- `/login` renders a template with the [Descope web component](https://docs.descope.com/client-sdk/descope-components#descope-component) instead of calling `oauth.auth0.authorize_redirect()`.
- `/logout` changed from redirect to Auth0's `/v2/logout?returnTo=...&client_id=...` to [`descope_client.logout(refresh_token)`](https://docs.descope.com/authorization/session-management/session-validation/backend#logout-current-session-using-backend-sdk) + cookie deletion.
- Home route reads `DS` cookie from `request.cookies`, validates with [`descope_client.validate_session()`](https://docs.descope.com/getting-started/python#implement-session-validation).

**Notes:**
- Auth0's authlib integration stores the full token response (`access_token`, `id_token`, `userinfo`) in Flask's server-side `session` ([authlib Flask OAuth docs](https://docs.authlib.org/en/latest/client/flask.html)). Descope doesn't use Flask sessions. State lives in client-side cookies. You can drop `session` from Flask imports; `APP_SECRET_KEY` becomes optional.
- `validate_session` returns a dict-like object. JWT standard claims (`sub`, `name`, `email`) are present. Custom claims from [Descope's JWT Templates](https://docs.descope.com/management/jwt-templates) also appear here.
- The `descope` Python SDK requires Python 3.7+. `authlib` supported older versions.

**Limitation:**
- Descope's Python SDK docs don't detail `validate_session()`'s return type beyond "jwt_response." It's a dict with JWT claims in practice, but official type annotations lag behind. Ref: [Descope Python SDK](https://github.com/descope/python-sdk), [Python quickstart](https://docs.descope.com/getting-started/python).

---

## Next.js (standalone)


**Changes:**
- [`@auth0/nextjs-auth0`](https://github.com/auth0/nextjs-auth0) → [`@descope/nextjs-sdk`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk).
- `UserProvider` → [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#auth-provider) (takes `projectId` prop; Auth0's reads from env vars automatically).
- `useUser()` → [`useSession()`](https://docs.descope.com/client-sdk/auth-helpers#booleans) + [`useUser()`](https://docs.descope.com/client-sdk/auth-helpers#core-sdk-functions) (Auth0 combines these; Descope separates session state from user data).
- Removed `pages/api/auth/[...auth0].tsx` catch-all route. In [Auth0 v4 this became automatic middleware](https://github.com/auth0/nextjs-auth0/blob/main/V4_MIGRATION_GUIDE.md), but with Descope there's no server-side OIDC handling at all.
- Added `pages/login.tsx` with [`<Descope>` component](https://docs.descope.com/client-sdk/descope-components#descope-component) rendering the `sign-up-or-in` flow.
- `withPageAuthRequired` (client) replaced by manual `useSession()` check + redirect to `/login`. Auth0 v4 [deprecated `withPageAuthRequired`](https://github.com/auth0/nextjs-auth0/blob/main/V4_MIGRATION_GUIDE.md) in favor of `getSession()` anyway.
- `withApiAuthRequired` replaced by server-side `session()` + manual 401 response. Descope's Next.js SDK exposes [`session()`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#server-side) for this.
- Logout changed from `<a href="/api/auth/logout">` to a button calling [`sdk.logout()`](https://docs.descope.com/client-sdk/auth-helpers#logout) via [`useDescope()`](https://docs.descope.com/client-sdk/auth-helpers#core-sdk-functions).

**Notes:**
- Auth0 provides `withPageAuthRequired` as both a client-side HOC and a `getServerSideProps` wrapper. Descope's Next.js SDK has no equivalent HOC. You check `isAuthenticated` from `useSession()` and redirect yourself. More verbose, more explicit.
- `NEXT_PUBLIC_` prefix is required on the project ID because [`AuthProvider`](https://docs.descope.com/client-sdk/descope-components#auth-provider) runs client-side.
- Both CSR and SSR protected pages are preserved: client-side uses `useSession()`, server-side uses `session()` from the [Next.js SDK server helpers](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#server-side).
- Auth0's `withApiAuthRequired` wraps the handler. Descope: call `session()` at handler top, return 401 yourself.
- `User` interface: removed `nickname`, `email_verified`, `updated_at`; `sub` → `userId`.

---

## Next.js (B2B SaaS / Multi-tenant)


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

The correct replacement for the Auth0 `getServerSideSession()` pattern (server component, no req argument) is `session`, not `getServerSession`. The name was invented by analogy, not verified.

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

The migration generated a `DescopeSession` interface shaped like Auth0's session object:
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
2. **Return type:** `session()` returns `AuthenticationInfo | undefined` from `@descope/node-sdk`, not a boolean-flagged Auth0-style session object.
3. **isAuthenticated:** Does not exist on `AuthenticationInfo`. Unauthenticated = `undefined`; authenticated = non-null object.
4. **claims vs token:** Decoded JWT claims are under `.token` (a `Token` object), not `.claims`. Raw JWT string is under `.jwt`.
5. **Next.js version:** Check `package.json` for Next.js ≥ 15. If so, `cookies()` and `headers()` from `next/headers` are async — all consumers must be async.
6. **Async cascade:** Tracing async upward from `cookies()` may require updating 10+ files. Plan for it.

---

## Next.js (with separate Express API server)


**Changes:**
- [`@auth0/nextjs-auth0`](https://github.com/auth0/nextjs-auth0) v4 → [`@descope/nextjs-sdk`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk) + [`@descope/node-sdk`](https://github.com/descope/node-sdk) (two packages: client SDK for Next.js, node SDK for the API server).
- `Auth0Client` from `@auth0/nextjs-auth0/server` → singleton `getDescopeClient()` using `@descope/node-sdk`.
- Removed Auth0's catch-all middleware that [auto-handled `/auth/*` routes in v4](https://github.com/auth0/nextjs-auth0/blob/main/V4_MIGRATION_GUIDE.md). Replaced with Next.js middleware using Descope's [`authMiddleware()`](https://github.com/descope/descope-js/tree/main/packages/sdks/nextjs-sdk#middleware) to check the `DS` cookie and redirect unauthenticated users.
- Express API server (`api-server.js`): replaced [`express-jwt`](https://github.com/auth0/express-jwt) + [`jwks-rsa`](https://github.com/auth0/node-jwks-rsa) with `@descope/node-sdk` [`validateSession()`](https://docs.descope.com/authorization/session-management/session-validation/backend#validate-session).
- Added `/login` page with [`<Descope>` React component](https://docs.descope.com/client-sdk/descope-components#descope-component).

**Access token proxying changes:**
Auth0's `auth0.getAccessToken()` returns a separate access token (scoped to `AUTH0_AUDIENCE`) passed to the external API as a Bearer token. The API server validates it against Auth0's JWKS endpoint via [`express-jwt`](https://github.com/auth0/express-jwt).

Descope has no separate access token. The session token (DS cookie) is the token you pass to the API server. The Next.js API route reads `DS` from cookies and forwards it as `Authorization: Bearer <DS>`. The API server validates it with `descopeClient.validateSession(token)`.

`AUTH0_AUDIENCE` and `AUTH0_SCOPE` env vars disappear. For audience validation with Descope, configure a custom `aud` claim in the Descope Console's [JWT Templates](https://docs.descope.com/management/jwt-templates) and pass the `audience` parameter to [`validateSession()`](https://docs.descope.com/getting-started/nodejs#implement-session-validation).

**Notes:**
- Auth0 v4's `Auth0Client` manages OIDC discovery, token caching, and session cookies. Descope's `DescopeClient` validates JWTs against [cached public keys](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation). The frontend ([Descope Flows](https://docs.descope.com/flows)) handles what `Auth0Client` used to do.
- [`jwks-rsa`](https://github.com/auth0/node-jwks-rsa) fetches and caches JWKS from Auth0's `/.well-known/jwks.json`. Descope's Node SDK does the same from `https://api.descope.com/v2/keys/<project_id>` ([ref](https://docs.descope.com/authorization/session-management/session-validation/backend/offline-jwt-validation#finding-your-public-key)). No configuration needed.
- Removing `express-jwt` + `jwks-rsa` cuts 2 dependencies and ~15 lines of JWKS config. The Descope replacement is ~15 lines of middleware calling `validateSession()`.

**Limitation:**
- The original API server validated the `audience` claim (ensuring the token targeted this API). Descope's `validateSession()` checks signature and expiry but skips audience by default. To replicate: (1) configure `aud` in [Descope's JWT Templates](https://docs.descope.com/management/jwt-templates), (2) pass `audience` to `validateSession()` ([Node SDK docs](https://docs.descope.com/getting-started/nodejs#implement-session-validation)). Easy to miss during migration.

---

## Go + Encore


**Changes:**
- Backend gutted: 4 auth endpoints (Login, Callback, Logout, AuthHandler) at ~150 lines of Go → 1 endpoint (AuthHandler, ~25 lines) validating DS session tokens with the [Descope Go SDK](https://github.com/descope/go-sdk).
- Removed `backend/auth/authenticator.go` (OIDC provider setup via [`go-oidc`](https://github.com/coreos/go-oidc), OAuth2 config, code exchange). Not needed.
- Frontend removed 3 API routes (`/auth/login`, `/auth/logout`, `/callback`). Replaced with `/login` page containing [`<Descope>` component](https://docs.descope.com/client-sdk/descope-components#descope-component) and client-side `LogoutButton` using [`useDescope().logout()`](https://docs.descope.com/client-sdk/auth-helpers#logout).
- `getRequestClient.ts` reads `DS` cookie instead of custom `auth-token` cookie.
- Generated Encore client (`client.ts`) simplified: auth service methods (Login, Logout, Callback) removed since those backend endpoints are gone.

**Two-process architecture:**
The original split auth between Go backend (OIDC/code exchange/token verification) and Next.js frontend (redirect orchestration). With Descope, auth is client-side. The Go backend validates tokens only. The split is cleaner: backend is a pure API, frontend owns auth UX.

Cookie name changed from `auth-token` (custom, set by callback route) to `DS` (Descope standard). `getRequestClient.ts` extracts this and passes it as Bearer token in the `Authorization` header. Encore's [`//encore:authhandler`](https://encore.dev/docs/go/primitives/defining-apis#access-controls) intercepts it.

**Notes:**
- Go SDK constructor: `client.NewWithConfig(&client.Config{ProjectID: "..."})`. Session validation: [`descopeClient.Auth.ValidateSessionWithToken(ctx, token)`](https://docs.descope.com/getting-started/go#implement-session-validation) returns `(bool, *descope.Token, error)`. `Token.Claims` is `map[string]interface{}`. Ref: [Descope Go SDK](https://github.com/descope/go-sdk).
- Encore's `//encore:authhandler` expects `(auth.UID, error)`. Descope's JWT `sub` claim maps to `auth.UID`. Same claim name as Auth0, different issuer.
- `encore.cue` config: ClientID + ClientSecret + Domain + RedirectURL → ProjectID only.
- `go.mod`: [`coreos/go-oidc/v3`](https://github.com/coreos/go-oidc) + `golang.org/x/oauth2` → [`descope/go-sdk`](https://github.com/descope/go-sdk). Fewer dependencies.

**Limitation:**
- The Go SDK's exported type names (`client.DescopeClient`, `descope.Token`) aren't documented in Descope's official docs. The [Go quickstart](https://docs.descope.com/getting-started/go) shows usage patterns, not Go type signatures. Types in this migration are inferred from [Go SDK README](https://github.com/descope/go-sdk#readme) examples; verify against `go doc` output.
- Encore's `//encore:service` init pattern (`initService()`) creates the Descope client at service startup. If Encore's lifecycle skips `initService`, the client won't exist. Same risk the original had with the OIDC authenticator.

---

## Agentic AI Stacks (LangChain / LangGraph + FGA + Token Vault)


Three sub-projects (`py-langchain`, `ts-langchain`, `ts-vercel-ai`) sharing the same architecture: a document RAG app with an AI agent that accesses third-party services (Google Calendar, Gmail, GitHub, Slack) and processes purchases.

### Architecture overview

| Layer | Auth0 component | Descope equivalent | Migration difficulty |
|---|---|---|---|
| Authentication (login/session) | `@auth0/nextjs-auth0` v4, `auth0-fastapi` | `@descope/nextjs-sdk`, Descope Python SDK + custom FastAPI JWT authorizer | Low: same patterns as the framework sections above |
| Fine-grained authorization | Auth0 FGA (OpenFGA) via `@openfga/sdk` + `@auth0/ai` `FGARetriever` | Descope ReBAC via `management.fga.*` + custom retriever | Medium: API shape differs, no `FGARetriever` |
| Third-party token storage | Auth0 Token Vault / Connected Accounts | Descope Outbound Apps | Medium: API differs, no AI-framework wrapper |
| Async user approval | Auth0 CIBA via `@auth0/ai` `withAsyncAuthorization()` | No equivalent; custom implementation needed | High |
| AI tool authorization wrappers | `@auth0/ai-langchain`, `@auth0/ai-vercel` | No equivalent; custom wrappers needed | High |

### Auth0 integration points across sub-projects

**py-langchain** (FastAPI + LangGraph Python):
- `auth0-fastapi` provides `AuthConfig`, `AuthClient`, session middleware, `/api/auth/*` routes, `require_session` dependency
- `auth0-ai` Python SDK provides `Auth0AI`, `with_token_vault()`, `with_async_authorization()`
- `auth0-ai-langchain` provides `FGARetriever`, `get_access_token_from_token_vault()`
- `openfga-sdk` for direct FGA tuple writes/deletes in document management
- LangGraph receives credentials via `config["configurable"]["_credentials"]` (injected by FastAPI proxy route)
- Frontend is a Vite React SPA; auth is cookie-based via `withCredentials: true` on axios

**ts-langchain** (Next.js + LangGraph TS):
- `@auth0/nextjs-auth0` v4 with `Auth0Client`, `enableConnectAccountEndpoint`, `getAccessToken()`, `getSession()`
- `@auth0/ai-langchain` provides `Auth0AI`, `withTokenVault()`, `withAsyncAuthorization()`, `FGARetriever`, `getAccessTokenFromTokenVault()`
- LangGraph custom auth handler (`auth.ts`) validates JWTs against Auth0 JWKS, attaches `getRawAccessToken()` to context
- `langgraph-nextjs-api-passthrough` proxies requests with Auth0 access token + user object injected
- Connected Accounts API uses `https://DOMAIN/me/v1/connected-accounts/accounts` with scoped tokens
- Uses `AUTH0_CUSTOM_API_CLIENT_ID`/`SECRET` for Token Vault federated token exchange

**ts-vercel-ai** (Next.js + Vercel AI SDK):
- Same auth setup as ts-langchain but uses Vercel AI SDK instead of LangGraph
- `@auth0/ai-vercel` replaces `@auth0/ai-langchain` for tool wrapping
- Tool authorization patterns are identical; the runtime difference is Vercel AI SDK vs LangGraph

### FGA schema (shared across all three)

```
type user
type doc
  relations
    define owner: [user]
    define viewer: [user, user:*]
    define can_view: owner or viewer
```

Documents are created with `owner` relation. Sharing adds `viewer` relations. RAG retrieval filters via `can_view` check. Delete removes all relations.

Descope ReBAC equivalent schema ([DSL format](https://docs.descope.com/authorization/rebac/define-schema)):
```
model AuthZ 1.0

type user

type doc
  relation owner: user
  relation viewer: user
  permission can_view: owner or viewer
```

### Credential flow (all three sub-projects)

```
Frontend (browser)
  → cookies sent with request
    → Next.js/FastAPI middleware validates session
      → extracts access_token + user from session
        → injects into LangGraph config as _credentials
          → tool reads _credentials to:
            a) call Auth0 /userinfo (user_info tool)
            b) exchange via Token Vault (google_calendar, gmail, github, slack tools)
            c) get CIBA approval token (shop_online tool)
            d) build FGA check query with user email (context_docs tool)
```

With Descope, step (a) changes to reading claims from the validated session token (no `/userinfo` call needed since claims are in the JWT). Steps (b-d) require custom implementations using Descope Outbound Apps API, a custom approval mechanism, and Descope ReBAC API respectively.

### Migration strategy notes

The authentication layer (login, session, middleware) follows the same patterns as the framework sections above. The complexity is in the four Auth0 product integrations layered on top.

Recommended migration order:
1. Swap auth layer first (auth0-fastapi/nextjs-auth0 to Descope SDKs). Low risk, proven patterns.
2. Migrate FGA to Descope ReBAC. Moderate lift; the API shape changes but the capability is equivalent.
3. Migrate Token Vault to Outbound Apps. Moderate lift; needs custom tool wrappers.
4. Build custom CIBA replacement. Highest risk; no direct equivalent.
