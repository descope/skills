# Authorization Matrix

For each endpoint from Phase 1, decide what *should* happen and compare to what the code *actually* enforces. The gap is where the bugs live.

## Table schema

| Column | Meaning |
|--------|---------|
| `endpoint` | `METHOD /path` or equivalent (GraphQL field, queue topic, RPC method). |
| `expected principal` | Who should be allowed: `public`, `authenticated`, `owner`, `same-tenant`, `role:admin`, `scope:x`, or a combination. Derived from conventions (see below). |
| `enforced check` | The exact check in code, with `file:line`. `none` if nothing. |
| `upstream` | Middleware/guard/filter/proxy rule that applies before the handler, with `file:line`. |
| `gap` | One of: `none`, `no-auth`, `no-authz`, `weak-authz`, `client-trusted-input`, `inconsistent`, `unknown`. |

## Inferring the expected principal

Most codebases do not document who should access what. Use these heuristics — all are rebuttable by reading the code.

### By path

| Pattern | Default expected principal |
|---------|----------------------------|
| `/admin/*`, `/internal/*`, `/ops/*`, `/_*` | `role:admin` (or higher) |
| `/api/public/*`, `/health`, `/metrics` (if unauth'd by design) | `public` |
| `/api/me/*`, `/account/*`, `/profile/*` | `authenticated`, scoped to self |
| `/users/:id/*`, `/orders/:id/*`, `/tenants/:tid/*` | `owner` or `same-tenant` |
| `/webhooks/*` | `signed-request` (HMAC verified) |
| `/auth/*`, `/login`, `/signup`, `/reset` | `public` but rate-limited |

### By verb × resource

| Shape | Expected |
|-------|----------|
| `GET /resource/:id` | owner or tenant-scoped read |
| `PUT/PATCH /resource/:id` | owner or admin |
| `DELETE /resource/:id` | owner or admin (often admin-only in real systems) |
| `POST /resource` (create) | authenticated; creator becomes owner |
| `GET /resource` (list) | authenticated; results scoped to owner/tenant |
| Any handler named `impersonate`, `promote`, `grant`, `refund`, `disable`, `delete_user` | `role:admin` minimum, usually with step-up MFA |

### By data returned

If the handler returns PII, financial data, or credentials — the expected principal is at minimum `owner`. If it returns aggregated data across users, it is `role:admin` or `internal`.

### Corroborating sources (check, don't trust blindly)

- OpenAPI / Swagger `security` blocks.
- GraphQL schema directives (`@auth`, `@hasRole`).
- Tests — `it('rejects non-admin users')` reveals intent even when the code drifts.
- Comments and docstrings — informative but not authoritative.
- Product docs or admin UI screenshots in the repo.

When expected and enforced disagree, and the tests assert the *enforced* behavior, the test may itself be wrong — note this in Open Questions.

## Classifying the gap

| Gap | Definition |
|-----|------------|
| `none` | Enforced check matches expected principal, including ownership/tenant scoping. |
| `no-auth` | Endpoint requires authentication but does not check it. |
| `no-authz` | Endpoint is authenticated but does not check role/ownership/tenant when it should. |
| `weak-authz` | A check exists but can be bypassed: uses request-supplied `userId`/`role`, checks only presence of a token, or compares against easily-forged values. |
| `client-trusted-input` | Authorization decision reads from `req.body`/`req.query`/`req.headers` beyond standard auth headers. |
| `inconsistent` | Some code paths enforce, others skip (e.g., middleware applied to one router group but not another covering the same resource). |
| `unknown` | Cannot determine statically — escalate to Open Questions. |

## Verifying the enforced check

A `file:line` reference is required. For each enforced check, confirm:

1. **It runs on every path into the handler.** Middleware registration order matters. A `router.use(auth)` after a `router.get(...)` does not protect that route. Guards applied at the controller level do not protect sibling controllers.
2. **It checks the right thing.** `authenticate()` proves identity but does not prove authorization. `@login_required` is not `@admin_required`.
3. **It scopes the query.** Ownership checks after the fetch (`if (record.owner !== user.id) throw`) are correct but fragile; scoped queries (`findOne({ id, ownerId })`) are sturdier.
4. **It is not bypassable via a sibling route.** If `GET /users/:id` is protected but `GET /users/:id/profile` is not, the profile route leaks.
5. **It survives the framework's quirks.** NestJS `@UseGuards` on a class does not cover handlers decorated with `@Public`. Spring `@PreAuthorize` requires `@EnableGlobalMethodSecurity`. Express middleware order matters.

## Example matrix row

| endpoint | expected | enforced check | upstream | gap |
|----------|----------|---------------|----------|-----|
| `GET /api/orders/:id` | owner or admin | `if (order.userId !== req.user.id) 403` at `routes/orders.ts:42` | `requireAuth` at `app.ts:15` applies | none |
| `PATCH /api/users/:id` | owner or admin | `User.update(req.params.id, req.body)` at `routes/users.ts:88` — no ownership check | `requireAuth` at `app.ts:15` | `no-authz` (IDOR, body also mass-assigned) |
| `POST /admin/refund` | role:admin | `requireAuth` only; no role check | `requireAuth` at `app.ts:15` | `no-authz` (BFLA) |
| `GET /webhooks/stripe` | signed-request | no signature check at `routes/webhook.ts:10` | none | `no-auth` |

A clean matrix is the backbone of the report. Every `gap != none` row becomes a candidate finding; cross-reference with the vulnerability catalog to assign CWE and severity.
