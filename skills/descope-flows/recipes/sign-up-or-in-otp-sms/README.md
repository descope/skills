# Sign up or in with an SMS code

Phone-first login: the user enters a phone number, gets a one-time code by SMS, and is signed in; a new user is
created on the way and asked for a name. The console template `otp-template-sign-up-or-in` (SMS already),
with an explicit mapping for the name.

## When to use

"Login with phone number", "SMS OTP", "text me a code", "passwordless by phone", consumer apps where users are known
by phone. For email codes see [sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md); for an
SMS code as a second factor after another login, see
[sign-up-or-in-otp-email-adaptive-mfa](../sign-up-or-in-otp-email-adaptive-mfa/README.md) and
[sign-up-or-in-progressive-profiling](../sign-up-or-in-progressive-profiling/README.md) (adding a phone).

## Flow

```
1 Welcome (phone) --> 9 send SMS code --> 10 Verify OTP --> 11 verify --> 5 new user? --yes--> 7 User Information --> 8 update user --> 6 End
                          ^                 |   \--Use a different number--> 1                \--no------------------------------> 6
                          \----resend-------/
```

| Task | Type, action | What to know |
|---|---|---|
| `1` | screen | `Phone` input `Yp9Ow4uOia` (`name: phone`, country code auto-detected, `custom.type: input`). Continue `cUBPvY4IoT` -> `9`. |
| `9` | `sign-up-or-in-otp-sms` | Sends the code to the phone typed on `1`; a new phone becomes a new user at `11`. |
| `10` | screen | `CodeInput` `L1T9iO4p5U` auto-submits -> `11`; "Send again" `resend` -> `9`; "Use a different number" `pnOqEGpL1b` -> `1`. Shows `{{sentTo.maskedPhone}}`. |
| `11` | `verify-code-otp-sms` | Checks the code; the phone becomes a verified login id. |
| `5` | condition | `authInfo.firstSeen` is-true: the user was just created. |
| `7`, `8` | screen, `update-user-properties` | `FullNameInput` `fullName`; `userPropertiesDefinitions` maps `displayName` from `form.fullName`. |
| `6` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Email or phone in one field**: see the content template `email-or-phone-template-sign-up-or-in`.
- **WhatsApp or voice instead of SMS**: the matching `sign-up-or-in-otp-*` / `verify-code-otp-*` pair, if the
  project has that messaging connector.
- **More profile fields**: add inputs to `7` and one `userPropertiesDefinitions` row per field on `8`.

## Pitfalls

- SMS costs money and is a fraud target (SMS pumping): add bot protection before `9`, as
  [sign-up-or-in-otp-email-recaptcha](../sign-up-or-in-otp-email-recaptcha/README.md) does before the email code.
  Free and limited plans hit an SMS quota (`E062121`).
- Keep `custom.type: input` on the phone node: the console derives the screen's input keys from it.
- Without `userPropertiesDefinitions`, `update-user-properties` falls back to an old path that sets only the display
  name; list every field explicitly.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: a new user signs up
  by SMS code (captured by the test project) and gives a name; stored with a verified phone and the name: pass.
  Sign-in of an existing phone user: not run (the runner's existing users have no phone).
