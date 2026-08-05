# PingOne CIAM Detection Patterns

## Contents

- [Search Groups](#search-groups)
- [PingOne Read-Only API Discovery Routes](#pingone-read-only-api-discovery-routes)
- [Package and Import Hints](#package-and-import-hints)
- [Environment Variable Hints](#environment-variable-hints)
- [Worker App Hints](#worker-app-hints)
- [Hierarchy and Group Hints](#hierarchy-and-group-hints)
- [OIDC and SAML Hints](#oidc-and-saml-hints)
- [DaVinci Hints](#davinci-hints)
- [Out-of-Scope Detection](#out-of-scope-detection)
- [Evidence Recording Template](#evidence-recording-template)

## Search Groups

Prefer `rg` when available. Keep grep forms available for portability.

```bash
# Ping orchestration SDK / DaVinci / ForgeRock-related imports
# Ping orchestration SDKs are client-side/mobile only: Kotlin, Swift, JavaScript/TypeScript, and React Native TypeScript.
grep -rni "pingone\|pingidentity\|davinci\|forgerock\|orchestration" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.kt" --include="*.kts" --include="*.swift" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
  . 2>/dev/null

# Swift/iOS Ping OIDC, orchestration, browser, and Protect patterns
grep -rni "import PingOrchestrate\|import PingOidc\|import PingProtect\|import PingOneProtect\|import PingLogger\|import PingBrowser\|OidcWebClient\|createOidcWebClient\|authorize\|discoveryEndpoint\|browserMode\|browserType\|acrValues" \
  --include="*.swift" \
  . 2>/dev/null

# Kotlin/Android Ping OIDC, orchestration, and Protect patterns
grep -rni "com.pingidentity.oidc.OidcWeb\|com.pingidentity.oidc.module.Oidc\|com.pingidentity.logger.Logger\|Logger.STANDARD\|OidcWeb\|module(Oidc)\|clientId\|discoveryEndpoint\|redirectUri\|scopes\|web.authorize\|onSuccess\|onFailure\|viewModelScope.launch\|MutableStateFlow\|PingProtect\|ping-android-sdk\|davinci-client\|orchestrate\|Oidc\|OIDC\|protect\|device.*profil\|Journey\|Node\|ContinueNode\|SuccessNode\|FailureNode" \
  --include="*.kt" --include="*.kts" --include="*.gradle" --include="*.gradle.kts" \
  . 2>/dev/null

# PingOne REST/API/protocol usage across app and backend code
# Use this to find Python/Go/Node/Java/.NET PingOne code; do not classify these as Ping SDK usage.
grep -rni "pingone\|auth.pingone.com\|api.pingone.com\|/as/authorize\|/as/token\|/userinfo\|/as/jwks" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.java" --include="*.cs" \
  --include="*.kt" --include="*.kts" --include="*.swift" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
  . 2>/dev/null

# PingOne env vars and config
grep -rni "PINGONE_\|PING_ONE_\|PING_CLIENT\|PING_ENVIRONMENT\|PING_REGION\|PING_ISSUER\|PING_AUTH" \
  --include="*.env*" --include="*.ts" --include="*.tsx" --include="*.js" \
  --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  . 2>/dev/null

# OIDC / OAuth config
grep -rni "issuer\|client_id\|clientId\|clientSecret\|redirect_uri\|redirectUri\|openid-configuration\|jwks_uri\|authorization_endpoint\|token_endpoint" \
  . 2>/dev/null

# PingOne URLs
grep -rni "auth.pingone.com\|api.pingone.com\|pingone.com" \
  . 2>/dev/null

# DaVinci / flow usage
grep -rni "davinci\|flowId\|flow_id\|interactionId\|collector\|node" \
  . 2>/dev/null

# User model / population / profile fields
grep -rni "population\|populationId\|userId\|username\|emailVerified\|verifyEmail\|profile\|customAttributes\|locale\|preferredLanguage" \
  . 2>/dev/null

# MFA / risk / verification / fraud connector evidence
grep -rni "mfa\|otp\|webauthn\|passkey\|risk\|riskInfo\|protect\|verify\|verification\|device\|bot\|fingerprint\|fraud\|captcha\|recaptcha\|turnstile\|hcaptcha" \
  . 2>/dev/null

# Claims / roles / authorization
grep -rni "scope\|claims\|groups\|groupId\|group_id\|roles\|permissions\|entitlements\|authorize\|policy\|dynamic.*group\|nested.*group\|memberOf\|membership" \
  . 2>/dev/null

# Webhooks / events
grep -rni "webhook\|event\|notification\|audit\|user.created\|user.updated\|user.deleted" \
  . 2>/dev/null
```

## PingOne Read-Only API Discovery Routes

Use these route skeletons only when the user opts into PingOne API discovery after the Descope MCP
check. Confirm `apiPath`, `envID`, credentials, region, and permissions from the user's PingOne
tenant. After any required OAuth token acquisition, use only read-only `GET` calls; do not create,
update, delete, disable, import, or rotate anything in PingOne during discovery.

All routes in this section use Authorization type `Bearer {{accessToken}}`.

Primary discovery routes:

| Source object | Read-only route | Use in the migration plan for |
|---|---|---|
| All environments | `GET {{apiPath}}/v1/environments` | Project/environment inventory and multi-environment strategy. |
| One environment | `GET {{apiPath}}/v1/environments/{{envID}}` | Confirm environment name, region, and IDs used by issuers/apps. |
| All populations in an environment | `GET {{apiPath}}/v1/environments/{{envID}}/populations` | Population names, IDs, descriptions, default marker, and user counts for tenant/attribute/Flow-branch classification. |
| One population | `GET {{apiPath}}/v1/environments/{{envID}}/populations/{{populationID}}` | Validate a specific population before mapping it to tenant, attribute, Flow branch, project strategy, or no object. |
| Population default identity provider | `GET {{apiPath}}/v1/environments/{{envID}}/populations/{{popID}}/defaultIdentityProvider` | Identify population-specific login/IdP behavior that may affect Flow routing, social login, or tenant SSO. |
| Built-in roles | `GET {{apiPath}}/v1/roles` | Understand PingOne built-in roles and permissions; use as source evidence only when they affect customer-facing admin or app authorization. |
| One built-in role | `GET {{apiPath}}/v1/roles/{{roleID}}` | Inspect one built-in role. This does not return custom-role details. |
| Custom roles for an environment | `GET {{apiPath}}/v1/environments/{{envID}}/roles?filter=%28type+eq+%22CUSTOM%22%29` | Custom role names and permissions for RBAC/FGA/app-side authorization mapping. |
| One custom role | `GET {{apiPath}}/v1/environments/{{envID}}/roles/{{roleID}}` | Inspect one custom role name, description, ID, and permission list. |
| All groups in an environment | `GET {{apiPath}}/v1/environments/{{envID}}/groups` | Group inventory, environment-level vs population-level scope, internal/external source, static/dynamic behavior, and rough role/attribute mapping. |
| One group | `GET {{apiPath}}/v1/environments/{{envID}}/groups/{{groupID}}` | Inspect one group; add `?include=totalMemberCounts` when member counts are needed for mapping confidence. |
| Parent groups for a group | `GET {{apiPath}}/v1/environments/{{envID}}/groups/{{groupID}}/memberOfGroups` | Detect nested/effective group hierarchy before flattening roles or recommending FGA/ReBAC. |

Secondary optional discovery routes:

| Source object | Read-only route | Use in the migration plan for |
|---|---|---|
| All applications | `GET {{apiPath}}/v1/environments/{{envID}}/applications` | Application inventory, type, protocol, client IDs, and multi-app migration path. |
| One application | `GET {{apiPath}}/v1/environments/{{envID}}/applications/{{appID}}` | Confirm app type, redirect/ACS/logout config, grants, policy assignments, and protocol shape. |
| Application grants | `GET {{apiPath}}/v1/environments/{{envID}}/applications/{{appID}}/grants` | OAuth grant/resource/scope relationships and service/admin app behavior. |
| Application attributes | `GET {{apiPath}}/v1/environments/{{envID}}/applications/{{appID}}/attributes` | Claims/SAML attribute mappings that may become Descope JWT Templates or SAML attributes. |
| Application sign-on policy assignments | `GET {{apiPath}}/v1/environments/{{envID}}/applications/{{appID}}/signOnPolicyAssignments` | Which PingOne sign-on policy governs the app. |
| Application flow policy assignments | `GET {{apiPath}}/v1/environments/{{envID}}/applications/{{appID}}/flowPolicyAssignments` | Whether DaVinci or flow policy configuration drives the app journey. |
| All sign-on policies | `GET {{apiPath}}/v1/environments/{{envID}}/signOnPolicies` | Policy inventory for Flow migration. |
| One sign-on policy | `GET {{apiPath}}/v1/environments/{{envID}}/signOnPolicies/{{policyID}}` | Policy-level behavior and decision points. |
| Sign-on policy actions | `GET {{apiPath}}/v1/environments/{{envID}}/signOnPolicies/{{policyID}}/actions` | Login methods, MFA, risk, recovery, and branches to rebuild in Descope Flows. |
| All resources | `GET {{apiPath}}/v1/environments/{{envID}}/resources` | Protected API/MCP resource inventory and audience strategy. |
| One resource | `GET {{apiPath}}/v1/environments/{{envID}}/resources/{{resourceID}}` | Resource identifier/audience, description, and token validation implications. |
| Resource scopes | `GET {{apiPath}}/v1/environments/{{envID}}/resources/{{resourceID}}/scopes` | Scope catalog for Descope Resources, Policies, and API enforcement. |
| Resource attributes | `GET {{apiPath}}/v1/environments/{{envID}}/resources/{{resourceID}}/attributes` | Resource-specific token claims or attribute mappings. |
| All identity providers | `GET {{apiPath}}/v1/environments/{{envID}}/identityProviders` | Social provider vs customer/org IdP inventory. |
| One identity provider | `GET {{apiPath}}/v1/environments/{{envID}}/identityProviders/{{providerID}}` | Provider type, domains, issuer/metadata, and SSO/social migration target. |
| Identity provider attributes | `GET {{apiPath}}/v1/environments/{{envID}}/identityProviders/{{providerID}}/attributes` | IdP claim mappings for social profile, tenant SSO, or SCIM/group mapping decisions. |

When summarizing API discovery, record which routes were queried, what data was available, and what
confidence that gives the Descope hierarchy recommendation. Prefer metadata and counts before full
user export. If direct API access is unavailable, ask for equivalent JSON/CSV exports or console
screenshots and mark discovery as partial. If a route is unavailable in the tenant, mark it as
unavailable and continue with the closest available export or console evidence.

## Package and Import Hints

Look for packages, namespaces, and imports that imply PingOne, DaVinci, or generic protocol usage.
Ping Orchestration SDKs are client-side/mobile only. The documented SDK platforms are
Kotlin/Android, Swift/iOS, and JavaScript/TypeScript; also treat React Native TypeScript as mobile
SDK scope.
Do not classify Python, Go, Node server, Java, or .NET findings as Ping orchestration SDK imports.
In those stacks, look for OIDC/SAML config, JWT validation, claims, env vars, PingOne REST/API
calls, cookies, or app-side authorization.

JavaScript/TypeScript hints:

- `@pingidentity/*`
- `@forgerock/*`
- `davinci`
- `pingone`
- Ping Orchestration SDK modules
- `oidc-client`, `oidc-client-ts`
- `openid-client`
- `passport-openidconnect`, `passport-oauth2`, `passport-saml`
- `next-auth` / Auth.js provider configuration with PingOne issuer
- `jose`, `jsonwebtoken`, `jwks-rsa` used with PingOne issuer/JWKS

Kotlin / Android and Swift / iOS hints:

The symbol inventory for both platforms is in the Swift and Kotlin grep commands under
[Search Groups](#search-groups). Beyond those symbols, also look for:

- Gradle, Swift Package Manager, or CocoaPods dependencies on Ping SDK artifacts (Ping Android SDK,
  DaVinci client packages, Ping Swift SDK packages).
- DaVinci, OIDC Redirect, Protect, MFA OTP, FIDO2/Passkeys, device ID, or device profiling modules.

Treat both as high-priority SDK surfaces, especially for PingOne Protect and device-context
collection. Classify the shape of the code:

- `OidcWeb` / `module(Oidc)` / `OidcWebClient` / discovery endpoint / browser mode / redirect URI ->
  mobile OIDC Redirect or centralized-login evidence.
- `PingOrchestrate` plus collector/node-shaped handling (`Journey`, `Node`, `ContinueNode`,
  `SuccessNode`, `FailureNode`) -> embedded DaVinci orchestration evidence.
- Collector/node-shaped UI code means the app renders Ping DaVinci inputs with native components.
  Plan to replace that renderer with Descope Mobile SDK Native Flow view integration, not translate
  each collector directly.

Python hints (not Ping orchestration SDKs):

- `authlib`
- `mozilla-django-oidc`
- `python-jose`, `PyJWT`
- `requests_oauthlib`
- Custom calls to PingOne `/as/authorize`, `/as/token`, `/userinfo`, or management endpoints

Go hints (not Ping orchestration SDKs):

- `coreos/go-oidc`
- `golang.org/x/oauth2`
- `lestrrat-go/jwx`
- Custom JWKS validation against PingOne issuer

Java/.NET hints (not Ping orchestration SDKs):

- Spring Security OAuth/OIDC configuration with PingOne issuer
- ASP.NET OpenIdConnect middleware with PingOne authority
- Nimbus JOSE/JWT, jose4j, Microsoft IdentityModel token validators pointed at PingOne

Interpretation:

- Generic OIDC libraries suggest Path A may be viable only when the app is not using Ping SDKs for
  login/session behavior.
- Ping/DaVinci SDK imports in Kotlin, Swift, JavaScript/TypeScript, or React Native TypeScript
  suggest Path B or C. For Swift, Kotlin, or React Native, Path B targets Descope Mobile SDK Native
  Flows by default and must replace the Ping SDK.
- Distinguish Ping OIDC Sign-on/centralized browser login from DaVinci collector-based flows, but
  do not recommend keeping Ping SDK code for either pattern.
- Backend Python/Go/Node/Java/.NET hits suggest Path A, token validation, REST/API migration,
  Management API automation, or app-side authorization review, not a Ping SDK swap.
- Only JWT/JWKS validation in APIs suggests downstream services need issuer/JWKS/claim updates, even if login lives elsewhere.

## Environment Variable Hints

PingOne CIAM variables often include:

- `PINGONE_ENVIRONMENT_ID`
- `PINGONE_CLIENT_ID`
- `PINGONE_CLIENT_SECRET`
- `PINGONE_REGION`
- `PINGONE_ISSUER`
- `PINGONE_AUTH_URL`
- `PINGONE_TOKEN_URL`
- `PINGONE_JWKS_URI`
- `PINGONE_REDIRECT_URI`
- `PINGONE_SCOPES`
- `PINGONE_API_BASE_URL`
- `PINGONE_POPULATION_ID`
- `PINGONE_DAVINCI_FLOW_ID`
- `PINGONE_WORKER_APP_ID`
- `PINGONE_WORKER_CLIENT_ID`
- `PINGONE_WORKER_CLIENT_SECRET`
- `PINGONE_ADMIN_CLIENT_ID`
- `PINGONE_ADMIN_CLIENT_SECRET`
- `PING_CLIENT_ID`
- `PING_CLIENT_SECRET`
- `PING_ENVIRONMENT_ID`
- `PING_ISSUER`

Descope additions usually include:

- `DESCOPE_PROJECT_ID`
- `NEXT_PUBLIC_DESCOPE_PROJECT_ID` for browser-rendered Next.js/React integrations
- `DESCOPE_MANAGEMENT_KEY` only for server-side Management API work

Do not add `DESCOPE_MANAGEMENT_KEY` to client-side bundles or `NEXT_PUBLIC_` variables.

## Worker App Hints

Worker apps are service/admin API clients, not customer login apps. For what they map to in
Descope, see
[implementation-nuances.md -> Worker Apps and Service Automation](./implementation-nuances.md#worker-apps-and-service-automation).

Search for:

```bash
grep -rni "worker\|client_credentials\|admin.*role\|administrator.*role\|PINGONE_WORKER\|PINGONE_ADMIN_CLIENT" \
  --include="*.env*" --include="*.ts" --include="*.tsx" --include="*.js" \
  --include="*.py" --include="*.go" --include="*.java" --include="*.cs" \
  --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  . 2>/dev/null
```

For each Worker app hit, record:

- Whether it calls PingOne admin/platform APIs.
- Which role assignments or scopes it relies on.
- Whether it manages users, populations, groups, applications, PingOne Authorize, Verify, MFA, or audit.
- Whether it is a temporary migration/export tool or a production service.
- Which Descope target it maps to - see the Worker app table in
  [implementation-nuances.md](./implementation-nuances.md#worker-apps-and-service-automation).

## Hierarchy and Group Hints

Collect hierarchy evidence here; classify it using the tables in
[implementation-nuances.md -> Hierarchy and Object Mapping](./implementation-nuances.md#hierarchy-and-object-mapping).
Population IDs in claims, database rows, or route params may indicate tenant routing, but they may
also be segmentation or policy state - confirm before creating tenants.

Search for:

```bash
grep -rni "population\|populationId\|group\|groupId\|memberOf\|membership\|dynamic.*group\|nested.*group\|role\|permission\|entitlement\|tenant\|organization\|account" \
  . 2>/dev/null
```

For each hit, record whether it indicates:

- Project/environment isolation
- Tenant/customer-community membership
- Role/permission authorization
- Segmentation or personalization
- Dynamic group rule inputs
- External SSO/SCIM group mapping
- Nested/effective access resolution

## OIDC and SAML Hints

PingOne OIDC evidence:

- Issuer contains `auth.pingone.com`
- Discovery URL contains `.well-known/openid-configuration`
- Endpoints contain `/as/authorize`, `/as/token`, `/as/userinfo`, or `/as/jwks`
- Code validates `iss`, `aud`, `client_id`, `scope`, `email_verified`, `groups`, or custom claims
- Framework config uses `authority`, `issuer`, `metadataUrl`, `jwksUri`, or `wellKnown`

If the app uses a generic OIDC client with no Ping SDK login/session dependency, consider Path A:

- Update issuer/authority to Descope
- Update client ID/secret if the protocol integration requires it
- Treat PingOne OIDC Web and SPA application records as the same OIDC Federated App migration
  surface - see
  [Federated App / Protocol-Config Migration](./implementation-nuances.md#federated-app--protocol-config-migration)
- Update redirect/logout URLs
- Update JWKS/discovery settings
- Update expected claims
- Preserve application session middleware where possible

SAML hints:

- `saml`, `metadata`, `acs`, `entityId`, `x509`, `certificate`, `NameID`
- Customer SSO may be configured in PingOne rather than in repo code
- PingOne External IdPs may appear in login, identifier-first, or external-IdP authentication policy
  steps rather than application code
- Map customer SSO to Descope tenant SSO / SSO Setup Suite only when the customer organization model is confirmed
- Map customer/org External IdPs to Descope tenant-level SSO connections; map consumer/social IdPs
  to Descope social login

## DaVinci Hints

DaVinci may appear as:

- A package/import name containing `davinci`
- `flowId`, `flow_id`, or `DAVINCI_FLOW_ID`
- `interactionId`
- Collector/node terminology
- Hosted widget/embed URLs
- Callback handlers receiving DaVinci interaction results
- Connector endpoints called by DaVinci rather than by the app

DaVinci-heavy migrations need external configuration evidence:

- Flow export
- Screenshots of journey graph
- List of connectors and endpoints
- Conditions/branching rules
- Claims set by the journey
- Error/fallback paths
- Risk, MFA, Verify, or Authorize nodes

If the repo only contains a flow ID, treat the code analysis as incomplete until the DaVinci flow
logic is reviewed.

## Out-of-Scope Detection

Run:

```bash
grep -rni "pingfederate\|pingdirectory\|pingaccess\|pingauthorize\|pingid" . 2>/dev/null
```

Also look for:

- Employee app launcher terminology
- Workforce SSO
- HRIS / HR-driven lifecycle provisioning
- Device trust for employees
- `PingID` used as employee MFA
- LDAP/directory migration language
- Reverse proxy/access gateway patterns
- ForgeRock/PingOne Advanced Identity Cloud journeys, realms, AM trees, IDM managed objects

If found, stop unless the user explicitly confirms this CIAM skill should continue for only the
PingOne for Customers portions.

Important nuance: `PingOne Authorize` can be in scope when it is customer-facing authorization in a
PingOne CIAM migration. `PingAuthorize` as a standalone product migration is out of scope unless the
user says otherwise.

## Evidence Recording Template

For each hit, record:

| File/source | Line | Evidence | PingOne surface | Migration area | Complexity |
|---|---:|---|---|---|---|
| `path/file.ts` | 42 | `PINGONE_ISSUER` | OIDC application login | Code/config | Low |

Migration area values:

- Code
- Console/Flow config
- Data migration
- Architecture review
- Out-of-scope review

Complexity guide:

- **Low** - issuer/env/config swap, mechanical claim name update, documented web Client SDK or Mobile SDK replacement
- **Medium** - session middleware rewrite, custom login UI, user/profile migration, SSO/SCIM config
- **High** - DaVinci journey rebuild, Protect risk decisions, Verify compliance workflow, Authorize/FGA model translation, ambiguous population-to-tenant mapping
