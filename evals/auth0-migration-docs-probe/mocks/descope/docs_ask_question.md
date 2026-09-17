---
type: fixed
expect:
  question: string
---
Answer (from Descope docs): For "{{input.question}}" — In `@descope/nextjs-sdk`, server-side session access is `import { session } from '@descope/nextjs-sdk/server'` and `const s = await session()` (async in Next.js 15; sync-compatible in 14). Client-side use `useSession()` from `@descope/nextjs-sdk/client`. Backend validation uses `validateSession` from `@descope/node-sdk`.
