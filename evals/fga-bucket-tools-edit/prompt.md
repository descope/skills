---
description: Editing an existing schema through bucket tools. Must read the current schema first (GetFGASchema via access_control_read) before dry-running the edit. Issue descope/skills#28 item 1.
tags: [fga, issue-28, bucket, edit]
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Reads current schema via access_control_read GetFGASchema, then adds Team type and editor relation with Team#member, dry-runs, shows DSL, waits for confirmation.
---
Add team-based access to my existing Descope FGA schema: create a Team type with members, and let members of a team be editors of a Project. Keep everything that is already there.
