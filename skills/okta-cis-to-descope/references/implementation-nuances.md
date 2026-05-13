# Descope Migration: Implementation Notes (Okta CIS)

## Contents

**General Insights — Architecture & Flow**
- [Okta owns the redirect; Descope validates tokens](#okta-owns-the-redirect-descope-validates-tokens)
- [Inbound Apps vs. Federated Apps: the core strategy fork](#inbound-apps-vs-federated-apps-the-core-strategy-fork)
- [OIDC compatibility path](#oidc-compatibility-path-alternative-to-full-migration)
- [scp vs. scope claim](#scp-vs-scope-claim)
- [No drop-in middleware](#no-drop-in-middleware)

**General Insights — Feature Mapping: Okta CIS → Descope**
- [Applications → Inbound Apps / Federated Apps](#applications--inbound-apps--federated-apps)
- [Authentication Policies → Flows](#authentication-policies--flows)
- [Authenticators → Auth Methods + Flow steps](#authenticators--auth-methods--flow-steps)
- [Identity Providers → Tenant SSO](#identity-providers--tenant-sso)
- [Authorization Servers → Resources](#authorization-servers--resources)
- [Custom Claims → JWT Templates](#custom-claims-expression-language--jwt-templates)
- [Log Streams → Audit Connectors](#log-streams--audit-connectors)
- [Service Apps → Access Keys](#service-apps--access-keys)
- [Groups / RBAC → Descope Roles](#groups--rbac--descope-roles)
- [User migration](#user-migration)

**General Insights — Common Gotchas**
- [JWT claims differ (scp, sub, no email by default)](#jwt-claims-differ)
- [Audience validation is opt-in](#audience-validation-is-opt-in)
- [One session token, not two](#one-session-token-not-two)
- [Logout is two steps](#logout-is-two-steps)
- [Env var reduction](#env-var-reduction)

**Framework Sections**
- [React + @okta/okta-react](#react--okta-okta-react)
- [Angular + @okta/okta-angular](#angular--okta-okta-angular)
- [Vue + @okta/okta-vue](#vue--okta-okta-vue)
- [Node.js / Express + @okta/oidc-middleware](#nodejs--express--okta-oidc-middleware)
- [Backend JWT validation (okta-jwt-verifier)](#backend-jwt-validation-okta-jwt-verifier)
- [Next.js](#nextjs)
- [Custom / open-source OIDC clients](#custom--open-source-oidc-clients)

- [Testing checklist](#testing-checklist)

> **See also:** `flows-and-widgets.md` in this directory — Okta→Descope lingo map, Flow structure and templates, Widget types, SSO Setup Suite, and the Console-vs-code decision guide. Read it before migrating any auth UI, MFA enrollment, user management pages, or SSO configuration.

---

## General Insights

**— Architecture & Flow —**

### Okta owns the redirect; Descope validates tokens

Okta CIS is a redirect-based OIDC provider. The app redirects the user to Okta's hosted
sign-in page, Okta authenticates, issues an authorization code, and the app exchanges it
for tokens via the token endpoint. The frontend SDK (`okta-auth-js`) and middleware packages
(`@okta/oidc-middleware`) handle this ceremony.

Descope splits the work differently. The frontend ([Descope Flows](https://docs.descope.com/flows)
via [web components](https://docs.descope.com/client-sdk/descope-components) or [client SDKs](https://docs.descope.com/client-sdk/initialize-sdk))
runs the authentication ceremony embedded in the app and stores JWTs in `DS` (session) and
`DSR` (refresh) cookies. The backend [validates those JWTs](https://docs.descope.com/authorization/session-management/session-validation/backend).
No redirect to an external login page, no authorization code exchange, no server-managed session store.

Every Okta→Descope migration adds a dedicated login page (or embeds the `<Descope>` component)
and removes the redirect/callback plumbing.

**Exception:** Descope can also act as a [standard OIDC provider](https://docs.descope.com/getting-started/oidc-endpoints).
If you want to preserve existing OIDC client code (e.g., `openid-client`, `passport-openidconnect`,
`@okta/oidc-middleware`), you can point it at Descope's OIDC endpoints instead of Okta's.
See the OIDC compatibility path section below.

---

### Inbound Apps vs. Federated Apps: the core strategy fork

This is the most important architectural decision in an Okta CIS migration. Make it before
writing any code.

**The signal: does the backend validate scopes?**

If any backend service reads the `scp` claim from the Okta access token and uses it to make
authorization decisions (e.g., allows `read:invoices` but not `write:invoices`) → **Inbound Apps**.

If the backend only validates the JWT's signature and expiry (confirming the user is authenticated,
but not checking which scopes are present) → **Federated Apps** (simpler path).

**Inbound Apps path:**
- Use when app enforces strict OAuth scopes for user-facing or M2M clients
- The Descope Inbound App defines the allowed scopes and audience
- Scope-based access control lives in Inbound App authorization rules (not the Resource)
- Access tokens are issued by Descope with the scopes the Inbound App permits
- Custom claims (Okta Expression Language) → JWT Template on the Inbound App

**Federated Apps path (OIDC compatibility layer):**
- Use when Okta acts purely as an authentication layer — the backend validates identity, not scopes
- Descope acts as an OIDC provider; the existing OIDC client library is pointed at Descope endpoints
- Minimum code change; suitable as an incremental first step
- Descope-native SDK migration can happen in a later phase

If the app has both — some clients using scopes, others not — use Inbound Apps for scope-enforcing
clients and Federated Apps for the rest. Resolve this per-client, not globally.

---

### OIDC compatibility path (alternative to full migration)

Descope exposes standard [OIDC endpoints](https://docs.descope.com/getting-started/oidc-endpoints):

| Endpoint | Okta | Descope |
|---|---|---|
| Issuer | `https://YOUR_DOMAIN.okta.com/oauth2/default` | `https://api.descope.com/YOUR_PROJECT_ID` |
| Authorization | `https://YOUR_DOMAIN.okta.com/oauth2/v1/authorize` | `https://api.descope.com/oauth2/v1/authorize` |
| Token | `https://YOUR_DOMAIN.okta.com/oauth2/v1/token` | `https://api.descope.com/oauth2/v1/token` |
| UserInfo | `https://YOUR_DOMAIN.okta.com/oauth2/v1/userinfo` | `https://api.descope.com/oauth2/v1/userinfo` |
| JWKS | `https://YOUR_DOMAIN.okta.com/oauth2/v1/keys` | `https://api.descope.com/YOUR_PROJECT_ID/.well-known/jwks.json` |
| End Session | `https://YOUR_DOMAIN.okta.com/oauth2/v1/logout` | `https://api.descope.com/oauth2/v1/logout` |

An app using `openid-client` or `@okta/oidc-middleware` can swap `OKTA_ISSUER` to
`https://api.descope.com/YOUR_PROJECT_ID` and keep the existing OIDC client code intact.
Claim shape differences (`scp` vs `scope`, `email_verified` behavior, etc.) still require
testing and adjustment, but it's a viable incremental path.

---

### scp vs. scope claim

Okta access tokens include scopes in the `scp` claim as a JSON array of strings:
```json
{ "scp": ["read:invoices", "write:invoices"] }
```

Descope uses the `scope` claim, which may be a JSON array or a space-separated string:
```json
{ "scope": "read:invoices write:invoices" }
```
or
```json
{ "scope": ["read:invoices", "write:invoices"] }
```

Any backend code that reads `token.scp`, `claims["scp"]`, or similar must be updated to
read `token.scope` (and handle both formats if the value may be a string). Check your
scope-parsing middleware carefully — this is a silent correctness bug, not a compile error.

---

### No drop-in middleware

Okta's `@okta/oidc-middleware` for Express mounts `/login`, `/logout`, and `/authorization-code/callback`
automatically and attaches `req.userContext`. Descope has no Express middleware package.
The replacement is ~20 lines of custom middleware:

1. Add `cookie-parser` (Descope session is in the `DS` cookie)
2. Write middleware: read `DS` cookie → call `descopeClient.validateSession()` → attach claims to `req`
3. Write a `requireAuth` guard (3 lines)

---

**— Feature Mapping: Okta CIS → Descope —**

### Applications → Inbound Apps / Federated Apps

| Okta app type | Descope equivalent | When to use |
|---|---|---|
| Web App (authorization code) | Federated App | No scope enforcement needed |
| SPA (authorization code + PKCE) | Federated App | No scope enforcement needed |
| Web App / SPA with scope validation | Inbound App | Backend checks `scp` claims |
| Native / Mobile | Federated App or Inbound App | Same signal: scope validation? |
| Service App / API Services (M2M) | Access Key | Client credentials flow |

Console path: **Applications → Inbound Apps** or **Applications → Federated Applications**.

---

### Authentication Policies → Flows

Okta has **three distinct policy types**. Treat each separately — they have different Descope migration targets and different levels of complexity.

Source: [developer.okta.com/docs/api/openapi/okta-management/management/tag/Policy](https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Policy/)

#### Sign-On Policies (per-app) → Flow

Fetching:
```bash
curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=ACCESS_POLICY"
```

Sign-On Policies define per-app authentication rule chains. Each rule has conditions (group membership, network zone, device context) and a resulting action (allow, require factor, deny). In Descope, each rule becomes a Condition branch in a Flow, and each factor requirement becomes an auth method step.

| Okta Sign-On Policy rule | Descope Flow equivalent |
|---|---|
| Require factor X | Auth method step |
| Condition: user in group Y | Condition on `user.roles` |
| Condition: network zone | Condition on request IP/context |
| Deny access | Condition → End (failure) |
| Post-auth Inline Hook | Flow Scriptlet or Generic HTTP Connector |

One Sign-On Policy typically maps to one Flow. Apps with multiple policies (e.g., different policies for different app integrations) typically map to one Flow per distinct auth experience.

#### Authenticator Enrollment Policies → Flow (MFA step or subflow)

Fetching:
```bash
curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=MFA_ENROLL"
```

Authenticator Enrollment Policies control when users must enroll in MFA and which factors are required vs. optional. In Descope, **enrollment is inline** — it happens during the sign-in Flow, not through a separate journey.

Migration approach:
- For **required** authenticators: add an MFA step to the main sign-in Flow. If the user hasn't enrolled, the Flow handles enrollment inline.
- For **optional** authenticators: add a conditional MFA step or a subflow triggered by group membership or risk context.
- For **context-sensitive enrollment** (e.g., require MFA only for admins): use a Condition branch → subflow pattern.

Note: Passkeys and TOTP cannot be migrated from Okta (see Authenticators section). Users must reprovision these factors after cutover — add a re-enrollment prompt to the Flow conditioned on `freshlyMigrated: true`.

#### Global Session Policies → Project session config

Fetching:
```bash
curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/policies?type=OKTA_SIGN_ON"
```

Global Session Policies control session lifetime, idle timeout, and re-authentication requirements. These do **not** map to Flows — they map to Descope's project-level session settings.

In Descope: Console → **Project → Session Management**. Set:
- Session token lifetime → match Okta's `maxSessionLifetimeMinutes`
- Refresh token lifetime → match Okta's idle session duration

Re-authentication requirements (e.g., step-up after N minutes) can be implemented using the `step-up` Flow template and the `su` JWT claim.

---

### Authenticators → Auth Methods + Flow steps

Okta Authenticators are the factors users can enroll and use. Each maps to a Descope
Auth Method configured in the Console and a corresponding step in a Flow.

| Okta Authenticator | Descope Auth Method | Notes |
|---|---|---|
| Passkeys (FIDO2 WebAuthn) | Passkeys (WebAuthn) | Console → Authentication → Passkeys |
| Okta Verify (push notification) | — | No direct equivalent; use Email Magic Link or TOTP instead |
| TOTP (Google Authenticator, Okta Verify TOTP mode) | TOTP | Console → Authentication → TOTP |
| Password | Password | Console → Authentication → Password |
| Phone (SMS, Voice) | SMS OTP | Console → Authentication → SMS |
| Email (magic link or OTP) | Email OTP / Magic Link | Console → Authentication → Email |
| Security Question | — | No equivalent; consider removing or replacing with another factor |
| Smart Card | — | Contact Descope support for enterprise smart card use cases |

**Critical: Passkeys and TOTP cannot be migrated.** Okta does not expose passkey credentials or TOTP seeds to third parties. Users who enrolled these in Okta must reprovision them in Descope after migration. Plan for this explicitly:
- Add a `freshlyMigrated` custom attribute (set to `true` on import)
- Add a re-enrollment step to the sign-in Flow, conditioned on `freshlyMigrated: true`, that guides users through enrolling a new passkey or TOTP authenticator
- Set `freshlyMigrated` to `false` once enrollment is complete

Source: [developer.okta.com/docs/guides/authenticators-overview](https://developer.okta.com/docs/guides/authenticators-overview/main/)

---

### Identity Providers → Tenant SSO

Okta Identity Providers (external SAML or OIDC per customer org) map to Descope Tenant SSO.

**Key advantage:** Descope can consume the existing IdP response using the **same ACS URL** already configured in each customer's IdP. Tenant admins do not need to reconfigure their SAML or OIDC settings — the cutover is transparent to them. This is achieved via DNS redirect (pointing `auth.yourdomain.com` from Okta to Descope). See [docs.descope.com/migrate/sso](https://docs.descope.com/migrate/sso) for the full DNS redirect and testing process.

**Preferred approach — SSO Setup Suite:** Before migrating Management SDK SSO calls, ask
whether the SSO Setup Suite removes the need for that code. The SSO Setup Suite is a no-code
Console wizard that guides tenant admins through per-tenant SAML/OIDC configuration with
step-by-step IdP-specific instructions — no engineering involvement needed for new tenant SSO
onboarding.

**SDK path (when programmatic SSO is needed):**

| Okta | Descope |
|---|---|
| Configure SAML IdP via API | `management.sso.configureSAMLByTenant(tenantId, settings)` |
| Configure OIDC IdP via API | `management.sso.configureOIDCByTenant(tenantId, settings)` |
| Per-org SAML connection | Per-tenant SSO (Console → SSO or Management SDK) |

See `flows-and-widgets.md` → SSO Setup Suite for the decision guide.

---

### Authorization Servers → Resources

Okta Authorization Servers define OAuth audiences and scopes. Descope's equivalent is the
Resources feature (relatively new — verify current behavior via the Descope Docs MCP).

**Key facts:**
- The audience is immutable in both Okta and Descope. Recreate the Resource with the same audience string.
- Scopes defined on the Okta Authorization Server → scopes defined on the Descope Inbound App
  (not on the Resource itself in Descope).
- The Resource in Descope represents the protected API/service; the Inbound App controls which
  clients can request which scopes.

**scp claim note:** Okta access tokens use `scp` (JSON array). Descope uses `scope` (array
or space-separated string). Backend scope-validation code must be updated.

---

### Custom Claims (Expression Language) → JWT Templates

In Okta, custom claims are defined at the Authorization Server level using Okta Expression
Language (e.g., `user.profile.department`, `user.roles`). These claims appear in access or
ID tokens depending on the claim's "Include in token type" setting.

In Descope, custom claims are defined in **JWT Templates** — associated with an Inbound App or
the project — and expressed as a JSON template with `{{user.*}}` interpolation:

```json
{
  "email": "{{user.email}}",
  "name": "{{user.name}}",
  "department": "{{user.customAttributes.department}}"
}
```

Console path: **Authorization → JWT Templates → New Template**. Apply the template to the
relevant Inbound App.

**Key difference:** In Okta, custom claims can be attached at the Resource level. In Descope,
JWT Templates are always on the Inbound App or project — never on the Resource.

---

### Log Streams → Audit Connectors

Okta Log Streams support two direct destinations:
- **Splunk Cloud** → Descope Splunk Audit Connector (available OOTB in Console → Connectors)
- **Amazon EventBridge** → Descope Audit Webhook Connector (custom HTTP sink)

Note: Datadog is NOT a direct Okta Log Stream destination (it integrates indirectly via
EventBridge or the System Log API). In Descope, Datadog integration uses a custom Audit Webhook.

Source: [help.okta.com/oie topics/Reports/log-streaming](https://help.okta.com/oie/en-us/Content/Topics/Reports/log-streaming/about-log-streams.htm)

Set up audit connectors before cutover to avoid gaps in event logging.

---

### Service Apps → Access Keys

Okta Service Apps (API Services) use the Client Credentials flow — exchange client ID + secret
for an access token. Descope's equivalent is [Access Keys](https://docs.descope.com/management/m2m-access-keys).

| Okta | Descope |
|---|---|
| Service App (client ID + secret) | Access Key |
| `POST /token` with `client_credentials` grant | `descopeClient.auth.exchangeAccessKey(accessKey)` |
| Resulting access token | Short-lived JWT (same validation as user tokens) |
| Scopes on the token | Scopes configured on the Inbound App |

Create Access Keys in Console → Access Keys. They support expiration, permitted IPs, and
tenant/role scoping.

---

### Groups / RBAC → Descope Roles

| Okta | Descope |
|---|---|
| Group | Role (flat or tenant-scoped) |
| Group membership | User → Role assignment |
| Group-based access control | RBAC via `roles` claim in JWT |
| `groups` claim in token | `roles` array in Descope JWT |

Roles must be created in the Console before code that assigns them will work:
Console → Authorization → RBAC → + Role.

If migrating groups to tenant-scoped roles (for B2B apps), use:
`management.role.create(name, description, permissionNames, tenantId)`

---

### User migration

See [docs.descope.com/migrate/okta-cis](https://docs.descope.com/migrate/okta-cis) for the authoritative guide. Three paths — choose based on user experience requirements and operational constraints.

#### Path 1: Full migration (bulk export → import)

Use the Okta Users API to export all users, then import into Descope before cutover. Use the Descope Management API directly.

```bash
# Export users — paginated, max 200 per page
curl -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/users?limit=200"
# For subsequent pages: ?after=${lastUserId} from the Link header
```

**Attribute mapping:**

| Okta field | Descope field | Notes |
|---|---|---|
| `profile.login` or `profile.email` | `loginIds` | Required; must be unique per user |
| `profile.email` | `email` | |
| `profile.firstName` | `givenName` | |
| `profile.lastName` | `familyName` | |
| Custom profile fields | `customAttributes` | Pre-define schema in Console first |

Import via Management SDK: `management.user.createBatch([...users])`

Set `freshlyMigrated: true` as a custom attribute on every imported user. Use this in Flow Conditions to route newly-migrated users through a first-login experience (password reset, re-enrollment for TOTP/passkeys), then flip to `false` once done.

**Alternative — own data store:** If Okta sits in front of your own database (On-prem SCIM Server Agent or Okta Access Gateway), you own the user data. Connect that same DB to Descope via a Generic HTTP Connector in your Flow and sever Okta from the path — no export/import needed.

#### Path 2: JIT migration (password verification)

No bulk export. When a user signs in, verify their password with the Okta Authentication API, then create or link the user in Descope and issue a Descope session. The user re-enters credentials once; subsequent sign-ins go through Descope only.

```bash
curl -X POST \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -d '{
    "username": "user@example.com",
    "password": "their-password"
  }' \
  "https://${OKTA_DOMAIN}/api/v1/authn"
```

On success: call `management.user.create(...)` or `management.user.update(...)` in Descope, then issue a Descope session. The Okta session is retired.

**JIT is flexible** — you control the Flow. You don't have to ask for a password. You can look up the user by email, verify ownership via magic link or OTP sent to the email on file, and provision them in Descope without ever asking for a password. Design the JIT Flow to match your UX goals.

#### Path 3: Session migration (JIT without re-login)

The highest-quality zero-disruption path. Deploy a new app version with the Descope SDK and session migration enabled. When a user opens the updated app with an existing Okta session token, Descope validates it, provisions the user in Descope just-in-time, and issues a Descope token. No re-login, no interruption.

See [docs.descope.com/migrate/session-migration](https://docs.descope.com/migrate/session-migration) for SDK integration (React, Next.js, Web JS, Kotlin, Swift).

#### Password constraint

Okta does not export password hashes. For full and JIT migrations, plan one of:
- Password reset campaign (email users before cutover)
- "Set new password on first login" Flow step, conditioned on `freshlyMigrated: true`
- Full switch to passwordless (magic link, passkeys, TOTP)

#### Dual-token validation during rollout

During any gradual rollout, the backend receives both Okta JWTs and Descope tokens. Validate both — inspect the `iss` claim to route to the correct validator:
- Okta: `iss` matches `https://YOUR_DOMAIN.okta.com/oauth2/...`
- Descope: `iss` matches `https://api.descope.com/YOUR_PROJECT_ID`

Remove the Okta validator once all sessions have expired or been migrated. See [docs.descope.com/migrate/session-migration#step-1-dual-token-validation-in-your-backend](https://docs.descope.com/migrate/session-migration#step-1-dual-token-validation-in-your-backend).

---

**— Common Gotchas —**

### JWT claims differ

Descope session JWTs contain `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions`, and `dct`
by default. They do **not** contain `email`, `name`, or `picture` (these must be added via a
JWT Template). Okta ID tokens include `email` and `name` by default.

`dct` (Descope Current Tenant) is the active tenant ID — the direct equivalent of Okta's
per-org context. Use `token.tenants` when you need per-tenant roles/permissions (it is a
keyed object: `{ [tenantId]: { roles, permissions } }`).

**scp vs. scope** — see [scp vs. scope claim](#scp-vs-scope-claim) above.

**Action required:** Configure a JWT Template in the Console to add `email`, `name`, and
any profile fields the app reads from the token.

---

### Audience validation is opt-in

Descope session tokens have no `aud` claim by default. Apps using `OKTA_AUDIENCE` for API
access control must:
1. Configure a custom `aud` claim in JWT Templates
2. Pass `audience` to `validateSession()` on the backend

---

### One session token, not two

Okta issues separate ID tokens and access tokens. Descope has one token: the session JWT
(`DS` cookie). Forward it as `Authorization: Bearer <DS>` to API servers.

---

### Logout is two steps

1. Call `descopeClient.logout(refreshToken)` to invalidate server-side
2. Clear `DS` and `DSR` cookies

Skipping either step leaves a broken state.

---

### Dual-token validation during phased rollout

During any gradual cutover, the backend receives both Okta JWTs and Descope tokens from different users. If the backend only accepts one token type, migrated users will break on un-updated services.

Inspect the `iss` (issuer) claim to route to the correct validator:
- Okta tokens: `iss` contains `okta.com`
- Descope tokens: `iss` is `https://api.descope.com/YOUR_PROJECT_ID`

Once all users have been migrated and all Okta sessions have expired, remove the Okta validation path.

Reference: [docs.descope.com/migrate/session-migration#step-1-dual-token-validation-in-your-backend](https://docs.descope.com/migrate/session-migration#step-1-dual-token-validation-in-your-backend)

---

### Env var reduction

Okta: `OKTA_CLIENT_ID`, `OKTA_CLIENT_SECRET`, `OKTA_ISSUER` (or `OKTA_DOMAIN`), `OKTA_AUDIENCE`,
`OKTA_REDIRECT_URI` (5+ variables).
Descope: `DESCOPE_PROJECT_ID` only (+ `DESCOPE_MANAGEMENT_KEY` for management ops).

---

## Framework Sections

### Okta Sign-In Widget (@okta/okta-signin-widget)

The Okta Sign-In Widget is a standalone, framework-agnostic JS component. It handles the full
sign-in UI without requiring a framework SDK. Many Okta CIS low-code users embed it directly.

**Migration:** The Descope Flow component is the direct replacement. The migration is almost
entirely Console-side — configure the Flow in the Console, then swap the widget initialization
for the Descope component.

**Vanilla JS / no framework:**
```html
<!-- Remove -->
<script src="https://global.oktacdn.com/okta-signin-widget/.../okta-sign-in.min.js"></script>
<link rel="stylesheet" href="https://global.oktacdn.com/okta-signin-widget/.../okta-sign-in.min.css">
<div id="okta-login-container"></div>
<script>
  const widget = new OktaSignIn({ issuer: '...', clientId: '...', redirectUri: '...' });
  widget.showSignInToElement(document.getElementById('okta-login-container'), { el: '#okta-login-container' });
</script>

<!-- Add -->
<script src="https://unpkg.com/@descope/web-component/dist/index.js"></script>
<descope-wc flow-id="sign-up-or-in" project-id="YOUR_PROJECT_ID"></descope-wc>
<script>
  document.querySelector('descope-wc').addEventListener('success', (e) => {
    const { sessionToken } = e.detail;
    // store token, redirect user
  });
</script>
```

**React:** Use `<Descope flowId="sign-up-or-in" />` from `@descope/react-sdk` — see React section below.

**Key difference:** The Okta widget handles its own redirect flow; the Descope component is fully
embedded with no redirect. The `success` event fires with the session token in-page.

---

### React + @okta/okta-react

`@okta/okta-react` wraps `okta-auth-js` and provides `OktaAuth`, `Security` provider,
`useOktaAuth()`, and the `LoginCallback` component.

**Changes:**
- Remove `@okta/okta-react` and `okta-auth-js`; add `@descope/react-sdk`
- Replace `<Security oktaAuth={oktaAuth}>` with `<AuthProvider projectId={...}>`
- Replace `useOktaAuth()` with `useSession()` + `useUser()` from `@descope/react-sdk`
- Replace `<LoginCallback>` with `<Descope flowId="sign-up-or-in" onSuccess={...} />`
- Remove redirect to Okta; add `/login` page with `<Descope>` component
- Logout: call `sdk.logout()` via `useDescope()` hook (not `oktaAuth.signOut()`)

**Key differences:**
- `useOktaAuth().authState.isAuthenticated` → `useSession().isAuthenticated`
- `useOktaAuth().authState.accessToken` → `useSession().sessionToken`
- `oktaAuth.getUser()` → `useUser().user` (populated from the session JWT + JWT Template)
- No `<SecureRoute>` — check `isAuthenticated` in the component and redirect manually

---

### Angular + @okta/okta-angular

`@okta/okta-angular` provides `OktaAuthGuard`, `OktaCallbackComponent`, `OktaAuthModule`,
and the `OKTA_AUTH` injection token.

**Changes:**
- Remove `@okta/okta-angular` and `okta-auth-js`; add `@descope/angular-sdk`
- Replace `OktaAuthModule.forRoot({...})` with `DescopeAuthModule.forRoot({projectId: ...})`
- Replace `OktaAuthGuard` with a custom guard using `DescopeAuthGuard` or `AuthGuard` from
  the Descope Angular SDK
- Replace `OktaCallbackComponent` route — Descope has no redirect callback
- Add `/login` route with `<descope-wc flowId="sign-up-or-in">` or Descope Angular component
- Inject `DescopeAuthService` in place of `OktaAuthService`

**Key differences:**
- `OktaAuthStateService.authState$` → `DescopeAuthService.session$`
- Route guards: `canActivate: [OktaAuthGuard]` → `canActivate: [AuthGuard]`
- No callback route needed (`/authorization-code/callback` → delete)

---

### Vue + @okta/okta-vue

`@okta/okta-vue` extends `okta-auth-js` with Vue Router integration and a `navigationGuard`.

**Changes:**
- Remove `@okta/okta-vue` and `okta-auth-js`; add `@descope/vue-sdk`
- Replace `createOktaAuth({...})` + `app.use(OktaVue, {oktaAuth})` with
  `app.use(descope, { projectId: ... })`
- Replace `navigationGuard` with Descope's session check in router `beforeEach`
- Add `/login` component with `<Descope flowId="sign-up-or-in" />`

**Key differences:**
- `$auth.isAuthenticated()` → `useSession().isAuthenticated`
- No callback route needed

---

### Node.js / Express + @okta/oidc-middleware

`@okta/oidc-middleware` auto-mounts `/login`, `/logout`, and `/authorization-code/callback`
and attaches `req.userContext` to every request.

**Changes:**
- Remove `@okta/oidc-middleware`; add `@descope/node-sdk` + `cookie-parser`
- Remove the auto-mounted routes; write a `/login` route that renders the Descope web component
- Replace `app.use(ExpressOIDC(...))` with custom middleware:

```javascript
const cookieParser = require('cookie-parser')
const Descope = require('@descope/node-sdk')

const descopeClient = Descope({ projectId: process.env.DESCOPE_PROJECT_ID })
app.use(cookieParser())

app.use(async (req, res, next) => {
  const sessionToken = req.cookies['DS']
  if (!sessionToken) { req.user = null; return next() }
  try {
    const authInfo = await descopeClient.validateSession(sessionToken)
    req.user = authInfo.token
  } catch {
    req.user = null
  }
  next()
})

function requireAuth(req, res, next) {
  if (!req.user) return res.redirect('/login')
  next()
}
```

- Logout: `descopeClient.logout(req.cookies['DSR'])` + clear `DS` and `DSR` cookies

**Key differences:**
- `req.userContext.userinfo` → `req.user` (decoded JWT claims)
- `req.userContext.tokens.accessToken` → `req.cookies['DS']` (the session JWT)
- `oidc.ensureAuthenticated()` → `requireAuth` function above

---

### Backend JWT validation (okta-jwt-verifier)

Okta provides `@okta/jwt-verifier` (Node.js) for validating access tokens on API servers.
Descope's equivalent is the session validation SDK or a JWKS URL update.

**Option A — Descope SDK (recommended for code-level replacement):**

```javascript
// Remove: const OktaJwtVerifier = require('@okta/jwt-verifier')
// Add:
const Descope = require('@descope/node-sdk')
const descopeClient = Descope({ projectId: process.env.DESCOPE_PROJECT_ID })

async function validateToken(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1]
  if (!token) return res.status(401).json({ error: 'No token' })
  try {
    const authInfo = await descopeClient.validateSession(token)
    req.auth = authInfo.token
    next()
  } catch {
    return res.status(401).json({ error: 'Invalid token' })
  }
}
```

**Option B — API gateway / JWT authorizer (no code change required):**
Update the JWKS URL and Issuer in your gateway config:
- JWKS: `https://api.descope.com/YOUR_PROJECT_ID/.well-known/jwks.json`
- Issuer: `https://api.descope.com/YOUR_PROJECT_ID`

**scp → scope claim:** Regardless of approach, update any scope-checking logic from
`token.scp` to `token.scope`.

---

### Next.js

Key points for Next.js:

- `@descope/nextjs-sdk` for both client and server components
- `session()` from `@descope/nextjs-sdk/server` — server components and API routes only
- `useSession()` + `useUser()` from `@descope/nextjs-sdk/client` — React client components
- **Next.js 15**: `cookies()` and `headers()` from `next/headers` are async. Write `await cookies()` and mark the containing function `async`. This cascades to all callers.
- `getServerSession` does not exist — the export is `session`. Verify against local type declarations before writing any import.
- No `/authorization-code/callback` route — delete it. Descope handles auth client-side.

**Session return type (`AuthenticationInfo`):**
```ts
interface AuthenticationInfo {
  jwt: string    // raw session JWT
  token: Token   // decoded claims: { sub?, exp?, iss?, [claim: string]: unknown }
  cookies?: string[]
}
```

No `isAuthenticated` or `user` wrapper. Write an adapter:
```ts
import { session as sdkSession } from "@descope/nextjs-sdk/server"

export async function getDescopeSession() {
  const authInfo = await sdkSession()
  if (!authInfo) return null
  return { isAuthenticated: true as const, jwt: authInfo.jwt, token: authInfo.token }
}
```

---

### Custom / open-source OIDC clients

Apps using `openid-client`, `passport-openidconnect`, `node-openid-client`, or similar
libraries only need endpoint reconfiguration:

| Config key | Okta value | Descope value |
|---|---|---|
| `issuer` | `https://YOUR_DOMAIN.okta.com/oauth2/default` | `https://api.descope.com/YOUR_PROJECT_ID` |
| `authorization_endpoint` | `…/oauth2/v1/authorize` | `https://api.descope.com/oauth2/v1/authorize` |
| `token_endpoint` | `…/oauth2/v1/token` | `https://api.descope.com/oauth2/v1/token` |
| `userinfo_endpoint` | `…/oauth2/v1/userinfo` | `https://api.descope.com/oauth2/v1/userinfo` |
| `jwks_uri` | `…/oauth2/v1/keys` | `https://api.descope.com/YOUR_PROJECT_ID/.well-known/jwks.json` |
| `end_session_endpoint` | `…/oauth2/v1/logout` | `https://api.descope.com/oauth2/v1/logout` |

After updating endpoints: verify the `scp` → `scope` claim mapping and any other claim
shape differences in your application code.

---

## Testing Checklist

After completing the migration, verify all of the following:

- [ ] Stale import sweep returns zero Okta references (`@okta`, `okta-auth-js`, `okta-jwt-verifier`, `OKTA_`)
- [ ] Compilation passes with zero errors
- [ ] Server starts without crash
- [ ] Unauthenticated requests to protected routes return 302 (redirect to login) or 401
- [ ] Login flow completes; user profile data appears in the UI (confirms JWT Template is working)
- [ ] `scope` claim (not `scp`) is present in the Descope access token if scopes are in use
- [ ] Logout invalidates the session (both `DS` and `DSR` cookies cleared; subsequent requests return 401)
- [ ] JWT claims contain expected fields (`email`, `name`, custom attributes via JWT Template)
- [ ] M2M Access Key exchange works and produces a valid JWT
- [ ] Tenant SSO login completes correctly (if applicable)
- [ ] API gateway JWT authorizer accepts Descope tokens (JWKS + Issuer updated)
