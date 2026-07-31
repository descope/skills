# PingOne CIAM Detection Patterns

## Contents

- [Search Groups](#search-groups)
- [Package and Import Hints](#package-and-import-hints)
- [Environment Variable Hints](#environment-variable-hints)
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

Useful `rg` equivalents:

```bash
rg -n -i "pingone|pingidentity|davinci|forgerock|orchestration" -g '*.{ts,tsx,js,jsx,kt,kts,swift}' -g '!node_modules' -g '!.next' -g '!dist'
rg -n -i "import PingOrchestrate|import PingOidc|import PingProtect|import PingOneProtect|import PingLogger|import PingBrowser|OidcWebClient|createOidcWebClient|authorize|discoveryEndpoint|browserMode|browserType|acrValues" -g '*.swift'
rg -n -i "com\\.pingidentity\\.oidc\\.OidcWeb|com\\.pingidentity\\.oidc\\.module\\.Oidc|com\\.pingidentity\\.logger\\.Logger|Logger\\.STANDARD|OidcWeb|module\\(Oidc\\)|clientId|discoveryEndpoint|redirectUri|scopes|web\\.authorize|onSuccess|onFailure|viewModelScope\\.launch|MutableStateFlow|PingProtect|ping-android-sdk|davinci-client|orchestrate|Oidc|OIDC|protect|device.*profil|Journey|Node|ContinueNode|SuccessNode|FailureNode" -g '*.{kt,kts,gradle}'
rg -n -i "pingone|auth\\.pingone\\.com|api\\.pingone\\.com|/as/authorize|/as/token|/userinfo|/as/jwks" -g '!node_modules' -g '!.next' -g '!dist'
rg -n -i "PINGONE_|PING_ONE_|PING_CLIENT|PING_ENVIRONMENT|PING_REGION|PING_ISSUER|PING_AUTH"
rg -n -i "issuer|client_id|clientId|clientSecret|redirect_uri|redirectUri|openid-configuration|jwks_uri|authorization_endpoint|token_endpoint"
rg -n -i "auth\.pingone\.com|api\.pingone\.com|pingone\.com"
rg -n -i "population|populationId|userId|username|emailVerified|verifyEmail|profile|customAttributes|locale|preferredLanguage"
```

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

Kotlin / Android hints:

- Treat Android/Kotlin as a high-priority SDK surface, especially for PingOne Protect and device
  context collection.
- Ping Orchestration SDK package/import names.
- DaVinci, OIDC Redirect, Protect, MFA OTP, FIDO2/Passkeys, device ID, or device profiling modules.
- Gradle dependencies from Ping SDK artifacts such as Ping Android SDK or DaVinci client packages.
- `import com.pingidentity.oidc.OidcWeb`
- `import com.pingidentity.oidc.module.Oidc`
- `import com.pingidentity.logger.Logger`
- `Logger.STANDARD`
- `OidcWeb { ... }`
- `module(Oidc) { clientId / discoveryEndpoint / scopes / redirectUri }`
- `viewModelScope.launch`
- `web.authorize { ... }`
- `onSuccess { user -> ... }` / `onFailure { throwable -> ... }`
- `MutableStateFlow` or other ViewModel state around login.
- Journey/node navigation types such as `Journey`, `Node`, `ContinueNode`, `SuccessNode`, or
  `FailureNode`.

Swift / iOS hints:

- Treat iOS/Swift as a high-priority SDK surface, especially for PingOne Protect and device context
  collection.
- `import PingOrchestrate`
- `import PingOidc`
- `import PingProtect` or `import PingOneProtect`
- `import PingLogger`
- `import PingBrowser`
- `OidcWebClient.createOidcWebClient`
- `config.module(PingOidc.OidcModule.config)`
- `clientId`, `scopes`, `redirectUri`, `discoveryEndpoint`
- `browserMode`, `browserType`, `acrValues`
- `authorize { options in ... }`
- Swift Package Manager or CocoaPods dependencies from Ping SDK artifacts.

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
  suggest Path B or C. For Swift, Kotlin, or React Native, Path B targets Descope Mobile SDKs and
  must replace the Ping SDK.
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

PingOne Worker apps are primarily service/admin API clients. They usually use client credentials and
administrator role assignments to call PingOne platform APIs. They are not normal customer login
apps and should not be mapped to Descope login Flows or Federated Apps.

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
- Whether it should map to Descope Management API with `DESCOPE_MANAGEMENT_KEY`, or Descope Access Keys/M2M for your own APIs.

## Hierarchy and Group Hints

Use hierarchy evidence to decide project, tenant, role, attribute, and SSO/SCIM mappings:

- PingOne environments usually map to Descope projects.
- PingOne populations map to tenants only when they represent customer organizations, realms, or
  isolated user communities.
- Population IDs in claims, database rows, or route params may indicate tenant routing, but they may
  also be segmentation or policy state. Confirm before creating tenants.
- PingOne users belong to exactly one population; do not create multi-tenant Descope membership
  unless the app has a confirmed multi-organization model.
- Groups used for app access, permissions, admin capability, or authorization claims map to
  project-level or tenant-level roles.
- Groups used for filtering, personalization, cohorts, regions, reporting, plans, or lifecycle state
  map to custom attributes or Flow/app conditions.
- Dynamic groups require source attributes and recreated rules, not just imported current members.
- External IdP, LDAP, or directory groups should remain authoritative through SSO/SCIM group-to-role
  mappings.
- Nested groups usually need flattened effective access unless the hierarchy itself is required.

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
- Update redirect/logout URLs
- Update JWKS/discovery settings
- Update expected claims
- Preserve application session middleware where possible

SAML hints:

- `saml`, `metadata`, `acs`, `entityId`, `x509`, `certificate`, `NameID`
- Customer SSO may be configured in PingOne rather than in repo code
- Map customer SSO to Descope tenant SSO / SSO Setup Suite only when the customer organization model is confirmed

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
