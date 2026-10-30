# Azure AD B2C Detection Patterns

## Contents

- [Search Groups](#search-groups)
- [Package and Config Hints](#package-and-config-hints)
- [Custom Policy XML Hints](#custom-policy-xml-hints)
- [Read-Only Microsoft Graph Discovery](#read-only-microsoft-graph-discovery)
- [Out-of-Scope Detection](#out-of-scope-detection)
- [Evidence Recording Template](#evidence-recording-template)

---

## Search Groups

Prefer `rg` when available. Exclude build output (`node_modules`, `.next`, `dist`, `bin`, `obj`, `venv`).

```bash
EXCL="--exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=bin --exclude-dir=obj --exclude-dir=venv"

# 1. MSAL / Microsoft identity packages (decides the framework guide)
grep -rn "@azure/msal-browser\|@azure/msal-react\|@azure/msal-angular\|@azure/msal-node\|Microsoft.Identity.Web\|Microsoft.Identity.Client\|passport-azure-ad\|azure-ad-b2c\|active-directory-b2c" \
  --include="package.json" --include="*.csproj" --include="requirements*.txt" --include="pyproject.toml" \
  --include="pom.xml" --include="build.gradle*" --include="Podfile" --include="*.gradle" $EXCL . 2>/dev/null
grep -rn "^msal\b\|^msal==" --include="requirements*.txt" . 2>/dev/null

# 2. B2C authority, domains, and policy names
grep -rn "b2clogin\.com\|onmicrosoft\.com\|knownAuthorities\|AzureAdB2C\|B2C_1_\|B2C_1A_\|SignUpSignInPolicyId\|ResetPasswordPolicyId\|EditProfilePolicyId\|b2cPolicies" $EXCL . 2>/dev/null

# 3. MSAL call sites (login, token, logout, redirect handling)
grep -rn "loginRedirect\|loginPopup\|acquireTokenSilent\|acquireTokenRedirect\|acquireTokenPopup\|handleRedirectPromise\|logoutRedirect\|logoutPopup\|MsalProvider\|MsalGuard\|MsalInterceptor\|MsalRedirectComponent\|useMsal\|useIsAuthenticated\|AuthenticatedTemplate\|MsalAuthenticationTemplate\|PublicClientApplication\|ConfidentialClientApplication\|AddMicrosoftIdentityWebApi\|AddMicrosoftIdentityWebApp\|AddMicrosoftIdentityUI" $EXCL . 2>/dev/null

# 4. B2C-specific logic that becomes dead code
grep -rn "AADB2C\|homeAccountId\|idTokenClaims\|\btfp\b\|\.acr\b\|protocolMode\|InteractionRequiredAuthError" $EXCL . 2>/dev/null

# 5. Token claims that change
grep -rn "\bscp\b\|RequiredScope\|VerifyUserHasAnyAcceptedScope\|GetObjectId\|\boid\b\|emails\[\|\"emails\"\|extension_\|\bidp\b\|identity/claims/scope" $EXCL . 2>/dev/null

# 6. Roles and groups
grep -rn "extension_.*[Rr]ole\|\"groups\"\|memberOf\|IsInRole\|Authorize(Roles\|hasRole\|roles\.includes" $EXCL . 2>/dev/null

# 7. Enterprise login routing
grep -rn "domain_hint\|domainHint\|extraQueryParameters\|login_hint" $EXCL . 2>/dev/null

# 8. Embedded (iframe) sign-in
grep -rn "<iframe\|window\.top\.location\.reload\|window\.parent\.postMessage\|JourneyFraming" $EXCL . 2>/dev/null

# 9. ROPC / password grant
grep -rn "grant_type=password\|acquireTokenByUsernamePassword\|AcquireTokenByUsernamePassword\|B2C_1_ROPC\|ROPC" $EXCL . 2>/dev/null

# 10. Microsoft Graph user management
grep -rn "graph\.microsoft\.com\|GraphServiceClient\|@microsoft/microsoft-graph-client\|msgraph" $EXCL . 2>/dev/null

# 11. Env vars and config
grep -rn "AZURE_AD_B2C\|AZURE_B2C\|B2C_\|MSAL_\|AAD_B2C\|REACT_APP_B2C\|VITE_B2C\|NEXT_PUBLIC_B2C" \
  --include="*.env*" --include="*.json" --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  --include="*.ts" --include="*.js" --include="*.cs" --include="*.py" $EXCL . 2>/dev/null

# 12. Custom policy XML in the repo
grep -rln "TrustFrameworkPolicy" --include="*.xml" $EXCL . 2>/dev/null
```

For each hit record: file:line, what it does, complexity (Low / Medium / High).

---

## Package and Config Hints

| Signal | Meaning | Guide |
|---|---|---|
| `@azure/msal-react` | React SPA, redirect/popup | `implementation-nuances.md` → React |
| `@azure/msal-angular` | Angular SPA | → Angular |
| `@azure/msal-browser` only | Vue or plain JS SPA | → Vue / Plain JavaScript |
| `next` + `@azure/msal-react` or NextAuth `AzureADB2CProvider` | Next.js | → Next.js |
| `Microsoft.Identity.Web` + `AddMicrosoftIdentityWebApi` | ASP.NET Core API | `backend-sdks.md` → .NET |
| `Microsoft.Identity.Web` + `AddMicrosoftIdentityWebApp` | ASP.NET Core web app (server-side login) | `implementation-nuances.md` → Server-side web apps |
| `@azure/msal-node` / `passport-azure-ad` `OIDCStrategy` | Node server-side login | → Server-side web apps |
| `passport-azure-ad` `BearerStrategy`, `jwks-rsa` with `b2clogin.com` | Node API validation | `backend-sdks.md` → Node.js |
| `msal` (Python), PyJWT with B2C metadata | Python | `backend-sdks.md` → Python |
| `spring-cloud-azure-starter-active-directory-b2c` | Spring | `backend-sdks.md` → Java |
| `MSAL` pods / `com.microsoft.identity.client` | iOS / Android | → Native / mobile |

Config shapes to find:
- MSAL: `authority: "https://<tenant>.b2clogin.com/<tenant>.onmicrosoft.com/<policy>"`, `knownAuthorities`, `b2cPolicies.names.*`, `protectedResources.*.scopes`
- .NET `appsettings.json`: `"AzureAdB2C": { "Instance", "Domain", "ClientId", "SignUpSignInPolicyId", "ResetPasswordPolicyId", "EditProfilePolicyId", "Scopes" }`
- API scopes: `https://<tenant>.onmicrosoft.com/<api>/<scope>` — the last segment is the scope name to recreate on the Descope Resource
- Custom domain: authority host that is not `*.b2clogin.com`

---

## Custom Policy XML Hints

Policy files chain: `TrustFrameworkBase.xml` → `TrustFrameworkLocalization.xml` →
`TrustFrameworkExtensions.xml` → relying party files (`SignUpOrSignin.xml`, `PasswordReset.xml`,
`ProfileEdit.xml`). Start from each relying party file (`<RelyingParty>` → `DefaultUserJourney`).

| XML element | What it tells you | Descope |
|---|---|---|
| `<UserJourney Id="…">` / `<OrchestrationStep>` | Steps of a login journey | Flow and its steps |
| `<ClaimsProvider>` with `Protocol Name="OpenIdConnect"` | OIDC IdP (customer Entra ID, social) — check `METADATA`, `client_id`, `ValidTokenIssuerPrefixes` (multi-tenant) | Tenant OIDC SSO or social login |
| `Protocol Name="SAML2"` | SAML IdP — check `PartnerEntity`, `WantsSignedRequests`, `SamlMessageSigning` / `SamlAssertionDecryption` keys | Tenant SAML SSO; signing/encryption dependency |
| `Handler="…RestfulProvider…"` | REST call (API connector equivalent) — check `ServiceUrl`, input/output claims | HTTP Connector |
| `<ClaimsTransformation>` | Claim logic | Scriptlet / JWT Template |
| `ClaimType Id="extension_…"` | Custom attribute | Custom attribute |
| `<OutputClaim … PartnerClaimType="…">` in the relying party | Token claims the app receives | JWT Template |
| `<ContentDefinition>` / `LoadUri` | Page layout templates | Flow styles |
| `JourneyFraming Enabled="true"` | Embedded (iframe) sign-in | Embedded Flow |
| `PhoneFactor`, `TOTP` technical profiles | MFA | MFA steps |
| `domain_hint` / `ClaimsProviderSelection` with `TargetClaimsExchangeId` per customer | Home realm discovery | Tenant email domains |
| `amr` captured from a federated IdP + skip MFA precondition | MFA trusted from the customer IdP | Condition on `idpOIDCClaims.amr` |
| `AuthenticationContextReferenceClaimPattern` | `acr` vs `tfp` policy claim | Delete consumers |

---

## Read-Only Microsoft Graph Discovery

Optional. Ask the user before calling the tenant. Use a dedicated app registration in the B2C
tenant with **read-only application permissions** and admin consent, then a client-credentials
token from `https://login.microsoftonline.com/<b2c-tenant-id>/oauth2/v2.0/token`
(`scope=https://graph.microsoft.com/.default`). Never write to the tenant.

| What | Request | Permission (application) |
|---|---|---|
| User flows (+ their IdPs) | `GET https://graph.microsoft.com/beta/identity/b2cUserFlows?$expand=identityProviders` | `IdentityUserFlow.Read.All` |
| Custom policies (list) | `GET https://graph.microsoft.com/beta/trustFramework/policies` | `Policy.Read.All` |
| Custom policy XML | `GET https://graph.microsoft.com/beta/trustFramework/policies/<id>/$value` | `Policy.Read.All` |
| Identity providers (social, Apple, OIDC) | `GET https://graph.microsoft.com/beta/identity/identityProviders` (v1.0 returns social and Apple only) | `IdentityProvider.Read.All` |
| App registrations (frontends, APIs, daemons) | `GET https://graph.microsoft.com/v1.0/applications?$select=id,appId,displayName,identifierUris,api,requiredResourceAccess,spa,web,publicClient,passwordCredentials` | `Application.Read.All` |
| Custom attributes | `GET https://graph.microsoft.com/v1.0/applications/<b2c-extensions-app object id>/extensionProperties` | `Application.Read.All` |
| User count | `GET https://graph.microsoft.com/v1.0/users/$count` with header `ConsistencyLevel: eventual` | `User.Read.All` |
| Users (for export) | See `implementation-nuances.md` → Exporting users | `User.Read.All` |

Notes:
- `beta` endpoints can change; fall back to asking the user for XML files or portal screenshots.
- Client secrets come back as `****` — expected; they cannot be migrated.
- API connectors (`GET /beta/identity/apiConnectors`) require `APIConnectors.ReadWrite.All` (no read-only permission) — prefer asking the user to list them from the portal (User flows → API connectors).
- SAML enterprise IdPs exist only in custom policy XML, not in the identity providers list.

From app registrations, classify each:
- `identifierUris` + `api.oauth2PermissionScopes` → **API** → Descope Resource (copy scope `value`s)
- `spa.redirectUris` / `web.redirectUris` + `requiredResourceAccess` to the API → **frontend** → Inbound App
- `passwordCredentials` and no redirect URIs, app permissions → **daemon** → Inbound App (client credentials)
- `b2c-extensions-app` → custom attribute storage, not an app to migrate

---

## Out-of-Scope Detection

Stop and confirm scope if you find:

| Signal | Product | Action |
|---|---|---|
| Authority `https://<tenant>.ciamlogin.com` | Microsoft Entra External ID | Out of scope — different product |
| Authority `https://login.microsoftonline.com/<tenant>` with no B2C policy, workforce app roles, groups claims | Workforce Microsoft Entra ID | Out of scope |
| `login.microsoftonline.com/<tenant>.onmicrosoft.com/<policy>` (legacy B2C endpoint) | Azure AD B2C (old endpoint) | In scope — treat as `b2clogin.com` |
| Azure AD B2B guest invitations | Workforce B2B | Out of scope |

---

## Evidence Recording Template

```markdown
## B2C Discovery Evidence

### Tenant
- Tenant name / domain: contoso.onmicrosoft.com
- Login host: contoso.b2clogin.com | login.contoso.com (custom domain)
- Users: N (local: N, social: N, enterprise: N)

### Journeys
| Policy | Type | Steps / notable logic | Descope Flow |
|---|---|---|---|
| B2C_1A_signup_signin | Custom policy | email+password, Google, 3 SAML IdPs, REST before token | sign-up-or-in |

### App registrations
| Name | Kind | Scopes / redirect URIs | Descope |
|---|---|---|---|
| tasks-api | API | tasks.read, tasks.write | Resource |
| tasks-spa | Frontend | https://app.contoso.com | Inbound App |

### API connectors / REST technical profiles
| Name | Hook point | URL | Purpose | Descope placement |
|---|---|---|---|---|

### Custom attributes
| Graph name | Policy/token name | Used by app | Descope custom attribute |
|---|---|---|---|

### Enterprise SSO connections
| Customer | IdP | Protocol | Email domain(s) | ACS / redirect URL host | Signed requests / encrypted assertions | OIDC secret available outside B2C | MFA behavior | Cutover result |
|---|---|---|---|---|---|---|---|---|
| Acme | Okta | SAML | acme.com | login.contoso.com | No | n/a | Trust IdP | May move without IdP changes |
| Globex | Entra ID | OIDC | globex.com | contoso.b2clogin.com | n/a | No | B2C adds MFA | Admin updates redirect URI + new secret |
```
