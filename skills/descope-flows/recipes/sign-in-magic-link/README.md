# Sign in with a magic link (existing users only)

Passwordless sign-in by email magic link for users who already have an account; nobody signs up here. An email with
no account sees the same "If an account exists, we've sent a sign-in link" screen as a known one, so the flow never
tells which emails are registered. From the console template `magiclink-template-sign-in`, plus the unknown-user path.

## When to use

"Magic link sign-in", "only existing / invited users can log in", "no self sign-up". If new users should be created
on their first link, start from [sign-up-or-in-magic-link](../sign-up-or-in-magic-link/README.md) instead.

## Flow

```
0 Sign In (email) --Sign In--> 4 send magic link --success--> 5 Magic Link Sent --polling--> 6 Verified Successfully
                                  |                              \--resend--> 4
                                  |--success--> 4.end verify --> 3 JWT
                                  \--UserDoesNotExists (nothing sent)--> 5
```

| Task | Type, action | What to know |
|---|---|---|
| `0` | screen | `EmailInput` (`email`), Sign In button `pOrs7z2-ym`. |
| `4` | `sign-in-magic-linkv3-email` | Fails with `UserDoesNotExists` before sending anything when no user has that email. `errorHandlingV2.UserDoesNotExists: custom` plus the next rule `UserDoesNotExists` -> `5` send it to the same waiting screen; other errors (rate limit, disabled tenant) stay on screen `0` (automatic). Two `success` rules, as in every magic link flow: the waiting screen and `4.end`. |
| `4.end` | `verify-magic-link` | Runs in the tab opened from the email link; the session is issued there by `3`. |
| `5`, `6` | screens | The original tab waits on `5` (`polling`), then shows `6`; `polling-error` (link expired) goes back to `0`. `5`'s text doesn't show `{{sentTo.maskedEmail}}`: it is empty when nothing was sent. |
| `3` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Redirect URL**: set `tasks.4.arguments.uri.value` to the app page that hosts the flow, unless the project has a
  magic link redirect URL or the app passes `redirectUrl` at flow start (otherwise `MagicLinkMisconfiguration` at
  runtime).
- **Explicit "No account found" message** (only if the user asks for it: it tells anyone which emails are
  registered, so say so in the report): set `errorHandlingV2.UserDoesNotExists` to `{"errorHandlingType":
  "customWithError", "errorMessage": "No account for this email"}` and point the `UserDoesNotExists` rule back to
  `0`, or to a new screen with the message and a button back to `0`.
- **Let unknown users sign up instead**: switch to the sign-up-or-in recipe.

## Pitfalls

- Keep `5` neutral: showing the masked address, or a different screen for unknown emails, tells the two cases apart.
- The rule's `interactionId` must be the exact error type, `UserDoesNotExists`; any other name never fires.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: an existing user signs in through the link;
  an email with no account reaches the same waiting screen `5`: pass.
