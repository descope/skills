---
name: descope-auth
description: Integrate Descope authentication into applications. Use when implementing login, signup, passwordless auth (OTP, Magic Link, Passkeys), OAuth, SSO, or MFA. Detects framework and provides targeted guidance.
---

# Descope Authentication

Integrate secure, passwordless authentication using Descope Flows and SDKs.

## Framework Detection

Detect the user's framework and use the appropriate reference:

| If project has... | Use reference |
|-------------------|---------------|
| `next` in package.json | `references/nextjs.md` |
| `react` (no Next.js) | `references/react.md` |
| `@angular/core` in package.json | `references/angular.md` |
| No frontend framework (plain HTML/JS) | `references/vanilla-js.md` |
| Native Android app (`com.android.application` in `build.gradle(.kts)`, not Flutter/React Native) | `references/kotlin.md` |
| Native iOS app (`.xcodeproj`/`.xcworkspace` or iOS `Package.swift`, not Flutter/React Native) | `references/swift.md` |
| Python/Node.js backend only | `references/backend.md` |

## Quick Start (all frameworks)

1. **Get a Project ID.** Go in this order and stop at the first step that works:
   1. **Already configured:** if the app already has a Descope Project ID (e.g. `NEXT_PUBLIC_DESCOPE_PROJECT_ID`, `DESCOPE_PROJECT_ID`, `VITE_DESCOPE_PROJECT_ID` in env files), reuse it. Do not create a new project.
   2. **Descope MCP Server connected** (it exposes a `session` tool): call `session` with action `getProjectStatus`, show the user the selected project's name and ID, and use it once they confirm. To use a different one (or if none is selected), call `session` with action `listProjects`, ask the user, then select their choice (`session` with action `selectProject`). Create a new project only when the user asks for one.
   3. **Not connected:** lead with the Descope MCP Server, not the Console: tell the user to connect it at `https://mcp.descope.com` and say that you will then pick or create the project and configure it for them (other regions and per-client setup: https://docs.descope.com/mcp/mcp-server). The user signs in once in the browser; users without a Descope account can sign up there and get a project. Some clients need a restart to pick up a new MCP server. Once connected, go back to sub-step 2 above (`getProjectStatus`).
   4. **User prefers not to use the MCP:** ask for the Project ID from https://app.descope.com/settings/project.
2. Configure the Project ID per the framework reference (e.g. `NEXT_PUBLIC_DESCOPE_PROJECT_ID=<your-id>` for Next.js, `Descope.setup(...)` for Android and iOS)
3. Follow framework-specific reference
4. **Verify**: After setup, confirm the `<Descope>` component renders the login form. Check the browser console — a missing or invalid Project ID produces a clear `Could not load flows` error.

When the Descope MCP Server is connected, use it for project configuration (e.g. enabling Google login, MFA settings, editing flows) instead of sending the user to the Console. Before any change, make sure the MCP session targets the app's project: select it (`session` with action `selectProject`) and confirm its ID matches the Project ID the app is configured with. Then get the user's approval for that change and call `session` with action `elevate`. If the user declines, skip the change.

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

For React SPA, Android, iOS, or backend-only setups, see the framework-specific references below.

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
- DO NOT store tokens in localStorage (web), plain SharedPreferences (Android), or UserDefaults (iOS) - SDK handles this securely
- DO NOT invent flow IDs - only use IDs from the table above
- DO NOT skip server-side validation - always validate on backend
- DO NOT expose DESCOPE_MANAGEMENT_KEY in client code

## References

- `references/nextjs.md` - Next.js App Router & Pages Router integration
- `references/react.md` - React SPA integration
- `references/angular.md` - Angular integration
- `references/vanilla-js.md` - Vanilla JavaScript / plain HTML integration
- `references/kotlin.md` - Kotlin / Android integration (Native Flows)
- `references/swift.md` - Swift / iOS integration (Native Flows, SwiftUI and UIKit)
- `references/backend.md` - Backend session validation
