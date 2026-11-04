# Email OTP with adaptive (risk-based) MFA by SMS

Sign up or in with an email code; ask for a second factor only when the sign-in looks risky. After the email code,
users who have a verified phone get a device fingerprint risk score, and only a high score triggers an SMS code.
Users without a verified phone add one now, so they have a second factor next time. Built from
[sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) without Google. The risk task and
condition come from the console template `socials-otp-template-sign-up-or-in`, the SMS tasks and the
phone screen from `adaptive-mfa-with-multiple-risk-inputs`.

## When to use

"Adaptive MFA", "risk-based authentication", "MFA only when suspicious", "ask for a code from a new device". 14 of 32
large customers' projects run a risk check in a flow, most often `riskInfo.riskScore` greater-than a threshold. For MFA on every login, see
[sign-up-or-in-otp-email-totp-mfa](../sign-up-or-in-otp-email-totp-mfa/README.md). For bot checks, see
[sign-up-or-in-otp-email-recaptcha](../sign-up-or-in-otp-email-recaptcha/README.md).

## Flow

```
0 Welcome (email) --> 19 send OTP --> 20 Verify OTP --> 21 verify --> 4 new user? --yes--> 12 User Information --> 7 update user --> 22
                                                                       \--no-------------------------------------------------> 22
22 verified phone? --yes--> 23 Fingerprint / Assess --> 24 risk high? --yes--> 25 send SMS code --> 26 Verify SMS code --> 27 verify --> 8 End
                   |                                                   \--no-----------------------------------------------------------> 8
                   \--no--> 28 Add a phone --> 29 send SMS code to it --> 30 Verify phone --> 31 verify ---------------------------------> 8
```

| Task | Type, action | What to know |
|---|---|---|
| `0`-`21`, `4`, `12`, `7` | | The OTP email login of the base recipe. |
| `22` | condition | `user.verifiedPhone` is-true. |
| `23` | `risk` ("Fingerprint / Assess") | Scores the session from the browser's device fingerprint and fills `riskInfo` (`riskScore`, `trustedDevice`, `knownDevice`, `botDetected`, `vpnDetected`). Enterprise feature: fingerprinting must be on for the project; the SDK collects the fingerprint and the task takes it from context, so it has no arguments. It declares no error types. |
| `24` | condition | `riskInfo.riskScore` greater-than `0.5`: the `risk` action's own output (it writes `riskInfo` directly; there is no result path). Here high means risky, and a score that couldn't be calculated is `0.2`, so it counts as low. |
| `25`-`27` | `sign-in-otp-sms`, screen, `verify-code-otp-sms` | The second factor: a code to the user's verified phone (as in the content template's task `14`). |
| `28`-`31` | screen, `update-user-otp-sms`, screen, `verify-code-otp-sms` | `Phone` input `UGk5ydN5aD`; adds the phone to the signed-in user and verifies it. "Use a different number" `pnOqEGpL1b` on `30` -> `28`. |
| `8` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Threshold**: change the `0.5` predicate of `24`.
- **Other signals**: add atomic conditions or branches on `riskInfo.impossibleTravel`, `riskInfo.trustedDevice`,
  `riskInfo.vpnDetected` (the template `adaptive-mfa-with-multiple-risk-inputs` combines `trustedDevice` and
  `impossibleTravel`).
- **Remember the device**: after `27`, a screen asking "Trust this device?" and a `trust-device` task; then
  `riskInfo.trustedDevice` can skip the SMS next time (template `adaptive-mfa-trusted-device`).
- **TOTP instead of SMS**: send `24`'s high branch to the TOTP tasks of
  [sign-up-or-in-otp-email-totp-mfa](../sign-up-or-in-otp-email-totp-mfa/README.md) and drop `22` and `28`-`31`.
- **Block instead of challenge**: send the high branch to a screen with a message.

## Pitfalls

- Phone enrollment at `28` happens without a risk check: whoever holds the email can add their own phone. To close
  that, move the risk check before `22` and block high-risk users who have no phone yet.
- `riskInfo` is merged across every task that writes it, keeping the highest `riskScore`. In this flow the writers
  are the `risk` action and, if a screen has a honeypot field, the engine's honeypot check (a filled field sets
  `1.0` with `botDetected`); both score high = risky, so `riskScore > 0.5` means the same thing either way. Adding a
  reCAPTCHA Enterprise assess (high = human) breaks that: then condition on `riskInfo.botDetected` or on the
  connector's own result (`connectors.<resultPath>.riskScore`) instead, see
  [connectors](../../references/connectors.md).
- Without fingerprinting on the project, every score is `0.2` and nobody gets the SMS code. Check that a risky
  sign-in (new browser, VPN) really gets one before relying on it.
- SMS costs money and has quotas (`E062121` on limited plans).

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or warnings, no style notes.
- Engine behavior read from source: the `risk` action's definition, inputs and no declared errors;
  the not-calculated score `0.2`; the honeypot score `1.0` and how the scores are merged.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end: a new
  and an existing user sign in with an email code and add a verified phone: pass. The risk branch (`23`-`27`): not
  run (the runner's users have no phone and it can't make a fingerprint).
