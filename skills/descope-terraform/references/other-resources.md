# descope_management_key Resource

Manage management keys for API authentication with RBAC scoping.

## Schema

**Required:**
- `name` (String) - Key designation
- `rebac` (Attributes) - Access control settings (replacement required on change)

**Optional:**
- `description` (String) - Key description
- `expire_time` (Number) - Unix timestamp for expiration; unlimited if omitted (replacement required on change)
- `permitted_ips` (List of String) - Allowed IP addresses/CIDR ranges; unrestricted if omitted
- `status` (String) - `"active"` or `"inactive"`

**Read-Only:**
- `id` (String)
- `cleartext` (String, Sensitive) - Plaintext key value, only available after creation

## rebac Block

All fields optional, but `company_roles` is mutually exclusive with `project_roles`/`tag_roles`.

| Field | Type | Description |
|-------|------|-------------|
| `company_roles` | Set of String | Company-level role assignments |
| `project_roles` | List | Per-project role assignments |
| `tag_roles` | List | Role assignments by project tags |

### project_roles

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_ids` | Set of String | Yes | Target project IDs |
| `roles` | Set of String | Yes | Assigned role names |

### tag_roles

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tags` | Set of String | Yes | Target project tags |
| `roles` | Set of String | Yes | Assigned role names |

## Example

```hcl
resource "descope_management_key" "ci_key" {
  name        = "CI/CD Pipeline Key"
  description = "Key for automated deployments"
  status      = "active"

  permitted_ips = ["10.0.0.0/8"]

  rebac = {
    tag_roles = [
      {
        tags  = ["staging"]
        roles = ["developer"]
      }
    ]
  }
}
```

---

# descope_descoper Resource

Manage Descope console user accounts with role-based access control.

## Schema

**Required:**
- `email` (String) - Console user email
- `rbac` (Attributes) - Access control configuration

**Optional:**
- `name` (String) - Display name
- `phone` (String) - Phone number

**Read-Only:**
- `id` (String)

## rbac Block

| Field | Type | Description |
|-------|------|-------------|
| `is_company_admin` | Boolean | Company-wide admin (mutually exclusive with project/tag roles) |
| `project_roles` | List | Per-project role assignments |
| `tag_roles` | List | Role assignments by project tags |

### project_roles / tag_roles

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_ids` / `tags` | Set of String | Yes | Target projects or tags |
| `role` | String | Yes | One of: `admin`, `developer`, `support`, `auditor` |

## Example

```hcl
resource "descope_descoper" "dev_user" {
  email = "developer@company.com"
  name  = "Dev User"

  rbac = {
    project_roles = [
      {
        project_ids = [descope_project.staging.id]
        role        = "developer"
      }
    ]
  }
}

resource "descope_descoper" "admin_user" {
  email = "admin@company.com"
  name  = "Admin User"

  rbac = {
    is_company_admin = true
  }
}
```

---

# descope_inbound_app Resource

Manage OAuth/OIDC inbound application registrations that authenticate into a Descope project.

## Schema

**Required:**
- `name` (String) - Application name
- `project_id` (String) - ID of the Descope project this app belongs to

**Optional:**
- `client_id` (String) - OAuth client ID
- `client_secret` (String, Sensitive) - OAuth client secret
- `non_confidential_client` (Boolean) - Set true for public clients (no client secret)
- `approved_callback_urls` (List of String) - Allowed redirect URIs
- `login_page_url` (String) - Custom login page URL
- `logo_url` (String) - Application logo URL
- `default_audience` (List of String) - Default token audience
- `force_add_all_authorization_info` (Boolean) - Include all authorization claims in tokens
- `audience_whitelist` (List of String) - Restrict accepted audiences
- `scopes` (Attributes) - Scopes the app can request (see below)
- `session_settings` (Attributes) - Token expiration and JWT template overrides

**Read-Only:**
- `id` (String)

## scopes Block

Three scope types share the same structure: `attributes`, `connections`, `permissions`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Scope name |
| `description` | String | No | Scope description |
| `optional` | Boolean | No | Whether the scope is optional |
| `values` | List of String | No | Allowed values for this scope |

## session_settings Block

Overrides project-level token settings for this app.

| Field | Type | Description |
|-------|------|-------------|
| `access_token_expiration` | String | Access token lifetime (e.g. `"1 hour"`) |
| `refresh_token_expiration` | String | Refresh token lifetime (e.g. `"7 days"`) |
| `jwt_template_id` | String | JWT template to apply to tokens |

## Example

```hcl
resource "descope_inbound_app" "my_app" {
  name       = "My App"
  project_id = descope_project.myproject.id

  approved_callback_urls = ["https://myapp.example.com/callback"]

  scopes = {
    permissions = [
      {
        name        = "read:profile"
        description = "Read user profile"
      }
    ]
  }

  session_settings = {
    access_token_expiration  = "1 hour"
    refresh_token_expiration = "7 days"
  }
}
```
