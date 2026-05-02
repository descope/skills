---
name: auth-review
description: Static security review for authentication and authorization vulnerabilities. Use when the user invokes /auth-review, asks to audit auth, find identity breaches, review access control, hunt for IDOR/BOLA, or check authorization. Framework- and vendor-agnostic. Enumerates every route/endpoint, builds an authorization matrix, applies a vulnerability catalog, and writes a triage report ready to turn into issues or PRs.
---

# Auth Review

Perform a **static, read-only** security review of authentication and authorization in the current codebase. Framework- and vendor-agnostic. Output: a triage report in `./auth-review/` with findings ready to file as issues or PRs.

## When to Use

- User invokes `/auth-review`.
- Requests like "audit auth", "find authz bugs", "review access control", "check for IDOR", "identity security review".
- Pre-release hardening or post-incident forensic code review focused on identity.

## Workflow

Run these phases **in order**. Do not skip ahead.

### Phase 1 — Enumerate every entrypoint

Identify every code path reachable by an external or semi-trusted caller. See `references/enumeration.md` for exhaustive patterns. A single repo often mixes HTTP, GraphQL, WebSocket, queue consumers, serverless handlers, and admin CLIs — list them all.

**Deliverable:** an **Endpoint Inventory** table: `method`, `path / trigger`, `handler (file:line)`, `auth required? (y/n/unknown)`, `roles or scopes`, `notes`.

Reconcile against router files, OpenAPI specs, and GraphQL schemas before moving on.

### Phase 2 — Build the authorization matrix

For each endpoint answer: *who should reach this, and what does the code actually enforce?* Use `references/authz-matrix.md` to infer the expected principal from conventions and classify gaps.

**Deliverable:** an **Authorization Matrix** table: `endpoint`, `expected principal`, `enforced check (file:line)`, `gap`.

### Phase 3 — Apply the vulnerability catalog

Walk `references/vulnerability-catalog.md` category by category. For each, run the detection heuristics, then **read** the matched files to confirm. Never flag from a grep hit alone.

Before calling a check missing, confirm no upstream middleware, decorator, guard, filter, interceptor, framework default, or reverse proxy enforces it. Trace at least one concrete caller path end-to-end for each finding. If a check is conditional, record the condition and whether an attacker controls it.

### Phase 4 — Write the report

Create `./auth-review/` if absent. Write to `./auth-review/report-YYYY-MM-DD.md` (append `-HHMM` if one already exists for today). Use the structure in `references/report-template.md`.

The report must include:

1. Executive summary with counts by severity.
2. Endpoint inventory (Phase 1).
3. Authorization matrix (Phase 2).
4. Findings — each with title, severity, CWE, `file:line`, evidence, exploit reasoning, remediation.
5. "Issues to file" — findings pre-formatted as ready-to-paste issue bodies.
6. Open questions the maintainer must answer.

After writing, summarize severity counts to the user and point at the file path. Do not create issues or PRs.

## Severity Scale

| Level  | Meaning |
|--------|---------|
| High   | Exploitable by unauthenticated or low-privilege attacker; leads to account takeover, data breach, privilege escalation, or tenant crossing. |
| Medium | Requires specific conditions, partial impact, or defense-in-depth failure. |
| Low    | Hardening recommendation; minor information disclosure; missing best practice. |

Always include a CWE ID (e.g., CWE-287, CWE-639, CWE-862, CWE-863). Use identifiers from `references/vulnerability-catalog.md` — do not invent IDs.

## DO NOT

- DO NOT modify source code. This skill is read-only.
- DO NOT execute the application, run network probes, or make outbound requests.
- DO NOT report a finding without a `file.ext:line` reference and evidence snippet.
- DO NOT flag a missing check before confirming no upstream middleware, guard, decorator, or proxy enforces it.
- DO NOT invent CWE IDs, CVSS scores, or framework behaviors — if unsure, mark the finding "unconfirmed" and move it to Open Questions.
- DO NOT include secrets, tokens, private keys, or real user data in the report. Redact as `[REDACTED]`.
- DO NOT commit the report to git unless the user asks.
- DO NOT create GitHub issues or PRs directly. Output issue-ready text and let the user file them.
- DO NOT stop after finding one bug. Enumerate everything, then report.
- DO NOT trust code comments or documentation over the code itself. A comment saying "admin only" is not a security control.

## References

- `references/enumeration.md` — entrypoint patterns across HTTP, GraphQL, WebSocket, RPC, serverless, and background stacks.
- `references/vulnerability-catalog.md` — full taxonomy with detection heuristics, CWE IDs, and fixes.
- `references/authz-matrix.md` — matrix schema and expected-principal inference rules.
- `references/report-template.md` — exact report structure and issue-body format.
