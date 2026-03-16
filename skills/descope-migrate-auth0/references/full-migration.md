# Auth0 Full Migration

Complete migration of users, roles, permissions, and tenants from Auth0 to Descope using the official migration tool.

## Environment Setup

### Clone the Migration Tool

```bash
git clone git@github.com:descope/descope-migration.git
cd descope-migration
```

### Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Configure Environment Variables

Rename `.env.example` to `.env` and populate:

```bash
AUTH0_TOKEN=<Your Auth0 Management API Token>
AUTH0_TENANT_ID=<Your Auth0 Tenant ID>
DESCOPE_PROJECT_ID=<Your Descope Project ID>
DESCOPE_MANAGEMENT_KEY=<Your Descope Management Key>
```

**Getting the Auth0 Management API Token:**
1. Go to Auth0 Dashboard → Applications → APIs → Auth0 Management API
2. Open the API Explorer tab
3. Copy the token (valid for 24 hours)

## Migration Execution

### Choose Your Method

| Method | When to use |
|--------|-------------|
| API-based | Under 1,000 users |
| JSON export | Over 1,000 users |

### API-Based Migration (< 1,000 users)

**Always start with a dry run:**

```bash
# Dry run — no changes made to Descope
python3 src/main.py auth0 --dry-run

# Dry run with passwords (if you have the password hash export)
python3 src/main.py auth0 --dry-run --with-passwords ./path_to_exported_password_users_file.json
```

Review the dry run output. When satisfied:

```bash
# Live run
python3 src/main.py auth0

# Live run with passwords
python3 src/main.py auth0 --with-passwords ./path_to_exported_password_users_file.json
```

Add `-v` or `--verbose` for detailed output.

### JSON Export Migration (> 1,000 users)

For larger user bases, first export from Auth0:

1. Install the **User Import/Export** extension in Auth0 Dashboard
2. Export users as JSON
3. Run the migration tool with `--from-json`:

```bash
# Dry run
python3 src/main.py auth0 --dry-run --from-json ./path_to_user_export.json

# Dry run with passwords
python3 src/main.py auth0 --dry-run --from-json ./path_to_user_export.json --with-passwords ./path_to_exported_password_users_file.json

# Live run
python3 src/main.py auth0 --from-json ./path_to_user_export.json

# Live run with passwords
python3 src/main.py auth0 --from-json ./path_to_user_export.json --with-passwords ./path_to_exported_password_users_file.json
```

## What the Tool Migrates

The migration tool automatically:
- Creates Descope roles and permissions mapped from Auth0
- Imports users with profile data (name, email, phone, etc.)
- Maps custom `user_metadata` and `app_metadata` to Descope custom attributes
- Creates the `connection` custom attribute (text) — stores Auth0 connection type
- Creates the `freshlyMigrated` custom attribute (boolean) — set to `true` on import
- Associates users with tenants (mapped from Auth0 organizations)
- Maps role assignments per user

## Password Migration

Password migration is **optional** and requires a separate process:

1. **Open a support ticket** with Auth0 requesting a user password hash export
2. Auth0 will provide a JSON file with hashed passwords
3. Pass this file to the migration tool using `--with-passwords`

If you choose NOT to migrate passwords:
- Use the `freshlyMigrated` attribute to force a password reset on first login
- Or transition users to passwordless auth (Magic Link, OTP, Passkeys)

## Expected Output

A successful migration produces a log file: `migration_log_auth0_%d_%m_%Y_%H:%M:%S.log`

Summary includes:
- Total users processed
- Successfully migrated/merged users
- Failed migrations with error codes
- Roles and permissions created
- Tenant associations created
- User-role mappings applied

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Duplicate loginId | User already exists in Descope | Tool merges users automatically |
| Invalid email format | Malformed email in Auth0 | Fix in Auth0 before re-running |
| Auth0 token expired | Management token >24hrs old | Generate a new token from Auth0 |
| Rate limit exceeded | Too many API calls | Tool handles this; re-run if needed |

## Application Code Updates

After migration, swap Auth0 SDK calls for Descope SDK equivalents:

### Environment Variables

Remove:
```
AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_AUDIENCE
```

Add:
```
DESCOPE_PROJECT_ID=<your-project-id>
```

### SDK Replacement Patterns

| Auth0 SDK | Descope SDK |
|-----------|-------------|
| `@auth0/auth0-react` | `@descope/react-sdk` |
| `@auth0/nextjs-auth0` | `@descope/nextjs-sdk` |
| `auth0-python` | `descope-python` |
| `auth0` (Node.js) | `@descope/node-sdk` |

### React Example

**Before (Auth0):**
```jsx
import { useAuth0 } from '@auth0/auth0-react';
const { user, isAuthenticated, loginWithRedirect, logout } = useAuth0();
```

**After (Descope):**
```jsx
import { useSession, useUser, useDescope } from '@descope/react-sdk';
const { isAuthenticated, isSessionLoading } = useSession();
const { user } = useUser();
const { logout } = useDescope();
```

### Backend Token Validation

**Before (Auth0):**
```python
from auth0.authentication import GetToken
# Manual JWT validation with Auth0 JWKS
```

**After (Descope):**
```python
from descope import DescopeClient
descope_client = DescopeClient(project_id="your-project-id")
jwt_response = descope_client.validate_session(session_token)
```

## Post-Migration Cleanup

1. **Verify** all users, roles, and tenants in the Descope console
2. **Test** sign-in flows end-to-end in your application
3. **Monitor** the `freshlyMigrated` attribute to track user re-verification
4. **Disable** (do not delete) the Auth0 tenant for 30-90 days as a rollback safety net
5. **Remove** Auth0 SDK dependencies from your application
6. **Archive** migration logs and export data for compliance
