# Screen components

Generated from the flow editor's component settings, @descope/flow-components `3.26.0` (the version the screen renderer uses; prop types from its type declarations), the web components it renders (@descope/web-components-ui `3.26.0`, vaadin `24.3.4`) and the Descope flow templates (152). Do not edit by hand. Machine-readable: [components.json](components.json) (`knownProps` lists every prop a component reads).

Typed props are the ones the package declares. A component also reads the attributes of the web component it renders: they are listed after each table as "Also reads". A prop in none of these is ignored. Where a prop lists values, use one of them. **Submits** says what an input posts under its `props.name`: the flow reads that value as is (a `DateInput` posts a number, not a date string). Input components used in fewer than 3 templates (`DateInput`, `TextInput`, `Boolean`, the selects, ...) are in [inputs.md](inputs.md).

Each screen node is `{"type": {"resolvedName": <name>}, "props": {...}, "custom": {...}, ...}`. The name is the first column below. Import does not fill in defaults: a node renders with exactly the props it carries, so copy the defaults you need, and copy `custom` as listed (the console derives interactions from it). In `custom` only `type` and `subType` change behavior; other keys (e.g. Image `initialLight`) are editor hints you may leave out, and `{}` is right for a component listed with `{}`. Kinds: **input** (its `props.name` is the input key the next tasks read; a `oneTimeCode` input with `data-auto-submit: true` also submits the screen), **button** (its `props.id` is an interaction: list it in the screen's `interactions` and connect it with a next rule), **polling** (adds the interactions `polling` and `polling-error`), **other** (layout and display).

## Common components (used in 3 or more templates)

### Container

Container: kind other, used in 150 templates.

Node `custom`: `{}`

Renders as flow-components `Container`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `paddingX` | `"4"` | `string` |
| `paddingY` | `"8"` | `string` |
| `justify` | `"center"` | `'center' \| 'start' \| 'end' \| 'between' \| 'around' \| 'evenly'` |
| `background` | `"#ffffff00"` | `string` |
| `width` | `"100%"` | `string` |
| `align` | `"start"` | `'center' \| 'start' \| 'end' \| 'baseline' \| 'stretch'` |
| `direction` | `"row"` | `'row' \| 'column'` |
| `spaceBetween` | `"4"` | `'0' \| '0.5' \| '1' \| '1.5' \| '2' \| '2.5' \| '3' \| '3.5' \| '4' \| '5' \|...` |
| `data-editor-type` | `"container"` |  |
| `st-items-grow` | `0` |  |
| `shadow` | | `'md' \| 'lg' \| 'xl' \| '2xl'` |
| `borderRadius` | | `'sm' \| 'md' \| 'lg' \| 'xl' \| '2xl' \| '3xl'` |
| `backgroundImageUrl` | | `string` |
| `variant` | | `string` |
| `horizontal-alignment` | | `'center' \| 'start' \| 'end' \| 'space-between'` |
| `vertical-alignment` | | `'center' \| 'start' \| 'end'` |
| `space-between` | | `'sm' \| 'md' \| 'lg'` |

Also reads (`descope-collapsible-container`): `collapsed`, `collapsible`, `text`.

Theme values: `vertical-padding` `sm`, `md`, `lg`; `horizontal-padding` `sm`, `md`, `lg`; `border-radius` `sm`, `md`, `lg`, `xl`, `2xl`, `3xl`; `icon-position` `left`, `right`.

The console also writes (the pinned renderer ignores them): `connector`, `connectorName`.

### ErrorMessage

Error Message: kind other, used in 150 templates.

Node `custom`: `{}`

Renders as flow-components `Alert`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `mode` | `"error"` | `'error' \| 'success'` |
| `data-type` | `"error-message"` |  |
| `variant` | `"body1"` | `string` |
| `text-align` | `"center"` | `'left' \| 'right' \| 'center'` |
| `full-width` | `false` | `boolean` |
| `link-target-blank` | `true` | `boolean` |
| `bordered` | | `boolean` |
| `children` | | `string` |

Theme values: `spacing` `xs`, `sm`, `md`, `lg`, `xl`.

The console also writes (the pinned renderer ignores them): `align`, `color`, `hide-when-empty`, `italic`.

### Text

Text: kind other, used in 145 templates.

Node `custom`: `{}`

Renders as flow-components `Text`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `children` | `"Text"` |  |
| `italic` | `false` | `boolean` |
| `variant` | `"body1"` | `'h1' \| 'h2' \| 'h3' \| 'subtitle1' \| 'subtitle2' \| 'body1' \| 'body2'` |
| `text-align` | `"center"` | `'left' \| 'right' \| 'center'` |
| `full-width` | `false` | `boolean` |
| `mode` | `"primary"` | `'primary' \| 'secondary' \| 'error' \| 'error-dark' \| 'success' \| 'success-...` |
| `isEnriched` | `true` | `boolean` |
| `link-target-blank` | `true` |  |
| `hide-when-empty` | | `boolean` |
| `typography` | | `'body1' \| 'body2' \| 'subtitle1' \| 'h1' \| 'h2' \| 'h3' \| 'subtitle2'` |

Also reads (`descope-enriched-text`, `descope-text`): `readonly`.

The console also writes (the pinned renderer ignores them): `align`, `data-errormessage-value-missing`, `st-host-direction`.

### Button

Button: kind button, custom.type `button`, used in 138 templates.

Node `custom`: `{"type": "button"}`

Renders as flow-components `Button`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |
| `variant` | `"contained"` | `string` |
| `color` | `"primary"` | `string` |
| `children` | `"Click Me"` |  |
| `full-width` | `false` | `boolean` |
| `formNoValidate` | `false` |  |
| `data-type` | `"button"` |  |
| `loading` | | `boolean` |
| `startIcon` | | `string` |
| `startIconDark` | | `string` |
| `startIconColorText` | | `boolean` |
| `data-name` | | `string` |

Also reads (`descope-button`): the `vaadin-button` attributes (`inputs.md`).

Theme values: `mode` `primary`, `secondary`, `success`, `error`, `surface`.

The console also writes (the pinned renderer ignores them): `auto-submit`, `shape`, `st-host-direction`, `text-align`.

### EmailInput

Email Input: kind input, custom.type `input`, used in 96 templates.

Node `custom`: `{"type": "input"}`

Renders as flow-components `Input`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `label` | `"Email"` | `string` |
| `label-type` | `"static"` | `'static' \| 'floating'` |
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` |
| `placeholder` | `"Email"` | `string` |
| `full-width` | `true` | `boolean` |
| `max` | `100` |  |
| `required` | `false` |  |
| `bordered` | `true` | `boolean` |
| `copy-to-clipboard` | `false` |  |
| `data-errormessage-value-missing` | `"Please fill out this field."` | `string` |
| `name` | `"email"` |  |
| `type` | `"email"` |  |
| `pattern` | `"^[\\w\\.\\%\\+\\-']+@[\\w\\.\\-]+\\.[A-Za-z]{2,}$"` |  |
| `data-errormessage-pattern-mismatch` | `"Must be a valid email"` | `string` |
| `autoComplete` | `null` |  |
| `helper-text` | | `string` |
| `external-input` | | `boolean` |

Also reads (`descope-email-field`, `descope-new-email`): `invalid`; and the `vaadin-email-field` attributes and the `vaadin-text-field` attributes (`inputs.md`).

**Submits**: string.

### Divider

Divider: kind other, used in 78 templates.

Node `custom`: `{}`

Renders as flow-components `Divider`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `children` | `"Text"` | `string \| number \| false \| true \| ReactElement<any, string \| JSXElementCo...` |
| `italic` | `false` | `boolean` |
| `variant` | `"body1"` | `'body1' \| 'body2' \| 'subtitle1' \| 'h1' \| 'h2' \| 'h3' \| 'subtitle2'` |
| `vertical` | `false` | `boolean` |
| `mode` | `"primary"` | `'primary' \| 'secondary' \| 'error' \| 'success'` |

### Image

Image: kind other, used in 73 templates.

Node `custom`: `{"initialLight": true, "initialDark": true}`

Set yourself (the editor default is a console asset): `src` (an image URL), `src-dark` (an image URL).

Renders as flow-components `Image`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `alt` | `"Image"` | `string` |
| `width` | | `string` |
| `height` | | `string` |
| `src` | | `string` |
| `src-dark` | | `string` |

Theme values: `size` `xs`, `sm`, `md`, `lg`; `item-padding` `xs`, `sm`, `md`, `lg`, `xl`.

### Link

Link: kind other, used in 70 templates.

Node `custom`: `{}`

Renders as flow-components `Link`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `children` | `"Link"` | `string \| number \| false \| true \| ReactElement<any, string \| JSXElementCo...` |
| `italic` | `false` | `boolean` |
| `variant` | `"body1"` | `'body1' \| 'body2' \| 'subtitle1' \| 'h1' \| 'h2' \| 'h3' \| 'subtitle2'` |
| `text-align` | `"center"` | `'right' \| 'left' \| 'center'` |
| `full-width` | `false` | `boolean` |
| `target` | `"_blank"` |  |
| `href` | `""` | `string` |
| `mode` | `"primary"` | `'primary' \| 'secondary' \| 'error' \| 'success'` |
| `textAlign` | | `'left' \| 'right' \| 'center'` |
| `readonly` | | `boolean` |

### GoogleButton

Google Button: kind button, custom.type `button`, subType `social`, used in 62 templates.

Node `custom`: `{"type": "button", "subType": "social"}`

Renders as flow-components `Button`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |
| `variant` | `"outline"` | `string` |
| `color` | `"primary"` | `string` |
| `children` | `"Sign in with Google"` |  |
| `full-width` | `false` | `boolean` |
| `formNoValidate` | `true` |  |
| `data-type` | `"social"` |  |
| `startIcon` | `"google"` | `string` |
| `data-descope-provider` | `"google"` |  |
| `startIconColorText` | `false` | `boolean` |
| `st-label-spacing` | `"10px"` |  |
| `aria-label` | `"Sign in with Google"` |  |
| `loading` | | `boolean` |
| `startIconDark` | | `string` |
| `data-name` | | `string` |

Also reads (`descope-button`): the `vaadin-button` attributes (`inputs.md`).

Theme values: `mode` `primary`, `secondary`, `success`, `error`, `surface`.

The console also writes (the pinned renderer ignores them): `shape`, `text-align`.

### PollingLoader

Polling: kind polling, custom.type `polling`, used in 61 templates.

Node `custom`: `{"type": "polling"}`

Renders as flow-components `Loader`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |
| `variant` | `"linear"` | `'linear' \| 'radial'` |
| `color` | `"primary"` | `'primary' \| 'secondary' \| 'error' \| 'success'` |
| `data-type` | `"polling"` |  |

Theme values: `mode` `primary`, `secondary`.

### Logo

Logo: kind other, used in 56 templates.

Node `custom`: `{}`

Renders as flow-components `Logo`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `alt` | `"Logo"` |  |
| `width` | | `string` |
| `height` | | `string` |

### FullNameInput

Full Name Input: kind input, custom.type `input`, used in 42 templates.

Node `custom`: `{"type": "input", "contextKey": "displayName"}`

Renders as flow-components `Input`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `label` | `"Display Name"` | `string` |
| `label-type` | `"static"` | `'static' \| 'floating'` |
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` |
| `placeholder` | `"Display Name"` | `string` |
| `full-width` | `true` | `boolean` |
| `max` | `100` |  |
| `required` | `false` |  |
| `bordered` | `true` | `boolean` |
| `copy-to-clipboard` | `false` |  |
| `data-errormessage-value-missing` | `"Please fill out this field."` | `string` |
| `name` | `"fullName"` |  |
| `type` | `"text"` |  |
| `helper-text` | | `string` |
| `data-errormessage-pattern-mismatch` | | `string` |
| `external-input` | | `boolean` |

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### BiometricsButton

Biometrics Button: kind button, custom.type `button`, used in 26 templates.

Node `custom`: `{"type": "button"}`

Renders as flow-components `Button`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |
| `variant` | `"outline"` | `string` |
| `color` | `"primary"` | `string` |
| `children` | `""` |  |
| `full-width` | `false` | `boolean` |
| `formNoValidate` | `false` |  |
| `data-type` | `"biometrics"` |  |
| `startIcon` | `"fingerprint"` | `string` |
| `startIconColorText` | `true` | `boolean` |
| `st-label-spacing` | `"10px"` |  |
| `st-icon-color` | `"currentColor"` |  |
| `aria-label` | `"Sign in with biometrics"` |  |
| `loading` | | `boolean` |
| `startIconDark` | | `string` |
| `data-name` | | `string` |

Also reads (`descope-button`): the `vaadin-button` attributes (`inputs.md`).

Theme values: `mode` `primary`, `secondary`, `success`, `error`, `surface`.

The console also writes (the pinned renderer ignores them): `auto-submit`, `shape`.

### PhoneInput (component Phone)

Phone Input: kind input, custom.type `input`, used in 18 templates.

Node `custom`: `{"type": "input"}`

Renders as flow-components `Phone`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `name` | `"phone"` |  |
| `variant` | `"countrySelection"` | `'countrySelection' \| 'inputBox'` |
| `country-input-label` | `"Code"` |  |
| `country-input-placeholder` | `"Code"` | `string` |
| `phone-input-placeholder` | `"Phone"` | `string` |
| `type` | `"tel"` |  |
| `label` | `"Phone"` | `string` |
| `label-type` | `"static"` | `'static' \| 'floating'` |
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` |
| `full-width` | `true` | `boolean` |
| `bordered` | `true` | `boolean` |
| `default-code` | `"autoDetect"` | `string` |
| `autoComplete` | `null` |  |
| `data-errormessage-missing-value` | `"Required"` |  |
| `data-errormessage-pattern-mismatch-too-short` | `"Please enter a valid phone"` |  |
| `minlength` | `"6"` |  |
| `maxlength` | `"20"` |  |
| `format-value` | `false` | `boolean` |
| `strict-validation` | `false` | `boolean` |
| `data-errormessage-value-missing` | `"Please fill out this field."` | `string` |
| `data-errormessage-pattern-mismatch` | `"Please match the requested format."` | `string` |
| `placeholder` | | `string` |
| `helper-text` | | `string` |
| `external-input` | | `boolean` |
| `restrict-countries` | | `string` |

Also reads (`descope-phone-field`, `descope-phone-input-box-field`): `invalid`, `required`; and the `vaadin-text-field` attributes (`inputs.md`).

The console also writes (the pinned renderer ignores them): `max`.

**Submits**: string: the number with its country code. (Not yet checked end to end.)

### SSOButton

SSO Button: kind button, custom.type `button`, used in 18 templates.

Node `custom`: `{"type": "button"}`

Renders as flow-components `Button`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |
| `variant` | `"outline"` | `string` |
| `color` | `"primary"` | `string` |
| `children` | `""` |  |
| `full-width` | `false` | `boolean` |
| `formNoValidate` | `false` |  |
| `data-type` | `"sso"` |  |
| `startIcon` | `"sso"` | `string` |
| `startIconColorText` | `true` | `boolean` |
| `st-label-spacing` | `"10px"` |  |
| `st-icon-color` | `"currentColor"` |  |
| `aria-label` | `"Sign in with SSO"` |  |
| `loading` | | `boolean` |
| `startIconDark` | | `string` |
| `data-name` | | `string` |

Also reads (`descope-button`): the `vaadin-button` attributes (`inputs.md`).

Theme values: `mode` `primary`, `secondary`, `success`, `error`, `surface`.

### CodeInput (component Code)

One Time Code: kind input, custom.type `oneTimeCode`, used in 16 templates.

Node `custom`: `{"type": "oneTimeCode"}`

Renders as flow-components `Code`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `name` | `"code"` |  |
| `type` | `"tel"` |  |
| `label` | `"Code"` | `string` |
| `data-errormessage-pattern-mismatch` | `"Must be a 6 digit number"` | `string` |
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` |
| `fullWidth` | `false` |  |
| `required` | `true` |  |
| `bordered` | `true` | `boolean` |
| `digits` | `6` | `number` |
| `data-auto-submit` | `false` |  |
| `data-errormessage-value-missing` | `"Please fill out this field."` | `string` |
| `placeholder` | | `string` |
| `full-width` | | `boolean` |
| `helper-text` | | `string` |
| `label-type` | | `'static' \| 'floating'` |
| `external-input` | | `boolean` |

Also reads (`descope-passcode`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

**Submits**: string: the digits typed.

### MicrosoftButton

Microsoft Button: kind button, custom.type `button`, subType `social`, used in 11 templates.

Node `custom`: `{"type": "button", "subType": "social"}`

Renders as flow-components `Button`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |
| `variant` | `"outline"` | `string` |
| `color` | `"primary"` | `string` |
| `children` | `"Sign in with Microsoft"` |  |
| `full-width` | `false` | `boolean` |
| `formNoValidate` | `true` |  |
| `data-type` | `"social"` |  |
| `startIcon` | `"microsoft"` | `string` |
| `data-descope-provider` | `"microsoft"` |  |
| `startIconColorText` | `false` | `boolean` |
| `st-label-spacing` | `"10px"` |  |
| `aria-label` | `"Sign in with Microsoft"` |  |
| `loading` | | `boolean` |
| `startIconDark` | | `string` |
| `data-name` | | `string` |

Also reads (`descope-button`): the `vaadin-button` attributes (`inputs.md`).

Theme values: `mode` `primary`, `secondary`, `success`, `error`, `surface`.

The console also writes (the pinned renderer ignores them): `text-align`.

### ScopesList

Inbound App Scopes: kind other, used in 10 templates.

Node `custom`: `{}`

Renders as flow-components `ScopesList`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `name` | `"thirdPartyAppApproveScopes"` |  |
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |
| `variant` | `"checkbox"` | `'checkbox' \| 'switch'` |
| `st-gap` | `"0em"` |  |
| `data` | | `Item$1[]` |
| `readonly` | | `boolean` |

### ThirdPartyAppLogo

Inbound App Logo: kind other, used in 9 templates.

Node `custom`: `{}`

Renders as flow-components `ThirdPartyAppLogo`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |

### TenantSwitcherComboBox

Tenant Switcher: kind other, used in 6 templates.

Node `custom`: `{}`

Renders as flow-components `ComboBox`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `data` | `[]` |  |
| `label` | `"Switch Tenant"` | `string` |
| `placeholder` | `"Choose Tenant"` | `string` |
| `name` | `"userSelectedTenant"` |  |
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` |
| `full-width` | `false` | `boolean` |
| `required` | `false` |  |
| `bordered` | `true` | `boolean` |
| `item-label-path` | `"data-name"` | `string` |
| `item-value-path` | `"data-id"` | `string` |
| `data-errormessage-value-missing` | `"Please select tenant."` | `string` |
| `children` | | `string & Element[] \| number & Element[] \| false & Element[] \| true & Eleme...` |
| `helper-text` | | `string` |
| `data-errormessage-pattern-mismatch` | | `string` |
| `label-type` | | `'static' \| 'floating'` |
| `external-input` | | `boolean` |
| `default-value` | | `string` |

Also reads (`descope-combo-box`): `invalid`, `require-match`; and the `vaadin-combo-box` attributes (`inputs.md`).

### NewPassword

New Password: kind input, custom.type `input`, used in 5 templates.

Node `custom`: `{"type": "input"}`

Renders as flow-components `NewPassword`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `name` | `"newPassword"` |  |
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` |
| `bordered` | `true` | `boolean` |
| `full-width` | `true` | `boolean` |
| `has-confirm` | `false` | `boolean` |
| `has-validation` | `false` | `boolean` |
| `password-label` | `"Password"` | `string` |
| `password-placeholder` | `"Password"` | `string` |
| `confirm-label` | `"Confirm password"` | `string` |
| `confirm-placeholder` | `"Confirm password"` | `string` |
| `active-policies` | `[]` | `string[]` |
| `autocomplete` | `"new-password"` |  |
| `policy-label` | `"Your password must have at least:"` | `string` |
| `data-password-policy-message-minlength` | `"{{value}} characters"` | `string` |
| `data-password-policy-message-lowercase` | `"1 lowercase letter"` | `string` |
| `data-password-policy-message-uppercase` | `"1 uppercase letter"` | `string` |
| `data-password-policy-message-anyletter` | `"1 letter (any case)"` | `string` |
| `data-password-policy-message-number` | `"1 number"` | `string` |
| `data-password-policy-message-nonalphanumeric` | `"1 symbol"` | `string` |
| `data-password-policy-message-passwordstrength` | `"Password strength"` | `string` |
| `data-password-policy-message-disallowedchars` | `"Does not contain: {{value}}"` | `string` |
| `data-password-policy-message-disallowemail` | `"Does not match your email"` | `string` |
| `st-policy-preview-padding` | `"0"` | `string` |
| `label-type` | `"static"` | `'static' \| 'floating'` |
| `external-input` | `false` | `boolean` |
| `data-errormessage-value-missing` | `"Please fill out this field."` | `string` |
| `data-errormessage-pattern-mismatch` | `"Passwords do not match"` | `string` |
| `data-errormessage-type-mismatch` | `"Value does not comply with requirements"` |  |
| `placeholder` | | `string` |
| `label` | | `string` |
| `helper-text` | | `string` |
| `data-password-policy-pattern-minlength` | | `string` |
| `data-password-policy-pattern-lowercase` | | `string` |
| `data-password-policy-pattern-uppercase` | | `string` |
| `data-password-policy-pattern-anyletter` | | `string` |
| `data-password-policy-pattern-number` | | `string` |
| `data-password-policy-pattern-nonalphanumeric` | | `string` |
| `data-password-policy-message-reuse` | | `string` |
| `data-password-policy-value-minlength` | | `string` |
| `data-password-policy-value-disallowedchars` | | `string` |
| `data-password-policy-value-email` | | `string` |
| `data-password-policy-value-reuse` | | `string` |
| `st-policy-preview-background-color` | | `string` |

Also reads (`descope-new-password`): `invalid`, `required`; and the `vaadin-text-field` attributes (`inputs.md`).

The console also writes (the pinned renderer ignores them): `confirmInputProps`.

**Submits**: string.

### Password

Login Password: kind other, used in 5 templates.

Node `custom`: `{}`

Renders as flow-components `Password`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `name` | `"password"` |  |
| `type` | `"password"` |  |
| `placeholder` | `"Password"` | `string` |
| `label` | `"Password"` | `string` |
| `label-type` | `"static"` | `'static' \| 'floating'` |
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl'` |
| `full-width` | `true` | `boolean` |
| `bordered` | `true` | `boolean` |
| `external-input` | `false` | `boolean` |
| `autocomplete` | `"current-password"` |  |
| `data-errormessage-value-missing` | `"Please fill out this field."` | `string` |
| `helper-text` | | `string` |
| `data-errormessage-pattern-mismatch` | | `string` |

Also reads (`descope-password`): `invalid`, `manual-visibility-toggle`, `required`; and the `vaadin-password-field` attributes (`inputs.md`).

### PasskeyButton

Passkey Button: kind button, custom.type `button`, used in 4 templates.

Node `custom`: `{"type": "button"}`

Renders as flow-components `Button`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `size` | `"md"` | `'xs' \| 'sm' \| 'md' \| 'lg'` |
| `variant` | `"outline"` | `string` |
| `color` | `"primary"` | `string` |
| `children` | `""` |  |
| `full-width` | `false` | `boolean` |
| `formNoValidate` | `false` |  |
| `data-type` | `"biometrics"` |  |
| `startIcon` | `"passkey"` | `string` |
| `startIconColorText` | `true` | `boolean` |
| `st-label-spacing` | `"10px"` |  |
| `st-icon-color` | `"currentColor"` |  |
| `aria-label` | `"Sign in with passkey"` |  |
| `loading` | | `boolean` |
| `startIconDark` | | `string` |
| `data-name` | | `string` |

Also reads (`descope-button`): the `vaadin-button` attributes (`inputs.md`).

Theme values: `mode` `primary`, `secondary`, `success`, `error`, `surface`.

The console also writes (the pinned renderer ignores them): `auto-submit`, `shape`.

### TOTPImage

TOTP Code: kind other, used in 4 templates.

Node `custom`: `{}`

Renders as flow-components `TOTPImage`.

| Prop | Editor default | Type (flow-components, or the theme's values) |
|---|---|---|
| `height` | `100` | `string` |
| `alt` | `"QR Code"` |  |
| `component` | `"code"` | `'text' \| 'code'` |
| `variant` | `"body1"` | `'body1' \| 'body2' \| 'subtitle1' \| 'h1' \| 'h2' \| 'h3' \| 'subtitle2'` |
| `mode` | `"primary"` | `'primary' \| 'secondary' \| 'error' \| 'success'` |
| `children` | `"{{totp.key}}"` | `string` |
| `text-align` | `"center"` | `'left' \| 'right' \| 'center'` |
| `width` | | `string` |
| `hide-when-empty` | | `boolean` |

Also reads (`descope-enriched-text`, `descope-text`, `descope-totp-image`): `full-width`, `link-target-blank`, `readonly`.

## All other components

| Name | Label | Kind | Renders as | Templates | Key defaults |
|---|---|---|---|---|---|
| `AccessKeyActivateButton` | Activate Access Key | button | `Button` | 0 | `children`="Activate", `data-type`="button" |
| `AccessKeyCreateButton` | Create Access Key | button | `Button` | 0 | `children`="+ Access Key", `data-type`="button" |
| `AccessKeyDeactivateButton` | Deactivate Access Key | button | `Button` | 0 | `children`="Deactivate", `data-type`="button" |
| `AccessKeyDeleteButton` | Delete Access Key | button | `Button` | 0 | `children`="Delete", `data-type`="button" |
| `AccessKeyRotateButton` | Rotate Access Key | button | `Button` | 0 | `children`="Rotate", `data-type`="button" |
| `AppleButton` | Apple Button | button | `Button` | 0 | `children`="Sign in with Apple", `data-type`="social", `startIcon`="apple", `data-descope-provider`="apple" |
| `AppsList` | Applications | other | `AppsList` | 0 |  |
| `AuditLogsExportButton` | Export Audit Logs | button | `Button` | 0 | `children`="Export", `data-type`="button" |
| `Avatar` | Avatar | other | `Avatar` | 0 |  |
| `Badge` | Badge | other | `Badge` | 0 |  |
| `BuiltInUserAttribute` | User Attribute | other | `UserAttribute` | 0 |  |
| `CertificateTextarea` | Certificate Textarea | other | `Textarea` | 1 | `name`="idpCert" |
| `ClientSecretInput` | Client Secret Input | other | `Input` | 1 | `name`="clientSecret" |
| `CodeSnippet` | Code Snippet | other | `CodeSnippet` | 1 | `children`="{ \"key\": \"value\" }" |
| `CollapsibleContainer` | Collapsible Container | other | `CollapsibleContainer` | 0 |  |
| `ContextTextarea` | Textarea | other | `Textarea` | 0 | `name`="" |
| `CustomProviderButton` | Oauth Button | button | `Button` | 0 | `children`="", `data-type`="social", `startIcon`="" |
| `CustomTenantUserAttribute` | Custom Tenant Attribute | other | `UserAttribute` | 0 |  |
| `CustomUserAttribute` | Custom User Attribute | other | `UserAttribute` | 0 |  |
| `DiscordButton` | Discord Button | button | `Button` | 0 | `children`="Sign in with Discord", `data-type`="social", `startIcon`="discord", `data-descope-provider`="discord" |
| `EmailDomainsTenantUserAttribute` | Email Domains Attribute | other | `UserAttribute` | 0 |  |
| `EmailUserAttribute` | User Email Attribute | other | `UserAttribute` | 0 |  |
| `EnforceSSOTenantUserAttribute` | Enforce SSO Attribute | other | `UserAttribute` | 0 |  |
| `FacebookButton` | Facebook Button | button | `Button` | 1 | `children`="Sign in with Facebook", `data-type`="social", `startIcon`="facebook", `data-descope-provider`="facebook" |
| `ForceSSOExclusionTenantUserAttribute` | Force SSO Exclusions Attribute | other | `UserAttribute` | 0 |  |
| `GenericFlowButton` | Button | button | `Button` | 0 | `children`="Click Me", `data-type`="button" |
| `GithubButton` | Github Button | button | `Button` | 0 | `children`="Sign in with Github", `data-type`="social", `startIcon`="github", `data-descope-provider`="github" |
| `GitlabButton` | Gitlab Button | button | `Button` | 0 | `children`="Sign in with Gitlab", `data-type`="social", `startIcon`="gitlab", `data-descope-provider`="gitlab" |
| `Grid` | Table | other | `Grid` | 0 |  |
| `GridCustomColumn` | EditorGridCustomColumn | other | `GridCustomColumn` | 0 |  |
| `GridItemDetailsColumn` | EditorGridItemDetailsColumn | other | `GridItemDetailsColumn` | 0 |  |
| `GridSelectionColumn` | GridSelectionColumn | other | `GridSelectionColumn` | 0 |  |
| `GridTextColumn` | EditorGridTextColumn | other | `GridTextColumn` | 0 |  |
| `Hcaptcha` | hCaptcha | other | `Hcaptcha` | 0 | `name`="hcaptcha" |
| `Honeypot` | Bot trap | other | `Honeypot` | 1 | `name`="dhp-ponyhot" |
| `LastAuthBadge` | Last Auth Badge | other | `LastAuthBadge` | 0 | `data-type`="last-auth-badge" |
| `LinkedinButton` | LinkedIn Button | button | `Button` | 0 | `children`="Sign in with LinkedIn", `data-type`="social", `startIcon`="linkedin", `data-descope-provider`="linkedin" |
| `LogoutButton` | Logout Button | button | `Button` | 0 | `children`="Logout", `data-type`="button" |
| `MultiSso` | Multi SSO | other | `MultiSso` | 0 |  |
| `NOTPImage` | NOTP Code | other | `NOTPImage` | 2 | `children`="{{notp.key}}" |
| `NOTPLink` | NOTP Redirect URL | other | `Link` | 2 | `children`="Redirect URL" |
| `NameTenantUserAttribute` | Name Attribute | other | `UserAttribute` | 0 |  |
| `NameUserAttribute` | User Name Attribute | other | `UserAttribute` | 0 |  |
| `OAuthUserAuthMethod` | OAuth | other | `UserAuthMethod` | 0 |  |
| `OutboundAppButton` | Outbound Application | button | `OutboundAppButton` | 0 | `data-type`="button" |
| `OutboundApps` | Outbound Applications | other | `OutboundApps` | 0 |  |
| `PasskeyUserAuthMethod` | Passkey Authentication Method | other | `UserAuthMethod` | 0 |  |
| `PasswordUserAuthMethod` | Password Authentication Method | other | `UserAuthMethod` | 0 |  |
| `PhoneUserAttribute` | User Phone Attribute | other | `UserAttribute` | 0 |  |
| `Recaptcha` | reCAPTCHA | other | `Recaptcha` | 1 |  |
| `RecaptchaV2` | reCAPTCHA V3 | other | `RecaptchaV2` | 0 |  |
| `RecoveryCodeInput` | Recovery Code Input | other | `Input` | 1 | `name`="recoveryCode" |
| `RecoveryCodesList` | Recovery Codes | other | `RecoveryCodesList` | 1 |  |
| `RecoveryCodesUserAuthMethod` | Recovery Codes Authentication Method | other | `UserAuthMethod` | 0 |  |
| `RoleCreateButton` | Create Role | button | `Button` | 0 | `children`="+ Role", `data-type`="button" |
| `RoleDeleteButton` | Delete Role | button | `Button` | 0 | `children`="Delete", `data-type`="button" |
| `RoleDuplicateButton` | Duplicate Role | button | `Button` | 0 | `children`="Duplicate", `data-type`="button" |
| `RoleEditButton` | Edit Role | button | `Button` | 0 | `children`="Edit", `data-type`="button" |
| `SecurityQuestionsSetup` | Security Questions Setup | other | `SecurityQuestionsSetup` | 1 | `name`="sqSetup" |
| `SecurityQuestionsVerify` | Security Questions Verify | other | `SecurityQuestionsVerify` | 2 | `name`="sqVerify" |
| `Select` | Time Filter | other | `Select` | 0 | `name`="" |
| `SlackButton` | Slack Button | button | `Button` | 1 | `children`="Sign in with Slack", `data-type`="social", `startIcon`="slack", `data-descope-provider`="slack" |
| `TOTPLink` | TOTP Provision URL | other | `Link` | 1 | `children`="Provision URL" |
| `TOTPUserAuthMethod` | TOTP User Auth Method | other | `UserAuthMethod` | 0 |  |
| `TenantAdminSSOLink` | SSO Setup Link Attribute | other | `Link` | 0 | `children`="SSO Setup" |
| `TenantPasswordPolicyUserAuthMethod` | Tenant Password Policy | other | `UserAuthMethod` | 0 |  |
| `TenantSelector` | Current Tenant Selector | other | `TenantSelector` | 0 | `name`="tenantSelector" |
| `TenantSessionSettingsUserAuthMethod` | Tenant Session Settings | other | `UserAuthMethod` | 0 |  |
| `Textarea` | Textarea | other | `Textarea` | 0 |  |
| `TimerButton` | Timer | button | `TimerButton` | 0 | `children`="Resend", `data-type`="button" |
| `TrustedDevices` | Trusted Devices | other | `TrustedDevices` | 0 |  |
| `Turnstile` | Turnstile | other | `Turnstile` | 0 |  |
| `UserAttribute` |  | other | `UserAttribute` | 0 |  |
| `UserAuthMethod` |  | other | `UserAuthMethod` | 0 |  |
| `UserManagementActivateButton` | Activate User | button | `Button` | 0 | `children`="Activate", `data-type`="button" |
| `UserManagementCreateButton` | Create User | button | `Button` | 0 | `children`="+ User", `data-type`="button" |
| `UserManagementDeleteButton` | Delete User | button | `Button` | 0 | `children`="Delete", `data-type`="button" |
| `UserManagementDisableButton` | Disable User | button | `Button` | 0 | `children`="Disable", `data-type`="button" |
| `UserManagementEditButton` | Edit User | button | `Button` | 0 | `children`="Edit", `data-type`="button" |
| `UserManagementRemovePasskeyButton` | Remove Passkey | button | `Button` | 0 | `children`="Remove passkey", `data-type`="button" |
| `UserManagementResetPasswordButton` | Reset Password | button | `Button` | 0 | `children`="Reset password", `data-type`="button" |
| `UserPasskeys` | Passkeys | other | `UserPasskeys` | 0 |  |
| `WhatsappButton` | WhatsApp Button | button | `Button` | 2 | `children`="Sign in with WhatsApp", `data-type`="button", `startIcon`="whatsapp", `data-descope-provider`="whatsapp" |

The other input components (59, from `APIKeyInput` to `UserInfoEndpointUrlInput`) are in [inputs.md](inputs.md), each with its defaults, the attributes it reads and what it submits.

## Names the console saves under an alias

The editor registers these components under a second name and saves nodes with it (CraftJS resolves the last registered name). Write the saved name; the component name also loads.

| Saved as (write this) | Component | Templates using saved name | Templates using component name |
|---|---|---|---|
| `CodeInput` | `Code` | 62 | 16 |
| `CustomIdentifierInput` | `CustomLoginIdInput` | 7 | 0 |
| `PhoneInput` | `Phone` | 15 | 18 |
| `RecaptchaV2` | `RecaptchaV3` | 0 | 0 |
