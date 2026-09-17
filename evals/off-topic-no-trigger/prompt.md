---
description: Negative control. An unrelated request must not trigger any Descope skill.
tags: [control, negative]
max_turns: 5
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Answers directly with a Python function. No Skill call.
---
Write a Python function that returns the reversed form of a string, with one example call.
