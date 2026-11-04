# Connectors

A connector task calls an outside service through a connector the user configured in the project (Connectors page):
an HTTP API, reCAPTCHA Enterprise, a fraud or identity-verification vendor. The connector holds the credentials and
base URL; the flow task picks the connector, a command, and the arguments.

A screen component never calls a connector by itself. A `Recaptcha` component on a screen only supplies the browser's
token (`sdkScriptsResults.grecaptcha_riskToken`); nothing is assessed and no score exists until a `connector` task
with the `assess` command runs. Likewise a condition on a
connector's result reads nothing unless a connector task ran before it.

## The task

```json
"17": {
  "id": "17",
  "type": "automated",
  "name": "reCAPTCHA Enterprise / Assess",
  "action": "connector",
  "arguments": {
    "templateId": { "type": "inline", "value": "recaptcha-enterprise" },
    "command": { "type": "inline", "value": "assess" },
    "connectorId": { "type": "inline", "value": "<the project's connector id>" },
    "args": { "type": "inline", "value": [] },
    "resultPath": { "type": "inline", "value": "recaptcha-enterprise_assess" },
    "async": { "type": "inline", "value": false },
    "exchangeStepId": { "type": "inline", "value": "" }
  },
  "errorHandlingV2": {
    "ConnectorFailed": { "errorHandlingType": "custom" },
    "create_assessment_error": { "errorHandlingType": "custom" }
  },
  "next": { "rules": [
    { "interactionId": "success", "taskId": "4" },
    { "interactionId": "ConnectorFailed", "taskId": "21" },
    { "interactionId": "create_assessment_error", "taskId": "21" }
  ] },
  "view": { "x": 816, "y": -48 }
}
```

| Argument | Value |
|---|---|
| `templateId` | The connector type: `http` (Generic HTTP), `recaptcha-enterprise`, `abuseipdb`, `fingerprint`, `forter`, `telesign`, `arkose`, `clear`, `incode`, ... |
| `command` | The operation, per connector type: `http`: `get`, `post`, `put`, `patch`, `delete`; `recaptcha-enterprise`: `assess`, `annotate` |
| `connectorId` | The id of the connector configured in the user's project (`CI...`). The flow can't create one: ask the user for it |
| `args` | Key/value rows for the command's parameters (`[]` when it takes none). Generic HTTP: `endpoint` (appended to the base URL), `payload` (a JSON string, `{{...}}` inserts context values), `timeout` |
| `resultPath` | Where the response lands: `connectors.<resultPath>`. The console uses `<templateId>_<command>` |
| `async`, `exchangeStepId` | `false` and `""` unless the connector has a two-step command (identity verification start/result pairs use `N`/`N.end`) |

Name the task for what the call does (`Fetch plan from API`), as most production flows do, or as the console names
a new one: `<connector name> / <command>` (`reCAPTCHA Enterprise / Assess`, `Generic HTTP / POST`).

## Reading the result

The response is in the context under `connectors.<resultPath>`:

- Generic HTTP: the parsed JSON body at `connectors.http_post.<field>`, with no `body` wrapper; a non-JSON or empty
  body becomes `{}`. With the connector's `includeHeadersInContext` on, the result is `{body, headers,
  statusCode}`, so fields move to `connectors.http_post.body.<field>` (header names lowercased). A non-2xx response
  is the `request_error` error, not a success with a status code (see Failures).
- reCAPTCHA Enterprise assess: `connectors.recaptcha-enterprise_assess.riskAnalysis.score`, Google's score from 0 to
  1, where 1 means very likely human and 0 very likely a bot.

Risk-tagged commands (reCAPTCHA `assess` among them) also merge their result into the flow's `riskInfo`. For
reCAPTCHA, `riskInfo.riskScore` is the same Google score (high = human, set from
`riskAnalysis.score`), and `riskInfo.botDetected` is true when it is below the connector's bot threshold (default
0.5). Descope's own risk sources run the other way (a filled honeypot field sets `riskScore` 1.0 = bot; fingerprint
risk is high = risky), and `riskInfo` keeps the highest score and ORs the booleans. With one risk source in the
flow, the score's direction is known (fingerprint `risk`: high = risky; reCAPTCHA: high = human) and a threshold
condition on `riskInfo.riskScore` is right. Only when several sources run can it mean either: then condition on
`riskInfo.botDetected` or on `connectors.<resultPath>`. The cut-off is the user's choice: ask for the number.

Read it in a condition, a `custom-claims` row or a later argument. Index into lists with the `jq:` prefix
(`guardrails.md`).

## Failures

Every connector task can fail with `ConnectorFailed` (connector missing or misconfigured, service unreachable) and
with its command's own errors (`request_error` for Generic HTTP; `create_assessment_error` for reCAPTCHA assess,
`annotate_assessment_error` for annotate). Left at `automatic`, a failure sends the user back to the last screen with
an error. Decide with the user whether the flow fails open (continue without the result) or closed (stop, or add
another check), and route both kinds of error explicitly with `custom` handling and a next rule each. On the
sign-in path, recommend failing closed (`guardrails.md`).

A connector on a failure path (reporting a wrong code or password to the app's backend, counting attempts) runs
after the sign-in has already failed. Its own errors must never lead toward a session: route `ConnectorFailed` and
the command's error to the same screen and message the user would see without the call, so an outage changes
nothing the user sees. If the call does something the user relies on (a lock that counts the failures), say in the
report that an outage skips it.

Generic HTTP: a non-2xx response fails with `request_error` and writes `{statusCode, errorText}` (`errorText` is the
raw body string) to `connectors.<resultPath>`. A timeout fails with `ConnectorFailed` and writes nothing. The
connector's base URL must be a public host: a private one (localhost, an internal address) fails every call with
`ConnectorFailed` "Invalid domain".

## Payload templates

Keep the Generic HTTP `payload` valid JSON with every `{{...}}` inside quotes (`{"password": "{{form.password}}"}`):
the engine then fills the values inside the parsed JSON and escapes them. In a payload that isn't valid JSON (an
unquoted `{{x}}`) values are pasted in as text, so a value with a quote can add fields to the request: an injection
risk when it carries user input. A string that is exactly `"{{x}}"` gets the value's own type (a number stays a
number); `{{x:json}}` JSON-encodes it.

These HTTP facts were not run end to end: list what you rely on under "Assumed, not verified".

## Bot protection with reCAPTCHA Enterprise

1. Put a `Recaptcha` component on the first screen (copy it from `catalog/screens/components.md`; `enterprise:
   true`). It sends the browser's token with the form.
2. After the screen, add the `connector` task above with `command: "assess"`.
3. Add a condition on `riskInfo.botDetected` (is-true blocks), or for your own threshold on
   `connectors.recaptcha-enterprise_assess.riskAnalysis.score`: `greater-than` the threshold continues, the rest go to a block screen or an extra factor (OTP). Add `ELSE`.
4. Route `ConnectorFailed` and `create_assessment_error` (fail open or closed, as agreed).
5. Optional: `annotate` tasks (`args`: `annotation` `LEGITIMATE` or `FRAUDULENT`, `reason`) tell Google how the
   assessment turned out, which improves later scores.

The user needs a reCAPTCHA Enterprise connector configured in the project; ask for its id. A complete flow is the
recipe `../recipes/sign-up-or-in-otp-email-recaptcha/README.md`.

For a full Generic HTTP example (POST after login, response into JWT claims, fails closed: an error screen and no session), see the recipe
`../recipes/sign-up-or-in-http-connector-claims/README.md`.
