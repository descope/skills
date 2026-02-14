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
