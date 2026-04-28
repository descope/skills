# CLAUDE.md — Descope Skills Repo

## Plugin Version Bumps

Every PR must bump the version in `.claude-plugin/plugin.json`. Use semantic versioning:

| Change type | Bump | Examples |
|---|---|---|
| Edit to an existing skill | **patch** (`1.0.0 → 1.0.1`) | Fix a code example, reword an instruction, add a clarification |
| New skill added | **minor** (`1.0.0 → 1.1.0`) | Add a new `SKILL.md` under `skills/` |
| Breaking change to an existing skill | **major** (`1.0.0 → 2.0.0`) | Rename a skill, remove a skill, change behavior in a way that breaks existing workflows |

Breaking changes should be very rare. When in doubt, treat a change as non-breaking (patch or minor).
