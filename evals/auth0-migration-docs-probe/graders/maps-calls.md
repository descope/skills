---
type: llm
---
PASS if the reply maps the Auth0 calls to Descope equivalents: `getSession()` to the Descope Next.js server-side session helper, `useUser()` to a Descope client hook such as `useUser` or `useSession` from `@descope/nextjs-sdk/client`, and the Auth0 middleware to Descope `authMiddleware`.
FAIL if any of the three mappings is missing, or if the reply only asks the user to install something and stops.
