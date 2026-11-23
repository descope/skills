# FusionAuth Detection Patterns

Codebase search commands for SKILL.md Part 2 → Step 1 (Codebase Analysis). Run them before the
Step 0 triage questions so the questions can be pre-filled from what the scan found.

## Contents

- Search commands (1–9)
- Known FusionAuth env vars (inside search 5)

## Search commands

Run these searches during SKILL.md Part 2 → Step 1. Adapt file extensions to the user's language and platform.

> **Portability note.** These use POSIX basic regex so they work with both GNU and BSD `grep` (macOS
> ships BSD grep, where GNU extensions like `\b` silently fail to match). If `rg` is available it is
> faster, but translate the alternations to `rg -e` syntax rather than pasting these verbatim.

> **FusionAuth is OIDC-first.** Many FusionAuth apps contain **no FusionAuth SDK at all** — they use a
> generic OAuth/OIDC library (`next-auth`, `openid-client`, `passport-openidconnect`, Spring Security,
> ASP.NET `AddOpenIdConnect`, `authlib`, `golang.org/x/oauth2`) pointed at the FusionAuth issuer. Those
> show up only in searches 4 and 5 (issuer URLs, `/oauth2/` paths, env vars). Do not conclude
> "FusionAuth is barely used" because search 2 and 3 come back empty.

```bash
# 1. Broad sweep — every FusionAuth package, import, config, and domain reference
grep -rni "fusionauth\|fusion_auth\|fusion-auth" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.mjs" --include="*.cjs" --include="*.vue" --include="*.html" --include="*.svelte" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.php" --include="*.java" \
  --include="*.kt" --include="*.kts" --include="*.cs" --include="*.csproj" --include="*.swift" \
  --include="*.dart" --include="*.gradle" --include="*.plist" --include="*.xml" \
  --include="*.json" --include="*.toml" --include="*.properties" --include="*.ftl" \
  --include="*.tf" --include="*.tfvars" --include="*.yml" --include="*.yaml" \
  --include="*.env*" --include="Dockerfile" --include="Podfile" --include="Gemfile" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist --exclude-dir=venv \
  --exclude-dir=build --exclude-dir=.gradle --exclude-dir=Pods --exclude-dir=vendor \
  . 2>/dev/null
```

```bash
# 2. Frontend SDK surface — React / Vue / Angular SDKs and Auth.js
grep -rn "FusionAuthProvider\|useFusionAuth\|FusionAuthLoginButton\|FusionAuthLogoutButton\|FusionAuthRegisterButton\|FusionAuthAccountButton\|RequireAuth\|RequireAnonymous\|Unauthenticated\|withFusionAuth\|createFusionAuth\|FusionAuthVuePlugin\|FusionAuthModule\|FusionAuthService\|fa-login\|fa-logout\|fa-register\|fusionauth/react-sdk\|fusionauth/vue-sdk\|fusionauth/angular-sdk\|startLogin\|startLogout\|startRegister\|manageAccount\|serverUrl\|shouldAutoRefresh\|shouldAutoFetchUserInfo\|nextCookieAdapter\|nuxtUseCookie\|useDpop\|dpopFetch\|providers/fusionauth" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.mjs" --include="*.cjs" --include="*.vue" --include="*.html" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist \
  . 2>/dev/null
```

`RequireAuth`, `Unauthenticated`, and `startLogin` are generic enough to collide with app code or
other libraries — confirm each hit imports from a FusionAuth package. `useDpop` matters: without it
the SDK talks to a **Hosted Backend** (`/app/login`, `/app/callback`, `/app/refresh`, `/app/me`,
`/app/logout`, either FusionAuth's built-in one or the team's own server) and keeps tokens in
`app.at` / `app.rt` / `app.idt` / `app.at_exp` cookies; with it, tokens live in the browser. `providers/fusionauth` catches both
`next-auth/providers/fusionauth` and `@auth/core/providers/fusionauth`, which is how most Next.js
apps integrate FusionAuth (there is no official FusionAuth Next.js SDK).

```bash
# 3. Backend client libraries — Management API usage and token handling
grep -rn "FusionAuthClient\|fusionauth-client\|typescript-client\|fusionauth_client\|go-client/pkg/fusionauth\|fusionauth.NewClient\|io.fusionauth\|FusionAuth.Client\|FusionAuthSyncClient\|retrieveUser\|retrieveUserByEmail\|searchUsersByQuery\|createUser\|register(\|createRegistration\|updateRegistration\|exchangeOAuthCodeForAccessToken\|exchangeRefreshTokenForAccessToken\|validateJWT\|retrieveJWTPublicKeys\|issueJWT\|retrieveUserInfoFromAccessToken\|ClientResponse" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.go" --include="*.rb" --include="*.php" \
  --include="*.java" --include="*.kt" --include="*.cs" \
  --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=build --exclude-dir=vendor \
  . 2>/dev/null
```

Every `FusionAuthClient` call is a **Management API** call made with an API key. Sort them into two
buckets while recording: calls that only validate or read the signed-in user (become Descope session
validation or `useUser()`), and administrative calls (become Descope Management SDK calls with a
Management Key, or a Widget).

```bash
# 4. Token claims, cookies, OAuth endpoints, and hand-rolled verification
#    (generic-OIDC apps show up only here and in search 5)
grep -rn "applicationId\|\"roles\"\|\.roles\b\|claims\.roles\|preferred_username\|email_verified\|authenticationType\|\"tid\"\|\.tid\b\|app\.at\|app\.rt\|app\.idt\|app\.at_exp\|/oauth2/authorize\|/oauth2/token\|/oauth2/logout\|/oauth2/userinfo\|/oauth2/introspect\|/.well-known/jwks\|openid-configuration\|/app/login\|/app/callback\|/app/refresh\|/app/me\|/app/logout\|/api/login\|/api/jwt/refresh\|/api/user\|HS256\|jwt.verify\|jwt.decode\|jose\|JwtBearer\|AddOpenIdConnect\|issuer-uri\|issuerUri\|IssuerUri" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" --include="*.rb" --include="*.php" \
  --include="*.go" --include="*.java" --include="*.kt" --include="*.cs" \
  --include="*.json" --include="*.yml" --include="*.yaml" --include="*.properties" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build --exclude-dir=vendor \
  . 2>/dev/null
```

Look hardest at `HS256` and `jwt.verify(token, <secret>)`. FusionAuth installs set up through
Kickstart (or before 1.50.0) sign tokens with an HMAC key by default, and HMAC keys never appear in
JWKS — so those backends validate with a shared secret and will reject every Descope token without a
clear error. Also note any `aud` / `applicationId` check: FusionAuth puts the Application (client) ID
in `aud`, and Descope session tokens have no `aud` by default.

```bash
# 5. Environment variables and configuration files
grep -rn "FUSIONAUTH\|FusionAuth__\|fusionauth\.\(url\|issuer\|client\|api\)" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.py" --include="*.go" --include="*.rb" --include="*.php" --include="*.java" --include="*.kt" \
  --include="*.cs" --include="*.swift" --include="*.dart" --include="*.gradle" \
  --include="*.properties" --include="appsettings*.json" \
  --include="*.env*" --include="*.yml" --include="*.yaml" --include="Dockerfile" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=build \
  . 2>/dev/null

# FusionAuth env var naming is NOT standardized — apps invent their own. Common ones:
#
# App-side (quickstarts and community conventions):
#   FUSIONAUTH_URL / FUSIONAUTH_BASE_URL / FUSIONAUTH_ISSUER / FUSIONAUTH_SERVER_URL,
#   FUSIONAUTH_CLIENT_ID / FUSIONAUTH_APPLICATION_ID, FUSIONAUTH_CLIENT_SECRET,
#   FUSIONAUTH_API_KEY, FUSIONAUTH_TENANT_ID, FUSIONAUTH_REDIRECT_URI,
#   NEXT_PUBLIC_FUSIONAUTH_*, VITE_FUSIONAUTH_*, REACT_APP_FUSIONAUTH_*
# Auth.js / NextAuth:
#   AUTH_FUSIONAUTH_ID, AUTH_FUSIONAUTH_SECRET, AUTH_FUSIONAUTH_ISSUER,
#   AUTH_FUSIONAUTH_TENANT_ID (or the FUSIONAUTH_* names passed to FusionAuthProvider),
#   NEXTAUTH_SECRET / AUTH_SECRET, NEXTAUTH_URL / AUTH_URL
# Server (self-hosted deployment, not the app — these mean the team RUNS FusionAuth):
#   FUSIONAUTH_APP_URL, FUSIONAUTH_APP_KICKSTART_FILE, FUSIONAUTH_APP_MEMORY,
#   FUSIONAUTH_APP_RUNTIME_MODE, FUSIONAUTH_APP_SILENT_MODE, DATABASE_URL,
#   DATABASE_ROOT_USERNAME, DATABASE_USERNAME, SEARCH_TYPE, SEARCH_SERVERS
# Spring Boot: spring.security.oauth2.client.provider.fusionauth.issuer-uri
# .NET: "FusionAuth": { "Authority", "ClientId", ... } in appsettings.json
#
# NOTE: the server-side variables decide which password-export route exists. A team that runs
# FusionAuth (docker-compose with fusionauth/fusionauth-app, Helm, kickstart) can read password hashes
# straight from its own database. A FusionAuth Cloud customer cannot — see SKILL.md Step 0.5.
```

```bash
# 6. Self-hosted FusionAuth infrastructure (compose, Helm, kickstart, themes in the repo)
grep -rni "fusionauth/fusionauth-app\|fusionauth-app:\|fusionauth/fusionauth-search\|helm.*fusionauth\|kickstart\|FUSIONAUTH_APP_KICKSTART_FILE\|opensearch\|elasticsearch" \
  --include="*.yml" --include="*.yaml" --include="*.env*" --include="*.tf" \
  --include="*.tpl" --include="Dockerfile" --include="Makefile" --include="*.json" \
  --exclude-dir=node_modules --exclude-dir=build \
  . 2>/dev/null

find . -maxdepth 5 \( -name "kickstart*.json" -o -name "*.ftl" -o -iname "*fusionauth*theme*" \) \
  ! -path "*/node_modules/*" 2>/dev/null
```

A `kickstart.json` is a gift: it lists tenants, applications, roles, lambdas, keys, and webhooks the
team expects to exist — a configuration inventory you don't have to ask for. `.ftl` files are
FreeMarker theme templates; each customized template is login UI that becomes a Flow screen.

```bash
# 7. Mobile SDKs and native OAuth configuration
grep -rn "FusionAuth\|fusionauth\|AuthorizationManager\|AppAuth\|flutter_appauth\|react-native-app-auth\|OIDAuthorizationService\|net.openid.appauth\|oauth2/authorize\|redirectUrl.*callback" \
  --include="*.swift" --include="*.kt" --include="*.java" --include="*.dart" \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.xml" \
  --include="*.plist" --include="*.gradle" --include="*.kts" \
  --exclude-dir=node_modules --exclude-dir=Pods --exclude-dir=build \
  . 2>/dev/null
```

Mobile FusionAuth apps frequently use AppAuth (iOS/Android), `flutter_appauth`, or
`react-native-app-auth` against the FusionAuth issuer rather than a FusionAuth SDK. `AppAuth` alone is
not evidence of FusionAuth — confirm the issuer it is configured with.

```bash
# 8. Dependency manifests
find . -maxdepth 4 \( \
  -name "package.json" -o -name "go.mod" -o -name "requirements.txt" -o \
  -name "pyproject.toml" -o -name "Pipfile" -o -name "pom.xml" -o -name "build.gradle" -o \
  -name "build.gradle.kts" -o -name "Package.swift" -o -name "Podfile" -o \
  -name "pubspec.yaml" -o -name "*.csproj" -o -name "Podfile.lock" -o \
  -name "Gemfile" -o -name "composer.json" -o \
  -name "libs.versions.toml" -o -name "settings.gradle" \
\) ! -path "*/node_modules/*" ! -path "*/build/*" \
  -exec grep -il "fusionauth\|next-auth\|@auth/\|openid-client\|passport-openidconnect\|oauth2-client\|OpenIdConnect\|authlib\|AppAuth" {} \;
```

`grep -il`, not `-l`: Podfiles and Gradle files mix case. The second half of the alternation
catches generic-OIDC apps; open each hit and confirm it is configured against FusionAuth.

```bash
# 9. Webhook handlers and lambda source kept in the repo
#    (often a separate service — ask if nothing is found)
grep -rni "user\.create\|user\.update\|user\.delete\|user\.deactivate\|user\.reactivate\|user\.login\.success\|user\.login\.failed\|user\.registration\.\|user\.email\.verified\|user\.password\.\|user\.two-factor\|group\.member\|entity\.create\|jwt\.refresh\|X-FusionAuth-Signature-JWT\|request_body_sha256\|function populate(\|function reconcile(\|function validate(\|jwt, user, registration" \
  --include="*.ts" --include="*.js" --include="*.py" --include="*.go" --include="*.rb" --include="*.php" \
  --include="*.java" --include="*.kt" --include="*.cs" \
  --exclude-dir=node_modules --exclude-dir=build \
  . 2>/dev/null
```

Webhook event names are matched by prefix here; confirm the exact `type` strings against the
FusionAuth webhook event reference before relying on them. `function populate(jwt, user,
registration, context)` is the signature of a JWT populate lambda; teams that
manage lambdas as code keep them as `.js` files and upload them in CI or kickstart. Each one encodes
custom claims the app reads — map them to a Descope JWT Template before the claim reads are touched.
Lambdas that only live in the FusionAuth admin UI won't appear here: export them with
`GET /api/lambda` (SKILL.md Step 3 → *User & Tenant Data* has the export recipe).
