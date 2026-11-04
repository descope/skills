# Actions: Other

Generated from Descope's action definitions. Do not edit by hand.

Inputs with Source `context` are filled from the context key of the same name (for example a screen input with that name); pass them as arguments only to override. Inputs with Source `argument` are set in the task's `arguments` as `{"type": "inline" | "context", "value": ...}`. Argument names not listed here are ignored at runtime. Every action can exit through `success`; to route an error yourself, set `"errorHandlingV2": {"<ErrorType>": {"errorHandlingType": "custom"}}` on the task and add a next rule with `interactionId` `<ErrorType>`. See [the catalog README](../README.md).

### `clear-last-error`

**Clear Last Error**. Clear the last error

**Error ids**: none declared.

- tags: clear, error
- next interactionIds: `success`

No inputs.

### `management-end`

**End**. Ends a management flow and configures the wanted output if specified

**Error ids**: none declared.

- ends the flow
- management flows: managementOnly
- tags: end, management
- next interactionIds: `success`

| Input | Type | Required | Source | Notes |
|---|---|---|---|---|
| `output` | list of `{key, type, value}` rows |  | argument | Flow output |

Also reads from context when present: `context` (hidden inputs: each reads the context key of its name; a task argument of the same name overrides it).

### `reset-form`

**Reset Form**. Reset all user input data

**Error ids**: none declared.

- tags: reset, form
- next interactionIds: `success`

No inputs.
