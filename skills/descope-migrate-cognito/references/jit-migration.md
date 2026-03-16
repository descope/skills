# Cognito Just-In-Time (JIT) Migration

Users provision in Descope when they first sign in. Cognito remains operational until all active users have migrated. This approach preserves passwords since credentials are verified against Cognito at sign-in time.

## Choose Your JIT Approach

| Approach | Best for | Password handling |
|----------|----------|-------------------|
| **USER_PASSWORD_AUTH + HTTP Connector** | Preserving existing passwords | Verified against Cognito in real-time |
| **Cognito as Custom OIDC Provider** | Passwordless transition or SSO | Redirects to Cognito Hosted UI |

## Approach 1: USER_PASSWORD_AUTH with HTTP Connector

Descope collects credentials and verifies them against Cognito via the `InitiateAuth` API. On success, the user is created in Descope with their existing password.

### Prerequisites

- Cognito User Pool must remain active
- App Client must have `ALLOW_USER_PASSWORD_AUTH` and `ALLOW_REFRESH_TOKEN_AUTH` enabled

### Step 1: Configure Cognito App Client

Ensure the App Client has these `ExplicitAuthFlows`:
- `ALLOW_USER_PASSWORD_AUTH`
- `ALLOW_REFRESH_TOKEN_AUTH`

### Step 2: Create Generic HTTP Connector in Descope

Go to Descope Console → Connectors → Generic HTTP:

| Setting | Value |
|---------|-------|
| **Name** | Cognito Password Verification |
| **Base URL** | `https://cognito-idp.<region>.amazonaws.com` |
| **Method** | POST |

**Headers:**
| Header | Value |
|--------|-------|
| `Content-Type` | `application/x-amz-json-1.1` |
| `X-Amz-Target` | `AWSCognitoIdentityProviderService.InitiateAuth` |

**Request Body Template:**
```json
{
  "ClientId": "<COGNITO_APP_CLIENT_ID>",
  "AuthFlow": "USER_PASSWORD_AUTH",
  "AuthParameters": {
    "USERNAME": "{{form.email}}",
    "PASSWORD": "{{form.password}}"
  }
}
```

### Step 3: Build Descope Flow

Create a Descope Flow with this logic:

```
[User enters email]
  → [Check if user exists in Descope (loginIds not empty)]
    → EXISTS: Normal Descope sign-in
    → NOT EXISTS: Collect email + password via form
      → [Call Cognito HTTP Connector]
        → SUCCESS (HTTP 200):
          → [Create user in Descope with "Sign Up / Password" action]
          → [Map attributes and roles from Cognito response]
          → [Set freshlyMigrated = true]
          → [Issue Descope session]
        → FAILURE:
          → [Show error: "Invalid credentials"]
          → [Offer passwordless recovery: Magic Link / OTP]
```

**Flow step details:**

1. **Condition: Check existing user** - Use condition on `user.loginIds`
   - If not empty → user already exists in Descope → normal sign-in
   - If empty → new user → proceed to credential collection

2. **Screen: Collect credentials** - Form with `form.email` and `form.password` fields

3. **Connector: Call Cognito** - Use the Generic HTTP Connector to call `InitiateAuth`

4. **Branch on result:**
   - HTTP 200 → user authenticated successfully → create in Descope
   - Any error → invalid credentials → offer recovery options

5. **Action: Create user** - Use "Sign Up / Password" action to create the user in Descope with their verified password

Over time, users sign in through Descope and Cognito calls are no longer needed.

### Monitor Migration Progress

Track how many users have migrated by querying the `freshlyMigrated` attribute:
- `freshlyMigrated = true` → user has migrated but hasn't completed post-migration steps
- `freshlyMigrated = false` → user has fully transitioned
- User doesn't exist in Descope → hasn't signed in since migration started

## Approach 2: Cognito as Custom OIDC Provider

Descope redirects users to the Cognito Hosted UI for authentication. Cognito returns an ID token, and Descope provisions the user from the token claims.

### Step 1: Get Cognito OIDC Details

From the Cognito User Pool:

| Setting | Value |
|---------|-------|
| **Domain** | `https://your-domain.auth.<region>.amazoncognito.com` |
| **Discovery URL** | `https://your-domain.auth.<region>.amazoncognito.com/.well-known/openid-configuration` |
| **Client ID** | From App Client settings |
| **Client Secret** | From App Client settings |

### Step 2: Add Cognito as Custom OIDC Provider in Descope

Go to Descope Console → Authentication → Social Login → Custom OAuth Provider:

| Setting | Value |
|---------|-------|
| **Name** | AWS Cognito |
| **Client ID** | Cognito App Client ID |
| **Client Secret** | Cognito App Client Secret |
| **Authorization URL** | `https://your-domain.auth.<region>.amazoncognito.com/oauth2/authorize` |
| **Token URL** | `https://your-domain.auth.<region>.amazoncognito.com/oauth2/token` |
| **User Info URL** | `https://your-domain.auth.<region>.amazoncognito.com/oauth2/userInfo` |
| **Scopes** | `openid email profile` |

### Step 3: Add OAuth Sign-In to Descope Flow

Add a "Sign Up or In / OAuth" step in your Descope Flow that redirects to Cognito.

### Step 4: Claim Mapping

Cognito ID token claims map to Descope user fields:

| Cognito Claim | Descope Field |
|---------------|---------------|
| `sub` | External user ID |
| `email` | `email` + `loginIds` |
| `email_verified` | `verifiedEmail` |
| `name` | `name` |
| `given_name` | `givenName` |
| `family_name` | `familyName` |
| `phone_number` | `phone` |
| `cognito:groups` | `roleNames` |

### Step 5: Use `freshlyMigrated` for Routing

After the user's first sign-in via Cognito OIDC:

```
[User signs in via Cognito OIDC]
  → [Descope provisions user from token claims]
  → [Set freshlyMigrated = true]
  → [Check freshlyMigrated == true?]
    → YES: Route to onboarding
      → [Optional: enroll passkey]
      → [Optional: set Descope password]
      → [Set freshlyMigrated = false]
    → NO: Normal sign-in
```

Over time, users who have completed onboarding sign in directly through Descope without the Cognito redirect.

## SSO Migration

If SAML or OIDC identity providers are configured in Cognito, migrate them to Descope:

1. Follow the [SSO Migration guide](https://docs.descope.com/migrate/sso) for the full process
2. Configure the same IdPs in Descope (no IdP-side reconfiguration needed with DNS redirect)
3. Test SSO flows before disabling Cognito
4. Update tenant-level SSO settings in Descope

## Decommissioning Cognito

Once all active users have migrated (tracked via `freshlyMigrated`):

1. **Monitor** Cognito CloudWatch metrics for remaining authentication activity
2. **Set a cutoff date** — users who haven't signed in by then get a forced password reset
3. **Disable** App Client authentication flows in Cognito
4. **Remove** HTTP Connector or OIDC provider configuration in Descope
5. **Disable** (do not delete) the Cognito User Pool for 30-90 days
6. **Clean up** IAM roles and policies used for migration
7. **Archive** Cognito export data for compliance
