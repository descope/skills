# Passwords with reset by email link

Email and password sign-in and sign-up, where "Forgot password" emails a link instead of a code: the link opens a
new tab where the user sets a new password and is signed in. The waiting screen reads the same whether or not the
email has an account. Built from
[passwords-sign-up-or-in-verify-email](../passwords-sign-up-or-in-verify-email/README.md) (which resets by code),
with `password-send-reset` and its `verify-magic-link` pair (the console's "Send Password Reset" action, catalog
`password-send-reset-group`) and the waiting screens of [sign-up-or-in-magic-link](../sign-up-or-in-magic-link/README.md).

## When to use

"Forgot password link", "reset password by email link", "send a password reset email", a legacy app migrating its
reset emails. For a reset code the user types, use
[passwords-sign-up-or-in-verify-email](../passwords-sign-up-or-in-verify-email/README.md).

## Flow

```
1 Login --Sign In--> 21 password sign-in --> 24 email verified? --> 0 JWT  (as in the base recipe)
  |--Sign up--> 6 Create account --> 7 password sign-up --> 8 verify email ...
  \--Forgot--> 16 Forgot password --Next--> 11 send reset link --success / PasswordSendResetFailed--> 12 Reset Link Sent
                                              |                                           |  \--resend--> 11
                                              |                                           |  \--polling-error (link expired)--> 16
                                              |                                           \--polling--> 25 Link Opened
                                              \--success--> 11.end verify link (the link's tab) --> 14 New password --> 15 update --> 0 JWT
```

| Task | Type, action | What to know |
|---|---|---|
| `16` | screen | `EmailInput` (`email`); Next `AMeyg_7npF` -> `11`. |
| `11` / `11.end` | `password-send-reset` / `verify-magic-link` | A pair: same name ("Send Password Reset"), `verifyStepId` = `11.end`, two `success` rules on `11` (to the waiting screen and to `11.end`). `uri`: the page the link opens; `providerId` / `templateId` `""` use the project's default email. Sends to the user's email; on success it sets `sentTo.maskedEmail`. |
| `11` errors | | `PasswordSendResetFailed` is also what an email with no account raises (read from the engine source). It is routed with `errorHandlingV2: custom` to the same waiting screen `12`, so the screen never tells which emails exist. |
| `12` | screen | Text that doesn't depend on the outcome ("If an account exists for this email..."), no ErrorMessage (it could name the missing account), a `PollingLoader` (`polling` once the link is used -> `25`, `polling-error` when it expires -> `16`), "Send again" `resend` -> `11`. |
| `25` | screen | Shown in the first tab once the link was opened: the user goes on in the link's tab. No next. |
| `14`, `15` | screen, `password-update` | In the link's tab, where `11.end` signed the user in: `NewPassword` (`newPassword`), then the update. |
| `0` | `logged-in` | Issues the session in the link's tab. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Redirect URL** (do this first): set `tasks.11.arguments.uri.value` to the app page that hosts the flow, or
  configure the project's magic link redirect URL (the action reads the magic link settings), or have the app pass
  `redirectUrl` when it starts the flow. With none of them `11` fails with `MagicLinkMisconfiguration`.
- **No self sign-up, no email verification, no name**: as in the base recipe's Adapt.
- **Send to a recovery email**: set `useRecoveryEmail` on `11` to `true`. A user without a verified recovery email
  then raises `SignInRecoveryDestinationNotSet` or `SignInRecoveryDestinationNotVerified`; route both to `12` too to
  keep hiding which accounts exist.
- **Email template**: `providerId` / `templateId` on `11`; the email carries the link. With both `""` it goes
  through the project's password settings' email provider, not the magic link one.

## Pitfalls

- Keep `11` / `11.end` together: same name, `verifyStepId` = `11.end`, both `success` rules on `11`.
- Don't route `PasswordSendResetFailed` to a screen that shows the error, and don't show `{{sentTo.maskedEmail}}` on
  `12`: an unknown email leaves it empty, which tells the visitor the account doesn't exist.
- The new password is set in the tab the link opened, not the first tab; the first tab only learns that the link
  was used (`25`).
- After `11.end`, `user.email` is set in the link's tab, so screen `14`
  can show `{{user.email}}` once `user.email` is in that task's `contextKeys` (checked end to end).
- `password-send-reset` is hidden in the console's action list (it appears as the "Send Password Reset" group);
  write the two tasks, never the `-group` name.

## Checked

- `scripts/validate_flow.py` and `scripts/flow_style.py` (this skill's checkers): ok, no errors, warnings or style
  notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: an existing user gets the link, it verifies on `11.end`, and the new
  password is set in the link's tab: pass. The unknown-email path: not run.
