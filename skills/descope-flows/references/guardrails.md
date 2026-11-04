# Guardrails

Each mistake below passes `ValidateFlow` and import today and then fails when the flow runs, or misleads the user.
Check every flow against this list before importing.

## Argument names must be the action's input names

An argument whose name is not one of the action's inputs is imported without an error and ignored at runtime, and a
missing required input only fails at runtime. Take every name from `GetActionCatalog` (full projection) or from a recipe.

The scriptlet action is the common case. Its inputs are `scriptCode`, `scriptArgs` and `outputPath`, not `code`,
`args` or `resultPath`:

```json
"10": {
  "id": "10",
  "type": "automated",
  "name": "Enforce SSO",
  "action": "scriptlet",
  "arguments": {
    "scriptArgs": { "type": "inline", "value": [
      { "key": "tenants", "type": "context", "value": "unauthUserTenants" },
      { "key": "loginIds", "type": "context", "value": "unauthUser.loginIds" }
    ] },
    "scriptCode": { "type": "inline", "value": "return { force: tenants.length === 1 }" },
    "outputPath": { "type": "inline", "value": "enforceSSO" }
  },
  "next": { "rules": [ { "interactionId": "success", "taskId": "11" } ] }
}
```

Each `scriptArgs` key becomes a variable in the script. The returned object lands in the context under
`scripts.<outputPath>`: later tasks and conditions read `scripts.enforceSSO.force` above, never `enforceSSO.force`.

A scriptlet changes nothing else by itself. To feed a result to a later action that reads a form value (a
normalized login id, a corrected email), add `overrideForm` with rows that write it back:

```json
"overrideForm": { "type": "inline", "value": [
  { "key": "form.externalId", "type": "context", "value": "scripts.normalizedId.externalId" }
] }
```

Keys are `form.<name>` (`form.email`, `form.externalId`, `form.phone` also set the login id the next action uses)
or `form.customAttributes.<key>`. `overrideForm` is a list of rows: anything else (`true`, an object) passes validation and then fails the flow with
a server error (E105002) when the scriptlet runs.

## Every outcome needs a next rule, and every loop an exit

At runtime, an interaction with no rule fails the flow with "Could not get next task" (E102103), the most common
flow error in production. Check each task:

- Screens: a rule for every interaction, including `resend`, "back" and "use another method" buttons, and for a
  link-sent screen both `polling` and `polling-error`.
- Conditions: an `ELSE` branch, always.
- Connectors and other actions that call out: decide what happens on failure. Either keep the default (back to the
  last screen with an error) or add custom error handling with its rule.

A loop (resend, retry, "back") must let the user leave it: a flow that cycles hits the engine's task limit and stops.

## Collected values are saved only if a task reads them

An input on a screen puts its value in the context under its `props.name` and nothing more. Name a custom input
`form.<key>` (`form.birthDate`) and read it as `form.<key>`; only built-in inputs (`email`, `phone`, `code`,
`fullName`, ...) keep bare names. A custom input with a bare name is empty wherever it is read
(`flow-structure.md`, "Input names"). It reaches the user only when a task reads it:

- An action input of the same name. Sign-up actions (`password-sign-up`, `sign-up-otp-email`,
  `sign-up-magic-link-email`, ...) have invisible `fullName`, `firstName`, `middleName` and `lastName` inputs (some
  also `phone`, `recoveryEmail`), so a screen input with one of those names is stored on the new user with no extra
  task. Check the action's inputs in the catalog: most `sign-up-or-in-*` actions, such as
  `sign-up-or-in-otp-email`, don't have them.
- Otherwise an `update-user-properties` task after the user exists, with a row per value:
  `{"key": "displayName", "type": "context", "value": "form.fullName"}`, `customAttributes.<key>` for custom
  attributes.

## Actions before the first screen route their errors

Automatic error handling sends the user back to the last screen. An action reached before any screen (the
IdP-initiated SSO path, a flow started with data) has none: give each of its errors custom handling and a rule to a
screen with a message and a way to start over.

## Handle the failures the user asked about

By default an action error sends the user back to the last screen and shows the error there, in that screen's
`ErrorMessage` component. That is not enough when the user asked for a behavior ("tell unknown users to sign up",
"lock after 3 tries"): route the specific error. Find the action's error types in the catalog (for example
`UserDoesNotExists` on the magic link sign-in actions), add `"errorHandlingV2": {"<ErrorType>":
{"errorHandlingType": "custom"}}` and a next rule `{"interactionId": "<ErrorType>", "taskId": "<screen with the
message>"}`. Give that screen a way back. To show the message on the screen the user came from instead, use
`"errorHandlingType": "customWithError"` with `"errorMessage": "<your text>"` and the rule back to that screen: with
`custom` the error is cleared and that screen shows nothing.

Route only errors the action declares: a rule for any other name never fires. `UserDoesNotExists` is declared by
`oauth-signin-v2`, the passkey sign-ins (`webauthn-sign-in-v2`, `webauthn-sign-in-start-v2`) and the magic link
sign-ins, not by `exchange-oauth-code` or the OTP actions.
For an "unknown email" path with OTP, test the user before sending (a condition on an `unauthUser.*` key from
`catalog/context-keys.md`) and list that check under "Assumed, not verified" in the report.

An explicit "no account found" message tells anyone which emails are registered (user enumeration). By default,
every unknown-account path (email, social, passkey, SSO) shows the same neutral message as a wrong credential ("If
an account exists, we sent a link", "Wrong email or password"). Write an explicit one only when the user asks for
it, and say so in the report.

Screens that show where a code or link went use the masked value (`{{sentTo.maskedEmail}}`,
`{{sentTo.maskedPhone}}`), as the recipes do. Don't replace it with the full email or phone.

## Failures on the auth path fail closed unless the user says otherwise

When a check on the way to a session fails to run (a connector or outside API down, a scriptlet error), routing the
error onward to `End` or the next step issues a session without the check: fail-open. Never choose that yourself,
and don't inherit it from a recipe unasked. Ask the user (SKILL.md, "Before building"), recommend failing closed (a
screen with a message and a way to retry), and if they choose fail-open, name in the report what it skips.

## Actions listed but not runnable

`sign-in-totp` is in the catalog but has no implementation: a flow that reaches it fails with a server error. To
check an authenticator code (sign-in, step-up, or right after `update-user-totp` enrollment) use `verify-totp-code`.

## Group actions are not task actions

Some catalog entries are shorthand for a pair of steps (they list `members`: `oauth`, `saml`, the magic link and
passkey groups). Never use a group id as a task's `action`. Write its members as two tasks, `N` and `N.end`, and set
the first one's step argument (`exchangeStepId`, `verifyStepId` or `finishStepId`) to `"N.end"`. The recipe's tasks
`3` (`oauth-start`) and `3.end` (`exchange-oauth-code`) are an example.

## Key/value list rows: `{key, type, value}`, never `inline`

`userPropertiesDefinitions`, `customClaims`, `scriptArgs`, `customAuditData` and `flowInput` take a list of rows
inside the inline wrapper. Not an object, not a string:

```json
"customClaims": { "type": "inline", "value": [
  { "key": "plan", "type": "string", "value": "pro" },
  { "key": "userId", "type": "context", "value": "user.userId" }
] }
```

Row `type` is `context`, `string`, `number`, `boolean` or `object`. A row typed `inline` runs but the editor can't
display it.

For `update-user-properties`, always pass `userPropertiesDefinitions`: without it the action falls back to a
deprecated path that only copies a `fullName` input to the display name. Row keys are user fields (`displayName`,
`givenName`, `middleName`, `familyName`, `picture`, `email`, `phone`, `loginId`, `verifiedEmail`, `verifiedPhone`,
`recoveryEmail`, `recoveryPhone`, `verifiedRecoveryEmail`, `verifiedRecoveryPhone`) or `customAttributes.<key>`. Any other key is ignored with only a log line. Use
`displayName`, not the legacy `name`.

## Custom claims can't replace system claims

A `custom-claims` row whose key is a system claim (`sub`, `iss`, `exp`, `amr`, `act`, `tenants`, `roles`,
`permissions` and the rest) is dropped without an error: the session JWT keeps the real value. Checked end to
end: rows for `sub`, `iss`, `amr` and `tenants` changed nothing and no step failed. To put another value in `sub`,
the project's session JWT template needs its override setting on (it covers `sub`, `act` and `amr`; not checked
with it on); say so to the user. Otherwise put the value in a claim with its own name
(`externalUserId`).

## List paths need the `jq:` prefix

Context paths split on `.` only. `connectors.myApi.body.items[0].id` looks up a key literally named `items[0]`,
resolves empty, and the condition silently takes the other branch. Write `jq:.connectors.myApi.body.items[0].id`
instead. See https://docs.descope.com/connectors/connector-json-usage.

## Screen ids must not start with `new-`

A screen whose `screenId` is `new-<something>` (`new-password`, `new-email`) is dropped on import without an error,
and its task then points at a missing screen. The one exception is `new-<its own task id>`, the editor's placeholder,
which import replaces with a fresh id. Avoid the prefix: use `set-new-password`, `password` and the like.

## Subflow id goes in `arguments.flowId`

```json
"type": "flow",
"arguments": { "flowId": { "type": "inline", "value": "my-subflow" } }
```

A top-level `"flowId": "my-subflow"` on the task is accepted and then dropped, and the subflow step fails at runtime.
Route the subflow task's rules on the subflow's `sharedInteractions` (`references/flow-structure.md`).

## What the Descope MCP's own texts get wrong

Until the MCP's descriptions are fixed, follow this skill where they disagree:

- The onboarding text says to import with `{flowId, dsl, screens, mode: "CREATE"}` and to use the raw
  `ImportFlow({flow})` only on explicit request. That call fails (no `traceId`), and `CREATE` fails on every re-import.
  Write the flow file this skill describes and use the dry run and apply in `flow-structure.md`.
- `ValidateFlow` says it accepts these screens; it rejects them. Use the `ImportFlow` dry run.
- `GetActionCatalog` with no arguments returns only the first 25 actions, without input names. Pass `query`, and
  `full: true` for the actions you use.
- A clean validation or dry run doesn't mean the arguments are right: check every name against the catalog.
- Server instructions may mention `skills/list` or `get_project_status`; neither is needed to build a flow.
- Don't build from `ComposeIntentDraft` or `SearchFlowAssets` output: their drafts use arguments the actions don't
  take (`loginIdInput`, `passwordInput`), magic links without a verify step, and the group id `oauth` as a task
  action. They import and then fail at runtime. Start from a recipe in this skill instead.

## Never overwrite a live flow by accident

`ImportFlow` with `{flow}` or `{flow, flowId}` and none of `dryRun`, `mode`, `traceId`, `draftToken` replaces the
flow with that id immediately, with almost no checks. Always dry-run first (`{flow, flowId, traceId, mode: "UPSERT",
dryRun: true}`), show the user what changes, and apply with `{draftToken, mode: "UPSERT"}`. Send the raw form only
when the user explicitly wants an immediate overwrite, and import new flows under a new id or into a test project.

## Auth methods don't need enabling for flows

Switching a method under Authentication Methods to block API/SDK use gates direct SDK and API calls, not flows: a
flow that uses email OTP or Google works while they are switched off that way. Don't tell the user to enable them.
The exception: a social provider set to "Disable All" is off for flows too; if the flow uses one, ask the user to
check it isn't. Never import a project snapshot (`ImportSnapshot`) to change project settings for a flow: it can
overwrite the project's configuration.

What a flow does need from the project:

- **Social login:** Google works with Descope's own OAuth app for testing. For production, and for any other
  provider unless the user has confirmed it works in their project, the user must configure it under Authentication
  Methods -> Social Login. Name the providers the flow uses (`data-descope-provider` on each social button) and tell the user
  to check each one is configured; import gives no warning for a missing one.
- **Connectors:** a connector task needs the connector created in the project first.
- **Subflows:** every `arguments.flowId` must exist in the project.
- **Custom attributes:** user and tenant custom attributes a flow writes must exist in the project.
