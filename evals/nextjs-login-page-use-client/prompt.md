---
description: App Router page.tsx is a Server Component by default; passing onSuccess/onError function props to <Descope> requires 'use client'. The skill's inline example omits it. Issue descope/skills#28 item 3. Needs --allow-tools Write.
tags: [auth, issue-28, nextjs]
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write]
expected_outcome: Writes src/app/login/page.tsx with 'use client' at the top (or extracts a client component), uses the sign-up-or-in flow and onSuccess.
---
Add a Descope login page to my Next.js 14 App Router project. Create the file at `src/app/login/page.tsx`. Use the `sign-up-or-in` flow and log the authenticated user to the console on success. Write the file.
