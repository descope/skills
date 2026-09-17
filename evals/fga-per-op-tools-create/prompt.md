---
description: Control case. The server exposes per-operation tools (GetFGASchema, DryRunSchema, CreateFGASchema) as the original skill assumes. A fix for issue 28 must not break this path.
tags: [fga, control, per-op]
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Probes GetFGASchema, drafts DSL, dry-runs, shows DSL, stops for confirmation.
---
Set up authorization for my docs app with Descope FGA. Users own documents. Documents live in folders. A document owner can view and edit it. A folder owner can view every document inside that folder. Members of a Team can be given viewer access to a document.
