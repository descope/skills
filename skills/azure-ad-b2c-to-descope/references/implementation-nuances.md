# Descope Migration: Implementation Notes (Azure AD B2C)

## Contents

**General Insights — Architecture**
- [B2C hosts every login; each policy is its own authority](#b2c-hosts-every-login-each-policy-is-its-own-authority)
- [Replace MSAL, don't reconfigure it](#replace-msal-dont-reconfigure-it)
- [Hosted login by default](#hosted-login-by-default)
- [Which Descope app: Inbound App, Federated App, or plain SDK](#which-descope-app-inbound-app-federated-app-or-plain-sdk)
- [Descope OIDC endpoints](#descope-oidc-endpoints)
- [Token claim mapping](#token-claim-mapping)

**General Insights — Feature Mapping**
- [User flows and custom policies → Flows](#user-flows-and-custom-policies--flows)
- [API connectors and REST technical profiles → HTTP Connectors](#api-connectors-and-rest-technical-profiles--http-connectors)
- [Identity providers](#identity-providers)
- [MFA and Conditional Access](#mfa-and-conditional-access)
- [Custom attributes](#custom-attributes)
- [Roles and groups](#roles-and-groups)
- [Page layouts → Flow styles](#page-layouts--flow-styles)
- [Passkeys](#passkeys)

**User Migration**
- [Exporting users from B2C](#exporting-users-from-b2c)
- [Password strategy](#password-strategy)
- [Social users](#social-users)
- [Enterprise SSO users](#enterprise-sso-users)

**Enterprise SSO Migration**
- [Per-connection inventory and cutover rules](#per-connection-inventory-and-cutover-rules)
- [Secrets and certificates](#secrets-and-certificates)
- [MFA for enterprise SSO users](#mfa-for-enterprise-sso-users)

**Framework Sections**
- [React + @azure/msal-react](#react--azuremsal-react)
- [Angular + @azure/msal-angular](#angular--azuremsal-angular)
- [Next.js](#nextjs)
- [Vue + @azure/msal-browser](#vue--azuremsal-browser)
- [Plain JavaScript + @azure/msal-browser](#plain-javascript--azuremsal-browser)
- [Embedded sign-in (iframe) → embedded Flow](#embedded-sign-in-iframe--embedded-flow)
- [Server-side web apps](#server-side-web-apps)
- [Native / mobile](#native--mobile)

- [Testing checklist](#testing-checklist)

> **See also:** `flows-and-widgets.md` (lingo, Flows, Widgets, SSO Setup Suite),
> `backend-sdks.md` (.NET, Node.js, Python, Java API validation), and
> `b2c-detection-patterns.md` (code search, Graph discovery, evidence template).

---

## General Insights

### B2C hosts every login; each policy is its own authority

B2C has no embeddable login SDK. Apps send users to a B2C-hosted page on
`https://<tenant>.b2clogin.com` (or a custom domain fronted by Azure Front Door). Each user flow
(`B2C_1_…`) or custom policy (`B2C_1A_…`) is a separate authority with its own metadata and keys:

```
https://contoso.b2clogin.com/contoso.onmicrosoft.com/B2C_1_susi/v2.0/.well-known/openid-configuration
https://contoso.b2clogin.com/contoso.onmicrosoft.com/B2C_1_susi/discovery/v2.0/keys
```

Apps therefore often hold several authorities (sign-up/sign-in, password reset, profile edit) and
policy-aware code. In Descope, these journeys become Flows behind one project; the per-policy
plumbing is deleted.

Four ways apps reach B2C:
1. **MSAL redirect/popup** (most SPAs) — `PublicClientApplication`, `knownAuthorities: ["<tenant>.b2clogin.com"]`
2. **Branded hosted page** — the same redirect with custom HTML/CSS/JS page layouts
3. **Embedded sign-in** — public preview, custom policies only, `<JourneyFraming Enabled="true" Sources="…"/>`; local accounts only; third-party cookie issues; MSAL not supported inside the iframe
4. **ROPC** — app collects the password; local accounts only; no MFA; no interactive steps

### Replace MSAL, don't reconfigure it

`@azure/msal-browser` and `@azure/msal-node` have an `OIDC` protocol mode for non-Microsoft
authorities, but Microsoft's own code documents it as *"Support is limited for this mode"*, and
B2C apps wrap MSAL in B2C-specific logic (policy-name account filtering, `AADB2C90118` handling,
per-policy authorities) that breaks regardless. `Microsoft.Identity.Web` has no OIDC mode.
Always replace MSAL with the Descope SDK or a standard OIDC library.

### Hosted login by default

B2C users already leave the app for `b2clogin.com`, so the Descope-hosted login page
([Auth Hosting](https://docs.descope.com/identity-federation/auth-hosting)) is the smallest UX
change. Use an embedded Flow only for B2C iframe users or when the customer asks.

| Stack | Hosted login |
|---|---|
| React (`@descope/react-sdk`) | `AuthProvider` `oidcConfig` + `sdk.oidc.loginWithRedirect()`; redirect return handled automatically |
| Angular (`@descope/angular-sdk`) | `DescopeAuthModule.forRoot({ projectId, oidcConfig })` |
| Next.js (`@descope/nextjs-sdk`) | Its `AuthProvider` passes `oidcConfig` through to the React SDK; tokens go to cookies by default (not in the README — test it) |
| Vue (`@descope/vue-sdk`) | Plugin passes `oidcConfig` to the web SDK at runtime but its types omit it (cast), and it does **not** finish login automatically — call `sdk.oidc.finishLoginIfNeed()` on the redirect page |
| Plain JS (`@descope/web-js-sdk`) | `createSdk({ projectId, oidcConfig })` + `sdk.oidc.loginWithRedirect()` |
| Server-side web apps | Standard OIDC library pointed at the Descope app |

With `oidcConfig` set, `refresh()` and `logout()` switch to the OIDC client (per the web-js SDK
source, shared by all of these SDKs) — confirm with the Docs MCP.

### Which Descope app: Inbound App, Federated App, or plain SDK

B2C forces even first-party SPAs to register their API ("Expose an API"), define scopes, and
request them with MSAL. Customers are used to scoped access tokens, so keep that model:

| B2C setup | Descope |
|---|---|
| API app registration with "Expose an API" scopes | **Resource** — same scope names (e.g. `tasks.read`) |
| Frontend app registration requesting those scopes | **Inbound App** — the frontend logs in through it and receives access tokens with `scope` |
| Partner / agent / CLI callers | One **Inbound App** each (consent, scoped tokens) |
| Client-credentials (daemon) app registration | **Inbound App** with client credentials |
| App with no API scopes (login only) | **Federated App** (standard OIDC library) or plain Descope SDK session |

For a frontend with **no API scopes**, hosted login can use the project's OIDC app instead:
`oidcConfig={true}` or `oidcConfig={{ applicationId }}` (a Federated App's ID; omitted → the
default OIDC application), and the backend validates the session token.

Configure hosted login with the Inbound App's `issuer` and `clientId` (both on the Inbound App
settings page; do not construct the issuer). When a custom issuer is set, the React SDK's
default `scope` is `openid` — set `scope` explicitly to include the Resource scopes. Verify the
exact way to request Resource scopes (scope names vs. resource indicator) with the Docs MCP.

### Descope OIDC endpoints

**Federated App / project-level OIDC** (client ID = Project ID, client secret = Access Key):

| Endpoint | Value |
|---|---|
| Issuer / discovery | `https://api.descope.com/<ProjectID>` + `/.well-known/openid-configuration` |
| Authorization | `https://api.descope.com/oauth2/v1/authorize` |
| Token | `https://api.descope.com/oauth2/v1/token` |
| JWKS | `https://api.descope.com/<ProjectID>/.well-known/jwks.json` |
| Logout | `https://api.descope.com/oauth2/v1/logout` |

**Inbound App** (own client ID and secret):

| Endpoint | Value |
|---|---|
| Issuer | `https://api.descope.com/v1/apps/<ProjectID>` (custom client IDs: `/v1/apps/customized/<ProjectID>`) — copy from the Inbound App settings page |
| Authorization | `/oauth2/v1/apps/authorize` |
| Token | `/oauth2/v1/apps/token` |
| JWKS | `jwks_uri` from the discovery document (typically `https://api.descope.com/<ProjectID>/.well-known/jwks.json`) |

Use the custom domain host instead of `api.descope.com` when one is configured.

### Token claim mapping

| B2C claim | Meaning | Descope |
|---|---|---|
| `sub` / `oid` | B2C object ID | New user ID; keep the old value as custom attribute `b2cObjectId` + JWT Template claim |
| `tfp` / `acr` | Policy name | None — delete code that reads it |
| `iss` | `https://<tenant>.b2clogin.com/<tenant-guid>/v2.0/` (or `/tfp/<guid>/<policy>/v2.0/`) | Inbound App: `https://api.descope.com/v1/apps/<ProjectID>`; session: `https://api.descope.com/<ProjectID>` |
| `aud` | App registration (client) ID | Inbound App access token: the Resource; session token: project ID |
| `scp` | Space-separated short scope names | `scope` — space-separated string (Inbound App tokens) |
| `emails` | Array of emails (local accounts) | `email` via JWT Template |
| `name`, `given_name`, `family_name` | Profile | Add via JWT Template |
| `idp` | Federated provider (e.g. `google.com`, customer IdP issuer) | Tenant (`dct` / `tenants`) and auth method (`amr`) |
| `extension_<name>` | Custom attribute (custom-policy name; Graph name is `extension_<appId>_<name>`) | Custom attribute + JWT Template |
| `azp` | Authorized party (client ID) | `azp` on Inbound App tokens — check it if only some clients may call the API |

Descope session tokens contain `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions`, `dct` by
default — not `email` or `name`. A user JWT Template applies to both session tokens and Inbound
App access tokens.

---

### User flows and custom policies → Flows

| B2C | Descope |
|---|---|
| Sign-up/sign-in user flow | `sign-up-or-in` Flow |
| Password reset user flow (or `AADB2C90118` redirect) | Password reset branch/Flow (template available) |
| Profile edit user flow | User Profile Widget or a profile Flow |
| Custom policy user journey | One Flow; orchestration steps → Flow steps; sub-journeys → subflows |
| Claims transformations | Scriptlets (logic) or JWT Template (token shaping) |
| Technical profile with `IncludeInSso`/session management | Project session settings |
| Token lifetimes (default 60 min access, 14-day refresh, 24 h for SPAs) | Project Settings → Session Management |
| Localization | Flow screen localization |

Read the custom policy XML (relying party file first, then the chain: Base → Localization →
Extensions) to list user journeys, orchestration steps, `ClaimsExchange` technical profiles, and
`OutputClaims`. Each relying party policy usually maps to one Flow.

### API connectors and REST technical profiles → HTTP Connectors

B2C API connectors run at three points; place the Descope HTTP Connector at the same point:

| B2C hook | Descope Flow placement |
|---|---|
| After federating with an IdP during sign-up | After the social/SSO step, before user creation |
| Before creating the user | Before the sign-up action |
| Before sending the token (preview) | Before the End step; write results via custom claims |

B2C sends user claims as JSON; a 409 response shows a validation message. In Descope, the
connector response is stored in `connectors.<contextKey>` for Conditions, custom claims, and
screens. B2C timeouts are 5 s (user flows) / 10 s (custom policies).

### Identity providers

| B2C | Descope |
|---|---|
| Google, Facebook, Apple, Microsoft account | Social login (register new client ID/secret; B2C returns `****` for stored secrets) |
| Single customer Entra ID (OIDC) | Tenant with OIDC SSO + email domains |
| SAML IdP (custom policies only) | Tenant with SAML SSO + email domains |
| Multi-tenant Entra (`common` + `ValidTokenIssuerPrefixes` allowlist) | "Sign in with Microsoft" social login + Flow condition for the allowlist; per-customer tenants only if they need own roles/settings |
| `domain_hint` / home realm discovery | Tenant email domains; `tenant` parameter on the hosted login URL skips the email screen |
| Another B2C tenant as IdP | OIDC provider or tenant SSO |

### MFA and Conditional Access

- B2C MFA (SMS/voice, email OTP, TOTP authenticator app) → MFA steps in the Flow. TOTP seeds can't migrate.
- Conditional Access in B2C only offers **require MFA** or **block** (B2C Premium P2 was discontinued on March 15, 2026, per Microsoft's B2C FAQ, and Identity Protection is no longer available in B2C) → Flow conditions plus risk/fraud connectors.
- "MFA only for some users/apps" → Flow condition on roles, tenant, or `ssoAppId`.

### Custom attributes

Graph name: `extension_<b2c-extensions-app client ID without hyphens>_<name>` (the
`b2c-extensions-app` registration). Custom policies use `extension_<name>`. Define each as a
Descope custom attribute before import; add the ones the app reads to the JWT Template.

### Roles and groups

B2C does not support roles for consumer accounts and cannot emit groups from user flows. Find how
the app built roles:

| Pattern | Detect | Descope |
|---|---|---|
| Custom attribute (`extension_Role`) | Claim checks on `extension_*` | Roles (import values), or keep as custom attribute |
| App database + API connector "before sending token" | REST call returning roles | Roles in Descope, or keep the DB and call it from a Flow HTTP Connector |
| Custom policy calling Graph `memberOf` | `RestfulProvider` to `graph.microsoft.com/.../memberOf`, `groups` claim | Roles, or tenants if groups represent customer organizations |
| Roles only in app database | No role claims | Nothing to migrate |

### Page layouts → Flow styles

B2C page layouts are hosted HTML templates (`ContentDefinition` `LoadUri` in custom policies, or
"custom page content" in user flows). Rebuild branding in Flow styles and screens; do not host
the old templates.

### Passkeys

B2C has no native passkeys and its Conditional Access cannot require them. Customers who have
passkeys used Microsoft's community FIDO2 sample or a partner (Nok Nok, Authsignal, Transmit).
Those credentials are bound to the old domain and cannot migrate — add a passkey enrollment step
after first login (`freshlyMigrated` condition). For everyone else, passkeys are a new capability.

---

## User Migration

See [docs.descope.com/migrate/azure-ad-b2c](https://docs.descope.com/migrate/azure-ad-b2c).

### Exporting users from B2C

App registration with `User.Read.All` (application), client credentials token from
`https://login.microsoftonline.com/<b2c-tenant-id>/oauth2/v2.0/token` with
`scope=https://graph.microsoft.com/.default`, then:

```http
GET https://graph.microsoft.com/v1.0/users?$select=id,identities,displayName,givenName,surname,mail,otherMails,mobilePhone,createdDateTime,extension_<appId>_<attr>&$top=999
```

Follow `@odata.nextLink`; on `429`, honor `Retry-After` with backoff. Extension attributes must
be listed explicitly in `$select`.

`identities[]` per user (`signInType`, `issuer`, `issuerAssignedId`):
- `emailAddress` / `userName` → local account; `issuerAssignedId` is the sign-in name
- `federated` → social or enterprise; `issuer` is the provider (e.g. `google.com`, the customer IdP), `issuerAssignedId` is the provider's user ID

**Field mapping:**

| B2C (Graph) | Descope |
|---|---|
| `identities[emailAddress or userName].issuerAssignedId` | `loginId` |
| `id` | `customAttributes.b2cObjectId` |
| `displayName` / `givenName` / `surname` | `name` / `givenName` / `familyName` |
| `mail` or `otherMails[0]` or the `emailAddress` identity | `email` (+ `verifiedEmail: true` for email sign-in accounts, which B2C verifies at sign-up — Graph has no per-user verification flag; confirm the policy verified emails) |
| `mobilePhone`, or the SMS MFA number from `GET /users/{id}/authentication/phoneMethods` (`UserAuthenticationMethod.Read.All`) | `phone` |
| `extension_<appId>_<name>` | `customAttributes.<name>` |
| — | `customAttributes.freshlyMigrated: true` |

Import with the batch create users Management API (`POST /v1/mgmt/user/create/batch`) or the
SDK equivalent (verify the method name via the Docs MCP).

### Password strategy

B2C does not export password hashes.

| Option | How | Trade-off |
|---|---|---|
| Full import without passwords | First-login password reset step, or passwordless (OTP, magic link, passkeys) | Fastest B2C shutdown; every password user acts once |
| JIT via ROPC | Flow collects email + password → HTTP Connector to the B2C ROPC endpoint → on success create the user and set the password in Descope | Keeps passwords; B2C stays up until active users have signed in; local accounts only; no MFA in that call |
| JIT with B2C as an OIDC provider | B2C policy configured as a custom OAuth provider in Descope; users sign in through B2C once and are created from the ID token | No passwords kept; B2C stays up |
| Session migration | Existing B2C sessions exchanged for Descope sessions ([docs](https://docs.descope.com/migrate/session-migration)) | Requires all users imported first |

**ROPC request** (requires a B2C ROPC user flow or custom policy):

```http
POST https://<tenant>.b2clogin.com/<tenant>.onmicrosoft.com/<B2C_1_ROPC_policy>/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=...&grant_type=password&scope=openid <client-id> offline_access&client_id=<client-id>&response_type=token id_token
```

### Social users

Import with the email as `loginId` and `verifiedEmail: true`. On first social login Descope links
to the existing user when the provider's email matches the login ID, the provider's email is
verified, and the provider trusts provided emails (Google's default). If someone changed the
provider's "trust provided emails" setting or claim mapping, users get new accounts instead.

### Enterprise SSO users

Descope looks up an SSO login by exact login ID, in this order:
1. **Direct:** SAML `<NameID>-<tenantID>`; OIDC `<external-ID claim>-<tenantID>` (claim is normally `sub`)
2. **Fallback** (only if "Convert existing users to SSO" is on — the default): SAML plain NameID; OIDC the IdP email, only if the connection trusts provided emails
3. **Otherwise:** a new SSO user is created — a duplicate of the imported one

Recipe:
1. Create the tenant and its SSO connection **before** importing that customer's users.
2. Import each enterprise user into **exactly one** tenant (multi-tenant users need the "Allow converting users that belong to multiple tenants" setting — flag them for a manual decision; it carries cross-tenant takeover risk).
3. Set the login ID to what the direct lookup uses:
   - **SAML:** `<NameID>-<tenantID>`. B2C's `issuerAssignedId` for SAML users is usually the NameID (the starter pack maps `assertionSubjectName` → `issuerUserId`) — confirm in the policy XML.
   - **OIDC:** `<sub>-<tenantID>`. Note B2C's Entra examples map the IdP's `oid` (not `sub`) into `issuerAssignedId`. Either configure the tenant connection's external-ID claim to match what B2C stored (verify via Docs MCP), or use the email fallback: import with email as login ID and enable trusted emails on the connection.
4. Add the email as an additional login ID when it differs.
5. Check that each customer IdP actually sends the stored email (Entra often sends a UPN).

---

## Enterprise SSO Migration

### Per-connection inventory and cutover rules

Build one row per customer connection (template in `b2c-detection-patterns.md`). Descope's
[SSO migration](https://docs.descope.com/migrate/sso) keeps old ACS URLs working by pointing the
old login hostname at a Cloudflare Worker that forwards to Descope (`spEntityId` / `spACSUrl`
overrides on the tenant). That requires a hostname the customer controls:

| Condition | Result |
|---|---|
| URLs on `<tenant>.b2clogin.com` | Customer IdP admin updates ACS/redirect URLs — no DNS redirect possible |
| SAML on a custom domain, no signed-request/encrypted-assertion dependency | Can move without IdP changes (DNS redirect) |
| SAML that requires signed requests or encrypts assertions to B2C's certificate | Upload the original private key (PFX) to the Descope tenant if the company kept it; otherwise the admin trusts Descope's certificate |
| OIDC connection | Redirect can be kept on a custom domain, but the admin issues a new client secret unless the original was stored outside B2C |

Some connections may have been created before a custom domain was added — check the URL each
customer IdP is actually configured with. Send affected admins a notice before cutover: what
changes (URL, certificate, secret), the values, and the date. Descope's SSO migration docs list
seamless SSO migration for Growth and Enterprise plans — confirm availability for the customer.

### Secrets and certificates

- Graph `openIdConnectIdentityProvider` / `socialIdentityProvider` `clientSecret`: *"write-only. A read operation returns `****`."*
- Graph `trustFrameworkKey`: `k`, `d`, `p`, `q`, `dp`, `dq`, `qi` — *"The field isn't readable."*
- Descope tenants accept an uploaded custom private key for SAML signing/decryption.

### MFA for enterprise SSO users

Reproduce what B2C does today:

| B2C | Descope Flow |
|---|---|
| Always adds its own MFA after company login | MFA step after the SSO step |
| Trusts the company IdP | No MFA step for SSO users |
| Skips MFA if the IdP's `amr` contains `mfa` (custom policy) | Condition on `idpOIDCClaims.amr` (OIDC) or an `idpSAMLAttributes.<name>` entry (SAML) |

Caveats: retaining OIDC IdP claims for tenant SSO may depend on a backend setting — confirm with
Descope that it is enabled for the project; SAML `AuthnContextClassRef` may not appear in `idpSAMLAttributes` — confirm the IdP
sends MFA as an assertion attribute.

---

## Framework Sections

### React + @azure/msal-react

**Remove:** `@azure/msal-browser`, `@azure/msal-react`, `msalConfig` / `b2cPolicies` /
`loginRequest` / `protectedResources` config files, `MsalProvider`, `PublicClientApplication`,
`handleRedirectPromise`, MSAL event callbacks (`LOGIN_SUCCESS`, `AADB2C90118` handling).

**Add:** `@descope/react-sdk`.

```jsx
import { AuthProvider } from '@descope/react-sdk';

<AuthProvider
  projectId={import.meta.env.VITE_DESCOPE_PROJECT_ID}
  oidcConfig={{
    issuer: import.meta.env.VITE_DESCOPE_INBOUND_ISSUER,   // from the Inbound App settings page
    clientId: import.meta.env.VITE_DESCOPE_INBOUND_CLIENT_ID,
    redirectUri: window.location.origin,
    scope: 'openid profile email tasks.read',              // include Resource scopes
  }}
>
  <App />
</AuthProvider>
```

| MSAL | Descope |
|---|---|
| `instance.loginRedirect(loginRequest)` | `useDescope().oidc.loginWithRedirect()` |
| `useIsAuthenticated()` | `useSession().isAuthenticated` (+ `isSessionLoading`) |
| `useMsal().accounts[0]` / `idTokenClaims` | `useUser().user` |
| `acquireTokenSilent({ scopes })` → `accessToken` | `useSession().sessionToken` (the SDK refreshes it) — verify which token is exposed with `oidcConfig` via the Docs MCP |
| `AuthenticatedTemplate` / `UnauthenticatedTemplate` | Conditional render on `isAuthenticated` |
| `MsalAuthenticationTemplate` | Guard component that calls `loginWithRedirect()` |
| `instance.logoutRedirect()` | `useDescope().oidc.logout({ post_logout_redirect_uri })` |
| Profile edit policy | User Profile Widget |
| Password reset policy / `AADB2C90118` | Part of the sign-in Flow — delete the handling |
| Account filtering by policy name | Delete |

The redirect page needs no code — `AuthProvider` finishes the login.

### Angular + @azure/msal-angular

**Remove:** `MsalModule`, `MsalGuard`, `MsalInterceptor`, `MsalRedirectComponent`,
`MsalBroadcastService`, `MsalService`, `protectedResourceMap`.

**Add:** `@descope/angular-sdk`:

```ts
DescopeAuthModule.forRoot({
  projectId: environment.descopeProjectId,
  oidcConfig: {
    issuer: environment.descopeInboundIssuer,
    clientId: environment.descopeInboundClientId,
    scope: 'openid profile email tasks.read',
  },
})
```

| MSAL Angular | Descope |
|---|---|
| `canActivate: [MsalGuard]` | `canActivate: [descopeAuthGuard]` with `data: { descopeFallbackUrl: '/login' }` |
| `MsalInterceptor` + `protectedResourceMap` | `descopeInterceptor` via `provideHttpClient(withInterceptors([descopeInterceptor]))`, with `pathsToIntercept` in `forRoot` (attaches `Bearer <session token>`, refreshes and retries on 401/403) |
| `MsalService.loginRedirect()` | `descopeAuthService.descopeSdk.oidc.loginWithRedirect()` |
| `MsalService.instance.getActiveAccount()` | `DescopeAuthService.user$` / `getSessionToken()` |
| `MsalBroadcastService.inProgress$` / account events | `DescopeAuthService.session$` / `user$` |
| `MsalRedirectComponent` bootstrap | Remove |

### Next.js

Typical B2C setups: `@azure/msal-react` in client components, or NextAuth with the Azure AD B2C
provider.

- Replace with `@descope/nextjs-sdk`. Its `AuthProvider` passes every prop (including `oidcConfig`) to the React SDK and sets session/refresh tokens in cookies (`sameSite: 'Lax'`) so `authMiddleware` and `session()` can read them — derived from SDK code; test it.
- NextAuth users: either switch to `@descope/nextjs-sdk`, or replace the Azure AD B2C provider with NextAuth's Descope provider (verify the provider config via the Docs MCP).
- Server: `session()` from `@descope/nextjs-sdk/server` (not `getServerSession`). Next.js 15: `cookies()`/`headers()` are async.
- Delete MSAL redirect pages and `/api/auth/callback/azure-ad-b2c` handling when NextAuth is removed.

### Vue + @azure/msal-browser

Vue B2C apps use `@azure/msal-browser` directly (often with a custom plugin/composable).

```ts
import descope from '@descope/vue-sdk';

app.use(descope, {
  projectId: import.meta.env.VITE_DESCOPE_PROJECT_ID,
  oidcConfig: {                       // missing from the plugin's types — cast
    issuer: import.meta.env.VITE_DESCOPE_INBOUND_ISSUER,
    clientId: import.meta.env.VITE_DESCOPE_INBOUND_CLIENT_ID,
    scope: 'openid profile email tasks.read',
  },
} as any);
```

On the redirect page, call `sdk.oidc.finishLoginIfNeed()` (from `useDescope()`) before relying
on `useSession()`, `fetchSession`, or `routeGuard` — the Vue plugin does not do it automatically.
Replace the custom MSAL navigation guard with `routeGuard`.

### Plain JavaScript + @azure/msal-browser

```js
import createSdk from '@descope/web-js-sdk';

const sdk = createSdk({
  projectId: 'P...',
  oidcConfig: { issuer: '...', clientId: '...', scope: 'openid profile email tasks.read' },
});

// login button
sdk.oidc.loginWithRedirect();

// on every page load (handles the redirect back)
await sdk.oidc.finishLoginIfNeed();
```

Remove `PublicClientApplication`, `handleRedirectPromise`, and `acquireTokenSilent` wrappers.

### Embedded sign-in (iframe) → embedded Flow

Remove the iframe, the sign-in route that hosted MSAL inside it, `window.top.location.reload()` /
`postMessage` glue, and the custom policy's `JourneyFraming`. Render the Flow in the page:

```jsx
import { Descope } from '@descope/react-sdk';

<Descope flowId="sign-up-or-in" onSuccess={() => navigate('/')} />
```

Social login now works (B2C's iframe supported local accounts only).

### Server-side web apps

**ASP.NET Core with `Microsoft.Identity.Web` (OIDC sign-in):** replace
`AddMicrosoftIdentityWebAppAuthentication(Configuration, "AzureAdB2C")` with standard cookie +
OpenID Connect handlers:

```csharp
builder.Services
    .AddAuthentication(o => {
        o.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
        o.DefaultChallengeScheme = OpenIdConnectDefaults.AuthenticationScheme;
    })
    .AddCookie()
    .AddOpenIdConnect(o => {
        o.Authority = builder.Configuration["Descope:Issuer"];   // Inbound App issuer, or https://api.descope.com/<ProjectID> for a Federated App
        o.ClientId = builder.Configuration["Descope:ClientId"];
        o.ClientSecret = builder.Configuration["Descope:ClientSecret"];
        o.ResponseType = "code";
        o.Scope.Add("email");
        o.Scope.Add("tasks.read");                                // Resource scopes, if any
        o.SaveTokens = true;
        o.MapInboundClaims = false;                               // keep claim names as issued
    });
```

Remove `AddMicrosoftIdentityUI`, `MicrosoftIdentity/Account/*` routes, policy-specific
challenge code (`EditProfile`, `ResetPassword`), and `AzureAdB2C` config.

**Node.js (`msal-node` `ConfidentialClientApplication` or `passport-azure-ad` `OIDCStrategy`):**
replace with `openid-client` (discovery from the Descope issuer, same callback route).

**Python (`msal` `ConfidentialClientApplication`, Flask/Django):** replace with Authlib or
another OIDC client using the Descope issuer.

**Java (Spring Security `oauth2Login` with a B2C registration):** change the client registration
`issuer-uri`, `client-id`, `client-secret`, and scopes to the Descope app.

### Native / mobile

MSAL iOS/Android with B2C authorities, or ROPC → Descope Swift / Kotlin / Flutter / React Native
SDKs with native Flows (or hosted login through the system browser). Moving off ROPC adds MFA and
passkeys. Update redirect URIs / deep links.

---

## Testing Checklist

- [ ] Stale-reference sweep returns nothing outside the dual-token validator during a phased rollout; nothing at all after B2C decommission (`@azure/msal`, `Microsoft.Identity.Web`, `passport-azure-ad`, `b2clogin.com`, `B2C_1`, `AzureAdB2C`, `scp`, `emails[0]`, `AADB2C`)
- [ ] Build passes; app starts
- [ ] Hosted login (or embedded Flow) completes and returns to the app
- [ ] Access token: `iss` = Inbound App issuer, `aud` = Resource, `scope` has the expected scopes
- [ ] API returns 200 with the token, 401 without, 403 without the scope
- [ ] `email`, `name`, `b2cObjectId`, roles present via JWT Template
- [ ] Imported local, social, and enterprise SSO users each land on their imported account
- [ ] Logout ends the session
- [ ] Dual-token validation accepts both B2C and Descope tokens during the rollout window
- [ ] M2M Inbound App client-credentials token is accepted by the API
