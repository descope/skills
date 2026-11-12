# Frontegg Detection Patterns

Codebase search commands for SKILL.md Part 2 → Step 1 (Codebase Analysis). Run them before the
Step 0 triage questions so the questions can be pre-filled from what the scan found.

## Contents

- Search commands (1–8)
- Known Frontegg env vars (inside search 5)

## Search commands

Run these searches during SKILL.md Part 2 → Step 1. Adapt file extensions to the user's language and platform.

> **Portability note.** These use POSIX basic regex so they work with both GNU and BSD `grep` (macOS
> ships BSD grep, where GNU extensions like `\b` silently fail to match). If `rg` is available it is
> faster, but translate the alternations to `rg -e` syntax rather than pasting these verbatim.

```bash
# 1. Broad sweep — every Frontegg package, import, config, and domain reference
grep -rni "frontegg" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.mjs" --include="*.cjs" --include="*.vue" --include="*.html" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.java" \
  --include="*.kt" --include="*.kts" --include="*.cs" --include="*.swift" \
  --include="*.dart" --include="*.gradle" --include="*.plist" --include="*.xml" \
  --include="*.json" --include="*.toml" --include="*.properties" \
  --include="*.entitlements" --include="*.pbxproj" --include="*.podspec" \
  --include="*.tf" --include="*.tfvars" --include="*.yml" --include="*.yaml" \
  --include="*.env*" --include="Dockerfile" --include="Podfile" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=venv \
  --exclude-dir=build --exclude-dir=.gradle --exclude-dir=Pods \
  . 2>/dev/null
```

```bash
# 2. Frontend SDK surface — providers, hooks, portal, entitlements, step-up
grep -rn "FronteggProvider\|FronteggAppProvider\|FronteggAppRouter\|FronteggRouter\|withFronteggApp\|FronteggApiMiddleware\|handleSessionOnEdge\|FronteggAppModule\|FronteggAuthService\|FronteggAppService\|useFrontegg\|useAuth(\|useAuthUser\|useAuthUserOrNull\|useAuthActions\|useLoginWithRedirect\|useIsAuthenticated\|useTenantsActions\|tenantsState\|ContextHolder\|AdminPortal\|useEntitlements\|useFeatureEntitlements\|usePermissionEntitlements\|NotEntitledJustification\|useStepUp\|useIsSteppedUp\|SteppedUpContent\|AuthorizedContent\|switchTenant\|requestAuthorize\|loginWithRedirect\|getAppUserSession\|getAppUserTokens\|withSSRSession\|contextOptions\|hostedLoginBox\|authOptions\|keepSessionAlive\|enableSessionPerTenant\|disableSilentRefresh\|customLoginBox" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.mjs" --include="*.cjs" --include="*.vue" --include="*.html" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
  . 2>/dev/null
```

Step-up symbols matter here: step-up is a SKILL.md Step 0 triage question, and Frontegg ships step-up
quickstarts for React, Angular, Vue, and Vanilla JS. Without those patterns a step-up app is
invisible to codebase analysis.

```bash
# 3. Backend SDK surface — middleware, token validation, entitlements client
grep -rn "FronteggContext\|withAuthentication\|IdentityClient\|validateIdentityOnToken\|FronteggAuthenticator\|AuditsClient\|EventsClient\|frontegg.flask\|frontegg.fastapi\|FronteggSecurity\|with_authentication\|frontegg/go-sdk\|frontegg.Init\|WithAuthentication\|UserFromContext\|ValidateToken\|HostedLogin\|CodeExchange\|EntitlementsClientFactory\|engineEndpoint\|engineToken\|isEntitledTo\|lookupTargetEntities\|lookupEntities\|entitlements-client" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.go" \
  --include="*.java" --include="*.kt" --include="*.cs" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=build \
  . 2>/dev/null
```

```bash
# 3b. Entitlements-engine INFRASTRUCTURE — lives in compose/Helm/env files, not source.
#     Both generations show up in the wild; detect either.
grep -rni "e10s\|e10s-engine-sync\|authzed/spicedb\|spicedb\|entitlements-engine\|entitlements-agent\|SPICEDB_ADDRESS\|SPICEDB_GRPC_PRESHARED_KEY\|ENTITLEMENTS_ENGINE_TOKEN\|FRONTEGG_CLIENT_CREDENTIALS_OAUTH\|POLLING_MIN_DELAY\|charts.frontegg.com" \
  --include="*.yml" --include="*.yaml" --include="*.env*" --include="*.tf" \
  --include="*.tpl" --include="Dockerfile" --include="Makefile" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.go" --include="*.java" \
  --exclude-dir=node_modules --exclude-dir=build \
  . 2>/dev/null
```

The current stack is the Frontegg entitlements engine (`frontegg/entitlements-engine`, deployed via
Helm; Frontegg's local docker-compose example uses `frontegg/e10s-engine-sync` plus CockroachDB)
against an existing SpiceDB, called through `@frontegg/e10s-client`. The older stack, which Frontegg
calls legacy, is the `frontegg/entitlements-agent` PDP container. A real estate often runs both, so
match either.
Note these tokens live in `docker-compose.yml`, Helm values, and `.env` files — greping only source
extensions for them finds nothing.

```bash
# 4. Token claims, cookies, headers, and hand-rolled verification
#    (.NET and Java apps have no Frontegg SDK — they show up only here)
grep -rn "tenantId\|tenantIds\|applicationId\|profilePictureUrl\|email_verified\|vendorMetadata\|fe_refresh\|fe_session\|X-API-KEY\|acr_values\|amr\|auth_time\|max_age\|jwks\|JwtBearer\|jwt.verify\|jwt.decode\|Authority.*frontegg\|\.frontegg\.com" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" \
  --include="*.go" --include="*.java" --include="*.kt" --include="*.cs" \
  --include="*.json" --include="*.yml" --include="*.yaml" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null
```

```bash
# 5. Environment variables and configuration files
grep -rn "FRONTEGG_" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.java" --include="*.kt" \
  --include="*.cs" --include="*.swift" --include="*.dart" --include="*.gradle" \
  --include="*.env*" --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null

# Known Frontegg env vars to expect:
#
# Core (all stacks):
#   FRONTEGG_CLIENT_ID, FRONTEGG_API_KEY, FRONTEGG_BASE_URL, FRONTEGG_APP_URL,
#   FRONTEGG_APP_ID, FRONTEGG_CLIENT_SECRET
# Logging: FRONTEGG_DEBUG_LEVEL (Node SDK), FRONTEGG_DEBUG (Python SDK)
# Next.js specific:
#   FRONTEGG_COOKIE_NAME, FRONTEGG_ENCRYPTION_PASSWORD, FRONTEGG_HOSTED_LOGIN,
#   FRONTEGG_JWT_PUBLIC_KEY, FRONTEGG_SHARED_SECRET, FRONTEGG_COOKIE_DOMAIN,
#   FRONTEGG_COOKIE_SAME_SITE, FRONTEGG_SECURE_JWT_ENABLED,
#   FRONTEGG_REWRITE_COOKIE_BY_APP_ID, FRONTEGG_FORWARD_IP, FRONTEGG_SSG_EXPORT,
#   FRONTEGG_TEST_URL, FRONTEGG_HOSTED_LOGIN_CALLBACK_ON_APP_URL,
#   DISABLE_INITIAL_PROPS_REFRESH_TOKEN
# Service endpoint overrides (backend SDKs):
#   FRONTEGG_API_GATEWAY_URL, FRONTEGG_IDENTITY_SERVICE_URL,
#   FRONTEGG_ENTITLEMENTS_SERVICE_URL, FRONTEGG_AUDITS_SERVICE_URL,
#   FRONTEGG_EVENT_SERVICE_URL, FRONTEGG_OAUTH_SERVICE_URL,
#   FRONTEGG_VENDORS_SERVICE_URL, FRONTEGG_METADATA_SERVICE_URL,
#   FRONTEGG_AUTHENTICATION_SERVICE_URL
# Mobile:
#   FRONTEGG_DOMAIN / FRONTEGG_CLIENT_ID / FRONTEGG_APPLICATION_ID (Android buildConfigField)
#
# NOTE: FRONTEGG_CLIENT_SECRET is a CORE Next.js variable as well as an entitlements-engine
# one. Seeing it does NOT imply ReBAC is in use — check search 3b before concluding that.
#
# NOTE: React, Vue, Angular, and Vanilla JS quickstarts hardcode baseUrl/clientId/appId
# inline in `contextOptions` rather than reading env vars. VITE_FRONTEGG_* and
# NEXT_PUBLIC_FRONTEGG_* are community conventions, not official — if search 5 returns
# nothing, rely on search 2 (`contextOptions`) instead of concluding Frontegg is unused.
```

```bash
# 6. Mobile SDK configuration and URL patterns
grep -rn "FronteggSwift\|FronteggWrapper\|FronteggApp\|FronteggAuth\|AbstractFronteggController\|com.frontegg.android\|com.frontegg.sdk\|EmbeddedAuthActivity\|HostedAuthActivity\|AuthenticationActivity\|frontegg_flutter\|FronteggProvider\|frontegg_domain\|frontegg_client_id\|oauth/account/login\|oauth/account/redirect\|oauth/callback\|oauth/logout\|user/token/refresh\|account/login\|account/sign-up\|account/logout\|oauth/portal" \
  --include="*.swift" --include="*.kt" --include="*.java" --include="*.dart" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.xml" \
  --include="*.plist" --include="*.gradle" \
  --exclude-dir=node_modules --exclude-dir=Pods --exclude-dir=build \
  . 2>/dev/null

find . -maxdepth 4 -name "Frontegg.plist" ! -path "*/Pods/*" 2>/dev/null
```

```bash
# 7. Dependency manifests
find . -maxdepth 4 \( \
  -name "package.json" -o -name "go.mod" -o -name "requirements.txt" -o \
  -name "pyproject.toml" -o -name "pom.xml" -o -name "build.gradle" -o \
  -name "build.gradle.kts" -o -name "Package.swift" -o -name "Podfile" -o \
  -name "pubspec.yaml" -o -name "*.csproj" -o -name "Podfile.lock" -o \
  -name "libs.versions.toml" -o -name "settings.gradle" \
\) ! -path "*/node_modules/*" ! -path "*/build/*" \
  -exec grep -il "frontegg" {} \;
```

`grep -il`, not `-l`: a `Podfile` contains `pod 'FronteggSwift'` with a capital F, so a
case-sensitive search silently skips every CocoaPods project.

```bash
# 8. Prehook and webhook handlers (often a separate service — ask if nothing is found)
#    All 14 prehook events, and webhook prefixes that "frontegg.user." alone would miss.
grep -rni "prehook\|pre-hook\|AUTH_INITIATED\|USER_SIGNUP\|USER_INVITE\|USER_UPDATE\|USER_DELETE\|CREATE_TENANT\|UPDATE_TENANT\|DELETE_TENANT\|JWT_GENERATION\|SOCIAL_LOGIN_AUTH\|OIDC_AUTH\|SAML_AUTH\|SEND_SMS\|SIGN_UP_USER_POOL\|x-webhook-secret\|frontegg\.user\|frontegg\.tenant\|frontegg\.group\|frontegg\.scim\|frontegg\.account" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.go" \
  --include="*.java" --include="*.kt" --include="*.cs" \
  --exclude-dir=node_modules --exclude-dir=build \
  . 2>/dev/null
```

Note the webhook prefixes drop the trailing dot: `frontegg\.user\.` does **not** match
`frontegg.userApiToken.created`, and `frontegg\.tenant\.` misses `frontegg.tenantApiToken.*`.
