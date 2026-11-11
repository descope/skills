# Actions: Enchanted link

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `sign-in-enchanted-link-email`

**Sign In / Enchanted Link / Email**. Enable users to sign in using Enchanted Link via Email. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified)

- member of `sign-in-enchanted-link-email-group`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `useRecoveryEmail` | boolean |  | argument | Send to recovery email; When enabled, send to the user's recovery email instead of their primary email. The action emits a specific error when the user has no recovery email set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `externalId`, `email`, `phone`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-enchanted-link-email-group`

**Sign In / Enchanted Link / Email**. Enable users to sign in using Enchanted Link via Email. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-in-enchanted-link-email`, `verify-enchanted-link`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `useRecoveryEmail` | boolean |  | argument | Send to recovery email; When enabled, send to the user's recovery email instead of their primary email. The action emits a specific error when the user has no recovery email set or it is not verified, so the flow can branch on that outcome. |
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `externalId`, `email`, `phone`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale`, `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-enchanted-link-sms`

**Sign In / Enchanted Link / SMS**. Enable users to sign in using Enchanted Link via SMS. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInPhoneFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified)

- member of `sign-in-enchanted-link-sms-group`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `externalId`, `email`, `phone`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-enchanted-link-sms-group`

**Sign In / Enchanted Link / SMS**. Enable users to sign in using Enchanted Link via SMS. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInPhoneFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-in-enchanted-link-sms`, `verify-enchanted-link`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `useRecoveryPhone` | boolean |  | argument | Send to recovery phone; When enabled, send to the user's recovery phone instead of their primary phone. The action emits a specific error when the user has no recovery phone set or it is not verified, so the flow can branch on that outcome. |
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `externalId`, `email`, `phone`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale`, `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-enchanted-link-email`

**Sign Up / Enchanted Link / Email**. Enable users to sign up using Enchanted Link via Email. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `sign-up-enchanted-link-email-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `email` | string | yes | context | Email |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |

Also reads from context when present: `externalId`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `pkceChallenge`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-enchanted-link-email-group`

**Sign Up / Enchanted Link / Email**. Enable users to sign up using Enchanted Link via Email. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-enchanted-link-email`, `verify-enchanted-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `email` | string | yes | context | Email |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `externalId`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `pkceChallenge`, `locale`, `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-enchanted-link-sms`

**Sign Up / Enchanted Link / SMS**. Enable users to sign up using Enchanted Link via SMS. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInPhoneFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `sign-up-enchanted-link-sms-group`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |

Also reads from context when present: `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `pkceChallenge`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-enchanted-link-sms-group`

**Sign Up / Enchanted Link / SMS**. Enable users to sign up using Enchanted Link via SMS. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInPhoneFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-enchanted-link-sms`, `verify-enchanted-link`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `externalId`, `email`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `context`, `startOptions`, `pkceChallenge`, `locale`, `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-enchanted-link-email`

**Sign Up or In / Enchanted Link / Email**. Enable users to sign up or in using Enchanted Link via Email. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `sign-up-or-in-enchanted-link-email-group`
- hidden in the console's action picker (still valid in a flow)
- tags: login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `email` | string | yes | context | Email |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-enchanted-link-email-group`

**Sign Up or In / Enchanted Link / Email**. Enable users to sign up or in using Enchanted Link via Email. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-or-in-enchanted-link-email`, `verify-enchanted-link`
- hidden in the console's action picker (still valid in a flow)
- tags: login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `email` | string | yes | context | Email |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `externalId`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale`, `sessionIdsToRevoke`, `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-enchanted-link-sms`

**Sign Up or In / Enchanted Link / SMS**. Enable users to sign up or in using Enchanted Link via SMS. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInPhoneFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `sign-up-or-in-enchanted-link-sms-group`
- hidden in the console's action picker (still valid in a flow)
- tags: login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-enchanted-link-sms-group`

**Sign Up or In / Enchanted Link / SMS**. Enable users to sign up or in using Enchanted Link via SMS. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkSignUpOrInPhoneFailed` (Error sending Enchanted Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-or-in-enchanted-link-sms`, `verify-enchanted-link`
- hidden in the console's action picker (still valid in a flow)
- tags: login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phone` | string | yes | context | Phone |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Enchanted Link action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `externalId`, `context`, `startOptions`, `lastAuth`, `pkceChallenge`, `locale`, `sessionIdsToRevoke`, `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-enchanted-link-email`

**Update User / Enchanted Link / Email**. Update a user's email. Before doing so, verify the new email using Enchanted Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkUpdateUserEmailFailed` (Error updating user), `EnchantedLinkUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `update-user-enchanted-link-email-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `email` | string | yes | context | Email |
| `externalId` | string | yes | context | External ID |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |

Also reads from context when present: `context`, `startOptions`, `authInfo`, `user`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-enchanted-link-email-group`

**Update User / Enchanted Link / Email**. Update a user's email. Before doing so, verify the new email using Enchanted Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkUpdateUserEmailFailed` (Error updating user), `EnchantedLinkUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `update-user-enchanted-link-email`, `verify-enchanted-link`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `email` | string | yes | context | Email |
| `externalId` | string | yes | context | External ID |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `context`, `startOptions`, `authInfo`, `user`, `locale`, `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-enchanted-link-sms`

**Update User / Enchanted Link / SMS**. Update a user's phone. Before doing so, verify the new phone using Enchanted Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkUpdateUserPhoneFailed` (Error updating user), `EnchantedLinkUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `update-user-enchanted-link-sms-group`
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

### `update-user-enchanted-link-sms-group`

**Update User / Enchanted Link / SMS**. Update a user's phone. Before doing so, verify the new phone using Enchanted Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnchantedLinkUpdateUserPhoneFailed` (Error updating user), `EnchantedLinkUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `update-user-enchanted-link-sms`, `verify-enchanted-link`
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
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `context`, `startOptions`, `authInfo`, `user`, `locale`, `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-enchanted-link`

**Verify Code / Enchanted Link**. Verify the enchanted link token is the one that was generated as part of the Enchanted Link authentication.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- member of `sign-in-enchanted-link-email-group`, `sign-in-enchanted-link-sms-group`, `sign-up-enchanted-link-email-group`, `sign-up-enchanted-link-sms-group`, `sign-up-or-in-enchanted-link-email-group`, `sign-up-or-in-enchanted-link-sms-group`, `update-user-enchanted-link-email-group`, `update-user-enchanted-link-sms-group`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `skipVerify`, `pkceVerifier` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-enchanted-linksingle`

**Verify Code / Enchanted Link**. Verify the enchanted link token is the one that was generated as part of the Enchanted Link authentication.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `EnchantedLinkVerifyFailed` (Error verifying Enchanted Link), `EnchantedLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `token` | string | yes | context | Token |
| `pendingRef` | string | yes | context | pendingRef |

Also reads from context when present: `pkceVerifier`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
