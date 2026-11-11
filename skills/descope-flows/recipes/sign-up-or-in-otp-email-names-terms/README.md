# Email OTP or Google, with first and last name and a required terms checkbox

Users sign up or in with an email code or Google. New users then give their first and last name and must tick "I
agree to the Terms of Service and Privacy Statement"; the flow checks the box again on the server before it saves
anything or issues a session. Built on
[sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) (its task ids kept): only its
User Information screen `12` and the step after it change.

## When to use

"First and last name at sign-up", "required terms / consent checkbox", "accept the terms of service before signing
up", any sign-up screen with a checkbox the user must tick. For a notice without a checkbox, the welcome screen's
"By continuing, I agree..." row (kept here too) is enough. The checkbox `form.termsAccepted` is the pattern for any
custom input: see "Custom inputs" below.

## Flow

```
0 Welcome --Continue--> 19 send code --> 20 Verify OTP --> 21 verify --\
          \--Google--> 3 OAuth --> 3.end -------------------------------> 4 new user? --no--> 8 End
                                                                          \--yes--> 12 User Information --> 22 terms accepted?
                                                                                      ^                       |--yes--> 7 update --> 8 End
                                                                                      \--Back-- 23 Terms Required <--no--/
```

| Task | Type, action | What to know |
|---|---|---|
| `0`-`4`, `19`-`21`, `8` | as in sign-up-or-in-otp-email-google | Unchanged. |
| `12` | screen | `FirstNameInput` `firstName` and `LastNameInput` `lastName` (both `required`), a `ContextBoolean` checkbox named `form.termsAccepted` (`required`), and the legal links row (`REPLACE_WITH_TERMS_URL`, `REPLACE_WITH_PRIVACY_URL`). `inputKeys` hold the names as written: `firstName`, `lastName`, `form.termsAccepted`. |
| `22` | condition | `form.termsAccepted` is-true -> `7`; else `23`. The checkbox's `required` is only enforced by the browser; this is the server-side check. |
| `23` | screen | "Please accept..." and Back -> `12`. Nothing saved, no session. |
| `7` | `update-user-properties` | `givenName` from `form.firstName`, `familyName` from `form.lastName`. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Custom inputs

Built-in inputs (`email`, `firstName`, `lastName`, `fullName`, `phone`, ...) keep their bare `name` and are read as
`form.<name>` (`form.firstName`). Any other input must be *named* `form.<key>` and is read as `form.<key>`: the
checkbox here is `name: "form.termsAccepted"`, read by `22` as `form.termsAccepted`. A checkbox named
`termsAccepted` would be unreadable both as `termsAccepted` and as `form.termsAccepted`, so `22` would always say
"not accepted".

## Adapt

- **Legal URLs** (required): ask the user for both, then set `href` on `ecYaE1yoII`/`pxkTtHb8KF` (screen `0`) and
  `HNqBjDNmUq`/`ZjwiLGgci0` (screen `12`). Never invent `/terms` or `/privacy`.
- **Record the acceptance**: add a row to `7`, e.g. `{"key": "customAttributes.termsAccepted", "type": "context",
  "value": "form.termsAccepted"}`. The custom attribute (boolean) must exist in the project; ask the user before
  adding it.
- **Display name too**: `update-user-properties` maps values, it can't join two inputs; add a `FullNameInput`
  (`fullName` -> `displayName`) or leave the display name to the app.
- **Optional names**: set `required: false` on `19OiRszfMK`/`RvnAvFT-Xs` (what an empty input writes to the user is not checked).
- **Email OTP only**: remove Google as in sign-up-or-in-otp-email-google's Adapt.
- **Existing users must accept new terms**: they skip `12` today (`4` sends them to `8`). Add a condition on a stored
  attribute (the "Record the acceptance" row) before `8`; that is a separate decision for the user.

## Pitfalls

- Never route `23` or the else of `22` to `7` or `8`: that signs up a user who didn't accept.
- Keep `22` even though the checkbox is `required`: a request built outside the browser skips that check.

## Checked

- `scripts/validate_flow.py`: ok, no errors or warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: a new user who ticks the box
  signs up with `givenName`/`familyName` stored; a new user whose request carries `form.termsAccepted: false` ends on
  `23`; an existing user signs in without `12`: pass. A copy without `22` (`12` -> `7`) fails the decline case.
- Not run: the Google path (same `4` -> `12` as the email path).
