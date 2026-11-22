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

## 1. Wrap App with AuthProvider and SessionKeeper

```tsx
// src/app/layout.tsx
import { AuthProvider } from '@descope/nextjs-sdk';
import { SessionKeeper } from './components/SessionKeeper';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider projectId={process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID!}>
      <html lang="en">
        <body>
          <SessionKeeper />
          {children}
        </body>
      </html>
    </AuthProvider>
  );
}
```

`AuthProvider` alone does not refresh the session. The SDK starts refreshing once a
component calls `useSession()`. Without `SessionKeeper`, a page that never calls it keeps
the expired session token, and server actions on that page fail. Once started, the SDK
also renews an expired token when the user returns to a background tab.

```tsx
// src/app/components/SessionKeeper.tsx
'use client';

import { useSession } from '@descope/nextjs-sdk/client';

export function SessionKeeper() {
  useSession(); // starts the SDK's session refresh on every page
  return null;
}
```

## 2. Add Sign-In Page

The sign-in page must not show the login flow straight away. A user sent here may
still have a valid refresh token, so wait for `useSession()` to finish loading: if the
SDK renewed the session, send the user back to the page they asked for (`next`).
Show the flow only when there is no usable session.

```tsx
// src/app/sign-in/page.tsx
'use client';

import { Suspense, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Descope } from '@descope/nextjs-sdk';
import { useSession } from '@descope/nextjs-sdk/client';
import { ensureFreshSession } from '@/lib/ensureFreshSession'; // section 5

// Only allow paths inside this app, so ?next= can't send users to another site.
// Parse instead of string checks: browsers strip tabs and newlines from URLs, so
// "/\t/evil.com" passes a startsWith('/') check and still leaves the site.
function safeNext(value: string | null): string {
  if (!value) return '/';
  try {
    const base = 'http://app.invalid'; // placeholder origin, only used for parsing
    const url = new URL(value, base);
    if (url.origin !== base || url.pathname.startsWith('//') || url.pathname.startsWith('/sign-in')) {
      return '/';
    }
    return url.pathname + url.search + url.hash;
  } catch {
    return '/';
  }
}

const LAST_RETURN_KEY = 'sign-in-last-return';

function SignIn() {
  const router = useRouter();
  const params = useSearchParams();
  const next = safeNext(params.get('next'));
  const renewFailed = params.has('renewFailed');
  const { isAuthenticated, isSessionLoading } = useSession();

  const returning = useRef(false);

  useEffect(() => {
    // Run once per mount: React Strict Mode runs effects twice in development.
    if (!isAuthenticated || renewFailed || returning.current) return;
    returning.current = true;
    (async () => {
      // Sent back here seconds after returning the user: the server is rejecting the
      // renewed session. Show the login flow instead of looping. Measure from page
      // load, so a slow refresh doesn't hide the loop.
      const startedAt = Date.now();
      const last = Number(sessionStorage.getItem(LAST_RETURN_KEY) ?? 0);
      // The SDK can report a session whose token is still being renewed.
      await ensureFreshSession();
      if (startedAt - last < 10_000) {
        router.replace(`/sign-in?renewFailed=1&next=${encodeURIComponent(next)}`);
        return;
      }
      sessionStorage.setItem(LAST_RETURN_KEY, String(Date.now()));
      router.replace(next);
    })();
  }, [isAuthenticated, renewFailed, next, router]);

  // Let the SDK renew the session from the refresh token before showing the login flow.
  if (!renewFailed && (isSessionLoading || isAuthenticated)) {
    return <p>Checking your session...</p>;
  }

  return (
    <Descope
      flowId="sign-up-or-in"
      onSuccess={() => {
        sessionStorage.removeItem(LAST_RETURN_KEY);
        router.replace(next);
      }}
      onError={(e) => console.error('Auth failed:', e.detail)}
    />
  );
}

export default function SignInPage() {
  return (
    <Suspense>
      <SignIn />
    </Suspense>
  );
}
```

Do not replace this with `redirectAfterSuccess="/"`: it shows the flow to users who are
still signed in and drops the page they asked for.

## 3. Protect Routes with Middleware

`authMiddleware` lets a request through when the session token has expired but the
refresh token is still valid. `session()` reads only the session token, so in that
case it returns `undefined` and the page treats a signed-in user as signed out. The
proxy below handles that split:

- **Page loads** require a valid session token (`skipRefreshTokenValidation: true`).
  Without one, the user goes to `/sign-in?next=<requested page>`, the sign-in page
  renews the session, and sends them back. Server Components can then trust `session()`.
- **Server actions and API routes** keep the default, so a valid refresh token is enough
  to pass. Each handler checks `session()` itself and returns 401 (or an error the
  client handles) when it is `undefined`. Requests with no valid token at all are
  still redirected to `/sign-in` by the middleware.

```typescript
// src/proxy.ts (Next.js 16+) or src/middleware.ts (Next.js 13-15)
import { NextResponse, type NextRequest } from 'next/server';
import { authMiddleware } from '@descope/nextjs-sdk/server';

// Added to the defaults ('/sign-in', '/sign-up'). All other routes are private.
const publicRoutes = ['/', '/sign-in', '/api/public/*'];

const pageAuth = authMiddleware({
  // projectId defaults to process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID
  redirectUrl: '/sign-in',
  publicRoutes,
  skipRefreshTokenValidation: true,
});

const requestAuth = authMiddleware({ redirectUrl: '/sign-in', publicRoutes });

export default async function proxy(req: NextRequest) {
  const isPageLoad =
    req.method === 'GET' &&
    !req.headers.has('next-action') &&
    !req.nextUrl.pathname.startsWith('/api');
  if (!isPageLoad) return requestAuth(req);

  const res = await pageAuth(req);
  if (res.headers.get('location')) {
    // Redirected to sign-in: remember the page the user asked for.
    const signIn = new URL('/sign-in', req.url);
    signIn.searchParams.set('next', req.nextUrl.pathname + req.nextUrl.search);
    return NextResponse.redirect(signIn);
  }
  return res;
}

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)']
};
```

> **Next.js 16:** the `middleware.ts` file convention is deprecated and renamed
> `proxy.ts` (same behavior, same `config`/`matcher`). On Next.js 13-15, name the file
> `middleware.ts`. `skipRefreshTokenValidation` requires `@descope/nextjs-sdk` 0.16.0
> or later. If the app sets `basePath`, or serves GET route handlers outside `/api`,
> adjust the sign-in URL and the `isPageLoad` check to match.

`session()` validates the token from the `Authorization` header or the session cookie
on each call, with or without the middleware.

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
import { redirect } from 'next/navigation';
import { session } from '@descope/nextjs-sdk/server';

export default async function Dashboard() {
  const currentSession = await session();
  // With the proxy from section 3 this only happens on a public route.
  if (!currentSession) redirect('/sign-in?next=/dashboard');
  return <p>Welcome, {currentSession.token.sub}</p>;
}
```

`session()` reads only the session token, never the refresh token. `undefined` can
mean "session token expired, refresh token still valid", so don't show "Access Denied"
for it on a page. Send the user through `/sign-in` with `next`, which renews the session
without asking them to sign in again.

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

### Calling Server Actions After Idle

When the user returns to a background tab, the SDK renews the expired session token
in the background, which takes a moment. A server action that runs in that window
reaches the server without a valid session token, and `session()` returns
`undefined`. From a client component, wait for the renewal before calling the action:

```typescript
// src/lib/ensureFreshSession.ts
'use client';

import { getSessionToken, isSessionTokenExpired, refresh } from '@descope/nextjs-sdk/client';

export async function ensureFreshSession() {
  const token = getSessionToken();
  // getSessionToken() returns '' when Descope manages the token as an HttpOnly
  // cookie. Then this does nothing and the SDK's background renewal applies.
  if (token && isSessionTokenExpired(token)) {
    await refresh().catch(() => {});
  }
}
```

```tsx
// src/app/projects/[id]/settings/SaveForm.tsx
'use client';

import { ensureFreshSession } from '@/lib/ensureFreshSession';
import { saveDescription } from './actions';

export function SaveForm({ id }: { id: string }) {
  return (
    <form
      action={async (formData) => {
        await ensureFreshSession();
        await saveDescription(id, formData);
      }}
    >
      <input name="description" />
      <button type="submit">Save</button>
    </form>
  );
}
```

The server action still checks `session()` itself and rejects the call when it is
`undefined`. The client-side wait only avoids failing a user whose session is valid.

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
