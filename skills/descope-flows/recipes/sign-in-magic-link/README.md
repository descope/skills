# Sign in with a magic link (existing users only)

Passwordless sign-in by email magic link for users who already have an account; nobody signs up here. An email with
no account gets an explicit "No account found" screen with a way back. From the console template
`magiclink-template-sign-in`, plus the unknown-user path.

## When to use

"Magic link sign-in", "only existing / invited users can log in", "no self sign-up". If new users should be created
on their first link, start from [sign-up-or-in-magic-link](../sign-up-or-in-magic-link/README.md) instead.

## Flow

```
0 Sign In (email) --Sign In--> 4 send magic link --success--> 5 Magic Link Sent --polling--> 6 Verified Successfully
                                  |                              \--resend--> 4
                                  |--success--> 4.end verify --> 3 JWT
                                  \--UserDoesNotExists--> 7 No account --Use a different email--> 0
```

| Task | Type, action | What to know |
|---|---|---|
| `0` | screen | `EmailInput` (`email`), Sign In button `pOrs7z2-ym`. |
| `4` | `sign-in-magic-linkv3-email` | Fails with `UserDoesNotExists` before sending anything when no user has that email. `errorHandlingV2.UserDoesNotExists: custom` plus the next rule `UserDoesNotExists` -> `7` give it its own path; other errors (rate limit, disabled tenant) stay on screen `0` (automatic). Two `success` rules, as in every magic link flow: the waiting screen and `4.end`. |
| `4.end` | `verify-magic-link` | Runs in the tab opened from the email link; the session is issued there by `3`. |
| `5`, `6` | screens | The original tab waits on `5` (`polling`), then shows `6`; `polling-error` (link expired) goes back to `0`. |
| `7` | screen | Title, explanation, and the button `Yb4tF9gJzE` back to `0`. |
| `3` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Redirect URL**: set `tasks.4.arguments.uri.value` to the app page that hosts the flow, unless the project has a
  magic link redirect URL or the app passes `redirectUrl` at flow start (otherwise `MagicLinkMisconfiguration` at
  runtime).
- **Message text**: edit `props.children` of the two `Text` nodes in task `7`'s screen (`Kq3vN8sLpT`, `Wm7cR2xHdB`),
  e.g. point to a sign-up page or a contact address.
- **Same message on the sign-in screen instead of a new screen**: drop task `7` and its screen, and set
  `errorHandlingV2.UserDoesNotExists` to `{"errorHandlingType": "customWithError", "errorMessage": "No account for
  this email"}` with the `UserDoesNotExists` rule going back to `0`.
- **Let unknown users sign up instead**: switch to the sign-up-or-in recipe.

## Pitfalls

- Saying "no account for this email" tells anyone which emails have accounts (user enumeration). When that matters,
  replace the text with a neutral one ("If an account exists, we sent a link") and point the rule at `5` instead.
- The rule's `interactionId` must be the exact error type, `UserDoesNotExists`; any other name never fires.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: an existing user signs in through the link;
  an email with no account ends on the "No account" screen with nothing sent and no user created: pass.
