# Next.js Integration

## Install

```bash
npm install @descope/nextjs-sdk
```

## Environment Variables

```bash
NEXT_PUBLIC_DESCOPE_PROJECT_ID=<project-id>
DESCOPE_MANAGEMENT_KEY=<management-key>  # For server-side management operations
```

## 1. Wrap App with AuthProvider

```tsx
// src/app/layout.tsx
import { AuthProvider } from '@descope/nextjs-sdk';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider projectId={process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID!}>
      <html lang="en">
        <body>{children}</body>
      </html>
    </AuthProvider>
  );
}
```

## 2. Add Login Page

```tsx
// src/app/login/page.tsx
import { Descope } from '@descope/nextjs-sdk';

export default function LoginPage() {
  return (
    <Descope
      flowId="sign-up-or-in"
      onSuccess={(e) => console.log('Authenticated:', e.detail.user)}
      onError={(e) => console.error('Auth failed:', e.detail)}
      redirectAfterSuccess="/"
    />
  );
}
```

## 3. Protect Routes with Middleware

```typescript
// src/middleware.ts
import { authMiddleware } from '@descope/nextjs-sdk/server';

export default authMiddleware({
  // Defaults to process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID
  projectId: process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID,
  // Defaults to process.env.SIGN_IN_ROUTE or '/sign-in'
  redirectUrl: '/login',
  // publicRoutes are ADDED to the defaults (SIGN_IN_ROUTE/'/sign-in' and
  // SIGN_UP_ROUTE/'/sign-up'), all other routes are private by default.
  publicRoutes: ['/login', '/signup', '/api/public/*'],
  // privateRoutes is ignored (with a warning) if publicRoutes is also set.
  // logLevel: 'debug' | 'info' | 'warn' | 'error' (default 'info')
});

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)']
};
```

> **Next.js 16:** the `middleware.ts` file convention is deprecated and renamed
> `proxy.ts` (same behavior, same `config`/`matcher`). `middleware.ts` still works
> today, but on Next.js 16+ use `proxy.ts`, or run
> `npx @next/codemod@canary middleware-to-proxy .`. Requires Next.js 13+.

Middleware validates the session JWT once and attaches the result to the request as
an `X-Descope-Session` header, so server components/route handlers using `session()`
below don't need to re-validate it — though `session()` also works without the
middleware (it falls back to reading/validating the token from cookies itself).

## 4. Access Session in Client Components

```tsx
'use client';
import { useSession, useUser, useDescope } from '@descope/nextjs-sdk/client';

export function UserProfile() {
  const { isAuthenticated, isSessionLoading } = useSession();
  const { user } = useUser();
  const { logout } = useDescope();

  if (isSessionLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <div>Not logged in</div>;

  return (
    <div>
      <p>Welcome, {user?.name}</p>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}
```

The same session helpers, core SDK functions (`refresh`, `selectTenant`, `logout`,
`me`, etc.), and state-change listeners documented in `references/react.md` are
available here from `@descope/nextjs-sdk/client` instead of `@descope/react-sdk`.

## 5. Server-Side Session Access

**App Router** (Server Components, Route Handlers, and Middleware) — use `session()`:

```typescript
// src/app/api/protected/route.ts
import { session } from '@descope/nextjs-sdk/server';

export async function GET() {
  const currentSession = await session();
  if (!currentSession) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }
  // currentSession.jwt is the raw JWT, currentSession.token is the parsed claims
  return Response.json({ user: currentSession.token.sub });
}
```

```tsx
// src/app/dashboard/page.tsx (Server Component)
import { session } from '@descope/nextjs-sdk/server';

export default async function Dashboard() {
  const currentSession = await session();
  if (!currentSession) return <p>Access Denied</p>;
  return <p>Welcome, {currentSession.token.sub}</p>;
}
```

**Pages Router API routes only** (`pages/api/`) — use `getSession(req)` instead;
it does not work in Middleware or Server Components:

```typescript
// pages/api/protected.ts
import { getSession } from '@descope/nextjs-sdk/server';
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const currentSession = getSession(req);
  if (!currentSession) {
    return res.status(401).json({ message: 'Unauthorized' });
  }
  return res.status(200).json({ user: currentSession.token.sub });
}
```

| Function | Use case | Middleware | API routes | Server Components |
|---|---|---|---|---|
| `session()` | App Router, Middleware, Server Components | Yes | Yes | Yes |
| `getSession(req)` | Pages Router API routes | No | Yes | No |

If middleware didn't already set the session, `session()` falls back to reading and
validating the token from cookies itself — this requires `projectId` to be available
via `NEXT_PUBLIC_DESCOPE_PROJECT_ID` or passed explicitly: `session({ projectId, baseUrl, logLevel })`.

## 6. Loading the Full User Profile Server-Side

`session()`/`getSession(req)` only return what's in the JWT. To fetch the full user
record for the already-authenticated `sub` (e.g. custom attributes not in the
token), use `createSdk()`:

```typescript
import { createSdk, session } from '@descope/nextjs-sdk/server';

const sdk = createSdk({
  projectId: process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID,
  managementKey: process.env.DESCOPE_MANAGEMENT_KEY,
});

export async function GET() {
  const currentSession = await session();
  if (!currentSession) return new Response('Unauthorized', { status: 401 });

  const { ok, data: user } = await sdk.management.user.load(currentSession.token.sub);
  if (!ok) return new Response('User not found', { status: 404 });
  return Response.json(user);
}
```

Never expose `DESCOPE_MANAGEMENT_KEY` to client code — only use `createSdk` in
server-only files (route handlers, server components, server actions).
