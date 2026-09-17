---
type: fixed
expect:
  query: string
---
Results for "{{input.query}}":
1. Session Validation (Node.js SDK) — https://docs.descope.com/session-management/session-validation — Use `descopeClient.validateSession(sessionToken)` to validate a session JWT. Use `validateAndRefreshSession(sessionToken, refreshToken)` to refresh when expired.
2. Next.js SDK: authMiddleware — https://docs.descope.com/getting-started/nextjs — `authMiddleware({ projectId, redirectUrl, publicRoutes })` from `@descope/nextjs-sdk/server` protects routes.
3. Session Management Overview — https://docs.descope.com/session-management
