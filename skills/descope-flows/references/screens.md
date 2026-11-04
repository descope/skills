# Screens

A screen task shows one screen and waits for the user. The screen itself lives in the flow's `screens` array. Copy
screens from a recipe or a snippet (`catalog/screens/snippets/`) and change them; don't write the component tree from
scratch.

## Shape

```json
{
  "screenId": "SC2Vg93fMjRBPZgHypz0jXqxTMhfD",
  "interactions": [
    { "id": "S-VOZ5i7gc", "type": "button", "label": "Continue", "icon": "", "subType": "" },
    { "id": "t1ZEVL_dUC", "type": "button", "label": "Continue with Google", "icon": "google", "subType": "social" }
  ],
  "contents": { "ROOT": { "...": "..." }, "S-VOZ5i7gc": { "...": "..." } }
}
```

- Only these three keys. The MCP import rejects any other.
- `screenId`: the console makes `"SC"` plus 27 letters and digits; write ids that look like that and are unique in the
  flow. Never start one with `new-` (import drops the screen, `guardrails.md`).
- `contents` is a map from node id to node. `ROOT` is a `Container` with `isCanvas: true` and no `parent`. Every
  other node names its `parent`, and the parent lists it in `nodes`, in display order. The two must agree: a node not
  in its parent's `nodes` isn't shown, and an id in `nodes` with no node breaks the screen.
- Node ids: 10 characters of letters, digits, `-` and `_` (`S-VOZ5i7gc`), as the console makes them; `props.id`
  equals the node's key.
- `metadata.componentsVersion` must be set when the flow has screens: write `"2.1.13"`. Without it import treats the
  screens as version 1.0.0 and renames props.

## A node

```json
"S-VOZ5i7gc": {
  "type": { "resolvedName": "Button" },
  "displayName": "Button",
  "custom": { "type": "button" },
  "hidden": false,
  "isCanvas": false,
  "linkedNodes": {},
  "nodes": [],
  "parent": "ROOT",
  "props": { "id": "S-VOZ5i7gc", "children": "Continue", "data-type": "button", "formNoValidate": false,
             "full-width": true, "mode": "primary", "size": "md", "variant": "contained" }
}
```

- `type.resolvedName` must be a component from `catalog/screens/components.md` (inputs used in few templates, such
  as `DateInput`, `TextInput` and `Boolean`, are in `catalog/screens/inputs.md`). An unknown name imports, then the
  screen doesn't render and the console goes blank when it opens the flow.
- Copy `props` from the component's defaults in that file: import fills nothing in. Use only the props listed for
  the component (defaults, typed props, "Also reads"): any other prop is ignored when the screen renders.
- Copy `custom` too. The console derives the interactions from it: a button with `custom: {}` loses its rules the
  next time someone saves the flow in the console.

## What moves the flow on

| Component | Interaction id | Notes |
|---|---|---|
| A button (`custom.type: "button"`) | its `props.id` | Social buttons: `custom.subType: "social"`, interaction `icon: "<provider>"`, `subType: "social"` |
| `CodeInput` with `props.data-auto-submit: true` and `custom.type: "oneTimeCode"` | its `props.id` | Submits when all digits are in |
| `PollingLoader` with `custom.type: "polling"` | `polling` and `polling-error` | Magic and enchanted link waits. `polling-error` fires when the link expires: rule it to a "Polling expired" screen or back to the first screen, as the content templates do |

List each in `interactions`, and give the screen task one `next.rules` entry per interaction, with that id. An
interaction without a rule fails at runtime (`NextTaskNotFound`) when used; a rule for an id no component has never
fires, and the console drops it on save. Name a resend button `resend`, as the console does.

## Inputs

Each input posts its value under its `props.name`, which actions then read from the context:

| Component | `props.name` | Read by |
|---|---|---|
| `EmailInput` | `email` | `sign-up-or-in-otp-email` and other email actions |
| `PhoneInput` | `phone` | SMS and voice actions |
| `CodeInput` | `code` | `verify-code-otp-email` (it takes the login id from the send step: no email field on the code screen) |
| `FullNameInput` | `fullName` | `update-user-properties` via a row `{"key": "displayName", "type": "context", "value": "form.fullName"}` |

### Naming an input

- **Built-in inputs keep their bare name**: the components above and the other named inputs in
  `catalog/screens/components.md` (`firstName`, `lastName`, `externalId`, `newPassword`, `recoveryEmail`, ...). The
  engine knows these names, so a later task reads `email` or `form.email`, `fullName` or `form.fullName`.
- **Every input you name yourself is `form.<key>`**, both as `props.name` and wherever it is read: a `DateInput`
  is `"name": "form.dateOfBirth"` and a scriptlet or `update-user-properties` row reads `form.dateOfBirth`. This
  is what the console writes when you type a context key for `DateInput`, `TextInput`, `Boolean`, a select and
  the other inputs whose default name is `""`.
- A custom input with a bare name (`dateOfBirth`, a checkbox `rememberMe`) is lost: neither `dateOfBirth` nor
  `form.dateOfBirth` holds its value. Only names that start with `form.` go into the `form` map, and only the
  built-in `form.*` keys map back to bare names. The full built-in list is in `flow-structure.md` "Input names".

### What an input posts

The value arrives as the web component holds it, not as a string you might expect. Each input's **Submits** line in
`components.md` or `inputs.md` says what it is:

- `DateInput`: a number, epoch milliseconds (local midnight in the user's browser, or UTC midnight with
  `"utc-time": true`). Not a `YYYY-MM-DD` string. Set `utc-time: true` whenever a later step compares dates (an
  age check), and see the `date-of-birth` snippet for a scriptlet that reads it.
- `Boolean` (checkbox or switch): `true` or `false`.
- Multi selects: an array of the selected values.
- Text, email, password, number and code inputs: a string (a number input posts the digits as a string).

The screen task lists them: `inputKeys` (names of nodes with `custom.type: "input"`), `allInputKeys` (every
`props.name` on the screen) and `calculatedInputKeys: true`.

Social buttons need no input: `oauth-start` takes the provider from the button pressed (`data-descope-provider`),
with its `defaultProvider` left `""`.

## Text and errors

- `Text` shows context values with `{{...}}`, e.g. `{{sentTo.maskedEmail}}` on a code screen. List them in the
  task's `contextKeys`. A key that is unset shows as nothing (so does a value of `0`, `false` or `""`): "Attempts
  left: {{remainingOTPAttempts}}" reads "Attempts left: " on the first try. Hide such a Text with a condition
  (below) instead of adding a second screen.
- Put an `ErrorMessage` on every screen an action can fail back to: by default an action error returns the user to
  the last screen and shows there.

## Show, hide or disable a component

A screen task can change its components by a condition, evaluated each time the screen is shown. Add
`componentsConditions` to the screen task (not the screen):

```json
"componentsConditions": [
  {
    "id": "k3vq8rz1p",
    "name": "No attempt count yet",
    "rules": [
      { "atomicConditions": [
        { "operator": "empty", "target": { "type": "context", "value": "remainingOTPAttempts" } }
      ] }
    ],
    "then": { "action": "hide", "componentIds": ["<node id of the attempts Text>"] }
  }
]
```

- `then.action` is `hide`, `show` or `disable`; `componentIds` are node ids (`props.id`) on this screen.
- `rules` take the condition task's rule shape (`catalog/conditions.md`); the condition fires when any rule matches.
  When two conditions fire on one component, the later one wins.
- `empty` is true for an unset key, `""`, `null` and an empty list; a number (even `0`) is not empty.
- Wrong one-time codes: `remainingOTPAttempts` is unset on the first try and once the code is used up, and holds the
  attempts left after each wrong code (`patterns.md`, "Lock after N wrong codes"). The condition above shows
  "Attempts left: {{remainingOTPAttempts}}" only after a wrong code; the `ErrorMessage` shows the error each time.
  (Shape and operator from the engine source and a content template; this example has not been run end to end.)

