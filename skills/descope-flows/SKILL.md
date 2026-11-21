---
name: descope-flows
description: Build new Descope flows with the Descope MCP, starting from a Descope flow template, and import them after a dry run and the user's yes. Use when the user asks for a new Descope sign-up, sign-in, MFA, step-up, SSO, social login, OTP, magic link, passkey, login or progressive-profiling flow. Builds new flows only, not for editing an existing flow.
---

# Descope Flows

Build a new Descope flow with the Descope MCP: start from a template, change only what the user asked for, check it
with the server, show what changed, and import only after the user says yes. New flows only. Every fact about actions,
conditions, context keys, screens and connectors comes from the MCP; where it and this skill disagree, the MCP wins.
"`flows_read` with operation `X`" means calling the tool with `{operation: "X", args: {...}}`. If the Descope MCP
isn't connected, say so and stop. Built, Changed from the template, Checked, Assumptions and For review are the
sections of the final report (see Report).

## Before building: settle these with the user

Ask in one short message, only what the request leaves open, and wait for the answers. Business facts only the user
knows (names of lists or attributes, API contracts, normalization rules) are questions, never assumptions; only
technical choices may be assumed. Never decide sign-up or failure behavior yourself.

- **Sign-up**: may new users sign up, or existing users only? With SSO, an existing-users-only flow must also stop a
  first SSO login from creating a user (just-in-time provisioning is a tenant SSO setting, not a flow step).
- **Security words**: what "lock", "block", "limit", "expire", "require" mean: for how long, counted where (this
  attempt only, or across attempts), and how it ends (time, an admin, a reset). A count kept in the flow starts again
  with every new attempt; a lock that outlives the attempt needs the app's backend. Say so if the user expects more.
- **Failures on the auth path**: for each connector, scriptlet or outside API, fail open or closed, retries,
  thresholds. Recommend failing closed.
- **Who may use it**: when the request names an audience ("our sales reps", "partners"), does the flow enforce it
  (email domain, tenant, role) or only describe it?
- **Account messages and SSO email**: an explicit "no account for this email" message is built only on request (see
  Security defaults). When a screen they ask for would reveal it (invite-only "not invited", a decline that names the
  email), offer neutral wording in the same message; build the revealing one only if they confirm, and list it under
  For review. When the user types an email to find their SSO, ask whether the IdP's email must match it; recommend
  yes.
- **Values only they know**: thresholds, links, provider names, brand inputs. Values only their project holds (site
  keys, redirect URLs; connector ids come from step 2) never hold up the build: take them if offered, otherwise keep a
  `REPLACE_WITH_...` placeholder and list it in the report.
- **A legacy system or outside API on the auth path**: is it checked on every sign-in (it still owns passwords) or
  only when Descope's own check fails? How does it signal a wrong password or unknown user versus an outage (status
  codes, a body field)? The flow needs both to show the right message and to fail closed on outages.
- **Several tenants**: which tenant does a new user join (none, one matched by email domain, a new one)? Before
  sign-in the flow doesn't know the user's tenants; offer to choose after sign-in, route by email domain, or have the
  app pass the tenant when it starts the flow.

A default you offer must come from a template or an MCP result; otherwise say it is unverified. Never default to
skipping a security check.

## Workflow

1. **Pick a template.** `flows_read` with operation `searchFlowTemplates` (the user's request as the query), then
   `getFlowTemplate` (`templateId`) for the best match; its `flow` is in the shape `ImportFlow` takes. Never write a
   flow from scratch: copy that `flow` and edit the copy. No close template? Take the nearest one
   and tell the user which parts are new. Template keywords are incomplete: when results are `match: any` or miss
   the request, search again with fewer or other words (a method, a template name) before listing all templates.
   - **Keep everything the template does** unless the request explicitly changes it: error routes, locked-account
     and reset paths, verified-email checks, name fields, legal links, masked email or phone. A path the request
     clearly rules out ("no social login") goes, listed under Changed from the template (a security check also under
     For review). Ask before any other removal ("only X" alone doesn't rule a path out), and keep the path if you
     can't ask.
   - **Combining templates**: the one closest to the main path is the base and keeps all its ids. Copied tasks and
     screens get ids not already in the flow (keep `N`/`N.end` pairs as `M`/`M.end`), and their routes point at the
     new ids.
2. **Look up every fact you use**, never guess one:
   - actions: `flows_read` with operation `GetActionCatalog` (`query` to find them, then `query` with `full: true`
     for the inputs and errors of the ones you use; check `total` and narrow the query when it is cut off). Use input
     names exactly; route only the error ids the action lists. An action with non-empty `members` is never a task's
     action: write its members as tasks `N` and `N.end`.
   - condition operators: `flows_read` `GetConditionOperators`. Context keys: `flows_read` `GetContextKeys`
     (`prefix` or `query`) for every key you add or change (one call per prefix is enough); the keys an action writes
     are its `outputs` in the full catalog entry. A key with `<name>` is a pattern: put in a real name from the source
     its description gives (custom attribute names: `users_read` with operation `UserCustomAttributes`). Never guess
     one: a misspelled key resolves empty.
   - screens: start from the template's screens and reuse their components and props; never invent a component or
     prop.
   - connectors: `connect_read` with operation `GetConnectorTemplate` (`{id: "<templateId>"}`) for a named vendor's
     commands and arguments (`LoadAllConnectorTemplates` first only when the vendor is unknown); `LoadAllConnectors`
     for the connector ids the project already has. **Use a vendor's connector template when one exists; Generic HTTP
     is for APIs with none.** A connector the request names but `LoadAllConnectors` doesn't list: ask before
     building, never put in a silent placeholder.
3. **Adapt the template** in your copy: set `flow.flowId` (the user's, or one you propose) and `metadata.name`, then
   change `contents.tasks` and `screens`, and check the copy against Security defaults. Read
   [Flow JSON reference](#flow-json-reference) before writing error routes, row inputs, conditions, connector tasks
   or screens.
   - Wire every requirement end to end: a value a screen collects is saved only if a task reads it, and every
     failure the user mentions (unknown email, wrong code, locked account) gets an explicit path and a message.
   - Automatic error handling (the message on the last screen) is fine for most errors. Route explicitly only when
     no screen precedes the action (start of flow, IdP-initiated: to a screen with a message and a way to start over),
     the call is optional (its failure continues the login), the message would reveal whether an account exists, or
     the user asked for it.
   - Something asked for "after X" (after sign-in, after sign-up) goes on every path that does X: email, social,
     SSO, new and returning users alike.
   - New tasks look console-made: the next unused numeric id (`N.end` for the second half of a two-step action), the
     action's display name, and no `view` (the import places new tasks); keep the template's `view` values.
   - Never make up terms or privacy links: use `REPLACE_WITH_TERMS_URL` / `REPLACE_WITH_PRIVACY_URL`. Never drop a
     requested step for an unknown value: ask, or for a technical choice pick one and list it under Assumptions.
     Secrets belong in the connector, never in flow JSON.
   - Project settings are not flow JSON (account linking by email is the OAuth "Email address handling" setting; SSO
     just-in-time provisioning; password policy). Don't imitate them: name the setting under For review.
4. **Dry run.** `flows_write` with operation `ImportFlow` and `{flow, flowId, traceId, mode: "CREATE", dryRun:
   true}` (`traceId`: any stable id); it runs the `ValidateFlow` checks too. Fix every error; for each warning, fix it
   or say under For review why it doesn't apply. Repeat until no errors remain. A clean result means the flow
   imports, not that it does what was asked. `CREATE` on a flow id that exists fails ("already exists"): pick another
   id, or, only if the user names that flow to replace, use `UPSERT` in both the dry run and the import. Any later
   change needs a new dry run.
5. **Diff.** Always run it: `flows_read` with operation `DiffFlows`, `before` the template's `flow` from step 1
   unchanged, `after` your final flow. It takes only full flows; there is no id form.
6. **Ask before importing.** Show the changes and the For review items, name the project the MCP is connected to
   (ask if you can't tell) and the flow id, and wait for an explicit yes.
7. **Import.** `flows_write` with operation `ImportFlow` and `{draftToken, mode}` from the dry run of the flow the
   user approved. If the call says the session must be elevated, get the user's yes, then make the elevate call it
   names. A `draftToken` lasts 30 minutes; after that, dry-run again. Then have the user run it once (console
   Run, or the hosted page with `?flow=<flowId>`).
8. **Report** (below).

## Security defaults

Apply these unless the user explicitly chooses otherwise, and name every exception in the report. A template is a
starting point, not a vetted default: check your copy against every rule below, fix what it breaks (an unknown-account
error left on automatic handling, SSO without email binding), and list each fix under Changed from the template.

- **No account enumeration.** On sign-in and password reset, a known and an unknown account get the same first screen
  and response. Templates often branch on existence there: fix it, sending nothing to the unknown one. The
  unknown-account error id often also covers send failures, which then look like success: list that under For review
  (watch the audit log). Timing, rate limits and errors only an existing account can hit (tenant SSO required,
  unverified magic-link destination, recovery not set up, password locked, disabled or expired) can still differ; name
  them under For review. Every unknown-account and wrong-credential failure (email, social, passkey, SSO) shows one
  neutral message ("If an account exists, we sent you a code", "Wrong email or password"). Route the action's
  unknown-account error (see Flow JSON reference, Unknown accounts) with custom handling to the screen known accounts
  see: automatic handling shows its text, which names the missing account, and `errorMessage` alone still sends that
  text to the client. Social, passkey and SSO sign-in give a known account a session with no screen: route their
  unknown-account error to a screen with the neutral message and a retry. A screen both reach shows at most the masked
  value the user typed, never a different channel (a phone for an email login); elsewhere show the masked value, never
  the full email or phone. An explicit "no account" message only on request, with the trade-off stated. On sign-up, keep
  the template's "already registered" behavior and list the enumeration trade-off under For review.
- **Fail closed.** When a check on the way to a session can't run (a connector or API down, a scriptlet error, a bot or
  fraud check that errors), the user gets a screen with a message and a way to retry, never the next step or a session.
  This covers the connector's own failure outcome, not only its "bad result" branch. In a condition that allows or
  denies access, test the allow case positively (`equal`, `in`, `is-true`, `greater-than`) and let `ELSE`, which catches
  missing values, deny; negated operators (`not-equal`, `not-in`) hold on a missing value. Risk and fraud checks can
  fail open on their own (a failed risk lookup sets `riskScore` 0.2 and every flag false): name that under For review;
  don't move the user's thresholds. A fail-open the user picks: say what it skips.
- **Gate before creation.** Checks that decide whether someone may have an account (age, consent, abuse) run before
  the action that creates the user (the catalog says which one does). A denial never routes to a send or verify step.
  Password sign-up followed by a verification step (OTP, magic link) sets `contents.deferUserCreation: true`, so an
  abandoned verification leaves no unverified user holding a password.
- **Calls on a failure path change nothing.** A connector that runs after a sign-in already failed (reporting it,
  counting attempts) routes its own errors to the same screen and message the user would see without it.
- **SSO email binding.** Flow collects the email before SSO -> `verifyInitiatedEmail: true` on `saml-start`, so the
  IdP's email must match; list it under For review (it blocks IdP emails that differ from the typed one). Button-only
  SSO has no email to match: leave it off.
- **Passkey-only sign-up** trusts whoever registers first: say so to the user. A passkey path (enroll or sign-in)
  gets a fallback branch on `device.webAuthnSupport` for devices without passkeys, or a question to the user.
- **User input in outside calls.** In a Generic HTTP payload, keep every `{{...}}` inside quotes so values are
  escaped; unquoted, a value can add fields to the request.

## Report

Five sections, headed **Built**, **Changed from the template**, **Checked**, **Assumptions** and **For review**, and
no others, except one status line above them (flow id, imported or draft) when the user asks for it and a short **How
to test** when you couldn't import or run the flow. A user's own format wins; keep the For review items and the
security fixes from Changed from the template in it.

- **Built**: the tasks and routes by path (screens, actions, conditions, where each error goes). Only what the JSON
  shows, never that a path works. Name any path that skips an "after X" step, and why.
- **Changed from the template**: the template's id, then the `DiffFlows` result, removals first. After each removal
  say why: the user asked, or agreed when you asked. A removal with neither goes back into the flow. Name behavior the
  template brings that the user didn't ask for (an existing session skipping verification, an optional field).
- **Checked**: only the calls you made in this session, with their results and counts from your own calls
  ("ImportFlow dry run: 3 calls, the last clean"; "not imported"; "not run").
- **Assumptions**: the defaults you picked, then every runtime behavior the JSON doesn't show (errors an action
  raises, defaults such as sender or code length, score scales, what the app or IdP receives), each with its source:
  an MCP result, a docs URL, or general knowledge. None of it is verified; keep it all here.
- **For review**: a checklist for whoever reviews the flow: the parts added rather than taken from the template
  (task and screen ids); every security choice (fail closed or open, account messages, SSO email binding, skipped
  verification, who may sign in); every placeholder to fill, with its task and argument; every requirement not run end
  to end, with the path to try.

State a number, default, platform behavior or limit ("can't be done") as fact only when an MCP result or your own
check says it; otherwise say you have no source, and ask or try it.

## Flow JSON reference

Shapes the MCP catalogs don't spell out. Action ids, inputs, error ids and context keys still come from the MCP;
screen components and props come from the template's screens.

### Error routing

A task routes its action's errors in `errorHandlingV2`, keyed by error id (the action's `errors[].type`, or for a
connector the command's error ids). A next rule whose `interactionId` is the error id is followed either way; with no
entry and no such rule, handling is automatic: the user is sent back to the last screen with the error; with no screen
before the task, the flow ends with the error.

```json
"errorHandlingV2": {"UserDoesNotExists": {"errorHandlingType": "custom"}},
"next": {"rules": [{"interactionId": "success", "taskId": "3"},
                   {"interactionId": "UserDoesNotExists", "taskId": "7"}]}
```

- `custom`: go to the task named by the next rule whose `interactionId` is the error id.
- `customWithError`: the same, and a screen reached next still shows the error.
- `ignore`: continue as on `success`.
- `abort`: end the flow with the error.
- `errorMessage` replaces the text the user sees with `automatic`, `abort` and `customWithError` (next task a single
  screen); `{{key}}` is filled from context. `custom` clears the error, so put the message on the target screen. The
  original text still reaches the client: an unknown-account error still needs `custom` routing (see Security
  defaults).

After an error, `lastError.Type` holds its id for a later condition, until a `clear-last-error` task.

### Unknown accounts

OTP (including embedded OTP), enchanted-link and email-verification sign-in (and push and NOTP) and password reset fail
for an unknown login id with the action's own error id (for example `OTPSignUpOrInEmailFailed`,
`OTPSignInEmbeddedFailed`, `EmailVerificationSignInFailed`, `PasswordSendResetFailed`), whose automatic message says the
user does not exist. Route that id with `custom` to the same neutral screen a known account reaches. Password sign-in
already masks it ("Wrong password or unknown user"). `UserDoesNotExists` (magic link, social, passkey, wallet) and
`UserExists` say it by name. On sign-up, `UserExists` may keep the template's "already registered" message; state the
trade-off.

### Task arguments and row inputs

Every task argument is `{type, value}`, `type` `"inline"` for a literal: `"command": {"type": "inline", "value":
"get"}`. A list of rows goes in the same wrapper: `"args": {"type": "inline", "value": [rows]}`.

An input the catalog shows as `visible` with type `object` takes a list of `{key, type, value}` rows (`args`,
`customClaims`, `userPropertiesDefinitions` and the like); `familyPropertiesDefinitions` and
`dependentPropertiesDefinitions` also take rows. Other object inputs are not rows; set one only when the request needs
it. With `type` `"context"`, `value` is a context key (with or without `{{ }}`). With any other type, `value` is used
as is, and `{{key}}` inside a string is still filled from context. A `value` that is itself a list of rows becomes an
object.

```json
[{"key": "email", "type": "context", "value": "form.email"},
 {"key": "plan", "type": "string", "value": "pro"},
 {"key": "address", "type": "object", "value": [{"key": "city", "type": "context", "value": "form.city"}]}]
```

### Conditions

Conditions are tried in order; the first that holds takes the rule with its `interactionId`. `ELSE` always holds,
so it goes last. Every condition but `ELSE` needs `atomicConditions`, which must all hold unless the condition sets
`logicalOr: true`: `target` is the context key, `predicate` the value compared, `operator` an id from
`GetConditionOperators`. The allow case is the tested one; `ELSE` denies.

```json
{"id": "7", "type": "condition", "name": "Is risk low?",
 "conditions": [
  {"name": "Low risk", "interactionId": "low", "atomicConditions": [{"operator": "less-than",
   "target": {"type": "context", "value": "riskInfo.riskScore"}, "predicate": {"type": "inline", "value": "0.5"}}]},
  {"name": "Otherwise", "interactionId": "ELSE"}],
 "next": {"rules": [{"interactionId": "low", "taskId": "5"}, {"interactionId": "ELSE", "taskId": "8"}]}}
```

### Connector tasks

A vendor integration (reCAPTCHA, Twilio, a CRM) is the `connector` action with that vendor's `templateId`, not an
action of its own. Commands, their parameters and error ids come from `GetConnectorTemplate` with
`{id: "<templateId>"}`. Each parameter not marked `hidden` is one `args` row whose `key` is the parameter's name;
hidden ones are filled from context and replace any row of that name.

- A parameter's `defaultValue` is the row's value when it is a real value; when it is an example (a commented sample
  query, a placeholder), write the value the request needs.
- Never put user input (`{{form...}}`, `{{user...}}`) into a SQL string; an example default may do it. Ask the user
  how the query gets its values.
- A command with `defaultAsync: true` gets `"async": true`. An async task returns no response and its command's
  failures are only logged (setup failures, such as a missing or disabled connector, still raise `ConnectorFailed`):
  leave out `resultPath` and error routing, and never gate access on it.

```json
{"id": "4", "type": "automated", "action": "connector", "name": "Check bot",
 "arguments": {"connectorId": {"type": "inline", "value": "<connector id>"},
  "templateId": {"type": "inline", "value": "http"}, "command": {"type": "inline", "value": "get"},
  "resultPath": {"type": "inline", "value": "botCheck"},
  "args": {"type": "inline", "value": [{"key": "endpoint", "type": "string", "value": "/v1/checkbot"}]}},
 "next": {"rules": [{"interactionId": "success", "taskId": "5"}]}}
```

- Output: the response lands at `connectors.<resultPath>` (the template doesn't list its fields).
- Errors: a failed command fails with its own error id, or `ConnectorFailed`. Generic HTTP fails with
  `request_error` on a non-2xx response (`connectors.<resultPath>.statusCode` and `.errorText`); an error matching a
  retry rule is `request_error_rule_<rule id>`, handled as `request_error` (a timeout or network error: as
  `ConnectorFailed`) when the task has no entry for it.
- Tags on a command set args at runtime, replacing a row of the same name: `with-email` (`email`), `with-phone`
  (`phone`), `with-user-id` (`userId`), `with-external-id` (`externalId`), `with-external-ids` (`externalIds`),
  `with-user-agent` (`userAgent`, `userIpAddress`), `with-callback-url` (`callbackUrl`), `with-webhook` (`pendingRef`,
  `webhookUrl`), `with-analytics-client-id` (`clientId`, unless set). `risk` adds the risk token and writes
  `riskInfo`.
- `exchangeStepId`: for a `with-callback-url` command, the id of the task the user comes back to; the callback URL
  resumes the flow there. Leave it out otherwise.

### Screens

- Every interaction a screen's components emit is listed in `interactions` and needs a next rule on the screen task;
  without one, the flow fails when the user triggers it.
- An input with a built-in name (`email`, `phone`, name fields) keeps it and is read as `form.<name>`. A custom
  input is named `form.<key>` and read as `form.<key>`; a bare custom name reads empty.
