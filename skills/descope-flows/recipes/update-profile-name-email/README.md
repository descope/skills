# Update profile: name and email

A flow for a user who is already signed in: they change their display name, or change their email after entering
a code sent to the new address. The app runs it from an account or settings page. Built from the console's own
user-profile widget flows `user-profile-set-name` and `user-profile-set-email`, joined with a "Change email"
button.

## When to use

"Edit profile", "account settings", "change my name / email", "update user details after login". Like step-up,
this is a separate flow the app starts for a signed-in user, not part of the login flow. For collecting missing
fields during login, use [sign-up-or-in-progressive-profiling](../sign-up-or-in-progressive-profiling/README.md);
for a ready-made settings UI, Descope's user profile widget runs flows of this kind.

## Flow

```
start --> 13 Load User --> 1 Edit profile (name) --Save--> 12 update user --> 11 Updated Successfully --Close--> 0 End
                             |   \--Close-----------------------------------------------------------------> 0
                             \--Change email--> 14 Change email --Save--> 15 send code to the new email --> 16 Verify OTP --> 17 verify --> 18 Verified Successfully --Close--> 0
                                                  \--Close--> 0                                              \--Close--> 0
```

| Task | Type, action | What to know |
|---|---|---|
| `13` | `loadUser` | Loads the signed-in user from the refresh token the app sends (the SDKs do). Without a session the flow fails here. |
| `1` | screen | `FullNameInput` `IBnA1ULfrs` (`fullName`); Save `q4FeBI9x5i` -> `12`, Change email `Ce8mJ2rLqT` -> `14`, Close `5Wgl023sDr` -> `0`. |
| `12` | `update-user-properties` | `userPropertiesDefinitions`: `displayName` from `form.fullName`. |
| `14` | screen | `EmailInput` (`email`): the new address. Save -> `15`. |
| `15` | `update-user-otp-email` | Sends a code to the new address; the user's email changes only after `17`. `addToLoginIDs` and `onMergeUseExisting` (empty here; going by their names) set whether the new email also becomes a login id and what happens if another user has it. |
| `16`, `17` | screen, `verify-code-otp-email` | `CodeInput` auto-submits; "Send again" `resend` -> `15`. |
| `0` | `logged-in` | Ends the flow. No sign-in happened, so it does not issue a new session JWT here (see Pitfalls). |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **More fields**: add inputs to `1` and one `userPropertiesDefinitions` row each on `12` (e.g. `givenName`,
  `customAttributes.<attr>`; a custom attribute must exist in the project).
- **Change phone**: the same pattern as `14`-`18` with a `Phone` input, `update-user-otp-sms` and
  `verify-code-otp-sms` (console widget flow `user-profile-set-phone`).
- **New email as login id**: set `addToLoginIDs` on `15` to `true`, so the user can sign in with the new address.

## Pitfalls

- The JWT the app holds keeps the old name and email: `logged-in` re-issues the session only when the flow changed
  something that needs it (custom claims, a tenant selection, a session cookie, a forced reload), not after these
  updates (read from the engine source). Have the app refresh the
  session, or reload the user from the management API, after the flow ends.
- Keep `13` first: every task after it acts on the loaded user; started without a session, the flow has no user.
- `update-user-properties` reads form values by the input's `name` (`form.fullName` here); rename the input and the
  mapping together.

## Checked

- `scripts/validate_flow.py` and `scripts/flow_style.py` (this skill's checkers): ok, no errors, warnings or style
  notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end:
  passes 2/2. A signed-in user changes the name (stored name checked), and a signed-in user changes the email
  after a code sent to the new address (stored email checked). The flow ends without a new session JWT when only
  the name changes, which the scenario allows (`expect.session: false`).
