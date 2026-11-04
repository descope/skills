# Compute values with a scriptlet and put them in the JWT

Email OTP sign-up or sign-in; after login a scriptlet (a small JavaScript function run by Descope) derives values from
the user (email domain, an admin flag, a tier) and they go into the session JWT as custom claims. If the script fails,
the user gets an error screen and no session: the app never sees a JWT without the claims it relies on. Built from
[sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) without Google; the scriptlet task follows
the console's shape (content template `sign-up-or-in-with-sso-exclusion-list`, task `10`).

## When to use

"Run custom logic in the flow", "compute a claim", "transform user data", "map roles", "decide based on several
fields" when no single action or condition does it. Scriptlets are in most large customers' flows. For a call to an
outside service, use [sign-up-or-in-http-connector-claims](../sign-up-or-in-http-connector-claims/README.md)
instead: scriptlets are for computing over values the flow already has.

## Flow

```
0 Welcome (email) --> 19 send OTP --> 20 Verify OTP --> 21 verify --> 4 new user? --yes--> 12 User Information --> 7 update user --> 22
                                                                       \--no-------------------------------------------------> 22
22 Scriptlet --success--> 23 custom claims --> 8 End (JWT)
      \--ScriptletFailed--> 24 Sign-in failed --Back to sign in--> 0
```

| Task | Type, action | What to know |
|---|---|---|
| `0`-`21`, `4`, `12`, `7` | | The OTP email login of the base recipe. |
| `22` | `scriptlet` | Three required inputs. `scriptArgs`: rows `{"key": "<variable>", "type": "context", "value": "<context path>"}`; each key becomes a variable in the script (`email` from `user.email`, `roles` from `user.roleNames`). `scriptCode`: the function body; it must `return` an object. `outputPath`: where the result lands, here `claims` -> `scripts.claims.<field>`. `overrideForm` (optional) writes result values back into `form.*`. |
| `22` errors | | `ScriptletFailed` (a syntax error, an exception thrown by the script) is routed with `errorHandlingV2.ScriptletFailed: custom` and a next rule `ScriptletFailed` -> `24` (fail closed). |
| `24` | screen | "We couldn't sign you in"; Back to sign in `S-VOZ5i7gc` -> `0`. |
| `23` | `custom-claims` | Copies `scripts.claims.emailDomain`, `.isAdmin`, `.tier` into JWT claims of the same names. |
| `8` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Your logic**: replace `tasks.22.arguments.scriptCode.value`. Add one `scriptArgs` row per value the script needs;
  the console's own example passes `unauthUserTenants` and `unauthUser.loginIds`.
- **Different output name**: change `outputPath` and every `scripts.<outputPath>.` path in later tasks together.
- **Branch on the result instead of (or as well as) claims**: put a condition after `22` on
  `scripts.claims.<field>`, e.g. `is-true` on `scripts.claims.isAdmin`.
- **Fail open** (only if the app works without the claims, and the user chose it): point the `ScriptletFailed`
  rule at `8` and delete `24`. The user then logs in with a JWT that lacks every claim from the script.

## Pitfalls

- A context path that doesn't exist reaches the script as `null` or as an empty value of its type, so guard every
  input: `typeof email === "string" ? ... : ""`, `Array.isArray(roles) ? ... : []`. Unguarded property access
  on a missing input is a common scriptlet failure in production flows.
- The input names are `scriptArgs`, `scriptCode` and `outputPath`; `args`, `code` and `resultPath` are silently
  dropped by import (descope/etc#18953). Rows are typed `context` (from the flow) or a value type such as `string`,
  never `inline`.
- The script returns an object; its fields are what later tasks can read. Returning a string or nothing gives no
  usable `scripts.<outputPath>` fields.
- Custom claims become part of the JWT the app trusts: don't derive authorization claims from values the user typed
  (`form.*`).

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: a new and an
  existing user end with `emailDomain`, `tier` and `isAdmin` claims from the script: pass. The failure path to `24`
  (a variant whose script throws): `ScriptletFailed` goes to `24` with no errorText; with
  `customWithError` the errorText is "Unexpected error occurred": pass.
