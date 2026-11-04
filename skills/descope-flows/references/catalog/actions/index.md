# Action index

Generated from Descope's action definitions. Do not edit by hand.

One line per action: id, console name, and its group file. `H` = hidden in the console picker (still valid), `G` = group shorthand (never a task action; use its members), `X` = no executor in the backend (fails at runtime; never use). Read the group file for inputs, outputs and errors.

## [OTP by email](otp-email.md)

- `sign-in-otp-email` [H]: Sign In / OTP / Email
- `sign-up-or-in-otp-email` [H]: Sign Up or In / OTP / Email
- `sign-up-otp-email` [H]: Sign Up / OTP / Email
- `update-email-otp-embedded`: Generate OTP Embedded Code for Update User Email
- `update-user-otp-email` [H]: Update User / OTP / Email
- `verify-code-otp-email` [H]: Verify Code / OTP / Email

## [OTP by SMS, voice, WhatsApp or IM](otp-phone.md)

- `sign-in-otp-im` [H]: Sign In / OTP / Instant Message (IM)
- `sign-in-otp-sms` [H]: Sign In / OTP / SMS
- `sign-in-otp-voice` [H]: Sign In / OTP / Voice call
- `sign-in-otp-whatsapp` [H]: sign-in-otp-whatsapp
- `sign-up-or-in-otp-im` [H]: Sign Up or In / OTP / Instant Message (IM)
- `sign-up-or-in-otp-sms` [H]: Sign Up or In / OTP / SMS
- `sign-up-or-in-otp-voice` [H]: Sign Up or In / OTP / Voice call
- `sign-up-or-in-otp-whatsapp` [H]: sign-up-or-in-otp-whatsapp
- `sign-up-otp-im` [H]: Sign Up / OTP / Instant Message (IM)
- `sign-up-otp-sms` [H]: Sign Up / OTP / SMS
- `sign-up-otp-voice` [H]: Sign Up / OTP / Voice call
- `sign-up-otp-whatsapp` [H]: sign-up-otp-whatsapp
- `update-phone-otp-embedded`: Generate OTP Embedded Code for Update User Phone
- `update-user-otp-im` [H]: Update User / OTP / Instant Message (IM)
- `update-user-otp-sms` [H]: Update User / OTP / SMS
- `update-user-otp-voice` [H]: Update User / OTP / Voice call
- `update-user-otp-whatsapp` [H]: update-user-otp-whatsapp
- `verify-code-otp-im` [H]: Verify Code / OTP / Instant Message (IM)
- `verify-code-otp-sms` [H]: Verify Code / OTP / SMS
- `verify-code-otp-voice` [H]: Verify Code / OTP / Voice call
- `verify-code-otp-whatsapp` [H]: verify-code-otp-whatsapp

## [OTP: embedded and other](otp.md)

- `otp-embedded-code-verifyv2`: Verify Embedded OTP Code
- `sign-in-otp-embedded`: Generate OTP Embedded Code for Sign In
- `sign-up-or-in-otp-embedded`: Generate OTP Embedded Code for Sign Up Or In
- `sign-up-otp-embedded`: Generate OTP Embedded Code for Sign Up

## [Magic link by email](magic-link-email.md)

- `sign-in-magic-linkv3-email` [H]: Sign In / Magic Link / Email
- `sign-in-magic-linkv3-email-group` [HG]: Sign In / Magic Link / Email
- `sign-up-magic-link-email` [H]: Sign Up / Magic Link / Email
- `sign-up-magic-link-email-group` [HG]: Sign Up / Magic Link / Email
- `sign-up-or-in-magic-linkv3-email` [H]: Sign Up or In / Magic Link / Email
- `sign-up-or-in-magic-linkv3-email-group` [HG]: Sign Up or In / Magic Link / Email
- `start-verify-recovery-magic-link-email`: Verify Recovery Email / Magic Link
- `update-user-magic-link-email` [H]: Update User / Magic Link / Email
- `update-user-magic-link-email-group` [HG]: Update User / Magic Link / Email

## [Magic link by SMS or WhatsApp](magic-link-phone.md)

- `sign-in-magic-linkv3-sms` [H]: Sign In / Magic Link / SMS
- `sign-in-magic-linkv3-sms-group` [HG]: Sign In / Magic Link / SMS
- `sign-in-magic-linkv3-whatsapp` [H]: sign-in-magic-linkv3-whatsapp
- `sign-in-magic-linkv3-whatsapp-group` [HG]: sign-in-magic-linkv3-whatsapp-group
- `sign-up-magic-link-sms` [H]: Sign Up / Magic Link / SMS
- `sign-up-magic-link-sms-group` [HG]: Sign Up / Magic Link / SMS
- `sign-up-magic-link-whatsapp` [H]: sign-up-magic-link-whatsapp
- `sign-up-magic-link-whatsapp-group` [HG]: sign-up-magic-link-whatsapp-group
- `sign-up-or-in-magic-linkv3-sms` [H]: Sign Up or In / Magic Link / SMS
- `sign-up-or-in-magic-linkv3-sms-group` [HG]: Sign Up or In / Magic Link / SMS
- `sign-up-or-in-magic-linkv3-whatsapp` [H]: sign-up-or-in-magic-linkv3-whatsapp
- `sign-up-or-in-magic-linkv3-whatsapp-group` [HG]: sign-up-or-in-magic-linkv3-whatsapp-group
- `start-verify-recovery-magic-link-sms`: Verify Recovery Phone / Magic Link / SMS
- `update-user-magic-link-sms` [H]: Update User / Magic Link / SMS
- `update-user-magic-link-sms-group` [HG]: Update User / Magic Link / SMS
- `update-user-magic-link-whatsapp` [H]: update-user-magic-link-whatsapp
- `update-user-magic-link-whatsapp-group` [HG]: update-user-magic-link-whatsapp-group

## [Magic link: verify and other](magic-link.md)

- `finish-verify-recovery-magic-link`: Finish Verify Recovery / Magic Link
- `verify-magic-link` [H]: Verify Code / Magic Link

## [Enchanted link](enchanted-link.md)

- `sign-in-enchanted-link-email` [H]: Sign In / Enchanted Link / Email
- `sign-in-enchanted-link-email-group` [HG]: Sign In / Enchanted Link / Email
- `sign-in-enchanted-link-sms` [H]: Sign In / Enchanted Link / SMS
- `sign-in-enchanted-link-sms-group` [HG]: Sign In / Enchanted Link / SMS
- `sign-up-enchanted-link-email` [H]: Sign Up / Enchanted Link / Email
- `sign-up-enchanted-link-email-group` [HG]: Sign Up / Enchanted Link / Email
- `sign-up-enchanted-link-sms` [H]: Sign Up / Enchanted Link / SMS
- `sign-up-enchanted-link-sms-group` [HG]: Sign Up / Enchanted Link / SMS
- `sign-up-or-in-enchanted-link-email` [H]: Sign Up or In / Enchanted Link / Email
- `sign-up-or-in-enchanted-link-email-group` [HG]: Sign Up or In / Enchanted Link / Email
- `sign-up-or-in-enchanted-link-sms` [H]: Sign Up or In / Enchanted Link / SMS
- `sign-up-or-in-enchanted-link-sms-group` [HG]: Sign Up or In / Enchanted Link / SMS
- `update-user-enchanted-link-email` [H]: Update User / Enchanted Link / Email
- `update-user-enchanted-link-email-group` [HG]: Update User / Enchanted Link / Email
- `update-user-enchanted-link-sms` [H]: Update User / Enchanted Link / SMS
- `update-user-enchanted-link-sms-group` [HG]: Update User / Enchanted Link / SMS
- `verify-enchanted-link` [H]: Verify Code / Enchanted Link
- `verify-enchanted-linksingle`: Verify Code / Enchanted Link

## [Embedded link](embedded-link.md)

- `sign-in-embedded-link` [H]: Sign In / Embedded Link
- `sign-in-embedded-link-group` [G]: Sign In / Embedded Link
- `sign-in-embedded-linkmgmt`: Sign In / Embedded Link
- `sign-up-embedded-link` [H]: Sign Up / Embedded Link
- `sign-up-embedded-link-group` [G]: Sign Up / Embedded Link
- `sign-up-or-in-embedded-link` [H]: Sign Up or In / Embedded Link
- `sign-up-or-in-embedded-link-group` [G]: Sign Up or In / Embedded Link
- `update-user-email-embedded-link` [H]: Update User / Embedded Link / Email
- `update-user-email-embedded-link-group` [G]: Update User / Embedded Link / Email
- `update-user-phone-embedded-link` [H]: Update User / Embedded Link / Phone
- `update-user-phone-embedded-link-group` [G]: Update User / Embedded Link / Phone
- `verify-embedded-link`: Verify Token

## [OAuth and social login](oauth.md)

- `exchange-oauth-code` [H]: OAuth / Exchange
- `exchange-oauth-code-in` [H]: OAuth / Exchange
- `exchange-oauth-code-up` [H]: OAuth / Exchange
- `oauth` [G]: Sign Up or In / OAuth
- `oauth-signin` [HG]: Sign In / OAuth
- `oauth-signin-v2` [G]: Sign In / OAuth
- `oauth-signup` [HG]: Sign Up / OAuth
- `oauth-signup-v2` [G]: Sign Up / OAuth
- `oauth-start` [H]: OAuth / Start
- `oauth-start-sign-in` [H]: Sign In / OAuth / Start
- `oauth-start-sign-in-v2` [H]: Sign In / OAuth / Start
- `oauth-start-sign-up` [H]: Sign Up / OAuth / Start
- `oauth-start-sign-up-v2` [H]: Sign Up / OAuth / Start
- `oauth-start-update-user` [H]: User / Update / OAuth
- `oauth-update-user` [G]: Update User / OAuth

## [Passkeys (WebAuthn)](passkeys.md)

- `webauthn-remove`: Update User / Remove Passkey (WebAuthn)
- `webauthn-remove-all`: Update User / Remove All Passkeys (WebAuthn)
- `webauthn-sign-in` [HG]: Sign In / Passkeys (WebAuthn)
- `webauthn-sign-in-finish` [H]: Sign In / Passkeys (WebAuthn) / Finish
- `webauthn-sign-in-start` [H]: Sign In / Passkeys (WebAuthn) / Start
- `webauthn-sign-in-start-v2` [H]: Sign In / Passkeys (WebAuthn) / Start
- `webauthn-sign-in-v2` [G]: Sign In / Passkeys (WebAuthn)
- `webauthn-sign-up` [G]: Sign Up / Passkeys (WebAuthn)
- `webauthn-sign-up-finish` [H]: Sign Up / Passkeys (WebAuthn) / Finish
- `webauthn-sign-up-or-in` [G]: Sign Up or In / Passkeys (WebAuthn)
- `webauthn-sign-up-or-in-finish` [H]: Sign Up or In / Passkeys (WebAuthn) / Finish
- `webauthn-sign-up-or-in-start` [H]: Sign Up or In / Passkeys (WebAuthn) / Start
- `webauthn-sign-up-start` [H]: Sign Up / Passkeys (WebAuthn) / Start
- `webauthn-update-user` [G]: Update User / Passkeys (WebAuthn)
- `webauthn-update-user-finish` [H]: Update User / Passkeys (WebAuthn) / Finish
- `webauthn-update-user-start` [H]: Update User / Passkeys (WebAuthn) / Start

## [Password](password.md)

- `get-tenant-password-config`: Tenant / Get Password Configuration
- `password-delete`: Delete Password
- `password-expire`: Expire Password
- `password-merge`: Merge User / Password
- `password-replace` [H]: Replace Password
- `password-replace-v2` [H]: Replace Password
- `password-replace-v3`: Replace Password
- `password-send-reset` [H]: Send Password Reset
- `password-send-reset-group` [HG]: Send Password Reset
- `password-sign-in` [H]: Sign In / Password
- `password-sign-in-v2` [H]: Sign In / Password
- `password-sign-up`: Sign Up / Password
- `password-update`: Update Password
- `reset-tenant-password-config`: Tenant / Reset Password Configuration
- `update-tenant-password-config`: Tenant / Update Password Configuration

## [TOTP, nOTP, push, recovery codes, security questions](mfa.md)

- `batch-remove-totp`: User / Batch / Remove TOTP seed
- `recovery-codes-generate`: Recovery Codes / Generate
- `remove-totp`: Update User / Remove TOTP seed
- `security-questions-setup`: Security Questions / Setup
- `security-questions-verify`: Security Questions / Verify
- `sign-in-notp` [H]: Sign In / NOTP (WhatsApp)
- `sign-in-push` [H]: Sign In / Push Notification
- `sign-in-recovery-code`: Sign In / Recovery Code
- `sign-in-totp` [HX]: Sign In / TOTP
- `sign-up-notp` [H]: Sign Up / NOTP (WhatsApp)
- `sign-up-or-in-notp` [H]: Sign Up or In / NOTP (WhatsApp)
- `sign-up-totp` [H]: Sign Up / TOTP
- `update-user-notp` [H]: Update User / NOTP (WhatsApp)
- `update-user-totp` [H]: Update User / TOTP
- `verify-totp-code` [H]: Verify Code / TOTP

## [JWT, session, step-up, impersonation, devices](session.md)

- `anonymous-user`: Sign Up / Anonymous user
- `custom-claims`: Custom Claims
- `generate-jwt-sign-in`: Generate JWT / Sign In with 3rd party IDP
- `generate-jwt-sign-up`: Generate JWT / Sign Up with 3rd party IDP
- `generate-jwt-sign-up-or-in`: Generate JWT / Sign Up or In with 3rd party IDP
- `impersonate`: User / Impersonate
- `impersonateFamilyDependent`: Family / Impersonate Dependent
- `impersonationConsent`: Update User / Impersonation consent
- `logged-in`: End
- `logout-session`: Log out session
- `mark-device-known`: Mark device as known
- `reset-current-auth`: Reset Auth Info
- `revoke-other-sessions`: Revoke Other Sessions
- `setStepUp` [H]: Add login options to flow
- `start-step-up` [G]: Step Up
- `step-up` [H]: Step Up
- `stop-impersonation`: User / Stop Impersonation
- `tenant-get-session-settings`: Tenant / Get Session Settings
- `tenant-reset-session-settings`: Tenant / Reset Session Settings
- `tenant-set-session-settings`: Tenant / Update Session Settings
- `trust-device`: Mark device as trusted
- `untrust-device`: Unmark device as trusted

## [Consent, inbound/outbound apps, agentic hub, device flow, CIBA, external auth, admin links](apps-consent.md)

- `admin-link-sso-generate` [H]: Generate SSO configuration admin link
- `admin-link-sso-generate-v2`: Generate SSO setup suite admin link
- `admin-link-sso-revoke`: Revoke SSO configuration admin link
- `agentic-hub-connection-connect` [H]: Agentic Hub / Connect
- `agentic-hub-connection-connect-group` [G]: Agentic Hub / Connect
- `agentic-hub-update-mcp-client`: Update MCP Client
- `ciba-finish`: CIBA Approval
- `ciba-user-code-verification`: CIBA User Code Verification
- `create-consent`: Update user consent
- `create-tenant-consent`: Update tenant consent
- `device-flow-finish`: Device Flow Approval
- `device-flow-user-code-verification`: Device Flow User Code Verification
- `external-auth` [G]: External Authentication
- `external-auth-exchange` [H]: External Auth / Exchange
- `external-auth-start` [H]: External Auth / Start
- `outbound-api-app-connect`: Outbound App / Connect API key
- `outbound-api-app-tenant-connect`: Outbound App / Connect tenant API key
- `outbound-app-user-tokens-delete`: Outbound App / Delete User Tokens
- `outbound-oauth-app-connect` [H]: Outbound App / Connect
- `outbound-oauth-app-connect-finish` [H]: Outbound OAuth App Connect Finish
- `outbound-oauth-app-connect-group` [G]: Outbound App / Connect
- `outbound-oauth-app-tenant-connect` [H]: Outbound App / Tenant Connect
- `outbound-oauth-app-tenant-connect-finish` [H]: Outbound App / Tenant Connect Finish
- `outbound-oauth-app-tenant-connect-group` [G]: Outbound App / Tenant Connect
- `provision-mcp-company` [H]: Provision MCP company
- `update-inbound-app`: Update Inbound App
- `update-inbound-app-status`: Update Inbound App Status

## [SSO: SAML, OIDC, SCIM, tenant SSO configuration](sso.md)

- `exchange-saml-code` [H]: SSO / Exchange
- `oidc-get-config`: SSO / Get OIDC Configuration
- `oidc-set-config`: SSO / Set OIDC Configuration
- `saml` [G]: SSO
- `saml-enabled` [H]: SSO / Enabled
- `saml-get-config`: SSO / Get SAML Configuration
- `saml-set-config`: SSO / Set SAML Configuration
- `saml-start` [H]: SSO / Start
- `scim-create-key`: SSO / Create SCIM access key
- `sso-additional-saml-attributes`: SSO / Add SAML Attributes
- `sso-create-configuration`: SSO / Create SSO Configuration
- `sso-delete-configuration`: SSO / Delete SSO Configuration
- `sso-disable-config`: SSO / Disable SSO Configuration
- `sso-no-user` [G]: SSO / Authenticate Only
- `sso-start-no-user` [H]: SSO / Start / Authenticate Only
- `sso-start-test` [H]: SSO / Start / Test
- `sso-test` [G]: SSO / Test Configuration (dry run)
- `update-users-add-sso-apps`: User / Batch / Add Applications
- `update-users-delete-sso-apps`: User / Batch / Delete Applications

## [Tenants and roles](tenants-roles.md)

- `createTenant`: Create Tenant
- `set-batch-user-roles`: User / Batch / Set Roles
- `tenant-get-config`: Tenant / Get Configuration
- `tenant-set-config`: Tenant / Update Configuration
- `update-user-dynamic-tenant`: Update User / Add Tenant Dynamically (unsafe)
- `update-user-roles`: User / Edit Roles
- `update-user-tenant-email-domain`: Update User / Add Tenant by Email Domain
- `update-users-add-roles`: User / Batch / Add Roles
- `update-users-delete-roles`: User / Batch / Remove Roles
- `updateTenant`: Update Tenant
- `user-add-roles`: Update User / Add Roles
- `user-remove-roles`: Update User / Remove Roles

## [Users](users.md)

- `createFamily`: Create Family
- `createFamilyDependent`: Family / Create Dependent
- `delete-user`: User / Delete
- `delete-users`: User / Batch / Delete
- `disable-user`: User / Disable
- `enable-user`: User / Enable
- `invite-user-email`: User / Invite
- `load-selected-user`: User / Load / Selected User
- `load-user-from-triggering-event`: Load User / From Triggering Event
- `loadUser`: Load User
- `stopFamilyImpersonation`: Family / Stop Impersonation
- `update-user-properties`: Update User / Attributes
- `update-users-status`: User / Batch / Update Status
- `validate-email`: Validate email address

## [Connectors, scriptlets, lists, risk and utilities](connectors-logic.md)

- `add-to-list`: Add to List
- `calc-risk-score-ng`: Calculate Risk Score
- `check-if-disposable-email`: Check if Disposable Email used
- `check-if-free-email`: Check if free email provider used
- `check-rate-limit`: Check Rate Limit
- `connector` [H]: Execute Connector
- `debug` [H]: debug
- `decrypt`: Decrypt Data
- `email-connector` [H]: Execute email Connector
- `encrypt`: Encrypt Data
- `generate-audit-event`: Generate Audit Event
- `im-connector` [H]: Execute IM Connector
- `load-mail-provider-host` [H]: Load Mail Provider Hostname
- `redirect-to-url`: Redirect to URL
- `remove-from-list`: Remove from List
- `risk`: Fingerprint / Assess
- `scriptlet`: Scriptlet
- `sms-connector` [H]: Execute SMS Connector
- `voice-connector` [H]: Execute voice call Connector

## [Other](other.md)

- `clear-last-error`: Clear Last Error
- `management-end`: End
- `reset-form`: Reset Form
