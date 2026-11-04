# Separate sign-in and sign-up with email OTP

A sign-in screen and a "Create an account" screen, both with an email code. Sign-in never creates an account;
sign-up asks the name first and never makes a second account for an email that has one. Both paths test the email
before sending and share one neutral code screen, so neither tells a visitor whether an email is registered. Built
on [sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) (its task ids kept) without Google.

## When to use

"Separate sign-up and sign-in", "a sign-up page and a login page", "don't create accounts from the login screen",
"collect the name before the account is created". For one screen that signs up or in, use
sign-up-or-in-otp-email-google.

## Flow

```
0 Sign in (email) --Continue--> 40 has an account? --yes--> 19 sign-in code --> 20 Code --> 21 verify --> 4 new user?
   |                                               \--no--> 20 (nothing sent)                              |--yes--> 7 name --> 8 End
   \--Create an account--> 41 Create Account (email, name) --> 42 has an account? --yes--> 19        \--no--> 8 End
                                                                                 \--no--> 43 sign-up code --> 20
20 --resend--> 46 came from sign-up? --yes--> 42;  --no--> 40
```

| Task | Type, action | What to know |
|---|---|---|
| `0` | screen | Email + Continue `S-VOZ5i7gc` -> `40`; "Create an account" `0UO1vj84P4` (link button) -> `41`. |
| `40`, `42` | conditions | `unauthUser.loginIds` not-empty: the email has an account. |
| `19` | `sign-in-otp-email` | Sends a code to an existing account only. On the sign-up path an existing email lands here too: it gets a sign-in code, not a second account and not an "already registered" message. |
| `43` | `sign-up-otp-email` | New email only. The account is created when `21` verifies the code. |
| `20` | screen | Shared by every path. Its text doesn't show `{{sentTo.maskedEmail}}` (empty when nothing was sent). An unknown email on the sign-in path reaches it with no code sent, so any code fails like a wrong one. |
| `46` | condition | Resend goes back through the path's own check: `form.fullName` is set only by `41`. |
| `41` | screen | Email, `FullNameInput` `fullName` (required), Continue -> `42`, "Already have an account? Sign in" `vsAjgHHuS-` -> `0`. |
| `4`, `7` | condition, `update-user-properties` | A new account gets `displayName` from `form.fullName`; existing users go straight to `8`. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Explicit messages** ("No account for this email", "This email is already registered"): only if the user asks;
  they tell anyone which emails are registered. Then route `40`'s else and `42`'s yes to a message screen.
- **Social login**: OAuth signs up and in at once (`exchange-oauth-code` creates the user), so it has no separate
  paths. Put the social button on `41` only if social sign-up is wanted, and say that it also signs existing users in.
- **More sign-up fields**: add inputs to `41` and rows to `7` (custom inputs named `form.<key>`).
- **Legal links**: `0` and `41` keep the `REPLACE_WITH_TERMS_URL` / `REPLACE_WITH_PRIVACY_URL` placeholders.

## Pitfalls

- Don't route `40`'s else to `43`: that signs up from the sign-in screen.
- Keep one code screen for every path: two screens (one for new, one for existing emails) tell the visitor which
  case they are in by the screen id alone.
- If a visitor goes to `41`, types a name, then goes back to `0`, `form.fullName` stays set and a resend on `20`
  takes the sign-up check (`42`). For an email with an account that is the same `19`; for an unknown email it sends
  a sign-up code.

## Checked

- `scripts/validate_flow.py`: ok, no errors or warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: an existing user signs in on the
  sign-in path (`sign-in-otp-email`); a new email signs up through `41` (`sign-up-otp-email`): pass.
- Not run: an unknown email on the sign-in path, an existing email on the sign-up path, resend through `46` (the
  runner picks buttons by route and can't force these). `unauthUser.loginIds` before a send was checked in
  sign-up-or-in-otp-email-age-check.
