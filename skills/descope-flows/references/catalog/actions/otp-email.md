# Actions: OTP by email

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `sign-in-otp-email`

**Sign In / OTP / Email**. Enable users to sign in using OTP via Email. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInEmailFailed` (Error sending OTP code), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified)
Note: `OTPSignUpOrInEmailFailed` is also the error for a login id with no user (message "Failed to sign in, email does not exist"); there is no separate user-not-found error id.

- hidden in the console's action picker (still valid in a flow)
- tags: one time password, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `useRecoveryEmail` | boolean |  | argument | Send to recovery email; When enabled, send to the user's recovery email instead of their primary email. The action emits a specific error when the user has no recovery email set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `phone`, `email`, `externalId`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `lastAuth`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-otp-email`

**Sign Up or In / OTP / Email**. Enable users to sign up or in using OTP via Email. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInEmailFailed` (Error sending OTP code), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password, sign in, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `email` | string | yes | context | Email |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `locale`, `context`, `lastAuth`, `customClaims`, `startOptions`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-otp-email`

**Sign Up / OTP / Email**. Enable users to sign up using OTP via Email. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPSignUpOrInEmailFailed` (Error sending OTP code), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `email` | string | yes | context | Email |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `context`, `externalId`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-email-otp-embedded`

**Generate OTP Embedded Code for Update User Email**. Generate an OTP Code that can be sent later via connector for user email update, use {{embeddedCode}} for code in connector

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPUpdateEmailEmbeddedFailed` (Error generating code)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `emailVerified` | boolean |  | argument | Mark provided email as verified |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `externalId`, `email`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-otp-email`

**Update User / OTP / Email**. Update a user's email. Before doing so, verify the new email using OTP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OTPUpdateUserEmailFailed` (Error updating user), `OTPUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `email` | string | yes | context | Email |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `context`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-code-otp-email`

**Verify Code / OTP / Email**. Verify the code manually inputted by the user is the one that was generated as part of the OTP authentication.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OTPVerifyCodeEmailFailed` (Error verifying OTP code), `OTPVerifyCodeExpired` (OTP code expired), `OTPUpdateUserConflict` (User update failed due to conflict with existing user)

- hidden in the console's action picker (still valid in a flow)
- tags: one time password
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `code` | string | yes | context | Code |

Also reads from context when present: `tmpExternalId`, `externalId`, `email`, `password`, `lastAuth` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
