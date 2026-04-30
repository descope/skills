# Execution Guide Reference

Full code reference for Phase 5 (Guided Migration Mode). Read this alongside `migration-plan.md` when executing the migration step by step.

---

## Pre-Flight Questions

Ask the user these questions before starting any code changes. Use **AskUserQuestion** to ask them all at once:

**1. Migration approach**
- **Full migration**: Bulk-import all users into Descope. Users cannot sign in with their old password (Cognito never exposes password hashes) — they reset passwords or go passwordless on first sign-in.
- **JIT migration**: Keep Cognito running temporarily. Each user is migrated into Descope on their first sign-in by verifying credentials against Cognito in real time. Preserves the password experience. Decommission Cognito once all users have migrated.
- **Large user base (50k+)**: Recommend working with the Descope CSM to coordinate the migration. Also consider deploying a preemptive Lambda trigger (pre-authentication or post-authentication) in Cognito to push users into Descope as they authenticate during the cutover window — this reduces the bulk import size and spreads load. The Descope migration tool (https://github.com/descope/descope-migration) still handles the remaining users.

**2. MFA**: Is MFA currently enabled? If yes — enforced for all users, or optional per user?
> MFA enrollments (TOTP apps, SMS codes, remembered devices) cannot be migrated. All enrolled users must re-enroll after migration. Ask whether MFA should be integrated into the main sign-up/sign-in flow or remain as a separate enrollment step (see Phase 2 MFA guidance).

**3. Database user IDs**: Does any table store Cognito `sub` values as foreign keys (`user_id`, `owner_id`, `created_by`)?
> If yes, a DB remapping script is needed after migration.

**Also collect** (before Phase A):
- `DESCOPE_PROJECT_ID` and `DESCOPE_MANAGEMENT_KEY` → https://app.descope.com → Company → Management Keys
- `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` with `cognito-idp:ListUsers`, `cognito-idp:ListGroups`, `cognito-idp:ListUsersInGroup`
- `COGNITO_USER_POOL_ID` (format: `us-east-1_XXXXXXXXX`)
- `COGNITO_APP_CLIENT_ID` and — if App Client has a secret — `COGNITO_CLIENT_SECRET`

---

## User Migration

### Full migration — run descope-migration tool

Check IAM permissions first: `cognito-idp:ListUsers`, `cognito-idp:ListGroups`, `cognito-idp:ListUsersInGroup`

```bash
git clone https://github.com/descope/descope-migration.git /tmp/descope-migration
cd /tmp/descope-migration
python3 -m venv /tmp/descope-migration/.venv
source /tmp/descope-migration/.venv/bin/activate
pip install -r requirements.txt --quiet
```

Write `.env` for the migration tool:
```
DESCOPE_PROJECT_ID=<from user>
DESCOPE_MANAGEMENT_KEY=<from user>
AWS_REGION=<detected from .env or config, or ask>
AWS_ACCESS_KEY_ID=<ask if not found in env>
AWS_SECRET_ACCESS_KEY=<ask if not found in env>
COGNITO_USER_POOL_ID=<detected or ask>
```

Dry run first:
```bash
cd /tmp/descope-migration && source .venv/bin/activate && python3 src/main.py cognito --dry-run
```

Report: total user count, group count, `FORCE_CHANGE_PASSWORD` count. Ask for explicit confirmation before live run.

```bash
cd /tmp/descope-migration && source .venv/bin/activate && python3 src/main.py cognito
```

**Multiple pools (Pattern J)**: Run the tool once per pool. Create a Descope Tenant for each pool in Console → Tenants before importing.

**FORCE_CHANGE_PASSWORD users**: Route these users to magic link or OTP in the Descope Flow — they cannot use password sign-in.

### JIT migration setup (if chosen instead of full migration)

1. Instruct the user to create a **Generic HTTP Connector** in Descope Console:
   - Base URL: `https://cognito-idp.<REGION>.amazonaws.com`
   - Headers: `Content-Type: application/x-amz-json-1.1`, `X-Amz-Target: AWSCognitoIdentityProviderService.InitiateAuth`
   - Method: POST

   > **App Client secret detected**: If `COGNITO_CLIENT_SECRET` was found, `USER_PASSWORD_AUTH` requires a `SECRET_HASH` = `HMAC-SHA256(clientSecret, username + clientId)`. Options:
   > - **(a) Proxy service** (recommended): Write a small Lambda or Express endpoint that computes `SECRET_HASH` and proxies to Cognito. Offer to write this proxy.
   > - **(b) New public App Client**: Create a Cognito App Client without a client secret, use only for JIT migration, delete after all users have migrated.

2. Write `DESCOPE_JIT_FLOW_SETUP.md` to the project root with setup instructions for the Descope Flow.

---

## Session Migration

### Dual-validation middleware (Node.js)

Deploy this middleware before cutover. It accepts both Cognito and Descope tokens during the transition window. Monitor `source: 'cognito'` log entries — remove the Cognito branch once they reach zero for a full business day.

```js
import DescopeClient from '@descope/node-sdk';
import { CognitoJwtVerifier } from 'aws-jwt-verify';

const descopeClient = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });
const cognitoVerifier = CognitoJwtVerifier.create({
  userPoolId: process.env.COGNITO_USER_POOL_ID,
  clientId: process.env.COGNITO_APP_CLIENT_ID,
  tokenUse: 'access',
});

async function verifySession(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });

  const unverifiedIss = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString()).iss ?? '';

  if (unverifiedIss.includes('api.descope.com')) {
    try {
      const authInfo = await descopeClient.validateSession(token);
      req.user = { id: authInfo.token.sub, source: 'descope' };
      return next();
    } catch {
      return res.status(401).json({ error: 'Invalid Descope token' });
    }
  } else {
    try {
      const decoded = await cognitoVerifier.verify(token);
      req.user = { id: decoded.sub, source: 'cognito' };
      return next();
    } catch {
      return res.status(401).json({ error: 'Invalid token' });
    }
  }
}
```

### Dual-validation middleware (Python)

```python
import base64, json
from descope import DescopeClient, AuthException
import cognitojwt

descope_client = DescopeClient(project_id=os.environ['DESCOPE_PROJECT_ID'])

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            payload_part = token.split('.')[1]
            payload_part += '=' * (-len(payload_part) % 4)
            unverified = json.loads(base64.b64decode(payload_part))
            iss = unverified.get('iss', '')
        except Exception:
            return jsonify({'error': 'Malformed token'}), 401

        if 'api.descope.com' in iss:
            try:
                claims = descope_client.validate_session(session_token=token)
                request.user = {'id': claims['sub'], 'source': 'descope'}
                return f(*args, **kwargs)
            except AuthException:
                return jsonify({'error': 'Invalid Descope token'}), 401
        else:
            try:
                claims = cognitojwt.decode(token, os.environ['AWS_REGION'], os.environ['COGNITO_USER_POOL_ID'])
                request.user = {'id': claims['sub'], 'source': 'cognito'}
                return f(*args, **kwargs)
            except Exception:
                return jsonify({'error': 'Invalid token'}), 401
    return decorated
```

### Cookie clearing (Next.js / SSR)

```ts
// middleware.ts — clear Cognito cookies and redirect to Descope login
const cognitoCookiePattern = /^CognitoIdentityServiceProvider\./;
const hasCognitoCookie = [...request.cookies.keys()].some(k => cognitoCookiePattern.test(k));
if (hasCognitoCookie) {
  const response = NextResponse.redirect(new URL('/login', request.url));
  [...request.cookies.keys()]
    .filter(k => cognitoCookiePattern.test(k))
    .forEach(k => response.cookies.delete(k));
  return response;
}
```

---

## Package Replacement

**Amplify frontend (React/Vite)**:
```bash
npm remove aws-amplify @aws-amplify/auth @aws-amplify/ui-react amazon-cognito-identity-js 2>/dev/null || true
npm install @descope/react-sdk
```

**Next.js** (including NextAuth.js replacement if Pattern H detected):
```bash
npm remove aws-amplify @aws-amplify/auth @aws-amplify/ui-react next-auth 2>/dev/null || true
npm install @descope/nextjs-sdk
```

**Node.js backend**:
```bash
npm remove aws-jwt-verify @aws-sdk/client-cognito-identity-provider amazon-cognito-identity-js 2>/dev/null || true
npm install @descope/node-sdk
```

**Python**:
```bash
pip uninstall cognitojwt python-jose --yes 2>/dev/null || true
pip install descope --break-system-packages
# Update requirements.txt: remove cognitojwt, python-jose; add descope
```

---

## Code Transformation Patterns

Apply all applicable transformations to each file in a single pass.

### Provider / Initialization

Replace `Amplify.configure({ Auth: ... })` block. Wrap root component:

```jsx
// React/Vite
import { AuthProvider } from '@descope/react-sdk';
<AuthProvider projectId={process.env.VITE_DESCOPE_PROJECT_ID}>
  <App />
</AuthProvider>

// Next.js
import { AuthProvider } from '@descope/nextjs-sdk/client';
<AuthProvider projectId={process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID}>
  <App />
</AuthProvider>
```

### Auth State (Hub.listen / currentAuthenticatedUser)

```jsx
// Remove Hub listener and manual user state. Replace with:
import { useSession, useUser } from '@descope/react-sdk';
const { isAuthenticated, isSessionLoading } = useSession();
const { user } = useUser();
```

### Sign-in / Sign-up UI (Patterns A, B, F)

```jsx
import { Descope } from '@descope/react-sdk';
<Descope
  flowId="sign-up-or-in"
  onSuccess={() => navigate('/dashboard')}
  onError={(e) => console.error('Auth error', e)}
/>
```

### Amplify Authenticator Component (Pattern C)

```jsx
// Before (HOC): export default withAuthenticator(App);
// After — at the login route:
import { Descope } from '@descope/react-sdk';
<Descope flowId="sign-up-or-in" onSuccess={() => navigate('/dashboard')} onError={() => {}} />
```

### Token Retrieval

```jsx
// Auth.currentSession() / .getIdToken().getJwtToken() / fetchAuthSession()
// Replace with:
import { useSession } from '@descope/react-sdk';
const { session } = useSession();
const token = session?.token; // the JWT string
```

### Sign-out

```jsx
import { useDescope } from '@descope/react-sdk';
const { logout } = useDescope();
await logout();
// For global sign-out: descopeClient.logoutAll(refreshToken) on backend
```

### Protected Routes

```jsx
import { useSession } from '@descope/react-sdk';
const { isAuthenticated, isSessionLoading } = useSession();
if (isSessionLoading) return <Spinner />;
return isAuthenticated ? children : <Navigate to="/login" />;
```

### Next.js Middleware

```ts
import { authMiddleware } from '@descope/nextjs-sdk/server';
export default authMiddleware({
  projectId: process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID!,
  redirectUrl: '/login',
  publicRoutes: ['/login', '/signup', '/api/public'], // preserve original publicRoutes
});
export const config = { matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'] };
```

### Next.js Server Components

```ts
import { session } from '@descope/nextjs-sdk/server';
const s = await session();
if (!s) redirect('/login');
// s.token.sub, s.token.email, etc.
```

### Node.js Backend Middleware (single provider)

```js
import DescopeClient from '@descope/node-sdk';
const descopeClient = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });

async function verifySession(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  try {
    const authInfo = await descopeClient.validateSession(token);
    req.user = { id: authInfo.token.sub };
    next();
  } catch {
    res.status(401).json({ error: 'Unauthorized' });
  }
}
```

### Role / Group Checks

```ts
// Before:
payload['cognito:groups'].includes('admin')
token['cognito:username']

// After:
descopeClient.validateRoles(authInfo, ['admin'])  // Node.js
token.roles?.includes('admin')                    // frontend
token['sub']                                      // replaces cognito:username
```

### Missing Auth Operations Mapping

| Before | After |
|---|---|
| `Auth.changePassword(user, oldPwd, newPwd)` | `await descopeClient.password.update(loginId, newPassword)` |
| `Auth.updateUserAttributes(user, attrs)` | `descopeClient.management.user.update(loginId, attrs)` |
| `Auth.deleteUser()` | `descopeClient.management.user.delete(loginId)` |
| `Auth.resendSignUp(username)` | Remove — handled inside Descope Flow |
| `Auth.confirmSignUp(username, code)` | Remove — handled inside Descope Flow |
| `Auth.forgotPassword(username)` | Remove — handled inside Descope Flow |
| `Auth.forgotPasswordSubmit(username, code, newPwd)` | Remove — handled inside Descope Flow |
| `user.attributes.email` | `user.email` (from `useUser()`) |
| `user.attributes['custom:*']` | `user.customAttributes['*']` (from `useUser()`) |
| `user.username` | `user.userId` or `session.token.sub` |
| `appClient.updateSession()` | `useDescope().refresh()` client-side (see below) |

### Session Update After Profile Changes

`appClient.updateSession()` has no server-side equivalent in Descope. When a server action updates user attributes (name, email, custom claims), use client-side refresh to propagate the change to the session token immediately:

```tsx
// Client component — profile update with immediate session refresh
'use client';
import { useDescope } from '@descope/react-sdk'; // or '@descope/nextjs-sdk/client'

export function ProfileForm() {
  const { refresh } = useDescope();

  async function handleSave(formData: FormData) {
    await saveProfileServerAction(formData); // your server action that calls management SDK
    await refresh(); // pull updated claims into the session token immediately
  }
  // ...
}
```

> If immediate reflection is not critical, you can skip `refresh()` and accept a lag of up to ~5 minutes until the next automatic token refresh. For profile pages, the explicit `refresh()` call is cleaner.

> **User management widgets**: For user-facing profile editing (name, email, phone), consider the Descope User Management Widget instead of building custom forms with management SDK calls. Ask the user if this fits their UX requirements before building code-based update flows.

### Auth State Change Listeners

Cognito's `Hub.listen('auth', callback)` pattern is replaced by the Descope auth-helpers event system. If the codebase has Hub listeners for sign-in/sign-out events, replace with:

```ts
import { getSessionToken, onSessionTokenChange } from '@descope/web-js-sdk';
// or via the React SDK:
import { useDescope } from '@descope/react-sdk';

// Listen for auth state changes (sign-in, sign-out, token refresh)
// See: https://docs.descope.com/client-sdk/auth-helpers#handling-authentication-state-changes
```

Use the Descope Docs MCP (`search-descope-docs` with "auth state change event listener") to get the current API for the exact framework in use.

### NextAuth.js Replacement (Pattern H)

1. Delete `pages/api/auth/[...nextauth].ts` (or `app/api/auth/[...nextauth]/route.ts`)
2. Replace `SessionProvider` with `AuthProvider` from `@descope/nextjs-sdk/client`
3. Replace `useSession()` from `next-auth/react` with `useSession` from `@descope/nextjs-sdk/client`
4. Replace `signIn()` / `signOut()` with Descope equivalents
5. Replace `getServerSession()` with `session()` from `@descope/nextjs-sdk/server`

### Multi-tenant Token Access (Pattern J)

```ts
// Before:
const tenant = payload['cognito:groups'].find(g => g.startsWith('org_'));

// After:
const tenantId = Object.keys(token.tenants ?? {})[0];
```

---

## Environment Variables

Back up all `.env` files first:
```bash
for f in <all .env files found>; do cp "$f" "$f.cognito-backup"; done
```

Comment out Cognito vars (prefix with `# REMOVED - Cognito migration`):
```
COGNITO_USER_POOL_ID
COGNITO_APP_CLIENT_ID
COGNITO_CLIENT_SECRET
COGNITO_REGION
AWS_USER_POOL_ID
AWS_USER_POOL_CLIENT_ID
NEXT_PUBLIC_USER_POOL_ID
NEXT_PUBLIC_USER_POOL_CLIENT_ID
NEXT_PUBLIC_AWS_REGION
REACT_APP_USER_POOL_ID
REACT_APP_USER_POOL_CLIENT_ID
VITE_USER_POOL_ID
VITE_USER_POOL_CLIENT_ID
```

Add only the vars relevant to the detected stack:
```bash
VITE_DESCOPE_PROJECT_ID=YOUR_DESCOPE_PROJECT_ID_HERE         # React/Vite only
NEXT_PUBLIC_DESCOPE_PROJECT_ID=YOUR_DESCOPE_PROJECT_ID_HERE  # Next.js only
REACT_APP_DESCOPE_PROJECT_ID=YOUR_DESCOPE_PROJECT_ID_HERE    # CRA only
DESCOPE_PROJECT_ID=YOUR_DESCOPE_PROJECT_ID_HERE              # Backend / server-side
DESCOPE_MANAGEMENT_KEY=YOUR_MANAGEMENT_KEY_HERE              # Only for admin/management ops
```

---

## Hosted UI and Federation Patterns

> **SSO Setup Suite first**: For any SAML or OIDC enterprise SSO migration (Paths E1, E2 below), present the **Descope SSO Setup Suite** as the primary option before writing any programmatic SSO configuration code. The SSO Setup Suite guides admins through a no-code flow in the Descope Console to configure SAML/OIDC connections — no code deployment required. Only fall back to `management.sso.configureOIDCSettings()` / `management.sso.configureSAMLSettings()` if automated provisioning via API is explicitly required.

### Path D1 — Self-use Hosted UI

Remove `oauth:` config from `Amplify.configure`. Replace login redirect trigger with:

```jsx
import { Descope } from '@descope/react-sdk';
<Descope flowId="sign-up-or-in" onSuccess={() => navigate('/dashboard')} onError={(e) => console.error(e)} />
```

Manual: add original `redirectSignIn` URLs to Descope Console → Project Settings → Allowed Redirect URLs.

### Path D2 — Cognito as OAuth Authorization Server

External clients need to redirect to Descope OIDC endpoints:
- Authorization: `https://api.descope.com/oauth2/v1/authorize?projectId=<PROJECT_ID>`
- Token: `https://api.descope.com/oauth2/v1/token`
- JWKS: `https://api.descope.com/v2/keys/<PROJECT_ID>`

Configure in Console → Applications → Create OIDC Application. Each external client must update its Cognito endpoint references.

### Social Providers (Google, Facebook, Apple)

Remove `Auth.federatedSignIn({ provider: 'Google' })` calls. Replace with `<Descope flowId="sign-up-or-in" />` — social buttons appear once connectors are configured in Console → Connectors.

### Path E1 — Single SAML IdP

Remove `Auth.federatedSignIn({ provider: '<SAMLProviderName>' })`. Replace with `<Descope flowId="sign-up-or-in" />`.

Manual: Console → SSO Applications → configure SAML with IdP metadata. Update IdP with Descope ACS URL and Entity ID.

### Path E2 — Multi-tenant SAML

Remove domain-routing logic and pre-signup Lambda domain validation. Replace login trigger with `<Descope flowId="sign-up-or-in" />`.

Manual: Create Descope Tenant per customer org, configure SAML connection per tenant, set domain(s) per tenant. Add SSO step to Sign-Up or In Flow.

---

## Infrastructure

### API Gateway Authorizer Swap

1. Console → Project Settings → JWT Templates: enable **AWS API Gateway** template
2. API Gateway: remove Cognito User Pool authorizer; create JWT Authorizer:
   - Issuer: `https://api.descope.com/P<DESCOPE_PROJECT_ID>`
   - Audience: `P<DESCOPE_PROJECT_ID>`
   - Token source: `$request.header.Authorization`

### Cognito Identity Pools (Pattern G)

Descope does not replace Identity Pools. Configure Descope as a federated OIDC provider in the existing Identity Pool:
- Descope OIDC endpoint: `https://api.descope.com/<DESCOPE_PROJECT_ID>`
- Modify Identity Pool trust to accept Descope tokens

### M2M / Service-to-Service (Pattern I)

Replace `POST /oauth2/token` + `client_credentials` with Descope Access Keys:
- Create Access Key in Console → Company → Access Keys
- Use Access Key JWT in service-to-service calls
