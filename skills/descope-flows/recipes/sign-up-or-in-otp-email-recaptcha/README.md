# Email OTP with reCAPTCHA Enterprise bot protection

Sign up or in with an email code, with an invisible reCAPTCHA Enterprise check: the Welcome screen gets a token from
Google in the browser, the flow asks reCAPTCHA Enterprise to score it before any code is sent, and likely bots (low
score or invalid token) land on a block screen. If the connector itself is down, users still get a code (fail
open). Built from [sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) without Google; the
reCAPTCHA component, assess step and score condition come from the console template
`recaptcha-enterprise-template-sign-up-or-in`.

## When to use

"Bot protection", "CAPTCHA", "reCAPTCHA", "stop fake sign-ups", "SMS/email pumping", "fraud check at sign-up".
Checking before the code is sent is what stops bots from making the project send emails or texts. hCaptcha and
Turnstile connectors feed the engine's risk token the same way; check their command names in the catalog. For risk scores from other signals
(impossible travel, new device), see the console templates `adaptive-mfa-*`.

## Flow

```
0 Welcome (email, invisible reCAPTCHA) --> 22 assess --> 23 bot? --no--> 19 send OTP --> 20 Verify OTP --> 21 verify --> 4 new user? ... --> 8 End
                                             |                           \--yes--> 24 Blocked --Try again--> 0
                                             |--create_assessment_error--------> 24
                                             \--ConnectorFailed (connector down)--> 19
```

| Task | Type, action | What to know |
|---|---|---|
| `0` | screen | `Recaptcha` `-ddBSWh6AN` with `enterprise: true`, `enabled: "true"` and `site-key`: the connector's site key. It runs invisibly (a small badge), loads Google's `enterprise.js` itself and refreshes the token about every two minutes. It is not a form input: the token goes to the engine with the next submit, and no task reads it by name. Continue `S-VOZ5i7gc` -> `22`. |
| `22` | `connector` | `templateId: "recaptcha-enterprise"`, `command: "assess"`, `connectorId`: the reCAPTCHA Enterprise connector configured in the project (Google Cloud project id, site key, API key). `args` is empty: the engine adds the token, the user's IP and user agent itself. The result lands at `connectors.recaptcha-enterprise_assess` (`resultPath`): Google's assessment, e.g. `.riskAnalysis.score` and `.riskAnalysis.reasons`, plus `.riskScore`. |
| `22` errors | | A missing, expired or malformed token is an error, not a low score: `create_assessment_error` (also when Google rejects the request) -> `24`. `ConnectorFailed` (the connector can't run) -> `19`. Both use `errorHandlingV2: custom` with a next rule named after the error. |
| `23` | condition | `riskInfo.botDetected` is-true -> `24`, else `19`. The assess command is risk-tagged, so the engine merges its `riskInfo` into the flow's (an earlier risk result keeps the higher `riskScore`, and `botDetected` is ORed): `botDetected` is Google's score below the connector's bot threshold setting (default 0.5), `riskScore` is the score itself (0 to 1, 1 = very likely human). The full assessment stays at `connectors.recaptcha-enterprise_assess` (`.riskAnalysis.score`). |
| `24` | screen | Block message and "Try again" `Wq4nT7cKzE` -> `0` (for the few humans scored low). |
| `19`-`8` | | The OTP email login of the base recipe. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Connector and site key** (required): replace `REPLACE_WITH_RECAPTCHA_CONNECTOR_ID` in
  `tasks.22.arguments.connectorId.value` with the connector's id, and `REPLACE_WITH_RECAPTCHA_SITE_KEY` in the
  `-ddBSWh6AN` node's `site-key` prop with the same connector's site key. When the component is added in the console
  editor, it copies the site key from the project's reCAPTCHA connector; the engine does not fill it from the flow's
  connector task.
- **Threshold**: set the connector's bot threshold (default 0.5); higher blocks more bots and more humans. For a
  threshold in the flow, test `connectors.recaptcha-enterprise_assess.riskScore` less-than your value instead.
- **Fail closed**: point the `ConnectorFailed` rule at `24` instead of `19`. Then a Google or connector outage blocks
  every sign-in.
- **Challenge instead of block**: send `23`'s "Likely bot" branch (`k7rb2xqm9wd`) to a second factor (e.g. an SMS code, or a TOTP step from
  [sign-up-or-in-otp-email-totp-mfa](../sign-up-or-in-otp-email-totp-mfa/README.md)) instead of `24`.
- **Teach the model**: after verification, a second `connector` task with `command: "annotate"` and `args` rows
  `annotation` = `LEGITIMATE`, `reason` = `PASSED_TWO_FACTOR` (the template's task `8`) reports the outcome to
  Google. It finds the assessment by itself; no wiring from `22` is needed.

## Pitfalls

- An invalid token can also come back as an error named after Google's reason (e.g. `MALFORMED`, `EXPIRED`, `DUPE`)
  instead of `create_assessment_error`. Those have no rule here, so the flow's default handling shows the error on
  the Welcome screen and no code is sent; don't add a catch-all that sends them on to `19`.
- Fail-open can hide a broken setup: a connector that can't be loaded or run ends as `ConnectorFailed` (a wrong
  `connectorId` most likely too), and then every user skips the check. Test the block path once (low score or no token) before relying on it.
- The connector's "override assessment" setting is for testing: it skips Google and returns a fixed score for
  everyone. Keep it off in production.
- The component's `site-key` must belong to the same Google Cloud project and key as the connector, or every token
  is invalid and every user is blocked.
- Don't test `riskInfo.riskScore` when another risk source runs in the flow (a fingerprint connector, the `risk`
  action, a honeypot field on a screen, which sets 1.0): the engine merges their results with `riskScore` = the highest, and those scores run the other way
  (high = risky). `botDetected` is OR-ed across sources, so it stays correct.
- Use `Recaptcha` (with `enterprise: true`) for this connector. `RecaptchaV2` in a screen is the console's
  "reCAPTCHA V3" component, which goes with the `recaptcha` (v3) connector.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Engine behavior read from source: `assess` carries the `risk` tag and returns `riskInfo.riskScore` =
  `riskAnalysis.score`; the token comes from context, not a form key; invalid token -> error; the connector's errors
  and result shape; the reCAPTCHA screen component.
- e2e: not run (needs a browser-made token; the connector's override setting could make it testable).
