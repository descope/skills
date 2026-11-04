# Actions: Magic link: verify and other

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `finish-verify-recovery-magic-link`

**Finish Verify Recovery / Magic Link**. Consume the magic link token that was sent to the user's recovery destination and mark it as verified.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `FinishRecoveryVerificationFailed` (Recovery verification failed)

- tags: recovery, magic link
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `token` | string | yes | context | Token |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `verify-magic-link`

**Verify Code / Magic Link**. Verify the magic link token is the one that was generated as part of the Magic Link authentication.

**Error ids** (the `errorHandlingV2` keys and error `interactionId`s this action can take): `ConcurrentSessionsExceeded` (Maximum concurrent sessions reached), `MagicLinkVerifyFailed` (Error verifying Magic Link), `MagicLinkUpdateUserConflict` (User update failed due to conflict with existing user)
Note: reads only `token`, `deliveryMethod` and `skipVerify`. The console copies the send task's arguments (`uri`, `verifyStepId`, `providerId`, `templateId`...) onto this task; they do nothing at runtime, copy them for console fidelity. A copied `skipVerify: true` skips verification here.

- member of `password-send-reset-group`, `sign-in-embedded-link-group`, `sign-in-magic-link-email-group`, `sign-in-magic-link-sms-group`, `sign-in-magic-link-whatsapp-group`, `sign-in-magic-linkv2-email-group`, `sign-in-magic-linkv2-sms-group`, `sign-in-magic-linkv2-whatsapp-group`, `sign-in-magic-linkv3-email-group`, `sign-in-magic-linkv3-sms-group`, `sign-in-magic-linkv3-whatsapp-group`, `sign-up-embedded-link-group`, `sign-up-magic-link-email-group`, `sign-up-magic-link-sms-group`, `sign-up-magic-link-whatsapp-group`, `sign-up-or-in-embedded-link-group`, `sign-up-or-in-magic-link-email-group`, `sign-up-or-in-magic-link-sms-group`, `sign-up-or-in-magic-link-whatsapp-group`, `sign-up-or-in-magic-linkv3-email-group`, `sign-up-or-in-magic-linkv3-sms-group`, `sign-up-or-in-magic-linkv3-whatsapp-group`, `update-user-email-embedded-link-group`, `update-user-magic-link-email-group`, `update-user-magic-link-sms-group`, `update-user-magic-link-whatsapp-group`, `update-user-phone-embedded-link-group`
- hidden in the console's action picker (still valid in a flow)
- waits for user input
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `token` | string | yes | context | Token |

Also reads from context when present: `skipVerify`, `deliveryMethod` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).
