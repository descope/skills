# Actions: OAuth and social login

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `exchange-oauth-code`

**OAuth / Exchange**. Second step of an OAuth authentication - get user claims.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled)

- member of `oauth`, `oauth-signin`, `oauth-signup`, `oauth-update-user`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `exchange-oauth-code-in`

**OAuth / Exchange**. Second step of an OAuth authentication - get user claims.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled), `UserDoesNotExists` (User does not exists)

- member of `oauth-signin-v2`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `exchange-oauth-code-up`

**OAuth / Exchange**. Second step of an OAuth authentication - get user claims.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled), `UserExists` (User exists), `UnauthSignUp` (Unauthorized sign up)

- member of `oauth-signup-v2`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth`

**Sign Up or In / OAuth**. Enable users to sign up or in using Social Login (OAuth). Users that try to sign in but don't exist in the Descope users table will be automatically created. Returns the identified user with its claims from the IDP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `oauth-start`, `exchange-oauth-code`
- tags: google, socials, sso, sign up, sign in, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode`, `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-signin`

**Sign In / OAuth**. Enable users to sign in using Social Login (OAuth). Returns the identified user with its claims from the IDP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `oauth-start-sign-in`, `exchange-oauth-code`
- hidden in the console's action picker (still valid in a flow)
- tags: google, socials, sso, sign in, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode`, `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-signin-v2`

**Sign In / OAuth**. Enable users to sign in using Social Login (OAuth). Returns the identified user with its claims from the IDP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled), `UserDoesNotExists` (User does not exists)

- **group (console shorthand, never a task action)**: write the members as tasks `oauth-start-sign-in-v2`, `exchange-oauth-code-in`
- tags: google, socials, sso, sign in, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode`, `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-signup`

**Sign Up / OAuth**. Enable users to sign up using Social Login (OAuth). Returns the identified user with its claims from the IDP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `oauth-start-sign-up`, `exchange-oauth-code`
- hidden in the console's action picker (still valid in a flow)
- tags: google, socials, sso, sign up, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode`, `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-signup-v2`

**Sign Up / OAuth**. Enable users to sign up using Social Login (OAuth). Returns the identified user with its claims from the IDP.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled), `UserExists` (User exists), `UnauthSignUp` (Unauthorized sign up)

- **group (console shorthand, never a task action)**: write the members as tasks `oauth-start-sign-up-v2`, `exchange-oauth-code-up`
- tags: google, socials, sso, sign up, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode`, `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-start`

**OAuth / Start**. First step of an OAuth authentication - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase)

- member of `oauth`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-start-sign-in`

**Sign In / OAuth / Start**. First step of an OAuth authentication - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase)

- member of `oauth-signin`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-start-sign-in-v2`

**Sign In / OAuth / Start**. First step of an OAuth authentication - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase)

- member of `oauth-signin-v2`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-start-sign-up`

**Sign Up / OAuth / Start**. First step of an OAuth authentication - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase)

- member of `oauth-signup`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-start-sign-up-v2`

**Sign Up / OAuth / Start**. First step of an OAuth authentication - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase)

- member of `oauth-signup-v2`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `revokeSelectedSessions` | boolean |  | argument | Revoke selected sessions; End the sessions chosen earlier in this flow - by the active sessions component or by a scriptlet - when this authentication succeeds, so a user at the maximum concurrent sessions is admitted instead of refused. Only the authenticating user's own live sessions are ever ended. |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `rawResponse` | boolean |  | argument | Expose Raw OAuth Response |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `loginHint` | string |  | argument | Login Hint; Optional login hint sent to the IdP as a query parameter (e.g., pre-fill username); value may be a context key |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |

Also reads from context when present: `stepUp`, `sessionIdsToRevoke`, `customClaims`, `startOptions`, `lastAuth`, `context`, `idpInitiated`, `exchangeCode` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-start-update-user`

**User / Update / OAuth**. First step of an OAuth update user - creating the redirect URI.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase)

- member of `oauth-update-user`
- hidden in the console's action picker (still valid in a flow)
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowAllMerge` | boolean |  | argument | Merge without a common identifier (like email) |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |

Also reads from context when present: `stepUp`, `customClaims`, `startOptions`, `lastAuth`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `oauth-update-user`

**Update User / OAuth**. Enable users to connect Social Login (OAuth) with existing user

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `OAuthStartFailed` (Error in OAuth authorization phase), `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `OAuthExchangeCodeFailed` (Error in OAuth exchange phase), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled), `OAuthExchangeNativeOAuthFailed` (Native OAuth failure), `OAuthCanceled` (OAuth canceled)

- **group (console shorthand, never a task action)**: write the members as tasks `oauth-start-update-user`, `exchange-oauth-code`
- tags: google, socials, sso, sign up, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `provider` | string | yes | context | Provider |
| `redirectUrl` | string |  | argument | Redirect URL; value may be a context key |
| `prompt` | array (select) |  | argument | Prompt; Specify how the Authorization Server prompts the end user for authentication and consent.; options: `none`, `login`, `consent`, `select_account` |
| `allowAllMerge` | boolean |  | argument | Merge without a common identifier (like email) |
| `allowSetDefaultProvider` | boolean |  | argument | Set a default OAuth provider |
| `defaultProvider` | string (select) |  | argument | Provider; depends on `allowSetDefaultProvider` |
| `popup` | boolean |  | argument | Open in Popup; Open the OAuth provider link in a popup window. If not selected, the user will be redirected to the OAuth provider link in the current tab. |
| `forceNonNative` | boolean |  | argument | Force Non-Native OAuth; Toggle this to force web-based OAuth even when native OAuth has been requested |
| `authUrlParams` | list of `{key, type, value}` rows |  | argument | Authorization URL Parameters; Extra query parameters appended to the provider authorization request. Values may use dynamic values from the flow context. |
| `exchangeCode` | string | yes | context | Exchange Code |

Also reads from context when present: `stepUp`, `customClaims`, `startOptions`, `lastAuth`, `context`, `exchangeError`, `provider`, `lastAuth`, `startOptions`, `defaultProvider`, `oauthType`, `nativeOAuth`, `failure`, `oauthErrorId`, `forceNonNative` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
