# Detection Patterns Reference

Use these patterns during Phase 1 to scan the codebase for all Cognito usage. Run every grep excluding `node_modules`, `.git`, `__pycache__`, `dist`, `.next`, and `build` directories.

---

## 1.1 Architecture Glob Patterns

Read these files first to understand overall system architecture before touching auth-specific files:

```
**/package.json                          (exclude node_modules)
**/requirements.txt
**/pyproject.toml
**/Pipfile
**/docker-compose.yml
**/docker-compose.*.yml
**/serverless.yml
**/template.yaml
**/cdk/**/*.ts
**/.github/workflows/*.yml
**/Makefile
**/Dockerfile
```

From these files, determine: architecture type (monolith / microservices / serverless / BFF / monorepo), tech stack, service boundaries, deployment model, and monorepo package structure.

---

## 1.2 Package Detection

**JavaScript/TypeScript** — read each `package.json`:

| Package | Stack | Notes |
|---|---|---|
| `aws-amplify` | React/Next.js frontend | `< 6.x` = v5 API, `>= 6.x` = v6 API |
| `@aws-amplify/auth` | React frontend | Usually alongside `aws-amplify` |
| `@aws-amplify/ui-react` | React frontend | Provides `<Authenticator>` component |
| `amazon-cognito-identity-js` | Frontend (lower-level) | Direct `CognitoUserPool`/`CognitoUser` usage |
| `aws-jwt-verify` | Node.js backend | `CognitoJwtVerifier` token validation |
| `@aws-sdk/client-cognito-identity-provider` | Node.js backend | Admin user management |
| `@aws-sdk/credential-providers` | Node.js backend | Identity Pool usage |
| `@aws-sdk/client-cognito-identity` | Node.js backend | Identity Pool usage |
| `next-auth` | Next.js | Check for Cognito provider — different migration path |
| `react-native` or `expo` | Mobile | Alongside any Cognito package = Pattern K |

**Python** — read `requirements.txt`, `pyproject.toml`, `Pipfile`:

| Package | Notes |
|---|---|
| `cognitojwt` | Token decode/verify |
| `python-jose` | Manual JWKS-based verification |
| `boto3` | Admin user management (may also serve other AWS purposes) |

---

## 1.3 Cognito Pattern Detection (Patterns A–K)

Patterns are not mutually exclusive — multiple can be active simultaneously.

### Pattern A — Amplify v5 + Custom UI

```
Grep: Auth\.signIn\(|Auth\.signUp\(|Auth\.currentSession\(|Hub\.listen
Files: .ts .tsx .js .jsx
```

### Pattern B — Amplify v6 + Custom UI

```
Grep: from 'aws-amplify/auth'
Grep: from "aws-amplify/auth"
Grep: fetchAuthSession\(|getCurrentUser\(
Files: .ts .tsx .js .jsx
```

### Pattern C — Amplify Authenticator Component (lowest migration complexity)

```
Grep: withAuthenticator\(|<Authenticator
```

### Pattern D — Cognito Hosted UI (OAuth PKCE redirect)

```
Grep: oauth:                                        (in Amplify.configure calls)
Grep: redirectSignIn|redirectSignOut|responseType.*code
Grep: Auth\.federatedSignIn\(\)                     (no provider argument)
Grep: amazoncognito\.com                            (direct hosted UI domain references)
```

**Sub-check for D2 (Cognito as OAuth Authorization Server)**:

```
Grep: ResourceServer|resource_server|customScopes|client_credentials
Grep: COGNITO_DOMAIN|cognitoDomain|auth\.<region>\.amazoncognito\.com
```

- **D1 — Self-use only** (own login page): migrate to embedded Descope component
- **D2 — OAuth Authorization Server** (external clients redirect to Cognito): migrate to Descope as OIDC provider

### Pattern E — Federated Social / SAML through Cognito

```
Grep: federatedSignIn.*provider|'Google'|'Facebook'|'Apple'|CognitoHostedUI   (case-sensitive)
Grep: saml|SAML                                     (in amplify/backend/auth/**)
Glob: **/amplify/backend/auth/**/*.json
```

**Sub-check for E2 (multi-tenant SAML)**:

```
Grep: email\.split\('@'\)|getEmailDomain|identityProvider.*domain|tenant.*saml|saml.*tenant
Grep: identity_provider=                            (in redirect URLs or backend logic)
Grep: pre-signup|pre_signup                         (Lambda for IdP domain validation)
```

- **E1 — Single SAML IdP**: one org, one IdP
- **E2 — Multi-tenant SAML**: email domain → tenant → IdP routing

### Pattern F — Low-level amazon-cognito-identity-js

```
Grep: CognitoUserPool\(|new CognitoUser\(|AuthenticationDetails\(|authenticateUser\(
```

### Pattern G — Cognito Identity Pools (AWS IAM credentials)

```
Grep: IdentityPoolId|CognitoIdentityCredentials|fromCognitoIdentityPool
Grep: identityPoolId                                (in Amplify.configure blocks)
```

### Pattern H — NextAuth.js with Cognito Provider

```
Grep: CognitoProvider|cognito.*next-auth|next-auth.*cognito   (case-insensitive)
Glob: **/pages/api/auth/[...nextauth].*
Glob: **/app/api/auth/[...nextauth].*
```

### Pattern I — M2M / Service-to-Service (Client Credentials)

```
Grep: client_credentials|grant_type.*client_credentials
Grep: oauth2/token                                  (without user context)
```

### Pattern J — Multi-tenant

```
Grep: tenantId|tenant_id                            (near auth or user context)
Grep: cognito:groups                                (used for tenant routing, not just roles)
```

Also check `.env` files for multiple `COGNITO_USER_POOL_ID` variants → multiple pools.

### Pattern K — React Native / Mobile

Detected by: `react-native` or `expo` in `package.json` alongside any Cognito package.

---

## 1.4 Special Behaviors Detection

### App Client secret (affects JIT migration)

```
Grep: SECRET_HASH|secretHash|getSecretHash|HMAC    (near Cognito auth calls)
Grep: clientSecret|COGNITO_CLIENT_SECRET           (in .env files)
```

### Custom auth challenge Lambda triggers (complex manual migration)

```
Glob: **/define-auth-challenge*
Glob: **/create-auth-challenge*
Glob: **/verify-auth-challenge*
Grep: DefineAuthChallenge|CreateAuthChallenge|VerifyAuthChallengeResponse
```

### Pre-token-generation Lambda (custom JWT claims → Descope JWT Templates)

```
Grep: TokenGeneration_Authentication|claimsOverrideDetails|claimsToAddOrOverride
Glob: **/pre-token-generation*
```

### Device tracking / remembered devices (no Descope equivalent)

```
Grep: rememberDevice\(|forgetDevice\(|Auth\.rememberDevice|getDevice\(
```

### FORCE_CHANGE_PASSWORD

Surfaces in migration tool dry-run output. Note presence now — these users cannot use password sign-in after migration and must be routed to magic link or OTP.

### Custom Cognito attributes

```
Grep: custom:                                       (catches custom:department, custom:role, etc.)
```

---

## 1.5 Full Project Scan

Run all patterns below across the full project:

```
Grep: aws-amplify|@aws-amplify|amazon-cognito-identity-js|aws-jwt-verify|CognitoJwtVerifier|cognitojwt|python-jose

Grep: Auth\.signIn|Auth\.signOut|Auth\.signUp|Auth\.currentAuthenticatedUser|Auth\.currentSession|Auth\.forgotPassword|Auth\.changePassword|Auth\.updateUserAttributes|Auth\.deleteUser|Auth\.resendSignUp|Auth\.confirmSignUp

Grep: fetchAuthSession|getCurrentUser|signIn\(|signOut\(

Grep: Hub\.listen|Amplify\.configure|withAuthenticator|<Authenticator

Grep: federatedSignIn|CognitoHostedUI

Grep: CognitoUserPool|CognitoUser|AuthenticationDetails|authenticateUser

Grep: cognitoVerifier\.verify|CognitoJwtVerifier\.create

Grep: cognitojwt\.decode|python_jose|from jose

Grep: cognito:groups|cognito:username|cognito:roles

Grep: USER_POOL_ID|UserPoolId|userPoolId|COGNITO_APP_CLIENT_ID|userPoolWebClientId

Grep: IdentityPoolId|CognitoIdentityCredentials|fromCognitoIdentityPool
```

Read each file found. Understand the pattern — do not just collect file names.

---

## 1.6 Lambda Trigger Files

```
Grep: exports.handler\s*=                          (in cognito/, triggers/, lambda/, functions/)
Grep: def handler\(event                           (in same directories)
Glob: **/cognito-triggers/**
Glob: **/lambda-triggers/**
```

---

## 1.7 Environment Variable Files

```
Glob: **/.env*                                     (exclude .env.example)
Glob: **/amplify/team-provider-info.json
Glob: **/amplify/backend/auth/**
```

Read all `.env` files. Note whether `COGNITO_CLIENT_SECRET` is present.

---

## 1.8 API Gateway Configuration

```
Grep: CognitoUserPoolsAuthorizer|UserPoolArn|CognitoAuthorizer
Files: serverless.yml, template.yaml, cdk/**
Glob: **/serverless.yml
Glob: **/template.yaml
Glob: **/cdk/**/*.ts
```

---

## 1.9 Cross-Cutting Dependency Analysis

Go deeper than the auth files themselves. For every auth-related pattern found above, trace its downstream impact.

### Authorization layers

Find all middleware, guards, decorators, or filters that consume Cognito tokens or user context:

```
Grep: req\.user|request\.user|currentUser|getUser
Path: middleware/, guards/, filters/, interceptors/

Grep: roles|permissions|can\(|authorize\(
Context: near auth context

Grep: @UseGuards|@Roles|@AuthGuard|requireAuth
Context: NestJS/Express decorators
```

### Database access patterns

Find how user identity scopes data:

```
Grep: userId|user_id|ownerId|owner_id|createdBy|created_by
Context: database queries, ORM models, migrations

Grep: sub\b
Context: SQL queries or ORM filters (Cognito sub used as FK)

Grep: row.level.security|RLS|policy.*user
Context: Postgres migrations or SQL files
```

### Frontend auth state management

Find how auth state propagates through the UI:

```
Grep: AuthContext|authContext|useAuth\b|AuthProvider
Files: .tsx .jsx
Context: custom implementations

Grep: localStorage.*token|sessionStorage.*token|cookie.*token
Context: token storage location

Grep: redux.*auth|zustand.*auth|recoil.*auth|jotai.*auth
Context: state management integration
```

### Backend service-to-service auth

Find if services pass user identity between themselves:

```
Grep: x-user-id|x-user-email|x-forwarded-user|x-auth-user
Context: HTTP headers

Grep: propagat.*token|forward.*token|pass.*token
Context: service client code

Grep: serviceToken|service_token|internal.*auth
Context: backend code
```

### Third-party integrations relying on identity

Find external services that receive or validate user tokens:

```
Grep: stripe|twilio|sendgrid|segment|mixpanel|amplitude
Context: near auth context or user IDs

Grep: webhook.*user|user.*webhook
Context: identity passed to webhooks

Grep: identityId|identity_id
Context: often Cognito Identity Pool IDs used in third-party calls
```

### Token structure assumptions

Find code making assumptions about JWT claims structure:

```
Grep: \.sub\b|token\.sub|payload\.sub|claims\.sub

Grep: \.email\b|token\.email|payload\.email
Context: backend validation code

Grep: cognito:|token\['cognito
Context: Cognito-specific claim namespacing

Grep: iss\b.*cognito|cognito.*iss\b
Context: issuer checks

Grep: aud\b|audience
Context: token validation (client ID used as audience)
```
