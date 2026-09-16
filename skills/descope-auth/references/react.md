# React Integration

## Install

```bash
npm install @descope/react-sdk
```

## Environment Variables

```bash
REACT_APP_DESCOPE_PROJECT_ID=<project-id>
```

The exact variable name/prefix depends on your bundler (Create React App needs the
`REACT_APP_` prefix and reads it from `process.env`; Vite needs a `VITE_` prefix and
reads it from `import.meta.env`). Only the prefix changes — the value is still your
Descope Project ID from https://app.descope.com/settings/project.

## 1. Wrap App with AuthProvider

```tsx
// src/App.tsx
import { AuthProvider } from '@descope/react-sdk';

function App() {
  return (
    <AuthProvider projectId={process.env.REACT_APP_DESCOPE_PROJECT_ID}>
      <Router />
    </AuthProvider>
  );
}
```

`AuthProvider` also accepts:

- `baseUrl` — required if your Descope project manages the session token in cookies
  via a custom domain (e.g. `https://auth.app.example.com`).
- `baseCdnUrl` — custom domain to override where external scripts/widgets are loaded from.
- `persistTokens` (default `true`) — set to `false` to avoid storing tokens in
  `localStorage` (reduces XSS risk).
- `autoRefresh` (default `true`) — set to `false` to disable automatic session refresh.
- `sessionTokenViaCookie` — store the session token in a JS cookie instead of
  `localStorage`. Only applies when the token is a client-readable cookie, not when
  Descope manages it as an `HttpOnly` backend cookie.
- `storeLastAuthenticatedUser` (default `true`) — persist the last-authenticated user's
  info in `localStorage` (used by `getUser()`).
- `customStorage` — provide your own storage backend (e.g. `sessionStorage`, an
  in-memory store, or an encrypted wrapper) instead of `localStorage`:

  ```tsx
  const inMemoryStorage = (() => {
    const map = new Map();
    return {
      getItem: (key: string) => (map.has(key) ? map.get(key) : null),
      setItem: (key: string, value: string) => { map.set(key, value); },
      removeItem: (key: string) => { map.delete(key); },
    };
  })();

  <AuthProvider projectId="my-project-id" customStorage={inMemoryStorage}>
    <App />
  </AuthProvider>
  ```

## 2. Create Login Page

```tsx
// src/pages/Login.tsx
import { Descope } from '@descope/react-sdk';
import { useNavigate } from 'react-router-dom';

function LoginPage() {
  const navigate = useNavigate();

  return (
    <Descope
      flowId="sign-up-or-in"
      onSuccess={(e) => {
        console.log('Authenticated:', e.detail.user);
        navigate('/dashboard');
      }}
      onError={(e) => console.error('Auth failed:', e.detail)}
    />
  );
}
```

You can also render one of the default flow components instead of passing a raw
`flowId` — `SignInFlow`, `SignUpFlow`, or `SignUpOrInFlow`:

```tsx
import { SignUpOrInFlow } from '@descope/react-sdk';

<SignUpOrInFlow
  onSuccess={(e) => console.log('Logged in!', e.detail.user)}
  onError={() => console.log('Could not log in')}
/>
```

## 3. Protect Routes

```tsx
// src/components/ProtectedRoute.tsx
import { useSession } from '@descope/react-sdk';
import { Navigate } from 'react-router-dom';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isSessionLoading } = useSession();

  if (isSessionLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" />;

  return <>{children}</>;
}
```

> **Important:** always gate on `isAuthenticated`, never on `sessionToken`.
> `sessionToken` is an empty string whenever the token isn't accessible to client-side
> code — for example when Descope manages the session as a `Secure` + `HttpOnly`
> cookie, or when `persistTokens={false}` is set. In those setups the user is fully
> authenticated while `sessionToken` reads empty, so guarding logic on it silently
> breaks for those users. Read `sessionToken` only when you need the raw JWT (e.g. to
> attach it to an API request), and read `claims` for claims out of the session.

## 4. Access User Data

```tsx
// src/components/UserProfile.tsx
import { useUser, useDescope } from '@descope/react-sdk';

function UserProfile() {
  const { user, isUserLoading } = useUser();
  const { logout } = useDescope();

  if (isUserLoading) return <div>Loading...</div>;

  return (
    <div>
      <p>Welcome, {user?.name}</p>
      <p>Email: {user?.email}</p>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}
```

`user` also includes `loginIds`, `userId`, `verifiedEmail`, `verifiedPhone`,
`roleNames`, and `userTenants` (each with `tenantId`, `tenantName`, `roleNames`,
`permissions`).

## 5. Router Setup

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@descope/react-sdk';
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AuthProvider projectId={process.env.REACT_APP_DESCOPE_PROJECT_ID}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```

## Session Helper Functions

In addition to `useSession`'s `isAuthenticated` / `isSessionLoading` /
`sessionToken` / `claims`, the SDK exports standalone helpers:

```tsx
import {
  getSessionToken, getRefreshToken, isSessionTokenExpired, isRefreshTokenExpired,
  getJwtRoles, getJwtPermissions, getCurrentTenant,
} from '@descope/react-sdk';

const token = getSessionToken();
const expired = isSessionTokenExpired(token);
const roles = getJwtRoles(token, '<tenant-id>'); // tenant id optional
const permissions = getJwtPermissions(token, '<tenant-id>');
const tenantId = getCurrentTenant(token);
```

`getRefreshToken` (and anything derived from the refresh token) won't work if refresh
tokens are stored in `httpOnly` cookies — they aren't accessible from the frontend
in that case.

## Core SDK Functions (via `useDescope`)

```tsx
const sdk = useDescope();

sdk.refresh({ skipIfNoSession: true }); // refresh the session token
sdk.selectTenant(tenantId);             // switch the `dct` claim in the JWT
sdk.myTenants(true);                    // tenant info for the current user
sdk.history();                          // current user's auth history
sdk.logout();                           // log out the current session
sdk.logoutAll();                        // log out all sessions for the user
sdk.me();                               // refetch current user details
sdk.isJwtExpired(token);                // check expiry without verifying signature
sdk.getTenants(token);                  // tenants listed in a JWT
```

`useSession` triggers one request on mount to try to refresh the session. If your app
never calls `useSession`, sessions won't auto-refresh — call `sdk.refresh()` yourself
(e.g. in a top-level `useEffect`).

### Auto Refresh

The SDK automatically refreshes the session token before it expires. Disable this
with `autoRefresh={false}` on `AuthProvider`. To skip refreshing for idle users, pass
`autoRefresh={{ customActivityTracking: true }}` and call `sdk.markUserActive()` on
user interactions (click/keydown/touchstart/tab-visible) from a component rendered
inside `AuthProvider`.

### Listening for Auth State Changes

```tsx
const sdk = useDescope();

useEffect(() => {
  const unsubToken = sdk.onSessionTokenChange((newSession, oldSession) => {});
  const unsubAuth = sdk.onIsAuthenticatedChange((isAuthenticated) => {});
  const unsubUser = sdk.onUserChange((newUser, oldUser) => {});
  const unsubClaims = sdk.onClaimsChange((newClaims, oldClaims) => {});
  return () => {
    unsubToken(); unsubAuth(); unsubUser(); unsubClaims();
  };
}, [sdk]);
```

### Refreshing User Data

`sdk.refresh()` updates the session token but does not re-fetch the user object. When
a user is updated out-of-band (backend Management SDK/API, SCIM, admin action), call
`sdk.me()` to refetch the user, or both `refresh()` then `me()` if you need updated
claims and user data together.

## OIDC Login

To use the SDK as an OIDC client against a Descope Federated App, pass `oidcConfig`
to `AuthProvider`:

```tsx
<AuthProvider
  projectId="my-project-id" // also serves as the client ID
  oidcConfig={{
    applicationId: 'my-application-id', // optional; default OIDC app if omitted
    redirectUri: 'https://my-app.com/redirect', // optional
    scope: 'openid profile email', // optional
  }}
>
  <App />
</AuthProvider>
```

## Vanilla / Framework-Agnostic Alternative

If you don't want React hooks or `AuthProvider` session management, the flow
component itself is also published as a framework-agnostic custom element,
[`@descope/web-component`](https://www.npmjs.com/package/@descope/web-component)
(`<descope-wc>`). See `references/vanilla-js.md` for that lower-level integration —
it does not provide `useSession` / `useUser` / `useDescope` or automatic session
management.
