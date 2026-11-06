# Descope Migration: Implementation Notes (Azure AD B2C)

## Contents

**Architecture**
- [B2C hosts every login; each policy is its own authority](#b2c-hosts-every-login-each-policy-is-its-own-authority)
- [MSAL POC first, then replace MSAL](#msal-poc-first-then-replace-msal)
- [Hosted login by default](#hosted-login-by-default)
- [Which Descope app: Inbound App, Federated App, or plain SDK](#which-descope-app-inbound-app-federated-app-or-plain-sdk)
  - [Consent for first-party Inbound Apps](#consent-for-first-party-inbound-apps)
  - [Selecting the Resource (resource parameter)](#selecting-the-resource-resource-parameter)
  - [Embedded Flows and scoped APIs](#embedded-flows-and-scoped-apis)
  - [Apps without API scopes](#apps-without-api-scopes)
- [Descope OIDC endpoints](#descope-oidc-endpoints)
  - [Finding the Inbound App issuer](#finding-the-inbound-app-issuer)
- [Token claim mapping](#token-claim-mapping)
- [B2C as a SAML IdP → Descope SAML app](#b2c-as-a-saml-idp--descope-saml-app)

**Feature Mapping**
- [User flows and custom policies → Flows](#user-flows-and-custom-policies--flows)
- [API connectors and REST technical profiles → HTTP Connectors](#api-connectors-and-rest-technical-profiles--http-connectors)
- [Identity providers](#identity-providers)
  - [Picking the tenant at sign-in](#picking-the-tenant-at-sign-in)
- [MFA and Conditional Access](#mfa-and-conditional-access)
- [Custom attributes](#custom-attributes)
- [Roles and groups](#roles-and-groups)
  - [Importing organizations](#importing-organizations)
- [Page layouts → Flow styles](#page-layouts--flow-styles)
- [Passkeys](#passkeys)
- [Localization](#localization)
- [Invitations and email / SMS templates](#invitations-and-email--sms-templates)
- [Fraud and risk detection](#fraud-and-risk-detection)
- [Custom domain on Azure Front Door](#custom-domain-on-azure-front-door)
- [App launcher portal (Azure My Apps)](#app-launcher-portal-azure-my-apps)
- [Session behavior and token lifetimes](#session-behavior-and-token-lifetimes)
  - [Split-clock setups → step-up](#split-clock-setups--step-up)
  - [Cross-app SSO](#cross-app-sso)
- [Audit and sign-in logs](#audit-and-sign-in-logs)

**Secrets, Certificates and Policy Keys**
- [Secrets can't be exported](#secrets-cant-be-exported)
- [Policy key inventory](#policy-key-inventory)

**User Migration**
- [User schema](#user-schema)
- [Exporting users from B2C](#exporting-users-from-b2c)
- [User ID strategy](#user-id-strategy)
  - [Overriding sub (JWT Template → Override system claims)](#overriding-sub-jwt-template--override-system-claims)
  - [Filling b2cObjectId for new users](#filling-b2cobjectid-for-new-users)
  - [App changes when keeping the B2C ID](#app-changes-when-keeping-the-b2c-id)
- [Password strategy](#password-strategy)
- [Social users](#social-users)
- [Enterprise SSO users](#enterprise-sso-users)

**Enterprise SSO Migration**
- [Cutover strategy](#cutover-strategy)
- [Per-connection inventory and cutover rules](#per-connection-inventory-and-cutover-rules)
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

> **See also:** `flows-and-widgets.md` (lingo, Flows, Widgets, SSO Setup Suite),
> `backend-sdks.md` (.NET, Node.js, Python, Java API validation), and
> `b2c-detection-patterns.md` (code search, Graph discovery, evidence template).

---

## Architecture

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

### MSAL POC first, then replace MSAL

Always offer a proof of concept that keeps MSAL and points it at Descope, so the customer can
plug in Descope values and see sign-in work before changing SDKs. It is a **POC step, never the
end state**: MSAL's non-Microsoft mode has limited support (Microsoft's code says *"Support is
limited for this mode"*), so the plan always replaces MSAL with the Descope SDK or a standard OIDC
library before production cutover.

| MSAL library | POC against Descope |
|---|---|
| `@azure/msal-browser`, `msal-react`, `msal-angular` | Yes — `system.protocolMode: "OIDC"` |
| `@azure/msal-node` | Yes — `system.protocolMode: "OIDC"` |
| MSAL.NET (`Microsoft.Identity.Client`) | Yes — `WithOidcAuthority(<issuer>)` on the app builder; check the installed version has it |
| `Microsoft.Identity.Web` | No — built for Entra / B2C. Use the standard ASP.NET OpenID Connect or JwtBearer handler (Server-side web apps; `backend-sdks.md` → .NET / ASP.NET Core) |
| MSAL Android / iOS | Not verified — go straight to the Descope native SDK |

**Values the customer plugs in** (msal-browser shown):

```js
const msalConfig = {
  auth: {
    clientId: '<Inbound App client ID>',          // public client with PKCE
    authority: '<Inbound App issuer>',            // Finding the Inbound App issuer
    knownAuthorities: ['<Descope host>'],          // e.g. api.descope.com or the custom domain
    redirectUri: '<registered on the Inbound App>',
  },
  system: { protocolMode: 'OIDC' },
};
const loginRequest = { scopes: ['openid', 'profile', 'offline_access', 'tasks.read'] };
```

**Sending the Resource** (Descope needs `resource` on the authorize and token requests — Selecting
the Resource):
- msal-browser 5.x: the request's `resource` option.
- msal-browser 2.x / 3.x: `extraQueryParameters: { resource }` (authorize) and
  `tokenQueryParameters: { resource }` (token, sent as a query parameter). Untested against Descope —
  the POC must confirm the access token's `aud` is the Resource.

**Still required in the POC** — MSAL doesn't hide these:
- Remove B2C policy logic: per-policy authorities, account filtering by policy name,
  `AADB2C90118` handling, `tfp` / `acr` checks (SKILL.md Execution Phase 4d). B2C user flows
  can't reset a password inside sign-in, so "Forgot password?" ends the sign-in with
  `AADB2C90118` and the app restarts login on the password-reset policy; in Descope, reset is a
  branch of the sign-in Flow, so the app never gets that error and the handler is dead code.
- Backend validates Descope tokens: issuer, `aud` = Resource, `scp` → `scope` (`backend-sdks.md`).
- Inbound App consent setup, the JWT Template claims, and logout through Descope's
  `end_session_endpoint` from discovery.

**POC checklist:** sign-in completes and returns to the app; the access token has the Inbound App
`iss`, `aud` = the Resource and the expected `scope`; silent token renewal works; logout ends the
Descope session; the API accepts the token. Then plan the SDK replacement (Execution Phase 4a).

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
request them with MSAL. Customers are used to scoped access tokens, so keep that model: the API
becomes a **Resource** with the same scope names, and the frontend signs in through an **Inbound
App**. SKILL.md Decision 1 picks the app; `b2c-detection-patterns.md` → App registration type →
Descope app classifies each registration.

#### Consent for first-party Inbound Apps

B2C never showed the customer's own users a consent screen for the customer's own app, so don't add
one (Match first, then enhance). In the Flow attached to the Inbound App:
- The success path **must** run **Update User Consent** (or **Update Tenant Consent**). The consent
  screen is optional; the consent action is not — without it the Flow fails.
- Turn on **Scopes auto approval** on that action and leave out the consent screen. The scopes are
  granted and the consent record is still written.
- Without auto approval, the screen before the action must include the **Inbound App Scopes**
  component. If it's missing and the scopes are optional, the Flow succeeds but the token carries
  **no** scopes — every API call then returns 403. Check this first when scopes go missing.

Partner, agent and CLI Inbound Apps (third-party callers) keep a real consent screen with the
Inbound App Scopes component.
[Consent flows](https://docs.descope.com/identity-federation/inbound-apps/consent-flows).

#### Selecting the Resource (`resource` parameter)

Scope names alone don't select a Resource — only the RFC 8707 `resource` parameter does, and
without it the token's `aud` isn't the Resource. Put the scope names in `oidcConfig.scope` (with a
custom issuer, the React SDK's default `scope` is just `openid`) and send the Resource on both
requests:

```js
sdk.oidc.loginWithRedirect({
  resource: '<Resource>',                         // authorize request
  extraTokenParams: { resource: '<Resource>' },   // token request
});
```

- **Why twice:** Descope expects the same `resource` on the authorize and token requests. The web
  SDK forwards these args to `oidc-client-ts`, which adds `resource` to the authorize URL but sends
  only `extraTokenParams` (plus code, verifier, client ID, redirect URI) on the code exchange.
- **Refresh:** the SDK's refresh call doesn't send `resource` — check that a refreshed access token
  still has `aud` = the Resource.
- `/authorize` accepts up to 50 `resource` values (`aud` lists them all); the token endpoint accepts one.
- Resource indicators are gated by project/app settings — allow the Inbound App to request the Resource.
- After login the SDK stores the OIDC access token as the session token, so
  `useSession().sessionToken` (React) / `getSessionToken()` is what the frontend sends to the API.

Configure hosted login with the Inbound App's `clientId` and `issuer` (Finding the Inbound App issuer).

#### Embedded Flows and scoped APIs

An embedded Flow (B2C iframe users, or on request) issues a Descope **session token** — `aud` is
the project ID and there is no `scope` claim. For apps whose API checks scopes, either keep hosted
login through the Inbound App, or map the scope checks to roles/permissions in the session token.
An embedded Flow can't mint Inbound App access tokens: its `thirdPartyAppId` /
`applicationScopes` / `thirdPartyAppStateId` start options only supply consent context or finish an
OAuth authorize already in progress — the token always comes from the OAuth `/token` exchange.

#### Apps without API scopes

Hosted login can use the project's OIDC app: `oidcConfig={true}` or
`oidcConfig={{ applicationId }}` (a Federated App's ID; omitted → the default OIDC application).
The backend validates the session token.

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
| Issuer | Default `https://api.descope.com/v1/apps/<ProjectID>` — see Finding the Inbound App issuer |
| Authorization | `/oauth2/v1/apps/authorize` |
| Token | `/oauth2/v1/apps/token` |
| JWKS | `jwks_uri` from the discovery document (typically `https://api.descope.com/<ProjectID>/.well-known/jwks.json`) |

#### Finding the Inbound App issuer

Never hardcode or construct it. Three things change it:
- **Imported client IDs:** importing any Inbound App with a custom client ID (for example to keep
  B2C's client IDs) switches the project's issuer to `…/v1/apps/customized/<ProjectID>`. The Inbound
  App settings page keeps showing the original issuer after the import, so don't copy it from there
  ([Issuer after importing client IDs](https://docs.descope.com/migrate/oauth-clients#issuer-after-importing-client-ids)).
- **Custom domain:** the host becomes the custom domain instead of `api.descope.com`.
- **Region:** non-US projects use their regional base URL.

How to get it: sign in once through the Inbound App and take `iss` from the access token, then
confirm `<iss>/.well-known/openid-configuration` returns 200 with the same `issuer`. Put that value
in config (frontend `oidcConfig.issuer`, backend issuer / authority) and read `jwks_uri` from the
discovery document. Execution Phase 6 → Test 4 checks that the configured issuer matches discovery.

### Token claim mapping

| B2C claim | Meaning | Descope |
|---|---|---|
| `sub` / `oid` | B2C object ID | Descope user ID by default. Keep the B2C value: custom attribute `b2cObjectId`, emitted as `oid` (and as `sub` with Override system claims) |
| `tfp` / `acr` | Policy name | None — delete code that reads it |
| `iss` | `https://<tenant>.b2clogin.com/<tenant-guid>/v2.0/` (or `/tfp/<guid>/<policy>/v2.0/`) | Inbound App: the Inbound App issuer (default `https://api.descope.com/v1/apps/<ProjectID>` — see Finding the Inbound App issuer); session: `https://api.descope.com/<ProjectID>` (custom domain / region change the host) |
| `aud` | App registration (client) ID | Inbound App access token: the Resource; session token: project ID |
| `scp` | Space-separated short scope names | `scope` — space-separated string (Inbound App tokens) |
| `emails` | Array of emails (local accounts) | `email` via JWT Template |
| `name`, `given_name`, `family_name` | Profile | Add via JWT Template |
| `idp` | Federated provider (e.g. `google.com`, customer IdP issuer) | Tenant (`dct` / `tenants`) and auth method (`amr`) |
| `extension_<name>` | Custom attribute (custom-policy name; Graph name is `extension_<appIdNoHyphens>_<name>`) | Custom attribute + JWT Template |
| `azp` | Authorized party (client ID) | `azp` on Inbound App tokens — check it if only some clients may call the API |

Descope session tokens contain `sub`, `amr`, `drn`, `tenants`, `roles`, `permissions`, `dct` by
default — not `email` or `name`. A user JWT Template applies to both session tokens and Inbound
App access tokens.

### B2C as a SAML IdP → Descope SAML app

Some B2C custom policies issue SAML assertions to the customer's own SAML apps (a relying party
policy with `<Protocol Name="SAML2"/>` and a `Saml2AssertionIssuer`). These apps usually key users
on the B2C object ID — Microsoft's SAML sample puts `objectId` in the `NameID`
(`<SubjectNamingInfo ClaimType="objectId" ExcludeAsClaim="true"/>`; `ExcludeAsClaim` keeps it out
of the attributes). Customized policies may also send it as an attribute (`objectId`, or
`http://schemas.microsoft.com/identity/claims/objectidentifier`) — the `PartnerClaimType` on each
relying-party `OutputClaim` is the attribute name the app sees. Each one becomes a
Descope **SAML Federated App**, and the assertion must look the same to the app.

**Inventory each SAML relying party** (policy XML, plus a captured assertion from a browser SAML
tracer — the XML doesn't show defaults):

| SAML app | Entity ID / ACS URL | `NameID` source + `Format` | Attributes sent (exact names) | Signed / encrypted | IdP-initiated? |
|---|---|---|---|---|---|

**Rebuild the assertion in Descope:**

| B2C assertion | Descope SAML app setting |
|---|---|
| `NameID` = `objectId` | Advanced → SAML Assertion Subject Type: custom attribute `b2cObjectId`. Use the same `Format` the app received; Descope recommends `unspecified` for custom attributes if the app doesn't care |
| `NameID` = email | Subject Type: Email |
| Attribute carrying `objectId` (`objectId`, `…/objectidentifier`, or another `PartnerClaimType`) | **SSO / Add SAML Attributes** Flow action: key = the exact attribute name, type **Dynamic**, value `user.customAttributes.b2cObjectId` |
| Other attributes (email, name, given/surname, roles) | SSO Mapping → User Attribute Mapping with the exact same attribute names; groups/roles via Group Mapping |
| Attributes computed in the policy (claims transformations, REST calls) | Compute in the Flow (Scriptlet / HTTP Connector), then **SSO / Add SAML Attributes** |

**Recommended: reconnect each SAML app once, in Cutover stage 1.** These are the customer's own apps, so
point each one at its Descope SAML app's metadata, one app at a time, and test it before the next
(Cutover strategy). The Worker approach below is the exception, for an app that is hard to
reconfigure.

**What still changes for the SAML app** (its admin acts once at cutover):
- New IdP metadata: entity ID, SSO URL and signing certificate come from the Descope SAML app.
  B2C let the policy set the issuer the app expects (`IssuerUri` on `Saml2AssertionIssuer`);
  check whether the app accepts Descope's entity ID or needs its IdP configuration updated.
  Upload the original B2C signing certificate as the app's custom certificate if the customer
  still has it (Policy key inventory) — otherwise the app must trust Descope's certificate.
- IdP-initiated SSO: B2C's IdP-initiated URL is replaced by the Descope app's
  `/v1/auth/saml/idp/initiate?app=<id>` URL; update any portal tiles or links.
- New users: their `NameID` / object ID attribute is their Descope user ID (`U…`), not a GUID — the
  same string-ID check as the app (App changes when keeping the B2C ID).

**Exception — keep the app's IdP URLs with a Worker.** If an app can't be reconfigured, a
Cloudflare Worker on B2C's custom-domain hostname can serve Descope's metadata at the old metadata
path, forward sign-in requests from the old SSO URL to Descope's (keeping `SAMLRequest` and
`RelayState`; POST binding needs an auto-submit form), and map the old IdP-initiated link. The
SSO migration Worker template handles the other direction, so this is new Worker logic. It does not
change what Descope signs, so the app still sees a change unless:
- B2C used a custom domain the customer controls (not `*.b2clogin.com`),
- the Descope SAML app's entity ID can be set to B2C's `IssuerUri` (unconfirmed — check), or the app
  doesn't check the issuer, and
- the original B2C signing certificate is uploaded to the Descope SAML app.
Test that Descope accepts the forwarded request (its `Destination` still names the old URL).

Docs: [SAML apps](https://docs.descope.com/identity-federation/applications/saml-apps),
[Add SAML Attributes](https://docs.descope.com/flows/actions/add-saml-attributes).

---

## Feature Mapping

### User flows and custom policies → Flows

| B2C | Descope |
|---|---|
| Sign-up/sign-in user flow | `sign-up-or-in` Flow |
| Password reset user flow (or `AADB2C90118` redirect) | Password reset branch/Flow (template available) |
| Profile edit user flow | User Profile Widget or a profile Flow |
| Custom policy user journey | One Flow; orchestration steps → Flow steps; sub-journeys → subflows |
| Claims transformations | Scriptlets (logic) or JWT Template (token shaping) |
| Technical profile with `IncludeInSso`/session management, token lifetimes | Session Management settings — see Session behavior and token lifetimes |
| Localization | Flow localization — see Localization |

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
| `domain_hint` / home realm discovery | Tenant email domains, or a tenant slug or ID — see Picking the tenant at sign-in |
| Another B2C tenant as IdP | OIDC provider or tenant SSO |

#### Picking the tenant at sign-in

B2C picks the customer's IdP from `domain_hint`, an IdP button, or a policy per customer. Find
which of these the app relies on (search group 7, Custom Policy XML Hints) and use the matching row:

| How B2C picks the customer | Descope |
|---|---|
| The user's email domain | Tenant email domains (SSO domains) — the Flow routes from the email the user types |
| `domain_hint` holds a customer key, not an email domain; a customer has several domains; the app already knows the customer | **Tenant slug or ID** passed in the `tenant` flow parameter (embedded Flow prop, or on the hosted login URL) — the Flow starts in that tenant and skips the email screen |
| The user picks or types their organization | **Tenant Name** input in the Flow — the user types the tenant's name (slug); conditions read it as `form.tenantName` |
| A per-customer app, login URL or subdomain | Hardcode the tenant slug in that app's hosting settings (**Tenant** field) |
| Several customers share one email domain | Allow duplicate SSO domains; a condition on `ssoDomainsTenantsCount` shows the Switch Tenant screen |

The `tenant` parameter is a hint: it sets the current tenant (`dct`) but doesn't add the user to
the tenant. Record the value the app sends today in the SSO inventory (Routing key) so each
customer's Descope tenant can be found from it.
[Tenant slug or ID](https://docs.descope.com/auth-methods/sso#option-2-tenant-slug-or-id),
[Flow inputs](https://docs.descope.com/flows/dynamic-keys/flow-inputs).

### MFA and Conditional Access

- B2C MFA (SMS/voice, email OTP, TOTP authenticator app) → MFA steps in the Flow. TOTP seeds can't migrate.
- Conditional Access in B2C only offers **require MFA** or **block** (Microsoft retired B2C Premium P2 and ID Protection on March 15, 2026, and moved all P2 tenants to P1 — [B2C FAQ](https://learn.microsoft.com/en-us/azure/active-directory-b2c/faq). Any risk-based Conditional Access policies a tenant still has no longer run) → Flow conditions plus risk/fraud connectors.
- "MFA only for some users/apps" → Flow condition on roles, tenant, or `ssoAppId`.

### Custom attributes

Graph name: `extension_<b2c-extensions-app client ID without hyphens>_<name>` (the
`b2c-extensions-app` registration). Custom policies use `extension_<name>`. Define each as a
Descope custom attribute of the matching type before import; add the ones the app reads to the
JWT Template. See User schema for the inventory and type mapping.

### Roles and groups

B2C does not support roles for consumer accounts and cannot emit groups from user flows. Find how
the app built roles:

| Pattern | Detect | Descope |
|---|---|---|
| Custom attribute (`extension_Role`) | Claim checks on `extension_*` | Roles (import values), or keep as custom attribute |
| App database + API connector "before sending token" | REST call returning roles | Roles in Descope, or keep the DB and call it from a Flow HTTP Connector |
| Custom policy calling Graph `memberOf` | `RestfulProvider` to `graph.microsoft.com/.../memberOf`, `groups` claim | Roles, or tenants if groups represent customer organizations |
| Roles only in app database | No role claims | Nothing to migrate |

The table above is how roles reach the token. Separately, find **how users get assigned** —
that process keeps running after cutover and needs its own replacement:

| How assignment happens in B2C | Descope replacement |
|---|---|
| An admin adds users to groups in the Azure portal | Console (Users → roles), or the Role / User Management Widget in the customer's own admin page |
| App code calls Graph (`POST /groups/{id}/members/$ref`, `PATCH` an `extension_*` role attribute) | Management SDK: `user.addRoles` / `addTenantRoles`, or update the custom attribute — see `backend-sdks.md` |
| A policy step at sign-up or sign-in decides the group (API connector, REST technical profile, claims transformation) | A Flow step that assigns the role or tenant — `flows-and-widgets.md` → Assigning roles and tenants in a Flow |
| A script or job syncs groups from another system (HR, CRM) | Same job, calling the Descope Management API instead of Graph |
| The customer's IdP sends groups (SAML attribute or OIDC claim) | SSO group mapping on the tenant ([docs](https://docs.descope.com/auth-methods/sso/saml#group-mapping)); SCIM if they want users and groups pushed ahead of login |

**Exporting current memberships for the import:** read groups and members through Graph
(`b2c-detection-patterns.md` → Read-Only Microsoft Graph Discovery), map each group to a Descope
role (or a tenant, if the group is a customer organization), and include the roles in the import batch.

#### Importing organizations

Whether organizations came from groups or a custom attribute
(`b2c-detection-patterns.md` → Customer organization discovery):
1. Create one tenant per boundary group or distinct attribute value, before importing users. Keep
   the B2C value (group ID or attribute value) on the tenant as a tenant custom attribute
   (`b2cOrgId`), so the app's existing org claim and data keys can still be matched.
2. Import each user with `userTenants` (`tenantId` plus `roleNames` for tenant roles from
   combined groups); project-level roles go in `roleNames`.
3. Keep the original attribute on the user (`customAttributes`) until the app reads the Descope
   tenant instead.

### Page layouts → Flow styles

B2C page layouts are hosted HTML templates (`ContentDefinition` `LoadUri` in custom policies, or
"custom page content" in user flows). Rebuild branding in Flow styles and screens; do not host
the old templates.

### Passkeys

B2C has no native passkeys and its Conditional Access cannot require them. Customers who have
passkeys used Microsoft's community FIDO2 sample or a partner (Nok Nok, Authsignal, Transmit).
Those credentials are bound to the old domain and cannot migrate — add a passkey enrollment step
after first login (`freshlyMigrated` condition). For everyone else, passkeys are a new capability.

### Localization

Match the languages and the wording users see today (Match first, then enhance) — reuse B2C's
translated strings instead of machine-translating from scratch.

**Where B2C keeps the strings:**
- User flows: Languages → language customization on, a default language, the enabled languages,
  and per-page overrides (each page's strings download and upload as a JSON resource file).
- Custom policies: the `<Localization Enabled="true">` element (usually in its own file in the
  inheritance chain) — `<SupportedLanguages DefaultLanguage="…">`, then one
  `<LocalizedResources Id="api.<page>.<lang>">` per page and language holding `<LocalizedString>`
  values (`ElementType` / `StringId`) and `<LocalizedCollections>` (drop-down options).
- Page layout templates: HTML in a `ContentDefinition` `LoadUri` can hold text too, sometimes per
  language (`{Culture:RFC5646}` in the URI).
- How the app picks the language: `ui_locales` on the authorize request (MSAL
  `extraQueryParameters`), or the browser language.

**In Descope:**
1. Build each Flow's screens in the default language first.
2. Configure localization on the Flow (Localization → source language and target languages, manual
   or through a localization connector). Do the same for widgets — a widget is localized as one unit,
   including the flows it runs.
3. Load B2C's strings for each language as overrides: by hand in the Console, the import/export in
   the localization page, or the Management API (`POST /v1/mgmt/localization/flow/import`). Map each
   B2C `StringId` to the matching screen text — B2C pages and Descope screens don't share keys, so
   this mapping is manual work; list it in the plan.
4. Repeated strings (product name, legal text) → Global Strings.
5. Error text: Flow components' errors are translated with the Flow; system errors (for example a
   wrong OTP) are translated in the frontend with the error transformer.
6. Email and SMS templates are localized separately (messaging templates).
7. Language selection: embedded Flows and widgets take a `locale` prop — set it from wherever the app
   sent `ui_locales` to B2C. For hosted login, check how the hosted page picks the language before
   relying on `ui_locales`.

Docs: [Localization](https://docs.descope.com/management/localization),
[Customizing flow errors](https://docs.descope.com/handling-flow-errors/customizing-flow-errors).

### Invitations and email / SMS templates

Keep two journeys apart: **sign-up** (the user starts it) and **invite** (an admin or the app starts
it). B2C has no built-in invitation for consumer accounts, so customers build their own — find out
how before mapping.

| B2C today | Descope |
|---|---|
| Self sign-up with email verification code (Microsoft sends the email; company branding only) | Sign-up Flow with email OTP or magic link; email from a Descope **messaging template** on an email connector |
| Custom email verification in a custom policy (display controls + REST call to SendGrid, Mailjet or similar with the provider's template) | The same provider as a Descope messaging connector (SendGrid, AWS SES, Postmark, MailerSend, Mandrill, SMTP, …); rebuild the template as a Descope messaging template, with **template options** for dynamic content |
| Invitation built by the app: create the user through Graph, then email a link carrying a signed `id_token_hint` to an invite policy | Descope invites: Management API (create user with `invite: true`, `inviteUrl`, `sendMail`, `templateOptions`), the Console, the User Management Widget, or the **User / Invite** Flow action. Optional magic link token in the invite and invite expiration (Project Settings → Sign Ups and User Invitations). The app stops minting `id_token_hint` — its signing key drops out of the policy key inventory |
| Invite-only app (self sign-up turned off; users created by admins) | Project Settings → **Block self-registration sign up**: only invited or SSO users get in |
| Password reset email | Password reset Flow (template available) with a messaging template |
| SMS codes sent by Microsoft's telephony | An SMS connector (Twilio, Twilio Verify, AWS SNS, Vonage, Infobip, Telesign, …) — the customer now owns sender setup and per-country cost; pair with SMS fraud controls (Fraud and risk detection) |

**What changes for the customer:** B2C sent verification email and SMS for them. In Descope they
choose the messaging connector, so plan for sender setup on their own domain (SPF / DKIM with the
email provider) and the provider account. Templates are localized in Descope too (Template
Localization; see Localization).

**Discovery:** does the app create users through Graph and send its own invite emails? Is there an
invite policy reading `id_token_hint`? Which REST technical profiles call an email provider (check the
`ServiceUrl` host)? Collect the current email and SMS wording, sender address, and branding.

Docs: [Inviting users](https://docs.descope.com/management/user-management/invite-users),
[Messaging templates](https://docs.descope.com/management/messaging-templates),
[User / Invite action](https://docs.descope.com/flows/actions/user-invite).

### Fraud and risk detection

Inventory every fraud or abuse control B2C applies today and give each one a Descope replacement
before cutover — a control that disappears is a regression, not a "later improvement". New signals
B2C never had are post-cutover work (Match first, then enhance). Descope's Fraud & Attack
Protection works in Flows, so it covers both hosted and embedded login.

**Where B2C keeps them:** Conditional Access policies (Graph), the portal (Security →
Authentication methods → Password protection for smart lockout; CAPTCHA on user flows), custom
policy XML (REST technical profiles calling fraud vendors, phone country-code lists), and Azure
Front Door WAF (Custom domain on Azure Front Door).

| B2C control | Descope |
|---|---|
| Conditional Access with Identity Protection risk (user risk / sign-in risk). Retired with B2C P2 on March 15, 2026 — if the policies still exist they no longer run, so this is a gap the customer may already have | Built-in `riskInfo` signals in Flow conditions → MFA or block: `impossibleTravel`, `vpnDetected`, `botDetected` / `riskScore` (Fingerprint Assess action), `trustedDevice` |
| Conditional Access location block (applies to sign-in, not sign-up, in B2C) | **Lists** (countries, IPs / CIDR) in Flow conditions — can cover sign-up too |
| B2C CAPTCHA (sign-up and sign-in for local accounts) | A CAPTCHA connector after a screen — reCAPTCHA (v3 / Enterprise), Turnstile, hCaptcha, Arkose — or the Fingerprint Assess action |
| Fraud vendor called from a custom policy (REST technical profile — check the `ServiceUrl` host) | The matching Descope fraud connector if one exists (Arkose, Sardine, Forter, Darwinium, Fingerprint, Telesign, …), otherwise a Generic HTTP Connector to the same API |
| Phone MFA country-code restrictions and telephony-fraud mitigation | Restrict phone countries and follow the SMS pumping (IRSF) guide; **Check Rate Limit** on SMS steps; Telesign for phone-number risk |
| Smart lockout (default: 10 failed attempts → 1-minute lockout, growing on repeat) | Password settings: **Temporary lock after x attempts, for y minutes** (or permanent lock); the password-attempts Flow condition for custom handling |
| Front Door WAF bot / rate rules | See Custom domain on Azure Front Door |

Notes:
- Fraud connectors that run a script in the browser (reCAPTCHA, Turnstile, hCaptcha, Arkose,
  Fingerprint) must come after a **Screen** in the Flow.
- Don't combine `riskInfo.riskScore` with a fraud connector — read the connector's own output
  instead.

Docs: [Fraud & Attack Protection](https://docs.descope.com/fraud-protection),
[Implementing fraud and risk signals](https://docs.descope.com/flows/use-cases/implementing-fraud-risk-signals),
[Preventing SMS pumping](https://docs.descope.com/flows/use-cases/preventing-irsf-sms-pumping),
[Password settings](https://docs.descope.com/auth-methods/passwords/settings).

### Custom domain on Azure Front Door

A B2C custom domain (`login.<company>.com` instead of `<tenant>.b2clogin.com`) is served through
Azure Front Door, and the Front Door profile often does more than route traffic: a WAF policy
(managed rules, bot protection, rate limits, geo filters, IP allow/deny lists), rules-engine header
or redirect rules, and sometimes "block the default `b2clogin.com` domain" on the B2C side. None of
that is in Microsoft Graph or the policy XML, so ask for it — a portal export, or read-only CLI:

```bash
az afd profile list -o table
az afd custom-domain list --profile-name <profile> -g <rg> -o table
az afd route list --profile-name <profile> --endpoint-name <endpoint> -g <rg> -o table
az afd security-policy list --profile-name <profile> -g <rg> -o table
az network front-door waf-policy list -g <rg> -o table
```

| On the B2C hostname today | Descope |
|---|---|
| Custom domain → Front Door → B2C | Cutover stage 1: a **new** Descope custom domain — a CNAME such as `auth.<app root>` to Descope's regional target. Descope cookies are `SameSite=Strict`, so the custom domain must be a subdomain of the app's own site. Cutover stage 2: B2C's hostname moves to Descope through the SSO migration Worker (Cutover strategy) |
| WAF rate limiting | **Check Rate Limit** Flow action (by IP, ASN or JA4) on sensitive steps, on top of Descope's API rate limits |
| WAF geo filter, IP allow / deny lists | **Lists** (IPs / CIDR, countries) referenced in Flow conditions |
| WAF bot protection, managed rules | Descope fraud protection and fraud connectors (Fraud and risk detection) |
| Rules-engine headers / redirects | Usually B2C-specific (policy routing, `b2clogin` rewrites) — drop them; move anything still needed into the Worker |

Keep Front Door serving B2C's hostname until Cutover stage 2. Descope documents the Cloudflare Worker for
moving it; keeping Front Door in front of Descope instead is not documented — confirm with Descope
before planning on it. After Cutover stage 2, remove the B2C origin and the Front Door routes for it.

Docs: [Custom domain](https://docs.descope.com/how-to-deploy-to-production/custom-domain),
[Check Rate Limit](https://docs.descope.com/flows/actions/rate-limit-action),
[Lists](https://docs.descope.com/management/project-settings#lists).

### App launcher portal (Azure My Apps)

Some customers give users a portal of app tiles — Azure My Apps (`myapps.microsoft.com`) or one
they built — where a click opens each app already signed in. My Apps belongs to Entra ID
(workforce), so check which tenant the tiles and assignments live in; if it's the customer's
workforce Entra tenant rather than the B2C tenant, read assignments from there.

| Azure My Apps | Descope |
|---|---|
| Portal of tiles | **Applications Portal Widget** embedded in the customer's own page, or the hosted **Admin Portal** (a landing page where users launch their SSO apps and manage their profile) |
| Each tile is an app registration / enterprise app | Each tile is a Descope **Federated App** (OIDC or SAML). The widget lists Federated Apps only — apps on embedded Flows or Inbound Apps don't appear unless they are also set up as a Federated App; check before promising a tile |
| User / group assignment decides who sees a tile | Federated App assignment per user (`ssoAppIds` on import, `addSSOapps` later) or per tenant (Application Access). The widget shows only the apps the user can access |
| Click → IdP-initiated SAML or the app's sign-in URL | SAML apps: the app's IdP-initiated URL (`/v1/auth/saml/idp/initiate?app=<id>`); OIDC apps: the app's sign-in URL |
| Tile name and logo | The Federated App's name and logo in Descope |

**Watch the access rule:** a user with **no** assigned apps can sign in to every Federated App;
the first assignment limits them to the assigned apps. Importing tile assignments therefore also
locks users out of apps they weren't assigned to. Decide the default (Project Settings →
Federated Apps) before importing assignments.

**Inventory:** one row per tile — app, protocol, launch URL type, who is assigned (users, groups,
or tenants), logo.

Docs: [Applications Portal Widget](https://docs.descope.com/widgets/users#applications-portal-widget),
[Admin Portal](https://docs.descope.com/widgets/admin-portal),
[Federated app access](https://docs.descope.com/identity-federation/applications).

### Session behavior and token lifetimes

B2C sets these per user flow (Properties → Session behavior) or per custom policy, so two policies
can behave differently. Descope sets them per project, with overrides per tenant, per Inbound App,
and per Flow. Read every policy's values first; match them 1:1 (Match first, then enhance).

**Where to read them in B2C:**
- User flows: Properties → web app session lifetime, web app session timeout, single sign-on
  configuration, "Enable keep me signed in session" (days). Token lifetimes: user flow → Properties
  → Token lifetime.
- Custom policies: the relying party's `<UserJourneyBehaviors>` (`SingleSignOn Scope` and
  `KeepAliveInDays`, `SessionExpiryType`, `SessionExpiryInSeconds`), and the JWT issuer technical
  profile's metadata (`token_lifetime_secs`, `id_token_lifetime_secs`,
  `refresh_token_lifetime_secs`, `rolling_refresh_token_lifetime_secs`).

**B2C runs two clocks; Descope runs one.**
- B2C's sign-in session is a cookie on its own host (`b2clogin.com` or its custom domain). It only
  decides whether a user who is sent back to B2C must type credentials again.
- The tokens B2C gives the app decide how long the app keeps the user signed in without going back
  to B2C at all. The refresh token lifetime behaves as an **idle timeout** (unused for N days → signed
  out); the sliding window is an **absolute cap** from sign-in.
- In Descope the refresh token *is* the session: the app's session and "must they sign in again" are
  the same thing. The two B2C clocks can't be set independently — see Split-clock setups below.

| B2C setting | Range / default | What it really does | Descope |
|---|---|---|---|
| Access and ID token lifetime | 5–1440 min, default 60 | How often the app renews | **Session Token Timeout** (Project Settings → Session Management; minimum 3 minutes) |
| Refresh token lifetime | 1–90 days, default 14 (SPAs: 24 h)  | Idle timeout: unused for N days → signed out | **Session Inactivity** set to N days. While the app is open the SDK refreshes in the background, so "idle" means "app not used", as in B2C |
| Refresh token sliding window | default 90 days; 1–365 days or no expiry | Absolute cap from sign-in | **Refresh Token Timeout** (max 6 months; 3 years on Enterprise). "No expiry" can't be matched — use the maximum |
| Web app session lifetime + **Rolling** timeout | up to 24 h | Sign-in cookie extended on each silent sign-in | **Session Inactivity** (as above) |
| Web app session lifetime + **Absolute** timeout | up to 24 h | Sign-in cookie hard stop | **Refresh Token Timeout**; if it's much shorter than the token lifetimes, it's a split-clock setup (below) |
| "Keep me signed in" (KMSI) | 1–90 days | Persists the sign-in cookie for users who opt in | Checkbox on the login screen → condition → **Custom Claims** action with **Set Custom Refresh Duration**. Broader than B2C: it lengthens the whole session, not just the sign-in cookie — say so in the plan |
| Single sign-on scope `Tenant` | — | All apps share the B2C session | Shared session across apps — see Cross-app SSO below |
| Single sign-on scope `Application` / `Policy` | — | Session shared only within one app / one policy | No equivalent setting. If a journey must not reuse the session, force sign-in for it (step-up, or **Force Authentication** on that OIDC / SAML Federated App) |
| Single sign-on scope `Suppressed` | — | Every request asks for credentials | **Force Authentication** on that OIDC / SAML Federated App (Descope's equivalent of `prompt=login`) |

Refresh Token Rotation: turn it on if the B2C apps relied on rotating refresh tokens (B2C rotates
them by default). The docs don't say whether rotation extends the Refresh Token Timeout — treat the
timeout as the absolute cap.

**When policies differ:**
- By customer organization → tenant-level session settings (session / refresh token expiration,
  inactivity) on each tenant.
- By app → Inbound App custom token lifetimes (the app's session settings, or the **Update Inbound
  App** Flow action with **Custom**), or a per-app Flow with **Set Custom Refresh Duration**.
- By journey inside one app → the Flow for that journey sets **Set Custom Refresh Duration**.

Record the result in the plan as one row per policy: B2C values → Descope setting and level
(project / tenant / app / Flow).

Docs: [Session Management](https://docs.descope.com/management/project-settings#session-management),
[Custom Claims action](https://docs.descope.com/flows/actions/custom-claims).

#### Split-clock setups → step-up

B2C could keep users in the app for months (long refresh tokens)
but ask for a password again after an hour when they open a sensitive link (short sign-in cookie,
and the link sends them back to B2C). Descope can't split the session, so model the intent instead:
- Run a step-up Flow when the user performs a sensitive action. After it, the session carries
  `su: true` until **Step Up Token Timeout** (Project Settings → Session Management) — set that to
  B2C's sign-in cookie lifetime (for example 1 hour).
- The backend checks `su` on every sensitive endpoint and returns a challenge when it's missing;
  the frontend then runs the step-up Flow. B2C apps already sent users to B2C for those links, so
  this replaces that redirect — but it is an app code change: list each sensitive action in the
  code-change inventory.
- Docs: [Step-up authentication](https://docs.descope.com/mfa-and-step-up/step-up).

#### Cross-app SSO

Browsers never share cookies across root domains. B2C got cross-app SSO by
keeping its session on one central host that every app redirected to. Descope behaves the same way
only when sign-in happens on one central host:
- **Hosted login or federated apps** (Descope's domain, or one custom domain such as
  `auth.company.com`): the session lives on that host, so apps on different root domains
  (`company-sales.com`, `company-billing.com`) share it, as with B2C. The docs confirm this for
  federated apps (signed-in users are sent back without re-authenticating unless **Force
  Authentication** is on); verify it for hosted login through Inbound Apps.
- **Embedded Flows on each app's own domain:** the session cookie lives on each app's domain. Apps on
  subdomains of one root (`sales.company.com`, `billing.company.com`) can share it: set the cookie
  domain to the root, or keep the refresh cookie on `auth.company.com` and have each app refresh
  through it ([Sharing cookies across multiple subdomains](https://docs.descope.com/how-to-deploy-to-production/custom-domain#sharing-cookies-across-multiple-subdomains)). Apps on different root
  domains can't share it — a custom domain belongs to one root — so use hosted login for those apps.
- If B2C's scope was `Tenant` and apps sit on different root domains, Decision 0 should prefer
  hosted login for them.

### Audit and sign-in logs

B2C sends audit and sign-in logs to Azure Monitor (diagnostic settings → Log Analytics, Event Hubs
or Storage) and custom-policy journey traces to Application Insights. Descope streams audit events
through audit connectors — Datadog, Splunk, Sumo Logic, New Relic, AWS EventBridge or S3, and others —
or the Audit Webhook for any other target (for example an Azure Function that writes to Log
Analytics). Set it up before cutover so there's no gap, and rebuild alerts or dashboards built on
B2C log fields.

---

## Secrets, Certificates and Policy Keys

### Secrets can't be exported

Nothing secret can be read back from B2C, so plan for new or re-obtained credentials:

- Graph `openIdConnectIdentityProvider` / `socialIdentityProvider` `clientSecret`: *"write-only. A read operation returns `****`."*
- Graph `trustFrameworkKey`: `k`, `d`, `p`, `q`, `dp`, `dq`, `qi` — *"The field isn't readable."*
- Descope tenants accept an uploaded custom private key for SAML signing/decryption, as PEM. Convert
  a PFX with `openssl pkcs12 -in key.pfx -nocerts -nodes -out key.pem` (handle the output as a
  secret; delete it after upload).
- App registration `passwordCredentials` return `secretText: null` with only a short `hint`.

### Policy key inventory

Custom policies keep every secret and certificate in policy keys (keysets named `B2C_1A_…`).
None of the private values can be read, so each key in use is a credential someone has to
re-obtain or replace before cutover. Build the list in Step 1b:

1. Read the keysets: `GET https://graph.microsoft.com/beta/trustFramework/keySets`
   (`TrustFrameworkKeySet.Read.All`; delegated access also needs at least the B2C IEF Keyset
   Administrator role). Each key returns `kid`, `use` (`sig` / `enc`), `nbf` / `exp`, and the
   public certificate (`x5c`) — not the private part. Without Graph, ask for a portal screenshot of
   Identity Experience Framework → Policy keys.
2. Find which keysets are actually used: every `<CryptographicKeys><Key Id="…"
   StorageReferenceId="B2C_1A_…"/>` in the policy XML. The technical profile around it says what
   the key is for. Keysets that no policy references are not migrated.
3. Check `exp`. A key that expires before cutover must be rotated in B2C, or B2C breaks during a
   phased rollout.

| `Key Id` in the technical profile | Used for | Descope action |
|---|---|---|
| `issuer_secret`, `issuer_refresh_token_key` (JWT issuer — `TokenSigningKeyContainer`, `TokenEncryptionKeyContainer`) | Signing and encrypting B2C's own tokens | None. Descope signs its own tokens; APIs switch to Descope's keys (discovery / JWKS) |
| `client_secret` on a social IdP (Google, Facebook, Microsoft account) | Social login | Copy the secret from the provider's console (or create a new one) into Descope social login settings |
| Apple sign-in secret | Sign in with Apple | Descope needs Apple's Team ID, Key ID and the `.p8` private key from the Apple developer account — not the B2C client-secret JWT |
| `client_secret` on a customer OIDC IdP | Enterprise OIDC SSO | See Per-connection inventory: the customer IdP admin issues a new secret unless the original was kept outside B2C |
| `SamlMessageSigning`, `SamlAssertionDecryption` on a SAML IdP technical profile | B2C as the SAML service provider to a customer IdP (signed requests, encrypted assertions) | Upload the original private key (PEM) to the Descope tenant if the customer still has it; otherwise the customer IdP admin trusts Descope's certificate |
| `SamlMessageSigning`, `SamlAssertionSigning`, `MetadataSigning` on a `Saml2AssertionIssuer` | B2C as SAML IdP to the customer's own SAML apps | Upload the original certificate as a custom certificate on the Descope SAML Federated App if they still have it; otherwise each SAML app must trust Descope's certificate |
| `BasicAuthenticationUsername` / `BasicAuthenticationPassword`, `ClientCertificate`, `BearerAuthenticationToken`, or an API key header on a REST technical profile | Calling the customer's own APIs | Set the same credentials on the Flow HTTP Connector (the customer has the originals — they issued them) |
| Signing key for `id_token_hint` (invites, magic links) | Pre-filled or invite journeys started from the customer's own app | Replace with Descope invites / magic links; the customer's app stops minting these tokens |
| Anything else | Custom secrets used by claims transformations or REST calls | List it in the plan and ask the customer what issued it |

---

## User Migration

See [docs.descope.com/migrate/azure-ad-b2c](https://docs.descope.com/migrate/azure-ad-b2c).

### User schema

Build the Descope user schema from what B2C actually stores and uses — not only from the Graph
field list. Do this before any import: custom attributes must exist, with the right type, before
users are created.

**1. Inventory every attribute** — one row each:

| Attribute | Built-in or extension | Type | Collected at sign-up / profile edit? | Returned in the token? | Read by the app? | Per user or per organization? |
|---|---|---|---|---|---|---|

- Extension attributes and their types: Graph `extensionProperties` on the `b2c-extensions-app`
  (`name`, `dataType`).
- Which flows collect each attribute and which return it: user flow → User attributes and
  Application claims; custom policies → the `OutputClaims` of self-asserted and
  `AAD-UserWrite…` technical profiles (collected and stored) and of the relying party (returned).
- Claims a custom policy only computes or reads from a REST call, and never writes to the user,
  are not stored in B2C — there is nothing to export; rebuild them in the Flow if still needed.

**2. Map types** (create each custom attribute with the matching Descope type):

| B2C / Graph `dataType` | Descope custom attribute type |
|---|---|
| `String` | Text — or Single select if the values are a fixed list |
| `Boolean` | Boolean |
| `Integer`, `LargeInteger` (portal: Int) | Numeric |
| `DateTime` | Date |
| String used as a list (comma-separated, JSON array) | Multi select (split the values on import) |
| `Binary` | No equivalent — base64 into Text only if the app needs it |

**3. Map fields** with the single field-mapping table in Exporting users from B2C.

**4. Decide where each attribute lives:**
- Collected at sign-up or profile edit → an input on the Flow screen (or the User Profile Widget),
  saved with **Update User / Attributes**.
- Returned in B2C's token and read by the app → a JWT Template claim with the **same claim name** the
  app reads today.
- The same value for everyone in a customer organization (plan, region, contract tier) → a tenant
  custom attribute instead of a copy on every user.
- Not collected, not returned, not read → don't migrate it; list it in the plan as dropped.

Record the result in `MIGRATION-PLAN.md` under User Migration as the schema table.

### Exporting users from B2C

App registration with `User.Read.All` (application), client credentials token from
`https://login.microsoftonline.com/<b2c-tenant-id>/oauth2/v2.0/token` with
`scope=https://graph.microsoft.com/.default`, then:

```http
GET https://graph.microsoft.com/v1.0/users?$select=id,identities,accountEnabled,displayName,givenName,surname,mail,otherMails,mobilePhone,city,country,postalCode,state,streetAddress,jobTitle,ageGroup,consentProvidedForMinor,createdDateTime,extension_<appIdNoHyphens>_<attr>&$top=999
```

Follow `@odata.nextLink`; on `429`, honor `Retry-After` with backoff. Extension attributes must
be listed explicitly in `$select`.

`identities[]` per user (`signInType`, `issuer`, `issuerAssignedId`):
- `emailAddress` / `userName` → local account; `issuerAssignedId` is the sign-in name
- `phoneNumber` → local account that signs in with a phone number; `issuerAssignedId` is the number (E.164)
- `federated` → social or enterprise; `issuer` is the provider (e.g. `google.com`, the customer IdP), `issuerAssignedId` is the provider's user ID
- `userPrincipalName` → B2C's internal `<guid>@<tenant>.onmicrosoft.com` name, present on every user — **ignore it**; never use it as a login ID

A user can have several identities (for example email and a federated Google identity). Report
users with no `emailAddress`, `userName`, `phoneNumber` or `federated` identity instead of importing
them silently.

**Field mapping** (the only mapping table — User schema decides types and placement):

| B2C (Graph) | Descope |
|---|---|
| `identities[emailAddress, userName or phoneNumber].issuerAssignedId` | `loginId` (phone sign-in: the E.164 number, plus `phone` and `verifiedPhone: true`) |
| `id` | `customAttributes.b2cObjectId` (User ID strategy) |
| `displayName`, `givenName`, `surname` | `name`, `givenName`, `familyName` |
| `mail`, else the `emailAddress` identity | `email` (+ `verifiedEmail: true` for email sign-in accounts, which B2C verifies at sign-up — Graph has no per-user flag; confirm the policy verified emails) |
| `otherMails` | Usually drop, or keep in a Multi select custom attribute. Put one in `additionalIdentifiers` only if the user should sign in with it — those become extra login IDs |
| `mobilePhone`, or the SMS MFA number from `GET /users/{id}/authentication/phoneMethods` (`UserAuthenticationMethod.Read.All`) | `phone` (+ `verifiedPhone`) |
| `city`, `country`, `postalCode`, `state`, `streetAddress`, `jobTitle` | Custom attributes (Text, or Single select for country / state lists) — only those the app uses |
| `ageGroup`, `consentProvidedForMinor`, `legalAgeGroupClassification` | Custom attributes, plus a Flow condition if sign-in depends on them |
| `accountEnabled: false` | `status: "disabled"` |
| `createdDateTime` | `createdTime` (Unix seconds; not in the future) |
| `extension_<appIdNoHyphens>_<name>` | `customAttributes.<name>` (typed — User schema step 2) |
| — | `customAttributes.freshlyMigrated: true` |

Import with the batch create users Management API (`POST /v1/mgmt/user/create/batch`) or the
SDK equivalent (verify the method name via the Docs MCP).

### User ID strategy

Descope always generates its own user ID; the user import API has no field to set it. So B2C's
object ID can't become the Descope user ID — but the token can still carry it. Always import it
as the `b2cObjectId` custom attribute (the descriptive name is for the Descope user store; the
claim name is chosen separately).

**Migrated users vs. new users.** A user imported from B2C has a B2C object ID, so
`b2cObjectId` is set. A user who signs up after cutover never existed in B2C: they get only a
Descope user ID, and `b2cObjectId` is empty unless the sign-up Flow fills it. Every strategy below
must say what new users get.

| Strategy | What the token carries | Data change | New users | Watch out for |
|---|---|---|---|---|
| **Keep the B2C ID** (no app code change) | JWT Template emits `oid` from `b2cObjectId`. If the code keys on `sub` (B2C's default), also turn on **Override system claims** and set `sub` from `b2cObjectId`; Descope's ID moves to `dsub` | None | The sign-up Flow fills `b2cObjectId` with their Descope user ID (`U…`, not a GUID) — see Filling `b2cObjectId` for new users | See Overriding `sub` and App changes when keeping the B2C ID |
| **Switch to the Descope user ID** | `sub` = Descope user ID | One-time remap before cutover: after import, read each user's Descope ID and `b2cObjectId` (Management API search) and rewrite the keys | Nothing to do — they only have a Descope ID | Every system keyed on the B2C ID moves in the same window; rollback means reversing the remap |
| **Remap on first login** | `sub` = Descope user ID, plus `oid` from `b2cObjectId` | Gradual: on login, if no row matches `sub`, look up by `oid`, then store `sub` on that row | Nothing to do — no `oid`, matched by `sub` from the start | Users who never log in stay on the B2C ID; finish them later with the batch remap |

Systems outside the app that receive the B2C ID — SAML apps (B2C as a SAML IdP → Descope SAML app),
CRM, analytics, support tools — follow the same choice. List them in the plan.

#### Overriding `sub` (JWT Template → Override system claims)

By default Descope sets `sub` to its user ID and a JWT Template can't change it. Turn on
**Override system claims** on the JWT Template (`overrideSubject` in the Management API,
`override_subject_claim` in Terraform), then set the claims in advanced mode:

```json
{
  "oid": "{{user.customAttributes.b2cObjectId}}",
  "sub": "{{user.customAttributes.b2cObjectId}}"
}
```

Tokens then carry both IDs — Descope keeps its own in `dsub`:

```json
{
  "oid": "3f2a1c9e-7b4d-4e2a-9c1f-0a6b8d2e5f31",
  "sub": "3f2a1c9e-7b4d-4e2a-9c1f-0a6b8d2e5f31",
  "dsub": "U2RG6grrbT3REKYqk5yC4SjkMqzA"
}
```

Only override `sub` when the code keys on `sub`; if it reads `oid`, emit `oid` and leave `sub`
alone. Don't set `amr`, `act` or `iss` here, although the same toggle allows it. The override
applies to every app on that JWT Template, every token validator sees the new `sub`, and Management
API calls about a user must pass `dsub`. The docs don't say whether it reaches Inbound App access
tokens — test that before relying on it for a scoped API.
[Override System Claims](https://docs.descope.com/management/token/jwt-templates#override-system-claims).

#### Filling `b2cObjectId` for new users

Users who sign up after cutover never had a B2C ID. In the sign-up Flow, after the user is created
and only when `b2cObjectId` is empty: a Scriptlet with a dynamic argument `user.userId` returns it,
an override copies it to `form.customAttributes.b2cObjectId`, and **Update User / Attributes**
saves it. Their `oid` (and `sub`, if overridden) is then their Descope user ID.

#### App changes when keeping the B2C ID

No data moves: migrated users keep the same `oid` / `sub`, so existing rows and lookups keep
working, and rolling back to B2C during a phased rollout is safe. What the app team still changes:

- [ ] User ID columns typed as GUID / UUID (`uniqueidentifier`, `uuid`, `Guid` entity properties)
      become strings (e.g. `varchar(64)`) — new users' IDs look like `U2RG6grrbT3REKYqk5yC4SjkMqzA`
- [ ] GUID-only code accepts a string: `Guid.Parse` / `Guid.TryParse`, `UUID.fromString`,
      `{id:guid}` route constraints, GUID regexes, GUID-typed DTOs
- [ ] Every downstream system that receives the user ID (CRM, analytics, support tools, SAML apps,
      webhooks) gets the same check
- [ ] Calls to the Descope Management API about a user use Descope's ID — `dsub` with the `sub`
      override, `sub` without it
- [ ] The sign-up Flow fills `b2cObjectId` for new users, so `oid` / `sub` are never empty
- [ ] Tests cover one migrated user and one new user end to end

If the columns or downstream systems can't take a string before cutover, use **Remap on first
login** or **Switch to the Descope user ID** instead.

### Password strategy

B2C does not export password hashes.

| Option | How | Trade-off |
|---|---|---|
| Full import without passwords | First-login password reset step, or passwordless (OTP, magic link, passkeys) | Fastest B2C shutdown; every password user acts once |
| JIT via ROPC | Flow collects email + password → HTTP Connector to the B2C ROPC endpoint → on success create the user and set the password in Descope | Keeps passwords; B2C stays up until active users have signed in; local accounts only; no MFA in that call |
| JIT with B2C as an OIDC provider | B2C policy configured as a custom OAuth provider in Descope; users sign in through B2C once and are created from the ID token | No passwords kept; B2C stays up |
| Session migration | Existing B2C sessions exchanged for Descope sessions ([docs](https://docs.descope.com/migrate/session-migration)) | Session migration currently accepts Auth0 and Okta tokens — B2C needs Descope Support to confirm first. Default to re-login at cutover |

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

Descope looks up an SSO login by exact login ID, in this order (confirmed against the Descope
backend):
1. **Direct:**
   - SAML: `<NameID>-<tenantID>`.
   - OIDC: `<value of the claim mapped to Login ID>-<tenantID>` — the tenant's OIDC connection →
     User Attribute Mapping → Login ID. It is whatever claim that mapping selects (`oid`, `sub`,
     `email`, …), not inherently `sub` or `email`. The connection needs this mapping; `sub` is used
     only for an authentication-only connection whose mapping is empty.
   - The tenant suffix is never added twice (case-insensitive), so an imported login ID that already
     ends in `-<tenantID>` is matched as is.
2. **Fallback — only when "Convert existing users to SSO" (merge) is on, the default:**
   - SAML: plain NameID; then, where email fallback is enabled for the project, the plain mapped
     email and the email with the tenant suffix. Email fallback may not be on for every project —
     confirm with Descope before relying on it.
   - OIDC: the IdP email, only if the connection trusts provided emails.
3. **Otherwise:** a new SSO user is created — a duplicate of the imported one.

Recipe:
1. Create the tenant and its SSO connection **before** importing that customer's users.
2. Import each enterprise user into **exactly one** tenant (multi-tenant users need the "Allow converting users that belong to multiple tenants" setting — flag them for a manual decision; it carries cross-tenant takeover risk).
3. Set the login ID to what the direct lookup uses:
   - **SAML:** `<NameID>-<tenantID>`. B2C's `issuerAssignedId` for SAML users is usually the NameID (the starter pack maps `assertionSubjectName` → `issuerUserId`) — confirm in the policy XML.
   - **OIDC:** `<value>-<tenantID>`, where `<value>` is what B2C stored in `issuerAssignedId` for the user. B2C's Entra examples store the IdP's `oid` (not `sub`), so check the policy XML for which claim it kept. Then map **that same claim** to **Login ID** on the tenant's OIDC connection, so the claim Descope reads at sign-in equals what you imported. If B2C stored a value the IdP no longer sends, use the email fallback instead: import with email as the login ID and enable trusted emails on the connection.
4. Add the email as an additional login ID when it differs.
5. Check that each customer IdP actually sends the stored email (Entra often sends a UPN).

---

## Enterprise SSO Migration

### Cutover strategy

Follows [docs.descope.com/migrate/strategy](https://docs.descope.com/migrate/strategy). B2C is a
hosted provider whose apps sign in over OIDC (MSAL, OIDC middleware) or SAML, so Descope can act as
an **identity broker** in front of it while apps move one at a time.

**Direct, per app** — no enterprise IdP connections in B2C. Import users, move each app to Descope
(SDK swap, or a Federated App), test it, move the next. Retire B2C after the last app.

**Two-stage broker** — B2C holds customer IdP connections, or there are many apps:

*Cutover stage 1 — route every app through Descope.*
1. Set up a new Descope custom domain (e.g. `auth.<company>.com`). Leave B2C's hostname alone.
2. Add B2C to Descope as an OIDC connection (a B2C app registration for Descope, pointed at a B2C
   policy). The login Flow sends users who are not moved yet — enterprise SSO users in particular —
   to B2C, which signs them in through the customer's existing connection. Check that the Flow can
   pass the customer's `domain_hint` so B2C skips its own IdP picker. Everyone else signs in with
   Descope Flows directly. This is also the "JIT with B2C as an OIDC provider" password option.
3. Move apps one at a time to the new hostname: MSAL and server-side apps get the SDK / OIDC swap;
   SAML apps are reconnected once as Descope SAML Federated Apps (B2C as a SAML IdP → Descope SAML
   app). Test each app before the next.

*Cutover stage 2 — move the existing hostname.* When every app runs on Descope, point B2C's custom-domain
hostname at Descope through the SSO migration Worker
([docs.descope.com/migrate/sso](https://docs.descope.com/migrate/sso#setting-up-the-dns-redirect)) —
a CNAME alone breaks SSO because Descope doesn't serve B2C's paths. Customer IdPs keep posting to the
URLs they have, and SSO migration takes over each connection. Then stop federating to B2C and turn
it off.

Cutover stage 2 only works for connections on a hostname the customer owns. Connections configured on
`*.b2clogin.com` can't move this way — those customer admins update their connection, which they can
do themselves with the SSO Setup Suite. IdPs that validate the signature on SAML requests against
B2C's certificate also need their admin to update before Cutover stage 2 (Per-connection inventory).

### Per-connection inventory and cutover rules

Build one row per customer connection (template in `b2c-detection-patterns.md`). Descope's
[SSO migration](https://docs.descope.com/migrate/sso) keeps old ACS URLs working by pointing the
old login hostname at a Cloudflare Worker that forwards to Descope (`spEntityId` / `spACSUrl`
overrides on the tenant). That requires a hostname the customer controls:

| Condition | Result |
|---|---|
| URLs on `<tenant>.b2clogin.com` | Customer IdP admin updates ACS/redirect URLs — no DNS redirect possible |
| SAML on a custom domain, no signed-request/encrypted-assertion dependency | Can move without IdP changes (DNS redirect) |
| SAML that requires signed requests or encrypts assertions to B2C's certificate | If the company kept the original key, convert the PFX to a PEM private key (Descope's custom key upload expects PEM) and upload it to the Descope tenant; otherwise the admin trusts Descope's certificate |
| IdP that validates the signature on SAML requests against B2C's certificate (Keycloak is the common case) | Admin updates the connection before Cutover stage 2. Find these before any DNS change with the script in [Checking Which IdPs Validate Your SP Certificate](https://docs.descope.com/migrate/sso#checking-which-idps-validate-your-sp-certificate) |
| OIDC connection | Redirect can be kept on a custom domain, but the admin issues a new client secret unless the original was stored outside B2C |

Some connections may have been created before a custom domain was added — check the URL each
customer IdP is actually configured with. Affected admins get the notice drafted in the plan
(Enterprise SSO Cutover). Descope's SSO migration docs list
seamless SSO migration for Growth and Enterprise plans — confirm availability for the customer.

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
    issuer: import.meta.env.VITE_DESCOPE_INBOUND_ISSUER,   // see Finding the Inbound App issuer
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
| `instance.loginRedirect(loginRequest)` | `useDescope().oidc.loginWithRedirect({ resource: '<Resource>', extraTokenParams: { resource: '<Resource>' } })` |
| `useIsAuthenticated()` | `useSession().isAuthenticated` (+ `isSessionLoading`) |
| `useMsal().accounts[0]` / `idTokenClaims` | `useUser().user` |
| `acquireTokenSilent({ scopes })` → `accessToken` | `useSession().sessionToken` — with `oidcConfig` this is the Inbound App access token; the SDK refreshes it |
| `AuthenticatedTemplate` / `UnauthenticatedTemplate` | Conditional render on `isAuthenticated` |
| `MsalAuthenticationTemplate` | Guard component that calls `loginWithRedirect({ resource, extraTokenParams: { resource } })` |
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
| `MsalService.loginRedirect()` | `descopeAuthService.descopeSdk.oidc.loginWithRedirect({ resource: '<Resource>', extraTokenParams: { resource: '<Resource>' } })` |
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

// login button — `resource` selects the Resource (sets the token's aud)
sdk.oidc.loginWithRedirect({
  resource: 'https://api.example.com',                         // authorize request
  extraTokenParams: { resource: 'https://api.example.com' },   // token request
});

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
        o.Resource = builder.Configuration["Descope:Resource"];   // RFC 8707 resource on /authorize
        o.SaveTokens = true;
        o.MapInboundClaims = false;                               // keep claim names as issued
        // Send the same resource on the code exchange — Descope expects it on both requests
        o.Events.OnAuthorizationCodeReceived = ctx =>
        {
            ctx.TokenEndpointRequest!.Resource = builder.Configuration["Descope:Resource"];
            return Task.CompletedTask;
        };
    });
```

Remove `AddMicrosoftIdentityUI`, `MicrosoftIdentity/Account/*` routes, policy-specific
challenge code (`EditProfile`, `ResetPassword`), and `AzureAdB2C` config.

**Node.js (`msal-node` `ConfidentialClientApplication` or `passport-azure-ad` `OIDCStrategy`):**
replace with `openid-client` (discovery from the Descope issuer, same callback route; add
`resource` to the authorization request when the API is a Descope Resource).

**Python (`msal` `ConfidentialClientApplication`, Flask/Django):** replace with Authlib or
another OIDC client using the Descope issuer.

**Java (Spring Security `oauth2Login` with a B2C registration):** change the client registration
`issuer-uri`, `client-id`, `client-secret`, and scopes to the Descope app.

### Native / mobile

MSAL iOS/Android with B2C authorities, or ROPC → Descope Swift / Kotlin / Flutter / React Native
SDKs with native Flows (or hosted login through the system browser). Moving off ROPC adds MFA and
passkeys. Update redirect URIs / deep links.
