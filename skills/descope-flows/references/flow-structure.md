# Flow JSON Structure and Validation Rules

## Top-Level Structure

Every exported flow JSON has exactly two top-level keys:

```json
{
  "flow": { ... },
  "screens": [ ... ]
}
```

## Flow Object

The `flow` object contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String | Yes | Flow identifier (e.g., `sign-up-or-in`) |
| `name` | String | Yes | Display name |
| `description` | String | No | Flow description |
| `version` | Number | Yes | Schema version |
| `disabled` | Boolean | No | Whether flow is disabled |

Plus internal graph structure fields (nodes, edges, step configurations) — these vary by flow and should not be authored manually.

## Screens Array

Each screen object in the `screens` array represents a UI screen shown to users during the flow.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String | Yes | Screen identifier, referenced by screen steps in the flow |
| `version` | Number | No | Screen version |
| `htmlTemplate` | Object | Yes | Screen layout and widget definitions |
| `components` | Array | Varies | UI components (inputs, buttons, text, containers) |

## Flow Components

### Screens (UI)

Screen steps display a UI to the user. Each screen step references a screen by its `id` from the `screens` array.

Common screen widgets:
- **Input fields**: Email, phone, password, OTP code, custom text
- **Buttons**: Submit, social login providers, back navigation
- **Text**: Headers, descriptions, error messages, links
- **Containers**: Layout grouping for widgets

Widget `context` keys store user input for use in subsequent flow steps (e.g., `form.email`, `form.phone`).

### Actions (Backend Operations)

Actions execute server-side operations. Common action types:

| Action | Purpose |
|--------|---------|
| Send OTP | Send verification code via email/SMS/voice |
| Verify OTP | Validate code entered by user |
| Send Magic Link | Send passwordless login link |
| Verify Magic Link | Validate clicked link |
| Create User | Register new user account |
| Update User | Modify user attributes |
| Get User | Fetch user data |
| Generate TOTP | Create TOTP secret for authenticator apps |
| Verify TOTP | Validate TOTP code |
| WebAuthn Register | Register a passkey |
| WebAuthn Verify | Authenticate with a passkey |
| OAuth Start | Begin OAuth flow with provider |
| SSO Start | Begin SSO authentication |
| Run Connector | Execute a configured connector |
| Run Scriptlet | Execute custom JavaScript logic |

### Connectors

Connector steps call external services. The connector must be configured in the Descope project.

Response data is stored under `connectors.<contextKey>`:
- `connectors.<contextKey>.statusCode` — HTTP status code
- `connectors.<contextKey>.body` — Response body
- `connectors.<contextKey>.headers` — Response headers

### Conditions

Condition steps branch the flow based on expressions:
- Check user attributes
- Check connector response codes/data
- Check flow context values
- Check form input values

Conditions must have both a **true** and **false** branch connected to subsequent steps.

### Subflows

Subflow steps invoke another flow by its ID. The referenced flow must exist in the project.

## Validation Rules

### Structural Rules

1. **Valid JSON** — File must parse as valid JSON
2. **Top-level keys** — Must have `flow` and `screens`
3. **Flow ID required** — `flow.id` must be present and non-empty
4. **Flow name required** — `flow.name` must be present and non-empty
5. **Flow version** — `flow.version` should be present

### Reference Integrity Rules

6. **Screen references** — Every screen step in the flow must reference a screen `id` that exists in the `screens` array
7. **No orphan screens** — Every screen in the `screens` array should be referenced by at least one screen step (warning, not error)
8. **Connector references** — Every connector step must reference a connector configured in the target project
9. **Subflow references** — Every subflow step must reference a flow ID that exists in the target project

### Logical Rules

10. **Reachable nodes** — All flow steps should be reachable from the start node
11. **Condition branches** — Condition steps must have both true and false branches
12. **No dead ends** — Non-terminal steps should have at least one outgoing edge (except for success/failure terminals)
13. **Context key usage** — Steps that read context keys (e.g., `form.email`) should have a preceding step that writes that key

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Dangling screen reference | Screen step references a screen not in `screens` array | Add the missing screen or fix the reference |
| Missing connector | Flow references a connector not configured in the project | Configure the connector in the project first |
| Unreachable nodes | Steps not connected to the flow graph | Connect orphan steps or remove them |
| Missing flow ID | `flow.id` is empty or missing | Set a valid flow ID from the allowed list |
| Invalid context key | Step reads a key that's never written | Ensure a preceding step writes the required key |
