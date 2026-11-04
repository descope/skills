# Input components

Generated with [components.md](components.md), from the same sources. Do not edit by hand. The inputs used in 3 or more templates are in components.md; these are the others.

Defaults are the editor's: copy them into `props` and set `name` (a key you choose is `form.<key>`, see `../../screens.md`). **Submits** is what the input posts under its `props.name`.

## Wrapped vaadin fields

Most inputs render a vaadin field and pass every prop on to it as an attribute, so these are read too:

| Field | Attributes |
|---|---|
| `vaadin-checkbox` | `autofocus`, `checked`, `disabled`, `indeterminate`, `label` |
| `vaadin-combo-box` | `accessible-name`, `allow-custom-value`, `allowed-char-pattern`, `auto-open-disabled`, `autofocus`, `autoselect`, `clear-button-visible`, `data-provider`, `disabled`, `error-message`, `filter`, `filtered-items`, `helper-text`, `invalid`, `item-label-path`, `item-value-path`, `items`, `label`, `loading`, `opened`, `overlay-class`, `page-size`, `pattern`, `placeholder`, `readonly`, `required`, `selected-item`, `size`, `title` |
| `vaadin-custom-field` | `accessible-name`, `error-message`, `format-value`, `helper-text`, `inputs`, `invalid`, `label`, `parse-value`, `required` |
| `vaadin-email-field` | `accessible-name`, `allowed-char-pattern`, `autocapitalize`, `autocomplete`, `autocorrect`, `autofocus`, `autoselect`, `clear-button-visible`, `disabled`, `error-message`, `helper-text`, `invalid`, `label`, `maxlength`, `minlength`, `pattern`, `placeholder`, `readonly`, `required`, `title` |
| `vaadin-multi-select-combo-box` | `accessible-name`, `allow-custom-value`, `allowed-char-pattern`, `auto-expand-horizontally`, `auto-expand-vertically`, `autofocus`, `autoselect`, `clear-button-visible`, `data-provider`, `disabled`, `error-message`, `filter`, `helper-text`, `i18n`, `invalid`, `item-id-path`, `item-label-path`, `item-value-path`, `items`, `label`, `loading`, `opened`, `overlay-class`, `page-size`, `placeholder`, `readonly`, `required`, `selected-items`, `selected-items-on-top`, `size`, `title` |
| `vaadin-number-field` | `accessible-name`, `allowed-char-pattern`, `autocapitalize`, `autocomplete`, `autocorrect`, `autofocus`, `autoselect`, `clear-button-visible`, `disabled`, `error-message`, `helper-text`, `invalid`, `label`, `max`, `min`, `placeholder`, `readonly`, `required`, `step`, `step-buttons-visible`, `title` |
| `vaadin-password-field` | `accessible-name`, `allowed-char-pattern`, `autocapitalize`, `autocomplete`, `autocorrect`, `autofocus`, `autoselect`, `clear-button-visible`, `disabled`, `error-message`, `helper-text`, `i18n`, `invalid`, `label`, `maxlength`, `minlength`, `password-visible`, `pattern`, `placeholder`, `readonly`, `required`, `reveal-button-hidden`, `title` |
| `vaadin-radio-group` | `accessible-name`, `disabled`, `error-message`, `helper-text`, `invalid`, `label`, `readonly`, `required` |
| `vaadin-text-field` | `accessible-name`, `allowed-char-pattern`, `autocapitalize`, `autocomplete`, `autocorrect`, `autofocus`, `autoselect`, `clear-button-visible`, `disabled`, `error-message`, `helper-text`, `invalid`, `label`, `maxlength`, `minlength`, `pattern`, `placeholder`, `readonly`, `required`, `title` |

## Components

### APIKeyInput

API Key: custom `{"type": "input", "contextKey": "apiKey"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "API Key", "label-type": "static", "size": "md", "placeholder": "API Key", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "apiKey", "type": "password"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-password`): `invalid`, `manual-visibility-toggle`; and the `vaadin-password-field` attributes (`inputs.md`).

**Submits**: string.

### AddressField

Address Input: custom `{"type": "input"}`, renders as flow-components `AddressField`, used in 0 templates.

Defaults: `{"name": "form.address", "label": "Address", "label-type": "static", "size": "md", "type": "address", "placeholder": "Enter address", "full-width": true, "required": false, "bordered": true, "data-connector-id": "", "connector-template": "", "min-search-length": "", "allow-custom-value": false, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`.

Also reads (`descope-address-field`): `invalid`; and the `vaadin-custom-field` attributes (`inputs.md`).

**Submits**: not yet documented; check before a flow reads it.

### AuthorizationEndpointUrlInput

Authorization Endpoint Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "Authorization Endpoint", "label-type": "static", "size": "md", "placeholder": "Authorization Endpoint", "full-width": true, "max": 100, "required": true, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "authUrl", "type": "url", "pattern": "^https?:\\/\\/(?:www.)?(?:(?:[\\-a-zA-Z0-9@\\:%\\._\\+~#=]{1,256}.[a-zA-Z0-9\\(\\)]{1,6})|localhost)(?:[\\-a-zA-Z0-9\\(\\)@:%_\\+\\.~#\\?&\\/\\/=]*)$", "data-errormessage-pattern-mismatch": "Must be a valid URL"}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### Boolean

Boolean Input: custom `{"type": "input"}`, renders as flow-components `Boolean`, used in 0 templates.

Defaults: `{"label": "Boolean Input", "size": "md", "full-width": true, "required": false, "checked": false, "bordered": true, "type": "checkbox", "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `placeholder`, `helper-text`, `data-errormessage-pattern-mismatch`, `label-type` (static \| floating), `external-input`.

Also reads (`descope-checkbox`): `invalid`; and the `vaadin-text-field` attributes and the `vaadin-checkbox` attributes (`inputs.md`).

**Submits**: boolean: `true` when checked, `false` when not.

### ClientIdInput

Client ID Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "Client ID", "label-type": "static", "size": "md", "placeholder": "Client ID", "full-width": true, "max": 100, "required": true, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "clientId"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### ContextBoolean

Boolean input: custom `{"type": "input", "dynamicContext": true}`, renders as flow-components `Boolean`, used in 0 templates.

Defaults: `{"label": "Boolean input", "size": "md", "full-width": true, "required": false, "checked": false, "bordered": true, "type": "checkbox", "data-errormessage-value-missing": "Please fill out this field.", "name": "", "placeholder": "Boolean input"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `label-type` (static \| floating), `external-input`.

Also reads (`descope-checkbox`): `invalid`; and the `vaadin-text-field` attributes and the `vaadin-checkbox` attributes (`inputs.md`).

**Submits**: boolean: `true` when checked, `false` when not.

### ContextInput

Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"name": "", "label": "Input", "label-type": "static", "size": "md", "placeholder": "Input", "full-width": true, "max": 100, "required": false, "bordered": true, "copyToClipboard": false, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `copy-to-clipboard`, `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### ContextKeyInput

Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 2 templates.

Defaults: `{"name": "", "label": "Input", "label-type": "static", "size": "md", "placeholder": "Input", "full-width": true, "max": 100, "required": false, "bordered": true, "copyToClipboard": false, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `copy-to-clipboard`, `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### CountrySubdivisionCityField

Country / State / City: custom `{"type": "input"}`, renders as flow-components `CountrySubdivisionCityField`, used in 0 templates.

Defaults: `{"bordered": true, "name": "location", "country-label": "Country", "country-placeholder": "Country", "city-label": "City", "city-placeholder": "City", "horizontal": false, "st-flex-gap": "1em", "label-type": "static", "size": "md", "full-width": false, "required": false, "lang": "autoDetect", "data-source-base-url": "https://static.descope.com/dynamic/descope-content-main/address/en"}`

Typed: `placeholder`, `value`, `label`, `helper-text`, `data-errormessage-pattern-mismatch`, `data-errormessage-value-missing`, `hide-country`, `hide-subdivision`, `hide-city`, `default-country`, `allowed-countries`, `pinned-countries`, `subdivision-label`, `subdivision-placeholder`.

Also reads (`descope-country-subdivision-city-field`): `invalid`; and the `vaadin-custom-field` attributes (`inputs.md`).

**Submits**: not yet documented; check before a flow reads it.

### CustomIdentifierInput (component CustomLoginIdInput)

Custom Login ID Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "Custom Login ID", "label-type": "static", "size": "md", "placeholder": "Custom Login ID", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "externalId", "type": "text", "autoComplete": null}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### DateInput

Date Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"name": "", "label": "Date Input", "label-type": "static", "years-range": "1900-2099", "format": "MM/DD/YYYY", "size": "md", "type": "date", "placeholder": "Enter date", "full-width": true, "required": false, "bordered": true, "disable-calendar": false, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-date-field`): `calendar-months`, `calendar-weekdays`, `initial-value`, `opened`, `pattern`, `readonly`, `utc-time`.

**Submits**: number: epoch milliseconds of the chosen date (`""` when empty or invalid). Local midnight in the user's browser, unless the node has `utc-time: true` (then UTC midnight). Not a `YYYY-MM-DD` string: a scriptlet gets the number and builds a date with `new Date(value)`.

### DocumentUploadFile

Upload Image: custom `{"type": "input"}`, renders as flow-components `UploadFile`, used in 0 templates.

Defaults: `{"size": "md", "full-width": false, "required": false, "button-variant": "outline", "button-mode": "primary", "bordered": true, "data-errormessage-value-missing": "Please upload a file.", "title": "Upload a document", "description": "Click the button below to upload a document", "icon": "<data:image/svg+xml data URI, 482 chars>", "button-label": "Upload", "accept": "image/*,application/pdf", "name": "document"}`

Typed: `readonly`.

Also reads (`descope-upload-file`): `pattern`.

**Submits**: not yet documented; check before a flow reads it.

### DynamicMultiSelect

Dynamic Multi Select: custom `{"type": "input"}`, renders as flow-components `MultiSelect`, used in 0 templates.

Defaults: `{"name": "", "variant": "dynamicCombobox", "label": "Dynamic Multi Select", "label-type": "static", "size": "md", "placeholder": "Submit values using Enter", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `data`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### EmailDomainsMultiSelect

Email Domains: custom `{"type": "input", "dynamicContext": true, "dynamicContextKey": "tenantEmailDomains"}`, renders as flow-components `MultiSelect`, used in 0 templates.

Defaults: `{"name": "tenantEmailDomains", "variant": "dynamicCombobox", "label": "Email Domains", "label-type": "static", "size": "md", "placeholder": "Email Domains", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field.", "allow-custom-value": true, "data": []}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### EmailInvitesInput

Email Invite Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "Invitees", "label-type": "static", "size": "md", "placeholder": "invitee1@email.com;invitee2@email.com", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "invitees", "type": "text", "pattern": "^[\\w\\.\\%\\+\\-']+@[\\w\\.\\-]+\\.[A-Za-z]{2,}(;[\\w\\.\\%\\+\\-]+@[\\w\\.\\-]+\\.[A-Za-z]{2,})*$", "data-errormessage-pattern-mismatch": "Must be a valid email", "autoComplete": null}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### EnforceSSOBoolean

Enforce SSO: custom `{"type": "input", "dynamicContext": true, "dynamicContextKey": "enforceSSO"}`, renders as flow-components `Boolean`, used in 0 templates.

Defaults: `{"label": "Enforce SSO", "size": "md", "full-width": true, "required": false, "checked": false, "bordered": true, "type": "checkbox", "data-errormessage-value-missing": "Please fill out this field.", "name": "enforceSSO", "placeholder": "Enforce SSO"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `label-type` (static \| floating), `external-input`.

Also reads (`descope-checkbox`): `invalid`; and the `vaadin-text-field` attributes and the `vaadin-checkbox` attributes (`inputs.md`).

**Submits**: boolean: `true` when checked, `false` when not.

### EntityIdInput

IdP Entity ID: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "IdP Entity ID", "label-type": "static", "size": "md", "placeholder": "IdP Entity ID", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "entityId", "type": "text"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### FirstNameInput

First Name Input: custom `{"type": "input", "contextKey": "givenName"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "Given Name", "label-type": "static", "size": "md", "placeholder": "Given Name", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "firstName", "type": "text"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### GrantTypeSingleSelect

Grant Type Input: custom `{"type": "input"}`, renders as flow-components `SingleSelect`, used in 1 templates.

Defaults: `{"name": "grantType", "variant": "combobox", "data": [{"value": "authorization_code", "label": "Authorization code"}, {"value": "implicit", "label": "Implicit"}], "label": "Grant Type", "label-type": "static", "placeholder": "Grant Type", "size": "md", "full-width": true, "required": false, "bordered": true, "allowClearValue": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `default-value`, `layout` (vertical \| horizontal).

Also reads (`descope-button-selection-group`, `descope-combo-box`, `descope-radio-group`): `invalid`, `require-match`; and the `vaadin-text-field` attributes and the `vaadin-combo-box` attributes and the `vaadin-radio-group` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string: the selected item's value (`""` when none).

### HybridField

Email or Phone: custom `{"type": "input"}`, renders as flow-components `HybridField`, used in 1 templates.

Defaults: `{"name": "externalId", "bordered": true, "label": "Email or Phone", "size": "md", "placeholder": "Insert email or phone", "full-width": true, "required": false, "label-type": "static", "phone-variant": "countrySelection", "phone-input-label": "Phone", "phone-format-value": false, "phone-strict-validation": false, "country-input-label": "Code", "country-input-placeholder": "Code", "external-input": false, "default-code": "autoDetect"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `data-errormessage-value-missing`, `variant` (countrySelection \| inputBox), `phone-input-placeholder`, `restrict-countries`, `data-errormessage-pattern-mismatch-email`, `data-errormessage-value-missing-email`, `data-errormessage-value-missing-phone`.

**Submits**: string: the value of whichever field is active.

### IDPMetadataUrlInput

IdP Metadata URL: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "IdP Metadata URL", "label-type": "static", "size": "md", "placeholder": "IdP Metadata URL", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "idpMetadataURL", "type": "url", "pattern": "^https?:\\/\\/(?:www.)?(?:(?:[\\-a-zA-Z0-9@\\:%\\._\\+~#=]{1,256}.[a-zA-Z0-9\\(\\)]{1,6})|localhost)(?:[\\-a-zA-Z0-9\\(\\)@:%_\\+\\.~#\\?&\\/\\/=]*)$", "data-errormessage-pattern-mismatch": "Must be a valid URL"}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### ImpersonateIDInput

Impersonated User: custom `{"type": "input"}`, renders as flow-components `Input`, used in 2 templates.

Defaults: `{"label": "Impersonated user", "label-type": "static", "size": "md", "placeholder": "Login ID of the impersonated user", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "impersonateId"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### Input

Text Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "Input", "label-type": "static", "size": "md", "placeholder": "Input", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### IssuerInput

Issuer Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "Issuer", "label-type": "static", "size": "md", "placeholder": "Issuer", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "issuer"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### JwksEndpointUrlInput

JWKs Endpoint Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "JWKs Endpoint", "label-type": "static", "size": "md", "placeholder": "JWKs Endpoint", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "jwksUrl", "type": "url", "pattern": "^https?:\\/\\/(?:www.)?(?:(?:[\\-a-zA-Z0-9@\\:%\\._\\+~#=]{1,256}.[a-zA-Z0-9\\(\\)]{1,6})|localhost)(?:[\\-a-zA-Z0-9\\(\\)@:%_\\+\\.~#\\?&\\/\\/=]*)$", "data-errormessage-pattern-mismatch": "Must be a valid URL"}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### LastNameInput

Last Name Input: custom `{"type": "input", "contextKey": "familyName"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "Family Name", "label-type": "static", "size": "md", "placeholder": "Family Name", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "lastName", "type": "text"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### LoginUrlInput

IdP Login URL: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "IdP Login URL", "label-type": "static", "size": "md", "placeholder": "IdP Login URL", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "idpURL", "type": "url", "pattern": "^https?:\\/\\/(?:www.)?(?:(?:[\\-a-zA-Z0-9@\\:%\\._\\+~#=]{1,256}.[a-zA-Z0-9\\(\\)]{1,6})|localhost)(?:[\\-a-zA-Z0-9\\(\\)@:%_\\+\\.~#\\?&\\/\\/=]*)$", "data-errormessage-pattern-mismatch": "Must be a valid URL"}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### MonthDayInput

Month-Day Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"name": "", "label": "Month/Day Input", "label-type": "static", "format": "MM/DD", "placeholder": "Enter date", "size": "md", "type": "month-day", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-month-day-field`): `disable-picker`, `initial-value`, `opened`, `pattern`, `picker-label-cancel`, `picker-label-submit`, `picker-months`, `readonly`.

**Submits**: string: month and day in the node's `format` (e.g. `"03/14"`), `""` when empty.

### MultiSelect

Multi Select: custom `{"type": "input"}`, renders as flow-components `MultiSelect`, used in 0 templates.

Defaults: `{"name": "", "variant": "combobox", "data": [{"value": "Value1", "label": "Value1"}, {"value": "Value2", "label": "Value2"}, {"value": "Value3", "label": "Value3"}], "label": "Multi Select", "label-type": "static", "size": "md", "placeholder": "Enter items", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### NumericInput

Numeric Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"type": "number", "placeholder": "Number", "label": "Number", "label-type": "static", "data-errormessage-pattern-mismatch": "Must be a valid number", "autoComplete": null, "size": "md", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-number-field`): `invalid`; and the `vaadin-number-field` attributes (`inputs.md`).

**Submits**: string: the digits typed (not a JSON number).

### OIDCUserAttributesMappings

OIDC User Attribute Mapping: custom `{"type": "input"}`, renders as flow-components `MappingsField`, used in 1 templates.

Defaults: `{"name": "oidcMappings", "size": "md", "full-width": true, "bordered": true, "label-value": "IdP User Value", "label-attr": "User Attribute", "button-label": "Add user attribute mapping", "separator": "map to", "options": [{"value": "email", "label": "Email"}, {"value": "name", "label": "Display Name"}, {"value": "givenName", "label": "Given Name"}, {"value": "middleName", "label": "Middle Name"}, {"value": "familyName", "label": "Family Name"}, {"value": "picture", "label": "Picture"}, {"value": "phoneNumber", "label": "Phone Number"}, {"value": "verifiedEmail", "label": "Verified Email"}, {"value": "verifiedPhone", "label": "Verified Phone Number"}], "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `label-type` (static \| floating), `external-input`, `default-values`.

Also reads (`descope-mappings-field`): `invalid`, `required`; and the `vaadin-custom-field` attributes (`inputs.md`).

**Submits**: not yet documented; check before a flow reads it.

### PhotoUploadFile

Take Photo: custom `{"type": "input"}`, renders as flow-components `UploadFile`, used in 0 templates.

Defaults: `{"size": "md", "full-width": false, "required": false, "button-variant": "outline", "button-mode": "primary", "bordered": true, "data-errormessage-value-missing": "Please upload a file.", "title": "Take a selfie", "description": "Click the button below to open your camera", "icon": "<data:image/svg+xml data URI, 1062 chars>", "button-label": "Take Photo", "accept": "image/*", "name": "photo"}`

Typed: `readonly`.

Also reads (`descope-upload-file`): `pattern`.

**Submits**: not yet documented; check before a flow reads it.

### PromptMultiSelect

Prompt Input: custom `{"type": "input"}`, renders as flow-components `MultiSelect`, used in 1 templates.

Defaults: `{"name": "prompt", "variant": "combobox", "data": [{"value": "none", "label": "None"}, {"value": "login", "label": "Login"}, {"value": "consent", "label": "Consent"}, {"value": "select_account", "label": "Select account"}], "label": "Prompt", "label-type": "static", "size": "md", "placeholder": "Prompt", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### ProviderNameInput

Provider Name Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "Provider Name", "label-type": "static", "size": "md", "placeholder": "Provider Name", "full-width": true, "max": 100, "required": true, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "providerName"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### RecoveryEmailInput

Recovery Email Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "Recovery Email", "label-type": "static", "size": "md", "placeholder": "Recovery Email", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "recoveryEmail", "type": "email", "pattern": "^[\\w\\.\\%\\+\\-']+@[\\w\\.\\-]+\\.[A-Za-z]{2,}$", "data-errormessage-pattern-mismatch": "Must be a valid email", "autoComplete": null}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-email-field`, `descope-new-email`): `invalid`; and the `vaadin-email-field` attributes and the `vaadin-text-field` attributes (`inputs.md`).

**Submits**: string.

### RecoveryPhone

Recovery Phone: custom `{"type": "input"}`, **does not render**, used in 0 templates.

Defaults: `{"name": "recoveryPhone", "variant": "countrySelection", "country-input-label": "Code", "country-input-placeholder": "Code", "phone-input-placeholder": "Recovery Phone", "type": "tel", "label": "Recovery Phone", "label-type": "static", "size": "md", "full-width": true, "bordered": true, "default-code": "autoDetect", "autoComplete": null, "data-errormessage-missing-value": "Required", "data-errormessage-pattern-mismatch-too-short": "Please enter a valid phone", "minlength": "6", "maxlength": "20", "format-value": false, "strict-validation": false, "data-errormessage-value-missing": "Please fill out this field.", "data-errormessage-pattern-mismatch": "Please match the requested format."}`

**Submits**: not yet documented; check before a flow reads it.

### RolesMultiSelect

Roles Selector: custom `{"type": "input", "requiresRolesList": true}`, renders as flow-components `MultiSelect`, used in 0 templates.

Defaults: `{"name": "userRoles", "variant": "combobox", "data": [{"value": "Value1", "label": "Value1"}, {"value": "Value2", "label": "Value2"}, {"value": "Value3", "label": "Value3"}], "label": "Roles", "label-type": "static", "size": "md", "placeholder": "Roles", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### SAMLGroupMappings

SAML Group Mapping: custom `{"type": "input", "requiresSAMLGroupMappingsRoles": true}`, renders as flow-components `SAMLGroupMappings`, used in 1 templates.

Defaults: `{"name": "samlGroupMappings", "size": "md", "full-width": true, "bordered": true, "label-value": "IdP Group Name", "label-attr": "Role", "label-group": "Group Attribute Name", "button-label": "Add group mapping", "separator": "map to", "options": [], "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `label-type` (static \| floating), `external-input`.

Also reads (`descope-saml-group-mappings`): `invalid`, `required`; and the `vaadin-custom-field` attributes (`inputs.md`).

**Submits**: not yet documented; check before a flow reads it.

### SAMLUserAttributesMappings

SAML User Attribute Mapping: custom `{"type": "input"}`, renders as flow-components `MappingsField`, used in 1 templates.

Defaults: `{"name": "samlMappings", "size": "md", "full-width": true, "bordered": true, "label-value": "IdP User Value", "label-attr": "User Attribute", "button-label": "Add user attribute mapping", "separator": "map to", "options": [{"value": "email", "label": "Email"}, {"value": "name", "label": "Display Name"}, {"value": "givenName", "label": "Given Name"}, {"value": "middleName", "label": "Middle Name"}, {"value": "familyName", "label": "Family Name"}, {"value": "picture", "label": "Picture"}, {"value": "phoneNumber", "label": "Phone Number"}, {"value": "verifiedEmail", "label": "Verified Email"}, {"value": "verifiedPhone", "label": "Verified Phone Number"}], "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `label-type` (static \| floating), `external-input`, `default-values`.

Also reads (`descope-mappings-field`): `invalid`, `required`; and the `vaadin-custom-field` attributes (`inputs.md`).

**Submits**: not yet documented; check before a flow reads it.

### SCIMKeyInput

SCIM Access Key: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "SCIM Access Key", "label-type": "static", "size": "md", "placeholder": "", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": true, "data-errormessage-value-missing": "Please fill out this field.", "name": "scimKey", "type": "text", "readOnly": true}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### SCIMUrlInput

SCIM URL: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "SCIM URL", "label-type": "static", "size": "md", "placeholder": "", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": true, "data-errormessage-value-missing": "Please fill out this field.", "name": "scimUrl", "type": "text", "readOnly": true}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### SPACSUrlInput

SP ACS URL: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "SP ACS URL", "label-type": "static", "size": "md", "placeholder": "SP ACS URL", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": true, "data-errormessage-value-missing": "Please fill out this field.", "name": "spAcsUrl", "type": "url", "readOnly": true}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### SPEntityIdInput

SP Entity ID: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "SP Entity ID", "label-type": "static", "size": "md", "placeholder": "SP Entity ID", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": true, "data-errormessage-value-missing": "Please fill out this field.", "name": "spEntityId", "type": "text", "readOnly": true}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### SPMetadataUrlInput

SP Metadata URL: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "SP Metadata URL", "label-type": "static", "size": "md", "placeholder": "SP Metadata URL", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": true, "data-errormessage-value-missing": "Please fill out this field.", "name": "spMetadataUrl", "type": "url", "readOnly": true}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### SPOIDCCallbackUrlInput

SP OIDC Callback URL: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "SP OIDC Callback URL", "label-type": "static", "size": "md", "placeholder": "SP OIDC Callback URL", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": true, "data-errormessage-value-missing": "Please fill out this field.", "name": "oidcCallBackUrl", "type": "url", "readOnly": true}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### SSOAppsMultiSelect

SSO Apps Selector: custom `{"type": "input", "requiresSSOAppsList": true}`, renders as flow-components `MultiSelect`, used in 0 templates.

Defaults: `{"name": "ssoApplications", "variant": "combobox", "data": [{"value": "Value1", "label": "Value1"}, {"value": "Value2", "label": "Value2"}, {"value": "Value3", "label": "Value3"}], "label": "Applications", "label-type": "static", "size": "md", "placeholder": "Applications", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### SSOExclusionsMultiSelect

SSO Exclusions: custom `{"type": "input", "dynamicContext": true, "dynamicContextKey": "enforceSSOExclusions"}`, renders as flow-components `MultiSelect`, used in 0 templates.

Defaults: `{"name": "enforceSSOExclusions", "variant": "dynamicCombobox", "label": "SSO Exclusions", "label-type": "static", "size": "md", "placeholder": "SSO exclusion list", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field.", "allow-custom-value": true, "data": []}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### ScopesMultiSelect

Scopes Input: custom `{"type": "input"}`, renders as flow-components `MultiSelect`, used in 1 templates.

Defaults: `{"name": "scope", "variant": "dynamicCombobox", "label": "Scopes", "label-type": "static", "size": "md", "placeholder": "Scopes", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `data`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### SelfProvisionDomainsInput

Self Provision Domains: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "Self Provision Domains", "label-type": "static", "size": "md", "placeholder": "Self Provision Domains", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "selfProvisionDomains"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### SingleSelect

Single Select: custom `{"type": "input"}`, renders as flow-components `SingleSelect`, used in 0 templates.

Defaults: `{"name": "", "variant": "combobox", "data": [{"value": "Value1", "label": "Value1"}, {"value": "Value2", "label": "Value2"}, {"value": "Value3", "label": "Value3"}], "label": "Single Select", "label-type": "static", "size": "md", "placeholder": "Single Select", "full-width": true, "required": false, "bordered": true, "allowClearValue": true, "require-match": true, "data-has-dynamic-attr-values": true, "data-errormessage-value-missing": "Please fill out this field.", "data-errormessage-pattern-mismatch": "Please select an option from the list"}`

Typed: `children`, `helper-text`, `external-input`, `default-value`, `layout` (vertical \| horizontal).

Also reads (`descope-button-selection-group`, `descope-combo-box`, `descope-radio-group`): `invalid`; and the `vaadin-text-field` attributes and the `vaadin-combo-box` attributes and the `vaadin-radio-group` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string: the selected item's value (`""` when none).

### TableWidgetsSearchInput

Search: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"name": "", "label": "", "label-type": "static", "size": "sm", "placeholder": "Search", "full-width": false, "max": 100, "required": false, "bordered": true, "copyToClipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "data-id": "search-input", "data-testid": "search-input", "id": "search"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `copy-to-clipboard`, `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### TenantDomainInput

Tenant Domain: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "Tenant Domain", "label-type": "static", "size": "md", "placeholder": "Tenant Domain", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "tenantDomain"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### TenantDomainsMultiSelect

SSO Domains Input: custom `{"type": "input"}`, renders as flow-components `MultiSelect`, used in 1 templates.

Defaults: `{"name": "tenantDomains", "variant": "dynamicCombobox", "label": "SSO Domains", "label-type": "static", "size": "md", "placeholder": "SSO Domains", "full-width": true, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `children`, `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`, `data`, `min-items-selection`, `max-items-selection`, `default-values`, `layout` (vertical \| horizontal).

Also reads (`descope-button-multi-selection-group`, `descope-multi-select-combo-box`): `invalid`, `readonly`; and the `vaadin-text-field` attributes and the `vaadin-multi-select-combo-box` attributes (`inputs.md`).

**Submits**: array of strings: the selected items' values.

### TenantNameInput

Tenant Name: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "Tenant Name", "label-type": "static", "size": "md", "placeholder": "Tenant Name", "full-width": true, "max": 100, "required": false, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "tenantName"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `external-input`.

Also reads (`descope-text-field`): `invalid`, `type`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### TextInput

Text Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 0 templates.

Defaults: `{"label": "Text Input", "size": "md", "type": "text", "placeholder": "Input", "full-width": true, "max": 100, "required": false, "bordered": true, "data-errormessage-value-missing": "Please fill out this field."}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `label-type` (static \| floating), `external-input`.

Also reads (`descope-text-field`): `copy-to-clipboard`, `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### TokenEndpointUrlInput

Token Endpoint Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "Token Endpoint", "label-type": "static", "size": "md", "placeholder": "Token Endpoint", "full-width": true, "max": 100, "required": true, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "tokenUrl", "type": "url", "pattern": "^https?:\\/\\/(?:www.)?(?:(?:[\\-a-zA-Z0-9@\\:%\\._\\+~#=]{1,256}.[a-zA-Z0-9\\(\\)]{1,6})|localhost)(?:[\\-a-zA-Z0-9\\(\\)@:%_\\+\\.~#\\?&\\/\\/=]*)$", "data-errormessage-pattern-mismatch": "Must be a valid URL"}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.

### TrustThisDeviceBoolean

Trust this device: custom `{"type": "input"}`, renders as flow-components `Boolean`, used in 0 templates.

Defaults: `{"label": "Trust this device", "size": "md", "full-width": true, "required": false, "checked": false, "bordered": true, "type": "checkbox", "data-errormessage-value-missing": "Please fill out this field.", "name": "trustThisDevice", "placeholder": "Trust this device"}`

Typed: `helper-text`, `data-errormessage-pattern-mismatch`, `label-type` (static \| floating), `external-input`.

Also reads (`descope-checkbox`): `invalid`; and the `vaadin-text-field` attributes and the `vaadin-checkbox` attributes (`inputs.md`).

**Submits**: boolean: `true` when checked, `false` when not.

### UploadFile

EditorUploadFile: custom `{"type": "input"}`, renders as flow-components `UploadFile`, used in 0 templates.

Defaults: `{"size": "md", "full-width": false, "required": false, "button-variant": "outline", "button-mode": "primary", "bordered": true, "data-errormessage-value-missing": "Please upload a file."}`

Typed: `title`, `description`, `icon`, `button-label`, `accept`, `name`, `readonly`.

Also reads (`descope-upload-file`): `pattern`.

**Submits**: not yet documented; check before a flow reads it.

### UserInfoEndpointUrlInput

User Info Endpoint Input: custom `{"type": "input"}`, renders as flow-components `Input`, used in 1 templates.

Defaults: `{"label": "User Info Endpoint", "label-type": "static", "size": "md", "placeholder": "User Info Endpoint", "full-width": true, "max": 100, "required": true, "bordered": true, "copy-to-clipboard": false, "data-errormessage-value-missing": "Please fill out this field.", "name": "userDataUrl", "type": "url", "pattern": "^https?:\\/\\/(?:www.)?(?:(?:[\\-a-zA-Z0-9@\\:%\\._\\+~#=]{1,256}.[a-zA-Z0-9\\(\\)]{1,6})|localhost)(?:[\\-a-zA-Z0-9\\(\\)@:%_\\+\\.~#\\?&\\/\\/=]*)$", "data-errormessage-pattern-mismatch": "Must be a valid URL"}`

Typed: `helper-text`, `external-input`.

Also reads (`descope-text-field`): `invalid`; and the `vaadin-text-field` attributes (`inputs.md`).

Theme values: `text-align` `right`, `left`, `center`.

**Submits**: string.
