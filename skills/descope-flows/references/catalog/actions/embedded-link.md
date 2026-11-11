# Actions: Embedded link

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `sign-in-embedded-link`

**Sign In / Embedded Link**. Enable users to sign in using Embedded Link via Email.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EmbeddedLinkSignUpOrInFailed` (Error generating Embedded Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- member of `sign-in-embedded-link-group`
- hidden in the console's action picker (still valid in a flow)
- tags: login, token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `timeout` | number |  | argument | Token expiration time (in minutes) |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `email`, `phone`, `customClaims`, `startOptions`, `lastAuth`, `context`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-embedded-link-group`

**Sign In / Embedded Link**. Enable users to sign in using Embedded Link via Email.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EmbeddedLinkSignUpOrInFailed` (Error generating Embedded Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Embedded Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-in-embedded-link`, `verify-magic-link`
- tags: login, token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `timeout` | number |  | argument | Token expiration time (in minutes) |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `email`, `phone`, `customClaims`, `startOptions`, `lastAuth`, `context`, `sessionIdsToRevoke`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-in-embedded-linkmgmt`

**Sign In / Embedded Link**. Enable users to sign in using Embedded Link via Email.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EmbeddedLinkSignUpOrInFailed` (Error generating Embedded Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- declared id `sign-in-embedded-link` (GetActionCatalog shows that one; tasks use `sign-in-embedded-linkmgmt`)
- management flows: managementOnly
- tags: login, token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `timeout` | number |  | argument | Token expiration time (in minutes) |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `email`, `phone`, `customClaims`, `startOptions`, `lastAuth`, `context`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-embedded-link`

**Sign Up / Embedded Link**. Enable users to sign up using Embedded Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EmbeddedLinkSignUpFailed` (Error generating Embedded Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- member of `sign-up-embedded-link-group`
- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- tags: login, token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `emailVerified` | boolean |  | argument | Mark provided email as verified |
| `phoneVerified` | boolean |  | argument | Mark provided phone as verified |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `timeout` | number |  | argument | Token expiration time (in minutes) |

Also reads from context when present: `externalId`, `email`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `startOptions`, `lastAuth`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-embedded-link-group`

**Sign Up / Embedded Link**. Enable users to sign up using Embedded Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EmbeddedLinkSignUpFailed` (Error generating Embedded Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Embedded Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-embedded-link`, `verify-magic-link`
- tags: login, token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `emailVerified` | boolean |  | argument | Mark provided email as verified |
| `phoneVerified` | boolean |  | argument | Mark provided phone as verified |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `timeout` | number |  | argument | Token expiration time (in minutes) |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `email`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `startOptions`, `lastAuth`, `context`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-embedded-link`

**Sign Up or In / Embedded Link**. Enable users to sign up or in using Embedded Link. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EmbeddedLinkSignUpOrInFailed` (Error generating Embedded Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- member of `sign-up-or-in-embedded-link-group`
- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- tags: login, token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `emailVerified` | boolean |  | argument | Mark provided email as verified (sign up only) |
| `phoneVerified` | boolean |  | argument | Mark provided phone as verified (sign up only) |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `timeout` | number |  | argument | Token expiration time (in minutes) |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `externalId`, `email`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `startOptions`, `lastAuth`, `context`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sign-up-or-in-embedded-link-group`

**Sign Up or In / Embedded Link**. Enable users to sign up or in using Embedded Link. Users that try to sign in but don't exist in the Descope users table will be automatically created.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EmbeddedLinkSignUpOrInFailed` (Error generating Embedded Link), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Embedded Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `sign-up-or-in-embedded-link`, `verify-magic-link`
- tags: login, token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `emailVerified` | boolean |  | argument | Mark provided email as verified (sign up only) |
| `phoneVerified` | boolean |  | argument | Mark provided phone as verified (sign up only) |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `timeout` | number |  | argument | Token expiration time (in minutes) |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `email`, `phone`, `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `customClaims`, `startOptions`, `lastAuth`, `context`, `sessionIdsToRevoke`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-email-embedded-link`

**Update User / Embedded Link / Email**. Update a user's email. Before doing so, verify the new email using an Embedded Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorEmbeddedLinkUpdateUser` (Error generating Embedded Link), `ActionErrorEmbeddedLinkUnauthorizedRequest` (Error validating user jwt)

- member of `update-user-email-embedded-link-group`
- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- tags: token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `emailVerified` | boolean |  | argument | Mark provided email as verified |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |
| `timeout` | number |  | argument | Token expiration time (in minutes) |

Also reads from context when present: `externalId`, `email`, `startOptions`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-email-embedded-link-group`

**Update User / Embedded Link / Email**. Update a user's email. Before doing so, verify the new email using an Embedded Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorEmbeddedLinkUpdateUser` (Error generating Embedded Link), `ActionErrorEmbeddedLinkUnauthorizedRequest` (Error validating user jwt), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Embedded Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `update-user-email-embedded-link`, `verify-magic-link`
- tags: token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `emailVerified` | boolean |  | argument | Mark provided email as verified |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |
| `timeout` | number |  | argument | Token expiration time (in minutes) |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `email`, `startOptions`, `context`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-phone-embedded-link`

**Update User / Embedded Link / Phone**. Update a user's phone. Before doing so, verify the new phone using an Embedded Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorEmbeddedLinkUpdateUser` (Error generating Embedded Link), `ActionErrorEmbeddedLinkUnauthorizedRequest` (Error validating user jwt)

- member of `update-user-phone-embedded-link-group`
- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- tags: token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phoneVerified` | boolean |  | argument | Mark provided phone as verified |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |
| `timeout` | number |  | argument | Token expiration time (in minutes) |

Also reads from context when present: `externalId`, `phone`, `startOptions`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-phone-embedded-link-group`

**Update User / Embedded Link / Phone**. Update a user's phone. Before doing so, verify the new phone using an Embedded Link.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorEmbeddedLinkUpdateUser` (Error generating Embedded Link), `ActionErrorEmbeddedLinkUnauthorizedRequest` (Error validating user jwt), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Embedded Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- **group (console shorthand, never a task action)**: write the members as tasks `update-user-phone-embedded-link`, `verify-magic-link`
- tags: token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `phoneVerified` | boolean |  | argument | Mark provided phone as verified |
| `verifyStepId` | string | yes | argument | Verification Step ID |
| `uri` | string |  | argument | URI; value may be a context key |
| `addToLoginIDs` | boolean |  | argument | Add to login IDs |
| `onMergeUseExisting` | any (radio) |  | argument | values: `{"Upon merge use existing user's value": true}` |
| `timeout` | number |  | argument | Token expiration time (in minutes) |
| `token` | string | yes | context | Token |

Also reads from context when present: `externalId`, `phone`, `startOptions`, `context`, `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-embedded-link`

**Verify Token**. Verify a token that was generated outside a flow

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying token), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)

- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `token` | string | yes | context | Token |
| `deleteTokenAtFlowEnd` | boolean |  | argument | Delete token only at the end of the flow; Tokens are deleted right after usage by default. Enable this setting to keep the token valid until the flow's execution ends. |

Also reads from context when present: `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
