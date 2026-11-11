# Patterns without a recipe

Common customer requests that no recipe covers yet. Start from the closest recipe and change what is described here.
Action ids, inputs and keys below are from `catalog/`; the Descope template named in each one shows the whole wiring.
None of these was run end to end by this skill: list what you rely on under "Assumed, not verified" in the report.

## Trusted device: skip MFA on a remembered device

Template `adaptive-mfa-trusted-device`. After the first factor, a condition on `riskInfo.trustedDevice` (is-true)
goes straight to `logged-in`; `ELSE` runs the second factor (for example `sign-in-otp-sms` and
`verify-code-otp-sms`). After the second factor, a screen asks "Trust this device?": one button goes to `End`, the
other to a `trust-device` task ("Mark device as trusted"), then `End`. Start from
`recipes/sign-up-or-in-otp-email-adaptive-mfa` or `recipes/sign-up-or-in-otp-email-totp-mfa` and add the condition
and the screen.

## Existing users only (no sign-up)

Use sign-in actions instead of sign-up-or-in ones: `sign-in-otp-email` / `sign-in-otp-sms` (an unknown user gets
`OTPSignUpOrInEmailFailed` / `OTPSignUpOrInPhoneFailed`, shown on the screen by default; the same error type
covers a failed send, so a rule on it can't tell "no account" from "couldn't send"), the magic link sign-ins (`UserDoesNotExists`, see the `sign-in-magic-link`
recipe), the group `oauth-signin-v2` for social login (tasks `oauth-start-sign-in-v2` and `exchange-oauth-code-in`,
see the group rules in `guardrails.md`), passwords with `password-sign-in-v2` alone. Drop the user-information screen and
any `authInfo.firstSeen` branch. Users are then created elsewhere (Management API, invitations). Say in the
report that an explicit "no account" message reveals which emails are registered (`guardrails.md`).

SSO is the exception: `saml-start` / `exchange-saml-code` creates the user on a first SSO login, and no flow input
stops it (a condition on `authInfo.firstSeen` after the exchange runs once the user already exists). Turn off JIT
provisioning in the tenant's SSO configuration: an SSO login by a user who doesn't exist in Descope then fails at
the exchange step. Route the exchange's errors (`SAMLExchangeCodeFailed`, `OAuthExchangeCodeFailed`,
`SSSOExchangeCodeFailed`) with `customWithError` to the sign-in screen and a message, and list under Assumed which
error type that login raises: it isn't verified. Ask the user to switch the setting, per SSO configuration; the
flow can't. `sso-no-user` (SSO / Authenticate Only) is not a substitute: it signs no one in.

## Just-in-time password migration from a legacy system

No dedicated action. First ask which system owns the password: is the legacy system checked on every sign-in (it
still owns passwords: users or admins can change them there), or only when Descope's own check fails (passwords
move to Descope once)? Follow the user's words: "checked against our legacy API first" means legacy first.

**Legacy first (the legacy system owns passwords).** Sign-in screen -> the `connector` task posting the login id and
password to the legacy sync API -> a condition on a body field that it succeeded -> `password-sign-in-v2` with the
same form inputs -> `End`. The sync API must create or update the user in Descope with the current password
(management API) before it answers, or the Descope sign-in that follows fails after every legacy password change.
`request_error` and the condition's `ELSE` go to the sign-in screen with an error; `ConnectorFailed` (legacy down)
fails closed unless the user chooses otherwise. Password changes in the flow (reset, update) go to the legacy API
first, then to Descope (`password-update` or the reset recipe's action): legacy first, so a legacy failure leaves
both systems on the old password.

Forgot password, legacy first: a user the legacy system knows may not be in Descope yet, and `password-send-reset`
then fails as if the account didn't exist. Before the send, call the legacy sync API with the email (a `connector`
task) so it creates or updates the user in Descope. Route its `request_error` (unknown email) to the same neutral
"if an account exists, we sent a link" screen the reset recipe uses, so the answer never tells which emails exist;
`ConnectorFailed` (legacy down) fails closed with a "try again later" message unless the user chooses otherwise.

The password recipes check that the email is verified after sign-in (`passwords-reset-by-link` task `24`). Users the
sync API creates are unverified unless it marks the email verified, so every synced user would be stopped there.
Ask the user: have the sync API set the email verified when the legacy system had verified it (keeps the check), or
remove the check for this flow (list the removal in the report).

**Descope first (passwords move once).** Users still in the old system sign in once with their old password and
are created in Descope. Warn the user: while the legacy system can still change passwords, Descope first lets an
old password in (Descope's copy wins), so use it only once the legacy system no longer changes them.
`password-sign-in-v2`; route `PasswordSignInFailed` (custom) to a Generic HTTP `connector` task that posts the login id
and password to the legacy system's verify endpoint (`connectors.md`); a non-2xx answer is `request_error`, a 2xx
answer continues to a condition on a body field (`connectors.http_post.<field>`); success -> `password-sign-up` with the same form inputs (`email`,
`password`; it also has `skipPasswordPolicy`, for legacy passwords that fail the project's policy) -> `End`; failure, `request_error` and
`PasswordSignUpFailed` -> the sign-in screen with an error. The password travels to the legacy API: say so, and keep
its credentials in the connector, never in the flow. A wrong password of an already migrated user also takes this
path and fails there.

Second shape, when the legacy side owns the migration: its sync API checks the password and creates the user in
Descope itself (management API, with the password or its hash). Then the flow never signs up: `password-sign-in-v2`
`PasswordSignInFailed` (custom) -> the `connector` task posting the login id and password -> a condition that the
call succeeded -> a second `password-sign-in-v2` task with the same form inputs -> `End`. It has to be a second task:
its `PasswordSignInFailed` goes back to the sign-in screen with an error, not to the connector again. Ask which shape
the legacy API implements before building, and what an outage of it should do (fail closed: the sign-in screen with
an error, unless the user chooses otherwise).

## Different messages for different HTTP failures (4xx vs 5xx)

`customWithError` shows its message only on a rule straight to a screen, so a message that depends on the status
needs its own screen per branch. Route `request_error` (custom) to a condition on `connectors.<resultPath>.statusCode`
(written on `request_error`): `less-than` `500` -> a screen saying the details are wrong ("Wrong email or
password"), `ELSE` -> a screen saying the service is unavailable. Copy the sign-in screen for each (same inputs,
its own `Text` message and new ids) so the user can retry there, or use a short message screen with a "Try again"
button back to the sign-in screen. Route `ConnectorFailed` to the unavailable screen too.

## Lock after N wrong codes

Descope already caps wrong one-time codes: after 3 wrong entries (the default) the code is deleted, and only a new code
(`resend`) can sign the user in. Wrong codes and the capped one both fail `verify-code-otp-*` with
`OTPVerifyCodeEmailFailed` (`OTPVerifyCodePhoneFailed` for SMS); after a wrong code `remainingOTPAttempts` holds the
attempts left, at the cap it is empty. Checked end to end: wrong codes 1 and 2 answer "attempts
left: 2", then 1; the third wrong code already ends the code, and even the right one then fails; after `resend` the
fresh code signs in. Every failure stays on the code screen as `OTPVerifyCodeEmailFailed`. So "lock after 3 wrong codes"
needs no counter: the default handling shows each error on the code screen. A dedicated message at the cap would route
the error (custom) to a condition on `remainingOTPAttempts` (a number, unset at the cap; the checked run
did not read it); which operator tests an unset number is not checked, so prefer the default unless the user asks. For the default 3, a scriptlet counter adds nothing: its count lives in the run, so a restart or a new code resets it.

Ask what the user means by a lock. A lower count per code can be enforced with a run-scoped counter (a scriptlet),
knowing that a restart or a new code resets it. A lock that outlives the code (the account blocked for a while, or until
support unlocks it) can't be built in the flow: no action writes an unauthenticated user (`update-user-properties` needs
a signed-in user, `disable-user` is for management flows). Have the app's backend count failures and disable the user
through the management API, reached by a Generic HTTP `connector` task on the error path, and check
`unauthUser.isDisabled` before sending a code. Say the trade-off: anyone who knows an email can then lock that account
by typing wrong codes, so prefer a lock that expires. Passwords have a native lock: the project's password settings lock
the user after failed attempts, and `password-sign-in-v2` fails with `UserTemporarilyLocked`. Sends are rate limited too
(`ActionErrorRateLimitExceeded` on the send action).

## SSO enforcement per tenant

Template `sign-up-or-in-with-sso-exclusion-list`, and the recipe `sso-by-domain-or-otp-email`. After the email is
entered, a condition on `ssoEnabled` (SSO configured for the user's tenant or email domain) sends the user to
`saml-start` / `exchange-saml-code` (OIDC too); `ELSE` to the other method. `tenant.enforceSSO` and
`tenant.enforceSSOExclusions` say whether the tenant enforces SSO and who may bypass it. They are readable before
login: after a screen that collects the email, `tenant.*` resolves to the tenant of the email's domain (empty, so
`enforceSSO` false, when none matches). To enforce, branch right after that screen: `tenant.enforceSSO` is-true and
`form.email` not-in `tenant.enforceSSOExclusions` -> SSO only, without offering another method; the template
computes the same bypass in a scriptlet (results under `scripts.<outputPath>`). Sign-in actions also fail with
`ActionErrorTenantRequiresSSO` when the tenant enforces SSO: route it to the SSO task instead of an error.

## One input for email or phone

Template `email-or-phone-template-sign-up-or-in`. The screen has one `HybridField` ("Email or Phone") named
`externalId`. A condition with operator `is-email` on `form.externalId` goes to `sign-up-or-in-otp-email`, `ELSE` to
`sign-up-or-in-otp-sms` (`is-phone` exists too); both actions read `externalId`. Each branch has its own verify
screen and `verify-code-otp-email` / `verify-code-otp-sms`.
