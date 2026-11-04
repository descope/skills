# Actions: Users

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `createFamily`

**Create Family**. Create a new family, and assign it to user

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorFamilyJWT` (Error in authorization phase), `ActionErrorFamilyNotEnabled` (Family feature is not enabled), `ActionErrorFamilyCreation` (Error creating new family), `ActionErrorFamilyGetDefaultRoles` (Error getting available roles), `ActionErrorFamilyAssignUser` (Error adding user to new family), `ActionErrorFamilyAssignRoles` (Error assigning family roles)

- needs project feature `families`
- tags: create, family
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `dynamicName` | string |  | argument | Family Name (will not override 'Family Name' end user input); value may be a context key |
| `skipCurrentUser` | boolean |  | argument | Do not add the current user to the new family |
| `familyRoles` | string |  | argument | Family roles for the current user (comma separated, defaults to Family Admin) |

Also reads from context when present: `context`, `familyName`, `familyPropertiesDefinitions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `createFamilyDependent`

**Family / Create Dependent**. Create a dependent user in the current user's family

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorFamilyJWT` (Error in authorization phase), `ActionErrorFamilyNotEnabled` (Family feature is not enabled), `ActionErrorFamilyNotResolved` (No family to create the dependent in), `ActionErrorFamilyNotMember` (User is not a member of the family), `ActionErrorFamilyDependentNoIdentifier` (Dependent requires a login ID or a name), `ActionErrorFamilyMembersLimit` (Family members limit exceeded), `ActionErrorFamilyDependentCreation` (Error creating dependent user)

- needs project feature `families`
- tags: create, family, dependent
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `familyId` | string |  | argument | Family ID (defaults to the flow's family or the user's current family); value may be a context key |
| `dependentName` | string |  | argument | Dependent name; value may be a context key |
| `dependentLoginId` | string |  | argument | Dependent login ID (derived from the name when empty); value may be a context key |
| `dependentEmail` | string |  | argument | Dependent email; value may be a context key |
| `dependentPhone` | string |  | argument | Dependent phone; value may be a context key |

Also reads from context when present: `context`, `startOptions`, `dependentPropertiesDefinitions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `delete-user`

**User / Delete**. Delete the logged-in user

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorDeleteMe` (Failed to delete user)

- tags: delete, users
- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `delete-users`

**User / Batch / Delete**. Delete selected users

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `DeleteUsers` (Failed to delete users), `DeleteUsersPermissions` (No valid permission to delete user), `DeleteUsersSelectTenant` (Error fetching tenants from JWT), `DeleteUsersEmptyTenant` (No tenant associated with request)

- tags: delete, users, batch
- next interactionIds: `success`

Also reads from context when present: `context`, `startOptions`, `userIds` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `disable-user`

**User / Disable**. Disable a user. The user ID is extracted from the triggering event if present. For API-triggered flows, pass the user ID via options.input.userId in the HTTP call, or directly set client.userId

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `DisableUserFailed` (Failed to disable user), `DisableUserNoUserID` (No user ID provided)

- management flows: managementOnly
- tags: user, disable, status
- next interactionIds: `success`

Also reads from context when present: `triggeringEvent`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `enable-user`

**User / Enable**. Enable a user. The user ID is extracted from the triggering event if present. For API-triggered flows, pass the user ID via options.input.userId in the HTTP call, or directly set client.userId

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EnableUserFailed` (Failed to enable user), `EnableUserNoUserID` (No user ID provided)

- management flows: managementOnly
- tags: user, enable, status
- next interactionIds: `success`

Also reads from context when present: `triggeringEvent`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `invite-user-email`

**User / Invite**. Invite users via email, invited user will be added to tenant according to the inviter tenants

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `InviteUsers` (Error sending invite), `InviteUsersPermissions` (No valid permission to send an invite), `InviteUsersSelectTenant` (Error validating tenant)

- tags: invite, users
- docs: https://docs.descope.com/knowledgebase/general/inviteusers/#descope-flows
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `sendInvite` | string (boolean) |  | argument | Send an invitation to user; default `true` |
| `providerId` | string |  | argument | Connector; depends on `sendInvite` |
| `templateId` | string |  | argument | Template; depends on `sendInvite` |
| `inviteUrl` | string |  | argument | Invite URL; depends on `sendInvite`; value may be a context key |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys; depends on `sendInvite` |
| `invitees` | string | yes | context | Invitees |
| `roles` | array |  | argument | Roles |
| `appIds` | array |  | argument | Applications |
| `userPropertiesDefinitions` | list of `{key, type, value}` rows |  | argument | User properties to update in JSON format |
| `validateTenantAdmin` | boolean (radio) |  | argument | values: `{"Allow only tenant admins to invite": true}` |

Also reads from context when present: `startOptions`, `tenant`, `userSelectedTenant`, `context`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `load-selected-user`

**User / Load / Selected User**. Load selected user from management widget

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `LoadSelectedUserFailed` (Failed to load selected user), `LoadSelectedUserPermissions` (No valid permission to load selected user), `LoadSelectedUserSelectTenant` (Error fetching tenants from JWT), `LoadSelectedUserEmptyTenant` (No tenant associated with request)

- tags: load, user, selected
- next interactionIds: `success`

Also reads from context when present: `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `load-user-from-triggering-event`

**Load User / From Triggering Event**. Load user based on the triggering event's user ID

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorLoadUserFromTriggeringEventFailed` (Error loading user from triggering event), `ActionErrorLoadUserFromTriggeringEventNoUserID` (Error loading user from triggering event - missing user ID), `ActionErrorLoadUserFromTriggeringEventNoEvent` (Error loading user from triggering event - missing triggering event)

- management flows: managementOnly
- tags: load, user, event
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `triggeringEvent` | object | yes | context | Triggering Event |
| `loadInvalidUsers` | boolean |  | argument | Load Invalid Users; If set to true, users that are disabled or expired will be loaded as well. |

### `loadUser`

**Load User**. Load user from incoming refresh token, and make its data available for the rest of the flow

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorLoadUserJwtVerify` (Error verifying refresh token), `ActionErrorLoadUserNoUser` (Error finding associated user), `ActionErrorLoadUserFromJWTFailed` (Error getting and validating refresh token)

- member of `start-step-up`
- tags: load, user, refresh, token, stepup, step up
- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `stopFamilyImpersonation`

**Family / Stop Impersonation**. Stop family impersonation, get back a jwt of the acting family admin

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorStopFamilyImpersonationFailed` (Failed creating JWT for the acting family admin), `ActionErrorLoadUserNoUser` (Acting family admin does not exist or is disabled), `ActionErrorStopImpersonationJWTParseError` (Failed extracting the acting family admin from JWT), `ActionErrorFamilyNotEnabled` (Family feature is not enabled)

- needs project feature `families`
- tags: stop, impersonate, family
- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-properties`

**Update User / Attributes**. Update an authenticated user's attributes, such as display name. Define what user attribute to update with which dynamic value. In order to update a user's email or phone, use their dedicated steps.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `UpdateUserPropertiesFailed` (Error updating user properties)

- management flows: compatible
- tags: profile, details, attribute, attributes
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `userPropertiesDefinitions` | list of `{key, type, value}` rows | yes | argument | User properties to update in JSON format |

Also reads from context when present: `fullName`, `firstName`, `middleName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `authInfo`, `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-users-status`

**User / Batch / Update Status**. Update status of selected users

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `UpdateUsersStatusFailed` (Failed to update users status), `UpdateUsersStatusPermissions` (No valid permission to update users status), `UpdateUsersStatusSelectTenant` (Error fetching tenants from JWT), `UpdateUsersStatusEmptyTenant` (No tenant associated with request)

- tags: update, users, status, activate, disable, batch
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `status` | string (select) | yes | argument | New status; options: `enabled`, `disabled` |

Also reads from context when present: `context`, `startOptions`, `userIds` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `validate-email`

**Validate email address**. Validate email format and verify the domain has MX records.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorValidateEmailInvalidEmail` (Invalid email address)

- management flows: none
- tags: email, validation, format, domain
- next interactionIds: `success`

Also reads from context when present: `email` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
