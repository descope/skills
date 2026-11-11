# Magic link, then a required passkey

Users sign up or in with a magic link, then must pass a passkey as the second factor: a user who has a passkey
confirms with it, a user without one adds one before the session is issued. A user who already has a passkey can't
get a session on the link alone; a user without one is enrolled on the strength of the link (trust on first use: see
Adapt). A device that can't create a passkey ends on a "passkey required" screen. Built on
[sign-up-or-in-magic-link](../sign-up-or-in-magic-link/README.md) (its task ids kept), with the passkey sign-in from
the console template `biometrics-magiclink-template-step-up` and the passkey screens of
[sign-up-or-in-passkeys-otp-email](../sign-up-or-in-passkeys-otp-email/README.md).

## When to use

"Magic link plus passkey", "passkey as 2FA / MFA", "require a passkey after the email link", "mandatory passkey
enrollment". For a passkey that is offered but optional, use
[sign-up-or-in-passkeys-otp-email](../sign-up-or-in-passkeys-otp-email/README.md) (it has "Not now"); for a passkey
*or* a magic link as alternatives, the content template `biometrics-magiclink-template-sign-up-or-in`.

## Flow

```
0 Welcome (email) --> 7 send link --> 8 Magic Link Sent --polling--> 9 Verified Successfully (first tab)
                      7.end verify (the link's tab) --> 3 new user? --yes--> 4 User Information --> 5 update --> 10
                                                                     \--no--> 10
10 has a passkey? --yes--> 11 Confirm with Passkey --> 13 passkey sign-in --> 13.end --> 6 End
                 \--no--> 12 device supports passkeys? --yes--> 14 Add Passkey --> 15 add passkey --> 15.end --> 6
                                                       \--no--> 16 Passkey Required (no next, no session)
```

| Task | Type, action | What to know |
|---|---|---|
| `0`-`9` | as in sign-up-or-in-magic-link | Unchanged, except that `3` (existing user) and `5` go to `10` instead of `6`. Everything after `7.end` runs in the link's tab. |
| `10` | condition | `user.webauthn` is-true: the signed-in user already has a passkey. |
| `11` | screen | `PasskeyButton` `Q86IXDdAAn` (auto-submits, so the browser prompt opens at once) -> `13`. No "send me a code" or "skip": the passkey is the second factor. Its `ErrorMessage` shows a cancelled or failed ceremony; the user can retry. |
| `13` / `13.end` | `webauthn-sign-in-start-v2` / `webauthn-sign-in-finish` | The passkey sign-in. It reads the login id from the typed `email` (the address the link went to), so the browser is only offered that user's passkeys. The session always goes to the owner of the passkey used (`13.end` replaces the signed-in user), never to the link user unless it is theirs. Only `13` takes `finishStepId`. |
| `12` | condition | `device.webAuthnSupport` is-true -> `14`; else `16`. |
| `14` | screen | "Add a passkey" `6Cy2f8gQ_7` -> `15`. No "Not now". |
| `15` / `15.end` | `webauthn-update-user-start` / `-finish` | Adds a passkey to the user signed in by the link. |
| `16` | screen | Fail closed: a message, no button, no next. The user opens the link on another device. |
| `6` | `logged-in` | Issues the session, only after `13.end` or `15.end`. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Existing users without a passkey** (ask the user): `10` else -> `12` -> `14` lets whoever holds the link enroll a
  passkey on that account and sign in, which covers every existing user on the day the flow goes live. Ask whether
  email-only first enrollment is acceptable, or whether enrollment needs another factor (a code to a verified phone,
  an existing session) before `14`.
- **Account recovery**: a user who loses every passkey device can't sign in (the link alone is never enough). Ask
  the user what recovery they want (support resets passkeys with the management API, or a second recovery factor);
  don't add a fallback that skips the passkey without asking.
- **Social login as the first factor** too: give `11`'s path a login id first. After OAuth there is no typed
  `email`, and `webauthn-sign-in-start-v2` with no login id accepts any account's passkey (see Pitfalls).
- **Users on devices without passkeys**: `16` can offer a roaming security key or a phone (cross-device) only if the
  project allows them; change its text, don't route it to `6`.
- **Restrict authenticators**: `restrictPasskeyTypes` and `userVerificationDiscouraged` on `15` (empty = project
  defaults).
- **Collect more at sign-up**: as in sign-up-or-in-magic-link (task `4`, custom inputs named `form.<key>`).

## Pitfalls

- `13` takes its login id from `email`, which `0` set, so the browser offers the link user's passkeys; whoever
  finishes `13` with a passkey gets that passkey owner's session. Never put `13` after a step that leaves `email`
  empty (social login, a flow started for a signed-in user): with no login id the browser offers every passkey on
  the device, and the session goes to whichever account's passkey is used.
- Never route `16`, a cancelled ceremony on `11`/`14`, or an error of `13`/`15` to `6`: that is a session on the
  magic link alone.
- Passkeys are bound to the domain (RP ID) the flow runs on, and the ceremony runs in the link's tab: the link must
  open on the app's domain.
- Keep `N` and `N.end` paired: same name, `finishStepId` = `N.end` on the start task.

## Checked

- `scripts/validate_flow.py`: ok, no errors or warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: a new and an existing
  user, on the runner's device (no passkey support), go through the link and stop on `16` with no session: pass. A
  copy with `12`'s else routed to `6` fails the scenario, so it catches a fail-open gate.
- Not run: the passkey ceremonies `13` and `15` (the runner can't do WebAuthn). Read from the engine code, not run:
  `13`'s login id comes from `email` and limits which passkeys the browser offers; `13.end` replaces the signed-in
  user with the passkey's owner; an error on `13`/`15` returns to `11`/`14`, never to `6`.
