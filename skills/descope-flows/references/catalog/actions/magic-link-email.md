# Actions: Magic link by email

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `sign-in-magic-linkv3-email`

**Sign In / Magic Link / Email**. Enable users to sign in using Magic Link via Email. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `UserDoesNotExists` (User does not exist), `MagicLinkDestinationNotVerified` (Email not verified)

- member of `sign-in-magic-linkv3-email-group`
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
| `useRecoveryEmail` | boolean |  | argument | Send to recovery email; When enabled, send to the user's recovery email instead of their primary email. The action emits a specific error when the user has no recovery email set or it is not verified, so the flow can branch on that outcome. |

Also reads from context when present: `externalId`, `email`, `phone`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-magic-linkv3-email-group`

**Sign In / Magic Link / Email**. Enable users to sign in using Magic Link via Email. Users that try to sign in but don't exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `SignInRecoveryDestinationNotSet` (Recovery destination not set), `SignInRecoveryDestinationNotVerified` (Recovery destination not verified), `UserDoesNotExists` (User does not exist), `MagicLinkDestinationNotVerified` (Email not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-in-magic-linkv3-email`, `verify-magic-link`
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
| `useRecoveryEmail` | boolean |  | argument | Send to recovery email; When enabled, send to the user's recovery email instead of their primary email. The action emits a specific error when the user has no recovery email set or it is not verified, so the flow can branch on that outcome. |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `email`, `phone`, `stepUp`, `sessionIdsToRevoke`, `customClaims`, `context`, `startOptions`, `lastAuth`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-magic-link-email`

**Sign Up / Magic Link / Email**. Enable users to sign up using Magic Link via Email. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)
Note: the user is created only when the link is verified, with `verifiedEmail` true; a link never opened leaves no user (checked end to end).

- member of `sign-up-magic-link-email-group`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |

Also reads from context when present: `externalId`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `context`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-magic-link-email-group`

**Sign Up / Magic Link / Email**. Enable users to sign up using Magic Link via Email. Users that try to sign up but already exist in the Descope users table will receive an error.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)
Note: the user is created only when the link is verified, with `verifiedEmail` true; a link never opened leaves no user (checked end to end).

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-magic-link-email`, `verify-magic-link`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `context`, `startOptions`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-magic-linkv3-email`

**Sign Up or In / Magic Link / Email**. Enable users to sign up or in using Magic Link via Email. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `MagicLinkDestinationNotVerified` (Email not verified)
Note: a new user is created only when the link is verified, with `verifiedEmail` true; a link never opened leaves no user (checked end to end).

- member of `sign-up-or-in-magic-linkv3-email-group`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `context`, `customClaims`, `startOptions`, `lastAuth`, `locale`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-magic-linkv3-email-group`

**Sign Up or In / Magic Link / Email**. Enable users to sign up or in using Magic Link via Email. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkSignUpOrInFailed` (Error sending Magic Link), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `MagicLinkDestinationNotVerified` (Email not verified), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)
Note: a new user is created only when the link is verified, with `verifiedEmail` true; a link never opened leaves no user (checked end to end).

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-or-in-magic-linkv3-email`, `verify-magic-link`
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
| `skipVerify` | boolean |  | argument | Custom Token Verification; Use a dedicated Verify Token action. Use this option to include additional conditions before verification |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `context`, `customClaims`, `startOptions`, `lastAuth`, `locale`, `sessionIdsToRevoke`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `start-verify-recovery-magic-link-email`

**Verify Recovery Email / Magic Link**. Send a magic link to a recovery email so the user can verify it. The action returns immediately and the user completes verification in a separate flow.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `StartRecoveryVerificationFailed` (Error starting recovery verification), `RecoveryDestinationMissing` (Recovery email is not set on the user), `MagicLinkMisconfiguration` (Verification URL is not configured), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- tags: recovery, magic link
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Recovery Template |
| `verifyFlowId` | string (recoveryVerifyDestination) |  | argument | Recovery verification destination |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `verifyURL`, `recoveryEmail`, `context`, `authInfo`, `user`, `locale`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-magic-link-email`

**Update User / Magic Link / Email**. Update a user's email. Before doing so, verify the new email using Magic Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkUpdateUserEmailFailed` (Error updating user), `MagicLinkUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded)

- member of `update-user-magic-link-email-group`
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

### `update-user-magic-link-email-group`

**Update User / Magic Link / Email**. Update a user's email. Before doing so, verify the new email using Magic Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `MagicLinkUpdateUserEmailFailed` (Error updating user), `MagicLinkUnauthorizedRequest` (Unauthorized request), `ActionErrorRateLimitExceeded` (Rate Limit Exceeded), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `update-user-magic-link-email`, `verify-magic-link`
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

Also reads from context when present: `context`, `startOptions`, `authInfo`, `user`, `locale`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
