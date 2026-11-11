# Inbound app consent, with email OTP sign-in

The consent flow of an inbound app (Descope as the OAuth / OIDC provider for a third-party or partner app, an MCP
client, an AI agent): when the app sends the user to authorize, the user signs in with an email OTP if they have no
session, then sees the app's requested scopes and authorizes or cancels. Users who already consented to those scopes
skip the screen. From the console template `inbound-apps-user-consent`, without Google and Microsoft.

## When to use

"Inbound app", "third-party app consent", "OAuth consent screen", "authorize an MCP client / agent", "Descope as
the identity provider for another app". Choose this flow as the consent flow in the inbound app's settings in the
console. The flow only works when started by the app's `/authorize`, which passes the app and its scopes; run
on its own, it has no app to consent to. For consent by a tenant admin on behalf of the whole tenant, start from the
templates `inbound-apps-tenant-consent` or `inbound-apps-user-tenant-consent` (`create-consent` with
`tenantLevel: true`, after a tenant selector).

## Flow

```
start --> 1 signed in? --yes--> 14 Load User ------------------------------------------------------> 4
                       \--no--> 7 Welcome (email) --> 8 send OTP --> 9 Verify OTP --> 10 verify --> 4
4 not consented yet? --yes--> 13 app verified? --yes--> 5 Consent (verified) --Authorize--> 6 create-consent --> 0 End
                     |                         \--no--> 15 Consent (unverified, warning) --Authorize--> 6
                     |                                    5 / 15 --Cancel--> 0 End (access_denied)
                     \--no (already consented)--> 0 End
```

| Task | Type, action | What to know |
|---|---|---|
| `1` | condition | `user.loggedIn` is-true: the user has a session in this browser (the SDK sends its refresh token). |
| `14` | `loadUser` | Loads the signed-in user, so no sign-in screen is shown. |
| `7`-`10` | screens, `sign-up-or-in-otp-email`, `verify-code-otp-email` | Email OTP for users without a session. |
| `4` | condition | `thirdPartyApp.user.consented` is-false. `consented` is true when one of the user's unexpired consents for this app covers all the requested scopes; it then also records that consent, and `0` issues the code with it. |
| `13` | condition | `inboundApp.verified` is-true: the app's status in the console is Verified. Unverified apps get the screen with a red warning. |
| `5`, `15` | screen | `ScopesList` `u8HvnRL4YV` named `thirdPartyAppApproveScopes` (checkboxes, all checked; required scopes can't be unchecked), filled by the engine with the requested scopes. Texts use `{{project.name}}` and `{{thirdPartyApp.name}}`; `ThirdPartyAppLogo` shows the app's logo. Authorize `_Z6xPaS9jy` -> `6`; Cancel `6N3cb_5t3T` -> `0`. |
| `6` | `create-consent` | Stores the user's consent to the checked scopes and records it for `0`. Optional arguments: `duration` (minutes; empty = no expiry), `tenantLevel`, `scopesAutoApproval` (grant the requested scopes without a screen). |
| `0` | `logged-in` | Returns to the app: with a consent, an authorization code; without one (Cancel), the app's error redirect with `error=access_denied` and "Consent not granted or rejected". |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Social login too**: put the template's Google / Microsoft buttons back on `7` (an `oauth-start` /
  `exchange-oauth-code` pair to `4`), as in [sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md).
- **Consent expires**: set `duration` on `6` (e.g. `{"type": "inline", "value": "43200"}` for 30 days); after it,
  `4` asks again.
- **One screen for all apps**: drop `13` and `15` and point `4`'s rule at `5` (no warning for unverified apps).
- **Texts**: `LmrSIGOWZb` (title) and `_FBvzhJtOx` ("... will be able to:") on both consent screens; the warning is
  `XGFJtHqtkn` / `NpV0qhppf_` on `15`.

## Pitfalls

- Keep the `ScopesList` named `thirdPartyAppApproveScopes` and keep that key in the screen task's `allInputKeys`: the
  engine fills the list only then, and `create-consent` reads the checked scopes from that input.
- Cancel works by reaching `0` without a consent; don't add a `create-consent` on that path, and don't send Cancel
  anywhere that could set one (only `4`'s check does, and only for an existing full consent).
- The user can uncheck optional scopes only if the app allows partial scopes; otherwise, or for a required scope,
  `create-consent` fails (`CreateConsentFailed`) and the error shows on the consent screen.
- Users need the roles or permissions an approved permission scope maps to, or `create-consent` fails.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Engine behavior (Cancel -> `access_denied`, `consented` semantics, `create-consent` arguments and validation, the
  `allInputKeys` requirement) read from the engine source.
- e2e: not run (the runner can't start a flow from an inbound app's `/authorize`).
