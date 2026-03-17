---
name: descope-migrate-cognito
description: Migrate users and configuration from AWS Cognito to Descope. Use when planning or executing an AWS Cognito-to-Descope migration, moving users/groups from Cognito User Pools, or setting up just-in-time migration from Cognito.
---

# Migrate from AWS Cognito to Descope

Step-by-step guide for migrating users, groups, and configuration from AWS Cognito User Pools to Descope.

## Step 1: Fetch Documentation (BLOCKING)

Before proceeding, fetch the official Descope Cognito migration guide:

- URL: https://docs.descope.com/migrate/cognito

Read the full page and use it as ground truth alongside this skill. **Stop. Do not proceed until complete.**

## Step 2: Pre-Migration Assessment

**CRITICAL CONSTRAINT:** AWS Cognito does NOT export password hashes. Full migration is always a without-passwords migration. Plan for either passwordless auth or a forced password reset.

Inventory the current Cognito setup:

1. **User count** - total users in the User Pool
2. **Authentication methods** - username/password, social (OAuth), SAML SSO, MFA
3. **User attributes** - standard attributes + custom attributes (prefixed with `custom:`)
4. **User groups** - list all Cognito User Groups (these become Descope Roles)
5. **App clients** - list all App Client configurations
6. **Lambda triggers** - identify pre/post authentication, migration, custom message triggers
7. **Identity providers** - external IdPs configured in Cognito
8. **AWS service dependencies** - API Gateway JWT authorizers, AppSync, ALB auth
9. **Migration approach** - full bulk import or just-in-time (JIT)

### Concept Mapping

| AWS Cognito | Descope |
|-------------|---------|
| User Pool | Project |
| User | User with loginIds, profile, custom attributes |
| Hosted UI / Custom flow | Descope Flows |
| Identity Provider | Custom OAuth Providers or Tenant-based SSO |
| App Client | Inbound Application |
| User attributes | Custom attributes and built-in fields |
| User Groups | Roles |
| Lambda Triggers | Flow steps, Connectors, webhooks |
| MFA (SMS, TOTP) | TOTP, SMS OTP, passkeys, authenticator apps |

### Attribute Mapping

| Cognito Attribute | Descope Field |
|-------------------|---------------|
| `Username` or `email` | `loginIds` (required, unique) |
| `name` | `name` |
| `given_name` | `givenName` |
| `family_name` | `familyName` |
| `email` | `email` |
| `phone_number` | `phone` |
| `email_verified` | `verifiedEmail` |
| `phone_number_verified` | `verifiedPhone` |
| `custom:*` | Custom attributes |
| User Groups | `roleNames` |

## Step 3: Choose Migration Approach

| Approach | When to use | Reference |
|----------|-------------|-----------|
| **Full Migration** | Bulk export/import, clean cutover | `references/full-migration.md` |
| **JIT Migration** | Users provision on first sign-in, Cognito stays active | `references/jit-migration.md` |

**Decision tree:**
- Want a clean cutover to Descope? → Full Migration
- Need Cognito to stay active during transition? → JIT Migration
- Want to preserve user passwords during migration? → JIT Migration (Approach 1: USER_PASSWORD_AUTH)
- OK with passwordless or password reset? → Full Migration
- Have AWS service dependencies (API Gateway, AppSync)? → Either approach, update JWT authorizers after

## Step 4: Prerequisites

**For Full Migration (migration tool):**
- `DESCOPE_PROJECT_ID` - from https://app.descope.com/settings/project
- `DESCOPE_MANAGEMENT_KEY` - from https://app.descope.com/settings/company/managementkeys
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` - IAM credentials with `cognito-idp:ListUsers`, `cognito-idp:ListGroups`, `cognito-idp:AdminListGroupsForUser` permissions
- `COGNITO_USER_POOL_ID` - from AWS Cognito console (e.g., `us-east-1_XXXXXXXXX`)

**For JIT Migration:**
- Cognito User Pool must remain operational
- Cognito App Client with `ALLOW_USER_PASSWORD_AUTH` enabled (Approach 1)
- OR Cognito User Pool domain configured (Approach 2: OIDC)

## Step 5: Execute Migration

Follow the appropriate reference guide for your chosen approach.

## Step 6: Password Strategy (Full Migration Only)

Since Cognito does not export password hashes, choose one:

| Strategy | How |
|----------|-----|
| **Transition to passwordless** (Recommended) | Enable Magic Link, OTP, or Passkeys in Descope Flows |
| **Force password reset** | Use `freshlyMigrated` attribute to trigger reset on first login |
| **JIT password verification** | Use JIT migration to verify passwords against Cognito at sign-in |

## Step 7: AWS Service Integration

If your app uses AWS services that validate Cognito tokens, update them to accept Descope tokens:

| AWS Service | Action |
|-------------|--------|
| API Gateway JWT Authorizer | Update issuer URL and audience to Descope values |
| AppSync | Configure Descope as OIDC authorizer |
| ALB Authentication | Update OIDC settings to Descope endpoints |

During migration, backends may need to validate tokens from BOTH providers. See `references/full-migration.md` for dual validation code.

## Step 8: Post-Migration Verification

1. **User count parity** - compare Cognito user count vs Descope user count
2. **Role check** - verify all Cognito User Groups exist as Descope Roles
3. **Attribute check** - verify custom attributes migrated correctly
4. **Password reset flow** - test the password reset or passwordless flow
5. **Social login test** - verify OAuth connections work through Descope
6. **AWS service test** - verify API Gateway / AppSync accept Descope tokens
7. **Application integration test** - verify your app works end-to-end with Descope SDK

### freshlyMigrated Flow

Use the `freshlyMigrated` custom attribute in Descope Flows to:
- Route migrated users through email/phone verification (if needed)
- Force password reset on first login
- Prompt passkey enrollment
- Set `freshlyMigrated = false` after user completes post-migration steps

Set `verifiedEmail` and `verifiedPhone` to `true` during import if users were pre-verified in Cognito to avoid unnecessary re-verification.

## DO NOT

- DO NOT run the migration tool without a `--dry-run` first
- DO NOT assume Cognito will export password hashes — it will not
- DO NOT delete the Cognito User Pool until migration is fully verified (keep 30-90 days)
- DO NOT expose `DESCOPE_MANAGEMENT_KEY` or AWS credentials in client-side code
- DO NOT commit `.env` files containing secrets to version control
- DO NOT exceed Cognito API rate limits (5 req/sec for ListUsers) — implement backoff
- DO NOT skip updating AWS service JWT authorizers — apps will break silently

## References

- `references/full-migration.md` - Full bulk migration with tool or manual export
- `references/jit-migration.md` - Just-in-time migration (Cognito stays active)
