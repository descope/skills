---
description: Control case. No Descope MCP tools are available at all. The skill must print the stop message and must not draft a schema. A fix for issue 28 must keep this behavior.
tags: [fga, control, no-mcp]
max_turns: 8
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Prints the "Descope Management MCP is required" message and ends the turn without any DSL.
---
Set up authorization for my docs app with Descope FGA. Users own documents. A document owner can view and edit it.
