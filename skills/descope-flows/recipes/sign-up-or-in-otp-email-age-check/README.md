# Email OTP with an age check before sign-up

Users sign up or in with an email code. An email that has no account is first asked for a date of birth; a scriptlet
computes the age, and a visitor under 18 stops before any code is sent, so no account is created. Existing users sign
in as before. Built on [sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) (its task ids
kept) without Google: social login creates the account before any screen could ask the age.

## When to use

"Age check", "minimum age", "date of birth at sign-up", "block minors", any sign-up that reads a `DateInput`. It is
also the reference for reading a date in a scriptlet and for custom inputs (`form.<key>`).

## Flow

```
0 Welcome (email) --> 30 has an account? --yes--> 19 send code --> 20 Verify OTP --> 21 verify --> 4 new user? ...
                                          \--no--> 31 Date of Birth --> 32 scriptlet (age) --> 33 old enough? --yes--> 19
                                                                          \--ScriptletFailed--> 35   \--no--> 34 Not Eligible
4 new user? --yes--> 12 User Information --> 7 update --> 8 End;   --no--> 8 End
```

| Task | Type, action | What to know |
|---|---|---|
| `30` | condition | `unauthUser.loginIds` not-empty: the typed email already has an account -> `19` (no age question). Else `31`. |
| `31` | screen | `DateInput` named `form.dateOfBirth` (`required`, `utc-time: true`, `format: "MM/DD/YYYY"`). |
| `32` | `scriptlet` | `scriptArgs` `dob` from `form.dateOfBirth`; returns `{eligible, valid, age}` at `scripts.age.*`. Anything but an epoch-ms number is not eligible. `ScriptletFailed` -> `35`. |
| `33` | condition | `scripts.age.eligible` is-true -> `19`; else `34`. |
| `34`, `35` | screens | Not eligible / check failed, with Back -> `0`. No code sent, no account, no session. |
| `19`-`21`, `4`, `12`, `7`, `8` | as in sign-up-or-in-otp-email-google | Unchanged. The account is created when `21` verifies the code. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Dates

- `DateInput` submits a number: epoch milliseconds of the chosen day, `""` when empty or invalid. Never a
  `YYYY-MM-DD` string; a scriptlet that matches a date pattern never succeeds.
- Without `utc-time`, the number is local midnight in the user's browser, and the day read back on the server can be
  off by one. With `utc-time: true` it is UTC midnight: read it with `getUTCFullYear()`, `getUTCMonth()` and
  `getUTCDate()`, as `32` does.
- A custom input is named `form.<key>` on the screen and read as `form.<key>`: here `form.dateOfBirth`. Named
  `dateOfBirth`, it would be empty to `32`, and every visitor would be "not eligible".

## Adapt

- **Another minimum age**: `MIN_AGE` in `32`'s `scriptCode`, and the text of `34`.
- **Store the date of birth**: add a row to `7`, e.g. `{"key": "customAttributes.dateOfBirth", "type": "context",
  "value": "form.dateOfBirth"}`. The attribute must exist in the project; what unit a date attribute expects from a
  flow (milliseconds or seconds) is not checked: ask, or store `scripts.age.age` in a number attribute instead.
- **Existing users without a date of birth**: `30` lets every existing account in. Asking them too is a separate
  decision for the user.
- **Social login**: OAuth signs the user up before any screen, so an age gate there means deleting the new
  under-age account afterwards (`delete-user`). Ask before building that.
- **Message for minors**: `34` says why. A generic "We can't create an account" hides the reason; ask the user which
  they want.

## Pitfalls

- Never route `34`, `35` or `33`'s else to `19`: that sends a code and creates the account.
- Ask the age before `19`: `sign-up-or-in-otp-email` creates the user when the code is verified, so a check after
  `21` leaves an under-age account behind.
- The date is typed by the visitor; this is an age declaration, not age verification.

## Checked

- `scripts/validate_flow.py`: ok, no errors or warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: a new adult
  (`form.dateOfBirth` 1990-01-01 UTC in epoch ms) signs up; a new minor (2020-01-01) ends on `34`; an existing user
  signs in without `31`: pass. So `unauthUser.loginIds` is empty for a new email and set for an existing one at `30`
  (the existing case would otherwise have reached `31` and failed the age check).
- Not run: `35` (scriptlet failure), the local-midnight variant without `utc-time`.
