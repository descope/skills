# Call your API after login and add its answer to the JWT

Email OTP sign-up or sign-in; after login the flow POSTs the user to the app's backend through the Generic HTTP
connector and copies fields of the response (`plan`, `accountId`) into the session JWT as custom claims. If the API call
fails, the user gets an error screen and no session: the app never sees a JWT without the claims it relies on. Built
from [sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) without Google; the connector and
claims tasks follow the console's shape (console templates' connector tasks, Descope's own connector test flows).

## When to use

"Call our API during login", "sync the user to our backend", "enrich the token with data from our service", "check
the user against our database", webhooks on sign-up. Generic HTTP is the most used connector in production flows.
For a check that should block login (deny list, account status), route the response through a condition instead of
straight to the claims (see Adapt).

## Flow

```
0 Welcome (email) --> 19 send OTP --> 20 Verify OTP --> 21 verify --> 4 new user? --yes--> 12 User Information --> 7 update user --> 22
                                                                       \--no-------------------------------------------------> 22
22 HTTP POST --success--> 23 custom claims --> 8 JWT
      \--request_error / ConnectorFailed--> 24 Sign-in failed --Back to sign in--> 0
```

| Task | Type, action | What to know |
|---|---|---|
| `0`-`21`, `4`, `12`, `7` | | The OTP email login of the base recipe. |
| `22` | `connector` | `templateId: "http"` (Generic HTTP), `command: "post"` (also `get`, `put`, `patch`, `delete`), `connectorId`: the id of an HTTP connector configured in the project (Connectors page; it holds the base URL, auth and headers). `args` rows: `endpoint` (appended to the connector's base URL), `payload` (a JSON string; `{{...}}` inserts context values such as `user.userId`, `user.email`, `form.<input>`), `timeout` in seconds. The response's JSON body lands at `connectors.<resultPath>.<field>` (`connectors.http_post.plan`); only with the connector's "include headers in context" setting is it `{body, headers, statusCode}`, fields under `.body.<field>`. A non-2xx answer (`request_error`) writes `statusCode` and `errorText` there; a plain timeout is `ConnectorFailed` and writes nothing (from the connector's source, not run). |
| `22` errors | | `request_error` is the HTTP connector's error for a non-2xx answer (a plain timeout is `ConnectorFailed`). It is routed with `errorHandlingV2.request_error: custom` and a next rule `request_error` -> `24` (fail closed). `ConnectorFailed` (the connector can't run: missing, misconfigured, unreachable) is routed the same way. |
| `24` | screen | "We couldn't sign you in"; Back to sign in `S-VOZ5i7gc` -> `0`. |
| `23` | `custom-claims` | Each `customClaims` row is a claim name and a value; `type: context` reads a context path. Check the response shape: a path the response lacks does not become a useful claim. |
| `8` | `logged-in` | Issues the session with the claims. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Connector id** (required): replace `REPLACE_WITH_HTTP_CONNECTOR_ID` in `tasks.22.arguments.connectorId.value` with
  the project's HTTP connector id (the MCP or management API lists connectors). Create the connector first if the
  project has none; the flow can't create it.
- **Endpoint and payload**: set the `endpoint` row (e.g. `/users/sync`) and the `payload` string. Keep the payload valid
  JSON with every `{{...}}` quoted (`"{{user.email}}"`): the engine then escapes the values. Unquoted, a value with a
  quote can add fields to the request ([connectors](../../references/connectors.md), Payload templates).
- **Claims**: edit `tasks.23.arguments.customClaims.value`, one `{"key": "<claim>", "type": "context", "value":
  "connectors.http_post.<field>"}` per claim. Claims can also be static (`"type": "string"`).
- **Block login on the API's answer**: insert a condition between `22` and `23`, e.g. `equal` on
  `connectors.http_post.allowed` with predicate `true`, ELSE to `24`.
- **Fail open** (only if the app works without the claims, and the user chose it): point the `request_error` and
  `ConnectorFailed` rules at `8` and delete `24`. A legacy outage then logs users in without the claims.
- **Call only on sign-up**: move the call into the new-user branch (`7` -> `22`) and point `4`'s ELSE at `8`.
- **GET instead of POST**: `command: "get"`, drop the `payload` row, and pass values in the endpoint's query string
  (`/users?email={{user.email}}`); rename `resultPath` (e.g. `http_get`) and the claims' paths with it.

## Pitfalls

- Don't put the API secret in the flow: it belongs in the connector's authentication settings.
- `resultPath` and the `connectors.<resultPath>` paths in later tasks must match; renaming one breaks the claims
  silently (empty values).
- `request_error` is a connector-template error, not one of the `connector` action's catalog errors, so a strict
  catalog check may flag the rule; it is valid (Descope's own connector tests route it).
- Custom claims become part of the JWT that the app's backend trusts: only copy fields the API controls.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end (a variant): the success path can't run locally (the HTTP Lambda refuses private
  hosts). With the connector at a private host the step failed as `ConnectorFailed` and went to `24`, no errorText:
  pass.
