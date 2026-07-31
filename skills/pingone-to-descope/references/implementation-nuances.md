# PingOne CIAM Implementation Nuances

## Contents

- [Path Selection](#path-selection)
- [Federated App / Protocol-Config Migration](#federated-app--protocol-config-migration)
- [Web Client and Mobile SDK Flow Migration](#web-client-and-mobile-sdk-flow-migration)
- [Token Validation](#token-validation)
- [Hierarchy and Object Mapping](#hierarchy-and-object-mapping)
- [Claim Mapping](#claim-mapping)
- [Worker Apps and Service Automation](#worker-apps-and-service-automation)
- [PingOne Protect Replacement](#pingone-protect-replacement)
- [User Migration and Password Cutover](#user-migration-and-password-cutover)
- [Framework Notes](#framework-notes)
- [Console-First Decisions](#console-first-decisions)
- [Testing Notes](#testing-notes)

## Path Selection

Choose a path from evidence, not from provider preference.

| Path | Use when | Main work | Risk |
|---|---|---|---|
| Path A: Federated App / protocol-config migration | App uses generic OIDC/OAuth/SAML libraries and no Ping SDK in that client | Configure Descope OIDC or SAML Federated App; repoint issuer/metadata/JWKS/SAML metadata/client config to Descope; update claims | Do not use this to keep Ping mobile/OIDC SDK code and point it at Descope. |
| Path B: Descope web Client SDK or Mobile SDK + Flow migration | Web/mobile app imports Ping Orchestration/OIDC SDKs or DaVinci SDK/widget code, renders custom auth UI, or directly handles auth calls | Use Descope web Client SDK/web component for web, or Descope Mobile SDK for Swift/Kotlin/Flutter/React Native; embed or invoke Flow; validate sessions where backend validation exists | Ping SDKs must be replaced; do not invent Python/Go/Node/Java/.NET Ping SDK swaps. |
| Path C: Journey/config migration | PingOne authentication policies or DaVinci flows define most behavior | Recreate journeys in Descope Flows + Connectors | Repo may not contain the important logic; request PingOne/DaVinci exports. |
| Mixed | Multiple apps/services use different integration styles | Execute per surface | Requires careful cutover sequencing and token validation updates across services. |

Descope Client SDKs are web SDKs: Web JS, React, Vue, Angular, and Next.js. Descope Mobile SDKs are
Swift/iOS, Kotlin/Android, Flutter, and React Native. Ping Orchestration/OIDC SDK findings in Swift,
Kotlin, or React Native should map to Descope Mobile SDK work, not "client SDK" work.

Reference the current Descope SDK terminology before writing SDK guidance:

- `https://docs.descope.com/client-sdk`
- `https://docs.descope.com/mobile-sdk`

Ping Orchestration SDKs are client-side/mobile SDKs for Kotlin/Android, Swift/iOS,
JavaScript/TypeScript, and React Native TypeScript. Backend Python, Go, Node server, Java, and .NET
code may still contain PingOne OIDC/SAML config, token validation, claims, REST/API calls, cookies,
or authorization logic, but it should not be treated as Ping orchestration SDK usage.

Prioritize Swift/iOS and Kotlin/Android SDK evidence when it exists. These native SDKs are often
the most important Ping client footprint in CIAM migrations, especially when PingOne Protect or
device profiling collects risk context from mobile devices.

## Federated App / Protocol-Config Migration

Path A is valid when the app already uses generic OIDC/OAuth or SAML middleware and PingOne is only
the configured identity provider. It is not valid for a Swift/Kotlin/React Native app that imports
Ping OIDC or Orchestration SDKs; migrate those SDKs instead.

Inventory:

- Issuer / authority / discovery URL
- SAML metadata URL, SSO URL, ACS URL, entity ID, certificate, and NameID requirements, if SAML
- Client ID and secret
- Redirect URI and post-logout redirect URI
- Scopes
- JWKS URI or discovery metadata
- Audience validation
- Claim names the app reads
- Session cookie strategy owned by the app/framework

Typical changes:

- For PingOne OIDC Web applications, create/configure a Descope OIDC Federated Application.
- For PingOne SAML applications, create/configure a Descope SAML Federated Application.
- Replace PingOne issuer/authority/discovery with Descope's OIDC Federated App issuer/discovery.
- Replace PingOne SAML metadata/certificate/SSO URL with Descope's SAML Federated App metadata.
- Replace PingOne client credentials with Descope OIDC Federated App values when required by the framework.
- Update allowed redirect, ACS, and logout URLs in Descope Console.
- Update JWKS/discovery references or SAML certificate/assertion validation.
- Update claim expectations and tests.

Do not recommend Path A if the app depends on Ping Orchestration/OIDC SDK session helpers, DaVinci
interaction state, or PingOne APIs during login. In those cases, Path A may still be a temporary
downstream API validation strategy, but the app integration needs Path B and the auth journey may
also need Path C.

## Web Client and Mobile SDK Flow Migration

Path B is for apps that need Descope-native web or mobile integration. Use it for Ping SDKs,
DaVinci widgets/SDKs, embedded auth UI, or direct auth API calls. Do not use it only because a
backend service validates PingOne tokens.

Target the correct Descope SDK family:

- Web apps: Descope web Client SDKs or web components.
- Mobile apps: Descope Mobile SDKs for Swift/iOS, Kotlin/Android, Flutter, or React Native.
- Ping mobile/OIDC SDK imports: replace the SDK. Do not keep Ping SDK and swap discovery endpoint,
  issuer, client ID, or redirect URI to Descope.

Native mobile checkpoint:

- Swift/iOS: look for `PingOrchestrate`, `PingOidc`, `PingProtect`, `PingOneProtect`,
  `PingBrowser`, `PingLogger`, `OidcWebClient`, `createOidcWebClient`, `authorize`,
  `discoveryEndpoint`, `browserMode`, `browserType`, and `acrValues`.
- Kotlin/Android: look for Ping Android SDK or DaVinci client Gradle dependencies, `PingProtect`,
  `com.pingidentity.oidc.OidcWeb`, `com.pingidentity.oidc.module.Oidc`, `Logger.STANDARD`,
  `OidcWeb`, `module(Oidc)`, `web.authorize`, `viewModelScope.launch`, `MutableStateFlow`,
  `onSuccess`, `onFailure`, `orchestrate`, `oidc`, `protect`, device ID, device profiling,
  `Journey`, `Node`, `ContinueNode`, `SuccessNode`, and `FailureNode`.
- If these apps collect Protect/device context, preserve the risk-signal purpose in Descope Flows,
  fingerprinting, and Fraud & Risk Connectors instead of treating the code as generic login UI.

Web/mobile responsibilities:

- Render or invoke Descope Flow with the correct web Client SDK, web component, or Mobile SDK.
- Use only public Project ID in browser code.
- Handle success/error redirects.
- Read UI auth state through Descope web/mobile SDK helpers rather than decoding JWTs in UI code.
- Trigger logout through the web Client SDK or Mobile SDK when appropriate.

Backend responsibilities:

- Validate session JWTs on protected routes and APIs.
- Read server-side claims after validation.
- Enforce roles/permissions/tenant access in middleware or application logic.
- Use Management API only for admin operations such as user CRUD, tenant setup, roles, SSO, SCIM, or imports.
- Treat Python, Go, Node server, Java, and .NET work as protocol config, session/token validation,
  claims, REST/API calls, or Management API automation unless direct client orchestration code is
  present elsewhere.

Console/Flow responsibilities:

- Auth methods and login/signup UX
- MFA / step-up
- Password reset and account recovery
- Social login providers
- Risk/adaptive decisions
- Identity verification steps
- Custom claims/JWT Templates
- SSO Setup Suite and tenant SSO
- Widgets for profile/user/tenant/admin experiences

## Token Validation

Every service that validates PingOne tokens must be updated. Search beyond the login app: APIs,
workers, gateways, GraphQL servers, background services, and tests may validate issuer, audience,
JWKS, scopes, groups, or entitlements.

Validation checklist:

- Confirm token source: cookie, `Authorization` header, framework session, or API gateway.
- Replace PingOne issuer/JWKS with Descope validation.
- Preserve audience validation if the app uses it today; configure the corresponding Descope JWT
  claim/template first.
- Update tests and fixtures that hard-code PingOne `iss`, `aud`, `kid`, claim names, or groups.
- Do not hand-parse JWTs on the client to drive auth state; use SDK helpers.

Active PingOne sessions do not automatically survive cutover. Plan for forced re-login unless the
team designs and tests an explicit bridging strategy.

## Hierarchy and Object Mapping

Use the PingOne hierarchy as a starting model, then classify each object by behavior:

| PingOne object | Descope object | Implementation note |
|---|---|---|
| Environment | Project | Separate dev/staging/prod environments usually become separate projects. |
| Application | Federated App, SDK/Flow integration, or service automation pattern | Map by PingOne application type, not by repo name. |
| Population | Tenant when it is a customer organization, realm, or isolated community | If it is a segment, policy bucket, region, product line, or lifecycle bucket, use attributes, Flow branches, project strategy, or app logic instead. |
| Population-level access group | Tenant-level role | Use when the population maps to a tenant and the group grants access inside that tenant. |
| Environment-level access group | Project-level role | Use for global/cross-population authorization. |
| Segmentation group | Custom attribute | Use for filtering, reporting, personalization, cohorts, or non-authz Flow conditions. |
| Dynamic group | Source attributes plus ABAC, Flow condition, FGA, or app logic | Recreate the membership rule; do not import only a static member snapshot. |
| External directory group | SSO/SCIM group-to-role mapping | Keep the external IdP, LDAP, or provisioning system authoritative. |
| Nested group | Flattened effective roles/permissions, or FGA if hierarchy matters | Preserve effective access. |
| Unused group | No Descope object | Drop only after dependency analysis. |

PingOne users belong to exactly one population. Descope users can belong to multiple tenants, but a
migration should assign each user only to the tenant created from the original population unless the
app already supports multi-organization membership.

## Claim Mapping

PingOne claims vary by application, policy, resource, and custom claim configuration. Do not assume
profile or authorization claims appear in Descope tokens by default.

Common claim review:

| PingOne claim/source | Descope target | Notes |
|---|---|---|
| `sub` / PingOne user ID | Descope user ID or mapped external ID/custom attribute | Decide whether app needs stable old ID preserved. |
| `email`, `email_verified` | JWT Template and user profile | Add claims explicitly if code reads them from tokens. |
| `given_name`, `family_name`, `name` | JWT Template / user profile | Keep display code stable or update adapters. |
| `username` | Login ID or custom attribute | PingOne username may not equal email. |
| `populationId` / population claim | Tenant ID, custom attribute, Flow branch, or project strategy | Map to tenant only when the population is a customer organization/realm/isolated community. |
| `groups` | Tenant roles, project roles, custom attributes, SSO/SCIM mappings, FGA, JWT Templates, or app-side logic | Classify access vs. segmentation vs. dynamic/external membership before recreating claims. |
| `roles` | Descope RBAC roles / JWT roles | Roles must exist in Descope before assignment. |
| `permissions` / `entitlements` | Descope permissions, FGA, JWT Templates, or app-side authz | Entitlements may require model review. |
| Custom claims | JWT Templates or Flow custom claims | Recreate only claims the app reads. |
| `amr` / MFA method claims | Descope auth method claims / step-up signal | Verify exact Descope claim shape through MCP. |

JWT Template guidance:

- Add profile claims (`email`, `name`, picture, locale) only if the app reads them from the token.
- Add legacy identifiers if the app needs to map old PingOne users during migration.
- Avoid carrying every PingOne claim forward without a consumer.
- Document every claim in `MIGRATION-PLAN.md` with its reader and purpose.

## Worker Apps and Service Automation

PingOne Worker apps are primarily service/admin API clients. Treat them separately from customer
sign-in applications. They usually use client credentials and administrator role assignments to call
PingOne platform APIs, and they are not a login Flow or Federated App migration target.

Map Worker app usage by intent:

| PingOne Worker app use | Descope target | Notes |
|---|---|---|
| Manage Descope resources after migration: users, tenants, roles, SSO/SCIM, FGA, imports | Descope Management API with `DESCOPE_MANAGEMENT_KEY` | Management Key is an admin secret. Keep it server-side only. |
| Authenticate a machine/service to your own app APIs | Descope Access Keys / M2M | Access Keys are not the same as Management Keys; use them for service auth to your own systems. |
| Temporary PingOne export/migration script | PingOne Worker credentials for source reads + Descope Management API for target writes | Remove or rotate PingOne Worker credentials after cutover. |
| PingOne Authorize automation | Descope RBAC/FGA Management API or app-side authorization review | Requires authorization model review. |

Before writing code, inventory Worker app roles, scopes, APIs called, secret storage, and whether
the service must persist after cutover.

## PingOne Protect Replacement

Treat PingOne Protect as risk-decision behavior inside the customer auth journey. Do not replace it
with a vague "risk integration"; preserve what the current journey does for each signal: allow,
reduce friction, challenge, block, notify, score, or log.

Use Descope built-in fingerprinting first when it covers the behavior:

| Current Protect behavior | Descope Flow replacement |
|---|---|
| Bot-like sign-up or sign-in | Branch on `riskInfo.botDetected`; optionally add Bot Trap or a CAPTCHA connector. |
| Impossible travel | Branch on `riskInfo.impossibleTravel`; require step-up, notify, or block. |
| High/medium/low risk score | Branch on `riskInfo.riskScore`; tune thresholds with the security/product owner. |
| Trusted or unrecognized device | Branch on `riskInfo.trustedDevice`; skip MFA for trusted devices or require step-up for untrusted devices. |

Mobile Protect/device collection checkpoint:

- iOS Swift and Android Kotlin SDK code may be the source of the device, behavioral, browser/session,
  or risk payload that PingOne Protect evaluates.
- Record where native code collects device info, device ID, signals, or risk payloads, and whether
  the app passes them into DaVinci/auth journeys.
- Replace the decision path with Descope fingerprinting `riskInfo`, Fraud & Risk Connectors, Flow
  conditions, and any required mobile app changes.

Add Fraud & Risk Connectors when the PingOne Protect policy depends on provider-specific signals:

- CAPTCHA and bot defense: reCAPTCHA Enterprise, reCAPTCHA v3, Turnstile, hCaptcha, Arkose Labs.
- Device/browser intelligence: Fingerprint or another supported device intelligence connector.
- IP reputation and threat intelligence: AbuseIPDB, Bitsight, Traceable, or equivalent.
- Phone, identity, or account risk: Telesign, Reassigned, Alloy, Elephant, or equivalent.
- Fraud or behavioral risk scoring: Forter, Sardine, Darwinium, or an external provider through a
  connector or Generic HTTP Connector.
- Breach/password/email reputation: Pwned or equivalent.

Fraud connector steps belong inside Descope Flows. They collect user/device/session context, call the
third-party provider, expose the result for conditional Flow logic, and then the Flow decides whether
to continue, step up, block, or notify. Many fraud/fingerprinting providers require a separate
subscription; confirm licensing before production.

Relevant Descope docs:

- `https://docs.descope.com/fingerprinting`
- `https://docs.descope.com/connectors/connector-configuration-guides/fraud`

## User Migration and Password Cutover

PingOne does not support exporting passwords or password hashes. Do not plan a hash import or
password-preservation migration.

Existing users have two Descope Flow-based options:

1. **Require password reset on first login.** Configure a Descope Flow to prompt migrated users to
   reset their password the first time they sign in through Descope. After resetting, users
   authenticate with their newly set Descope password for future logins.
2. **Move to passwordless authentication.** Configure a Descope Flow to use passwordless methods
   such as OTP, magic link, passkeys/WebAuthn, social login, or other confirmed passwordless methods.

Decide before cutover and exercise the selected Flow path in dev/staging dry runs before production.

## Framework Notes

### Swift / iOS

- Treat Swift Ping SDK imports as high-signal Path B evidence, especially in customer login,
  PingOne Protect, or device-context flows.
- Inventory `PingOrchestrate`, `PingOidc`, `PingProtect`/`PingOneProtect`, `PingBrowser`,
  `PingLogger`, `OidcWebClient`, `createOidcWebClient`, `authorize`, `discoveryEndpoint`,
  `browserMode`, `browserType`, and `acrValues`.
- For Swift apps using Ping OIDC/Orchestration SDKs, replace Ping SDK with the Descope Swift Mobile
  SDK. Do not keep `PingOidc`, `OidcWebClient`, or Ping discovery/client configuration and point it
  at Descope.
- For Protect/device collection, preserve the risk context and decision path with Descope
  fingerprinting, Fraud & Risk Connectors, and Flow conditions.

### Kotlin / Android

- Treat Kotlin/Android Ping SDK imports and Gradle dependencies as high-signal Path B evidence,
  especially in customer login, PingOne Protect, device ID, or device profiling flows.
- Inventory Ping Android SDK or DaVinci client dependencies, `com.pingidentity.oidc.OidcWeb`,
  `com.pingidentity.oidc.module.Oidc`, `com.pingidentity.logger.Logger`, `Logger.STANDARD`,
  `OidcWeb`, `module(Oidc)`, OIDC `clientId`, `discoveryEndpoint`, `scopes`, `redirectUri`,
  `web.authorize`, `viewModelScope.launch`, `MutableStateFlow`, `onSuccess`, `onFailure`,
  `PingProtect`, `orchestrate`, `oidc`, `protect`, device ID, device profiling, `Journey`, `Node`,
  `ContinueNode`, `SuccessNode`, and `FailureNode`.
- For sample-shaped code using `OidcWeb { module(Oidc) { ... } }`, classify it as mobile OIDC
  login first, then separately check whether Protect/device profiling modules are present.
- For Android apps using Ping OIDC/Orchestration SDKs, replace Ping SDK with the Descope Kotlin
  Mobile SDK. Do not keep `OidcWeb`, `module(Oidc)`, or Ping discovery/client configuration and
  point it at Descope.
- For Protect/device collection, preserve the risk context and decision path with Descope
  fingerprinting, Fraud & Risk Connectors, and Flow conditions.

### Next.js / React

- Use `NEXT_PUBLIC_DESCOPE_PROJECT_ID` only for client-side providers/components.
- Keep Management Key server-only.
- Server-side session validation belongs in server components, route handlers, middleware, API
  routes, or backend services.
- Client components should use Descope hooks/components for user/session state.
- Check the Next.js version before writing cookie/header helpers; async behavior differs by version.
- Generic Auth.js/NextAuth OIDC provider configs may use Path A before a web Client SDK/Flow migration.

### Express / Node APIs

- If the app currently validates PingOne JWTs with `jwks-rsa`, `jose`, or framework middleware,
  update issuer/JWKS/audience/claims.
- Ping does not provide a Node server orchestration SDK to replace. Treat Node API work as token
  validation, cookies, claims, REST/API calls, or Management API automation.
- If using Descope SDK validation, verify the exact `validateSession` API with MCP.
- Parse cookies explicitly if session tokens are cookie-based.
- Preserve public/protected route semantics from existing middleware.

### Python / Flask / FastAPI / Django

- Generic OIDC libraries can often use Path A.
- Custom JWT validators must update issuer/JWKS/audience checks.
- Ping does not provide a Python orchestration SDK to replace. Do not add Descope Python SDK as a
  direct Ping replacement; use it only if the migration explicitly needs Descope session validation
  or Management API work, and verify method names before code generation.
- Django middleware/auth backends may need claim-to-user adapter updates.

### Go

- Generic `go-oidc` integrations often fit Path A.
- Update issuer provider, OAuth2 config, JWKS verifier, expected audience, and claim structs.
- Ping does not provide a Go orchestration SDK to replace. Do not add Descope Go SDK as a direct
  Ping replacement; use it only if the migration explicitly needs Descope session validation or
  Management API work, and verify method names before code generation.

### Java / Spring

- Spring Security OAuth2 Resource Server or OIDC Login configs may use Path A.
- Update `issuer-uri`, `jwk-set-uri`, client registration, scopes, and claim mappers.
- If roles are mapped from claims, update authorities conversion.
- Ping does not provide a Java orchestration SDK to replace. Treat Java work as OIDC/resource server
  config, claims, authority mapping, or Descope validation/Management API only if needed.

### .NET

- ASP.NET OpenIdConnect and JwtBearer configs may use Path A.
- Update `Authority`, `Audience`, metadata address, callback paths, and claim mappings.
- Ping does not provide a .NET orchestration SDK to replace. Treat .NET work as protocol config,
  token validation, claims, cookies, or Descope Management API only if needed.
- Keep Management Key out of client/browser code.

## Console-First Decisions

Before writing custom code, ask whether the feature should be handled in Console/Flows:

| Need | Prefer |
|---|---|
| Login/sign-up UI | Descope Flow |
| Passwordless, magic link, OTP | Auth method config + Flow |
| MFA enrollment/challenge | Flow step, subflow, or step-up Flow |
| Risk/adaptive auth | Descope fingerprinting `riskInfo` signals + Fraud & Risk Connectors + Flow conditions |
| Identity verification | Flow step + external provider connector if needed |
| Social login | Social provider config + Flow |
| Customer SSO setup | Tenant SSO / SSO Setup Suite |
| Customer provisioning | Tenant SCIM/provisioning |
| User profile management | User Profile Widget |
| Tenant admin user management | User Management Widget / Role Management Widget |
| Custom token fields | JWT Templates / Flow custom claims |

The clean migration is often less code than the PingOne implementation because journey behavior moves
into Descope Flows.

## Testing Notes

Compile/static checks first:

- TypeScript: `npx tsc --noEmit`
- Python: project test command plus import check
- Go: `go test ./...`
- Java: `mvn test` or Gradle equivalent
- .NET: `dotnet test`

Auth smoke tests:

- Unauthenticated protected route returns 302/401, not 500.
- Login page renders Descope component or OIDC redirect starts.
- Successful login creates a Descope session.
- API validates Descope token and rejects missing/invalid tokens.
- Expected claims appear only after JWT Template configuration.
- Logout clears local session and invalidates refresh token if applicable.
- User profile displays expected fields.
- MFA/step-up triggers in the expected branch.
- Social login provider works in dev/staging.
- Customer SSO routes to the right tenant/IdP.
- SCIM/provisioning updates users after cutover.
- Webhook/event handlers receive and validate Descope events.

Production cutover notes:

- Run user import dry run in dev/staging first.
- Confirm the password cutover decision - see [User Migration and Password Cutover](./implementation-nuances.md#user-migration-and-password-cutover).
- Tell stakeholders whether users will need to log in again.
- Ensure all services validating PingOne tokens switch together or accept both issuers during a
  tested transition window.
- Keep PingOne rollback credentials/config available until production verification is complete.
