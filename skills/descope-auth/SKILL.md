---
name: descope-auth
description: Integrate Descope authentication into applications. Use when implementing login, signup, passwordless auth (OTP, Magic Link, Passkeys), OAuth, SSO, or MFA. Detects framework (including React Native and Expo) and provides targeted guidance.
---

# Descope Authentication

Integrate secure, passwordless authentication using Descope Flows and SDKs.

## Framework Detection

Detect the user's framework and use the appropriate reference:

| If project has... | Use reference |
|-------------------|---------------|
| `next` in package.json | `references/nextjs.md` |
| `react-native` dependency (bare React Native or Expo); `react-native-web` alone does not count | `references/react-native.md` |
| `react` (no Next.js, no React Native) | `references/react.md` |
| `@angular/core` in package.json | `references/angular.md` |
| No frontend framework (plain HTML/JS) | `references/vanilla-js.md` |
| Native Android app (`com.android.application` in `build.gradle(.kts)`, not Flutter/React Native) | `references/kotlin.md` |
| Native iOS app (`.xcodeproj`/`.xcworkspace` or iOS `Package.swift`, not Flutter/React Native) | `references/swift.md` |
| Python/Node.js backend only | `references/backend.md` |

If more than one row matches, use the first match, except that a `react-native` or `expo` dependency (not `react-native-web`) always wins over `next` and `react`: a React Native app in a monorepo gets `references/react-native.md`. If there is no `package.json` yet and the user says they are building a React Native or Expo app, use `references/react-native.md`.

## Quick Start (all frameworks)

1. Get Project ID from https://app.descope.com/settings/project
2. Configure the Project ID per the framework reference (e.g. `NEXT_PUBLIC_DESCOPE_PROJECT_ID=<your-id>` for Next.js, `Descope.setup(...)` for Android and iOS, `<AuthProvider projectId="...">` for React Native)
3. Follow framework-specific reference
4. **Verify**: After setup, confirm the flow renders the login form (the `<Descope>` component on web, `FlowView` in React Native). On web, check the browser console — a missing or invalid Project ID produces a clear `Could not load flows` error.

### Minimal Inline Example (Next.js)

```tsx
// src/app/login/page.tsx
import { Descope } from '@descope/nextjs-sdk';

export default function LoginPage() {
  return (
    <Descope
      flowId="sign-up-or-in"
      onSuccess={(e) => console.log('Authenticated:', e.detail.user)}
      onError={(e) => console.error('Auth failed:', e.detail)}
    />
  );
}
```

For React SPA, React Native, Android, iOS, or backend-only setups, see the framework-specific references below.

## Valid Flow IDs (CRITICAL - do not invent others)

| Flow ID | Purpose |
|---------|---------|
| `sign-up-or-in` | Combined signup/login (RECOMMENDED) |
| `sign-up` | Registration only |
| `sign-in` | Login only |
| `step-up` | MFA step-up authentication |
| `update-user` | Profile updates, add auth methods |

## Authentication Methods

| Method | When to use |
|--------|-------------|
| OTP (Email/SMS) | Quick verification codes |
| Magic Link | Passwordless email links |
| Passkeys | Biometric/WebAuthn (most secure) |
| OAuth | Social login (Google, GitHub, etc.) |
| SSO | Enterprise SAML/OIDC |
| Passwords | Traditional auth (not recommended) |

## DO NOT (Security Guardrails)

- DO NOT parse JWTs manually - always use SDK's `validateSession()`
- DO NOT store tokens in localStorage (web), plain SharedPreferences (Android), UserDefaults (iOS), or AsyncStorage (React Native) - SDK handles this securely
- DO NOT invent flow IDs - only use IDs from the table above, unless the user or task gives you a specific flow ID
- DO NOT skip server-side validation - always validate on backend
- DO NOT expose DESCOPE_MANAGEMENT_KEY in client code

## References

- `references/nextjs.md` - Next.js App Router & Pages Router integration
- `references/react.md` - React SPA integration
- `references/angular.md` - Angular integration
- `references/vanilla-js.md` - Vanilla JavaScript / plain HTML integration
- `references/kotlin.md` - Kotlin / Android integration (Native Flows)
- `references/swift.md` - Swift / iOS integration (Native Flows, SwiftUI and UIKit)
- `references/react-native.md` - React Native / Expo integration (FlowView)
- `references/backend.md` - Backend session validation
