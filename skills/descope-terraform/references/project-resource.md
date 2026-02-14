# descope_project Resource

The primary resource for managing a Descope project. Contains all project configuration.

## Top-Level Schema

**Required:**
- `name` (String) - Project name

**Optional:**
- `admin_portal` (Attributes) - Admin portal configuration
- `applications` (Attributes) - OIDC and SAML application registrations
- `attributes` (Attributes) - Custom attributes for users, tenants, access keys
- `authentication` (Attributes) - Authentication method settings
- `authorization` (Attributes) - Roles and permissions (RBAC)
- `connectors` (Attributes) - Third-party service integrations
- `environment` (String) - Set to `"production"` for production projects
- `flows` (Attributes Map) - Custom authentication flows (keyed by flow ID)
- `invite_settings` (Attributes) - User invitation behavior
- `jwt_templates` (Attributes) - JWT token template definitions
- `lists` (Attributes List) - IP allowlists, text lists, custom JSON data
- `project_settings` (Attributes) - General project settings
- `styles` (Attributes) - Custom styling for authentication flows
- `tags` (Set of String) - Descriptive tags, max 50 characters each
- `widgets` (Attributes Map) - Embeddable widget components

**Read-Only:**
- `id` (String)

## authentication Block

All authentication methods are optional and can be combined.

### magic_link

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable magic link auth |
| `expiration_time` | String | Link expiry (e.g. `"1 hour"`) |
| `redirect_url` | String | Post-auth redirect URL |
| `email_service` | Attributes | Email connector and templates |
| `text_service` | Attributes | SMS connector and templates |

### enchanted_link

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable enchanted link auth |
| `expiration_time` | String | Link expiry |
| `redirect_url` | String | Post-auth redirect URL |
| `email_service` | Attributes | Email connector and templates |

### otp

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable OTP auth |
| `domain` | String | Domain restriction |
| `expiration_time` | String | Code expiry |
| `email_service` | Attributes | Email connector and templates |
| `text_service` | Attributes | SMS connector and templates |
| `voice_service` | Attributes | Voice call connector and templates |

### password

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable password auth |
| `min_length` | Number | Minimum password length |
| `lowercase` | Boolean | Require lowercase |
| `uppercase` | Boolean | Require uppercase |
| `number` | Boolean | Require number |
| `non_alphanumeric` | Boolean | Require special character |
| `lock` | Boolean | Lock after failed attempts |
| `lock_attempts` | Number | Attempts before lock |
| `temporary_lock` | Boolean | Enable temporary lock |
| `temporary_lock_attempts` | Number | Attempts before temp lock |
| `temporary_lock_duration` | String | Temp lock duration |
| `expiration` | Boolean | Require password expiry |
| `expiration_weeks` | Number | Weeks until expiry |
| `reuse` | Boolean | Prevent reuse |
| `reuse_amount` | Number | Number of previous passwords to check |
| `mask_errors` | Boolean | Hide specific error details |
| `email_service` | Attributes | Password reset email config |

### oauth

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable OAuth |
| `system` | Attributes | Built-in providers (see below) |
| `custom` | Attributes Map | Custom OAuth providers |

**Built-in OAuth providers** (configured under `system`): `apple`, `discord`, `facebook`, `github`, `gitlab`, `google`, `linkedin`, `microsoft`, `slack`

Each provider accepts: `client_id`, `client_secret` (Sensitive), `scopes`, `claim_mapping`, `disabled`, `merge_user_accounts`, `manage_provider_tokens`, `redirect_url`, `prompts`

**Custom OAuth provider fields:**
- `authorization_endpoint`, `token_endpoint`, `user_info_endpoint`, `jwks_endpoint`, `issuer`
- `client_id`, `client_secret` (Sensitive)
- `scopes` (List), `claim_mapping` (Map), `prompts` (List)
- `allowed_grant_types` (List), `callback_domain`
- `logo`, `description`, `disabled`

### passkeys

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable passkey auth |
| `top_level_domain` | String | Domain for WebAuthn |

### sso

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable SSO |
| `merge_users` | Boolean | Merge SSO users with existing |
| `redirect_url` | String | Post-SSO redirect |
| `allow_duplicate_domains` | Boolean | Allow same domain across tenants |
| `allow_override_roles` | Boolean | Allow SSO to override roles |
| `groups_priority` | Boolean | SSO group mapping priority |
| `sso_suite_settings` | Attributes | Admin portal SSO configuration |

### totp

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable TOTP |
| `service_label` | String | Label shown in authenticator apps |

### embedded_link

| Field | Type | Description |
|-------|------|-------------|
| `disabled` | Boolean | Disable embedded link |
| `expiration_time` | String | Link expiry |

## authorization Block

```hcl
authorization = {
  permissions = [
    {
      name        = "read:data"       # Required
      description = "Read access"     # Optional
    }
  ]
  roles = [
    {
      name        = "admin"                       # Required
      description = "Full access"                 # Optional
      key         = "admin-role"                  # Optional
      permissions = ["read:data", "write:data"]   # Optional, Set of String
      default     = false                         # Optional
      private     = false                         # Optional
    }
  ]
}
```

## applications Block

### oidc_applications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Application name |
| `description` | String | No | Application description |
| `claims` | List of String | No | Token claims to include |
| `disabled` | Boolean | No | Disable application |
| `force_authentication` | Boolean | No | Force re-authentication |
| `login_page_url` | String | No | Custom login page |
| `logo` | String | No | Application logo URL |

### saml_applications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Application name |
| `manual_configuration` | Attributes | No | Manual SAML setup (requires `acs_url`, `entity_id`) |
| `dynamic_configuration` | Attributes | No | Dynamic SAML via `metadata_url` |
| `attribute_mapping` | List | No | SAML attribute mappings (`name`, `value`) |
| `subject_name_id_type` | String | No | NameID type |
| `subject_name_id_format` | String | No | NameID format |

## attributes Block

Define custom attributes for users, tenants, and access keys.

```hcl
attributes = {
  user = [
    {
      name           = "department"    # Required
      type           = "string"        # Required: string, number, boolean, singleselect, multiselect, date
      select_options = []              # Required for singleselect/multiselect
    }
  ]
  tenant = [
    {
      name           = "plan"
      type           = "singleselect"
      select_options = ["free", "pro", "enterprise"]
    }
  ]
  access_key = [
    {
      name = "environment"
      type = "string"
    }
  ]
}
```

## project_settings Block

| Field | Type | Description |
|-------|------|-------------|
| `refresh_token_expiration` | String | Token expiry (e.g. `"3 weeks"`) |
| `enable_inactivity` | Boolean | Enable session inactivity timeout |
| `inactivity_time` | String | Inactivity timeout (e.g. `"1 hour"`) |

## flows Block

Flows are keyed by flow ID and accept JSON data exported from the Descope console.

```hcl
flows = {
  "sign-up-or-in" = {
    data = file("flows/sign-up-or-in.json")
  }
}
```

## Email/SMS Service Template Structure

Used across magic_link, enchanted_link, otp, and password blocks:

```hcl
email_service = {
  connector = "sendgrid-connector-id"
  templates = [
    {
      name            = "sign-in"          # Required
      subject         = "Your login code"  # Required
      html_body       = "<p>Code: {{code}}</p>"
      plain_text_body = "Code: {{code}}"
      active          = true
    }
  ]
}

text_service = {
  connector = "twilio-connector-id"
  templates = [
    {
      name   = "sign-in"        # Required
      body   = "Your code: {{code}}"  # Required
      active = true
    }
  ]
}
```

## invite_settings Block

Controls user invitation behavior configuration.

## lists Block

```hcl
lists = [
  {
    name  = "allowed-ips"
    type  = "ip"
    values = ["10.0.0.0/8"]
  }
]
```

## jwt_templates Block

Define custom JWT token templates for session tokens.

## styles Block

Customize the visual appearance of authentication flows and widgets.

## widgets Block

Configure embeddable authentication and user management widgets (keyed by widget ID).

## admin_portal Block

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | Boolean | Enable admin portal |
| `style_id` | String | Style to apply |
| `widgets` | List | Widget configurations (`type`, `widget_id` required) |
