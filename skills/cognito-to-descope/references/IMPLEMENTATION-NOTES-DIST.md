# AWS Cognito → Descope: Implementation Reference

Comprehensive technical reference for migrating apps from AWS Cognito to Descope.
Covers AWS Amplify (v5 & v6), React, Next.js, Node.js/Express, and Python/Flask.

**Sources**: https://docs.descope.com/migrate/cognito · https://github.com/descope/descope-migration · https://docs.descope.com/getting-started/react · https://github.com/descope/node-sdk · https://github.com/descope/python-sdk · https://docs.descope.com/authorization/session-management/session-validation/backend · https://docs.descope.com/authorization/session-management/session-validation/oidc-jwt-authorizers/aws-jwt-authorizer

---

## Detection Patterns (for automated scanning)

The following patterns identify Cognito usage in a codebase. Use these during Phase 0 discovery.

### Package identifiers (in package.json / requirements.txt)

| Package | Stack | Notes |
|---|---|---|
| `aws-amplify` | React/Next.js frontend | Check version: <6.x = v5 API, >=6.x = v6 API |
| `@aws-amplify/auth` | React frontend | Usually alongside aws-amplify |
| `@aws-amplify/ui-react` | React frontend | Provides `<Authenticator>` component |
| `amazon-cognito-identity-js` | Frontend (lower-level) | Direct CognitoUserPool/CognitoUser usage |
| `aws-jwt-verify` | Node.js backend | CognitoJwtVerifier token validation |
| `@aws-sdk/client-cognito-identity-provider` | Node.js backend | Admin user management |
| `cognitojwt` | Python backend | Token decode/verify |
| `python-jose` | Python backend | Manual JWKS-based verification |
| `boto3` | Python backend | Admin user management (may be used for other AWS too) |

### Code patterns by transformation type

| Pattern to grep | Transformation | Section |
|---|---|---|
| `Amplify\.configure\(` | Provider setup | 3.1 |
| `withAuthenticator\(` | Sign-in UI → Descope component | 3.3 |
| `<Authenticator` | Sign-in UI → Descope component | 3.3 |
| `Hub\.listen\('auth'` | Auth state listener removal | 3.2 |
| `Auth\.currentAuthenticatedUser\(` | Auth state → useSession | 3.2 |
| `getCurrentUser\(` | Auth state (Amplify v6) → useSession | 3.2 |
| `Auth\.currentSession\(` | Token retrieval → session.token | 3.4 |
| `fetchAuthSession\(` | Token retrieval (v6) → session.token | 3.4 |
| `getIdToken\(\)\.getJwtToken\(` | Token extraction → session.token | 3.4 |
| `Auth\.signIn\(` | Sign-in form → Descope Flow | 3.3 |
| `Auth\.signUp\(` | Sign-up form → Descope Flow | 3.3 |
| `Auth\.signOut\(` | Logout → useDescope().logout | 3.5 |
| `signOut\({ global` | Global sign-out → logoutAll | 3.5 |
| `Auth\.forgotPassword\(` | Password reset → Flow (no code) | 3.3 |
| `CognitoUserPool\(` | SDK init → remove | 3.1 |
| `authenticateUser\(` | Sign-in → Descope Flow | 3.3 |
| `CognitoJwtVerifier\.create\(` | Backend init → DescopeClient | 3.9 |
| `cognitoVerifier\.verify\(` | Token validation → validateSession | 3.9 |
| `jwksUri.*cognito-idp` | Manual JWKS → Descope SDK | 3.9 |
| `cognitojwt\.decode\(` | Python token verify → validate_session | 3.10 |
| `python_jose\|from jose` | Python JWKS → Descope SDK | 3.10 |
| `cognito:groups` | Role check → validateRoles() | 3.11 |
| `cognito:username` | User ID → sub | 3.11 |
| `AdminGetUserCommand\|admin_get_user` | User lookup → mgmt SDK | 3.12/3.13 |
| `AdminAddUserToGroupCommand\|admin_add_user_to_group` | Group assign → setRoles | 3.12/3.13 |
| `AdminUserGlobalSignOutCommand\|admin_user_global_sign_out` | Revoke → logout | 3.12/3.13 |
| `IdentityPoolId\|CognitoIdentityCredentials` | Identity Pool (manual item) | Phase 5E |
| `CognitoUserPoolsAuthorizer\|UserPoolArn` | API Gateway authorizer (manual item) | Phase 5D |
| `exports\.handler\|def handler\(event` | Lambda triggers (manual item) | Phase 5C |

### Amplify v5 vs v6 detection

Check `package.json` for `aws-amplify` version:
- `"aws-amplify": "^5.x.x"` → v5: class-based `Auth.signIn()`, `Auth.signOut()`, `Hub.listen()`
- `"aws-amplify": "^6.x.x"` → v6: function imports `signIn()`, `signOut()`, `fetchAuthSession()`

Both map to the same Descope patterns — but the before-code in your edits must match the version actually in use.

### Env variable names to replace

All of these should be removed or commented out and replaced with Descope equivalents:
```
COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID, COGNITO_REGION,
AWS_USER_POOL_ID, AWS_USER_POOL_CLIENT_ID,
NEXT_PUBLIC_USER_POOL_ID, NEXT_PUBLIC_USER_POOL_CLIENT_ID, NEXT_PUBLIC_AWS_REGION,
REACT_APP_USER_POOL_ID, REACT_APP_USER_POOL_CLIENT_ID,
VITE_USER_POOL_ID, VITE_USER_POOL_CLIENT_ID
```

---

## Table of Contents

1. [Core Concepts](#1-core-concepts)
2. [User Migration](#2-user-migration)
3. [React / Amplify Frontend](#3-react--amplify-frontend)
4. [Next.js Frontend](#4-nextjs-frontend)
5. [Node.js / Express Backend](#5-nodejs--express-backend)
6. [Python / Flask Backend](#6-python--flask-backend)
7. [AWS API Gateway Authorizer](#7-aws-api-gateway-authorizer)
8. [Lambda Triggers](#8-lambda-triggers)
9. [Auth Method Equivalents](#9-auth-method-equivalents)
10. [Terminology Mapping](#10-terminology-mapping)
11. [Environment Variables](#11-environment-variables)
12. [Key Gotchas](#12-key-gotchas)
13. [Migration Checklist](#13-migration-checklist)
14. [Useful Links](#14-useful-links)

---

## 1. Core Concepts

### The fundamental difference

Cognito is AWS's managed authentication service built around **User Pools** (for authentication) and **Identity Pools** (for temporary AWS credentials). Developers interact with Cognito via AWS Amplify SDK (`Auth.signIn`, `Auth.signUp`, etc.) or the lower-level `amazon-cognito-identity-js` library. Cognito issues its own JWTs (ID token + access token) that must be validated against Cognito's JWKS endpoint.

Descope replaces the User Pool layer with **Descope Flows** — visual, configurable auth journeys embedded as a single component in your app. The backend validation pattern is equivalent: client gets a JWT, sends it to the backend, backend validates it.

**Identity Pools (AWS credentials federation) are not replaced by Descope** — if your app uses Identity Pools to grant users temporary AWS IAM credentials (e.g., for direct S3/DynamoDB access), that layer needs separate handling. See Gotcha #9.

### Token differences

- **Cognito**: Two tokens per session — an **ID token** (user identity claims) and an **access token** (authorization scopes). JWKS at `https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json`. Issuer: `https://cognito-idp.{region}.amazonaws.com/{userPoolId}`.
- **Descope**: One session token (JWT) plus a refresh token. JWKS at `https://api.descope.com/v2/keys/{projectId}`. Issuer: `https://api.descope.com/{projectId}` (or OIDC-compliant form for API Gateway: `https://api.descope.com/P<projectId>`). Lifetime configurable in Console.

Key claim differences:
- Cognito uses `cognito:username` for the username identifier; Descope uses `sub` (UUID).
- Cognito groups surface as `cognito:groups` array claim; Descope surfaces roles differently via the SDK.
- Cognito ID token has `email_verified`, `phone_number_verified`; Descope embeds similar verified flags.

### Session management

- **Cognito / Amplify**: `Auth.currentAuthenticatedUser()` for current user, `Auth.currentSession()` for tokens. `Hub.listen('auth', callback)` for auth events. Amplify v6 uses `getCurrentUser()` and `fetchAuthSession()`.
- **Descope React SDK**: `useSession()` hook provides `isAuthenticated`, `isSessionLoading`, `session.token`. `useUser()` provides user attributes. Auto-refreshes tokens transparently. No event listener setup needed.

---

## 2. User Migration

### Critical limitation: no password hash export

**AWS Cognito does not expose user password hashes.** This is the most important difference from Firebase migration. It means:
- Full migration always results in users needing to either reset their password or switch to passwordless.
- JIT (Just-In-Time) migration is the preferred path if preserving the password sign-in experience is required.

### Option A: Full Migration (bulk import, passwordless or force-reset)

Use the Descope migration tool:

```bash
git clone git@github.com:descope/descope-migration.git
cd descope-migration
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Set up `.env`:
```
DESCOPE_PROJECT_ID=Pxxx...
DESCOPE_MANAGEMENT_KEY=Kxxx...
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
```

Run:
```bash
python3 src/main.py cognito --dry-run   # safe preview
python3 src/main.py cognito             # live migration
```

The tool automatically:
1. Converts Cognito User Groups to Descope Roles.
2. Imports all users with standard attributes and `custom:*` attributes.
3. Associates users with their groups/roles.

After import, users cannot sign in with their old passwords. Use a `freshlyMigrated` custom attribute (set to `true` during import) to trigger a password-reset or passwordless step in your Descope Flow on first sign-in.

```python
# Manual export + mapping (for custom implementations)
import boto3

cognito = boto3.client('cognito-idp', region_name='us-east-1')
user_pool_id = 'us-east-1_XXXXXXXXX'

users, pagination_token = [], None
while True:
    kwargs = {'UserPoolId': user_pool_id, 'Limit': 60}
    if pagination_token:
        kwargs['PaginationToken'] = pagination_token
    response = cognito.list_users(**kwargs)
    users.extend(response['Users'])
    pagination_token = response.get('PaginationToken')
    if not pagination_token:
        break

def map_cognito_user(u):
    attrs = {a['Name']: a['Value'] for a in u.get('Attributes', [])}
    email = attrs.get('email')
    descope_user = {
        'loginIds': [email] if email else [u['Username']],
        'email': email,
        'phone': attrs.get('phone_number'),
        'name': attrs.get('name'),
        'givenName': attrs.get('given_name'),
        'familyName': attrs.get('family_name'),
        'verifiedEmail': attrs.get('email_verified') == 'true',
        'verifiedPhone': attrs.get('phone_number_verified') == 'true',
        'customAttributes': {
            k.replace('custom:', ''): v
            for k, v in attrs.items() if k.startswith('custom:')
        },
        'roleNames': u.get('Groups', []),
    }
    descope_user['customAttributes']['freshlyMigrated'] = True
    return descope_user
```

Batch-import via Descope API:
```python
import requests

url = 'https://api.descope.com/v1/mgmt/user/create/batch'
headers = {
    'Authorization': f'Bearer {DESCOPE_PROJECT_ID}:{DESCOPE_MANAGEMENT_KEY}',
    'Content-Type': 'application/json'
}
batch_size = 100
for i in range(0, len(descope_users), batch_size):
    r = requests.post(url, json={'users': descope_users[i:i+batch_size]}, headers=headers)
    print(r.status_code, r.text)
```

### Option B: JIT Migration (preserves passwords, gradual rollout)

Keep Cognito running. On first sign-in through Descope, the flow verifies credentials against Cognito via a Generic HTTP Connector, then provisions the user in Descope.

**Step 1** — Create a Generic HTTP Connector in Descope:
- Base URL: `https://cognito-idp.<region>.amazonaws.com`
- Headers: `Content-Type: application/x-amz-json-1.1` and `X-Amz-Target: AWSCognitoIdentityProviderService.InitiateAuth`
- Method: POST
- Body template:
```json
{
  "ClientId": "<COGNITO_APP_CLIENT_ID>",
  "AuthFlow": "USER_PASSWORD_AUTH",
  "AuthParameters": {
    "USERNAME": "{{form.email}}",
    "PASSWORD": "{{form.password}}"
  }
}
```

**Step 2** — Build the JIT Flow in Descope:
1. Check if user already exists in Descope (`user.loginIds` not empty → skip Cognito, use normal Descope sign-in).
2. For new users: collect email + password, call Cognito connector.
3. On Cognito success: create user in Descope (`Sign Up / Password` action).
4. On Cognito failure: route to passwordless recovery (magic link, OTP, or force password reset in Descope).
5. Set `freshlyMigrated = false` once provisioned in Descope to skip Cognito on future logins.

### User ID changes

Cognito user IDs are UUIDs (`sub` in the ID token, also accessible as the `Username` field). Descope assigns new user IDs. Store the Cognito `sub` as a Descope custom attribute (`cognitoSub`) during migration to maintain lookup capability:

```python
descope_user['customAttributes']['cognitoSub'] = attrs.get('sub', u['Username'])
```

### Handling FORCE_CHANGE_PASSWORD users

Cognito users with `UserStatus: FORCE_CHANGE_PASSWORD` have never completed their first sign-in. Treat them the same as freshly migrated users — route them through a password-reset flow in Descope on first sign-in.

---

## 3. React / Amplify Frontend

### AWS Amplify v5 → Descope

**Install:**
```bash
npm remove aws-amplify @aws-amplify/auth @aws-amplify/ui-react
npm install @descope/react-sdk
```

**Provider setup** (replaces `Amplify.configure` + `withAuthenticator`):

```jsx
// Before (Amplify v5)
import { Amplify } from 'aws-amplify';
Amplify.configure({
  Auth: {
    region: 'us-east-1',
    userPoolId: 'us-east-1_XXXXXXXX',
    userPoolWebClientId: 'xxxxxxxxxxxxxxxxxxxxxxxxxx',
    authenticationFlowType: 'USER_PASSWORD_AUTH',
  }
});

// After (Descope)
// main.jsx or index.jsx
import { AuthProvider } from '@descope/react-sdk';

root.render(
  <AuthProvider projectId="YOUR_DESCOPE_PROJECT_ID">
    <App />
  </AuthProvider>
);
```

**Auth state** (replaces `Auth.currentAuthenticatedUser()` + Hub listener):

```jsx
// Before (Amplify v5)
import { Auth, Hub } from 'aws-amplify';
const [user, setUser] = useState(null);
useEffect(() => {
  Auth.currentAuthenticatedUser().then(setUser).catch(() => setUser(null));
  const unsub = Hub.listen('auth', ({ payload }) => {
    if (payload.event === 'signIn') Auth.currentAuthenticatedUser().then(setUser);
    if (payload.event === 'signOut') setUser(null);
  });
  return unsub;
}, []);

// After (Descope)
import { useSession, useUser } from '@descope/react-sdk';
const { isAuthenticated, isSessionLoading } = useSession();
const { user } = useUser();
// user contains: name, email, phone, picture, customAttributes, roles, etc.
```

**Sign-in UI** (replaces `withAuthenticator` HOC or manual `Auth.signIn` form):

```jsx
// Before (Amplify v5 — Authenticator component)
import { Authenticator } from '@aws-amplify/ui-react';
return <Authenticator />;

// Before (Amplify v5 — manual)
import { Auth } from 'aws-amplify';
await Auth.signIn(email, password);

// After (Descope — handles all auth methods in one component)
import { Descope } from '@descope/react-sdk';

function LoginPage() {
  const navigate = useNavigate();
  return (
    <Descope
      flowId="sign-up-or-in"    // Flow ID from Descope Console → Flows
      onSuccess={() => navigate('/dashboard')}
      onError={(e) => console.error('Auth error', e)}
    />
  );
}
```

**Getting the ID token for API calls** (replaces `Auth.currentSession()`):

```jsx
// Before (Amplify v5)
const session = await Auth.currentSession();
const token = session.getIdToken().getJwtToken();
// OR access token:
const accessToken = session.getAccessToken().getJwtToken();
fetch('/api/data', { headers: { Authorization: `Bearer ${token}` } });

// After (Descope)
import { useSession } from '@descope/react-sdk';
const { session } = useSession();
// session.token is the current session JWT, auto-refreshed by SDK
fetch('/api/data', { headers: { Authorization: `Bearer ${session?.token}` } });
```

**Sign-out** (replaces `Auth.signOut()`):

```jsx
// Before (Amplify v5)
import { Auth } from 'aws-amplify';
await Auth.signOut();
// Global sign-out (revokes all tokens):
await Auth.signOut({ global: true });

// After (Descope)
import { useDescope } from '@descope/react-sdk';
const { logout } = useDescope();
await logout();
// Note: Descope logout() revokes the current session's refresh token
```

**Protected routes:**

```jsx
// Before (Amplify v5 — manual)
const PrivateRoute = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    Auth.currentAuthenticatedUser().then(setUser).catch(() => {}).finally(() => setLoading(false));
  }, []);
  if (loading) return <Spinner />;
  return user ? children : <Navigate to="/login" />;
};

// After (Descope)
import { useSession } from '@descope/react-sdk';
const PrivateRoute = ({ children }) => {
  const { isAuthenticated, isSessionLoading } = useSession();
  if (isSessionLoading) return <Spinner />;
  return isAuthenticated ? children : <Navigate to="/login" />;
};
```

### AWS Amplify v6 → Descope

Amplify v6 uses tree-shakeable imports. Patterns are similar but import paths changed.

**Install:**
```bash
npm remove aws-amplify
npm install @descope/react-sdk
```

```jsx
// Before (Amplify v6)
import { signIn, signOut, getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';
import { Hub } from 'aws-amplify/utils';

// Check current user
try {
  const user = await getCurrentUser();
  // user.username, user.userId, user.signInDetails
} catch { /* not signed in */ }

// Sign in
const { isSignedIn, nextStep } = await signIn({ username: email, password });

// Get token
const session = await fetchAuthSession();
const token = session.tokens?.idToken?.toString();

// Sign out
await signOut();
// OR global sign-out:
await signOut({ global: true });

// After (Descope) — same as Amplify v5 above
```

### amazon-cognito-identity-js (lower-level) → Descope

```jsx
// Before (amazon-cognito-identity-js)
import { CognitoUserPool, CognitoUser, AuthenticationDetails } from 'amazon-cognito-identity-js';

const userPool = new CognitoUserPool({ UserPoolId: '...', ClientId: '...' });
const authDetails = new AuthenticationDetails({ Username: email, Password: password });
const cognitoUser = new CognitoUser({ Username: email, Pool: userPool });

cognitoUser.authenticateUser(authDetails, {
  onSuccess: (session) => {
    const idToken = session.getIdToken().getJwtToken();
    // proceed
  },
  onFailure: (err) => console.error(err),
  newPasswordRequired: (attrs) => { /* force change password */ }
});

// After (Descope) — replace entirely with the <Descope flowId="sign-up-or-in"> component
```

---

## 4. Next.js Frontend

### Install

```bash
npm remove aws-amplify @aws-amplify/auth
npm install @descope/nextjs-sdk
```

### Middleware (replaces Amplify SSR or custom Cognito token verification)

```ts
// Before (Cognito — custom middleware)
import { NextResponse } from 'next/server';
import { verify } from 'jsonwebtoken';
import jwksClient from 'jwks-rsa';

// Custom Cognito JWT validation in middleware...

// After (Descope)
// middleware.ts
import { authMiddleware } from '@descope/nextjs-sdk/server';

export default authMiddleware({
  projectId: process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID!,
  redirectUrl: '/login',
  publicRoutes: ['/login', '/signup', '/api/public'],
});

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

### Server Components

```tsx
// app/dashboard/page.tsx
import { session } from '@descope/nextjs-sdk/server';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const s = await session();
  if (!s) redirect('/login');
  return (
    <div>
      <h1>Hello, {s.token.email}</h1>
      <p>User ID: {s.token.sub}</p>
    </div>
  );
}
```

### Root layout (wrap with AuthProvider)

```tsx
// app/layout.tsx
import { AuthProvider } from '@descope/nextjs-sdk';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <AuthProvider projectId={process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID!}>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

---

## 5. Node.js / Express Backend

### Install

```bash
npm remove amazon-cognito-jwt-verify aws-jwt-verify
npm install @descope/node-sdk
```

### Initialization

```js
// Before (aws-jwt-verify — most common Node.js approach)
import { CognitoJwtVerifier } from 'aws-jwt-verify';

const verifier = CognitoJwtVerifier.create({
  userPoolId: 'us-east-1_XXXXXXXXX',
  tokenUse: 'id',  // or 'access'
  clientId: 'xxxxxxxxxxxxxxxxxxxxxxxxxx',
});

// Before (jsonwebtoken + jwks-rsa — manual approach)
import jwksClient from 'jwks-rsa';
const client = jwksClient({
  jwksUri: `https://cognito-idp.us-east-1.amazonaws.com/${USER_POOL_ID}/.well-known/jwks.json`
});

// After (Descope)
import DescopeClient from '@descope/node-sdk';
const descopeClient = DescopeClient({
  projectId: process.env.DESCOPE_PROJECT_ID,
  // managementKey: process.env.DESCOPE_MANAGEMENT_KEY  // only for admin operations
});
```

### Auth middleware

```js
// Before (aws-jwt-verify)
async function verifyToken(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  try {
    const payload = await verifier.verify(token);
    req.user = payload; // sub, email, cognito:username, cognito:groups, etc.
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
}

// After (Descope)
async function verifySession(req, res, next) {
  const sessionToken = req.headers.authorization?.split('Bearer ')[1]
    || req.cookies?.DS;    // if using cookie-based sessions
  const refreshToken = req.cookies?.DSR;

  if (!sessionToken) return res.status(401).json({ error: 'Unauthorized' });
  try {
    // Auto-refreshes if session token is expired and a valid refresh token is provided
    const authInfo = await descopeClient.validateAndRefreshSession(
      sessionToken, refreshToken
    );
    req.user = authInfo.token; // sub, email, roles, custom claims, etc.
    next();
  } catch {
    res.status(401).json({ error: 'Invalid or expired session' });
  }
}
```

### Protected routes

```js
app.get('/api/profile', verifySession, (req, res) => {
  // req.user.sub  → Descope user ID (equivalent to Cognito sub)
  // req.user.email → user email
  res.json({ id: req.user.sub, email: req.user.email });
});
```

### Role / group validation (replaces `cognito:groups` claim check)

```js
// Before (Cognito — checking cognito:groups in JWT)
const groups = decoded['cognito:groups'] || [];
const isAdmin = groups.includes('admins');

// After (Descope)
const isAdmin = descopeClient.validateRoles(authInfo, ['admin']);
const canWrite = descopeClient.validatePermissions(authInfo, ['content:write']);
// Tenant-scoped roles (multi-tenant apps):
const isTenantAdmin = descopeClient.validateTenantRoles(authInfo, tenantId, ['admin']);
```

### User management

```js
// Before (AWS SDK v3 — CognitoIdentityProviderClient)
import { CognitoIdentityProviderClient, AdminGetUserCommand } from '@aws-sdk/client-cognito-identity-provider';
const client = new CognitoIdentityProviderClient({ region: 'us-east-1' });
const user = await client.send(new AdminGetUserCommand({
  UserPoolId: '...', Username: email
}));

// After (Descope)
const resp = await descopeClient.management.user.load(loginId);        // by email/phone
const resp2 = await descopeClient.management.user.loadByUserId(userId); // by Descope user ID

// Assign roles (replaces AdminAddUserToGroup)
await descopeClient.management.user.setRoles(loginId, ['admin']);

// Revoke all sessions (replaces AdminUserGlobalSignOut)
await descopeClient.management.user.logout(userId);
```

### Dual token validation during cutover

During a transition where both Cognito and Descope tokens may be in circulation:

```js
async function verifyAnyToken(req, res, next) {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });

  // Check issuer to route to the right validator
  const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString());
  const issuer = payload.iss || '';

  try {
    if (issuer.includes('cognito-idp.amazonaws.com')) {
      const cognito = await cognitoVerifier.verify(token);
      req.user = { sub: cognito.sub, email: cognito.email, source: 'cognito' };
    } else if (issuer.includes('descope.com')) {
      const authInfo = await descopeClient.validateSession(token);
      req.user = { ...authInfo.token, source: 'descope' };
    } else {
      throw new Error('Unknown token issuer');
    }
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
}
```

---

## 6. Python / Flask Backend

### Install

```bash
pip uninstall cognitojwt python-jose
pip install descope
```

### Initialization

```python
# Before (cognitojwt — common approach)
import cognitojwt
COGNITO_REGION = 'us-east-1'
COGNITO_USER_POOL_ID = 'us-east-1_XXXXXXXXX'
COGNITO_APP_CLIENT_ID = 'xxxxxxxxxx'
# Usage:
claims = cognitojwt.decode(token, COGNITO_REGION, COGNITO_USER_POOL_ID, app_client_id=COGNITO_APP_CLIENT_ID)

# Before (python-jose — manual JWKS)
from jose import jwk, jwt as jose_jwt
import requests
jwks_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
jwks = requests.get(jwks_url).json()
claims = jose_jwt.decode(token, jwks, algorithms=['RS256'], audience=client_id)

# After (Descope)
from descope import DescopeClient, AuthException
descope_client = DescopeClient(project_id='YOUR_DESCOPE_PROJECT_ID')

# For management operations (user CRUD, roles, etc.):
descope_client = DescopeClient(
    project_id='YOUR_DESCOPE_PROJECT_ID',
    management_key='YOUR_MANAGEMENT_KEY'
)
```

### Auth decorator (replaces cognitojwt.decode)

```python
# Before (Cognito)
from functools import wraps
from flask import request, jsonify
import cognitojwt

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            claims = cognitojwt.decode(token, COGNITO_REGION, COGNITO_USER_POOL_ID)
            request.user = claims  # sub, email, cognito:username, cognito:groups
        except Exception:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# After (Descope)
from functools import wraps
from flask import request, jsonify
from descope import DescopeClient, AuthException

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not session_token:
            return jsonify({'error': 'Unauthorized'}), 401
        try:
            jwt_response = descope_client.validate_session(session_token=session_token)
            request.user = jwt_response  # dict: sub, email, roles, custom claims
        except AuthException:
            return jsonify({'error': 'Invalid or expired token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/profile')
@require_auth
def profile():
    return jsonify({
        'id': request.user['sub'],
        'email': request.user.get('email')
    })
```

### User management

```python
# Before (boto3 — Cognito admin operations)
import boto3
cognito = boto3.client('cognito-idp', region_name='us-east-1')
cognito.admin_get_user(UserPoolId=user_pool_id, Username=email)
cognito.admin_add_user_to_group(UserPoolId=..., Username=..., GroupName='admins')
cognito.admin_user_global_sign_out(UserPoolId=..., Username=...)

# After (Descope)
resp = descope_client.mgmt.user.load(login_id='user@example.com')
resp_by_id = descope_client.mgmt.user.load_by_user_id(user_id='U2abc...')
descope_client.mgmt.user.set_roles(login_id='user@example.com', roles=['admin'])
descope_client.mgmt.user.logout_user(user_id='U2abc...')
```

---

## 7. AWS API Gateway Authorizer

### Replacing a Cognito Authorizer with a Descope JWT Authorizer

Cognito User Pools integrate directly with AWS API Gateway as a native authorizer. When migrating to Descope, replace the Cognito authorizer with a JWT authorizer pointed at Descope.

**Step 1** — Enable API Gateway-compatible JWT template in Descope:

In the Descope Console → Project Settings → JWT Templates, create or switch to the **AWS API Gateway** template. This changes the `iss` claim from `P<projectId>` to `https://api.descope.com/P<projectId>` (required for API Gateway OIDC discovery).

**Step 2** — In AWS API Gateway (HTTP API), remove the Cognito authorizer and create a JWT Authorizer:

- **Issuer URL**: `https://api.descope.com/P<YOUR_DESCOPE_PROJECT_ID>`
- **Audience**: `P<YOUR_DESCOPE_PROJECT_ID>` (your Descope Project ID)
- **Token source**: `$request.header.Authorization` (Bearer token)

For REST API (not HTTP API), use a Lambda authorizer that calls `descopeClient.validateSession(token)`.

**Step 3** — Dual validation during cutover (Node.js Lambda authorizer):

```js
const { CognitoJwtVerifier } = require('aws-jwt-verify');
const DescopeClient = require('@descope/node-sdk');

const cognitoVerifier = CognitoJwtVerifier.create({
  userPoolId: process.env.COGNITO_USER_POOL_ID,
  tokenUse: 'access',
  clientId: process.env.COGNITO_CLIENT_ID,
});
const descopeClient = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });

exports.handler = async (event) => {
  const token = event.authorizationToken?.replace('Bearer ', '');
  if (!token) return generatePolicy('user', 'Deny', event.methodArn);

  const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString());

  try {
    if ((payload.iss || '').includes('cognito-idp')) {
      await cognitoVerifier.verify(token);
    } else {
      await descopeClient.validateSession(token);
    }
    return generatePolicy('user', 'Allow', event.methodArn);
  } catch {
    return generatePolicy('user', 'Deny', event.methodArn);
  }
};

function generatePolicy(principalId, effect, resource) {
  return {
    principalId,
    policyDocument: {
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: effect, Resource: resource }]
    }
  };
}
```

---

## 8. Lambda Triggers

Cognito Lambda triggers are event hooks that run custom logic at specific points in the auth flow. In Descope, equivalent logic is implemented via **Flow steps**, **Connectors**, or **Webhooks**.

| Cognito Lambda Trigger | Descope Equivalent |
|---|---|
| Pre Sign-up | Add a pre-registration step in the Flow (e.g., check blocklist via HTTP Connector) |
| Post Confirmation | Use a Descope Webhook (post-user-creation event) or Flow step after sign-up success |
| Pre Token Generation | **JWT Templates** in Descope Console — customize claims in the issued JWT |
| Custom Authentication | Build a custom Flow with your logic using Flow steps + Generic HTTP Connectors |
| Post Authentication | Webhook on successful login event |
| User Migration | JIT migration via Generic HTTP Connector (see Section 2) |
| Verify Auth Challenge | Implement as a custom Flow step |
| Define Auth Challenge | Implement as a custom Flow with conditional branching |

---

## 9. Auth Method Equivalents

| Cognito / Amplify | Descope | Notes |
|---|---|---|
| `Auth.signIn(user, pass)` | `<Descope flowId="sign-up-or-in">` component | Descope Flow handles all auth methods |
| `Auth.signUp(...)` | Same sign-up-or-in flow | Flow detects new vs returning user |
| `Auth.forgotPassword(email)` | Forgot-password step in Flow | Built into Descope's sign-in flow |
| `Auth.confirmForgotPassword(...)` | Same Flow — auto-handled by step |  |
| `Auth.signOut()` / `signOut()` | `logout()` from `useDescope()` | |
| `Auth.signOut({ global: true })` | `descopeClient.logoutAll(refreshToken)` | Revokes all sessions |
| `Auth.currentAuthenticatedUser()` | `useSession()` + `useUser()` hooks | |
| `Auth.currentSession()` | `useSession()` — `session.token` auto-refreshed | |
| `fetchAuthSession()` (v6) | `useSession()` — `session.token` | |
| `Amplify.configure({ Auth: ... })` | `<AuthProvider projectId="...">` | |
| `withAuthenticator` HOC | `<Descope flowId="sign-up-or-in">` component | |
| `<Authenticator>` component | `<Descope flowId="sign-up-or-in">` component | |
| `Hub.listen('auth', ...)` | `useSession().isAuthenticated` (reactive) | |
| `CognitoJwtVerifier.create(...)` | `DescopeClient({ projectId })` | Node.js backend |
| `cognitojwt.decode(...)` | `descope_client.validate_session(...)` | Python backend |
| `Admin.verifyIdToken` | `descopeClient.validateSession(token)` | |
| `AdminAddUserToGroup` | `management.user.setRoles(loginId, roles)` | |
| `AdminUserGlobalSignOut` | `management.user.logout(userId)` | |
| Cognito User Groups | Descope Roles | Migrated automatically by migration tool |
| `custom:*` attributes | Descope custom attributes | Create definitions in Console first |
| `cognito:username` claim | `sub` claim in Descope JWT | Different format |
| `cognito:groups` claim | Use `descopeClient.validateRoles()` | Not a raw JWT claim in Descope |
| Cognito Hosted UI | Descope Flow embeddable component | More customizable |
| Pre-Token Generation trigger | Descope JWT Templates | Configure in Console → Project Settings → JWT Templates |
| Cognito User Pool authorizer | Descope JWT authorizer in API Gateway | See Section 7 |

---

## 10. Terminology Mapping

| AWS Cognito | Descope |
|---|---|
| User Pool | Project |
| User Pool ID (`us-east-1_XXXX`) | Project ID (`Pxxx...`) |
| App Client | Inbound Application (or just uses Project ID) |
| User Group | Role |
| Identity Pool | Not replaced — use AWS Federation with Descope as IdP if needed |
| Hosted UI | Descope Flow (embeddable component) |
| Lambda Trigger | Flow step / Connector / Webhook |
| Pre-Token Generation | JWT Template |
| `custom:*` attribute | Custom Attribute (define schema in Console → Users → Attributes) |
| `cognito:username` | `sub` (Descope user ID) |
| `cognito:groups` | Roles (checked via SDK, not raw claim) |
| JWKS URL | `https://api.descope.com/v2/keys/{projectId}` |
| Management Key | Descope Management Key (`Kxxx...`) |
| AWS SDK (boto3, aws-sdk) | Descope SDK (node-sdk, python-sdk) |

---

## 11. Environment Variables

```bash
# Cognito (remove these)
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
NEXT_PUBLIC_AWS_REGION=...
NEXT_PUBLIC_USER_POOL_ID=...
NEXT_PUBLIC_USER_POOL_CLIENT_ID=...

# Descope (add these)
# Frontend (public — safe to expose)
VITE_DESCOPE_PROJECT_ID=Pxxx...           # React/Vite apps
NEXT_PUBLIC_DESCOPE_PROJECT_ID=Pxxx...   # Next.js apps
REACT_APP_DESCOPE_PROJECT_ID=Pxxx...     # Create React App

# Backend (secret — never expose to client)
DESCOPE_PROJECT_ID=Pxxx...
DESCOPE_MANAGEMENT_KEY=Kxxx...            # Only needed for management/admin operations
```

**Project ID** (starts with `P`): Console → Project Settings → Project ID
**Management Key** (starts with `K`): Console → Company → Management Keys → Create New Key

---

## 12. Key Gotchas

### 1. Passwords cannot be exported from Cognito
This is the most critical difference from Firebase. AWS Cognito does not expose password hashes. Full migration always requires either JIT migration (to preserve passwords) or a forced password-reset / passwordless flow on first sign-in. Plan this conversation with users before cutover.

### 2. User Pool ID vs App Client ID
Cognito requires both a User Pool ID and an App Client ID. Descope only needs a Project ID (frontend) and optionally a Management Key (backend admin). Remove all Cognito ID references from frontend code — they are unnecessary with Descope.

### 3. Identity Pools are separate
Cognito Identity Pools (for granting temporary AWS IAM credentials to users) are not replaced by Descope. If your app uses Identity Pools to let users access S3, DynamoDB, etc. directly, you need to configure Descope as a federated identity provider in the Identity Pool rather than removing Cognito entirely.

### 4. Amplify v5 vs v6 APIs differ significantly
Amplify v6 changed from class-based (`Auth.signIn`) to function-based (`signIn`) with tree-shaking. Identify which version is in use before writing migration code.

### 5. Cognito Hosted UI redirect flows
Apps using Cognito Hosted UI with OAuth redirect flows (PKCE) need to update the auth flow. Descope flows work inline (no hosted UI redirect by default) but can be configured as an OIDC/OAuth2 authorization server for apps that need the redirect pattern. Check if the app uses Cognito Hosted UI vs. custom UI.

### 6. Lambda Triggers contain custom business logic
Cognito Lambda triggers often hold critical business logic (e.g., blocking certain email domains at pre-signup, enriching tokens at pre-token-generation). Audit all Lambda triggers before migration and recreate each as a Descope Flow step, Connector call, or Webhook. Do not skip this step.

### 7. FORCE_CHANGE_PASSWORD users need special handling
Cognito users who have never signed in after being admin-created have `UserStatus: FORCE_CHANGE_PASSWORD`. These users cannot have their accounts migrated seamlessly — mark them with `freshlyMigrated: true` and route them through a password-set step in Descope.

### 8. API Gateway Cognito authorizer must be swapped
If using AWS API Gateway with a Cognito User Pool authorizer, the authorizer must be replaced with a Descope JWT authorizer (or Lambda authorizer calling Descope SDK) before the frontend migration. Do the backend authorizer swap first.

### 9. `cognito:groups` is a JWT claim; Descope roles are not
Code checking `token['cognito:groups']` directly must be updated to use `descopeClient.validateRoles(authInfo, roles)` or check `authInfo.token.roles`. The raw claim in Descope JWTs is `roles` (array of strings), not `cognito:groups`.

### 10. Custom attributes need schema pre-creation
Cognito custom attributes (`custom:department`) are migrated to Descope custom attributes. But Descope requires the attribute schema to be defined in the Console (Users → Attributes) before batch-importing users with those attributes. Pre-create all `custom:*` attribute definitions first.

### 11. Cognito MFA settings don't auto-migrate
If Cognito MFA (TOTP or SMS) was enabled per-user, those MFA enrollments don't transfer. Users will need to re-enroll in MFA through Descope flows after migration. Configure an appropriate MFA enrollment step in your Descope flow for this cohort.

### 12. Token claim names change — update all backend checks
Replace all `payload['cognito:username']` → `payload['sub']`, all `payload['cognito:groups']` → use SDK validation. Any hardcoded claim names in authorization logic will break silently if not updated.

---

## 13. Migration Checklist

### Pre-migration
- [ ] Audit all Cognito Lambda triggers — document their business logic
- [ ] Identify if Identity Pools are used (separate concern from User Pool migration)
- [ ] Identify Amplify v5 vs v6 in frontend codebase
- [ ] Export users from Cognito User Pool (using migration tool or boto3)
- [ ] Note users with `FORCE_CHANGE_PASSWORD` status
- [ ] Create custom attribute schema definitions in Descope Console (for `custom:*` attrs)
- [ ] Create Descope project and configure auth flows in Console
- [ ] Configure social connectors (Google, Apple, etc.) in Descope Console
- [ ] Plan password strategy: JIT migration (preserve) vs full migration (force reset)

### User migration
- [ ] Run `python3 src/main.py cognito --dry-run` and verify output
- [ ] Run `python3 src/main.py cognito` (live import)
- [ ] Verify user count and email coverage in Descope Console
- [ ] Confirm Cognito Groups → Descope Roles mapping is correct
- [ ] Plan/execute Cognito `sub` → Descope user ID mapping in database (if stored as FK)

### Backend
- [ ] Replace Cognito JWT validation (`aws-jwt-verify` / `cognitojwt`) with Descope SDK
- [ ] Replace `verifyToken` middleware with Descope `validateSession`
- [ ] Replace `cognito:groups` claim checks with `descopeClient.validateRoles()`
- [ ] Replace boto3/AWS SDK admin user operations with Descope management SDK
- [ ] Update AWS API Gateway: replace Cognito authorizer with Descope JWT authorizer
- [ ] Recreate Lambda trigger logic in Descope Flows/Connectors/Webhooks
- [ ] Update environment variables (remove Cognito IDs, add Descope Project ID)
- [ ] Add dual-token validation if running a gradual cutover

### Frontend
- [ ] Remove `aws-amplify` / `amazon-cognito-identity-js`; install Descope React/Next.js SDK
- [ ] Replace `Amplify.configure()` with `<AuthProvider projectId="...">`
- [ ] Replace `Auth.currentAuthenticatedUser()` / `getCurrentUser()` with `useSession()` + `useUser()`
- [ ] Replace `Auth.currentSession()` / `fetchAuthSession()` with `session.token` from `useSession()`
- [ ] Replace `Authenticator` component / custom sign-in forms with `<Descope flowId="sign-up-or-in" />`
- [ ] Replace `Auth.signOut()` with `logout()` from `useDescope()`
- [ ] Replace all `Hub.listen('auth', ...)` event listeners
- [ ] Update all environment variables (remove Cognito pool IDs)

### Testing
- [ ] Sign-up flow (new user)
- [ ] Sign-in with migrated credentials (JIT path or password-reset path, as applicable)
- [ ] Social login (Google, etc.)
- [ ] Session persistence across page refresh
- [ ] Token validation on backend
- [ ] Role/group-based access control
- [ ] Logout and session revocation
- [ ] Password reset flow
- [ ] Protected route access control
- [ ] API Gateway authorization (if applicable)
- [ ] MFA enrollment (if MFA was enabled in Cognito)

---

## 14. Useful Links

| Resource | URL |
|---|---|
| Cognito Migration Guide (Descope) | https://docs.descope.com/migrate/cognito |
| Descope Migration Tool | https://github.com/descope/descope-migration |
| React SDK | https://docs.descope.com/getting-started/react |
| Next.js SDK | https://docs.descope.com/getting-started/nextjs |
| Node.js SDK | https://github.com/descope/node-sdk |
| Python SDK | https://github.com/descope/python-sdk |
| Backend Session Validation | https://docs.descope.com/authorization/session-management/session-validation/backend |
| AWS API Gateway JWT Authorizer | https://docs.descope.com/authorization/session-management/session-validation/oidc-jwt-authorizers/aws-jwt-authorizer |
| JWT Templates | https://docs.descope.com/management/jwt-templates |
| Generic HTTP Connector (JIT) | https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http |
| Cognito as OIDC Provider in Descope | https://docs.descope.com/auth-methods/oauth/providers/custom-providers |
| Descope Console | https://app.descope.com |
| User Attribute Schema | https://app.descope.com/users/attributes |
