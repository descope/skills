---
name: descope-migrate-auth0
description: Migrate users and configuration from Auth0 to Descope. Use when planning or executing an Auth0-to-Descope migration, moving users/roles/tenants from Auth0, or setting up hybrid Auth0+Descope authentication.
---

# Migrate from Auth0 to Descope

Step-by-step guide for migrating users, roles, permissions, and tenants from Auth0 to Descope.

## Step 1: Fetch Documentation (BLOCKING)

Before proceeding, fetch the official Descope Auth0 migration guide:

- URL: https://docs.descope.com/migrate/auth0

Read the full page and use it as ground truth alongside this skill. **Stop. Do not proceed until complete.**

## Step 2: Pre-Migration Assessment

Inventory the current Auth0 setup before writing any code:

1. **User count** - determines API-based (<1000 users) vs JSON export migration
2. **Authentication methods** - passwords, social (OAuth), enterprise SSO (SAML/OIDC), MFA
3. **Password hashes** - do you need password migration? (requires Auth0 support ticket)
4. **Roles & permissions** - list all Auth0 roles and permissions to map
5. **Tenants/organizations** - list Auth0 organizations if multi-tenant
6. **Custom user metadata** - identify `user_metadata` and `app_metadata` fields
7. **Migration approach** - full cutover or hybrid (Auth0 remains active)

### Concept Mapping

| Auth0 | Descope |
|-------|---------|
| Tenant | Project |
| User | User with loginIds, profile, custom attributes |
| Universal Login / Lock | Descope Flows |
| Connection | Authentication method |
| Organization | Tenant |
| Role | Role |
| Permission | Permission |
| Rule / Action | Flow steps, Connectors, webhooks |
| MFA | TOTP, SMS OTP, passkeys, authenticator apps |
| Management API Token | Management Key |

## Step 3: Choose Migration Approach

| Approach | When to use | Reference |
|----------|-------------|-----------|
| **Full Migration** | Complete transition away from Auth0 | `references/full-migration.md` |
| **Hybrid Migration** | Auth0 remains active, Descope as federated IdP | `references/hybrid-migration.md` |

**Decision tree:**
- Want to fully replace Auth0? → Full Migration
- Need gradual rollout or Auth0 must remain for some apps? → Hybrid Migration
- Have 1000+ users? → Full Migration with JSON export
- Have <1000 users? → Full Migration with API-based export

## Step 4: Prerequisites

Before running the migration tool:

1. **Auth0 Tenant ID** - from dashboard URL (e.g., `dev-xyz`)
2. **Auth0 Management API Token** - 24-hour token from Auth0 Management API Explorer
3. **Descope Project ID** - from https://app.descope.com/settings/project
4. **Descope Management Key** - from https://app.descope.com/settings/company/managementkeys

## Step 5: Execute Migration

Follow the appropriate reference guide for your chosen approach. The migration tool handles:
- Creating Descope roles and permissions from Auth0 equivalents
- Importing users with profile data and custom attributes
- Mapping tenant/organization associations
- Setting `freshlyMigrated` custom attribute for post-migration flows

## Step 6: Post-Migration Verification

After migration completes:

1. **User count parity** - compare Auth0 user count vs Descope user count
2. **Role and permission check** - verify all roles/permissions exist in Descope console
3. **Tenant association check** - verify tenant memberships are correct
4. **Test authentication** - sign in as a migrated user via Descope
5. **Social login test** - verify OAuth connections (Google, GitHub, etc.)
6. **MFA test** - verify MFA still works for applicable users
7. **Application integration test** - verify your app works with Descope SDK

### freshlyMigrated Flow

Use the `freshlyMigrated` custom attribute in Descope Flows to:
- Route migrated users through email/phone verification
- Force password updates (if passwords were migrated)
- Prompt passkey enrollment
- Set `freshlyMigrated = false` after user completes post-migration steps

## DO NOT

- DO NOT run the migration tool without a `--dry-run` first
- DO NOT skip the pre-migration assessment — missing data causes partial migrations
- DO NOT delete Auth0 tenant until migration is fully verified (keep 30-90 days)
- DO NOT expose `DESCOPE_MANAGEMENT_KEY` in client-side code or commit to git
- DO NOT commit `.env` files containing tokens to version control
- DO NOT run live migration during peak usage hours
- DO NOT assume password migration is automatic — it requires a separate Auth0 support ticket

## References

- `references/full-migration.md` - Full migration with descope-migration tool
- `references/hybrid-migration.md` - Hybrid migration (Auth0 remains active)
