# Sign up or in, then fill in the missing profile

Email OTP sign-up or sign-in; after login the flow checks the user's profile and asks only for what is missing, one
screen per item: a verified phone (by SMS code), then a name. Users with a complete profile go straight to the session.
From the console template `sign-up-or-in-with-progressive-profiling`, with three template bugs fixed (see
Pitfalls).

## When to use

"Progressive profiling", "ask for missing details after login", "collect phone/name only if we don't have them",
"onboarding fields for existing users". The pattern (condition on a `user.*` field, a screen, an update action, back
to the next check) is the point; the OTP email login in front can be swapped for any other first factor.

## Flow

```
1 Welcome (email) --> 2 send OTP --> 3 Verify Email OTP --> 4 verify --> 15 profile complete? --yes--> 0 JWT
                                                                          \--no--> 5 phone verified? --yes--> 10 has name? --yes--> 0 JWT
                                                                                     \--no--> 6 Get Phone --> 12 send SMS code --> 8 Verify Phone OTP --> 9 verify --> 10
                                                                                                                         10 --no--> 11 Get Name --> 13 update user --> 0 JWT
```

| Task | Type, action | What to know |
|---|---|---|
| `1`-`4` | screen, `sign-up-or-in-otp-email`, screen, `verify-code-otp-email` | Email OTP login. Codes auto-submit (`oneTimeCodeId`). |
| `15` | condition | One condition with two atomic conditions (AND): `user.verifiedPhone` is-true and `user.name` not-empty. A shortcut past the per-item checks. |
| `5` | condition | `user.verifiedPhone` is-true -> skip the phone step. |
| `6`, `12` | screen, `update-user-otp-sms` | `PhoneInput` (`phone`); `update-user-otp-sms` texts a code to it and, once verified, sets the user's phone. |
| `8`, `9` | screen, `verify-code-otp-sms` | Verifies the SMS code; then continues to the name check. |
| `10` | condition | `user.name` (the display name) not-empty -> done. |
| `11`, `13` | screen, `update-user-properties` | `FullNameInput` (`fullName`); `userPropertiesDefinitions` maps `form.fullName` to `displayName`. |
| `0` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Another missing field** (e.g. company): add a condition task (`not-empty` on `user.customAttributes.company`), a
  screen with an input named `form.company` (a custom input; a bare `company` is never readable as `form.company`),
  and an `update-user-properties` task mapping
  `{"key": "customAttributes.company", "type": "context", "value": "form.company"}`; chain it like `10` -> `11` ->
  `13`, and add the field to `15`'s atomic conditions. The custom attribute must exist in the project.
- **Given and family name instead of a display name**: on task `11`'s screen use inputs named `givenName` and
  `familyName`, check `user.givenName` in `10` and `15`, and map both keys in `13`.
- **No phone step**: point `15`'s ELSE and `9`'s success at `10`, remove `user.verifiedPhone` from `15`, delete `5`,
  `6`, `8`, `9`, `12` and the screens of `6` and `8`.
- **Ask only new users**: put a condition on `authInfo.firstSeen` after `4` and send existing users to `0`.

## Pitfalls

- Map from the input's actual `props.name`. The template's Get Name screen has `fullName` but mapped
  `form.displayName`, which is always empty, so names were never saved; this recipe maps `form.fullName`.
- Check the stored profile (`user.*`), not the form (`form.*`), in conditions that run before the screen: the template's
  `15` checked `form.displayName`, which is empty for every returning user.
- Every input component needs `custom: {"type": "input"}` to count as an input (`inputKeys`); the template's
  `PhoneInput` had `custom: {}`, fixed here.
- Phone verification texts a real phone on a real project (an SMS connector or Descope's default sender must be
  available); the local e2e runner cannot complete it.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end (a test project that captures
  SMS): a new user gives a phone (verified by SMS code) and a name, both stored; an existing user with a name gives
  only the phone: pass.
