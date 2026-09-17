---
description: The Descope MCP server proxies docs as docs_search and docs_ask_question, not search-descope-docs. The auth0 migration skill must find them and must not tell the user to install a docs MCP they already have. Issue descope/skills#28 item 2.
tags: [migration, issue-28, docs]
max_turns: 12
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Calls docs_search as the availability probe, proceeds, and does not print the "Descope Docs MCP is not installed" message.
---
I'm migrating a Next.js 14 App Router app from Auth0 to Descope. Today it uses `@auth0/nextjs-auth0` with `getSession()` in server components and `useUser()` on the client, and the Auth0 middleware protects `/dashboard/*`. First step only for now: confirm you can reach the Descope docs, then list which of my Auth0 calls change and what they map to in Descope. Do not write any files yet.
