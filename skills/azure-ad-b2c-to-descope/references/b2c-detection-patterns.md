# Azure AD B2C Detection Patterns

## Contents

- [Search Groups](#search-groups)
- [Package and Config Hints](#package-and-config-hints)
- [Custom Policy XML Hints](#custom-policy-xml-hints)
- [Read-Only Microsoft Graph Discovery](#read-only-microsoft-graph-discovery)
  - [App registration type → Descope app](#app-registration-type--descope-app)
  - [Sign-in method inventory](#sign-in-method-inventory)
- [Out-of-Scope Detection](#out-of-scope-detection)
- [Evidence Recording Template](#evidence-recording-template)

---

## Search Groups

Prefer `rg` when available. Exclude build output, vendored code, lockfiles and minified bundles —
the broad claim searches (groups 4, 5, 8) otherwise flood with matches from them. `-I` skips binary
files. The patterns work with macOS (BSD) and GNU grep.

```bash
# An array, so it expands correctly in both bash and zsh (zsh doesn't word-split "$EXCL")
# Don't exclude lib/ or packages/ by name — monorepos keep source there. For .NET, check that
# wwwroot/lib hits are vendored libraries before acting on them.
EXCL=(-I --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=bin --exclude-dir=obj
  --exclude-dir=venv --exclude-dir=.git --exclude-dir=build --exclude-dir=out --exclude-dir=target --exclude-dir=Pods
  --exclude-dir=vendor --exclude-dir=coverage
  --exclude='*.lock' --exclude='*-lock.json' --exclude='*.min.js')

# 1. MSAL / Microsoft identity packages (decides the framework guide)
grep -rni "@azure/msal-browser\|@azure/msal-react\|@azure/msal-angular\|@azure/msal-node\|Microsoft.Identity.Web\|Microsoft.Identity.Client\|passport-azure-ad\|azure-ad-b2c\|active-directory-b2c\|msal4j\|identity.client:msal\|'MSAL'\|\"MSAL\"" \
  --include="package.json" --include="*.csproj" --include="packages.config" --include="requirements*.txt" --include="pyproject.toml" \
  --include="Pipfile" --include="pom.xml" --include="build.gradle*" --include="*.gradle" --include="*.gradle.kts" \
  --include="Podfile" --include="Package.swift" --include="Cartfile" "${EXCL[@]}" . 2>/dev/null
# Python: msal as a requirement line, or quoted in pyproject.toml / Pipfile lists
grep -rnE "^msal([=<>~! ]|$)|[\"']msal([=<>~! ]|[\"'])" --include="requirements*.txt" --include="pyproject.toml" --include="Pipfile" . 2>/dev/null

# 2. B2C authority, domains, and policy names
grep -rn "b2clogin\.com\|onmicrosoft\.com\|knownAuthorities\|AzureAdB2C\|B2C_1_\|B2C_1A_\|SignUpSignInPolicyId\|ResetPasswordPolicyId\|EditProfilePolicyId\|b2cPolicies" "${EXCL[@]}" . 2>/dev/null

# 3. MSAL call sites (login, token, logout, redirect handling)
grep -rn "loginRedirect\|loginPopup\|acquireTokenSilent\|acquireTokenRedirect\|acquireTokenPopup\|handleRedirectPromise\|logoutRedirect\|logoutPopup\|MsalProvider\|MsalGuard\|MsalInterceptor\|MsalRedirectComponent\|useMsal\|useIsAuthenticated\|AuthenticatedTemplate\|MsalAuthenticationTemplate\|PublicClientApplication\|ConfidentialClientApplication\|AddMicrosoftIdentityWebApi\|AddMicrosoftIdentityWebApp\|AddMicrosoftIdentityUI" "${EXCL[@]}" . 2>/dev/null

# 4. B2C-specific logic that becomes dead code
grep -rn "AADB2C\|homeAccountId\|idTokenClaims\|\btfp\b\|\.acr\b\|protocolMode\|InteractionRequiredAuthError" "${EXCL[@]}" . 2>/dev/null

# 5. Token claims that change
grep -rn "\bscp\b\|RequiredScope\|VerifyUserHasAnyAcceptedScope\|GetObjectId\|\boid\b\|emails\[\|\"emails\"\|extension_\|\bidp\b\|identity/claims/scope" "${EXCL[@]}" . 2>/dev/null

# 5b. User ID reads — anything stored, compared or used as a key decides the User ID strategy
#     (a `sub` hit used as a data key means the JWT Template must override `sub`)
grep -rnI "\.sub\b\|\[['\"]sub['\"]\]\|ClaimTypes\.NameIdentifier\|nameidentifier\|localAccountId\|homeAccountId\|\.oid\b\|\[['\"]oid['\"]\]\|objectidentifier" "${EXCL[@]}" . 2>/dev/null

# 6. Roles and groups
grep -rniI "extension_.*role\|\"groups\"\|memberOf\|IsInRole\|Authorize(Roles\|hasRole\|requireRole\|roles\.includes\|ClaimTypes\.Role\|\.role\b\|\[['\"]role['\"]\]" "${EXCL[@]}" . 2>/dev/null

# 7. Enterprise login routing
grep -rn "domain_hint\|domainHint\|extraQueryParameters\|login_hint" "${EXCL[@]}" . 2>/dev/null

# 8. Embedded (iframe) sign-in
grep -rn "<iframe\|window\.top\.location\.reload\|window\.parent\.postMessage\|JourneyFraming" "${EXCL[@]}" . 2>/dev/null

# 9. ROPC / password grant
grep -rn "grant_type=password\|acquireTokenByUsernamePassword\|AcquireTokenByUsernamePassword\|B2C_1_ROPC\|ROPC" "${EXCL[@]}" . 2>/dev/null

# 10. Microsoft Graph user management
grep -rn "graph\.microsoft\.com\|GraphServiceClient\|@microsoft/microsoft-graph-client\|msgraph" "${EXCL[@]}" . 2>/dev/null
# 10b. Invites and outbound auth email / SMS (app-built invitations, custom verification)
grep -rniI "id_token_hint\|invit[a-z]*link\|sendInvit\|@sendgrid\|sendgrid\|mailjet\|SendGridClient\|twilio" "${EXCL[@]}" . 2>/dev/null

# 11. Env vars and config
grep -rn "AZURE_AD_B2C\|AZURE_B2C\|B2C_\|MSAL_\|AAD_B2C\|REACT_APP_B2C\|VITE_B2C\|NEXT_PUBLIC_B2C" \
  --include="*.env*" --include="*.json" --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.mjs" --include="*.vue" \
  --include="*.cs" --include="*.config" --include="*.py" "${EXCL[@]}" . 2>/dev/null

# 12. Custom policy XML in the repo
grep -rln "TrustFrameworkPolicy" --include="*.xml" "${EXCL[@]}" . 2>/dev/null

# 13. User IDs stored or parsed as GUIDs (new users get string IDs if the B2C ID is kept)
grep -rniI "uniqueidentifier\|guid\.\(try\)\?parse\|uuid\.fromstring\|{[a-z]*:guid}\|\bguid [a-z]*id\b\|user_\?id.*\b\(uuid\|guid\)\b" "${EXCL[@]}" . 2>/dev/null

# 14. Customer organization in claims and queries (org claim reads, tenant-scoped data access)
grep -rniI "extension_[a-z]*\(org\|tenant\|company\|customer\|account\)\|\b\(org\|tenant\|company\|customer\)_\?id\b\|\b\(org\|tenant\|company\)\(id\|name\)\b" "${EXCL[@]}" . 2>/dev/null
```

For each hit record: file:line, what it does, complexity (Low / Medium / High).

---

## Package and Config Hints

| Signal | Meaning | Guide |
|---|---|---|
| `@azure/msal-react` | React SPA, redirect/popup | `implementation-nuances.md` → React + @azure/msal-react |
| `@azure/msal-angular` | Angular SPA | → Angular + @azure/msal-angular |
| `@azure/msal-browser` only | Vue or plain JS SPA | → Vue + @azure/msal-browser / Plain JavaScript + @azure/msal-browser |
| `next` + `@azure/msal-react` or NextAuth `AzureADB2CProvider` | Next.js | → Next.js |
| `Microsoft.Identity.Web` + `AddMicrosoftIdentityWebApi` | ASP.NET Core API | `backend-sdks.md` → .NET / ASP.NET Core |
| `Microsoft.Identity.Web` + `AddMicrosoftIdentityWebApp` | ASP.NET Core web app (server-side login) | `implementation-nuances.md` → Server-side web apps |
| `@azure/msal-node` / `passport-azure-ad` `OIDCStrategy` | Node server-side login | → Server-side web apps |
| `passport-azure-ad` `BearerStrategy`, `jwks-rsa` with `b2clogin.com` | Node API validation | `backend-sdks.md` → Node.js |
| `msal` (Python), PyJWT with B2C metadata | Python | `backend-sdks.md` → Python |
| `spring-cloud-azure-starter-active-directory-b2c` | Spring | `backend-sdks.md` → Java / Spring |
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
| `domain_hint` / `ClaimsProviderSelection` with `TargetClaimsExchangeId` per customer | Home realm discovery | Tenant email domains, or a tenant slug if the hint is a customer key |
| `ParseDomain` claims transformation + orchestration steps with `<Precondition>`s on the domain claim | Home realm discovery from the typed email, rules inside the policy | Each domain in a precondition → email domain on that customer's tenant (Routing key) |
| `<Domain>` element on a customer's `ClaimsProvider` | The value `domain_hint` matches for that IdP | Email domain or tenant slug, per Picking the tenant at sign-in |
| `RestfulProvider` profile whose output claim names an IdP or org (`identityProvider`, `idp`, `orgId`), followed by a step chosen by that claim | Home realm discovery through the customer's API | `implementation-nuances.md` → Organization lookup through an API connector |
| `amr` captured from a federated IdP + skip MFA precondition | MFA trusted from the customer IdP | Condition on `idpOIDCClaims.amr` |
| `AuthenticationContextReferenceClaimPattern` | `acr` vs `tfp` policy claim | Delete consumers |
| `<RelyingParty>` with `<Protocol Name="SAML2"/>`, `SubjectNamingInfo`, `Saml2AssertionIssuer` | B2C issues SAML to the customer's own SAML apps — check `NameID` source/format and output claim names | Descope SAML Federated App (`implementation-nuances.md` → B2C as a SAML IdP → Descope SAML app) |
| `<UserJourneyBehaviors>` (`SingleSignOn`, `SessionExpiryType`, `SessionExpiryInSeconds`) and JWT issuer metadata (`token_lifetime_secs`, `refresh_token_lifetime_secs`, `rolling_refresh_token_lifetime_secs`) | Session behavior and token lifetimes for that policy | Session Management, tenant / app overrides, Custom Refresh Duration (`implementation-nuances.md` → Session behavior and token lifetimes) |
| `<Localization Enabled="true">`, `<LocalizedResources>`, `<LocalizedString>` | Languages and translated strings per page | Flow localization overrides (`implementation-nuances.md` → Localization) |
| `<DisplayControl … UserInterfaceControlType="VerificationControl">` with a REST technical profile to an email provider; an `IdTokenHint` technical profile / `id_token_hint` input | Custom verification email; invitation journey | Messaging connector + templates; Descope invites (`implementation-nuances.md` → Invitations and email / SMS templates) |
| `<CryptographicKeys><Key Id="…" StorageReferenceId="B2C_1A_…"/>` | A policy key in use — the `Key Id` and its technical profile say what for | `implementation-nuances.md` → Policy key inventory |
| `Handler="…ConditionalAccessProtocolProvider…"` | Conditional Access evaluated inside the custom policy — only journeys that call it are affected | Flow conditions (+ MFA / block steps) |

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
| App registrations (frontends, APIs, daemons) | `GET https://graph.microsoft.com/v1.0/applications?$select=id,appId,displayName,identifierUris,api,requiredResourceAccess,spa,web,publicClient,passwordCredentials,keyCredentials` | `Application.Read.All` |
| Custom attributes | `GET https://graph.microsoft.com/v1.0/applications/<b2c-extensions-app object id>/extensionProperties` | `Application.Read.All` |
| Conditional Access policies | `GET https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies` | `Policy.Read.All` |
| Policy keys (metadata only) | `GET https://graph.microsoft.com/beta/trustFramework/keySets` | `TrustFrameworkKeySet.Read.All` |
| Groups and members (roles and organizations) | `GET https://graph.microsoft.com/v1.0/groups?$select=id,displayName,description`, then `GET .../groups/<id>/members?$select=id` | `GroupMember.Read.All` |
| User count | `GET https://graph.microsoft.com/v1.0/users/$count` with header `ConsistencyLevel: eventual` | `User.Read.All` |
| Users (for export) | See `implementation-nuances.md` → Exporting users from B2C | `User.Read.All` |

Notes:
- `beta` endpoints can change; fall back to asking the user for XML files or portal screenshots.
- Secrets can't be read back: identity provider client secrets return `****`; app registration
  `passwordCredentials` return `secretText: null` with only a short `hint`. Neither can be migrated.
- API connectors (`GET /beta/identity/apiConnectors`) require `APIConnectors.ReadWrite.All` (no read-only permission) — prefer asking the user to list them from the portal (User flows → API connectors).
- SAML enterprise IdPs exist only in custom policy XML, not in the identity providers list.

### App registration type → Descope app

The registration's platform type decides which OAuth grants it uses, and that decides the Descope
app. Classify every registration:

| B2C registration (Graph fields) | Grant today | Descope |
|---|---|---|
| `identifierUris` + `api.oauth2PermissionScopes` (**API**) | — (receives tokens) | Descope **Resource**; copy each scope `value` |
| `spa.redirectUris` (**SPA**) | Authorization code + PKCE | **Public** Inbound App (PKCE required). The Console creates Inbound Apps as confidential by default — switch it under Client Authentication, or the SPA can't refresh without a secret |
| `publicClient.redirectUris` (**mobile / desktop**) | Authorization code + PKCE | **Public** Inbound App + Descope native SDK |
| `web.redirectUris` + `passwordCredentials` / `keyCredentials`, calls the API (`requiredResourceAccess` → the API with delegated scopes, `type: "Scope"`) (**web app**) | Authorization code with a client secret or certificate | **Confidential** Inbound App |
| `web.redirectUris`, sign-in only (no API scopes) | Authorization code (or OIDC only) | Federated App (OIDC) or plain Descope SDK session — see Decision 1 |
| No redirect URIs + `passwordCredentials` / `keyCredentials` + application permissions (`requiredResourceAccess` with `type: "Role"`, requested as `<api>/.default`) (**daemon**) | Client credentials | **Confidential** Inbound App with the Client Credentials grant (public apps can't use it); application permissions become scopes on the Resource |
| `web.implicitGrantSettings.enableAccessTokenIssuance` or `enableIdTokenIssuance` = `true` | Implicit | Flag it: Inbound Apps don't offer the implicit grant. Move the app to authorization code + PKCE as part of the SDK swap |
| `b2c-extensions-app` | — | Custom attribute storage, not an app to migrate |

Client secrets and certificate private keys can't be read from Graph. A confidential Inbound App
gets a new secret unless the existing client ID and secret are imported through the Management
API ([docs.descope.com/migrate/oauth-clients](https://docs.descope.com/migrate/oauth-clients)).
Importing changes the project's Inbound App issuer to `/v1/apps/customized/<ProjectID>`.

### Sign-in method inventory

B2C defines sign-in methods in two places — the tenant's identity providers list and
`ClaimsProvider` technical profiles in custom policy XML — and each policy offers its own subset.
Neither source is complete (SAML IdPs and many custom OIDC IdPs exist only in XML; the tenant list can
hold IdPs no policy uses). Build one list from all three:
1. Graph `identityProviders` (tenant list)
2. Graph `b2cUserFlows?$expand=identityProviders`, plus the local account sign-in types (email,
   username, phone — ask, or read them in the portal under Identity providers → Local account, if
   Graph doesn't show them)
3. Each custom policy's `ClaimsProvider` technical profiles — count one only if a `UserJourney`
   reaches it through `ClaimsProviderSelection` / `ClaimsExchange` (base and extension files define
   profiles no journey uses)

Record which policies offer each method. Enable each method once at project level in Descope, then
show it only in the Flows that replace those policies.

### Customer organization discovery

B2C has no organization object. Customers model organizations with **groups**, a **custom
attribute** (`extension_CompanyId`, `extension_TenantId`), customer IdPs, or their own database
behind an API connector. Check all of them — a setup can use more than one, and the user's
triage answer can be wrong.

**Inputs:** groups (`groups?$select=id,displayName,description`) and members, joined to the user
export for email domains; custom attributes (`extensionProperties`) and their values from the user
export (list them in `$select`); relying party `OutputClaims`; search groups 6 and 14.

**Candidates:** every group, and every custom attribute whose name suggests an organization
(`org`, `tenant`, `company`, `customer`, `account`) or whose values pass the signals below.

| Signal | Customer boundary (→ tenant) | Functional role (→ role) |
|---|---|---|
| Spread across users | Each user has one value / one group of the set — they partition users | Users hold several; memberships overlap |
| Email domains | Most users with the same value share one email domain | Mixed domains |
| Number of distinct values or groups | Grows with customers, often large | Small, fixed (`Admin`, `Editor`, `Billing`) |
| Names / values | Company names or IDs (`Acme`, `C-1042`) | Job or permission names |
| Link to SSO | Lines up with one customer IdP or `domain_hint` value | None |
| Code usage | Filters data (`WHERE org_id = …`, tenant-scoped queries) | Allows or blocks actions (`IsInRole`, `[Authorize(Roles=…)]`) |
| In the token | Sent as an org claim (`tenant_id`, `org`) | Sent as `roles` / `groups` |

Classify each candidate:
- **Boundary** → a Descope tenant per distinct value or group.
- **Role** → a Descope role.
- **Both** — combined names (`Acme-Admins`), or a user in a boundary group plus a role group →
  tenant plus a **tenant role**.
- **Profile data** — an org-like attribute that is free text (`CompanyName` typed at sign-up),
  with spelling variants and no code filtering on it → keep as a custom attribute; ask before
  turning it into tenants.
- **Unclear** → ask.

Multi-valued attributes (comma-separated IDs) or users in several boundary groups mean users in
more than one organization — the Flow must pick the current tenant (`implementation-nuances.md`
→ Picking the tenant at sign-in).

Show the table of candidates with their evidence, then confirm with `AskUserQuestion` before the
import mapping is set. Import order: `implementation-nuances.md` → Importing organizations.
Organizations held in the customer's database: `implementation-nuances.md` → Organization lookup
through an API connector. The claim the app reads: `implementation-nuances.md` → Keeping the app's
organization claim.

### Tenants with only user flows

If `trustFramework/policies` returns nothing (or the user says they use only user flows), there
is no policy XML: skip Custom Policy XML Hints and read each user flow instead.

| What | Source |
|---|---|
| Sign-in methods | `b2cUserFlows?$expand=identityProviders` (Sign-in method inventory) |
| Sign-up attributes collected | `GET .../b2cUserFlows/<id>/userAttributeAssignments` |
| API connectors | Ask the user (portal → User flow → API connectors). Graph's `b2cUserFlows/<id>/apiConnectorConfiguration` needs `IdentityUserFlow.ReadWrite.All` — no read-only permission, so don't request it |
| Token claims (Application claims) | **Not in Graph.** Ask for each user flow's Application claims list (portal → User flow → Application claims), or decode a real token from each user flow |
| Session, MFA, password complexity, page layouts | Portal, per user flow — ask |

User flows can't route by organization (no per-customer IdP selection, no `domain_hint` logic of
their own), so any customer organizations live in groups, custom attributes, an API connector, or
the app — run Customer organization discovery on those.

---

## Out-of-Scope Detection

Stop and confirm scope if you find:

| Signal | Product | Action |
|---|---|---|
| Authority `https://<tenant>.ciamlogin.com` | Microsoft Entra External ID | Out of scope — different product |
| Authority `https://login.microsoftonline.com/<tenant>` with no B2C policy, workforce app roles, groups claims | Workforce Microsoft Entra ID | Out of scope |
| `login.microsoftonline.com/<tenant>.onmicrosoft.com/<policy>` (legacy B2C endpoint) | Azure AD B2C (old endpoint) | In scope — treat as `b2clogin.com` |
| Azure AD B2B guest invitations | Workforce B2B | Out of scope |
| Generic OIDC library (`angular-auth-oidc-client`, `oidc-client-ts`, `openid-client`, `passport-openidconnect`, `AddOpenIdConnect`) pointed at a non-Microsoft authority | Another identity provider | Out of scope — name the matching migration skill (SKILL.md Part 1.5) |

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

### Customer organizations
| Source (group / attribute) | Name | Distinct values | Evidence | Classification | Descope |
|---|---|---|---|---|---|
| Group set | `Acme`, `Globex`, … (212) | 212 | One group per user; 96% share an email domain; data filtered by group ID | Boundary | Tenants |
| Attribute | `extension_Role` | 3 | `Admin` / `User` / `Viewer`; `IsInRole` checks | Role | Roles |

### Enterprise SSO connections
| Customer | IdP | Protocol | Routing key (domain / `domain_hint` / slug) | Email domain(s) | ACS / redirect URL host | Signed requests / encrypted assertions | OIDC secret available outside B2C | MFA behavior | Cutover result |
|---|---|---|---|---|---|---|---|---|---|
| Acme | Okta | SAML | email domain | acme.com | login.contoso.com | No | n/a | Trust IdP | May move without IdP changes |
| Globex | Entra ID | OIDC | `domain_hint=globex` → slug | globex.com | contoso.b2clogin.com | n/a | No | B2C adds MFA | Admin updates redirect URI + new secret |
```
