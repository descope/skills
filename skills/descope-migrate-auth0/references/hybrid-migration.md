# Auth0 Hybrid Migration

Hybrid migration keeps Auth0 active while adding Descope as a federated identity provider. Users gradually transition to Descope without a hard cutover.

## When to Use Hybrid Migration

- Multiple applications depend on Auth0 and can't migrate simultaneously
- Need zero-downtime migration with gradual rollout
- Want to test Descope in production before full commitment
- Some applications must remain on Auth0 temporarily

## How It Works

1. Import users from Auth0 into Descope (same as full migration Step 1)
2. Configure Descope as an external identity provider in Auth0
3. Users authenticate through Descope, which federates back to Auth0
4. Over time, move applications to use Descope directly
5. Eventually decommission Auth0

## Step 1: Import Users

Follow the same user import process from `full-migration.md`:

```bash
git clone git@github.com:descope/descope-migration.git
cd descope-migration
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Configure `.env` and run:

```bash
# Dry run first
python3 src/main.py auth0 --dry-run

# Live run
python3 src/main.py auth0
```

## Step 2: Set Up Hosted Auth Page

Use Descope’s hosted auth pages to run your login Flow and initiate the OIDC flow into Auth0 (as described in the Auth0 OIDC setup guide: [`https://docs.descope.com/identity-federation/applications/setup-guides/auth0/auth0-oidc`](https://docs.descope.com/identity-federation/applications/setup-guides/auth0/auth0-oidc)).

### Create or Reuse an OIDC Flow

- **If you want Passkeys**: Start from the Descope sample `oidc-flow.json` in the Auth0 passkey sample app and import it into your project: [`https://github.com/descope-sample-apps/auth0-passkey-implementation/blob/main/oidc-flow.json`](https://github.com/descope-sample-apps/auth0-passkey-implementation/blob/main/oidc-flow.json).
- **Otherwise**: Use an existing login Flow or create a new one that:
  - Verifies the user’s email/phone
  - Optionally enrolls passkeys or MFA
  - Ends with a redirect back to your application / Auth0.

Make sure your Flow logic always results in a verified identity, especially when using passkeys.

### Hosted Flow URL

Descope automatically hosts your Flow via the Auth Hosting Application. The URL format is:

`https://auth.descope.io/<PROJECT_ID>?flow=<FLOW_ID>`

Examples:

- For the imported sample: `https://auth.descope.io/<PROJECT_ID>?flow=oidc-flow`
- For a custom Flow: `https://auth.descope.io/<PROJECT_ID>?flow=<your-flow-id>`

You’ll use this URL later:
- In custom UIs (e.g., an Auth0 Universal Login custom page button or link)
- As the target when you “Continue with Descope” from Auth0.

## Step 3: Configure Descope as IdP in Auth0

Set up Descope as an enterprise connection in Auth0 using OpenID Connect:

### Get Descope OIDC Details

From the Descope console, gather:
- **Issuer URL:** `https://api.descope.com/<your-project-id>`
- **Authorization endpoint:** `https://api.descope.com/oauth2/v1/authorize`
- **Token endpoint:** `https://api.descope.com/oauth2/v1/token`
- **JWKS URI:** `https://api.descope.com/<your-project-id>/.well-known/jwks.json`
- **Client ID and Secret:** Use your Project ID as the Client ID, and the Access Key generated under Access Keys in the Descope Console as the Client Secret.

### Create Auth0 Enterprise Connection

1. Go to Auth0 Dashboard → Authentication → Enterprise → OpenID Connect
2. Create a new connection with Descope's OIDC endpoints
3. Map Descope claims to Auth0 user profile attributes
4. Enable the connection for the appropriate Auth0 Applications

### Claim Mapping

| Descope Claim | Auth0 Profile Field |
|---------------|---------------------|
| `sub` | `user_id` |
| `email` | `email` |
| `email_verified` | `email_verified` |
| `name` | `name` |
| `given_name` | `given_name` |
| `family_name` | `family_name` |
| `phone_number` | `phone_number` |

## Step 4: Test Hybrid Login

1. Open your application's login page
2. Select the Descope enterprise connection (or configure it as the default)
3. User authenticates via Descope Flows
4. Descope issues tokens, Auth0 accepts them via federation
5. Application receives Auth0 session as before

Verify:
- Login and logout work end-to-end
- User profile data maps correctly
- Roles and permissions are preserved
- MFA flows work if applicable

## Step 5: Gradual Application Migration

Migrate applications one at a time from Auth0 to Descope directly:

1. **Pick a non-critical application** to migrate first
2. **Replace Auth0 SDK** with Descope SDK (see `full-migration.md` for SDK mapping)
3. **Update environment variables** from Auth0 to Descope
4. **Test thoroughly** in staging
5. **Deploy** and monitor
6. **Repeat** for the next application

## Step 6: freshlyMigrated Flow for Transitioning Users

Use the `freshlyMigrated` custom attribute in Descope Flows to handle users transitioning from Auth0:

### Flow Logic

```
[User signs in]
  → [Check freshlyMigrated == true?]
    → YES: Route to verification
      → [Verify email/phone]
      → [Optional: enroll passkey]
      → [Optional: set new password]
      → [Set freshlyMigrated = false]
      → [Continue to app]
    → NO: Normal sign-in flow
```

This ensures migrated users complete any required re-verification exactly once.

## Step 7: Decommission Auth0

Once all applications use Descope directly:

1. **Verify** no applications still depend on Auth0 sessions
2. **Check** Auth0 logs for any remaining authentication activity
3. **Disable** the Auth0 enterprise connection in Descope
4. **Disable** (do not delete) the Auth0 tenant
5. **Wait 30-90 days** before permanent deletion as a rollback window
6. **Remove** Auth0 dependencies from all codebases
7. **Archive** Auth0 export data and migration logs
