# Recipes

Complete flows that import as-is. Pick the closest one, copy its `flow.json`, and adapt it following its README.

| The user wants | Recipe | Methods |
|---|---|---|
| Sign up or in with email codes and/or social login | [sign-up-or-in-otp-email-google](sign-up-or-in-otp-email-google/README.md) | OTP email, Google (any social provider) |
| Separate sign-in and sign-up screens (sign-in never creates accounts), no enumeration | [sign-in-or-sign-up-otp-email](sign-in-or-sign-up-otp-email/README.md) | OTP email |
| Sign-up asks first and last name and a required terms checkbox (custom input `form.<key>`) | [sign-up-or-in-otp-email-names-terms](sign-up-or-in-otp-email-names-terms/README.md) | OTP email, Google, checkbox checked on the server |
| Age check (date of birth, minimum age) before the account is created | [sign-up-or-in-otp-email-age-check](sign-up-or-in-otp-email-age-check/README.md) | OTP email, DateInput, scriptlet |
| Passwordless sign up or in by email link | [sign-up-or-in-magic-link](sign-up-or-in-magic-link/README.md) | Magic link email |
| Magic link, then a required passkey as second factor (enroll one if missing) | [sign-up-or-in-magic-link-passkey-required](sign-up-or-in-magic-link-passkey-required/README.md) | Magic link email, passkeys (WebAuthn) |
| Email + password: sign in, sign up, forgot password, verify email | [passwords-sign-up-or-in-verify-email](passwords-sign-up-or-in-verify-email/README.md) | Password, OTP email (verification, reset) |
| Email + password with "forgot password" by email link | [passwords-reset-by-link](passwords-reset-by-link/README.md) | Password, reset link, OTP email (verification) |
| SSO for domains whose tenant has it, email OTP for everyone else | [sso-by-domain-or-otp-email](sso-by-domain-or-otp-email/README.md) | SSO (SAML/OIDC, IdP-initiated), OTP email |
| Ask for missing profile fields (phone, name) after login | [sign-up-or-in-progressive-profiling](sign-up-or-in-progressive-profiling/README.md) | OTP email, OTP SMS (phone verification) |
| Call the app's API after login, put its answer in the JWT | [sign-up-or-in-http-connector-claims](sign-up-or-in-http-connector-claims/README.md) | OTP email, Generic HTTP connector, custom claims |
| Magic link sign-in for existing users only, with a message for unknown emails | [sign-in-magic-link](sign-in-magic-link/README.md) | Magic link email |
| Custom logic in the flow (compute values, map roles) and claims from it | [sign-up-or-in-scriptlet-claims](sign-up-or-in-scriptlet-claims/README.md) | OTP email, scriptlet, custom claims |
| Passkeys for returning users, email OTP otherwise, offer a passkey after login | [sign-up-or-in-passkeys-otp-email](sign-up-or-in-passkeys-otp-email/README.md) | Passkeys (WebAuthn), OTP email |
| Re-verify a signed-in user before a sensitive action (step-up) | [step-up-otp-email](step-up-otp-email/README.md) | Step-up, OTP email |
| Two-factor login: email OTP, then an authenticator app (TOTP), with enrollment | [sign-up-or-in-otp-email-totp-mfa](sign-up-or-in-otp-email-totp-mfa/README.md) | OTP email, TOTP |
| Users in several tenants pick one at login (session for that tenant) | [sign-up-or-in-otp-email-tenant-selection](sign-up-or-in-otp-email-tenant-selection/README.md) | OTP email, tenant selection |
| Reuse a step (here TOTP MFA) across flows by calling a subflow | [sign-up-or-in-otp-email-mfa-subflow](sign-up-or-in-otp-email-mfa-subflow/README.md) | OTP email, TOTP, subflow |
| Consent screen for an inbound app (OAuth/OIDC provider for partner apps, MCP clients, agents) | [inbound-app-consent-otp-email](inbound-app-consent-otp-email/README.md) | Inbound app consent, OTP email |
| Bot protection: stop likely bots before a code is sent (reCAPTCHA Enterprise) | [sign-up-or-in-otp-email-recaptcha](sign-up-or-in-otp-email-recaptcha/README.md) | OTP email, reCAPTCHA Enterprise connector |
| Sign up or in with a phone number and an SMS code | [sign-up-or-in-otp-sms](sign-up-or-in-otp-sms/README.md) | OTP SMS |
| MFA only when the sign-in looks risky (fingerprint risk score), SMS as second factor | [sign-up-or-in-otp-email-adaptive-mfa](sign-up-or-in-otp-email-adaptive-mfa/README.md) | OTP email, risk (fingerprint), OTP SMS |
| Passwordless email link the user matches by number (works across devices) | [sign-up-or-in-enchanted-link](sign-up-or-in-enchanted-link/README.md) | Enchanted link email |
| Signed-in user edits their name or changes their email (code to the new address) | [update-profile-name-email](update-profile-name-email/README.md) | Load user, update user, OTP email |

**Legal links**: login screens carry "terms of use" and "privacy policy" Links whose `href` is
`REPLACE_WITH_TERMS_URL` / `REPLACE_WITH_PRIVACY_URL`. Ask the user for both URLs (never invent `/terms` or
`/privacy`); if they have none yet, keep the placeholders and list each in the report with its screen and component
id. Remove the legal row only when the user asks.
