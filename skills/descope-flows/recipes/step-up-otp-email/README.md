# Step-up with an email OTP

For a user who is already signed in: before a sensitive action (change of payment details, deleting data, viewing
secrets) the app runs this flow, the user proves it's them again with a one-time code by email, and the flow returns
a fresh session whose JWT is marked as stepped up. From the console template `otp-template-step-up` (SMS),
switched to email.

## When to use

"Step-up authentication", "re-authenticate before X", "confirm it's you", "elevated session", "sudo mode". Step-up is
a separate flow the app starts for a signed-in user, not a branch of the login flow. For risk-based MFA during login
(ask for a second factor only when the risk score is high) the pattern is a condition on `riskInfo.riskScore` inside
the login flow instead; see the console templates `adaptive-mfa-*`.

## Flow

```
start --> 14 Step Up (loadUser) --> 14.end Step Up (step-up) --> 11 send OTP to the user's email --> 12 Verify OTP --> 13 verify --> 7 End (JWT, stepped up)
                                                                  ^    |                              \--resend--> 11
                                                                  |    \--any error--> 15 Code not sent
                                                                  \--Try again--------------------/
```

| Task | Type, action | What to know |
|---|---|---|
| `14` | `loadUser` | Loads the signed-in user from the refresh token the app sends with the flow request. Without a signed-in user the flow fails here: the app must start it from an authenticated page (the SDKs send the refresh token). |
| `14.end` | `step-up` | Marks the flow as step-up; the console pairs it with `14` under the name "Step Up". The session that `7` issues is a step-up session. |
| `11` | `sign-in-otp-email` | Sends the code to the loaded user's email; no email input on any screen. |
| `11` errors | | No screen runs before `11`, so automatic error handling has nowhere to show an error: all six declared errors (rate limit, send failure, tenant requires SSO or disabled, recovery destination) use `errorHandlingV2: custom` and go to `15`. |
| `15` | screen | "We couldn't send you a code"; Try again `resend` -> `11`. |
| `12`, `13` | screen, `verify-code-otp-email` | `CodeInput` `L1T9iO4p5U` auto-submits; `resend` -> `11`. Shows `{{sentTo.maskedEmail}}`. |
| `7` | `logged-in` | Issues the new session; its JWT carries `su: true` (checked by e2e). |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **SMS instead of email**: `sign-in-otp-sms` on `11`, `verify-code-otp-sms` on `13`, and `{{sentTo.maskedPhone}}` in
  task `12`'s screen text (this is the template's original form). The user needs a verified phone.
- **Passkey instead of a code**: replace `11`-`13` with a `webauthn-sign-in-start` / `webauthn-sign-in-finish` pair
  (`N` / `N.end`, `finishStepId` = `N.end`, as the passkey pairs in
  [sign-up-or-in-passkeys-otp-email](../sign-up-or-in-passkeys-otp-email/README.md)) and a screen with a
  `PasskeyButton` before it.
- **In the app**: start this flow (its flow id) only before the sensitive action, then have the backend check the new
  session's `su` claim before doing it.

## Pitfalls

- Keep `14` (`loadUser`) and `14.end` (`step-up`) first and together; a step-up flow without `loadUser` has no user to
  send the code to.
- The backend must check the step-up claim; the flow alone protects nothing if the API accepts any session.
- `sign-in-otp-email` errors if the user has no email (e.g. phone-only users); offer SMS for those.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: a signed-in user (refresh
  token) verifies an email code and ends with the same user id and `su: true`: pass. The error path to `15`: not
  run (no way found to make `sign-in-otp-email` fail for a signed-in user locally).
