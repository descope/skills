# Condition context keys

Generated from the console's condition editor. Do not edit by hand.

299 keys a condition can test: `"target": {"type": "context", "value": "<key>"}` in a condition task's `atomicConditions`. Pick an operator from [conditions.md](conditions.md) that applies to the key's type (`is-true`/`is-false` for booleans, `equal`/`in`/`contains` for strings...). Keys with `<name>` take any name. `form.<key>` reads a custom screen input named `form.<key>` (an input named `<key>` is not `form.<key>`); built-in inputs (`email`, `phone`, name inputs) keep their bare name ([Input names](../flow-structure.md#input-names)). Every `user.<x>` key also exists as `unauthUser.<x>` for a user identified but not yet authenticated (for example after `loadUser` by login id), except `user.loggedIn`, `user.passwordExpired`, `user.passwordExpiresAt`, `user.recoveryEmail`, `user.recoveryPhone`, `user.verifiedRecoveryEmail`, `user.verifiedRecoveryPhone`. Any other context key a flow writes (connector results under `connectors.<name>`, scriptlet results under `scripts.<path>`) can be tested too; the console just doesn't list it.

Keys are case-sensitive: copy them exactly. `user.<x>` reads `authInfo.user.<x>`.

`Claim` = also usable as a value in custom claims.

## Authentication result and user (`authInfo.*`, `user.*`)

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `authInfo.sessionJwt` | string |  |  | A JSON web token used for session authentication and authorization purposes. |
| `authInfo.refreshJwt` | string |  |  | A JSON web token used for obtaining a new sessionJwt after expiration. |
| `authInfo.cookieDomain` | string |  |  | The domain that the cookie is valid for, used for cross-domain authentication. |
| `authInfo.cookiePath` | string |  |  | The path that the cookie is valid for, used for limiting cookie access to specific paths. |
| `authInfo.cookieMaxAge` | number |  |  | The maximum duration for which the cookie is valid, in seconds. |
| `authInfo.cookieExpiration` | number |  |  | The date and time at which the cookie expires, used for setting an explicit expiration date. |
| `authInfo.firstSeen` | boolean |  | yes | Whether the user is logging in for the first time. |
| `user.userId` | string |  | yes | A unique identifier for a user. |
| `user.test` | boolean |  | yes | Will be set to true if this user is a test user. |
| `user.loginIds` | string |  | yes | All unique identifiers for a user. Usually an email and/or phone. |
| `user.name` | string |  | yes | The user's name. |
| `user.givenName` | string |  | yes | The user's given name. |
| `user.middleName` | string |  | yes | The user's middle name. |
| `user.familyName` | string |  | yes | The user's family name. |
| `user.email` | string |  | yes | The user's email address. |
| `user.emailDomain` | string |  | yes | The domain of the user's email address. |
| `user.phone` | string |  | yes | The user's phone number. |
| `user.verifiedEmail` | boolean |  | yes | Whether the user's email address has been verified. |
| `user.verifiedPhone` | boolean |  | yes | Whether the user's phone number has been verified. |
| `user.recoveryEmail` | string |  | yes | The user's recovery email address. |
| `user.recoveryPhone` | string |  | yes | The user's recovery phone number. |
| `user.verifiedRecoveryEmail` | boolean |  | yes | Whether the user's recovery email address has been verified. |
| `user.verifiedRecoveryPhone` | boolean |  | yes | Whether the user's recovery phone number has been verified. |
| `user.userTenants` | string |  |  | An array of tenants associated with the user. |
| `user.project.roles` | string |  | yes | All project level roles associated with this user |
| `user.idpGroups` | string |  | yes |  |
| `app.clientId` | string |  | yes | The Application Client ID associated with the flow. |
| `user.project.permissions` | string |  | yes | All project level permissions associated with this user |
| `user.tenant.roles` | string |  |  | The tenant level user roles |
| `user.picture` | string |  | yes | The user's picture. |
| `user.outbound.token.valid` | boolean |  |  | Indicates whether the user has valid outbound token. |
| `device.webAuthnSupport` | boolean |  | yes | Indicates whether the device supports Passkeys (WebAuthn). |
| `device.oauthSupport` | boolean |  |  | Indicates whether the device supports OAuth (Social). Users coming from mobile web-views (as opposed to browsers) will be blocked by some OAuth providers. |
| `startOptions.redirectURL` | string |  | yes | The URL of the application that triggered the flow. |
| `startOptions.tenant` | string |  | yes | The tenant input that was provided to the flow. |
| `embeddedCode` | string |  | yes | Embedded OTP code |
| `user.oauth.google` | boolean |  | yes | Whether the user has signed in with Google. |
| `user.oauth.facebook` | boolean |  | yes | Whether the user has signed in with Facebook. |
| `user.oauth.microsoft` | boolean |  | yes | Whether the user has signed in with Microsoft. |
| `user.oauth.gitlab` | boolean |  | yes | Whether the user has signed in with Gitlab. |
| `user.oauth.github` | boolean |  | yes | Whether the user has signed in with Github. |
| `user.oauth.apple` | boolean |  | yes | Whether the user has signed in with Apple. |
| `user.oauth.discord` | boolean |  | yes | Whether the user has signed in with Discord. |
| `user.oauth.linkedin` | boolean |  | yes | Whether the user has signed in with Linkedin. |
| `user.oauth.slack` | boolean |  | yes | Whether the user has signed in with Slack. |

## Last authentication on this device (`lastAuth.*`)

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `lastAuth.loginId` | string |  |  | The unique identifier associated with the user's most recent login session. |
| `lastAuth.authMethod` | string | `otp-email`, `otp-sms`, `magiclink-email`, `magiclink-sms`, `enchantedlink`, `totp`, `oauth`, `sso/saml`, `sso/oidc`, `webauthn`, `password` |  | The method used for the user's most recent authentication, such as a password or biometric authentication. |
| `lastAuth.tenantId` | string |  |  | The tenant ID associated with the user's most recent authentication. |
| `lastAuth.ssoTenantId` | string |  |  | The SSO tenant ID used in the user's most recent authentication, relevant when multiple SSO configurations exist per tenant. |
| `lastAuth.ssoId` | string |  |  | The SSO ID used in the user's most recent authentication, relevant when multiple SSO configurations exist per tenant. |

## Current authentication (`currentAuth.*`)

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `currentAuth.loginId` | string |  |  |  |
| `currentAuth.authMethod` | string | `otp-email`, `otp-sms`, `magiclink-email`, `magiclink-sms`, `enchantedlink`, `totp`, `oauth`, `sso/saml`, `sso/oidc`, `webauthn`, `password` |  |  |

## Flow data: form inputs, request, geo, tenant, SSO, user attributes

When `tenant.*` and `ssoEnabled` are available: loaded on first read, no action needed, and before login. `tenant.<x>` reads the tenant the flow resolves, first match wins: a user already in context (authenticated, else loaded) -> that user's tenant (the only one, or the one matching `startOptions`); else the request's tenant, `startOptions.tenant`, the form's `tenantName`; else **the domain of the form's email**, matched to a tenant by its domains. So a condition on `tenant.enforceSSO` or `ssoEnabled` right after a screen that collects the email resolves for that email's domain. No matching tenant: `tenant.*` is empty (booleans read false). `ssoEnabledIgnoreUser` is `ssoEnabled` without the user step.

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `mailProviderHost` | string |  | yes | The hostname of the user's email provider, used for authentication purposes. |
| `adminLinks.ssoConfiguration` | string |  | yes | The SSO configuration admin link, used to setup SSO configuration for the tenant admin. |
| `jwtClaims.<name>` | string |  | yes | Get JWT claim value by name (e.g. 'jwtClaims.myClaimName') |
| `redirectURL` | string |  | yes | The URL to which the user will be redirected after authentication. |
| `cookies.<name>` | string |  | yes | Get cookie value by name (e.g. 'cookies.myCookieName') |
| `idpGroups` | string |  | yes | IdP Groups (SSO JIT / SCIM) |
| `idpSAMLAttributes` | string |  | yes | IdP SAML Attributes |
| `idpOIDCClaims` | string |  | yes | IdP OIDC Claims |
| `form.email` | string |  | yes | The email form input. |
| `form.emailDomain` | string |  | yes | The domain of the email form input. |
| `form.phone` | string |  | yes | The phone form input. |
| `form.photo` | string |  | yes | The picture uploaded by the "Take Photo" component. |
| `provider` | string | `google`, `facebook`, `microsoft`, `gitlab`, `github`, `apple`, `discord`, `linkedin`, `slack` | yes | The authentication provider used for authentication purposes. |
| `tenant` | string |  |  | The tenant associated with a user account. |
| `ssoId` | string |  |  | SSO ID |
| `abTestingKey` | abtesting |  |  | A random persistent number between 1-100 assigned to the client, that will help you split the flow for A/B testing. |
| `form.externalId` | string |  | yes | The custom login ID form input. |
| `form.displayName` | string |  | yes | The display name form input. |
| `form.givenName` | string |  | yes | The given name form input. |
| `form.middleName` | string |  | yes | The middle name form input. |
| `form.familyName` | string |  | yes | The family name form input. |
| `form.invitees` | string |  | yes | The invitees form input. |
| `form.impersonateId` | string |  | yes | The impersonate ID selected from the form input. |
| `form.tenantName` | string |  | yes | The tenant name form input. |
| `form.selfProvisionDomains` | string |  | yes | The self provision domains form input. |
| `form.idpMetadataURL` | string |  |  | The IdP metadata URL form input. |
| `form.tenantDomain` | string |  | yes | The tenant domain form input. |
| `form.entityId` | string |  | yes | The entity ID form input. |
| `form.idpURL` | string |  |  | The IDP URL form input. |
| `form.idpCert` | string |  |  | The IdP certificate form input. |
| `form.trustThisDevice` | boolean |  |  | Mark this device as trusted. |
| `geo.country` | string | `<country name, e.g. United States>`, `Embargoed Countries (US EAR)`, `Sanctioned Countries (US EAR)`, `European Union` | yes | The geographic location (country) of a user. |
| `geo.city` | string |  | yes | The city of a user. |
| `ipAddress` | ipaddress |  | yes | The IP address of the user who initiated the current request |
| `asn` | string |  | yes | The Autonomous System Number (ASN) of the user's network for the current request |
| `ja4` | string |  | yes | The TLS fingerprint (JA4) of the user who initiated the current request |
| `failedPasswordAttempts` | number |  |  | The number of failed password attempts made by the user. |
| `remainingOTPAttempts` | number |  |  | The number of remaining OTP code entry attempts. |
| `failedSQAttempts` | number |  |  | The number of failed security question verification attempts made by the user. |
| `idpInitiated` | boolean |  |  | Indicates whether the authentication request was initiated by an identity provider (IdP). |
| `externalToken` | boolean |  |  | Indicates whether flow has started with an external token (from invite of embedded link) to be verified. |
| `ssoEnabled` | boolean |  |  | Indicates whether single sign-on (SSO) is enabled for a user tenant, by user's email domain or tenant id |
| `ssoEnabledIgnoreUser` | boolean |  |  | Indicates whether single sign-on (SSO) is enabled based on the logged in user's email domain or tenant id. Should be used after login actions such as sign up / in. |
| `isDisposableEmail` | boolean |  |  | Indicates whether the email domain is of type disposable or burner email, need to run action "Check if Disposable Email used" prior to this condition |
| `isFreeEmailProvider` | boolean |  |  | Indicates whether the email domain is of type free email provider, like gmail.com, need to run action "Check if Free Email used" prior to this condition |
| `ssoAppId` | string |  | yes | The Application ID associated with the flow. |
| `user.loggedIn` | boolean |  |  | Indicates whether the user is already logged in. |
| `user.createdTime` | time |  | yes | The time the user was created. |
| `user.status` | string | `enabled`, `disabled`, `invited` | yes | The user's status. Such as "disabled", "enabled" or "invited". |
| `user.totp` | boolean |  | yes | Indicates whether the user has TOTP set. |
| `user.sso` | boolean |  | yes | Indicates whether the user has ever logged in with SSO. |
| `user.scim` | boolean |  | yes | Indicates whether the user has ever provisioned or updated by SCIM. |
| `user.webauthn` | boolean |  | yes | Indicates whether the user has a Passkey (WebAuthn) set. |
| `user.password` | boolean |  | yes | Indicates whether the user has ever logged in with a password and also still has one stored. |
| `user.passwordExpired` | boolean |  | yes | Indicates whether the user's password has expired, either explicitly or based on project expiration settings. |
| `user.passwordExpiresAt` | number |  | yes | The date (epoch seconds) when the user's password expires based on project expiration settings, or 0 if no expiration is configured. |
| `user.tenantNames` | string |  | yes | All user tenant names as array. |
| `user.tenantCount` | number |  | yes | The number of tenants this user is part of. |
| `user.tenantIds` | string |  | yes | Tenants the associated user belongs to. A user can belong to multiple organizations. |
| `user.lastAuth.country` | string |  | yes | Last country user logged in from |
| `user.lastAuth.countries` | string |  | yes | Latest countries user logged in from |
| `user.lastAuth.city` | string |  | yes | Last city user logged in from |
| `user.lastAuth.cities` | string |  | yes | Latest cities user logged in from |
| `user.lastAuth.ip` | string |  | yes | Last IP user logged in from |
| `user.lastAuth.ips` | string |  | yes | Latest IPS user logged in from |
| `user.lastAuth.time` | time |  | yes | Last time user logged in |
| `time.now` | time |  | yes | The time now in milliseconds since 1/1/1970. |
| `device.location.uri` | string |  | yes | The full URI where the flow is used. Such as "https://app.domain.com/path?q=v#fragment". |
| `device.location.origin` | string |  | yes | The origin where the flow is used. Such as "https://app.domain.com". |
| `device.location.scheme` | string |  | yes | The scheme of the URL where the flow is used. Such as "http" or "https". |
| `device.location.hostname` | string |  | yes | The hostname where the flow is used. Such as "app.domain.com". |
| `device.location.port` | string |  | yes | The port where the flow is used. Such as "3000". |
| `device.location.path` | string |  | yes | The path where the flow is used. Such as "/path". |
| `device.location.rawQuery` | string |  | yes | The raw query string where the flow is used. Such as "q=v". |
| `device.location.fragment` | string |  | yes | The fragment (the URI part after #) where the flow is used. Such as "fragment", in case the full URI is "https://app.domain.com#fragment". |
| `device.location.query` | string |  | yes | The query object where the flow is used. Such as {"q": "v"}. |
| `project.name` | string |  | yes | Project name that this flow runs in |
| `sourceIP` | ipaddress |  | yes | The originating IP address of the request that triggered the flow |
| `tenant.id` | string |  | yes | The tenant ID |
| `tenant.name` | string |  | yes | The tenant name |
| `tenant.domain` | string |  | yes | The tenant domain. |
| `tenant.domains` | string |  | yes | The tenant domains as array. |
| `tenant.enforceSSO` | boolean |  | yes | Indicates whether SSO is enforced for the tenant. |
| `tenant.subtenant` | boolean |  | yes | Indicates whether the tenant is a subtenant. |
| `tenant.enforceSSOExclusions` | string |  | yes | Specify login IDs that can bypass SSO authentication. |
| `tenant.disabled` | boolean |  | yes | Indicates whether the tenant is disabled. |
| `tenant.selfProvisionDomain` | string |  | yes | Email domain that allows tenant self provisioning. |
| `tenant.selfProvisionDomains` | string |  | yes | Array of email domains that allows tenant self provisioning. |
| `tenant.outbound.token.valid` | boolean |  |  | Indicates whether the tenant has valid outbound token. |
| `isEmailScanner` | boolean |  |  | Possibility of an e-mail scanner attempting to click a magic link detected |
| `inbound.authorize.resource` | string |  | yes | OIDC resource values that were sent by the application in the request to Descope |
| `inbound.authorize.scope` | string |  | yes | OIDC scope values that were sent by the application in the request to Descope |
| `oauthRequest.redirectUrl` | string |  | yes |  |
| `flowId` | string |  | yes | The ID of the flow being executed. e.g. 'sign-up-or-in'. |
| `flowExecutionId` | string |  | yes | The unique ID of the specific flow execution. |

## Risk (`riskInfo.*`, needs a risk/fingerprint connector)

What fills `riskInfo`: only a task, never a screen component on its own. A `connector` task whose command has the `risk` tag merges the command output's `riskInfo` into the context and sets `riskAssessmentId`; the `risk` action does too. Merging with an earlier risk result: booleans are OR-ed, `riskScore` takes the max. reCAPTCHA Enterprise (connector template `recaptcha-enterprise`): the screen's Recaptcha component only supplies the token; the `assess` command (tagged `risk`; `annotate` is not) writes `riskInfo.riskScore` = Google's score, **1.0 = human, 0.0 = bot** (so low is risky), and `riskInfo.botDetected` = score < the connector's `botThreshold` (default 0.5); its `smsRiskScore` is dropped (not a `riskInfo` field). The full output is also at `connectors.<resultPath>` (e.g. `connectors.recaptcha-enterprise_assess.riskAnalysis.score`).

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `riskInfo.riskScore` | number |  |  | A numerical value representing the risk score associated with a user's behavior or activity. |
| `riskInfo.smsRiskScore` | number |  |  | A numerical value representing the risk score associated with a user's SMS behavior or activity. |
| `riskInfo.botDetected` | boolean |  |  | Indicates whether a user is likely a bot based on their behavior or activity. |
| `riskInfo.trustedDevice` | boolean |  |  | Indication of whether this device has been marked as trusted before or not. |
| `riskInfo.impossibleTravel` | boolean |  |  | Indication of whether this user has connected from two different countries and the time between those connections can't be made through conventional air travel. |

## Risk, fingerprint connectors only

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `riskInfo.vpnDetected` | boolean |  |  | Indication of whether the end user is using a VPN. |
| `riskInfo.newDevice` | boolean |  |  | Indication of whether the end user is using a device that hasn't been spotted before in your application. |

## Known device

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `user.fingerprint.knownDevice` | boolean |  |  | Indication of whether the end user is using a device that has been spotted before in your application. |
| `fingerprint.knownDevice` | boolean |  |  | Indication of whether this device has been spotted before in your application. |

## Known device, Descope fingerprint only

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `user.descopeFingerprint.knownDevice` | boolean |  |  | Indication of whether the end user is using a device that has been spotted before in your application. |

## User agent (`userAgent.*`)

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `userAgent.mobile` | boolean |  | yes | Is request coming from a mobile device? |
| `userAgent.desktop` | boolean |  | yes | Is request coming from a PC? |
| `userAgent.device` | string |  | yes | Device type (present for iOS and Android devices) |
| `userAgent.raw` | string |  | yes | Raw User Agent header |
| `userAgent.name` | string |  | yes | Short agent name |
| `userAgent.os` | string |  | yes | Operating system |
| `userAgent.osVersion` | string |  | yes | Operating system version |
| `userAgent.tablet` | boolean |  | yes | Is request coming from a Tablet? |
| `userAgent.url` | string |  | yes | URL provided in case of a bot |
| `sourceUserAgent.mobile` | boolean |  | yes | Is request that originated the flow coming from a mobile device? |
| `sourceUserAgent.desktop` | boolean |  | yes | Is request that originated the flow coming from a PC? |
| `sourceUserAgent.device` | string |  | yes | Device type (present for iOS and Android devices) of request that originated the flow |
| `sourceUserAgent.raw` | string |  | yes | Raw User Agent header of request that originated the flow |
| `sourceUserAgent.name` | string |  | yes | Short agent name of request that originated the flow |
| `sourceUserAgent.os` | string |  | yes | Operating system of request that originated the flow |
| `sourceUserAgent.osVersion` | string |  | yes | Operating system version of request that originated the flow |
| `sourceUserAgent.tablet` | boolean |  | yes | Is request that originated the flow coming from a Tablet? |
| `sourceUserAgent.url` | string |  | yes | URL that originated the flow provided in case of a bot |

## Unauthenticated user extras

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `unauthUser.isDisabled` | boolean |  |  | Indicates whether the unauthenticated user is disabled. |

## Inbound app registration

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `inboundAppRegister.redirectURI` | string |  |  | The redirect URI that was asked during the application dynamic client registration request |
| `inboundAppRegister.scopes` | string |  |  | The scopes that were asked during the application dynamic client registration request |

## Outbound apps

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `outboundApp.type` | string |  |  | The type of the outbound application. |
| `outboundAppId` | string |  |  | Outbound Application ID |

## Agentic hub / MCP client (`mcpClient.*`)

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `mcpClient.id` | string |  |  |  |
| `mcpClient.name` | string |  |  |  |
| `mcpClient.description` | string |  |  |  |
| `mcpClient.logo` | string |  |  |  |
| `mcpClient.scopes` | string |  |  |  |
| `mcpClient.verified` | boolean |  |  |  |
| `mcpClient.user.consented` | boolean |  |  |  |
| `mcpClient.tenant.consented` | boolean |  |  |  |

## Management flows: triggering event (`triggeringEvent.*`)

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `triggeringEvent.type` | string |  |  | The type of event that triggered the flow execution. |
| `triggeringEvent.projectId` | string |  |  | The project ID where the event that triggered the flow execution occurred. |
| `triggeringEvent.userId` | string |  |  | The user ID associated with the event that triggered the flow execution. |
| `triggeringEvent.loginIds` | string |  |  | The login IDs associated with the event that triggered the flow execution. |
| `triggeringEvent.tenants` | string |  |  | The tenants associated with the event that triggered the flow execution. |
| `triggeringEvent.scim` | boolean |  |  | Indicates whether the event that triggered the flow execution is related to SCIM operations. |
| `triggeringEvent.changeData` | string |  |  | The change data associated with the event that triggered the flow execution. |
| `triggeringEvent.tenantId` | string |  |  | The tenant ID associated with the event that triggered the flow execution. |
| `triggeringEvent.tenantName` | string |  |  | The tenant name associated with the event that triggered the flow execution. |
| `triggeringEvent.tenantPreviousName` | string |  |  | The previous tenant name associated with the event that triggered the flow execution. |
| `triggeringEvent.tenantDomains` | string |  |  | The tenant domains associated with the event that triggered the flow execution. |
| `triggeringEvent.tenantPreviousDomains` | string |  |  | The previous tenant domains associated with the event that triggered the flow execution. |
| `triggeringEvent.tenantNames` | string |  |  | The tenant names associated with the event that triggered the flow execution. |
| `triggeringEvent.userIds` | string |  |  | The user IDs associated with the event that triggered the flow execution. |
| `triggeringEvent.count` | number |  |  | The number of entities affected by the event that triggered the flow execution. |
| `triggeringEvent.groupId` | string |  |  | The group ID associated with the event that triggered the flow execution. |
| `triggeringEvent.groupExternalId` | string |  |  | The group external ID associated with the event that triggered the flow execution. |
| `triggeringEvent.groupDisplayName` | string |  |  | The group display name associated with the event that triggered the flow execution. |
| `triggeringEvent.roleNames` | string |  |  | The role names associated with the event that triggered the flow execution. |
| `triggeringEvent.addedPermissions` | string |  |  | The permissions added in the event that triggered the flow execution. |
| `triggeringEvent.removedPermissions` | string |  |  | The permissions removed in the event that triggered the flow execution. |
| `triggeringEvent.scimAction` | string |  |  | The SCIM action associated with the event that triggered the flow execution. |
| `triggeringEvent.scimRequest` | string |  |  | The SCIM request data associated with the event that triggered the flow execution. |
| `triggeringEvent.scimResult` | string |  |  | The SCIM result data associated with the event that triggered the flow execution. |
| `triggeringEvent.scimError` | string |  |  | The SCIM error associated with the event that triggered the flow execution. |
| `triggeringEvent.user.id` | string |  |  | The user ID associated with the triggering event. |
| `triggeringEvent.user.ids` | string |  |  | The user IDs associated with the triggering event. |
| `triggeringEvent.user.loginIds` | string |  |  | The login IDs associated with the triggering event. |
| `triggeringEvent.user.tenants` | string |  |  | The tenants associated with the triggering event. |
| `triggeringEvent.user.scim` | boolean |  |  | Whether the user event was triggered via SCIM. |
| `triggeringEvent.user.changeData` | string |  |  | The change data associated with the triggering event. |
| `triggeringEvent.tenant.id` | string |  |  | The tenant ID associated with the triggering event. |
| `triggeringEvent.tenant.name` | string |  |  | The tenant name associated with the triggering event. |
| `triggeringEvent.tenant.previousName` | string |  |  | The previous tenant name associated with the triggering event. |
| `triggeringEvent.tenant.domains` | string |  |  | The tenant domains associated with the triggering event. |
| `triggeringEvent.tenant.previousDomains` | string |  |  | The previous tenant domains associated with the triggering event. |
| `triggeringEvent.tenant.names` | string |  |  | The tenant names associated with the triggering event. |
| `triggeringEvent.group.id` | string |  |  | The group ID associated with the triggering event. |
| `triggeringEvent.group.externalId` | string |  |  | The group external ID associated with the triggering event. |
| `triggeringEvent.group.displayName` | string |  |  | The group display name associated with the triggering event. |
| `triggeringEvent.group.tenants` | string |  |  | The tenants associated with the group event. |
| `triggeringEvent.group.scim` | boolean |  |  | Whether the group event was triggered via SCIM. |
| `triggeringEvent.role.roles` | string |  |  | The roles affected by the triggering event. Each role contains id, name, addedPermissions, and removedPermissions. |
| `triggeringEvent.scimEvent.action` | string |  |  | The SCIM action associated with the triggering event. |
| `triggeringEvent.scimEvent.userId` | string |  |  | The user ID associated with the SCIM event. |
| `triggeringEvent.scimEvent.loginIds` | string |  |  | The login IDs associated with the SCIM event. |
| `triggeringEvent.scimEvent.tenants` | string |  |  | The tenants associated with the SCIM event. |
| `triggeringEvent.scimEvent.changeData` | string |  |  | The change data associated with the SCIM event. |
| `triggeringEvent.scimEvent.request` | string |  |  | The SCIM request data associated with the triggering event. |
| `triggeringEvent.scimEvent.result` | string |  |  | The SCIM result data associated with the triggering event. |
| `triggeringEvent.scimEvent.error` | string |  |  | The SCIM error associated with the triggering event. |
| `triggeringEvent.samlCertExpiryEvent.window` | string |  |  | Which expiry window fired: '30d', '7d', or 'expired'. |
| `triggeringEvent.samlCertExpiryEvent.daysUntilExpiry` | number |  |  | Days until the SAML IdP certificate expires (negative if already expired). |
| `triggeringEvent.samlCertExpiryEvent.notAfter` | string |  |  | The SAML IdP certificate's NotAfter timestamp (RFC3339). |
| `triggeringEvent.samlCertExpiryEvent.samlSettingsId` | string |  |  | The ID of the tenant SAML SSO settings entry. |
| `triggeringEvent.samlCertExpiryEvent.ssoConfigName` | string |  |  | Display name of the tenant SAML SSO configuration. |
| `triggeringEvent.samlCertExpiryEvent.idpEntityId` | string |  |  | The IdP Entity ID configured on the tenant SAML SSO. |
| `triggeringEvent.samlCertExpiryEvent.idpSsoUrl` | string |  |  | The IdP SSO URL configured on the tenant SAML SSO. |
| `triggeringEvent.samlCertExpiryEvent.acsUrl` | string |  |  | The ACS URL configured for the tenant SAML SSO. |
| `triggeringEvent.samlCertExpiryEvent.certFingerprint` | string |  |  | SHA-256 fingerprint of the SAML IdP certificate. |
| `triggeringEvent.samlCertExpiryEvent.certSubject` | string |  |  | Subject DN of the SAML IdP certificate. |
| `triggeringEvent.samlCertExpiryEvent.certIssuer` | string |  |  | Issuer DN of the SAML IdP certificate. |
| `triggeringEvent.samlCertExpiryEvent.isAdditional` | boolean |  |  | True if the expiring cert is in the additional certs slot (idpCerts); false if it's the primary cert (idpCert). |
| `triggeringEvent.changeData.display_name` | string |  |  | The display name change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.given_name` | string |  |  | The given name change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.middle_name` | string |  |  | The middle name change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.family_name` | string |  |  | The family name change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.email` | string |  |  | The email change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.verified_email` | boolean |  |  | The verified email change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.phone` | string |  |  | The phone change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.verified_phone` | boolean |  |  | The verified phone change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.picture` | string |  |  | The picture change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.login_id` | string |  |  | The login ID change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.old_login_id` | string |  |  | The old login ID change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.original_login_id` | string |  |  | The original login ID change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.status` | string |  |  | The status change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.logout_time` | number |  |  | The logout time change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.logout_token` | string |  |  | The logout token change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.logout_device_removed` | boolean |  |  | The logout device removed change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.typed_logout_token` | string |  |  | The typed logout token change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.invalidate_jwt_family` | boolean |  |  | The invalidate JWT family change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.impersonate_consent` | boolean |  |  | The impersonate consent change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.user_expiration` | number |  |  | The user expiration change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.added_tenants` | string |  |  | The added tenants change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.remove_tenant` | string |  |  | The removed tenants change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.removed_roles` | string |  |  | The removed roles change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.added_roles` | string |  |  | The added roles change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.sso_apps` | string |  |  | The SSO apps change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_totp` | boolean |  |  | The using TOTP change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_passkeys` | boolean |  |  | The using Passkeys change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_password` | boolean |  |  | The using Password change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_saml` | boolean |  |  | The using SAML change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_scim` | boolean |  |  | The using SCIM change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_push` | boolean |  |  | The using Push change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_google` | boolean |  |  | The using Google change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_github` | boolean |  |  | The using GitHub change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_apple` | boolean |  |  | The using Apple change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_microsoft` | boolean |  |  | The using Microsoft change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_facebook` | boolean |  |  | The using Facebook change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_gitlab` | boolean |  |  | The using GitLab change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_discord` | boolean |  |  | The using Discord change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_linkedin` | boolean |  |  | The using LinkedIn change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.using_slack` | boolean |  |  | The using Slack change data associated with the event that triggered the flow execution. |
| `triggeringEvent.changeData.customAttributes` | string |  |  | The custom attributes change data associated with the event that triggered the flow execution. |
| `triggeringEvent.metadata.cfRay` | string |  |  | The Cloudflare Ray ID of the request that triggered the flow execution. |
| `triggeringEvent.metadata.occurred` | time |  |  | The timestamp of the event that triggered the flow execution. |
| `triggeringEvent.metadata.externalRequestId` | string |  |  | The X-Request-ID header of the request that triggered the flow execution. |
| `triggeringEvent.metadata.actorId` | string |  |  | The ID of the user or API key that initiated the event that triggered the flow execution. |
| `triggeringEvent.metadata.remoteAddress` | ipaddress |  |  | The IP address of the request that triggered the flow execution. |
| `triggeringEvent.metadata.country` | string |  |  | The country of the request that triggered the flow execution. |
| `triggeringEvent.metadata.userAgent` | string |  |  | The User-Agent header of the request that triggered the flow execution. |

## Keys not to use

| Key | Type | Values | Claim | Description |
|---|---|---|---|---|
| `user.isDisabled` | boolean |  |  | Don't use: reads false unless `unauthUser.isDisabled` was tested earlier in the flow. Use `unauthUser.isDisabled`. |
| `user.webAuthn` | boolean |  |  | Don't use: reads false unless `user.webauthn` was tested earlier in the flow. Use `user.webauthn`. |
