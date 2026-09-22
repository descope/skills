---
description: Descope MCP exposes bucket tools (access_control_read/write), not per-operation tools. The skill must still proceed. Issue descope/skills#28 item 1.
tags: [fga, issue-28, bucket]
max_turns: 15
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Skill loads, probes GetFGASchema via access_control_read, drafts a DSL, dry-runs it via access_control_read, shows the DSL and stops for confirmation. Never prints the "MCP is required" stop message. Never calls access_control_write.
---
Set up authorization for my docs app with Descope FGA. Users own documents. Documents live in folders. A document owner can view and edit it. A folder owner can view every document inside that folder. Members of a Team can be given viewer access to a document.
