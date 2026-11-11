# Passkeys, with email OTP for everyone else

Users who have a passkey sign in with it (browser autofill on the email field, or a passkey button); everyone else
signs up or in with an email OTP and is then offered to add a passkey, on devices that support passkeys, with a "Not
now" to skip. From the console template `passkeys-otp-email`, with the offer made optional and gated on
device support.

## When to use

"Passkeys", "WebAuthn", "biometric login", "passwordless with passkeys and a fallback", "add a passkey after login".
In production the common shape is exactly this: passkey sign-in for returning users plus adding a passkey after
another login (webauthn-update-user-*), with a check on device passkey support (`device.webAuthnSupport`; `deviceInfo.webAuthnSupport` is its deprecated alias).

## Flow

```
1 Welcome (email) --passkey autofill (C_nrfXQJJp)--> 2 passkey sign-up-or-in --> 2.end --> 0 End
   \--Next--> 3 user has a passkey? --yes--> 11 Sign In with Passkey --passkey button--> 2
                                     |                               \--Send me a code--> 12 sign-in OTP --> 13 Verify OTP --> 14 verify --> 0
                                     \--no--> 5 sign-up-or-in OTP --> 6 Verify OTP --> 7 verify --> 15 device supports passkeys? --no--> 0
                                                                                                     \--yes--> 9 Add Passkeys --Add--> 10 add passkey --> 10.end --> 0
                                                                                                                              \--Not now--> 0
```

| Task | Type, action | What to know |
|---|---|---|
| `1` | screen | `EmailInput` `C_nrfXQJJp` with `autoComplete: "webauthn"`: the browser offers saved passkeys in the field, and picking one submits it (interaction id = the input's id, icon `passkey`). Next `6Cy2f8gQ_7` continues with the typed email. |
| `3` | condition | One condition, two atomic conditions (AND): `unauthUser.loginIds` not-empty and `unauthUser.webauthn` is-true: the email belongs to a user who has a passkey. |
| `2` / `2.end` | `webauthn-sign-up-or-in-start` / `-finish` | Two-step passkey ceremony; `finishStepId` names `2.end` on both. |
| `11` | screen | `PasskeyButton` `Q86IXDdAAn` -> `2`; "Send me One Time Password" `6IU4qIgA7r` -> email OTP sign-in (`12`-`14`) for a user away from their passkey device. |
| `5`-`7` | `sign-up-or-in-otp-email`, screen, `verify-code-otp-email` | New users and users without a passkey. Codes auto-submit (`oneTimeCodeId`). |
| `15` | condition | `device.webAuthnSupport` is-true -> offer; else straight to `0`. |
| `9` | screen | "Add a passkey" `6Cy2f8gQ_7` -> `10`; "Not now" `Hn4sW8vQ2c` -> `0`. |
| `10` / `10.end` | `webauthn-update-user-start` / `-finish` | Adds a passkey to the now signed-in user. |
| `0` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Offer the passkey only once**: before `15`, add a condition on a custom attribute (e.g.
  `user.customAttributes.passkeyOffered` is-true -> `0`), and set it with `update-user-properties`
  (`{"key": "customAttributes.passkeyOffered", "type": "boolean", "value": true}`) on the "Not now" path. The
  attribute must exist in the project.
- **Passkey-first without the email autofill**: remove `autoComplete: "webauthn"` from `C_nrfXQJJp` and the
  `C_nrfXQJJp` rule of `1`, and its entry in the screen's `interactions`.
- **Add passkeys from inside the app** (a settings page, not at login): see the template
  `biometrics-template-add-passkeys` pattern: `loadUser` first, then `15` -> `9` -> `10`; the app starts that flow
  for a signed-in user.
- **Restrict authenticators**: `restrictPasskeyTypes` and `userVerificationDiscouraged` on `2` and `10` (empty =
  project defaults).

## Pitfalls

- Passkeys are bound to the domain (RP ID) the flow runs on; a flow tested on one domain won't find passkeys created on
  another. Configure the domain in the project's passkey settings.
- Keep `N` and `N.end` paired: same name, same arguments, `finishStepId` = `N.end`.
- The template auto-submitted the enrollment screen's only button, so users could not decline; this recipe asks.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: the OTP path for a new and an existing
  user (no passkey; the runner's device reports no passkey support, so `15` goes to `0`): pass. Passkey ceremonies:
  not run (the runner can't do WebAuthn).
