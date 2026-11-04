# Actions: Password

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `get-tenant-password-config`

**Tenant / Get Password Configuration**. Get a tenant's password configuration.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorGetTenantPasswordConfigFailed` (Error while getting tenant password config), `ActionErrorGetTenantPasswordConfigPermissions` (No valid permission to get tenant password configuration)

- tags: get, password, tenant
- next interactionIds: `success`

Also reads from context when present: `context`, `tenant`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-delete`

**Delete Password**. Delete the current password for a logged-in user.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordDeleteFailed` (Error in password delete), `PasswordDeleteFailedUnauthorized` (Unauthorized request)

- next interactionIds: `success`

Also reads from context when present: `externalId`, `email`, `phone` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-expire`

**Expire Password**. Expire the current password for a logged-in user.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordExpireFailed` (Error in password expire), `PasswordExpireFailedUnauthorized` (Unauthorized request)

- next interactionIds: `success`

Also reads from context when present: `externalId`, `email`, `phone` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-merge`

**Merge User / Password**. Merge logged in user with other password user.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordSignInFailed` (Error in password merge), `PasswordExpired` (Password Expired), `UserDisabled` (User is disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `UserTemporarilyLocked` (User is temporarily locked), `NoLoginID` (Missing login ID)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `password` | string | yes | context | Password |
| `loginType` | string (select) |  | argument | Merge By; options: `email`, `phone`, `loginId` |

Also reads from context when present: `externalId`, `email`, `phone`, `code`, `lastAuth`, `startOptions`, `currentAuth` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-replace`

**Replace Password**. Enable users to update their password using their current active password.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordReplaceFailed` (Error in password replace)

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `password` | string | yes | context | Password |
| `newPassword` | string | yes | context | NewPassword |

Also reads from context when present: `externalId`, `email`, `phone` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-replace-v2`

**Replace Password**. Enable users to update their password using their current active password.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordReplaceFailed` (Error in password replace), `UserDisabled` (User is disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `UserTemporarilyLocked` (User is temporarily locked)

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `password` | string | yes | context | Password |
| `newPassword` | string | yes | context | NewPassword |

Also reads from context when present: `externalId`, `email`, `phone` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-replace-v3`

**Replace Password**. Enable users to update their password using their current active password.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordReplaceFailed` (Error in password replace), `UserDisabled` (User is disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `UserTemporarilyLocked` (User is temporarily locked), `PasswordReplaceBadCredentials` (Incorrect current password), `PasswordReplaceReused` (Password has already been used), `PasswordReplaceInvalidPassword` (Invalid password)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `password` | string | yes | context | Password |
| `newPassword` | string | yes | context | NewPassword |

Also reads from context when present: `externalId`, `email`, `phone` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-send-reset`

**Send Password Reset**. Sends a password reset prompt according to the password settings in the console.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordSendResetFailed` (Error in password send reset), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified)

- member of `password-send-reset-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `uri` | string |  | argument | URI; value may be a context key |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `useRecoveryEmail` | boolean |  | argument | Send to recovery email; When enabled, send to the user's recovery email instead of their primary email. The action emits a specific error when the user has no recovery email set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `externalId`, `email`, `phone`, `context`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-send-reset-group`

**Send Password Reset**. Sends a password reset prompt according to the password settings in the console.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordSendResetFailed` (Error in password send reset), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `password-send-reset`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `uri` | string |  | argument | URI; value may be a context key |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `useRecoveryEmail` | boolean |  | argument | Send to recovery email; When enabled, send to the user's recovery email instead of their primary email. The action emits a specific error when the user has no recovery email set or it is not verified, so the flow can branch on that outcome. |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `email`, `phone`, `context`, `startOptions`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-sign-in`

**Sign In / Password**. Enable users to sign in using a password.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordSignInFailed` (Error in password sign in), `PasswordExpired` (Password Expired), `UserDisabled` (User is disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `UserTemporarilyLocked` (User is temporarily locked), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `password` | string | yes | context | Password |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `email`, `phone`, `code`, `lastAuth`, `startOptions`, `stepUp`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-sign-in-v2`

**Sign In / Password**. Enable users to sign in using a password.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordSignInFailed` (Error in password sign in), `PasswordExpired` (Password Expired), `UserDisabled` (User is disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `UserTemporarilyLocked` (User is temporarily locked), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `password` | string | yes | context | Password |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `email`, `phone`, `code`, `lastAuth`, `startOptions`, `stepUp`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-sign-up`

**Sign Up / Password**. Enable users to sign up using a password.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordSignUpFailed` (Error in password sign up)
Note: creates the user at once, enabled, with the password and `verifiedEmail` false, and signs them in; a later OTP or link step does not undo it, so a sign-up abandoned before the code leaves an unverified user with a password: check `user.verifiedEmail` after a password sign-in (checked end to end).

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `newPassword` | string | yes | context | NewPassword |
| `password` | string | yes | context | Password |
| `skipPasswordPolicy` | boolean |  | argument | Skip password policy (unsafe); Warning: creates the user even if the password does not meet the password policy, which weakens account security. Use only for migrating users whose existing password was already verified, and prompt them to change it later |

Also reads from context when present: `externalId`, `code`, `email`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `password-update`

**Update Password**. Enable authenticated users to update their password.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `PasswordUpdateFailed` (Error in password update)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `newPassword` | string | yes | context | NewPassword |
| `password` | string | yes | context | **NOT the current password: another name for the new one, used only when `newPassword` is empty; nothing checks the current password. Supply `newPassword`; `Required` is not enforced on either (checked end to end)**; Password |

Also reads from context when present: `externalId`, `email`, `phone`, `code` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `reset-tenant-password-config`

**Tenant / Reset Password Configuration**. Reset tenant's password configuration to project's defaults.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorResetTenantPasswordConfigFailed` (Error while resetting tenant password config), `ActionErrorResetTenantPasswordConfigPermissions` (No valid permission to reset tenant password configuration), `ActionErrorResetTenantPasswordConfigGetProjectConfigFailed` (Error fetching project config for tenant password reset), `ActionErrorUpdateTenantPasswordConfigEmptyTenant` (No tenant associated with request)

- tags: reset, tenant, password
- next interactionIds: `success`

Also reads from context when present: `context`, `tenant`, `startOptions`, `tenantPasswordSettings` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-tenant-password-config`

**Tenant / Update Password Configuration**. Update password settings for current tenant

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorUpdateTenantPasswordConfigFailed` (Failed to update tenant password configuration), `ActionErrorUpdateTenantPasswordConfigPermissions` (No valid permission to update tenant password configuration), `ActionErrorUpdateTenantPasswordConfigEmptyTenant` (No tenant associated with request), `ActionErrorUpdateTenantPasswordConfigOverrideByProject` (Some fields were not made more restrictive and can't be applied)

- tags: update, tenant, password
- next interactionIds: `success`

Also reads from context when present: `context`, `tenant`, `startOptions`, `tenantPasswordSettings`, `psEnabled`, `psMinLength`, `psLowercase`, `psUppercase`, `psNumber`, `psNonAlphanumeric`, `psExpiration`, `psExpirationWeeks`, `psReuse`, `psReuseAmount`, `psLock`, `psLockAttempts`, `psTempLock`, `psTempLockAttempts`, `psTempLockDuration`, `psEnableStrength`, `psPasswordStrengthScore` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
