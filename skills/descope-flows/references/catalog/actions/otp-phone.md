# Actions: OTP by SMS, voice, WhatsApp or IM

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `sign-in-otp-im`

**Sign In / OTP / Instant Message (IM)**. Enable users to sign up using OTP via instant message (IM). Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (IM blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified)
Note: `OTPSignUpOrInPhoneFailed` is also the error for a login id with no user (message "Failed to sign in, phone does not exist"); there is no separate user-not-found error id.

- hidden in the console's action picker (still valid in a flow)
- tags: one time password, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `context`, `phone`, `email`, `externalId`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `lastAuth`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-otp-sms`

**Sign In / OTP / SMS**. Enable users to sign up using OTP via SMS. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (SMS blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified)
Note: `OTPSignUpOrInPhoneFailed` is also the error for a login id with no user (message "Failed to sign in, phone does not exist"); there is no separate user-not-found error id.

- hidden in the console's action picker (still valid in a flow)
- tags: one time password, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `context`, `phone`, `email`, `externalId`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `lastAuth`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-otp-voice`

**Sign In / OTP / Voice call**. Enable users to sign up using OTP via voice call. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (Call blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified)
Note: `OTPSignUpOrInPhoneFailed` is also the error for a login id with no user (message "Failed to sign in, phone does not exist"); there is no separate user-not-found error id.

- hidden in the console's action picker (still valid in a flow)
- tags: one time password, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `context`, `phone`, `email`, `externalId`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `lastAuth`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-otp-whatsapp`

**sign-in-otp-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified)
Note: `OTPSignUpOrInPhoneFailed` is also the error for a login id with no user (message "Failed to sign in, phone does not exist"); there is no separate user-not-found error id.

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `phone`, `email`, `externalId`, `context`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `lastAuth`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-otp-im`

**Sign Up or In / OTP / Instant Message (IM)**. Enable users to sign up or in using OTP via instant message (IM). Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (IM blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password, sign in, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `context`, `lastAuth`, `customClaims`, `startOptions`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-otp-sms`

**Sign Up or In / OTP / SMS**. Enable users to sign up or in using OTP via SMS. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (SMS blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password, sign in, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `context`, `lastAuth`, `customClaims`, `startOptions`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-otp-voice`

**Sign Up or In / OTP / Voice call**. Enable users to sign up or in using OTP via voice call. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (Call blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password, sign in, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `context`, `lastAuth`, `customClaims`, `startOptions`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-otp-whatsapp`

**sign-up-or-in-otp-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `phone` | string | yes | context | Phone |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `context`, `externalId`, `lastAuth`, `customClaims`, `startOptions`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-otp-im`

**Sign Up / OTP / Instant Message (IM)**. Enable users to sign up using OTP via instant message (IM). Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (IM blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `context`, `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-otp-sms`

**Sign Up / OTP / SMS**. Enable users to sign up using OTP via SMS. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (SMS blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `context`, `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-otp-voice`

**Sign Up / OTP / Voice call**. Enable users to sign up using OTP via voice call. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (Call blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `context`, `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-otp-whatsapp`

**sign-up-otp-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInPhoneFailed` (Error sending OTP code), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `externalId`, `email`, `context`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-phone-otp-embedded`

**Generate OTP Embedded Code for Update User Phone**. Generate an OTP Code that can be sent later via connector for user phone update, use {{embeddedCode}} for code in connector

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPUpdatePhoneEmbeddedFailed` (Error generating code)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phoneVerified` | boolean |  | argument | Mark provided phone as verified |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `externalId`, `email`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-otp-im`

**Update User / OTP / Instant Message (IM)**. Update a user's phone. Before doing so, verify the new phone using OTP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPUpdateUserPhoneFailed` (Error updating user), `OTPUnauthorizedRequest` (Unauthorized request), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (IM blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `phone` | string | yes | context | Phone |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `context`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-otp-sms`

**Update User / OTP / SMS**. Update a user's phone. Before doing so, verify the new phone using OTP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPUpdateUserPhoneFailed` (Error updating user), `OTPUnauthorizedRequest` (Unauthorized request), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (SMS blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `phone` | string | yes | context | Phone |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `context`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-otp-voice`

**Update User / OTP / Voice call**. Update a user's phone. Before doing so, verify the new phone using OTP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPUpdateUserPhoneFailed` (Error updating user), `OTPUnauthorizedRequest` (Unauthorized request), `OTPSignUpOrInPhoneCallBlockedByTwilioFailed` (Call blocked by provider), `OTPSignUpOrInPhoneRateLimitByProviderFailed` (Rate limit exceeded by provider), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `phone` | string | yes | context | Phone |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `context`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-otp-whatsapp`

**update-user-otp-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPUpdateUserPhoneFailed` (Error updating user), `OTPUnauthorizedRequest` (Unauthorized request)

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `phone` | string | yes | context | Phone |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `context`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-code-otp-im`

**Verify Code / OTP / Instant Message (IM)**. Verify the code manually inputted by the user is the one that was generated as part of the OTP authentication.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OTPVerifyCodePhoneFailed` (Error verifying OTP code), `OTPVerifyCodeExpired` (OTP code expired), `OTPUpdateUserConflict` (User update failed due to conflict with existing user)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `code` | string | yes | context | Code |

Also reads from context when present: `tmpExternalId`, `externalId`, `phone`, `password`, `lastAuth` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-code-otp-sms`

**Verify Code / OTP / SMS**. Verify the code manually inputted by the user is the one that was generated as part of the OTP authentication.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OTPVerifyCodePhoneFailed` (Error verifying OTP code), `OTPVerifyCodeExpired` (OTP code expired), `OTPUpdateUserConflict` (User update failed due to conflict with existing user)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `code` | string | yes | context | Code |

Also reads from context when present: `tmpExternalId`, `externalId`, `phone`, `password`, `lastAuth` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-code-otp-voice`

**Verify Code / OTP / Voice call**. Verify the code manually inputted by the user is the one that was generated as part of the OTP authentication.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OTPVerifyCodePhoneFailed` (Error verifying OTP code), `OTPVerifyCodeExpired` (OTP code expired), `OTPUpdateUserConflict` (User update failed due to conflict with existing user)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `code` | string | yes | context | Code |

Also reads from context when present: `tmpExternalId`, `externalId`, `phone`, `password`, `lastAuth` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-code-otp-whatsapp`

**verify-code-otp-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OTPVerifyCodePhoneFailed` (Error verifying OTP code), `OTPVerifyCodeExpired` (OTP code expired), `OTPUpdateUserConflict` (User update failed due to conflict with existing user)

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `code` | string | yes | context | Code |

Also reads from context when present: `tmpExternalId`, `externalId`, `phone`, `password`, `lastAuth` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
