# Next.js Integration

## Install

```bash
npm install @descope/nextjs-sdk
```

## Environment Variables

```bash
NEXT_PUBLIC_DESCOPE_PROJECT_ID=<project-id>
DESCOPE_MANAGEMENT_KEY=<management-key>  # For server operations
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
  projectId: process.env.NEXT_PUBLIC_DESCOPE_PROJECT_ID,
  redirectUrl: '/login',
  publicRoutes: ['/login', '/signup', '/api/public/*'],
});

export const config = {
  matcher: ['/((?!.+\\.[\w]+$|_next).*)', '/', '/(api|trpc)(.*)']
};
```

## 4. Access Session in Components

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

## 5. Server-Side Session Access

```typescript
// src/app/api/protected/route.ts
import { getSession } from '@descope/nextjs-sdk/server';

export async function GET() {
  const session = await getSession();
  if (!session) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }
  return Response.json({ user: session.user });
}
```
