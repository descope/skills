# Actions: Consent, inbound/outbound apps, agentic hub, device flow, CIBA, external auth, admin links

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `admin-link-sso-generate`

**Generate SSO configuration admin link**. Generate SSO configuration time-based admin link for a tenant

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `AdminLinkSSOGenerateFailed` (Error while generating sso config admin link), `ConfigProvideTenant` (Insufficient permission to tenant)

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- tags: sso, single sign on, admin link, configuration
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `timeout` | number | yes | argument | Token expiration time (in minutes) |

Also reads from context when present: `tenant`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `admin-link-sso-generate-v2`

**Generate SSO setup suite admin link**. Generate SSO setup suite time-based admin link for a tenant

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `AdminLinkSSOGenerateFailed` (Error while generating SSO setup suite admin link), `ConfigProvideTenant` (Insufficient permission to tenant)

- management flows: compatible
- tags: sso, single sign on, admin link, configuration, setup, suite, self service
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `timeout` | number | yes | argument | Token expiration time (in minutes) |

Also reads from context when present: `tenant`, `ssoId`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `admin-link-sso-revoke`

**Revoke SSO configuration admin link**. Revoke SSO configuration admin link for a tenant

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `AdminLinkSSORevokeFailed` (Error while revoking sso config admin link), `ConfigProvideTenant` (Insufficient permission to tenant)

- management flows: compatible
- tags: sso, single sign on, admin link, configuration
- next interactionIds: `success`

Also reads from context when present: `tenant`, `ssoId`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `agentic-hub-connection-connect`

**Agentic Hub / Connect**. Create a user's provider token in the agentic hub connection tool.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `AgenticHubConnectionConnectFailed` (Agentic Hub connection start error)

- member of `agentic-hub-connection-connect-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `defaultOutboundOAuthAppId` | string |  | argument | Agentic Hub Connection ID |
| `useConfiguredScopes` | boolean |  | argument | Use configured scopes; Uncheck to use the connection scopes mapped from what the user consented to in this flow. Requires a consent step earlier in the flow.; default `true` |
| `defaultOutboundOAuthAppScopes` | array |  | argument | Agentic Hub Connection Scopes; Define which scopes should be used when one wasn't set prior to this step. If not set, the scopes mapped in the MCP client will be used for the connection.; depends on `useConfiguredScopes`; value may be a context key |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the connection tool.; value may be a context key |
| `defaultOutboundOAuthAppResources` | array |  | argument | Agentic Hub Connection Resources; Define which resources should be used for the connection tool.; value may be a context key |
| `outboundExternalIdentifier` | string |  | argument | External Identifier; Optional external identifier for the outbound connection.; value may be a context key |
| `exchangeStepId` | string | yes | argument | Outbound Connect Exchange Step ID |

Also reads from context when present: `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `agentic-hub-connection-connect-group`

**Agentic Hub / Connect**. Create a user's provider token in the agentic hub connection tool.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `AgenticHubConnectionConnectFailed` (Agentic Hub connection start error), `OutboundOAuthAppConnectFinishFailed` (Outbound App connection finish erro)

- **group (console shorthand, never a task action)**: write the members as tasks `agentic-hub-connection-connect`, `outbound-oauth-app-connect-finish`
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `defaultOutboundOAuthAppId` | string |  | argument | Agentic Hub Connection ID |
| `useConfiguredScopes` | boolean |  | argument | Use configured scopes; Uncheck to use the connection scopes mapped from what the user consented to in this flow. Requires a consent step earlier in the flow.; default `true` |
| `defaultOutboundOAuthAppScopes` | array |  | argument | Agentic Hub Connection Scopes; Define which scopes should be used when one wasn't set prior to this step. If not set, the scopes mapped in the MCP client will be used for the connection.; depends on `useConfiguredScopes`; value may be a context key |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the connection tool.; value may be a context key |
| `defaultOutboundOAuthAppResources` | array |  | argument | Agentic Hub Connection Resources; Define which resources should be used for the connection tool.; value may be a context key |
| `outboundExternalIdentifier` | string |  | argument | External Identifier; Optional external identifier for the outbound connection.; value may be a context key |
| `exchangeStepId` | string | yes | argument | Outbound Connect Exchange Step ID |

Also reads from context when present: `context`, `startOptions`, `context`, `exchangeError` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `agentic-hub-update-mcp-client`

**Update MCP Client**. Update the MCP client details.

**Error ids**: none declared.

- management flows: compatible
- tags: mcp, client, update
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `name` | string | yes | argument | Name; Name of the MCP client; default `{{mcpClient.name}}`; value may be a context key |
| `description` | string | yes | argument | Description; Description of the MCP client; default `{{mcpClient.description}}`; value may be a context key |
| `status` | string (select) | yes | argument | Status; Status of the MCP client; default `current`; options: `current`, `verified`, `unverified` |
| `tags` | array |  | argument | Tags |
| `sessionSettingsEnabled` | boolean (radio) |  | argument | Session settings enabled; values: `{"Custom": true}` |
| `refreshTokenExpiration` | string (duration) |  | argument | Refresh token expiration; depends on `sessionSettingsEnabled` |
| `refreshTokenExpirationUnit` | string (durationType) |  | argument | Refresh token expiration unit; default `days` |
| `sessionTokenExpiration` | string (duration) |  | argument | Session token expiration; depends on `sessionSettingsEnabled` |
| `sessionTokenExpirationUnit` | string (durationType) |  | argument | Session token expiration unit; default `minutes` |
| `userTemplateId` | string |  | argument | User JWT template; depends on `sessionSettingsEnabled`; value may be a context key |
| `keyTemplateId` | string |  | argument | Access Key template; depends on `sessionSettingsEnabled`; value may be a context key |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `ciba-finish`

**CIBA Approval**. Approve backchannel authentication request

**Error ids**: none declared.

- tags: oidc, ciba, verification
- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `ciba-user-code-verification`

**CIBA User Code Verification**. Verify the CIBA User-code

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `CIBAUserCodeVerificationFailed` (Error verifying backchannel user code), `CIBAUserCodeVerificationInvalid` (Backchannel user code expired)

- tags: oidc, ciba, user code, verification
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `userCode` | string | yes | context | User Code |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `create-consent`

**Update user consent**. Update the user's 3rd party application consent

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `CreateConsentFailed` (Error updating user consent), `CreateConsentPoliciesDenied` (Error updating user consent, denied by policy)

- management flows: compatible
- tags: consent
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `tenantLevel` | boolean |  | argument | Tenant level |
| `scopesAutoApproval` | boolean |  | argument | Scopes auto approval |
| `duration` | string |  | argument | Valid for (in minutes); value may be a context key |
| `tags` | array |  | argument | Tags |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `create-tenant-consent`

**Update tenant consent**. Update the tenant's 3rd party application consent

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `CreateConsentFailed` (Error updating tenant consent), `CreateConsentPoliciesDenied` (Error updating tenant consent, denied by policies)

- management flows: compatible
- tags: consent
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `scopesAutoApproval` | boolean |  | argument | Scopes auto approval |
| `duration` | string |  | argument | Valid for (in minutes); value may be a context key |
| `tags` | array |  | argument | Tags |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `device-flow-finish`

**Device Flow Approval**. Approve pairing new device

**Error ids**: none declared.

- tags: oidc, device flow, verification
- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `device-flow-user-code-verification`

**Device Flow User Code Verification**. Verify the Device flow User-code

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `DeviceFlowUserCodeVerificationFailed` (Error verifying user code), `DeviceFlowUserCodeVerificationInvalid` (User code expired)

- tags: oidc, device flow, user code, verification
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `userCode` | string | yes | context | User Code |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `external-auth`

**External Authentication**. Authenticate users on your own website and bridge the result back to the Descope flow. The flow redirects to your login page, and after authenticating the user you call the management API to complete the flow.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ExternalAuthMisconfiguration` (External auth misconfiguration), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `ExternalAuthFailed` (Error in external auth exchange), `ExternalAuthTimeout` (External auth timed out)

- **group (console shorthand, never a task action)**: write the members as tasks `external-auth-start`, `external-auth-exchange`
- tags: external, custom, authentication, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `externalAuthUrl` | string | yes | argument | External Auth URL; value may be a context key |
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `external-auth-exchange`

**External Auth / Exchange**. Second step of external authentication - verify the exchange code and create session.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `ExternalAuthFailed` (Error in external auth exchange), `ExternalAuthTimeout` (External auth timed out)

- member of `external-auth`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeCode` | string | yes | context | Exchange Code |

### `external-auth-start`

**External Auth / Start**. First step of external authentication - redirect the user to the customer's login page.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ExternalAuthMisconfiguration` (External auth misconfiguration)

- member of `external-auth`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `externalAuthUrl` | string | yes | argument | External Auth URL; value may be a context key |

Also reads from context when present: `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-api-app-connect`

**Outbound App / Connect API key**. Create a user's api key in the outbound application.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundAPIAppConnectFailed` (Outbound App connection error)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `defaultOutboundOAuthAppId` | string |  | argument | Default Outbound App ID |
| `apiKey` | string | yes | context |  |

Also reads from context when present: `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-api-app-tenant-connect`

**Outbound App / Connect tenant API key**. Create a tenant's api key in the outbound application.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundAPIAppTenantConnectFailed` (Outbound App connection error)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `defaultOutboundOAuthAppId` | string |  | argument | Default Outbound App ID |
| `apiKey` | string | yes | context |  |

Also reads from context when present: `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-app-user-tokens-delete`

**Outbound App / Delete User Tokens**. Delete all tokens of a user in the outbound application.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundAppUnauthorizedRequest` (Unauthorized request), `OutboundAppUserTokensDeleteFailed` (Outbound App delete user tokens error)

- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-oauth-app-connect`

**Outbound App / Connect**. Create a user's provider token in the outbound application.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundOAuthAppConnectFailed` (Outbound App connection start error)

- member of `outbound-oauth-app-connect-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `defaultOutboundOAuthAppId` | string |  | argument | Default Outbound App ID |
| `useConfiguredScopes` | boolean |  | argument | Use configured scopes; Uncheck to use the connection scopes mapped from what the user consented to in this flow. Requires a consent step earlier in the flow.; default `true` |
| `defaultOutboundOAuthAppScopes` | array |  | argument | Outbound App Scopes; Define which scopes should be used when one wasn't set prior to this step. If not set, the default scopes defined in the Outbound App will be used.; depends on `useConfiguredScopes`; value may be a context key |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the Outbound App.; value may be a context key |
| `defaultOutboundOAuthAppResources` | array |  | argument | Outbound App Resources; Define which resources should be used for the Outbound App.; value may be a context key |
| `outboundExternalIdentifier` | string |  | argument | External Identifier; Optional external identifier for the outbound connection.; value may be a context key |
| `exchangeStepId` | string | yes | argument | Outbound Connect Exchange Step ID |

Also reads from context when present: `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-oauth-app-connect-finish`

**Outbound OAuth App Connect Finish**. Second step of an Outbound OAuth App Connect action

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundOAuthAppConnectFinishFailed` (Outbound App connection finish erro)

- member of `agentic-hub-connection-connect-group`, `outbound-oauth-app-connect-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

Also reads from context when present: `context`, `exchangeError` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-oauth-app-connect-group`

**Outbound App / Connect**. Create a user's provider token in the outbound application.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundOAuthAppConnectFailed` (Outbound App connection start error), `OutboundOAuthAppConnectFinishFailed` (Outbound App connection finish erro)

- **group (console shorthand, never a task action)**: write the members as tasks `outbound-oauth-app-connect`, `outbound-oauth-app-connect-finish`
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `defaultOutboundOAuthAppId` | string |  | argument | Default Outbound App ID |
| `useConfiguredScopes` | boolean |  | argument | Use configured scopes; Uncheck to use the connection scopes mapped from what the user consented to in this flow. Requires a consent step earlier in the flow.; default `true` |
| `defaultOutboundOAuthAppScopes` | array |  | argument | Outbound App Scopes; Define which scopes should be used when one wasn't set prior to this step. If not set, the default scopes defined in the Outbound App will be used.; depends on `useConfiguredScopes`; value may be a context key |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the Outbound App.; value may be a context key |
| `defaultOutboundOAuthAppResources` | array |  | argument | Outbound App Resources; Define which resources should be used for the Outbound App.; value may be a context key |
| `outboundExternalIdentifier` | string |  | argument | External Identifier; Optional external identifier for the outbound connection.; value may be a context key |
| `exchangeStepId` | string | yes | argument | Outbound Connect Exchange Step ID |

Also reads from context when present: `context`, `startOptions`, `context`, `exchangeError` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-oauth-app-tenant-connect`

**Outbound App / Tenant Connect**. Create a tenant's provider token in the outbound application.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundOAuthAppTenantConnectFailed` (Outbound App tenant connect start error)

- member of `outbound-oauth-app-tenant-connect-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `defaultOutboundOAuthAppId` | string |  | argument | Default Outbound App ID |
| `defaultOutboundOAuthAppScopes` | array |  | argument | Outbound App Scopes; Define which scopes should be used when one wasn't set prior to this step. If not set, the default scopes defined in the Outbound App will be used.; value may be a context key |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the Outbound App.; value may be a context key |
| `defaultOutboundOAuthAppResources` | array |  | argument | Outbound App Resources; Define which resources should be used for the Outbound App.; value may be a context key |
| `outboundExternalIdentifier` | string |  | argument | External Identifier; Optional external identifier for the outbound connection.; value may be a context key |
| `exchangeStepId` | string | yes | argument | Outbound Tenant Connect Exchange Step ID |

Also reads from context when present: `context`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-oauth-app-tenant-connect-finish`

**Outbound App / Tenant Connect Finish**. Second step of an Outbound OAuth App Tenant Connect action

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundOAuthAppTenantConnectFinishFailed` (Outbound App tenant connect finish error)

- member of `outbound-oauth-app-tenant-connect-group`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

Also reads from context when present: `context`, `exchangeError` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `outbound-oauth-app-tenant-connect-group`

**Outbound App / Tenant Connect**. Create a tenant's provider token in the outbound application.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OutboundOAuthAppTenantConnectFailed` (Outbound App tenant connect start error), `OutboundOAuthAppTenantConnectFinishFailed` (Outbound App tenant connect finish error)

- **group (console shorthand, never a task action)**: write the members as tasks `outbound-oauth-app-tenant-connect`, `outbound-oauth-app-tenant-connect-finish`
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `defaultOutboundOAuthAppId` | string |  | argument | Default Outbound App ID |
| `defaultOutboundOAuthAppScopes` | array |  | argument | Outbound App Scopes; Define which scopes should be used when one wasn't set prior to this step. If not set, the default scopes defined in the Outbound App will be used.; value may be a context key |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the Outbound App.; value may be a context key |
| `defaultOutboundOAuthAppResources` | array |  | argument | Outbound App Resources; Define which resources should be used for the Outbound App.; value may be a context key |
| `outboundExternalIdentifier` | string |  | argument | External Identifier; Optional external identifier for the outbound connection.; value may be a context key |
| `exchangeStepId` | string | yes | argument | Outbound Tenant Connect Exchange Step ID |

Also reads from context when present: `context`, `startOptions`, `context`, `exchangeError` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `provision-mcp-company`

**Provision MCP company**. Auto-provision a company, project, tenant, and admin role for MCP users

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `provisionMcpCompany` (Error provisioning MCP company), `provisionMcpCompanyExists` (MCP company already exists)

- hidden in the console's action picker (still valid in a flow)
- license: `allowMCPAutoProvision`
- tags: company, provision, mcp
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `companyName` | string |  | argument | Company name |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-inbound-app`

**Update Inbound App**. Update the inbound application details.

**Error ids**: none declared.

- management flows: compatible
- tags: inbound, application
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `name` | string | yes | argument | Name; Name of the inbound application; default `{{thirdPartyApp.name}}`; value may be a context key |
| `description` | string | yes | argument | Description; Description of the inbound application; default `{{thirdPartyApp.description}}`; value may be a context key |
| `status` | string (select) | yes | argument | Status; Status of the inbound application; default `current`; options: `current`, `verified`, `unverified` |
| `tags` | array |  | argument | Tags |
| `sessionSettingsEnabled` | boolean (radio) |  | argument | Session settings enabled; values: `{"Custom": true}` |
| `refreshTokenExpiration` | string (duration) |  | argument | Refresh token expiration; depends on `sessionSettingsEnabled` |
| `refreshTokenExpirationUnit` | string (durationType) |  | argument | Refresh token expiration unit; default `days` |
| `sessionTokenExpiration` | string (duration) |  | argument | Session token expiration; depends on `sessionSettingsEnabled` |
| `sessionTokenExpirationUnit` | string (durationType) |  | argument | Session token expiration unit; default `minutes` |
| `userTemplateId` | string |  | argument | User JWT template; depends on `sessionSettingsEnabled`; value may be a context key |
| `keyTemplateId` | string |  | argument | Access Key template; depends on `sessionSettingsEnabled`; value may be a context key |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `update-inbound-app-status`

**Update Inbound App Status**. Update the status of an inbound application.

**Error ids**: none declared.

- management flows: compatible
- tags: inbound, application, status
- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
