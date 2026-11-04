# Email OTP, then TOTP as a second factor

Two-factor login: a one-time code by email first, then a code from an authenticator app (TOTP: Google
Authenticator, 1Password, Authy...). Users who already have TOTP enter a code; everyone else (new users included)
connects an app by scanning a QR code and confirms with a first code. Built from
[sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) without Google; the TOTP tasks and the
QR screen come from the console template `add-totp-mfa-with-recovery-codes`.

## When to use

"MFA", "2FA", "authenticator app", "TOTP", "require a second factor". For a second factor by SMS instead, swap the
TOTP tasks for `sign-in-otp-sms` / `verify-code-otp-sms` (the user needs a verified phone; see
[sign-up-or-in-progressive-profiling](../sign-up-or-in-progressive-profiling/README.md) for collecting one). For
MFA only when risk is high, put a condition on `riskInfo.riskScore` before `22` (console templates `adaptive-mfa-*`).

## Flow

```
0 Welcome (email) --> 19 send OTP --> 20 Verify OTP --> 21 verify --> 4 new user? --yes--> 12 User Information --> 7 update user --> 22
                                                                       \--no-------------------------------------------------> 22
22 Has TOTP? --yes--> 23 Verify TOTP --> 24 verify-totp-code -----------------------------------> 8 End (JWT)
             \--no--> 25 update-user-totp --> 26 Connect an authenticator app (QR) --> 27 verify-totp-code --> 8
```

| Task | Type, action | What to know |
|---|---|---|
| `0`-`21`, `4`, `12`, `7` | | The OTP email login of the base recipe. |
| `22` | condition | `user.totp` is-true: the user has a TOTP secret. |
| `23`, `24` | screen, `verify-totp-code` | `Code` input `oneTimeCodeId` (`name: code`, auto-submits). |
| `25` | `update-user-totp` | Creates a new TOTP secret for the signed-in user and puts its QR image and key in context for the next screen. |
| `26` | screen | `TOTPImage` `UV4gtH3-wl` shows the QR code; the user scans it and types the first code. |
| `27` | `verify-totp-code` | Confirms that the app produces valid codes before the session is issued. |
| `8` | `logged-in` | Issues the session after both factors. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Recovery codes**: after `27`, add `recovery-codes-generate` and a screen with a `RecoveryCodesList` (the template
  `add-totp-mfa-with-recovery-codes`, tasks `6`-`8`), and a sign-in path that accepts a recovery code (template
  `sign-in-with-totp-or-recovery-codes`).
- **Optional enrollment**: add a screen before `25` with "Set up now" (-> `25`) and "Not now" (-> `8`) buttons, as the
  passkey offer in [sign-up-or-in-passkeys-otp-email](../sign-up-or-in-passkeys-otp-email/README.md).
- **Show the key as text too** (users who can't scan): add a `TOTPLink` component to task `26`'s screen.
- **Another first factor**: keep `22`-`27` and point the other method's success at `22`.

## Pitfalls

- `update-user-totp` replaces the user's TOTP secret: never route a user who already has TOTP (`user.totp` true)
  to `25`, or their existing authenticator stops working.
- `verify-totp-code` needs a signed-in or identified user: put it after the first factor, as here.
- The session is issued only at `8`; don't add a `logged-in` between the factors.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: a new user signs up and
  enrolls TOTP (stored TOTP true); a user with TOTP signs in with an email code and a TOTP code: pass.
