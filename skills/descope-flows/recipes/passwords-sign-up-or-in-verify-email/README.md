# Passwords: sign in, sign up with email verification, reset, expired password

Email + password login with an explicit sign-up screen, an email OTP to verify new (and still unverified) users, a
forgot-password path by email code, and a forced replace when the password has expired. From the console
template `passwords-explicit-sign-up`.

## When to use

The user wants classic email + password login, usually with "verify the email", "forgot password" or "reset
password". In production, password sign-in and reset are far more common than password sign-up: if users are created
elsewhere (invites, an admin, a migration), delete the sign-up branch (`6`, `7`) and keep the rest.

## Flow

```
1 Login --Sign In--> 21 password sign-in --success--> 24 email verified? --yes--> 0 JWT
  |                        |                               \--no--> 8 send email OTP --> 20 Verify email code --> 10 verify --> 0 JWT
  |                        \--PasswordExpired--> 22 Replace Expired Password --> 23 replace --> 24
  |--Sign up--> 6 Create account --Sign Up--> 7 password sign-up --> 8 (same email verification)
  \--Forgot--> 16 Forgot password --Next--> 11 send reset OTP --> 12 Verify reset code --> 19 verify --> 14 New password --> 15 update --> 0 JWT
```

| Task | Type, action | What to know |
|---|---|---|
| `1` | screen | `EmailInput` (`email`), `Password` (`password`), buttons Sign In `AMeyg_7npF`, Forgot `21RBHXscmj`, Sign up `XLmMGCy6IS`. |
| `21` | `password-sign-in-v2` | Reads `email`/`password` from the screen. `PasswordExpired` has custom error handling (`errorHandlingV2`) and its own next rule to `22`; other errors show on the screen (automatic). |
| `22`, `23` | screen, `password-replace-v3` | Current `password` + `newPassword`. |
| `24` | condition | `user.verifiedEmail` is-true -> `0`; else verify first. |
| `6`, `7` | screen, `password-sign-up` | `FullNameInput` (`fullName`), `EmailInput`, `NewPassword` (`newPassword`, shows the project password policy through the `pswdPolicy` context key). `password-sign-up` stores `fullName` as the user's name. |
| `8` | `update-user-otp-email` | Sends a code to the user's email to verify it (`addToLoginIDs: false`, `onMergeUseExisting: "true"`). |
| `20`, `10` | screen, `verify-code-otp-email` | `Code` input `code` auto-submits (`oneTimeCodeId` interaction) or the Next button submits. |
| `16`, `11` | screen, `sign-in-otp-email` | The reset proves email ownership with a sign-in code; after `19` the user is authenticated. |
| `14`, `15` | screen, `password-update` | Sets the new password for the now authenticated user. |
| `0` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **No self sign-up**: delete tasks `6`, `7`, task `6`'s screen, the Sign up button `XLmMGCy6IS` in the
  task `1`'s screen and the `XLmMGCy6IS` rule of task `1`, and its entry in the screen's `interactions`.
- **No email verification**: make `21` and `23` go straight to `0` and `7` to `0`, then delete tasks `8`, `10`, `20`,
  `24` and task `20`'s screen.
- **Reset by link instead of code**: start from [passwords-reset-by-link](../passwords-reset-by-link/README.md).
- **No name at sign-up**: delete node `raEe6rX__S` from task `6`'s screen (and from its parent's `nodes`) and
  `fullName` from task `6`'s `inputKeys` and `allInputKeys`.
- **Email templates**: `providerId`/`templateId` on `8` and `11` are `""` (project default); set them to use a custom
  email connector or template.
- **Password rules** live in the project's password settings, not in the flow.

## Pitfalls

- `21` routes `PasswordExpired` to `22` through a next rule whose `interactionId` is the error type. The engine picks
  that rule by the error type alone; `errorHandlingV2.PasswordExpired: custom` is how the console editor records that
  the error has its own path. Write both, as here.
- Both `Verify ...` screens share component ids (`oneTimeCodeId`, `3FKqSxRQeF`, `resend`): fine, ids are per screen.
- Screen ids here are the console's (`SC...`). When adding a screen, give it a new unique id of the same form and never
  one that starts with `new-`: import treats `new-<taskId>` as an editor placeholder, renaming it when task
  `<taskId>` exists and dropping the screen when it doesn't.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end:
  a new user signs up and ends verified, with a password and the typed name stored; an existing user resets the password: pass.
