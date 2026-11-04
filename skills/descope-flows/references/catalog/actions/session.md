# Actions: JWT, session, step-up, impersonation, devices

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `anonymous-user`

**Sign Up / Anonymous user**. Create a valid JWT for an anonymous user

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorAnonymousJwt` (Anonymous user JWT error)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `roles` | array |  | argument | Roles to add to user; value may be a context key |

Also reads from context when present: `customClaims`, `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `custom-claims`

**Custom Claims**. Create and update custom claims on the user's JWT.

**Error ids**: none declared.

- management flows: compatible
- tags: custom claims, jwt, claims, security
- docs: https://docs.descope.com/manage/customclaims/#using-custom-claims-within-descope-flows
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `customClaims` | list of `{key, type, value}` rows |  | argument | Custom claims in JSON format |
| `providedCustomClaimsKey` | string |  | argument | Context Key for Custom Claims Map (Optional); Specifies the key in the context where the Custom Claims map is stored.; value may be a context key |
| `customRefreshDuration` | boolean |  | argument | Set Custom Refresh Duration |
| `refreshDuration` | string (duration) |  | argument | Custom Refresh Duration; depends on `customRefreshDuration` |
| `refreshDurationType` | string (durationType) |  | argument | Refresh Duration Type; default `days` |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `generate-jwt-sign-in`

**Generate JWT / Sign In with 3rd party IDP**. Generate JWT for user sign in. Use only after validating user input via a third party provider.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `GenerateJWTSignInFailed` (Error generating JWT for sign in), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- tags: jwt, json web token, sign in, login
- next interactionIds: `success`

Also reads from context when present: `phone`, `email`, `externalId`, `stepUp`, `customClaims`, `context`, `lastAuth`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `generate-jwt-sign-up`

**Generate JWT / Sign Up with 3rd party IDP**. Generate JWT for user sign up. Use only after validating user input via a third party provider.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `GenerateJWTSignUpFailed` (Error generating JWT for sign up), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- tags: jwt, json web token, sign up, registration
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `phone`, `email`, `externalId`, `context`, `firstName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `generate-jwt-sign-up-or-in`

**Generate JWT / Sign Up or In with 3rd party IDP**. Generate JWT for user sign up or in. Use only after validating user input via a third party provider.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `GenerateJWTSignUpOrInFailed` (Error generating JWT for sign up or in), `ActionErrorTenantRequiresSSO` (Tenant Requires SSO), `ActionErrorTenantDisabled` (Tenant Disabled)

- tags: jwt, json web token, sign up, sign in, registration, login
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `providerId` | string |  | argument | Connector |
| `templateId` | string |  | argument | Template |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys |

Also reads from context when present: `phone`, `email`, `externalId`, `stepUp`, `customClaims`, `context`, `firstName`, `lastName`, `recoveryEmail`, `recoveryPhone`, `lastAuth`, `startOptions`, `locale` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `impersonate`

**User / Impersonate**. Impersonate another user, (Can be done only with impersonation permission)

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorImpersonateFailed` (Impersonation has failed), `ActionErrorImpersonateNoPermission` (Insufficient permissions for impersonation), `ActionErrorImpersonateConsent` (User did not grant impersonation consent), `ActionErrorMissingImpersonatingUser` (User does not exist)

- tags: impersonate, users
- docs: https://docs.descope.com/knowledgebase/general/userimpersonation/
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `impersonateId` | string | yes | context | impersonateId |
| `validateConsent` | boolean |  | argument | Validate user consent |
| `stepup` | boolean |  | argument | Add stepup claim to jwt |

Also reads from context when present: `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `impersonateFamilyDependent`

**Family / Impersonate Dependent**. Impersonate a dependent of the current user's family (requires the family impersonate-dependents permission)

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorFamilyImpersonateFailed` (Family impersonation has failed), `ActionErrorFamilyImpersonateNoPermission` (Insufficient permissions for family impersonation), `ActionErrorFamilyImpersonateNotDependent` (Impersonation target is not a family dependent), `ActionErrorFamilyImpersonateDependentMissing` (Dependent does not exist), `ActionErrorFamilyNotEnabled` (Family feature is not enabled)

- needs project feature `families`
- tags: impersonate, family, dependent
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `dependentLoginId` | string | yes | argument | Dependent login ID; value may be a context key |
| `selectedFamily` | string |  | argument | Family to scope the impersonated session to (optional); value may be a context key |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `impersonationConsent`

**Update User / Impersonation consent**. Update an authenticated user's impersonation consent

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `impersonationConsent` (Error granting impersonation consent)

- management flows: compatible
- tags: impersonation, consent
- docs: https://docs.descope.com/knowledgebase/general/userimpersonation/
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `duration` | number | yes | argument | Consent Expiration in Hours |
| `tenantSpecific` | boolean |  | argument | Limit consent to the user's selected tenant |

Also reads from context when present: `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `logged-in`

**End**. Ends the flow and generates JWT where applicable

**Error ids**: none declared.

- ends the flow
- tags: end, generate jwt, jwt, token
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `endWithoutSession` | boolean |  | argument | End without session; When enabled, the flow ends without issuing or returning a session - no JWT, user, cookies, login event, or trusted-device JWT. The user keeps any session they already had. Use for flows that should complete without logging the user in (e.g. the user-profile widget, or a deliberate no-login outcome). |
| `refreshCookieName` | string |  | argument | Refresh Cookie Name; Use this to set a custom cookie name for the refresh JWT. Note that this is only applicable when the Refresh Token Response Method is set to 'Cookies' in the Project configuration.; value may be a context key |
| `sessionCookieName` | string |  | argument | Session Cookie Name; Use this to set a custom cookie name for the session JWT. Note that this is only applicable when the Session Token Response Method is set to 'Cookies' in the Project configuration.; value may be a context key |
| `externalTokenConnector` | string |  | argument | External Token Connector; Configure the external token connector that will added to any authentication with Descope. |
| `oidcAnonymous` | boolean |  | argument | Return token after flow (without user authentication); Issues a JWT on flow completion, even without user authentication. Useful for triggering connector logic, performing risk or fraud evaluations, or supporting flows that don't require user authentication. |
| `output` | list of `{key, type, value}` rows |  | argument | Flow output |

Also reads from context when present: `riskInfo`, `authInfo`, `externalId`, `requestIds`, `context`, `startOptions`, `forceReloadUser` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `logout-session`

**Log out session**. Log out a session. Ends the current session when the user is signed in, or - after a sign in was refused for reaching the maximum concurrent sessions - the session the user selected from their active sessions.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `LogoutSession` (Failed to log out the session)

- tags: logout, sign out, session
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `sessionIds` | array |  | argument | Sessions to log out; default from context `sessionIdsToRevoke`; value may be a context key |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `mark-device-known`

**Mark device as known**. Mark this device as known for this user, regardless of end user input. Unlike trust-device, known-device grants no privilege - it is a pure recognition/notification signal, never an MFA-bypass gate.

**Error ids**: none declared.

- tags: known, device
- next interactionIds: `success`

Also reads from context when present: `known` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `reset-current-auth`

**Reset Auth Info**. Reset all authentication data

**Error ids**: none declared.

- tags: reset, auth
- next interactionIds: `success`

No inputs.

### `revoke-other-sessions`

**Revoke Other Sessions**. Revoke all other sessions of the current user.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorRevokeOtherSessions` (Error revoking other sessions)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `sessionTypes` | array |  | argument | Session Types |

### `setStepUp`

**Add login options to flow**. Add login option to flow, step-up yes or no (will need a refresh token to be provided by client)

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorParseCustomClaims` (Error parsing custom claims as json string)

- hidden in the console's action picker (still valid in a flow)
- alternatives: `start-step-up`, `custom-claims`
- tags: stepup, step up
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `stepUp` | boolean | yes | argument | Step up |
| `customClaims` | string |  | argument | Custom claims in JSON format |

### `start-step-up`

**Step Up**. Load user from incoming refresh token, and make its data available for the rest of the flow. Mark this flow as step up.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorLoadUserJwtVerify` (Error verifying refresh token), `ActionErrorLoadUserNoUser` (Error finding associated user), `ActionErrorLoadUserFromJWTFailed` (Error getting and validating refresh token)

- **group (console shorthand, never a task action)**: write the members as tasks `loadUser`, `step-up`
- tags: load, user, refresh, token, stepup, step up, stepup, step up
- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `step-up`

**Step Up**. Mark this flow as step up.

**Error ids**: none declared.

- member of `start-step-up`
- hidden in the console's action picker (still valid in a flow)
- tags: stepup, step up
- next interactionIds: `success`

No inputs.

### `stop-impersonation`

**User / Stop Impersonation**. Stop impersonation, get back a jwt of impersonator

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorStopImpersonationFailed` (Failed creating JWT for impersonator), `ActionErrorLoadUserNoUser` (Impersonator user does not exists or disabled), `ActionErrorStopImpersonationJWTParseError` (Failed extracting impersonator user from JWT)

- tags: stop, impersonate, users
- next interactionIds: `success`

Also reads from context when present: `userSelectedTenant` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `tenant-get-session-settings`

**Tenant / Get Session Settings**. Get tenant session settings

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `GetTenantSessionSettingsFailed` (Failed to get tenant session settings), `GetTenantSessionSettingsPermissions` (No valid permission to get tenant session settings)

- tags: get, tenant, session, settings
- next interactionIds: `success`

Also reads from context when present: `context`, `tenant`, `startOptions` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `tenant-reset-session-settings`

**Tenant / Reset Session Settings**. Reset session settings for current tenant

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ResetTenantSessionSettingsFailed` (Failed to reset tenant session settings), `ResetTenantSessionSettingsPermissions` (No valid permission to reset tenant session settings), `ResetTenantSessionSettingEmptyTenant` (No tenant associated with request), `ResetTenantSessionSettingGetProjectSettingsFails` (Failed to get project session settings)

- tags: reset, tenant, session, settings
- next interactionIds: `success`

Also reads from context when present: `context`, `tenant`, `startOptions`, `tenantSettings` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `tenant-set-session-settings`

**Tenant / Update Session Settings**. Update session settings for current tenant

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SetTenantSessionSettingsFailed` (Failed to update tenant session settings), `SetTenantSessionSettingsPermissions` (No valid permission to update tenant session settings), `ActionErrorSetTenantSessionSettingEmptyTenant` (No tenant associated with request)

- tags: update, tenant, session, settings
- next interactionIds: `success`

Also reads from context when present: `context`, `tenant`, `startOptions`, `tenantSettings`, `tsEnabled`, `tsRefreshTokenExpiration`, `tsRefreshTokenExpirationUnit`, `tsSessionTokenExpiration`, `tsSessionTokenExpirationUnit`, `tsEnableInactivity`, `tsInactivityTime`, `tsInactivityTimeUnit` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `trust-device`

**Mark device as trusted**. Mark device as trusted, regardless of end user input.

**Error ids**: none declared.

- tags: trust, device
- next interactionIds: `success`

Also reads from context when present: `trust` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `untrust-device`

**Unmark device as trusted**. Unmarks the deviceId in {{form.deviceId}} as trusted.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `UntrustDeviceFailed` (Untrust device failed)

- tags: untrust, device
- next interactionIds: `success`

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
