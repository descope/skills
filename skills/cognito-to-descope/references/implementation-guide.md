# AWS Cognito → Descope: Implementation Guide

Comprehensive technical reference for migrating apps from AWS Cognito to Descope.
Covers AWS Amplify v5/v6, React, Next.js, Node.js/Express, Python/Flask, and infrastructure patterns.

> **See also:** `flows-widgets-console.md` in this directory — Cognito→Descope terminology map, Flows/Widgets/SSO Setup Suite overview, Lambda trigger → Flow step mapping, and the Console-vs-code decision guide. Read it before migrating any auth UI, MFA enrollment, user management pages, or SSO configuration.

---

## Contents

**Architecture & Flow**
- [How auth is structured differently](#how-auth-is-structured-differently)
- [OIDC compatibility path](#oidc-compatibility-path)
- [Token differences](#token-differences)
- [Session management](#session-management)

**Common Gotchas**
- [Passwords cannot be exported from Cognito](#passwords-cannot-be-exported-from-cognito)
- [FORCE_CHANGE_PASSWORD users](#force_change_password-users)
- [cognito:groups is a JWT claim; Descope roles are not](#cognitogroups-is-a-jwt-claim-descope-roles-are-not)
- [cognito:username → sub](#cognitousername--sub)
- [User claims differ — email and name not in Descope JWT by default](#user-claims-differ)
- [Custom attributes need schema pre-creation](#custom-attributes-need-schema-pre-creation)
- [Amplify v5 vs v6 APIs differ significantly](#amplify-v5-vs-v6-apis-differ-significantly)
- [App Client secret requires SECRET_HASH for JIT migration](#app-client-secret-requires-secret_hash-for-jit-migration)
- [Hosted UI redirect flows need explicit handling](#hosted-ui-redirect-flows)
- [Identity Pools are not replaced by Descope](#identity-pools-are-not-replaced-by-descope)
- [API Gateway Cognito authorizer must be swapped explicitly](#api-gateway-cognito-authorizer-must-be-swapped)
- [Session refresh after profile changes](#session-refresh-after-profile-changes)
- [Logout requires two steps](#logout-requires-two-steps)
- [Dual-validation during cutover](#dual-validation-during-cutover)

**Feature Mapping: Cognito → Descope**
- [Social login / federated identity](#social-login--federated-identity)
- [RBAC: Cognito User Groups → Descope Roles](#rbac-cognito-user-groups--descope-roles)
- [Multi-tenancy](#multi-tenancy)
- [Lambda Triggers → Flows and Connectors](#lambda-triggers--flows-and-connectors)
- [MFA enrollment](#mfa-enrollment)
- [User migration](#user-migration)
- [M2M: client credentials → Descope Access Keys](#m2m-client-credentials--descope-access-keys)
- [Email templates](#email-templates)
- [Custom domains](#custom-domains)
- [Attack protection](#attack-protection)
- [Testing checklist](#testing-checklist)

**Framework Sections**
- [React / Amplify v5](#react--amplify-v5)
- [React / Amplify v6](#react--amplify-v6)
- [amazon-cognito-identity-js (low-level)](#amazon-cognito-identity-js)
- [Next.js standalone](#nextjs-standalone)
- [Next.js: Migration Bug Catalog](#nextjs-migration-bug-catalog)
- [Next.js + Express API server](#nextjs--express-api-server)
- [NextAuth.js + Cognito](#nextauthjs--cognito)
- [Node.js / Express backend](#nodejs--express-backend)
- [Python / Flask backend](#python--flask-backend)

**Infrastructure**
- [User migration commands and JIT setup](#user-migration-commands-and-jit-setup)
- [AWS API Gateway authorizer swap](#aws-api-gateway-authorizer-swap)
- [Cognito Identity Pools](#cognito-identity-pools)
- [Hosted UI and federation paths](#hosted-ui-and-federation-paths)
- [M2M: Access Keys](#m2m-access-keys)

**Reference**
- [Auth method equivalents](#auth-method-equivalents)
- [Terminology mapping](#terminology-mapping)
- [Environment variables](#environment-variables)
- [Migration checklist](#migration-checklist)
- [Useful links](#useful-links)

---

## General Insights

**— Architecture & Flow —**

### How auth is structured differently

Cognito's auth model depends on which pattern the app uses:

- **Amplify + custom UI** (`Auth.signIn()`, `Auth.signUp()`): The Amplify SDK manages the auth ceremony client-side, issuing an ID token and access token stored in localStorage or memory. The backend validates tokens against Cognito's JWKS. No server-side OAuth callback routes required.
- **Cognito Hosted UI** (OAuth PKCE redirect): The browser redirects to Cognito's hosted page. Cognito returns an authorization code. Amplify exchanges it for tokens automatically — there are no explicit `/callback` routes to write — but the app depends on the redirect flow.

Descope unifies both patterns. The [`<Descope>` component](https://docs.descope.com/client-sdk/descope-components) runs the authentication ceremony inside the browser, storing JWTs in `DS` (session) and `DSR` (refresh) cookies. No redirect to an external page, no code exchange, no server-side callback route.

Every Cognito→Descope migration:
- Removes `Amplify.configure({ Auth: {...} })` and all Amplify auth imports
- Adds `<AuthProvider projectId="...">` at the app root
- Replaces sign-in UI (`<Authenticator>`, custom `Auth.signIn` forms) with `<Descope flowId="sign-up-or-in" />`
- Replaces backend JWT validation (`aws-jwt-verify`, `cognitojwt`) with `descopeClient.validateSession()`

**Exception**: If you want to preserve an existing OIDC redirect flow, Descope exposes standard OIDC endpoints. See [OIDC compatibility path](#oidc-compatibility-path) below.

### OIDC compatibility path

Descope exposes standard [OIDC endpoints](https://docs.descope.com/getting-started/oidc-endpoints):

| Endpoint | URL |
|---|---|
| Authorization | `https://api.descope.com/oauth2/v1/authorize` |
| Token | `https://api.descope.com/oauth2/v1/token` |
| UserInfo | `https://api.descope.com/oauth2/v1/userinfo` |
| JWKS | `https://api.descope.com/v2/keys/<projectId>` |
| End Session | `https://api.descope.com/oauth2/v1/logout` |
| Revocation | `https://api.descope.com/oauth2/v1/revoke` |

Apps that use Cognito Hosted UI with PKCE can swap the Authorization Server to Descope and keep most redirect-based OIDC client code intact. Claim shape differences (`cognito:username` vs `sub`, `cognito:groups` vs `roles`) still require code updates. It's a viable incremental path: swap the IdP first, then refactor to Descope-native SDKs.

### Token differences

- **Cognito**: Two tokens per session — an **ID token** (identity: `sub`, `email`, `cognito:username`, `cognito:groups`, custom attributes) and an **access token** (authorization: scopes, client). JWKS at `https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json`. Issuer: `https://cognito-idp.{region}.amazonaws.com/{userPoolId}`.
- **Descope**: One **session token** (JWT) plus a **refresh token** (`DSR` cookie). JWKS at `https://api.descope.com/v2/keys/{projectId}`. Issuer: `https://api.descope.com/{projectId}`.

Key claim differences:

| Claim | Cognito | Descope |
|---|---|---|
| User ID | `sub` (UUID) | `sub` (new Descope UUID — different value) |
| Username | `cognito:username` | Not present; use `sub` |
| Groups/roles | `cognito:groups` (array) | `roles` array (embedded by default) |
| Permissions | Not a first-class concept | `permissions` array (embedded by default) |
| Email | `email` | Not in JWT by default — add via [JWT Templates](https://docs.descope.com/management/jwt-templates) |
| Email verified | `email_verified` | Not in JWT by default; available on user object as `verifiedEmail` |
| Tenant ID | Not a first-class concept | `dct` (active tenant ID), `tenants` (per-tenant roles/permissions object) |
| Issuer | `https://cognito-idp.{region}.amazonaws.com/{poolId}` | `https://api.descope.com/{projectId}` |
| Audience | App Client ID | Not set by default; configure via JWT Templates if needed |

### Session management

- **Amplify v5**: `Auth.currentAuthenticatedUser()` for current user, `Auth.currentSession()` for tokens, `Hub.listen('auth', callback)` for auth events.
- **Amplify v6**: `getCurrentUser()` and `fetchAuthSession()` with tree-shaking imports.
- **Descope React SDK**: `useSession()` provides `isAuthenticated`, `isSessionLoading`, `session.token`. `useUser()` provides user attributes. Tokens auto-refresh transparently. No event listener setup needed.

---

**— Common Gotchas —**

### Passwords cannot be exported from Cognito

**AWS Cognito does not expose user password hashes.** This is a hard technical limitation. It means:
- Full migration always results in users needing to reset their password or switch to passwordless on first sign-in.
- JIT (Just-In-Time) migration is the preferred path when preserving the password sign-in experience is required.

### FORCE_CHANGE_PASSWORD users

Cognito users with `UserStatus: FORCE_CHANGE_PASSWORD` have never completed their initial sign-in after admin creation. These users cannot authenticate via JIT migration (Cognito rejects the credential). Mark them with a `freshlyMigrated` custom attribute and route them through a password-set or magic-link step in your Descope Flow on first sign-in.

### `cognito:groups` is a JWT claim; Descope roles are not

Cognito embeds group membership as a `cognito:groups` array directly in the JWT. Code like `token['cognito:groups'].includes('admin')` is common.

Descope surfaces roles in the JWT `roles` array, but the idiomatic way to check them is via the SDK:

```js
// Before (Cognito)
const groups = decoded['cognito:groups'] || [];
if (groups.includes('admin')) { ... }

// After (Descope)
const isAdmin = descopeClient.validateRoles(authInfo, ['admin']);
// OR read the array directly from the validated token:
if (authInfo.token.roles?.includes('admin')) { ... }
// Tenant-scoped roles (multi-tenant apps):
const isTenantAdmin = descopeClient.validateTenantRoles(authInfo, tenantId, ['admin']);
```

### `cognito:username` → `sub`

Cognito's `cognito:username` is a username string. Descope has no username concept in the JWT — the user identifier is `sub` (a new Descope UUID). Replace all `token['cognito:username']` reads with `token.sub`. If `cognito:username` or Cognito `sub` was used as a database foreign key, a DB remapping script is needed after migration.

### User claims differ

Descope's default session JWT contains `sub`, `amr`, `drn`, `tenants`, `roles`, and `permissions`. It does **not** include `email`, `name`, or `picture` unless added via [JWT Templates](https://docs.descope.com/management/jwt-templates). Configure a JWT Template before cutover — without it, all profile claim reads return `undefined` silently.

### Custom attributes need schema pre-creation

Cognito custom attributes (`custom:department`, `custom:role`, etc.) migrate to Descope custom attributes. Descope requires the attribute schema to be defined in Console → Users → Attributes **before** importing users with those attributes. Pre-create all `custom:*` definitions first or the batch import will silently drop those fields.

### Amplify v5 vs v6 APIs differ significantly

Amplify v6 moved from class-based to function-based imports:

```js
// v5: class-based
import { Auth } from 'aws-amplify';
await Auth.signIn(email, password);

// v6: function imports with tree-shaking
import { signIn } from 'aws-amplify/auth';
await signIn({ username: email, password });
```

Check `package.json` for `aws-amplify` version before writing migration code. Both versions map to the same Descope patterns, but the Cognito `before` code in your edits must match the version actually in use.

### App Client secret requires SECRET_HASH for JIT migration

If a Cognito App Client has a client secret, the `USER_PASSWORD_AUTH` flow requires a `SECRET_HASH` = `HMAC-SHA256(clientSecret, username + clientId)`. The Descope Generic HTTP Connector cannot compute this hash itself. Options:

1. **(Recommended) Deploy a proxy service** — a small Lambda or Express endpoint that receives `{ username, password }`, computes `SECRET_HASH`, calls Cognito's `InitiateAuth`, and returns the result. Point the Descope Connector at the proxy.
2. **Create a new public App Client** — no client secret, used only for JIT migration, deleted after all users have migrated.

### Hosted UI redirect flows

Apps using Cognito Hosted UI with OAuth PKCE (triggered by `Auth.federatedSignIn()` or an `oauth: {}` block in `Amplify.configure`) have a redirect-based auth flow. Descope Flows are embedded by default. Options:

- **Embedded (recommended)**: Remove the `oauth:` config block. Replace the login trigger with `<Descope flowId="sign-up-or-in" />`. Add original `redirectSignIn` URLs to Console → Project Settings → Allowed Redirect URLs.
- **Redirect (OIDC path)**: Keep existing redirect client code, swap the Authorization Server endpoint to Descope. See [Hosted UI and federation paths](#hosted-ui-and-federation-paths).

If Cognito Hosted UI was acting as an **OAuth Authorization Server for external clients** (other apps redirected to your Cognito domain for authorization), configure Descope as an OIDC Application in the Console and update external clients' authorization endpoint URLs.

### Identity Pools are not replaced by Descope

Cognito Identity Pools grant users temporary AWS IAM credentials for direct AWS service access (S3, DynamoDB, etc.). Descope replaces the User Pool (authentication) layer, not the Identity Pool (AWS credential federation) layer.

If your app uses Identity Pools, configure Descope as a federated OIDC provider in the existing Identity Pool after migration. See [Cognito Identity Pools](#cognito-identity-pools).

### API Gateway Cognito authorizer must be swapped

AWS API Gateway Cognito User Pool authorizers validate tokens against Cognito's JWKS automatically. After switching to Descope tokens, API calls will return 401 until the authorizer is updated. Swap the backend authorizer before the frontend cutover. See [AWS API Gateway authorizer swap](#aws-api-gateway-authorizer-swap).

### Session refresh after profile changes

Profile updates via the Management SDK do not update the JWT already in the browser. To immediately reflect changes after a profile update:

```ts
// @descope/react-sdk or @descope/nextjs-sdk/client
const { refresh } = useDescope();
await refresh();
```

Alternatively, subscribe to auth state changes via the [auth-helpers event system](https://docs.descope.com/client-sdk/auth-helpers#handling-authentication-state-changes) if session updates can originate from multiple places (admin role grant, tenant assignment, profile edit).

For server-side claim updates without waiting for a client refresh: `POST /v1/mgmt/user/jwt/update`. The user's next token refresh picks up the new claims.

### Logout requires two steps

Descope logout requires two explicit actions:

1. Call `descopeClient.logout(refreshToken)` (server-side) or `sdk.logout()` (client-side) to invalidate the refresh token on Descope's servers.
2. Clear the `DS` and `DSR` cookies.

Clearing cookies without calling logout → the refresh token stays valid. Calling logout without clearing cookies → the client holds a stale session that confuses auth-state hooks.

### Dual-validation during cutover

During a gradual rollout where both Cognito and Descope tokens may be in circulation, peek at the unverified `iss` claim to route to the right validator. See the dual-validation middleware in the [Node.js](#nodejs--express-backend) and [Python](#python--flask-backend) sections. Monitor `source: 'cognito'` log entries — remove the Cognito validation branch once entries reach zero for a full business day.

---

**— Feature Mapping: Cognito → Descope —**

### Social login / federated identity

Cognito Social Connections (Google, Facebook, Apple via Hosted UI or `Auth.federatedSignIn({ provider: 'Google' })`) map to Descope [social auth methods](https://docs.descope.com/authentication/social):

1. Configure each provider in Console → Authentication → Social.
2. Add the provider to the Sign-Up or In Flow.
3. Replace `Auth.federatedSignIn({ provider: 'Google' })` calls with `<Descope flowId="sign-up-or-in" />` — configured providers render automatically.

**Social OAuth callback URL** (register with each provider): `https://api.descope.com/v1/oauth/callback`

**SSO Setup Suite**: For B2B apps with per-tenant SAML/OIDC IdPs, the SSO Setup Suite lets tenant admins configure their own IdP through a guided Console wizard — no SDK calls or code deployment needed. Present this before migrating any `management.sso.*` code. See `flows-widgets-console.md` → SSO Setup Suite.

### RBAC: Cognito User Groups → Descope Roles

Cognito User Groups used for capabilities (`admin`, `editor`, `read-only`) map to **Descope Roles**. The migration tool automatically converts them during user import.

Cognito User Groups used as **organization identifiers** (`acme-corp`, `tenant_123`, a UUID) may map to **Descope Tenants** instead. See [Multi-tenancy](#multi-tenancy) below.

SDK methods:
```js
descopeClient.management.permission.create(name, description)
descopeClient.management.role.create(name, description, permissionNames, tenantId)
await descopeClient.management.user.setRoles(loginId, ['admin'])
```

Backend code checking `payload['cognito:groups'].includes('admin')` changes to:
```js
const isAdmin = descopeClient.validateRoles(authInfo, ['admin']);
const canWrite = descopeClient.validatePermissions(authInfo, ['content:write']);
```

### Multi-tenancy

| Cognito Pattern | Descope Equivalent |
|---|---|
| Single User Pool — groups for capabilities only | Descope Roles (no Tenants needed) |
| Single User Pool — groups as org identifiers | Descope Tenants (one per org group) |
| Multiple User Pools, one per customer org | Descope Tenants (one per pool, all in one Project) |
| User Pool Group linked to per-customer SAML IdP | Descope Tenant with an SSO connection |

**Key difference**: Cognito's `cognito:groups` is a flat array. Descope's `tenants` is a nested object: `{ "tenantId": { "roles": [...], "permissions": [...] } }`. Use `dct` when you only need the active tenant ID; use `tenants` when you need per-tenant roles.

Switching active tenants does not require re-authentication — implement it client-side (e.g., an `active_tenant` cookie) and read the active tenant from the `tenants` object in the JWT.

When a user is added to a new tenant via the Management SDK, the existing JWT is stale — the `tenants` claim was set at login and doesn't include the new tenant. The user must re-authenticate to get an updated JWT.

**Finding a user's tenants**: use `management.user.load(loginId)` and read `.userTenants` — it lists only that user's tenants. Avoid `management.tenant.loadAll()` + client-side filter; it scans every tenant in the project.

### Lambda Triggers → Flows and Connectors

| Cognito Lambda Trigger | Descope Equivalent |
|---|---|
| Pre Sign-up | Flow condition or HTTP Connector for blocklist / domain validation |
| Post Confirmation | Post-login webhook or Flow step after sign-up success |
| Pre Token Generation | [JWT Templates](https://docs.descope.com/management/jwt-templates) — customize claims in the issued JWT |
| Custom Authentication | Custom Flow with conditional branching + HTTP Connectors |
| Post Authentication | Webhook on successful login event |
| User Migration | JIT migration via Generic HTTP Connector |
| Verify Auth Challenge | Custom Flow step |
| Define Auth Challenge | Custom Flow with conditional branching |

> **Pre-Token Generation → JWT Templates** is the most impactful trigger to migrate. If the trigger adds claims to tokens, recreate those claims in a JWT Template **before cutover**. Without this, backend code reading those custom claims will break silently on the first Descope token.

### MFA enrollment

MFA enrollment is managed through Flows, not the Management SDK — there is no `createEnrollmentTicket()` equivalent. Add an MFA step to the Sign-Up or In Flow in the Console; users enroll in-browser.

**MFA enrollments do not migrate.** All users who had TOTP or SMS MFA enabled in Cognito must re-enroll after migration. Plan user communication before cutover.

Factor deletion SDK support:
- Passkeys: `descopeClient.management.user.removeAllPasskeys(loginId)` — SDK-supported
- TOTP: No SDK method; use Console → User Management → [user] → Delete TOTP Seed
- SMS/OTP: No documented SDK method — may require direct REST API calls

### User migration

**Full migration** (bulk import — users reset password or go passwordless on first sign-in):

Cognito does not expose password hashes. All migrated users must use magic link, OTP, or set a new password on first sign-in. Mark them with a `freshlyMigrated` custom attribute to trigger this step in the Descope Flow.

**JIT migration** (preserves passwords — recommended when password continuity matters):

Keep Cognito running during a transition window. On each user's first Descope login, a Generic HTTP Connector verifies their credentials against Cognito in real-time and provisions the user in Descope. See [User migration commands and JIT setup](#user-migration-commands-and-jit-setup).

**User ID mapping**: Cognito `sub` values and Descope `sub` values are different UUIDs. The migration tool stores the original Cognito `sub` as a `cognitoSub` custom attribute in Descope. If Cognito `sub` is used as a database foreign key, a DB remapping script is needed after migration.

### M2M: client credentials → Descope Access Keys

| Cognito | Descope |
|---|---|
| App Client with `client_credentials` grant | Access Key in Console → Company → Access Keys |
| `POST /oauth2/token` with `grant_type=client_credentials` | `descopeClient.auth.exchangeAccessKey(accessKey)` |
| Token scoped to `audience` | JWT with tenant/role claims (configure via Access Key settings) |
| Token validated via JWKS | Token validated via `descopeClient.validateSession()` — same as user tokens |

### Email templates

| Email type | Cognito | Descope |
|---|---|---|
| Magic Link / OTP | SES / Cognito built-in | Console → Authentication Methods → Magic Link or OTP → Connector → + New Template |
| Password Reset | Cognito built-in / Lambda Custom Message | Console → Authentication Methods → Passwords → Reset Password Email |
| User Invitation | Custom implementation | Console → Project Settings → Sign Ups and User Invitations → Connector → + New Template |
| Account verification | Cognito built-in | Handled as a Flow step (email verification is a Flow step, not a standalone email) |

### Custom domains

Cognito Hosted UI supports custom domains. Descope supports [custom domains](https://docs.descope.com/how-to-deploy-to-production/custom-domain):

1. Create a CNAME record (e.g. `auth.example.com`) pointing to `cname.descope.com` (US) or `CNAME.euc1.descope.com` (EU).
2. Set the App URL in Console → Project Settings → General.
3. Verify the custom domain in Console.
4. Pass `baseUrl` to the SDK/component: `<AuthProvider projectId="..." baseUrl="https://auth.example.com">`.

### Attack protection

Cognito has built-in advanced security features (compromised credential detection, adaptive authentication) as Dashboard toggles.

Descope handles security through [Flows](https://docs.descope.com/flows) and connectors — more composable but requiring explicit configuration:

| AWS / Cognito feature | Descope equivalent |
|---|---|
| Compromised credentials check | [Have I Been Pwned connector](https://docs.descope.com/connectors) — blocks credentials found in known breaches |
| Bot detection | Flow step with [Arkose Bot Manager](https://docs.descope.com/connectors), reCAPTCHA Enterprise, or Fingerprint |
| Adaptive authentication | Flow conditional logic + connector-based risk signals |
| IP-based blocking | Flow step with AbuseIPDB connector or IP conditional logic |

### Testing checklist

**Compile first — no env vars needed.** Run `npx tsc --noEmit` (or `go build ./...`, etc.) immediately after code changes, before setting env vars or starting the server. Do not treat the migration as done until this exits clean.

After migrating, verify:
- DS and DSR cookies are set after login (DevTools → Application → Cookies)
- Protected routes redirect to `/login` when DS cookie is absent
- Protected routes render when DS cookie is present and valid
- Logout clears both DS and DSR cookies
- Logout invalidates the refresh token (re-login requires re-authentication)
- User claims (`name`, `email`) display correctly — confirm JWT Template is configured
- API routes return 401 when no token is provided
- Role/group-based access control works (`validateRoles()` returns expected results)
- Session persists across page refresh
- `FORCE_CHANGE_PASSWORD` users are routed to a reset step
- MFA enrollment works (if MFA was enabled in Cognito)
- API Gateway authorizer accepts Descope tokens (if applicable)
- If dual-validation deployed: both Cognito and Descope tokens accepted during transition window

---

## Framework Sections

### React / Amplify v5

**Changes:**
```bash
npm remove aws-amplify @aws-amplify/auth @aws-amplify/ui-react amazon-cognito-identity-js
npm install @descope/react-sdk
```

Replace `Amplify.configure` + Provider setup:
```jsx
// Before
import { Amplify } from 'aws-amplify';
Amplify.configure({ Auth: { region: '...', userPoolId: '...', userPoolWebClientId: '...' } });

// After — main.jsx / index.jsx
import { AuthProvider } from '@descope/react-sdk';
root.render(
  <AuthProvider projectId={process.env.REACT_APP_DESCOPE_PROJECT_ID}>
    <App />
  </AuthProvider>
);
```

Replace auth state + Hub listener:
```jsx
// Before
import { Auth, Hub } from 'aws-amplify';
const [user, setUser] = useState(null);
useEffect(() => {
  Auth.currentAuthenticatedUser().then(setUser).catch(() => setUser(null));
  const unsub = Hub.listen('auth', ({ payload }) => {
    if (payload.event === 'signIn') Auth.currentAuthenticatedUser().then(setUser);
    if (payload.event === 'signOut') setUser(null);
  });
  return unsub;
}, []);

// After
import { useSession, useUser } from '@descope/react-sdk';
const { isAuthenticated, isSessionLoading } = useSession();
const { user } = useUser(); // user.name, user.email, user.customAttributes, user.roleNames
```

Replace sign-in UI (`withAuthenticator`, `<Authenticator>`, or manual `Auth.signIn` forms):
```jsx
// Before (Authenticator HOC)
export default withAuthenticator(App);
// Before (manual)
await Auth.signIn(email, password);

// After — render at the /login route
import { Descope } from '@descope/react-sdk';
<Descope
  flowId="sign-up-or-in"
  onSuccess={() => navigate('/dashboard')}  // required — component does not auto-navigate
  onError={(e) => console.error('Auth error', e)}
/>
```

Replace token retrieval for API calls:
```jsx
// Before
const session = await Auth.currentSession();
const token = session.getIdToken().getJwtToken();
fetch('/api/data', { headers: { Authorization: `Bearer ${token}` } });

// After
import { useSession } from '@descope/react-sdk';
const { session } = useSession();
// session.token is the current session JWT, auto-refreshed by the SDK
fetch('/api/data', { headers: { Authorization: `Bearer ${session?.token}` } });
```

Replace sign-out:
```jsx
// Before
await Auth.signOut();
await Auth.signOut({ global: true }); // revokes all sessions

// After
import { useDescope } from '@descope/react-sdk';
const { logout } = useDescope();
await logout(); // revokes current session's refresh token
// Global sign-out: descopeClient.management.user.logout(userId) on the backend
```

Replace protected routes:
```jsx
// Before
const PrivateRoute = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    Auth.currentAuthenticatedUser().then(setUser).catch(() => {}).finally(() => setLoading(false));
  }, []);
  if (loading) return <Spinner />;
  return user ? children : <Navigate to="/login" />;
};

// After
import { useSession } from '@descope/react-sdk';
const PrivateRoute = ({ children }) => {
  const { isAuthenticated, isSessionLoading } = useSession();
  if (isSessionLoading) return <Spinner />;
  return isAuthenticated ? children : <Navigate to="/login" />;
};
```

**Notes:**
- `Auth.forgotPassword()`, `Auth.confirmSignUp()`, `Auth.resendSignUp()`, `Auth.confirmForgotPassword()` — remove entirely. These flows are handled inside the Descope Flow component.
- `Auth.changePassword()` → `descopeClient.password.update(loginId, newPassword)` (backend management call).
- `user.attributes.email` → `user.email`; `user.attributes['custom:*']` → `user.customAttributes['*']`; `user.username` → `user.userId` or `session.token.sub`.
- `Hub.listen` listeners for `signIn`/`signOut` are no longer needed — `isAuthenticated` from `useSession()` is reactive.

---

### React / Amplify v6

Amplify v6 uses tree-shaking imports. The Descope migration target is identical to v5 — only the Cognito `before` patterns differ.

```jsx
// Before (Amplify v6 imports)
import { signIn, signOut, getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';
import { Hub } from 'aws-amplify/utils';

// Check current user
try { const user = await getCurrentUser(); } catch { /* not signed in */ }

// Sign in
const { isSignedIn, nextStep } = await signIn({ username: email, password });

// Get token
const session = await fetchAuthSession();
const token = session.tokens?.idToken?.toString();

// Sign out
await signOut();
await signOut({ global: true });

// After — same as Amplify v5 above
```

**Notes:**
- Amplify v6's `signIn` may return `{ isSignedIn: false, nextStep: { signInStep: 'CONFIRM_SIGN_IN_WITH_...' } }` for MFA or custom auth challenges. These multi-step flows are handled entirely within the Descope Flow component — no equivalent conditional branching needed in your code.

---

### amazon-cognito-identity-js

```jsx
// Before
import { CognitoUserPool, CognitoUser, AuthenticationDetails } from 'amazon-cognito-identity-js';

const userPool = new CognitoUserPool({ UserPoolId: '...', ClientId: '...' });
const authDetails = new AuthenticationDetails({ Username: email, Password: password });
const cognitoUser = new CognitoUser({ Username: email, Pool: userPool });

cognitoUser.authenticateUser(authDetails, {
  onSuccess: (session) => { const idToken = session.getIdToken().getJwtToken(); },
  onFailure: (err) => console.error(err),
  newPasswordRequired: (attrs) => { /* FORCE_CHANGE_PASSWORD handling */ }
});

// After — replace entirely with the Descope component at the /login route
import { Descope } from '@descope/react-sdk';
<Descope
  flowId="sign-up-or-in"
  onSuccess={() => navigate('/dashboard')}
  onError={(e) => console.error(e)}
/>
```

**Notes:**
- The `newPasswordRequired` callback handled Cognito's `FORCE_CHANGE_PASSWORD` flow. In Descope, route these users through a password-set step in the Flow (see [FORCE_CHANGE_PASSWORD users](#force_change_password-users)).
- `amazon-cognito-identity-js` was often used to compute `SECRET_HASH`. Once migrated, this concern disappears entirely.

---

### Next.js standalone

**Changes:**
```bash
npm remove aws-amplify @aws-amplify/auth
npm install @descope/nextjs-sdk
```

Root layout (replaces `Amplify.configure`):
```tsx
// app/layout.tsx
import { AuthProvider } from '@descope/nextjs-sdk';

export default function RootLayout({ children }) {
  return (
    <html><body>
      <AuthProvider projectId={process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID!}>
        {children}
      </AuthProvider>
    </body></html>
  );
}
```

Middleware:
```ts
// middleware.ts
import { authMiddleware } from '@descope/nextjs-sdk/server';

export default authMiddleware({
  projectId: process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID!,
  redirectUrl: '/login',
  publicRoutes: ['/login', '/signup', '/api/public'],
});
export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'] };
```

Login page:
```tsx
// app/login/page.tsx
'use client';
import { Descope } from '@descope/nextjs-sdk/client';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  return (
    <Descope
      flowId="sign-up-or-in"
      onSuccess={() => router.push('/dashboard')}  // required — does not auto-navigate
      onError={(e) => console.error(e)}
    />
  );
}
```

Server components:
```tsx
// app/dashboard/page.tsx
import { session } from '@descope/nextjs-sdk/server';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const s = await session();
  if (!s) redirect('/login');
  return <div>Hello {s.token.email} — User ID: {s.token.sub}</div>;
}
```

Client components:
```tsx
'use client';
import { useSession, useUser, useDescope } from '@descope/nextjs-sdk/client';

const { isAuthenticated, isSessionLoading } = useSession();
const { user } = useUser();
const { logout } = useDescope();
```

**Notes:**
- `NEXT_PUBLIC_` prefix is required: `AuthProvider` runs client-side and cannot access server-only env vars.
- **Critical client/server split**: `session()` from `@descope/nextjs-sdk/server` is for server components, server actions, and API routes **only**. In `'use client'` components, use `useSession()` + `useUser()` from `@descope/nextjs-sdk/client`. Using `session()` in a client component compiles but throws at runtime. Always check for `'use client'` at the top of the file before deciding which to use.
- **Never import from `@descope/nextjs-sdk/server` in a client component** — it will break the build or leak the management key. **Never import from `@descope/nextjs-sdk/client` in a server component** — unvalidated session state cannot be trusted.
- No `withPageAuthRequired` HOC equivalent. Check `isAuthenticated` from `useSession()` and redirect manually.

---

### Next.js: Migration Bug Catalog

Every error below traces to incorrect assumptions about the `@descope/nextjs-sdk` API surface. Each stems from not verifying the SDK's `.d.ts` before writing imports and wrapper types.

---

**Bug 1: `getServerSession` doesn't exist — correct export is `session`**

```ts
// Wrong — getServerSession does not exist in @descope/nextjs-sdk
import { getServerSession } from '@descope/nextjs-sdk/server';
const s = await getServerSession();

// Correct
import { session } from '@descope/nextjs-sdk/server';
const s = await session();  // returns AuthenticationInfo | undefined

// For API routes (explicit req object):
import { getSession } from '@descope/nextjs-sdk/server';
const s = await getSession(req);
```

---

**Bug 2: Return type is `AuthenticationInfo`, not an `{isAuthenticated, claims}` object**

Migrations often invent a `DescopeSession` interface shaped like NextAuth's session:

```ts
// Wrong assumption — none of these properties exist on what session() returns
interface DescopeSession {
  isAuthenticated: boolean   // ✗ does not exist
  claims: { sub: string; email?: string }  // ✗ does not exist; decoded claims are on "token"
  token: string              // ✗ misleading — the raw JWT string is on "jwt", not "token"
}
```

`session()` returns `AuthenticationInfo` from `@descope/node-sdk`:

```ts
interface AuthenticationInfo {
  jwt: string     // raw session JWT string
  token: Token    // decoded JWT claims: { sub?, exp?, iss?, [claim: string]: unknown }
  cookies?: string[]
}
```

Because incorrect casts like `session as unknown as DescopeSession` bypass TypeScript, these bugs fail silently at runtime: every `!session?.isAuthenticated` check evaluates as `true` (property doesn't exist), making every auth guard fail open.

Correct typed adapter:
```ts
import { session as sdkSession } from '@descope/nextjs-sdk/server';

export interface DescopeSession {
  isAuthenticated: boolean;
  jwt: string;
  token: {
    sub: string;
    email?: string;
    name?: string;
    roles?: string[];
    tenants?: Record<string, { roles: string[]; permissions: string[] }>;
    [key: string]: unknown;
  };
}

export async function getDescopeSession(): Promise<DescopeSession | null> {
  const authInfo = await sdkSession();
  if (!authInfo) return null;
  return {
    isAuthenticated: true,
    jwt: authInfo.jwt,
    token: authInfo.token as DescopeSession['token'],
  };
}
```

---

**Bug 3: `cookies()` from `next/headers` is async in Next.js 15**

```ts
// Wrong in Next.js 15+ — cookies() returns Promise<ReadonlyRequestCookies>
const cookieStore = cookies();   // ✗ synchronous call; compiles but throws at runtime

// Correct for Next.js 15+
const cookieStore = await cookies();
```

Check `package.json` for `next >= 15` before generating any `cookies()` or `headers()` reads.

---

**Bug 4: Making a helper async cascades to all callers — trace the full chain**

When any shared helper that reads cookies/headers becomes async, every function that calls it must also become async and add `await`. This can cascade through 20+ files. TypeScript accepts `await` on non-Promise values without error, so missing `await` calls fail silently at runtime.

**Practice**: After making any shared auth helper async, immediately grep all call sites and propagate `async`/`await` before finishing the edit.

---

**Summary: verify before generating Next.js + `@descope/nextjs-sdk` code**

1. Resolve `node_modules/@descope/nextjs-sdk/dist/types/server/*.d.ts` — confirm exact export names before writing any import.
2. `session()` returns `AuthenticationInfo | undefined`, not a session object with `isAuthenticated`.
3. Decoded claims are under `.token`, not `.claims`. Raw JWT string is under `.jwt`.
4. Check `package.json` for Next.js ≥ 15 — if so, `cookies()` and `headers()` are async.
5. Async cascade from `cookies()` may require updating many files. Plan for it before starting.

---

### Next.js + Express API server

**Changes:**
```bash
# Next.js frontend
npm install @descope/nextjs-sdk
# Express API server
npm remove amazon-cognito-jwt-verify aws-jwt-verify express-jwt jwks-rsa
npm install @descope/node-sdk
```

Next.js API route forwarding the token to the Express server:
```ts
import { session } from '@descope/nextjs-sdk/server';

export async function GET() {
  const s = await session();
  if (!s) return Response.json({ error: 'Unauthorized' }, { status: 401 });
  const response = await fetch('http://api-server/data', {
    headers: { Authorization: `Bearer ${s.jwt}` },
  });
  return Response.json(await response.json());
}
```

Express API server — replace `CognitoJwtVerifier` or `express-jwt` + `jwks-rsa`:
```js
import DescopeClient from '@descope/node-sdk';
const descopeClient = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });

async function verifySession(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  try {
    const authInfo = await descopeClient.validateAndRefreshSession(token);
    req.user = authInfo.token;
    next();
  } catch {
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}
```

**Notes:**
- `COGNITO_APP_CLIENT_ID` and audience env vars disappear from the API server. The token carries no `aud` claim by default. To replicate audience validation: configure `aud` in [JWT Templates](https://docs.descope.com/management/jwt-templates) and pass `audience` to `validateSession()`.
- `jwks-rsa` fetched and cached JWKS from Cognito's endpoint. Descope's Node SDK does the same from `https://api.descope.com/v2/keys/{projectId}` automatically — no configuration needed.

---

### NextAuth.js + Cognito

```bash
npm remove next-auth
npm install @descope/nextjs-sdk
```

1. Delete `pages/api/auth/[...nextauth].ts` (or `app/api/auth/[...nextauth]/route.ts`)
2. Replace `SessionProvider` with `AuthProvider` from `@descope/nextjs-sdk`
3. Replace `useSession()` from `next-auth/react` with `useSession` from `@descope/nextjs-sdk/client`
4. Replace `signIn()` / `signOut()` with Descope equivalents
5. Replace `getServerSession(authOptions)` with `session()` from `@descope/nextjs-sdk/server`

**Notes:**
- NextAuth's `getServerSession(authOptions)` takes an argument. Descope's `session()` takes no required argument — remove the `authOptions` import entirely.
- NextAuth's session object shape (`session.user.name`, `session.user.email`) differs from Descope's `AuthenticationInfo`. Rebuild any session type wrappers using the typed adapter in the [Bug Catalog](#nextjs-migration-bug-catalog) above.

---

### Node.js / Express backend

**Changes:**
```bash
npm remove amazon-cognito-jwt-verify aws-jwt-verify @aws-sdk/client-cognito-identity-provider
npm install @descope/node-sdk
```

Initialize:
```js
// Before
import { CognitoJwtVerifier } from 'aws-jwt-verify';
const verifier = CognitoJwtVerifier.create({
  userPoolId: 'us-east-1_XXXXXXXXX',
  tokenUse: 'id',
  clientId: 'xxxxxxxxxx',
});

// After
import DescopeClient from '@descope/node-sdk';
const descopeClient = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });
// Add managementKey only for admin operations:
// DescopeClient({ projectId: '...', managementKey: process.env.DESCOPE_MANAGEMENT_KEY })
```

Session middleware:
```js
// Before (aws-jwt-verify)
async function verifyToken(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  try {
    const payload = await verifier.verify(token);
    req.user = payload; // sub, email, cognito:username, cognito:groups
    next();
  } catch { res.status(401).json({ error: 'Invalid token' }); }
}

// After (Descope)
async function verifySession(req, res, next) {
  const sessionToken = req.headers.authorization?.split('Bearer ')[1] || req.cookies?.DS;
  const refreshToken = req.cookies?.DSR;
  if (!sessionToken) return res.status(401).json({ error: 'Unauthorized' });
  try {
    const authInfo = await descopeClient.validateAndRefreshSession(sessionToken, refreshToken);
    req.user = authInfo.token; // sub, email, roles, permissions, tenants, custom claims
    next();
  } catch { res.status(401).json({ error: 'Invalid or expired session' }); }
}
```

User management (replaces AWS SDK admin calls):
```js
// Before (AWS SDK)
import { CognitoIdentityProviderClient, AdminGetUserCommand,
         AdminAddUserToGroupCommand, AdminUserGlobalSignOutCommand } from '@aws-sdk/client-cognito-identity-provider';
await client.send(new AdminGetUserCommand({ UserPoolId: '...', Username: email }));
await client.send(new AdminAddUserToGroupCommand({ UserPoolId: '...', Username: email, GroupName: 'admin' }));
await client.send(new AdminUserGlobalSignOutCommand({ UserPoolId: '...', Username: email }));

// After (Descope)
await descopeClient.management.user.load(loginId);
await descopeClient.management.user.setRoles(loginId, ['admin']);
await descopeClient.management.user.logout(userId);
```

Dual-validation middleware (deploy during cutover when both token types circulate):
```js
async function verifyAnyToken(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });

  const unverifiedIss = JSON.parse(
    Buffer.from(token.split('.')[1], 'base64url').toString()
  ).iss ?? '';

  try {
    if (unverifiedIss.includes('api.descope.com')) {
      const authInfo = await descopeClient.validateSession(token);
      req.user = { ...authInfo.token, source: 'descope' };
    } else if (unverifiedIss.includes('cognito-idp.amazonaws.com')) {
      const payload = await cognitoVerifier.verify(token);
      req.user = { sub: payload.sub, email: payload.email, source: 'cognito' };
    } else {
      throw new Error('Unknown issuer');
    }
    next();
  } catch { res.status(401).json({ error: 'Invalid token' }); }
}
```

Cookie clearing for Next.js / SSR cutover (force re-authentication by clearing Cognito cookies):
```ts
// middleware.ts
const cognitoCookiePattern = /^CognitoIdentityServiceProvider\./;
const hasCognitoCookie = [...request.cookies.keys()].some(k => cognitoCookiePattern.test(k));
if (hasCognitoCookie) {
  const response = NextResponse.redirect(new URL('/login', request.url));
  [...request.cookies.keys()]
    .filter(k => cognitoCookiePattern.test(k))
    .forEach(k => response.cookies.delete(k));
  return response;
}
```

**Notes:**
- Remove the Cognito verifier from dual-validation middleware once `source: 'cognito'` log entries reach zero for a full business day.
- `validateAndRefreshSession(sessionToken, refreshToken)` auto-refreshes if the session token is expired and a valid refresh token is provided. Use `validateSession(token)` when no refresh token is available.

---

### Python / Flask backend

**Changes:**
```bash
pip uninstall cognitojwt python-jose --yes
pip install descope
# Update requirements.txt: remove cognitojwt, python-jose; add descope
```

Initialize:
```python
# Before (cognitojwt)
import cognitojwt
claims = cognitojwt.decode(token, COGNITO_REGION, COGNITO_USER_POOL_ID)

# Before (python-jose — manual JWKS)
from jose import jwk, jwt as jose_jwt
jwks = requests.get(f'https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json').json()
claims = jose_jwt.decode(token, jwks, algorithms=['RS256'], audience=client_id)

# After (Descope)
from descope import DescopeClient, AuthException
descope_client = DescopeClient(project_id=os.environ['DESCOPE_PROJECT_ID'])
# With management operations:
# DescopeClient(project_id='...', management_key=os.environ['DESCOPE_MANAGEMENT_KEY'])
```

Auth decorator:
```python
from functools import wraps
from flask import request, jsonify
from descope import DescopeClient, AuthException

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not session_token:
            session_token = request.cookies.get('DS', '')
        if not session_token:
            return jsonify({'error': 'Unauthorized'}), 401
        try:
            jwt_response = descope_client.validate_session(session_token=session_token)
            request.user = jwt_response  # dict: sub, email, roles, custom claims
        except AuthException:
            return jsonify({'error': 'Invalid or expired token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/profile')
@require_auth
def profile():
    return jsonify({'id': request.user['sub'], 'email': request.user.get('email')})
```

Dual-validation (Python, for cutover):
```python
import base64, json
from descope import DescopeClient, AuthException
import cognitojwt

descope_client = DescopeClient(project_id=os.environ['DESCOPE_PROJECT_ID'])

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Unauthorized'}), 401
        try:
            payload_part = token.split('.')[1]
            payload_part += '=' * (-len(payload_part) % 4)
            iss = json.loads(base64.b64decode(payload_part)).get('iss', '')
        except Exception:
            return jsonify({'error': 'Malformed token'}), 401

        if 'api.descope.com' in iss:
            try:
                claims = descope_client.validate_session(session_token=token)
                request.user = {**claims, 'source': 'descope'}
                return f(*args, **kwargs)
            except AuthException:
                return jsonify({'error': 'Invalid Descope token'}), 401
        else:
            try:
                claims = cognitojwt.decode(token, os.environ['AWS_REGION'], os.environ['COGNITO_USER_POOL_ID'])
                request.user = {'sub': claims['sub'], 'email': claims.get('email'), 'source': 'cognito'}
                return f(*args, **kwargs)
            except Exception:
                return jsonify({'error': 'Invalid token'}), 401
    return decorated
```

User management:
```python
# Before (boto3)
import boto3
cognito = boto3.client('cognito-idp', region_name='us-east-1')
cognito.admin_get_user(UserPoolId=pool_id, Username=email)
cognito.admin_add_user_to_group(UserPoolId=pool_id, Username=email, GroupName='admin')
cognito.admin_user_global_sign_out(UserPoolId=pool_id, Username=email)

# After (Descope)
resp = descope_client.mgmt.user.load(login_id='user@example.com')
resp_by_id = descope_client.mgmt.user.load_by_user_id(user_id='U2abc...')
descope_client.mgmt.user.set_roles(login_id='user@example.com', roles=['admin'])
descope_client.mgmt.user.logout_user(user_id='U2abc...')
```

**Notes:**
- `validate_session()` returns a `dict` with JWT claims. `sub`, `roles`, `permissions` are present by default; `email` and `name` require a JWT Template.
- Descope's Python SDK requires Python 3.7+.

**Limitation:**
- The Python SDK's `validate_session()` return type is underdocumented — a `dict` with JWT claims in practice, but type annotations lag. Verify against the [Python SDK](https://github.com/descope/python-sdk) for current signatures.

---

## Infrastructure

### User migration commands and JIT setup

**Full migration** — Descope migration tool:
```bash
git clone https://github.com/descope/descope-migration.git /tmp/descope-migration
cd /tmp/descope-migration
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt --quiet
```

Write `.env` for the tool:
```
DESCOPE_PROJECT_ID=<your project ID>
DESCOPE_MANAGEMENT_KEY=<your management key>
AWS_REGION=<e.g. us-east-1>
AWS_ACCESS_KEY_ID=<IAM key with cognito-idp:ListUsers, ListGroups, ListUsersInGroup>
AWS_SECRET_ACCESS_KEY=<IAM secret>
COGNITO_USER_POOL_ID=<e.g. us-east-1_XXXXXXXXX>
```

```bash
python3 src/main.py cognito --dry-run   # preview: user count, group count, FORCE_CHANGE_PASSWORD count
python3 src/main.py cognito             # live import — confirm dry-run output before running
```

The tool automatically: converts Cognito User Groups → Descope Roles, imports all standard and `custom:*` attributes, stores the original Cognito `sub` as `cognitoSub` custom attribute.

**Multiple pools**: Create a Descope Tenant per pool in Console → Tenants before importing. Run the tool once per pool.

**JIT migration** — preserves user passwords via Generic HTTP Connector:

1. Create a **Generic HTTP Connector** in Descope Console:
   - Base URL: `https://cognito-idp.<REGION>.amazonaws.com`
   - Headers: `Content-Type: application/x-amz-json-1.1`, `X-Amz-Target: AWSCognitoIdentityProviderService.InitiateAuth`
   - Method: POST
   - Body template:
   ```json
   {
     "ClientId": "<COGNITO_APP_CLIENT_ID>",
     "AuthFlow": "USER_PASSWORD_AUTH",
     "AuthParameters": { "USERNAME": "{{form.email}}", "PASSWORD": "{{form.password}}" }
   }
   ```

2. **If App Client secret is present** (`COGNITO_CLIENT_SECRET` in env files), deploy a proxy:
   ```js
   const crypto = require('crypto');
   function getSecretHash(username) {
     return crypto.createHmac('sha256', process.env.COGNITO_CLIENT_SECRET)
       .update(username + process.env.COGNITO_APP_CLIENT_ID)
       .digest('base64');
   }
   // Compute SECRET_HASH and add to AuthParameters before proxying to Cognito
   ```
   Point the Descope Connector at the proxy URL instead of Cognito directly.

3. Build the JIT Flow in Descope Console:
   - Check if user exists in Descope → if yes, skip Cognito and use normal sign-in
   - For new users: collect email + password → call Cognito Connector
   - On Cognito success: provision user in Descope → set `freshlyMigrated = false`
   - On Cognito failure: route to magic link or OTP (also handles `FORCE_CHANGE_PASSWORD` users)

---

### AWS API Gateway authorizer swap

**Step 1** — Enable the API Gateway-compatible JWT template in Descope:

Console → Project Settings → JWT Templates → select the **AWS API Gateway** template. This sets the `iss` claim to the format API Gateway requires for OIDC discovery.

**Step 2** — HTTP API: replace the Cognito User Pool authorizer with a JWT Authorizer:

- **Issuer URL**: `https://api.descope.com/<YOUR_PROJECT_ID>` (Project ID starts with `P`)
- **Audience**: `<YOUR_PROJECT_ID>`
- **Token source**: `$request.header.Authorization`

**REST API**: Use a Lambda authorizer. For dual-validation during cutover:

```js
const { CognitoJwtVerifier } = require('aws-jwt-verify');
const DescopeClient = require('@descope/node-sdk');

const cognitoVerifier = CognitoJwtVerifier.create({
  userPoolId: process.env.COGNITO_USER_POOL_ID,
  tokenUse: 'access',
  clientId: process.env.COGNITO_CLIENT_ID,
});
const descopeClient = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });

exports.handler = async (event) => {
  const token = event.authorizationToken?.replace('Bearer ', '');
  if (!token) return generatePolicy('user', 'Deny', event.methodArn);

  const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString());
  try {
    if ((payload.iss || '').includes('cognito-idp')) {
      await cognitoVerifier.verify(token);
    } else {
      await descopeClient.validateSession(token);
    }
    return generatePolicy('user', 'Allow', event.methodArn);
  } catch {
    return generatePolicy('user', 'Deny', event.methodArn);
  }
};

function generatePolicy(principalId, effect, resource) {
  return {
    principalId,
    policyDocument: {
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: effect, Resource: resource }]
    }
  };
}
```

---

### Cognito Identity Pools

Descope does not replace Identity Pools. Configure Descope as a federated OIDC identity provider in the existing Identity Pool:

- Descope OIDC endpoint: `https://api.descope.com/{projectId}`
- Modify the Identity Pool trust policy to accept tokens from Descope's issuer
- Users authenticate via Descope, then exchange the Descope session token for temporary AWS IAM credentials through the Identity Pool as before

---

### Hosted UI and federation paths

**Self-use only** (Cognito Hosted UI used only for the app's own login, no external clients):

Remove the `oauth:` block from `Amplify.configure`. Replace the login redirect trigger with:
```jsx
import { Descope } from '@descope/react-sdk';
<Descope
  flowId="sign-up-or-in"
  onSuccess={() => navigate('/dashboard')}
  onError={(e) => console.error(e)}
/>
```

Manual: add original `redirectSignIn` URLs to Console → Project Settings → Allowed Redirect URLs.

**Cognito as OAuth Authorization Server** (external clients redirect to your Cognito domain for authorization):

External clients must update their authorization endpoint to Descope. Configure in Console → Applications → Create OIDC Application. Descope endpoints:
- Authorization: `https://api.descope.com/oauth2/v1/authorize`
- Token: `https://api.descope.com/oauth2/v1/token`
- JWKS: `https://api.descope.com/v2/keys/<PROJECT_ID>`

> `https://api.descope.com/oauth2/v1/callback` does **not** exist — do not use it as a callback URL when configuring an IdP.

**Single SAML IdP**:

Remove `Auth.federatedSignIn({ provider: '<SAMLProviderName>' })`. Replace with `<Descope flowId="sign-up-or-in" />`.

Manual: Console → SSO Applications → configure SAML with IdP metadata. Update IdP with Descope ACS URL (found in Console → SSO → [tenant] → SP Settings — **tenant-specific, not a global URL**) and Entity ID.

**Multi-tenant SAML** (email domain → tenant → IdP routing):

Remove domain-routing logic and any pre-signup Lambda domain validation. Replace with `<Descope flowId="sign-up-or-in" />`.

Manual: Create Descope Tenant per customer org, configure SAML connection per tenant, set email domain(s) per tenant. Add an SSO step to the Sign-Up or In Flow.

**SSO Setup Suite**: For B2B apps where tenant admins configure their own IdP, the SSO Setup Suite replaces `management.sso.configureSAMLByTenant()` / `configureOIDCByTenant()` calls with a guided no-code Console wizard. Surface this option before migrating any Management SDK SSO code.

---

### M2M: Access Keys

Replace Cognito's App Client client credentials flow with Descope Access Keys:

```js
// Before (Cognito client credentials)
const response = await fetch(`https://${COGNITO_DOMAIN}/oauth2/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: CLIENT_ID,
    client_secret: CLIENT_SECRET,
  }),
});

// After (Descope Access Key)
import DescopeClient from '@descope/node-sdk';
const descopeClient = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });
const { data } = await descopeClient.auth.exchangeAccessKey(process.env.DESCOPE_ACCESS_KEY);
// data.sessionToken contains the JWT — validate on the receiving service with validateSession()
```

Create Access Keys: Console → Company → Access Keys, or programmatically:
```js
await descopeClient.management.accessKey.create(name, expireTime, roles, keyTenants);
```

---

## Reference

### Auth method equivalents

| Cognito / Amplify | Descope | Notes |
|---|---|---|
| `Auth.signIn(user, pass)` | `<Descope flowId="sign-up-or-in" />` | Flow handles all auth methods |
| `Auth.signUp(...)` | Same Flow | Detects new vs returning user |
| `Auth.forgotPassword(email)` | Built into Descope Flow | Remove — no code equivalent needed |
| `Auth.confirmForgotPassword(...)` | Built into Descope Flow | Remove |
| `Auth.resendSignUp(username)` | Built into Descope Flow | Remove |
| `Auth.confirmSignUp(username, code)` | Built into Descope Flow | Remove |
| `Auth.signOut()` | `logout()` from `useDescope()` | |
| `Auth.signOut({ global: true })` | `descopeClient.management.user.logout(userId)` | Backend call |
| `Auth.currentAuthenticatedUser()` | `useSession()` + `useUser()` | |
| `Auth.currentSession()` | `useSession()` — `session.token` | Auto-refreshed |
| `fetchAuthSession()` (v6) | `useSession()` — `session.token` | |
| `Auth.changePassword(user, old, new)` | `descopeClient.password.update(loginId, newPwd)` | Backend management call |
| `Auth.updateUserAttributes(user, attrs)` | `descopeClient.management.user.update(loginId, attrs)` | |
| `Auth.deleteUser()` | `descopeClient.management.user.delete(loginId)` | |
| `Amplify.configure({ Auth: ... })` | `<AuthProvider projectId="...">` | |
| `withAuthenticator` HOC | `<Descope flowId="sign-up-or-in" />` | |
| `<Authenticator>` component | `<Descope flowId="sign-up-or-in" />` | |
| `Hub.listen('auth', ...)` | `useSession().isAuthenticated` (reactive) | No listener setup needed |
| `CognitoJwtVerifier.create(...)` | `DescopeClient({ projectId })` | Node.js backend |
| `cognitoVerifier.verify(token)` | `descopeClient.validateSession(token)` | |
| `cognitojwt.decode(...)` | `descope_client.validate_session(...)` | Python backend |
| `AdminAddUserToGroupCommand` | `management.user.setRoles(loginId, roles)` | |
| `AdminUserGlobalSignOutCommand` | `management.user.logout(userId)` | |
| Cognito User Groups | Descope Roles | Auto-converted by migration tool |
| `custom:*` attributes | Descope custom attributes | Define schema in Console first |
| `cognito:username` claim | `sub` claim | Different UUID value |
| `cognito:groups` claim | `authInfo.token.roles` / `validateRoles()` | |
| Cognito Hosted UI | Descope Flow (embeddable) | No external redirect required |
| Pre-Token Generation trigger | JWT Templates | Console → Project Settings → JWT Templates |
| Cognito User Pool authorizer (API GW) | Descope JWT authorizer | See Infrastructure section |

---

### Terminology mapping

| AWS Cognito | Descope |
|---|---|
| User Pool | Project |
| User Pool ID (`us-east-1_XXXX`) | Project ID (`Pxxx...`) |
| App Client | Inbound Application (or uses Project ID directly) |
| App Client secret | Not needed for frontend flows; Management Key for admin ops |
| User Group | Role |
| Identity Pool | Not replaced — federate with Descope as OIDC provider |
| Hosted UI | Descope Flow (embeddable component) |
| Lambda Trigger | Flow step / Connector / Webhook |
| Pre-Token Generation | JWT Template |
| `custom:*` attribute | Custom Attribute (define schema in Console → Users → Attributes) |
| `cognito:username` | `sub` (Descope user ID UUID) |
| `cognito:groups` | JWT `roles` array or checked via `validateRoles()` SDK method |
| JWKS URL | `https://api.descope.com/v2/keys/{projectId}` |
| Admin operations (boto3/AWS SDK) | Descope Management SDK (node-sdk, python-sdk, go-sdk) |
| Management Key | Descope Management Key (`Kxxx...`) |
| Cognito Adaptive Authentication | Descope Flow-based security connectors |

---

### Environment variables

Back up all `.env` files before modifying:
```bash
for f in <all .env files found>; do cp "$f" "$f.cognito-backup"; done
```

Comment out Cognito vars (prefix with `# REMOVED - Cognito migration`):
```
COGNITO_USER_POOL_ID
COGNITO_APP_CLIENT_ID
COGNITO_CLIENT_SECRET
COGNITO_REGION
AWS_USER_POOL_ID
AWS_USER_POOL_CLIENT_ID
NEXT_PUBLIC_USER_POOL_ID
NEXT_PUBLIC_USER_POOL_CLIENT_ID
NEXT_PUBLIC_AWS_REGION
REACT_APP_USER_POOL_ID
REACT_APP_USER_POOL_CLIENT_ID
VITE_USER_POOL_ID
VITE_USER_POOL_CLIENT_ID
```

Add only the vars relevant to the detected stack:
```bash
VITE_DESCOPE_PROJECT_ID=Pxxx...           # React/Vite
NEXT_PUBLIC_DESCOPE_PROJECT_ID=Pxxx...   # Next.js (client-side)
REACT_APP_DESCOPE_PROJECT_ID=Pxxx...     # Create React App
DESCOPE_PROJECT_ID=Pxxx...               # Backend / server-side
DESCOPE_MANAGEMENT_KEY=Kxxx...           # Only for admin/management operations
```

**Project ID** (starts with `P`): Console → Project Settings → Project ID
**Management Key** (starts with `K`): Console → Company → Management Keys → Create New Key

> **NEVER** expose `DESCOPE_MANAGEMENT_KEY` in a client-accessible env var (`NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`). Management keys have full read/write access to all users in the project.

---

### Migration checklist

**Pre-migration**
- [ ] Audit all Cognito Lambda triggers — document business logic for each
- [ ] Identify if Identity Pools are used (separate concern from User Pool migration)
- [ ] Identify Amplify v5 vs v6 in frontend codebase
- [ ] Check if App Client has a client secret (`COGNITO_CLIENT_SECRET` in env files)
- [ ] Note users with `FORCE_CHANGE_PASSWORD` status (surfaces in migration tool dry-run)
- [ ] Pre-create custom attribute schema in Console (for `custom:*` attrs) before importing users
- [ ] Create Descope project and configure auth flows in Console
- [ ] Configure social connectors (Google, Apple, etc.) in Console
- [ ] If Pre-Token Generation Lambda: recreate claims in JWT Templates before cutover
- [ ] Plan password strategy: JIT migration (preserve) vs full migration (force reset)

**User migration**
- [ ] Run `python3 src/main.py cognito --dry-run` — verify user count, group count, FORCE_CHANGE_PASSWORD count
- [ ] Run live import and verify user count in Descope Console
- [ ] Confirm Cognito Groups → Descope Roles mapping is correct
- [ ] Plan DB remapping if Cognito `sub` is stored as a FK in any table

**Backend**
- [ ] Replace Cognito JWT validation (`aws-jwt-verify` / `cognitojwt`) with Descope SDK
- [ ] Replace `cognito:groups` claim checks with `descopeClient.validateRoles()`
- [ ] Replace all `cognito:username` reads with `sub`
- [ ] Replace AWS SDK admin operations with Descope management SDK
- [ ] Update AWS API Gateway: replace Cognito authorizer with Descope JWT authorizer
- [ ] Recreate Lambda trigger logic in Flows/Connectors/Webhooks
- [ ] Update environment variables
- [ ] Deploy dual-token validation middleware if running a gradual cutover

**Frontend**
- [ ] Remove Amplify/Cognito packages; install Descope SDK
- [ ] Replace `Amplify.configure()` with `<AuthProvider projectId="...">`
- [ ] Replace `Auth.currentAuthenticatedUser()` / `getCurrentUser()` with `useSession()` + `useUser()`
- [ ] Replace `Auth.currentSession()` / `fetchAuthSession()` with `session.token` from `useSession()`
- [ ] Replace `<Authenticator>` / custom sign-in forms with `<Descope flowId="sign-up-or-in" />`
- [ ] Replace `Auth.signOut()` with `logout()` from `useDescope()`
- [ ] Remove all `Hub.listen('auth', ...)` listeners
- [ ] Update all environment variables

**Go-live**
- [ ] Deploy dual-validation middleware to production
- [ ] Deploy frontend with Descope SDK
- [ ] Monitor `source: 'cognito'` log entries — remove dual-validation once zero for a full business day
- [ ] Decommission Cognito User Pool
- [ ] Remove Cognito packages and commented-out env vars

---

### Useful links

| Resource | URL |
|---|---|
| Descope Cognito migration guide | https://docs.descope.com/migrate/cognito |
| Descope migration tool | https://github.com/descope/descope-migration |
| React SDK | https://docs.descope.com/getting-started/react |
| Next.js SDK | https://docs.descope.com/getting-started/nextjs |
| Node.js SDK | https://github.com/descope/node-sdk |
| Python SDK | https://github.com/descope/python-sdk |
| Go SDK | https://github.com/descope/go-sdk |
| Backend session validation | https://docs.descope.com/authorization/session-management/session-validation/backend |
| JWT Templates | https://docs.descope.com/management/jwt-templates |
| AWS API Gateway JWT authorizer | https://docs.descope.com/authorization/session-management/session-validation/oidc-jwt-authorizers/aws-jwt-authorizer |
| Generic HTTP Connector (JIT) | https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http |
| Descope Console | https://app.descope.com |
| User Attribute Schema | https://app.descope.com/users/attributes |
| OIDC endpoints reference | https://docs.descope.com/getting-started/oidc-endpoints |
