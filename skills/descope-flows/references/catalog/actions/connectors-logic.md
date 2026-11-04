# Actions: Connectors, scriptlets, lists, risk and utilities

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `add-to-list`

**Add to List**. Add one or more items to a list

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `AddToListFailed` (Error adding to list)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `listName` | list | yes | argument | List Name |
| `listItem` | string | yes | argument | Item; One value, a comma-separated list, a JSON array, or a {{context key}} that resolves to a list.; value may be a context key |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `calc-risk-score-ng`

**Calculate Risk Score**. Calculate Risk Score

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `CalcRiskScoreNGFailed` (Error calculating risk score)

- management flows: compatible
- tags: fraud, bots, risk, email, fake, accounts
- next interactionIds: `success`

Also reads from context when present: `email` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `check-if-disposable-email`

**Check if Disposable Email used**. Check if provided email is a disposable/burner email domain

**Error ids**: none declared.

- management flows: compatible
- tags: disposable, burner, email, webmail, mailbox, domain
- next interactionIds: `success`

Also reads from context when present: `email`, `maskedEmail` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `check-if-free-email`

**Check if free email provider used**. Check if provided email is a free email domain

**Error ids**: none declared.

- management flows: compatible
- tags: free, email, webmail, mailbox, domain
- next interactionIds: `success`

Also reads from context when present: `email` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `check-rate-limit`

**Check Rate Limit**. Enforce a per-minute request limit based on the user's origin. The rate limit is enforced across all flow executions.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ActionErrorCheckRateLimitExceeds` (Rate Limit Exceeded)

- license: `checkRateLimitAction`
- docs: https://docs.descope.com/knowledgebase/general/checkratelimit
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `rateLimitKey` | string (select) | yes | argument | Rate limit key; Select the entity to apply the rate limit on. IP - User's IP address, ASN - Autonomous System Number associated with the user's request, JA4 - User's device fingerprint.; options: `ip`, `asn`, `ja4` |
| `timeframe` | number (number) | yes | argument | Timeframe (in minutes); Timeframe in minutes for which the rate limit is enforced.; default `1` |
| `attempts` | number (number) | yes | argument | Max attempts per timeframe; Maximum number of allowed attempts in one timeframe. |

### `connector`

**Execute Connector**. Execute a connector

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConnectorFailed` (Connector execution error)
Plus the connector command's own error ids (`errors` of the command in the connector template): `http`: `request_error`; `http-static-ip`: `request_error`; `recaptcha-enterprise`: `create_assessment_error`, `assess_mismatch_action_error`, `annotate_assessment_error`.

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `connectorId` | string | yes | argument | Connector |
| `exchangeStepId` | string | yes | argument | Exchange Step ID |
| `command` | string | yes | argument | Connector command (e.g. get/post/put/delete) |
| `args` | list of `{key, type, value}` rows |  | argument | Command arguments (temp, will be replaced with a better UI) |
| `resultPath` | string |  | argument | Result Path (e.g. myResult) |
| `async` | boolean |  | argument |  |

Also reads from context when present: `context`, `startOptions`, `templateId` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `debug`

**debug**.

**Error ids**: none declared.

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `input` | string |  | argument |  |

### `decrypt`

**Decrypt Data**. Decrypt data using project encryption settings.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `DecryptFailed` (Error decrypting data), `DecryptFailedEmptyData` (Error decrypting data: empty data), `DecryptFailedInvalidData` (Error decrypting data: invalid data)

- management flows: compatible
- tags: decrypt, data
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `dataKey` | string | yes | argument | Data to decrypt from context; value may be a context key |
| `outputPath` | string | yes | argument | Result Path (Will go under `decrypt` (decrypt.<path>) in context) |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `email-connector`

**Execute email Connector**. Execute an email connector

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EmailConnectorFailed` (Error while executing email connector)

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `connectorId` | string | yes | argument | Connector |
| `to` | string | yes | argument | To |
| `subject` | string |  | argument | Subject |
| `bodyHtml` | html |  | argument | Body |
| `useExternalTemplate` | boolean |  | argument | Use External Template |
| `externalTemplateId` | string |  | argument | External Template ID; depends on `useExternalTemplate`; value may be a context key |
| `extraTemplateVals` | list of `{key, type, value}` rows |  | argument | Template Dynamic Keys; depends on `useExternalTemplate` |

Also reads from context when present: `context`, `templateId` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `encrypt`

**Encrypt Data**. Encrypt data using project encryption settings.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `EncryptFailed` (Error encrypting data), `EncryptFailedEmptyData` (Error encrypting data: empty data), `EncryptFailedInvalidData` (Error encrypting data: invalid data)

- management flows: compatible
- tags: encrypt, data
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `dataKey` | string | yes | argument | Data to encrypt from context; value may be a context key |
| `outputPath` | string | yes | argument | Result Path (Will go under `encrypt` (encrypt.<path>) in context) |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `generate-audit-event`

**Generate Audit Event**. Generate a custom audit event, that will be logged and available for usage in the project's Audit page (and any connected service).

**Error ids**: none declared.

- management flows: compatible
- tags: audit, event
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `customAuditActionName` | string | yes | argument | Action; value may be a context key |
| `customAuditType` | string (select) | yes | argument | Type; options: `info`, `warn`, `error` |
| `customAuditData` | list of `{key, type, value}` rows |  | argument | Data |
| `actorId` | string |  | argument | Actor ID; Optional actor to attribute the audit event to. Supports dynamic values such as {{user.userId}} in interactive flows, or {{triggeringEvent.metadata.actorId}} in management flows.; value may be a context key |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `im-connector`

**Execute IM Connector**. Execute an IM connector

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `IMConnectorFailed` (Error while executing im connector)

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `connectorId` | string | yes | argument | Connector |
| `phoneNumberTo` | string | yes | argument | To |
| `message` | html | yes | argument | Message |

Also reads from context when present: `context`, `templateId` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `load-mail-provider-host`

**Load Mail Provider Hostname**. Lookup and load the mail provider hostname (first MX record) of provided email

**Error ids**: none declared.

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- tags: mx, lookup, provider, webmail, mailbox
- next interactionIds: `success`

Also reads from context when present: `email`, `maskedEmail` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `redirect-to-url`

**Redirect to URL**. Redirect to a different URL as part of the flow.

**Error ids**: none declared.

- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `url` | string | yes | argument | Redirect URL; value may be a context key |
| `newTab` | boolean |  | argument | Open in a new tab |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `remove-from-list`

**Remove from List**. Remove one or more items from a list

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `RemoveFromListFailed` (Error removing from list)

- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `listName` | list | yes | argument | List Name |
| `listItem` | string | yes | argument | Item; One value, a comma-separated list, a JSON array, or a {{context key}} that resolves to a list.; value may be a context key |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `risk`

**Fingerprint / Assess**. Using fingerprinting techniques, Descope processes information from the authenticating user's session and decide if there's a risk. This is to identify odd behaviors, such as fraud attempts, and alert on them. Available only for Enterprise customers.

**Error ids**: none declared.
Note: never fails: when the fingerprint lookup errors it writes `riskInfo.riskScore` 0.2 with every boolean false and exits `success`, so an outage looks like a low-risk visitor and there is no error route.

- tags: fingerprint, fingerprinting, fraud, security
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `requestIds` | array | yes | context | Request IDs |

Also reads from context when present: `authInfo`, `externalId` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `scriptlet`

**Scriptlet**. Run JavaScript code to manipulate data from the Flow Context. The result of the script will be stored under the configured Context Key.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ScriptletFailed` (Script execution error)

- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `scriptArgs` | list of `{key, type, value}` rows | yes | argument | Script Arguments |
| `scriptCode` | string | yes | argument | Code |
| `outputPath` | string | yes | argument | **the result lands at `scripts.<outputPath>`, not under `scriptlets` as the label says**; Result Path (Will go under `scriptlets`, like we do for connectors with nice input) |
| `overrideForm` | list of `{key, type, value}` rows |  | argument |  |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `sms-connector`

**Execute SMS Connector**. Execute a SMS connector

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `SMSConnectorFailed` (Error while executing SMS connector)

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `connectorId` | string | yes | argument | Connector |
| `phoneNumberTo` | string | yes | argument | To |
| `message` | html | yes | argument | Message |

Also reads from context when present: `context`, `templateId` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `voice-connector`

**Execute voice call Connector**. Execute a voice call connector

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `VoiceConnectorFailed` (Error while executing voice call connector)

- hidden in the console's action picker (still valid in a flow)
- management flows: compatible
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `connectorId` | string | yes | argument | Connector |
| `phoneNumberTo` | string | yes | argument | To |
| `message` | html | yes | argument | Message |

Also reads from context when present: `context`, `templateId` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
