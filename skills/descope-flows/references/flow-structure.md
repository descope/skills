# Flow JSON structure

The format below is what the console's flow export writes and its import reads, and
what the Descope MCP `ImportFlow` and the Management API `/v2/mgmt/flow/import` take wrapped as `{"flow": <file>}`.
Every recipe in this skill is a complete example of it.

## Envelope

```json
{
  "flowId": "sign-up-or-in",
  "metadata": {
    "name": "Sign up or in",
    "description": "Optional, up to 1024 characters",
    "componentsVersion": "2.1.13",
    "sharedInteractions": [{ "id": "8.success", "type": "success" }]
  },
  "contents": {
    "startTask": "0",
    "tasks": { "...": "..." }
  },
  "screens": [ { "screenId": "SC34mQ8rTzKvN2bW6xHjLpE9aYcFd", "interactions": [], "contents": {} } ]
}
```

| Field | Notes |
|---|---|
| `flowId` | The flow's id in the project, used by SDKs (`<Descope flowId="...">`). Letters, digits, hyphens, under 50 characters; lowercase is safest. Importing over an existing id replaces that flow |
| `metadata` | Required, and `metadata.name` in it (import fails with E011003 otherwise). The rest is optional |
| `metadata.componentsVersion` | The screen component library version the screens were written for. Keep the recipe's value; import migrates the screens to the project's version |
| `metadata.sharedInteractions` | The flow's exits: `"<task id>.<interaction id>"` for every task outcome with no next task, e.g. `"8.success"` for the final `logged-in` task. A parent flow routes on these when it runs this flow as a subflow. The console recomputes it on save; keep it in step when you change the end of a flow |
| `contents.startTask` | Id of the first task the engine runs. Must exist in `tasks` and be a `screen`, `automated`, `condition` or `flow` task |
| `screens` | One object per screen, exactly `{screenId, interactions, contents}`. Order doesn't matter |
| `references` | Leave it out. Exports carry it; import doesn't need it |

Import silently drops any key it doesn't know, in `contents` and in every task. A misplaced field (a top-level
`flowId` on a subflow task, a typo like `argument`) disappears without an error, so copy field names from here.

### Validate and import with the MCP

`ImportFlow` (in `flows_write`) has two argument sets that don't mix:

1. **Dry run (checked):** `{flow: <the whole file>, flowId: "<same id as in the file>", traceId: "<any stable id,
   e.g. the flowId>", mode: "UPSERT", dryRun: true}`. Validates without writing, needs no write elevation, and
   returns diagnostics or a `draftToken`. Missing `flowId` or `traceId` fails with "... is required"; `mode`
   defaults to `CREATE`, which fails once the flow exists, so always pass `UPSERT`.
2. **Apply:** after the user agrees and write elevation, `{draftToken: "<from the dry run>", mode: "UPSERT"}`
   imports exactly what was checked. Or the raw call `{flow: <the whole file>}` with no other key (`flowId` stays
   inside `flow`): it imports immediately and overwrites a flow with the same id. It skips the `ValidateFlow` lint and the draft,
   but still canonicalizes ids and stops on blocking problems (screen shape, entry task, key/value rows).

The MCP import lays out the tasks itself only when no task has a non-zero `view`, and its layout is tangled. So
give every task a console-like `view` (below), never only some. If the dry run answers "AI flow synthesis is not enabled for this project",
skip it and import raw into a test flow id first.

Don't use `ValidateFlow` on this format: it rejects the screens (`screen_shape_invalid ... unsupported
keys=[contents screenId]`). If you must, pass `{dsl: <contents>, screens: [...]}` with each screen converted to
`{id: <screenId>, htmlTemplate: <contents>, interactions}`.

Neither check verifies action ids, argument names or screen components.

## Tasks

`contents.tasks` is an object keyed by task id. Each task repeats its key in `id`. Ids are digit strings, with
`.end` for the second half of a two-step action: `"0"`, `"12"`, `"3.end"`. One other id (`"welcome"`, `"step-1"`;
`"start"` aside) makes the MCP import renumber every task from 0 in path order, which breaks the user's references to
every step (console and Management API import keep ids as given). Keep existing ids when you
edit; give a new task the next unused number.

Every task has `id`, `name` (shown in the editor), `type`, `next`, and `view` (`{"x": .., "y": ..}`, its position in
the editor). Follow "Make it look console-made" below for all of them.

### `screen`: show a screen and wait for the user

```json
"20": {
  "id": "20",
  "type": "screen",
  "name": "Verify OTP",
  "screenId": "SC34mQ8sVb7GkR3nXwZ5tJhUoPq1e",
  "contextKeys": ["sentTo.maskedEmail"],
  "next": { "rules": [
    { "interactionId": "L1T9iO4p5U", "taskId": "21" },
    { "interactionId": "resend", "taskId": "19" },
    { "interactionId": "xFKyTBaTQn", "taskId": "0" }
  ] },
  "view": { "x": 1116, "y": -72 }
}
```

- `screenId` must match a `screens[].screenId`.
- Each rule's `interactionId` is the id of a button (or other interactive component) on that screen, and must be listed
  in that screen's `interactions`. One rule per button.
- Name a custom input `form.<key>` (`form.birthDate`); built-in inputs keep bare names (`email`, `code`). See
  "Input names" at the end of this file.
- `allInputKeys` lists the `props.name` of every component on the screen that has one; `inputKeys` the same for
  input components only (`custom.type: "input"`); and `calculatedInputKeys: true`. The editor computes these on save
  but import doesn't, and the engine reads `allInputKeys`, so write them.
- `contextKeys` lists the context values the screen's text uses (`{{sentTo.maskedEmail}}`). The screen receives
  only these (`sentTo` always): every `{{key}}` a screen shows must be listed, or it renders empty. The console
  fills the list on save; in hand-edited JSON keep it in step.

### `automated`: run an action

```json
"19": {
  "id": "19",
  "type": "automated",
  "name": "Sign Up or In / OTP / Email",
  "action": "sign-up-or-in-otp-email",
  "arguments": {
    "providerId": { "type": "inline", "value": "" },
    "templateId": { "type": "inline", "value": "" }
  },
  "next": { "rules": [ { "interactionId": "success", "taskId": "20" } ] },
  "view": { "x": 744, "y": 12 }
}
```

- `action` is an action id from the catalog (`GetActionCatalog`, or `catalog/actions/index.md`). Use the exact id; display names like "Sign Up or In /
  OTP / Email" are not ids.
- `arguments` maps the action's input names to `{"type": "inline", "value": ...}`. Input names come from the catalog,
  never from guesses (`references/guardrails.md`). An argument whose name is not an input of the action is silently
  ignored. Inputs the catalog marks as not visible (`email`, `phone`, `code` on the OTP actions) take no argument: the
  engine reads them from the context key of the same name, which a screen input with that `name` fills.
- Values can reference flow context with `{{...}}` inside strings, for example `"{{form.email}}"`.
- `next.rules` with `"interactionId": "success"` is where the flow goes when the action succeeds.
- **Errors.** By default (`automatic`) an action error returns the user to the last screen, whose `ErrorMessage`
  component shows it. To branch on an error instead, add `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType":
  "custom"}}` and a rule `{"interactionId": "<ErrorType>", "taskId": "..."}`; `custom` clears the error, so the
  next screen shows none. `"customWithError"` routes the same way and keeps the error when the rule leads straight
  to a screen, whose `ErrorMessage` shows it: add `"errorMessage": "No account for this email"` to replace the
  action's text (`{{...}}` context values work). Action error texts are often generic, so set `errorMessage`
  whenever the user should read it. That is the way to send an error back to the screen it came from
  with your own wording. `"ignore"` continues as if it succeeded; `"abort"` ends the flow with the error. Error
  types per action are in the catalog.
- The flow ends at an automated task with `"action": "logged-in"` (issues the session; named `End`) and
  `"next": {}`. Every successful path must reach one.
- **Two-step actions** are a pair of tasks, `N` and `N.end`, with the same `name` and the same `view` position (the
  editor draws them as one node): `oauth-start` -> `exchange-oauth-code`, `saml-start` -> `exchange-saml-code`,
  `webauthn-*-start` -> `-finish`, the magic link sends -> `verify-magic-link`. The first one's step argument
  (`exchangeStepId`, `verifyStepId`, `finishStepId`) is `"N.end"`.

Key/value list arguments (`update-user-properties` `userPropertiesDefinitions`, `custom-claims` `customClaims`, the
scriptlet's `scriptArgs`, `generate-audit-event` `customAuditData`) are a list of `{key, type, value}` rows inside the
inline wrapper:

```json
"userPropertiesDefinitions": {
  "type": "inline",
  "value": [ { "key": "displayName", "type": "context", "value": "form.fullName" } ]
}
```

A row's `type` is `context` (value is a context path, no braces) or a literal type: `string`, `number`, `boolean`,
`object`. Never `inline` on a row.

### `condition`: branch

```json
"4": {
  "id": "4",
  "type": "condition",
  "name": "Is new user?",
  "conditions": [
    {
      "interactionId": "iw9wg6crpmd",
      "name": "New user",
      "atomicConditions": [ {
        "operator": "is-true",
        "target": { "type": "context", "value": "authInfo.firstSeen" },
        "predicate": { "type": "inline", "value": "" }
      } ]
    },
    { "interactionId": "ELSE", "name": "Existing user" }
  ],
  "next": { "rules": [
    { "interactionId": "iw9wg6crpmd", "taskId": "12" },
    { "interactionId": "ELSE", "taskId": "8" }
  ] }
}
```

- Each branch has its own `interactionId` (any unique string) and one rule in `next.rules` with the same id. The last
  branch is `ELSE` with no `atomicConditions`.
- Several `atomicConditions` in one branch must all hold, unless the branch sets `logicalOr: true`.
- `target` is what is tested; `predicate` is the value compared against (empty for unary operators). The context
  keys a target can use (`authInfo.firstSeen`, `user.*`, `lastAuth.authMethod`, `geo.country`, ...) with their types
  and allowed values are in `catalog/context-keys.md`; also screen inputs (`form.<key>`, "Input names" below) and connector (`connectors.md`) or scriptlet results.
  Copy keys exactly as listed: context paths are case-sensitive, and a misspelled key resolves empty, which sends
  the condition down the other branch without an error.
- Common operators: `equal`, `not-equal`, `contains`, `doesnt-contains`, `greater-than`, `greater-than-or-equal`, `less-than`,
  `less-than-or-equal`, `empty`, `not-empty`, `is-true`, `is-false`, `in`, `not-in`, `matches`, `is-email`. More exist
  (dates, IP ranges, approved domains, list checks): `catalog/conditions.md` lists them all with what each applies
  to, as does `GetConditionOperators` with the MCP.
- Paths that index into a list need the `jq:` prefix (`references/guardrails.md`).

### `flow`: run another flow (subflow)

```json
"30": {
  "id": "30",
  "type": "flow",
  "name": "MFA",
  "arguments": { "flowId": { "type": "inline", "value": "mfa-subflow" } },
  "next": { "rules": [ { "interactionId": "5.success", "taskId": "8" } ] }
}
```

- The subflow id goes in `arguments.flowId`, never in a top-level `flowId` field (`references/guardrails.md`). The
  subflow must exist in the project before this flow runs.
- The rules route on the subflow's exits, its `metadata.sharedInteractions`: `"5.success"` means "the subflow ended
  after its task `5` succeeded". One rule per exit the parent cares about.
- Optional `arguments.flowInput` passes values in, as a key/value list (below).

### The `start` task

Console flows carry a typeless task `"start"`, the editor's Start node:

```json
"start": { "id": "start", "name": "start", "next": { "rules": [ { "taskId": "0" } ] }, "view": { "x": 108, "y": 228 } }
```

Write it, with its one rule pointing at the same task as `startTask`, and place it left of that task. The engine
never runs it (`startTask` names the first real task, never `"start"`), but the editor can crash on a flow without
it.

## Make it look console-made

A flow should look as if someone built it in the console editor, so the user can keep editing it there.

- **Ids:** `0, 1, 2, ...` in the order a person would add the tasks, entry screen first; `N.end` for the second task
  of a two-step pair; the `start` node. A new task in an existing flow gets the highest numeric id + 1.
- **Names:** an automated task takes its action's `displayName` from the catalog (`Sign Up or In / OTP / Email`;
  `update-user-properties` is usually `Update User / Properties`, its older and more common name); a two-step pair takes its group's `displayName` on both tasks (`Sign Up or In / OAuth`);
  `logged-in` is `End`. Screens get a descriptive name (`Welcome Screen`, `Verify OTP`); conditions a question
  (`Is new user?`), its branches for the outcome (`New user`, `Else`); a subflow task the called flow's name.
  `scriptlet`, `connector` and `generate-audit-event` tasks are mostly named for what they do (`Normalize login
  id`, `Fetch plan from API`).
- **Arguments:** the inputs you set, plus the action's payload inputs even when empty (`providerId` and `templateId`
  on send actions); leave optional inputs you don't use out, as production flows do. A two-step pair carries the same
  arguments on both tasks. Leave out invisible inputs and, unless you customize errors, `errorHandlingV2`.
- **Conditions:** branch `interactionId` is 10 or 11 random characters of `[0-9a-z]` (`iw9wg6crpmd`); branch names
  descriptive (`New user`); `ELSE` last.
- **Layout:** left to right. `start` near `{x: 0, y: 0}`, each next column +492 on x, branches +/-108 to 216 on y,
  `N.end` at the same `view` as `N`, every value a multiple of 12. Position every task: with any non-zero `view` set, the MCP
  doesn't lay out the flow at all, so a pile of tasks at one spot stays a pile; unpositioned tasks may be placed
  next to their neighbors.
- **Screens:** console-style ids, see `references/screens.md`.

## Context keys the recipes use

All of them, for conditions: `catalog/context-keys.md`.

| Key | Set by |
|---|---|
| `form.<key>` | A custom screen input named `form.<key>` (`props.name: "form.birthDate"`); read it only as `form.<key>`. Built-in inputs keep bare names and read bare or as `form.<name>`; see "Input names" below |
| `authInfo.firstSeen` | Any sign-up-or-in or OAuth action: `true` when the user was just created |
| `sentTo.maskedEmail`, `sentTo.maskedPhone` | OTP and magic link send actions |
| `user.*` | Any action that loads or creates the user (`user.email`, `user.name`, `user.customAttributes.<key>`) |

### Input names

An input's `props.name` decides where its value lands:

- **Built-in inputs keep their bare names**: `email`, `phone`, `externalId`, `fullName`, `displayName`,
  `firstName`, `middleName`, `lastName`, `givenName`, `familyName`, `recoveryEmail`, `recoveryPhone`,
  `emailDomain`, `tenantName`, `impersonateId` (the engine's list). Actions read them by these names, and
  conditions or rows can read them bare or as `form.<name>` (`form.email`); `form.email` is still set after later
  screens. Inputs an action reads by name (`code`, `password`, `newPassword`, `userSelectedTenant`) also keep the
  name the recipe or catalog gives them.
- **Every other input is named `form.<key>`** (`form.birthDate`, `form.rememberMe`, `form.company`) and read as
  `form.<key>` in conditions, scriptlet `scriptArgs` and `userPropertiesDefinitions` rows.
- A custom input with a bare name (`dateOfBirth`, a checkbox `rememberMe`) is empty both bare and as `form.<name>`:
  every condition and row that reads it gets nothing, without an error.

Checked end to end (two runs): `dateOfBirth` and `rememberMe` read empty both ways,
`form.birthDate` readable only as `form.birthDate`, `email`, `fullName` and `phone` readable both ways.

## Screens

A screen is exactly `{screenId, interactions, contents}`; `contents` is the editor's component tree. How to write
one, which components exist and what submits a screen: `references/screens.md`.
