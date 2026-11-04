# Actions: SSO: SAML, OIDC, SCIM, tenant SSO configuration

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `exchange-saml-code`

**SSO / Exchange**. Second step of a SSO authentication - get user groups.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `SSSOExchangeCodeFailed` (Error in SSO exchange phase), `SAMLExchangeCodeFailed` (Error in SSO SAML exchange phase), `OAuthExchangeCodeFailed` (Error in SSO OAuth exchange phase), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure)

- member of `saml`, `sso-no-user`, `sso-test`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeCode` | string | yes | context | Exchange Code |
| `ssoExchangeTenantId` | string | yes | context | SSO Exchange Tenant Id |

Also reads from context when present: `exchangeError`, `provider`, `ssoAuthType`, `lastAuth`, `fetchIDPGroups` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oidc-get-config`

**SSO / Get OIDC Configuration**. Get a tenant's SSO OIDC configuration.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `GetOIDCConfigFailed` (Error while getting SSO OIDC), `OIDCConfigSelectTenant` (Error fetching tenants from JWT), `ConfigProvideTenant` (Insufficient permission to tenant)

- management flows: compatible
- tags: oidc, single sign on
- next interactionIds: `success`

Also reads from context when present: `tenant`, `userSelectedTenant`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oidc-set-config`

**SSO / Set OIDC Configuration**. Set a tenant's SSO OIDC configuration.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SetOIDCConfigFailed` (Error while configuring SSO OIDC), `OIDCConfigSelectTenant` (Error fetching tenants from JWT), `ConfigProvideTenant` (Insufficient permission to tenant)

- management flows: compatible
- tags: oidc, single sign on
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerName` | string | yes | context | Provider Name |
| `clientId` | string | yes | context | Client ID |
| `authUrl` | string | yes | context | Auth URL |
| `tokenUrl` | string | yes | context | TokenURL |
| `grantType` | string | yes | context | GrantType |

Also reads from context when present: `tenant`, `userSelectedTenant`, `tenantDomains`, `redirectUrl`, `clientSecret`, `userDataUrl`, `jwksUrl`, `scope`, `manageProviderTokens`, `callbackDomain`, `prompt`, `issuer`, `oidcMappings`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `saml`

**SSO**. SSO authentication, via SAML or OIDC. Returns the identified user with its attributes from the SSO server.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SSOStartFailed` (Error in SSO authorization phase), `SAMLStartFailed` (Error in SSO SAML authorization phase), `OAuthStartFailed` (Error in SSO OAuth authorization phase), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `SSSOExchangeCodeFailed` (Error in SSO exchange phase), `SAMLExchangeCodeFailed` (Error in SSO SAML exchange phase), `OAuthExchangeCodeFailed` (Error in SSO OAuth exchange phase), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure)

- **group (console shorthand, never a task action)**: write the members as tasks `saml-start`, `exchange-saml-code`
- tags: saml, single sign on, oidc
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `redirectUrl` | string |  | argument | Redirect URL (Optional); The default URL the end user is redirected to after a successful SSO sign-in.; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt (OIDC only); Specify how the Authorization Server prompts the end user for authentication and consent. Relevant for OIDC SSO only.; options: `none`, `login`, `consent`, `select_account` |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `exchangeCode` | string | yes | context | Exchange Code |
| `forceAuthn` | boolean |  | argument | Force Authentication (SAML only); If enabled, forces the IdP to re-authenticate the user, even if a session already exists (SAML only) |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `verifyInitiatedEmail` | boolean |  | argument | Verify initiated email matches IdP response; Enable to verify that the email provided in the initiation phase matches the email returned by the Identity Provider. |
| `fetchIDPGroups` | boolean |  | argument | Fetch user's IdP Groups from SCIM; When enabled, SCIM-provisioned groups are fetched for the user and merged with any groups received from the IdP during the SSO exchange. |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeCode` | string | yes | context | Exchange Code |
| `ssoExchangeTenantId` | string | yes | context | SSO Exchange Tenant Id |

Also reads from context when present: `stepUp`, `customClaims`, `tenant`, `tenantName`, `ssoId`, `ssoIdOverridden`, `email`, `idpInitiated`, `startOptions`, `lastAuth`, `context`, `sessionIdsToRevoke`, `exchangeError`, `provider`, `ssoAuthType`, `lastAuth`, `fetchIDPGroups` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `saml-enabled`

**SSO / Enabled**. Is SSO configured for tenant

**Error ids**: none declared.

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- next interactionIds: `success`

Also reads from context when present: `stepUp`, `customClaims`, `tenant`, `startOptions`, `tenantName`, `ssoId`, `ssoIdOverridden`, `email` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `saml-get-config`

**SSO / Get SAML Configuration**. Get a tenant's SSO SAML configuration.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SAMLConfigSelectTenant` (Error fetching tenants from JWT), `ConfigProvideTenant` (Insufficient permission to tenant)

- management flows: compatible
- tags: saml, single sign on
- next interactionIds: `success`

Also reads from context when present: `tenant`, `userSelectedTenant`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `saml-set-config`

**SSO / Set SAML Configuration**. Set a tenant's SSO SAML configuration.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SetSAMLConfigFailed` (Error while configuring SSO SAML), `SAMLConfigSelectTenant` (Error fetching tenants from JWT), `ConfigProvideTenant` (Insufficient permission to tenant)

- management flows: compatible
- tags: saml, single sign on
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `redirectUrl` | string |  | argument | Post Authentication Redirect URL |

Also reads from context when present: `tenant`, `userSelectedTenant`, `idpURL`, `idpCert`, `entityId`, `tenantDomain`, `idpMetadataURL`, `calledGetSAMLConfig`, `tenantDomains`, `samlMappings`, `samlGroupMappings`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `saml-start`

**SSO / Start**. First step of a SSO authentication - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SSOStartFailed` (Error in SSO authorization phase), `SAMLStartFailed` (Error in SSO SAML authorization phase), `OAuthStartFailed` (Error in SSO OAuth authorization phase), `ActionErrorTenantDisabled` (Tenant Disabled)

- member of `saml`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `redirectUrl` | string |  | argument | Redirect URL (Optional); The default URL the end user is redirected to after a successful SSO sign-in.; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt (OIDC only); Specify how the Authorization Server prompts the end user for authentication and consent. Relevant for OIDC SSO only.; options: `none`, `login`, `consent`, `select_account` |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `exchangeCode` | string | yes | context | Exchange Code |
| `forceAuthn` | boolean |  | argument | Force Authentication (SAML only); If enabled, forces the IdP to re-authenticate the user, even if a session already exists (SAML only) |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `verifyInitiatedEmail` | boolean |  | argument | Verify initiated email matches IdP response; Enable to verify that the email provided in the initiation phase matches the email returned by the Identity Provider. |
| `fetchIDPGroups` | boolean |  | argument | Fetch user's IdP Groups from SCIM; When enabled, SCIM-provisioned groups are fetched for the user and merged with any groups received from the IdP during the SSO exchange. |
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |

Also reads from context when present: `stepUp`, `customClaims`, `tenant`, `tenantName`, `ssoId`, `ssoIdOverridden`, `email`, `idpInitiated`, `startOptions`, `lastAuth`, `context`, `sessionIdsToRevoke` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `scim-create-key`

**SSO / Create SCIM access key**. Create an access key for SCIM.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SCIMCreateKeyFailed` (Error creating SCIM access key), `SAMLConfigSelectTenant` (No valid tenant for user), `ConfigProvideTenant` (User invalid permissions for provided tenant)

- management flows: compatible
- tags: saml, single sign on, scim
- next interactionIds: `success`

Also reads from context when present: `tenant`, `userSelectedTenant`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sso-additional-saml-attributes`

**SSO / Add SAML Attributes**. Add custom SAML attributes to the SAML assertion.

**Error ids**: none declared.

- tags: sso, saml, attributes, custom attributes
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `samlAttributes` | list of `{key, type, value}` rows |  | argument | SAML Additional Attributes |
| `providedSAMLAttributesKey` | string |  | argument | Context Key for SAML Attribute Map (Optional); Specifies the key in the context where the SAML attribute map is stored.; value may be a context key |
| `addExistingSAMLAttributes` | boolean |  | argument | Add attributes from incoming SAML assertion |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sso-create-configuration`

**SSO / Create SSO Configuration**. Create a new SSO configuration for a tenant.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `CreateSSOConfigurationFailed` (Error creating SSO configuration), `SSOConfigurationPermission` (No valid tenant or insufficient permissions), `ConfigProvideTenant` (User invalid permissions for provided tenant)

- management flows: compatible
- tags: saml, oidc, single sign on
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `newSSOConfigurationName` | string | yes | context | Display Name |

Also reads from context when present: `tenant`, `userSelectedTenant`, `newSSOConfigurationId`, `authenticationOnly` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sso-delete-configuration`

**SSO / Delete SSO Configuration**. Delete an SSO configuration for a tenant.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `DeleteSSOConfigurationFailed` (Error deleting SSO configuration), `SSOConfigurationPermission` (No valid tenant or insufficient permissions), `ConfigProvideTenant` (User invalid permissions for provided tenant)

- management flows: compatible
- tags: saml, oidc, single sign on
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `deleteSSOConfigurationId` | string | yes | context | Configuration ID |

Also reads from context when present: `tenant`, `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sso-disable-config`

**SSO / Disable SSO Configuration**. Disable a tenant's SSO configuration.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SetSAMLConfigFailed` (Error while configuring SSO SAML), `SAMLConfigSelectTenant` (Error fetching tenants from JWT), `ConfigProvideTenant` (Insufficient permission to tenant)

- management flows: compatible
- tags: saml, single sign on
- next interactionIds: `success`

Also reads from context when present: `tenant`, `userSelectedTenant`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sso-no-user`

**SSO / Authenticate Only**. SSO authentication, via SAML or OIDC, without creating, updating, or signing in a user. The SAML attributes or OIDC claims remain available to the flow, and no session is created - follow with a Sign Up Anonymous User action to create one.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SSOStartFailed` (Error in SSO authorization phase), `SAMLStartFailed` (Error in SSO SAML authorization phase), `OAuthStartFailed` (Error in SSO OAuth authorization phase), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `SSSOExchangeCodeFailed` (Error in SSO exchange phase), `SAMLExchangeCodeFailed` (Error in SSO SAML exchange phase), `OAuthExchangeCodeFailed` (Error in SSO OAuth exchange phase), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure)

- **group (console shorthand, never a task action)**: write the members as tasks `sso-start-no-user`, `exchange-saml-code`
- tags: saml, single sign on, oidc, anonymous, no user
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `redirectUrl` | string |  | argument | Redirect URL (Optional); The default URL the end user is redirected to after a successful SSO sign-in.; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt (OIDC only); Specify how the Authorization Server prompts the end user for authentication and consent. Relevant for OIDC SSO only.; options: `none`, `login`, `consent`, `select_account` |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `exchangeCode` | string | yes | context | Exchange Code |
| `forceAuthn` | boolean |  | argument | Force Authentication (SAML only); If enabled, forces the IdP to re-authenticate the user, even if a session already exists (SAML only) |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `verifyInitiatedEmail` | boolean |  | argument | Verify initiated email matches IdP response; Enable to verify that the email provided in the initiation phase matches the email returned by the Identity Provider. |
| `fetchIDPGroups` | boolean |  | argument | Fetch user's IdP Groups from SCIM; When enabled, SCIM-provisioned groups are fetched for the user and merged with any groups received from the IdP during the SSO exchange. |
| `exchangeCode` | string | yes | context | Exchange Code |
| `ssoExchangeTenantId` | string | yes | context | SSO Exchange Tenant Id |

Also reads from context when present: `stepUp`, `customClaims`, `tenant`, `tenantName`, `ssoId`, `ssoIdOverridden`, `email`, `idpInitiated`, `startOptions`, `lastAuth`, `context`, `exchangeError`, `provider`, `ssoAuthType`, `lastAuth`, `fetchIDPGroups` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sso-start-no-user`

**SSO / Start / Authenticate Only**. First step of a SSO authentication that does not create, update, or sign in a user - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SSOStartFailed` (Error in SSO authorization phase), `SAMLStartFailed` (Error in SSO SAML authorization phase), `OAuthStartFailed` (Error in SSO OAuth authorization phase), `ActionErrorTenantDisabled` (Tenant Disabled)

- member of `sso-no-user`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `redirectUrl` | string |  | argument | Redirect URL (Optional); The default URL the end user is redirected to after a successful SSO sign-in.; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt (OIDC only); Specify how the Authorization Server prompts the end user for authentication and consent. Relevant for OIDC SSO only.; options: `none`, `login`, `consent`, `select_account` |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `exchangeCode` | string | yes | context | Exchange Code |
| `forceAuthn` | boolean |  | argument | Force Authentication (SAML only); If enabled, forces the IdP to re-authenticate the user, even if a session already exists (SAML only) |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `verifyInitiatedEmail` | boolean |  | argument | Verify initiated email matches IdP response; Enable to verify that the email provided in the initiation phase matches the email returned by the Identity Provider. |
| `fetchIDPGroups` | boolean |  | argument | Fetch user's IdP Groups from SCIM; When enabled, SCIM-provisioned groups are fetched for the user and merged with any groups received from the IdP during the SSO exchange. |

Also reads from context when present: `stepUp`, `customClaims`, `tenant`, `tenantName`, `ssoId`, `ssoIdOverridden`, `email`, `idpInitiated`, `startOptions`, `lastAuth`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sso-start-test`

**SSO / Start / Test**. First step of a SSO test authentication - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SSOStartFailed` (Error in SSO authorization phase), `SAMLStartFailed` (Error in SSO SAML authorization phase), `OAuthStartFailed` (Error in SSO OAuth authorization phase), `ActionErrorTenantDisabled` (Tenant Disabled)

- member of `sso-test`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `redirectUrl` | string |  | argument | Redirect URL (Optional); The default URL the end user is redirected to after a successful SSO sign-in.; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt (OIDC only); Specify how the Authorization Server prompts the end user for authentication and consent. Relevant for OIDC SSO only.; options: `none`, `login`, `consent`, `select_account` |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `exchangeCode` | string | yes | context | Exchange Code |
| `forceAuthn` | boolean |  | argument | Force Authentication (SAML only); If enabled, forces the IdP to re-authenticate the user, even if a session already exists (SAML only) |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `verifyInitiatedEmail` | boolean |  | argument | Verify initiated email matches IdP response; Enable to verify that the email provided in the initiation phase matches the email returned by the Identity Provider. |
| `fetchIDPGroups` | boolean |  | argument | Fetch user's IdP Groups from SCIM; When enabled, SCIM-provisioned groups are fetched for the user and merged with any groups received from the IdP during the SSO exchange. |

Also reads from context when present: `stepUp`, `customClaims`, `tenant`, `tenantName`, `ssoId`, `ssoIdOverridden`, `email`, `idpInitiated`, `startOptions`, `lastAuth`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sso-test`

**SSO / Test Configuration (dry run)**. SSO configuration test, via SAML or OIDC. Returns the IdP responses and the identified user with its attributes from the SSO server. This is dry run, user will not be created / updated in the system.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SSOStartFailed` (Error in SSO authorization phase), `SAMLStartFailed` (Error in SSO SAML authorization phase), `OAuthStartFailed` (Error in SSO OAuth authorization phase), `ActionErrorTenantDisabled` (Tenant Disabled), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `SSSOExchangeCodeFailed` (Error in SSO exchange phase), `SAMLExchangeCodeFailed` (Error in SSO SAML exchange phase), `OAuthExchangeCodeFailed` (Error in SSO OAuth exchange phase), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure)

- **group (console shorthand, never a task action)**: write the members as tasks `sso-start-test`, `exchange-saml-code`
- tags: saml, single sign on, oidc, test
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `redirectUrl` | string |  | argument | Redirect URL (Optional); The default URL the end user is redirected to after a successful SSO sign-in.; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt (OIDC only); Specify how the Authorization Server prompts the end user for authentication and consent. Relevant for OIDC SSO only.; options: `none`, `login`, `consent`, `select_account` |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `exchangeCode` | string | yes | context | Exchange Code |
| `forceAuthn` | boolean |  | argument | Force Authentication (SAML only); If enabled, forces the IdP to re-authenticate the user, even if a session already exists (SAML only) |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `verifyInitiatedEmail` | boolean |  | argument | Verify initiated email matches IdP response; Enable to verify that the email provided in the initiation phase matches the email returned by the Identity Provider. |
| `fetchIDPGroups` | boolean |  | argument | Fetch user's IdP Groups from SCIM; When enabled, SCIM-provisioned groups are fetched for the user and merged with any groups received from the IdP during the SSO exchange. |
| `exchangeCode` | string | yes | context | Exchange Code |
| `ssoExchangeTenantId` | string | yes | context | SSO Exchange Tenant Id |

Also reads from context when present: `stepUp`, `customClaims`, `tenant`, `tenantName`, `ssoId`, `ssoIdOverridden`, `email`, `idpInitiated`, `startOptions`, `lastAuth`, `context`, `exchangeError`, `provider`, `ssoAuthType`, `lastAuth`, `fetchIDPGroups` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-users-add-sso-apps`

**User / Batch / Add Applications**. Add federated applications to selected users

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `UpdateUsersAddSSOAppsFailed` (Failed to add users federated applications), `UpdateUsersAddSSOAppsPermissions` (No valid permission to add users federated applications), `UpdateUsersAddSSOAppsSelectTenant` (Error fetching tenants from JWT), `UpdateUsersAddSSOAppsEmptyTenant` (No tenant associated with request)

- tags: update, users, add, sso, applications, batch
- next interactionIds: `success`

Also reads from context when present: `context`, `startOptions`, `userIds`, `ssoApplications` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-users-delete-sso-apps`

**User / Batch / Delete Applications**. Remove federated applications from selected users

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `UpdateUsersDeleteSSOAppsFailed` (Failed to remove users federated applications), `UpdateUsersDeleteSSOAppsPermissions` (No valid permission to remove users federated applications), `UpdateUsersDeleteSSOAppsSelectTenant` (Error fetching tenants from JWT), `UpdateUsersDeleteSSOAppsEmptyTenant` (No tenant associated with request)

- tags: update, users, delete, remove, sso, applications, batch
- next interactionIds: `success`

Also reads from context when present: `context`, `startOptions`, `userIds`, `ssoApplications` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
