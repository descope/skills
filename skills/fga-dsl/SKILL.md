---
name: fga-dsl
description: Author, edit, or apply a Descope FGA schema using the ReBAC/ABAC DSL. Use this skill whenever the user asks to create a new FGA schema, modify an existing one, add types/relations/permissions/conditions, review an authorization model, or apply schema changes to a Descope project. Trigger even if the user says things like "set up authorization", "define roles and permissions", "add team-based access", "make this endpoint check FGA", or "update my authz model" — these almost always mean an FGA schema change.
---

# FGA DSL Authoring

Help the user design and apply Descope FGA schemas. The workflow is: understand the requirement → draft the DSL → validate via dry run → show the user + any data loss warnings → get confirmation → apply.

## MCP Setup — check first, stop if missing

**Before doing anything else**, check whether the Descope Management MCP is connected by looking for tools whose names contain `FGASchema` or `DryRunSchema` (e.g. `mcp__descope__DryRunSchema`). The exact prefix depends on how the user installed the MCP, but the operation IDs are `DryRunSchema`, `CreateFGASchema`, and `GetFGASchema`.

**If the tools are not found:** output only the message below, then end your turn. Do not generate a schema, do not say "here's what I'll apply once connected", do not do any design work, do not continue:

> The Descope Management MCP is required. If not yet installed, install and authorize it, then restart Claude Code and re-run `/fga-dsl`.
> If already installed, it may need authorization. Authorize the Descope MCP, then restart Claude Code and re-run `/fga-dsl`.

**If the tools are found:** call `GetFGASchema` immediately as a connectivity probe before doing any other work. If this call returns an authorization error, output only the message below and end your turn:

> The Descope MCP is installed but not authorized. Authorize it and re-run `/fga-dsl`.

All FGA operations go through MCP tool calls — never make raw HTTP requests yourself.

Once connected, use the `GetFGASchema` tool to read the current schema before editing — always do this when the user asks to modify an existing schema.

## Grammar

Every schema begins with exactly:
```
model AuthZ 1.0
```
No other name or version is accepted by the API.

Full structure:
```
model AuthZ 1.0

[constraint <Name>[:<Kind>][(args...)]]*
[condition <Name>(<param type, ...>) { <CEL bool expr> }]*

type <TypeName>
  [relation <name>: <TypeRef> [| <TypeRef>]* [with <condExpr>]]*
  [permission <name>: <expr>]*
```

Keywords: `model` `type` `relation` `permission` `condition` `constraint` `with`

Operators:
- Permission expr: `|` union, `&` intersect, `-` subtract. Mix operators with parens: `a | (b - c)`
- Set arrow: `relation.permission` — walks a stored relation to reach the subject's own permissions (e.g. `parent.can_view`)
- Userset: `Type#relation` — see dedicated section below
- `with` clause (relations only): `&` AND, `|` OR, `!` NOT, parens: `with A & (B | !C)`. Conditions are evaluated at **check time** — relations are stored unconditionally; `with` only affects whether the relation counts during permission evaluation.

**No comments** — the DSL parser has no comment token.

Naming: **PascalCase** for Types, Conditions, Constraints. **snake_case** for relations and permissions.

## Userset Pattern (`Type#relation`)

When a relation should be held by members of a group (e.g. "any member of this Team"), put `Type#relation` directly in the relation definition. This stores individual member subjects — the right granularity for permission checks.

The tempting wrong way is to store the group itself and walk to its members via a permission. This looks like it works but stores the wrong thing (a group object instead of its members), and the permission traversal does not expand correctly at check time.

**Wrong:**
```
type Repository
  relation contributor_team: Team
  permission contributor: contributor_team.member
```

**Right:**
```
type Repository
  relation contributor: Team#member
```

You can mix direct subjects with userset subjects: `relation editor: User | Team#member`

## ABAC Anti-Patterns to Avoid

### Never use a "blocked" relation + subtraction to express a condition

`with` conditions are evaluated at **check time** — when a permission check is made against the context passed in the request. Relations are always stored unconditionally; the condition only affects whether the relation counts during permission evaluation.

The `blocked` relation + subtraction pattern is wrong because it requires manually maintaining a separate set of `blocked` edges in the DB for every excluded user. It's the wrong tool: use `with !Condition` on the relation that grants access instead — it is evaluated automatically at check time with no extra stored relations.

```
// NEVER do this — requires maintaining a separate "blocked" edge per user in the DB
relation creator: User
relation blocked: User with NorthKorea
permission can_delete: creator - blocked

// Right — condition evaluated automatically at check time; no extra edges
relation creator: User with !NorthKorea
permission can_delete: creator
```

**Note:** `with` is currently only supported on **relation definitions**, not on permission expressions. If the user needs a condition on a permission expression directly (e.g. `permission can_delete: creator with !NorthKorea`), that is not yet supported — tell them and ask how they'd like to handle it.

### Don't write custom CEL when a built-in constraint covers it

A custom `condition` that checks a numeric range is just reinventing `NumRange` (or `NumAtLeast`/`NumAtMost`). Built-in constraints are validated at schema-save time and have no CEL cost. Use them.

**Wrong:**
```
condition DuringBusinessHours(hour_utc int) { hour_utc >= 10 && hour_utc < 22 }
```

**Right:**
```
constraint BusinessHours:NumRange(10, 21)
```

(Use a named alias when you want a descriptive name for the constraint.)

## Relations vs Permissions

A **relation** is a stored edge written to the database. A **permission** is a derived rule — no DB write, no stored state, just logic over existing relations. Because every relation requires an explicit API call to create, prefer satisfying a requirement with a permission whenever possible. Only introduce a new relation when a direct stored link is truly needed.

## Built-in Constraints

Use built-in constraints before reaching for custom CEL — they're validated at schema-save time and cheaper to evaluate.

| Constraint | Runtime params (zero-arg form) | Hardcoded form |
|---|---|---|
| `IpRange` | `ip ipaddress, ip_range string` | `IpRange("10.0.0.0/8")` |
| `IpList` | `ip ipaddress, allowed_ips list` | `IpList("1.2.3.4","5.6.7.8")` |
| `DateExpiryEpochSeconds` | `now_epoch_seconds int, expiry_epoch_seconds int` | `DateExpiryEpochSeconds(1735689600)` |
| `StringMatchRegex` | `str string` | `StringMatchRegex("^admin_.*")` (regex required) |
| `NumAtLeast` | `num double, min int` | `NumAtLeast(18)` |
| `NumAtMost` | `num double, max int` | `NumAtMost(100)` |
| `NumRange` | `num double, min int, max int` | `NumRange(0,100)` (min ≤ max) |
| `BoolCheck` | `bool bool, expected bool` | `BoolCheck(true)` |
| `GeoCountry` | `country_code string, allowed_countries list` | `GeoCountry("US","GB")` (ISO 3166-1 alpha-2) |
| `IntList` | `int int, allowed_ints list` | `IntList(1,2,3)` |
| `LabelList` | `label string, allowed_labels list` | `LabelList("foo","bar")` |

**Unique param names:** Each constraint exposes its runtime params by name in check requests. If two constraints of the same kind appear in a schema, their param names collide — use named aliases to give them distinct names:
```
constraint FiveEyes:GeoCountry("US","GB","CA","AU","NZ")
constraint Sanction:GeoCountry("KP","IR","SY","RU")
```
The alias form (`Name:Kind`) also applies when two zero-arg constraints of the same kind would produce identical param names.

**Custom CEL** — only when no built-in covers the logic, or when alias-based param separation isn't enough:
```
condition InNetwork(user_ip ipaddress, allowed_range string) { user_ip.in_cidr(allowed_range) }
```
CEL param types: `int`, `string`, `bool`, `double`, `list`, `ipaddress`. Body must return `bool`. Avoid nested `exists` — the evaluator enforces a cost limit.

## Edit-Safety Protocol

When editing an existing schema, first read the current schema with `GetFGASchema` so you have the real state.

- If the user asks to add something already present, tell them exactly what exists and stop — don't silently overwrite.
- Removing a **relation type** is permanent data loss: all stored relations of that type are deleted from the database. Always confirm this with the user and make sure they understand the impact before proceeding.
- Removing a **permission** deletes no data, but any downstream permissions or checks that depended on it will silently stop working. Confirm with user.
- Adding relations or permissions is generally safe. One exception: adding a new subject to a **subtraction** (`-`) clause narrows who gets blocked, which could unintentionally grant access to users who were previously excluded. Flag this.

## Validation and Apply Workflow

Follow this sequence every time you generate or edit a DSL:

### Step 1 — Dry run

Use the `DryRunSchema` MCP tool with the proposed DSL. This validates the schema and reports what data would be deleted if applied.

- On error: the schema is invalid. Read the error message, fix the DSL, retry. Cap at 5 iterations — if still failing, stop and show the user the last error.
- On success: continue to Step 2.

The response contains:
```json
{
  "deletesPreview": {
    "hasDeletes": true,
    "relations": ["folder#viewer", "doc#editor"],
    "types": ["LegacyRole"]
  }
}
```

### Step 2 — Show the user

Present:
1. The full proposed DSL (formatted in a code block)
2. If `hasDeletes` is true — a clear warning listing every relation type and namespace type that will be **permanently deleted** from the database

Example warning:
> **Warning: applying this schema will permanently delete all stored relations of these types:**
> - `folder#viewer`
> - `doc#editor`
>
> This cannot be undone. Confirm to proceed.

If `hasDeletes` is false, just show the schema and ask for confirmation.

### Step 3 — Get confirmation

Wait for explicit user approval before applying. Do not apply automatically.

### Step 4 — Apply

Use the `CreateFGASchema` MCP tool with the same DSL. Confirm success to the user.

## Examples

### Basic ReBAC with hierarchy

```
model AuthZ 1.0

type User

type Folder

type Doc
  relation owner: User
  relation parent: Folder
  permission can_view: owner | parent.owner
  permission can_edit: owner
```

### Group membership via userset

```
model AuthZ 1.0

type User

type Team
  relation member: User

type Repository
  relation owner: User
  relation contributor: User | Team#member
  permission can_push: owner | contributor
  permission can_read: can_push
```

### ABAC: time-gated access

```
model AuthZ 1.0

condition DuringShift(now int, begin int, end int) { now >= begin && now <= end }

type User

type PatientRecord
  relation viewer: User with DuringShift
  relation owner: User
  permission can_view: viewer | owner
```

### Reused constraint kind with aliases

```
model AuthZ 1.0

constraint FiveEyes:GeoCountry("US","GB","CA","AU","NZ")
constraint Sanction:GeoCountry("KP","IR","SY","RU")

type User

type Resource
  relation allowed: User with FiveEyes
  relation blocked: User with Sanction
  permission can_access: allowed - blocked
```
