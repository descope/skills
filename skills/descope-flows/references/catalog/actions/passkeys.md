# Actions: Passkeys (WebAuthn)

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `webauthn-remove`

**Update User / Remove Passkey (WebAuthn)**. Remove a single user passkey by its credential ID.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnRemoveFailed` (Failed to remove passkey), `WebauthnUnauthorizedRequest` (Unauthorized request)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `credentialId` | string | yes | context | Credential ID |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-remove-all`

**Update User / Remove All Passkeys (WebAuthn)**. Remove all user's registered passkeys.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnRemoveAllFailed` (Failed to remove all passkeys), `WebauthnUnauthorizedRequest` (Unauthorized request)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |

### `webauthn-sign-in`

**Sign In / Passkeys (WebAuthn)**. Enable users to sign in using Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnSignInStartFailed` (Error in Passkeys (WebAuthn) authorization phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `WebauthnSignInFinishFailed` (Error in Passkeys (WebAuthn) challenge phase), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `webauthn-sign-in-start`, `webauthn-sign-in-finish`
- hidden in the console's action picker (still valid in a flow)
- tags: biometrics, passkeys, webauthn, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `externalId`, `phone`, `email`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `transactionId`, `response`, `lastAuth`, `startOptions`, `failure`, `failureReason`, `failureMessage`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-in-finish`

**Sign In / Passkeys (WebAuthn) / Finish**. Completes the authentication process of existing users using Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `WebauthnSignInFinishFailed` (Error in Passkeys (WebAuthn) challenge phase), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- member of `webauthn-sign-in`, `webauthn-sign-in-v2`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `failure`, `failureReason`, `failureMessage`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-in-start`

**Sign In / Passkeys (WebAuthn) / Start**. Enable users to sign in using Passkeys (WebAuthn). Starts the authentication process.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnSignInStartFailed` (Error in Passkeys (WebAuthn) authorization phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- member of `webauthn-sign-in`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |

Also reads from context when present: `externalId`, `phone`, `email`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `transactionId`, `response`, `lastAuth`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-in-start-v2`

**Sign In / Passkeys (WebAuthn) / Start**. Enable users to sign in using Passkeys (WebAuthn). Starts the authentication process.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnSignInStartFailed` (Error in Passkeys (WebAuthn) authorization phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `UserDoesNotExists` (User does not exist)

- member of `webauthn-sign-in-v2`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |

Also reads from context when present: `externalId`, `phone`, `email`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `transactionId`, `response`, `lastAuth`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-in-v2`

**Sign In / Passkeys (WebAuthn)**. Enable users to sign in using Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnSignInStartFailed` (Error in Passkeys (WebAuthn) authorization phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `UserDoesNotExists` (User does not exist), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `WebauthnSignInFinishFailed` (Error in Passkeys (WebAuthn) challenge phase), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `webauthn-sign-in-start-v2`, `webauthn-sign-in-finish`
- tags: biometrics, passkeys, webauthn, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `externalId`, `phone`, `email`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `transactionId`, `response`, `lastAuth`, `startOptions`, `failure`, `failureReason`, `failureMessage`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-up`

**Sign Up / Passkeys (WebAuthn)**. Enable users to sign up using Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnSignUpStartFailed` (Error in Passkeys (WebAuthn) authorization phase), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `WebauthnSignUpFinishFailed` (Error in Passkeys (WebAuthn) challenge phase), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `webauthn-sign-up-start`, `webauthn-sign-up-finish`
- tags: biometrics, passkeys, webauthn
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |
| `restrictPasskeyTypes` | string (select) |  | argument | Restrict types of passkeys; Platform passkeys are stored on their device or profile. External passkeys are non-integrated authenticators such as security keys or mobile devices over a Bluetooth connection.; options: ``, `platform`, `external` |
| `passkeyDisplayName` | string |  | argument | Passkey Label; Label the browser and the device keychain show for this passkey. Leave empty to derive it from the user's name, email or phone.; value may be a context key |
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `externalId`, `phone`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `failure`, `failureReason`, `failureMessage` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-up-finish`

**Sign Up / Passkeys (WebAuthn) / Finish**. Completes the registration process of new users using Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `WebauthnSignUpFinishFailed` (Error in Passkeys (WebAuthn) challenge phase), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- member of `webauthn-sign-up`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `failure`, `failureReason`, `failureMessage` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-up-or-in`

**Sign Up or In / Passkeys (WebAuthn)**. Enable users to sign up or in using Passkeys (WebAuthn). Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnSignUpOrInStartFailed` (Error in Passkeys (WebAuthn) authorization phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `WebauthnSignUpOrInFinishFailed` (Error in Passkeys (WebAuthn) challenge phase), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `webauthn-sign-up-or-in-start`, `webauthn-sign-up-or-in-finish`
- tags: biometrics, passkeys, webauthn, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |
| `restrictPasskeyTypes` | string (select) |  | argument | Restrict types of passkeys; Platform passkeys are stored on their device or profile. External passkeys are non-integrated authenticators such as security keys or mobile devices over a Bluetooth connection.; options: ``, `platform`, `external` |
| `passkeyDisplayName` | string |  | argument | Passkey Label; Label the browser and the device keychain show for this passkey. Leave empty to derive it from the user's name, email or phone.; value may be a context key |
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `externalId`, `phone`, `email`, `transactionId`, `response`, `lastAuth`, `context`, `startOptions`, `failure`, `failureReason`, `failureMessage`, `webauthn` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-up-or-in-finish`

**Sign Up or In / Passkeys (WebAuthn) / Finish**. Completes the authentication process of new or existing users using Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `WebauthnSignUpOrInFinishFailed` (Error in Passkeys (WebAuthn) challenge phase), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- member of `webauthn-sign-up-or-in`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `failure`, `failureReason`, `failureMessage`, `webauthn` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-up-or-in-start`

**Sign Up or In / Passkeys (WebAuthn) / Start**. Enable users to sign up or in using Passkeys (WebAuthn). Starts the authentication process.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnSignUpOrInStartFailed` (Error in Passkeys (WebAuthn) authorization phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- member of `webauthn-sign-up-or-in`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |
| `restrictPasskeyTypes` | string (select) |  | argument | Restrict types of passkeys; Platform passkeys are stored on their device or profile. External passkeys are non-integrated authenticators such as security keys or mobile devices over a Bluetooth connection.; options: ``, `platform`, `external` |
| `passkeyDisplayName` | string |  | argument | Passkey Label; Label the browser and the device keychain show for this passkey. Leave empty to derive it from the user's name, email or phone.; value may be a context key |

Also reads from context when present: `externalId`, `phone`, `email`, `transactionId`, `response`, `lastAuth`, `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-sign-up-start`

**Sign Up / Passkeys (WebAuthn) / Start**. Enable users to sign up using Passkeys (WebAuthn). Start the registration process.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnSignUpStartFailed` (Error in Passkeys (WebAuthn) authorization phase)

- member of `webauthn-sign-up`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |
| `restrictPasskeyTypes` | string (select) |  | argument | Restrict types of passkeys; Platform passkeys are stored on their device or profile. External passkeys are non-integrated authenticators such as security keys or mobile devices over a Bluetooth connection.; options: ``, `platform`, `external` |
| `passkeyDisplayName` | string |  | argument | Passkey Label; Label the browser and the device keychain show for this passkey. Leave empty to derive it from the user's name, email or phone.; value may be a context key |

Also reads from context when present: `externalId`, `phone`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-update-user`

**Update User / Passkeys (WebAuthn)**. Update a user's device list, by providing an option to register it via Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnUnauthorizedRequest` (Unauthorized request), `WebauthnInvalidPasskeyLoginId` (Passkey login ID does not belong to the user), `WebauthnCredentialAlreadyAdded` (Device already has a passkey), `WebauthnUpdateUserFinishFailed` (Error updating user), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `webauthn-update-user-start`, `webauthn-update-user-finish`
- tags: biometrics, passkeys, webauthn
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `passkeyLoginId` | string |  | argument | Passkey Login ID; Which of the user's login IDs the passkey is registered against. Must be one of that user's own login IDs. Leave empty to use the login ID from the preceding authentication or step-up.; value may be a context key |
| `passkeyDisplayName` | string |  | argument | Passkey Label; Label the browser and the device keychain show for this passkey. Leave empty to derive it from the user's name, email or phone.; value may be a context key |
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |
| `restrictPasskeyTypes` | string (select) |  | argument | Restrict types of passkeys; Platform passkeys are stored on their device or profile. External passkeys are non-integrated authenticators such as security keys or mobile devices over a Bluetooth connection.; options: ``, `platform`, `external` |
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `tmpExternalId`, `context`, `startOptions`, `failure`, `failureReason`, `failureMessage` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-update-user-finish`

**Update User / Passkeys (WebAuthn) / Finish**. Completes the registration of the user's new device via Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnCredentialAlreadyAdded` (Device already has a passkey), `WebauthnUpdateUserFinishFailed` (Error updating user), `WebauthnFailed` (Authentication aborted), `WebauthnCanceled` (Passkey canceled)

- member of `webauthn-update-user`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `transactionId` | string | yes | context | Transaction ID |
| `response` | string | yes | context | Response |

Also reads from context when present: `failure`, `failureReason`, `failureMessage` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `webauthn-update-user-start`

**Update User / Passkeys (WebAuthn) / Start**. Update a user's device list, by providing an option to register it via Passkeys (WebAuthn).

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `WebauthnUnauthorizedRequest` (Unauthorized request), `WebauthnInvalidPasskeyLoginId` (Passkey login ID does not belong to the user)

- member of `webauthn-update-user`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `externalId` | string | yes | context | External ID |
| `passkeyLoginId` | string |  | argument | Passkey Login ID; Which of the user's login IDs the passkey is registered against. Must be one of that user's own login IDs. Leave empty to use the login ID from the preceding authentication or step-up.; value may be a context key |
| `passkeyDisplayName` | string |  | argument | Passkey Label; Label the browser and the device keychain show for this passkey. Leave empty to derive it from the user's name, email or phone.; value may be a context key |
| `origin` | string | yes | context | Origin |
| `finishStepId` | string | yes | argument | Finish Step ID |
| `userVerificationDiscouraged` | boolean |  | argument | Allow passkeys without user verification; Enable to allow users to authenticate using passkeys without biometrics or using security keys without a PIN. |
| `restrictPasskeyTypes` | string (select) |  | argument | Restrict types of passkeys; Platform passkeys are stored on their device or profile. External passkeys are non-integrated authenticators such as security keys or mobile devices over a Bluetooth connection.; options: ``, `platform`, `external` |

Also reads from context when present: `tmpExternalId`, `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
