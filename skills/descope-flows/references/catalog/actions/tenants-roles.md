# Actions: Tenants and roles

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `createTenant`

**Create Tenant**. Create a new tenant, and assign it to user

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `InvalidJWT` (Error in authorization phase), `TenantCreation` (Error creating new tenant), `TenantExists` (Tenant already exists), `GetDefaultRoles` (Error getting available roles), `AssignRoles` (Error user to new tenant), `ActionErrorParseCustomClaims` (Error parsing custom claims), `ActionErrorUpdateJWT` (Error updating jwt)

- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `dynamicName` | string |  | argument | Tenant Name (will not override 'Tenant Name' end user input); value may be a context key |
| `dynamicId` | string |  | argument | Tenant ID; value may be a context key |
| `parentId` | string |  | argument | Parent Tenant ID (leave empty for top level tenants); value may be a context key |
| `dynamicSelfProvision` | string |  | argument | Self Provision Domains (will override 'Self Provision Domain' end user input); value may be a context key |
| `tenantRoles` | string |  | argument | Tenant Roles (csv format) |
| `tenantPropertiesDefinitions` | list of `{key, type, value}` rows |  | argument | Tenant properties to update in JSON format |
| `setAsSelectedTenant` | boolean |  | argument | Set as selected tenant; If enabled, automatically set the newly created tenant as the selected tenant for the user; default `false` |

Also reads from context when present: `tenantName`, `tenantDomain`, `selfProvisionDomains`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `set-batch-user-roles`

**User / Batch / Set Roles**. Set roles for selected users (replaces existing roles)

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SetBatchUserRolesFailed` (Failed to set user roles), `SetBatchUserRolesPermissions` (No valid permission to set user roles), `SetBatchUserRolesSelectTenant` (Error fetching tenants from JWT), `SetBatchUserRolesEmptyTenant` (No tenant associated with request), `SetBatchUserRolesNoRolesProvided` (No roles provided for set user roles), `SetBatchUserRolesLoadRoles` (Failed to get roles for set user roles), `SetBatchUserRolesLoadUser` (Failed to load user for set user roles), `SetBatchUserRolesNoUsersSelected` (No users selected for set user roles)

- tags: update, users, set, role, batch
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `userIds` | array | yes | context | Users' IDs |

Also reads from context when present: `context`, `startOptions`, `userRoles` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `tenant-get-config`

**Tenant / Get Configuration**. Get a tenant configuration.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `GetTenantConfigFailed` (Error fetching tenants from JWT)

- management flows: compatible
- next interactionIds: `success`

Also reads from context when present: `tenant`, `startOptions`, `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `tenant-set-config`

**Tenant / Update Configuration**. Set tenant configuration.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SetTenantConfigFailed` (Error fetching tenants from JWT)

- management flows: compatible
- tags: tenant
- next interactionIds: `success`

Also reads from context when present: `tenant`, `selfProvisionDomains`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-dynamic-tenant`

**Update User / Add Tenant Dynamically (unsafe)**. Add a tenant to user using dynamic keys. This is potentially unsafe, as the tenant may be selected according to unverified user input

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorUpdateUserDynamicTenant` (Error associating user with tenant), `ActionErrorUpdateUserDynamicTenantNoTenant` (Tenant does not exists), `ActionErrorUpdateUserDynamicTenantNoUser` (Error loading associated user)
Note: `addTenant` may be a tenant id, name or domain (no match -> `ActionErrorUpdateUserDynamicTenantNoTenant`); a user already in the tenant passes as `success`. It does not set the context's `tenant`: a following tenant-level `user-add-roles` must name the tenant (see there) (adding by name checked end to end).

- tags: add, user, tenant
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `addTenant` | string | yes | argument | Tenant Name/ID; value may be a context key |

Also reads from context when present: `authInfo`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-roles`

**User / Edit Roles**. Edit roles for selected user

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `UpdateUserRolesFailed` (Failed to edit user roles), `UpdateUserRolesPermissions` (No valid permission to edit user roles), `UpdateUserRolesSelectTenant` (Error fetching tenants from JWT), `UpdateUserRolesEmptyTenant` (No tenant associated with request), `UpdateUserEditRolesLoadUser` (Failed to load user for edit roles), `UpdateUserRolesLoadRoles` (Failed to get roles for edit user roles), `UpdateUserRolesEmptyRoles` (No roles provided for edit user roles)

- tags: update, user, edit, role
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `userIds` | array | yes | context | Users' IDs |

Also reads from context when present: `context`, `startOptions`, `userRoles` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-user-tenant-email-domain`

**Update User / Add Tenant by Email Domain**. Add a tenant to user according to the user's email domain. The email must be valid and verified.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorUpdateUserTenantByEmailDomainNoUser` (Error loading associated user), `ActionErrorUpdateUserTenantByEmailDomainForbiddenEmail` (Error validating user email), `ActionErrorUpdateUserTenantByEmailDomainNoTenant` (Error finding matching tenant), `ActionErrorUpdateUserTenantByEmailDomain` (Error updating user tenant)

- tags: add, user, tenant, email, domain
- next interactionIds: `success`

Also reads from context when present: `authInfo`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-users-add-roles`

**User / Batch / Add Roles**. Add roles to selected users

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `UpdateUsersAddRolesFailed` (Failed to add users roles), `UpdateUsersAddRolesPermissions` (No valid permission to add users roles), `UpdateUsersAddRolesSelectTenant` (Error fetching tenants from JWT), `UpdateUsersAddRolesEmptyTenant` (No tenant associated with request), `UpdateUsersAddRolesLoadUser` (Failed to load user for add roles), `UpdateUsersAddRolesNoUsersSelected` (No users selected for add roles), `UpdateUsersAddRolesNoRolesProvided` (No roles provided for add roles)

- tags: update, users, add, role, batch
- next interactionIds: `success`

Also reads from context when present: `context`, `startOptions`, `userIds`, `userRoles` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-users-delete-roles`

**User / Batch / Remove Roles**. Remove roles from selected users

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `UpdateUsersDeleteRolesFailed` (Failed to remove users roles), `UpdateUsersDeleteRolesPermissions` (No valid permission to remove users roles), `UpdateUsersDeleteRolesSelectTenant` (Error fetching tenants from JWT), `UpdateUsersDeleteRolesEmptyTenant` (No tenant associated with request), `UpdateUsersDeleteRolesLoadUser` (Failed to load user for remove roles), `UpdateUsersDeleteRolesNoUsersSelected` (No users selected for remove roles), `UpdateUsersDeleteRolesNoRolesProvided` (No roles provided for remove roles)

- tags: update, users, delete, remove, role, batch
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `userIds` | array | yes | context | Users' IDs |

Also reads from context when present: `context`, `startOptions`, `userRoles` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `updateTenant`

**Update Tenant**. Update tenant attributes

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `InvalidJWT` (Error in authorization phase), `TenantUpdate` (Error updating tenant)

- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `tenantPropertiesDefinitions` | list of `{key, type, value}` rows | yes | argument | Tenant properties to update in JSON format |

Also reads from context when present: `tenant`, `startOptions`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `user-add-roles`

**Update User / Add Roles**. Add roles to user

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorAddRolesFailed` (Failed to Add roles), `ActionErrorAddRolesFailedDoNotExists` (Cannot validate user, before adding new roles)
Note: with `tenantLevel`, always pass a `tenant` argument with the tenant id. Without it the tenant is the context's `tenant`, else `startOptions.tenant`, else `userSelectedTenant`: right after `update-user-dynamic-tenant` that works only while the user has one tenant; a user already in another tenant fails with `ActionErrorAddRolesFailed` (checked end to end).

- tags: roles, users
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `roles` | array |  | argument | Roles to add to user; value may be a context key |
| `tenantLevel` | boolean (radio) |  | argument | values: `{"Add roles on tenant level": true}` |

Also reads from context when present: `startOptions`, `authInfo`, `context`, `tenant`, `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `user-remove-roles`

**Update User / Remove Roles**. Remove roles from user

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorRemoveRolesFailed` (Failed to remove roles), `ActionErrorRemoveRolesFailedDoNotExists` (Cannot validate user, before removing roles)

- tags: roles, users
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `roles` | array |  | argument | Roles to remove from user; value may be a context key |
| `tenantLevel` | boolean (radio) |  | argument | values: `{"Remove roles from tenant level": true}` |

Also reads from context when present: `startOptions`, `authInfo`, `context`, `tenant`, `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
