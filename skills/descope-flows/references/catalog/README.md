# Flow catalog

Reference data for writing flow JSON: every flow action with its inputs, outcomes and errors, and every condition
operator. Generated from the Descope backend code, so ids, input names and types are exact. The flow JSON format
itself is in the skill's flow-structure reference.

## Prefer the live catalog when the Descope MCP is connected

The live catalog is the customer's own Descope deployment, which may be newer than this snapshot. Call it through
the MCP's read tool:

- `flows_read({operation: "GetActionCatalog", args: {query: "otp", full: true}})`. `query` (or `category`) filters
  over id, name, description and tags; `tags`, `managementCompatibility` (`compatible`, `managementOnly`) and `limit`
  also filter. Results are paged (25 by default; the response reports `total`), so filter with `query` rather than
  listing everything. Pass `includeHidden: true` when not filtering: without a filter the live catalog leaves out
  hidden actions, and most actions a flow runs (`sign-up-or-in-otp-email`, `verify-code-otp-email`,
  `oauth-start`...) are hidden. `full: true` returns the full input schemas.
- `flows_read({operation: "GetConditionOperators", args: {}})`, optionally `applicableOn: ["string"]`.

Use the files here when the MCP isn't connected, or to read about an action before calling it.

## Files

| File | What | When to read |
|---|---|---|
| [actions/index.md](actions/index.md) | One line per action, by group, with flags | To find the right action id |
| `actions/<group>.md` | Each action in the group: description, inputs, outcomes, errors | Before writing a task with that action |
| [conditions.md](conditions.md) | Condition operators, the types they apply to | Before writing a condition task |
| [context-keys.md](context-keys.md) | Context keys a condition can test (`authInfo.firstSeen`, `user.email`, `form.<name>`...), types, values | Before writing a condition task |
| `actions.json` | The full data: `{conditions, actions}`, `actions` and `conditions` keyed by id, one entry per line; plus deprecated actions (`deprecated`, `replacedBy`; not in the markdown, never use them). Hand-written runtime facts are `notes` and `errorNotes` on an action and `note` on an input (the "Note:" lines in the markdown) | For tools (the validator), not for reading |
| `screens/components.md` | Screen components and their JSON | Before writing a screen |

Groups: [OTP by email](actions/otp-email.md), [OTP by phone](actions/otp-phone.md), [OTP other](actions/otp.md),
[magic link by email](actions/magic-link-email.md), [by phone](actions/magic-link-phone.md),
[magic link other](actions/magic-link.md), [enchanted link](actions/enchanted-link.md),
[embedded link](actions/embedded-link.md), [OAuth and social](actions/oauth.md), [passkeys](actions/passkeys.md),
[password](actions/password.md), [TOTP, nOTP, recovery](actions/mfa.md), [SSO](actions/sso.md),
[JWT and session](actions/session.md), [tenants and roles](actions/tenants-roles.md), [users](actions/users.md),
[connectors, scriptlets, utilities](actions/connectors-logic.md), [consent and apps](actions/apps-consent.md),
[other](actions/other.md).

## How to read an action

- **Inputs, Source `context`**: filled at runtime from the context key with the same name. A screen input named
  `email` feeds `sign-up-or-in-otp-email`'s `email` with no argument. Pass an argument only to override it.
- **Inputs, Source `argument`**: what the console shows in the action's dialog. Set them in the task's `arguments`:
  `"templateId": {"type": "inline", "value": "..."}`, or `{"type": "context", "value": "<context key>"}` to read a
  context key. An argument name that isn't an input of the action is ignored at runtime, with no error.
- **Type `list of {key, type, value} rows`** (`rows` in `actions.json`; the backend's own type says `object`):
  `scriptArgs`, `customClaims`, connector `args` and the like take `{"type": "inline", "value": [{"key": "...",
  "type": "context", "value": "<context key>"}, ...]}`. A bold note in an input's row corrects a misleading label.
- **Also reads from context when present**: optional inputs the console never shows. Leave them out.
- **next interactionIds**: every action exits through `success`. An error is handled automatically (shown to the
  user) unless you route it: add `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` to the task
  and a next rule `{"interactionId": "<ErrorType>", "taskId": "..."}`.
- **Error ids** (first line of each action): the only `<ErrorType>` values that action can take. A `connector` task
  can also fail with its connector command's own error ids (`templateCommandErrors` in `actions.json`), listed by
  template for Generic HTTP (`request_error`) and reCAPTCHA Enterprise (`templateErrors`).
- **Not runnable** (`[X]` in the index): the backend has no executor for it; a task with it fails at runtime.
  Today only `sign-in-totp` (use `verify-totp-code` to check a TOTP code).
- **Hidden** (`[H]` in the index): not in the console's action picker on its own, usually because the console shows
  it under a group. Still valid in a flow; most real flows use hidden actions.
- **Group** (`[G]`): console shorthand for a start action plus its completion action. It is never a task's
  `action`. Write its members as two tasks, `N` and `N.end`, both carrying the group's arguments, and point the
  start task's link argument at `"N.end"`: `verifyStepId` for magic, enchanted and embedded links,
  `exchangeStepId` for OAuth, SAML, SSO and external auth, `finishStepId` for passkeys. The start task's `success`
  rule goes to `N.end`; magic and enchanted links add a second `success` rule to the screen shown while the user
  opens the link. Example from the default sign-up-or-in flow: task `19` is `oauth-start` with
  `exchangeStepId: "19.end"` and next `success -> 19.end`, task `19.end` is `exchange-oauth-code`. The one group
  without a link argument is `start-step-up`: still two tasks, `N` = `loadUser` and `N.end` = `step-up`, both named
  `Step Up` with the same view, no arguments, `success -> N.end` (53 of 53 template step-up flows).

## Where it comes from

Everything here except this README is generated from Descope's own definitions: the actions and condition
operators are the same data as the MCP `GetActionCatalog` and `GetConditionOperators` (deprecated actions left
out), the context keys are the ones the console's condition editor offers, and `screens/` is the console's
component palette. Do not edit the generated files by hand.
