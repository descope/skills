# Actions: TOTP, nOTP, push, recovery codes, security questions

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `batch-remove-totp`

**User / Batch / Remove TOTP seed**. Remove the TOTP seed for selected users.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `BatchRemoveTOTPFailed` (Failed to batch remove TOTP), `BatchRemoveTOTPEmptyTenant` (Failed to get tenant for batch remove totp), `BatchRemoveTOTPSelectTenant` (Error fetching tenants from JWT), `BatchRemoveTOTPPermissions` (No valid permission for batch remove totp), `BatchRemoveTOTPUnauthorizedRequest` (Unauthorized request)

- tags: time based one time password, authenticator, reset, multi
- next interactionIds: `success`

Also reads from context when present: `context`, `tenant`, `userIds` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `recovery-codes-generate`

**Recovery Codes / Generate**. Generate recovery codes for a user.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `RecoveryCodesGenerateFailed` (Error in recovery codes generation)

- next interactionIds: `success`

Also reads from context when present: `externalId` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `remove-totp`

**Update User / Remove TOTP seed**. Remove the TOTP seed for an existing user.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `TOTPRemoveAllFailed` (Error removing TOTP), `TOTPUnauthorizedRequest` (Unauthorized request)

- tags: time based one time password, authenticator
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |

### `security-questions-setup`

**Security Questions / Setup**. Enable authenticated users to set up security questions.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SecurityQuestionsSetupQuestionsFailed` (Error in security questions setup)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `sqSetup` | object | yes | context | Security Questions Setup Answers |

Also reads from context when present: `externalId` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `security-questions-verify`

**Security Questions / Verify**. Enable authenticated users to verify their security questions.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `SecurityQuestionsVerifyUserLocked` (User is locked), `SecurityQuestionsVerifyInvalidAnswers` (Wrong answer), `SecurityQuestionsVerifyUserTemporarilyLocked` (User is temporarily locked), `SecurityQuestionsVerifyFailed` (Error in security questions verification)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `sqVerify` | object | yes | context | Security Questions Verification Answers |

Also reads from context when present: `externalId`, `stepUp` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-notp`

**Sign In / NOTP (WhatsApp)**. Enable users to sign up or in using NOTP. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `NOTPSignUpOrInFailed` (Error while using NOTP), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- console disables it unless `notp`
- tags: notp, whatsapp
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `autoRedirect` | boolean |  | argument | Auto Redirect In A New Tab; Automatically redirect the user to WhatsApp URL in a new tab |
| `providerId` | string |  | argument | Connector |
| `verifyTemplateId` | string |  | argument | Verify Template |
| `successTemplateId` | string |  | argument | Approval Template |
| `errorTemplateId` | string |  | argument | Error Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `phone`, `phone`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-push`

**Sign In / Push Notification**. Enable users to sign in using a push notification to a known device.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `PushNotificationSignInFailed` (Error sending push notification), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- tags: push, notification
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |

Also reads from context when present: `externalId`, `email`, `phone`, `customClaims`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-recovery-code`

**Sign In / Recovery Code**. Enable users to sign in using a recovery code.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `SignInRecoveryCodeFailed` (Error in recovery code sign in), `SignInRecoveryCodeUserTemporarilyLocked` (User is temporarily locked), `SignInRecoveryCodeUserLocked` (User is disabled), `SignInRecoveryCodeAlreadyUsed` (Recovery code already used), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `recoveryCode` | string | yes | context | Recovery Code |

Also reads from context when present: `externalId`, `stepUp`, `customClaims`, `context`, `lastAuth`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-totp`

**Sign In / TOTP**. Enable users to sign in using TOTP.

**Error ids**: none declared.

- **not runnable: the backend has no executor for it, and a task with this action fails the request with E010008. Never use it.**
- hidden in the console's action picker (still valid in a flow)
- tags: time based one time password, authenticator
- next interactionIds: `success`

No inputs.

### `sign-up-notp`

**Sign Up / NOTP (WhatsApp)**. Enable users to sign up using NOTP. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `NOTPSignUpOrInFailed` (Error while using NOTP)

- hidden in the console's action picker (still valid in a flow)
- console disables it unless `notp`
- tags: notp, whatsapp
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `autoRedirect` | boolean |  | argument | Auto Redirect In A New Tab; Automatically redirect the user to WhatsApp URL in a new tab |
| `providerId` | string |  | argument | Connector |
| `verifyTemplateId` | string |  | argument | Verify Template |
| `successTemplateId` | string |  | argument | Approval Template |
| `errorTemplateId` | string |  | argument | Error Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `phone`, `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-notp`

**Sign Up or In / NOTP (WhatsApp)**. Enable users to sign up or in using NOTP. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `NOTPSignUpOrInFailed` (Error while using NOTP), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- console disables it unless `notp`
- tags: notp, whatsapp
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `autoRedirect` | boolean |  | argument | Auto Redirect In A New Tab; Automatically redirect the user to WhatsApp URL in a new tab |
| `providerId` | string |  | argument | Connector |
| `verifyTemplateId` | string |  | argument | Verify Template |
| `successTemplateId` | string |  | argument | Approval Template |
| `errorTemplateId` | string |  | argument | Error Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `phone`, `externalId`, `context`, `startOptions`, `lastAuth`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-totp`

**Sign Up / TOTP**. Enable users to sign up using TOTP. A new user is created, along with its seed.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `TOTPSignUpFailed` (Error while using TOTP), `TOTPConfigSelectTenant` (Failed selecting tenant for TOTP configuration), `ConfigProvideTenant` (Provided tenant is not accessible)

- hidden in the console's action picker (still valid in a flow)
- tags: time based one time password, authenticator
- next interactionIds: `success`

Also reads from context when present: `externalId`, `email`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `startOptions`, `tenant`, `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-notp`

**Update User / NOTP (WhatsApp)**. Update a user's phone. Before doing so, verify the new phone using NOTP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `NOTPUpdateFailed` (Error while using NOTP), `NOTPUpdateUserConflict` (User update failed due to conflict with existing user), `NOTPUnauthorizedRequest` (Unauthorized request)

- hidden in the console's action picker (still valid in a flow)
- console disables it unless `notp`
- tags: notp, whatsapp
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `autoRedirect` | boolean |  | argument | Auto Redirect In A New Tab; Automatically redirect the user to WhatsApp URL in a new tab |
| `providerId` | string |  | argument | Connector |
| `verifyTemplateId` | string |  | argument | Verify Template |
| `successTemplateId` | string |  | argument | Approval Template |
| `errorTemplateId` | string |  | argument | Error Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `phone`, `context`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-totp`

**Update User / TOTP**. Create a seed for an existing user, so they can use an authenticator app.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `TOTPUpdateUserFailed` (Error updating user), `TOTPUnauthorizedRequest` (Unauthorized request), `TOTPConfigSelectTenant` (Failed selecting tenant for TOTP configuration), `ConfigProvideTenant` (Provided tenant is not accessible)

- hidden in the console's action picker (still valid in a flow)
- tags: time based one time password, authenticator
- next interactionIds: `success`

Also reads from context when present: `externalId`, `email`, `phone`, `authInfo`, `user`, `tenant`, `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-totp-code`

**Verify Code / TOTP**. Enable users to sign up or in using an authenticator app, based on a code that was received from it.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `TOTPVerifyCodeFailed` (Error verifying TOTP code), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `TOTPCodeReused` (Authenticator app code already used)

- hidden in the console's action picker (still valid in a flow)
- tags: time based one time password, authenticator
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `code` | string | yes | context | Code |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `email`, `phone`, `password`, `lastAuth`, `tmpExternalId`, `stepUp`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
