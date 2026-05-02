# Report Template

Write the report to `./auth-review/report-YYYY-MM-DD.md` (append `-HHMM` if one already exists today). Use the structure below verbatim — downstream tooling and reviewers expect it.

## Structure

````markdown
# Auth Review Report

- **Repository:** <repo name or path>
- **Commit:** <git HEAD short SHA, if available>
- **Date:** <YYYY-MM-DD>
- **Reviewer:** auth-review skill (static, read-only)

## Executive Summary

<2–4 sentences: what was reviewed, the highest-impact findings, and overall posture.>

**Findings by severity**

| Severity | Count |
|----------|-------|
| High     | <n>   |
| Medium   | <n>   |
| Low      | <n>   |

**Top risks** (one line each, highest severity first):

1. <title> — <file:line>
2. ...

## Scope

- **In scope:** <directories / services / packages reviewed>
- **Out of scope:** <anything skipped and why>
- **Frameworks detected:** <list>
- **Not covered by static review:** runtime configuration, infrastructure, deployed middleware that does not live in this repo, production secrets.

## Endpoint Inventory

| Method / Trigger | Path / Name | Handler | Auth required? | Roles / Scopes | Notes |
|------------------|-------------|---------|----------------|----------------|-------|
| GET              | /api/orders/:id | `routes/orders.ts:40` | yes | owner | |
| POST             | /admin/refund   | `routes/admin.ts:12` | yes | **missing** | flagged F-003 |
| GraphQL Mutation | `promoteUser`   | `graphql/user.ts:88` | yes | admin | |
| Queue            | `user.signup`   | `workers/signup.ts:10` | n/a | internal | verifies HMAC |
| ...              | ...             | ...     | ...             | ...             | ... |

## Authorization Matrix

| Endpoint | Expected | Enforced | Upstream | Gap |
|----------|----------|----------|----------|-----|
| `GET /api/orders/:id` | owner or admin | ownership check at `routes/orders.ts:42` | `requireAuth` `app.ts:15` | none |
| `PATCH /api/users/:id` | owner or admin | none | `requireAuth` `app.ts:15` | no-authz |
| ... | ... | ... | ... | ... |

## Findings

Each finding uses this block. Number them `F-001`, `F-002`, ... in order of severity then discovery.

---

### F-001 — <short title>

- **Severity:** High | Medium | Low
- **CWE:** CWE-XXX (<name>)
- **Category:** <from vulnerability-catalog.md>
- **Location:** `path/to/file.ext:line`
- **Affected endpoints:** `METHOD /path`, `METHOD /path`, ...

**Evidence**

```<lang>
// path/to/file.ext:line
<minimal code snippet demonstrating the issue — redact secrets as [REDACTED]>
```

**Exploit reasoning**

<2–5 sentences: who the attacker is, what they send, what the server does wrong, what they obtain. Be specific about preconditions.>

**Remediation**

<concrete change: library call to use, pattern to apply, test to add. Show a before/after if non-obvious.>

**References**

- `references/vulnerability-catalog.md#<section>`
- <CWE link, OWASP cheat sheet, RFC if applicable — only well-known canonical links; do not invent URLs>

---

## Issues to File

Each finding pre-formatted as a GitHub issue body. Paste as-is into `gh issue create --body-file ...` or the GitHub UI.

### Issue for F-001

**Title:** `[auth-review] <Severity>: <short title>`

**Body:**

```markdown
## Summary

<1-sentence statement of the bug and its impact.>

## Details

- **Severity:** <level>
- **CWE:** CWE-XXX
- **Location:** `path/to/file.ext:line`

## Evidence

\`\`\`<lang>
<snippet>
\`\`\`

## Suggested fix

<concrete change>

## Test to add

<one sentence describing the regression test>

---
_Found by `auth-review` static review on <date>. Finding ID: F-001._
```

(Repeat the issue block for each finding.)

## Open Questions

Things static analysis cannot resolve. The maintainer must answer each before closing the review.

- [ ] Is endpoint `X` intentionally public?
- [ ] Does a reverse proxy or API gateway enforce auth for `/admin/*` before requests reach the app?
- [ ] Is the session store configured with `secure: true` in production (env-driven)?
- [ ] Is field `role` meant to be user-editable on the profile endpoint?
- [ ] Which tenant-scoping mechanism is authoritative — the ORM default scope or the handler check?

## Methodology

- **Phases:** (1) Entrypoint enumeration, (2) Authorization matrix, (3) Catalog sweep, (4) Report.
- **Catalog:** `references/vulnerability-catalog.md` covers AuthN, JWT/tokens, sessions, IDOR/BOLA, privilege escalation and mass assignment, OAuth/OIDC/SAML, password reset, MFA, rate limiting, CSRF/CORS, SSRF adjacent to identity.
- **False-positive controls:** every flagged check was confirmed by reading the file; upstream middleware and guards were considered before calling a check missing.
- **Not performed:** dynamic probing, authenticated crawling, dependency CVE scan, infrastructure review.

## Appendix — Files Reviewed

<optional: list of files opened during the review, for auditability>
````

## Conventions

- Use fenced code blocks with language hints (`ts`, `py`, `go`, `rb`, `java`, `cs`, ...) so syntax highlighting works in GitHub.
- Keep evidence snippets short — 3 to 10 lines. Elide with `// ...` if the relevant code spans a larger function.
- Redact secrets: replace token/key strings with `[REDACTED]`.
- Use absolute repo-relative paths (`src/routes/users.ts:42`), not absolute filesystem paths.
- Keep finding titles factual: `"Admin refund endpoint lacks role check"`, not `"Critical bug!!"`.
- If severity is ambiguous, pick the lower level and explain why in the finding body.
- When no findings exist in a category, omit that finding entirely — do not add empty sections. The executive summary's counts should reflect that.
- If the review surfaces zero findings, state this plainly and list what was checked; a clean report is valuable.
