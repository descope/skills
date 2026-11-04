# Actions: Magic link by SMS or WhatsApp

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `sign-in-magic-linkv3-sms`

**Sign In / Magic Link / SMS**. Enable users to sign in using Magic Link via SMS. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `UserDoesNotExists` (User does not exist), `MagicLinkDestinationNotVerified` (Phone not verified)

- member of `sign-in-magic-linkv3-sms-group`
- hidden in the console's action picker (still valid in a flow)
- tags: login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `phone`, `email`, `externalId`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-magic-linkv3-sms-group`

**Sign In / Magic Link / SMS**. Enable users to sign in using Magic Link via SMS. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `UserDoesNotExists` (User does not exist), `MagicLinkDestinationNotVerified` (Phone not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-in-magic-linkv3-sms`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- tags: login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |
| `token` | string | yes | context | Token |

Also reads from context when present: `phone`, `email`, `externalId`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-magic-linkv3-whatsapp`

**sign-in-magic-linkv3-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `UserDoesNotExists` (User does not exist), `MagicLinkDestinationNotVerified` (Phone not verified)

- member of `sign-in-magic-linkv3-whatsapp-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `phone`, `email`, `externalId`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-magic-linkv3-whatsapp-group`

**sign-in-magic-linkv3-whatsapp-group**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `UserDoesNotExists` (User does not exist), `MagicLinkDestinationNotVerified` (Phone not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-in-magic-linkv3-whatsapp`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |
| `token` | string | yes | context | Token |

Also reads from context when present: `phone`, `email`, `externalId`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-magic-link-sms`

**Sign Up / Magic Link / SMS**. Enable users to sign up using Magic Link via SMS. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `sign-up-magic-link-sms-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |

Also reads from context when present: `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-magic-link-sms-group`

**Sign Up / Magic Link / SMS**. Enable users to sign up using Magic Link via SMS. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-magic-link-sms`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-magic-link-whatsapp`

**sign-up-magic-link-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link)

- member of `sign-up-magic-link-whatsapp-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |

Also reads from context when present: `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-magic-link-whatsapp-group`

**sign-up-magic-link-whatsapp-group**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-magic-link-whatsapp`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-magic-linkv3-sms`

**Sign Up or In / Magic Link / SMS**. Enable users to sign up or in using Magic Link via SMS. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `MagicLinkDestinationNotVerified` (Phone not verified)

- member of `sign-up-or-in-magic-linkv3-sms-group`
- hidden in the console's action picker (still valid in a flow)
- tags: login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `phone`, `email`, `externalId`, `context`, `startOptions`, `lastAuth`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-magic-linkv3-sms-group`

**Sign Up or In / Magic Link / SMS**. Enable users to sign up or in using Magic Link via SMS. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `MagicLinkDestinationNotVerified` (Phone not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-or-in-magic-linkv3-sms`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- tags: login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `token` | string | yes | context | Token |

Also reads from context when present: `phone`, `email`, `externalId`, `context`, `startOptions`, `lastAuth`, `locale`, `sessionIdsToRevoke`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-magic-linkv3-whatsapp`

**sign-up-or-in-magic-linkv3-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `MagicLinkDestinationNotVerified` (Phone not verified)

- member of `sign-up-or-in-magic-linkv3-whatsapp-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `context`, `startOptions`, `lastAuth`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-magic-linkv3-whatsapp-group`

**sign-up-or-in-magic-linkv3-whatsapp-group**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `MagicLinkDestinationNotVerified` (Phone not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-or-in-magic-linkv3-whatsapp`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `context`, `startOptions`, `lastAuth`, `locale`, `sessionIdsToRevoke`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `start-verify-recovery-magic-link-sms`

**Verify Recovery Phone / Magic Link / SMS**. Send a magic link via SMS to a recovery phone so the user can verify it. The action returns immediately and the user completes verification in a separate flow.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `StartRecoveryVerificationFailed` (Error starting recovery verification), `RecoveryDestinationMissing` (Recovery phone is not set on the user), `MagicLinkMisconfiguration` (Verification URL is not configured), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- tags: recovery, magic link
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Recovery Template |
| `verifyFlowId` | string (recoveryVerifyDestination) |  | argument | Recovery verification destination |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `verifyURL`, `recoveryPhone`, `context`, `authInfo`, `user`, `locale`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-magic-link-sms`

**Update User / Magic Link / SMS**. Update a user's phone. Before doing so, verify the new phone using Magic Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkUpdateUserPhoneFailed` (Error updating user), `MagicLinkUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `update-user-magic-link-sms-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `externalId` | string | yes | context | External ID |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `context`, `startOptions`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-magic-link-sms-group`

**Update User / Magic Link / SMS**. Update a user's phone. Before doing so, verify the new phone using Magic Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkUpdateUserPhoneFailed` (Error updating user), `MagicLinkUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `update-user-magic-link-sms`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `externalId` | string | yes | context | External ID |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |
| `token` | string | yes | context | Token |

Also reads from context when present: `context`, `startOptions`, `authInfo`, `user`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-magic-link-whatsapp`

**update-user-magic-link-whatsapp**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkUpdateUserPhoneFailed` (Error updating user), `MagicLinkUnauthorizedRequest` (Unauthorized request)

- member of `update-user-magic-link-whatsapp-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `externalId` | string | yes | context | External ID |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `context`, `startOptions`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-magic-link-whatsapp-group`

**update-user-magic-link-whatsapp-group**.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkUpdateUserPhoneFailed` (Error updating user), `MagicLinkUnauthorizedRequest` (Unauthorized request), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `update-user-magic-link-whatsapp`, `verify-magic-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `externalId` | string | yes | context | External ID |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |
| `token` | string | yes | context | Token |

Also reads from context when present: `context`, `startOptions`, `authInfo`, `user`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
