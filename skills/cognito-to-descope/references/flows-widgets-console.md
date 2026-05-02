# Descope Flows, Widgets, and Console-First Reference

This file covers Descope's no-code/low-code layer — Flows, Widgets, the SSO Setup Suite, and
the Console-vs-code decision guide. Read it when the migration touches Lambda triggers, auth UI,
MFA enrollment, user management pages, or SSO configuration. In all those areas, a
Console/Flow/Widget approach is usually faster and safer than writing code.

---

## Contents

- [Terminology: Cognito → Descope Lingo](#terminology-cognito--descope-lingo)
- [Flows: Structure and What They Replace](#flows-structure-and-what-they-replace)
- [Widgets: Post-Login Management UI](#widgets-post-login-management-ui)
- [SSO Setup Suite](#sso-setup-suite)
- [Console vs. Code: The Decision Guide](#console-vs-code-the-decision-guide)

---

## Terminology: Cognito → Descope Lingo

### Critical concept mapping

The most common migration mistake: Cognito and Descope carve up the namespace differently.
A Cognito User Pool is not a Descope Tenant — it is a Descope Project. Getting this wrong
breaks multi-tenancy analysis in Phase 2.

| Cognito term | Descope term | Notes |
|---|---|---|
| **User Pool** | **Project** | Top-level auth namespace. One User Pool = one Descope Project. |
| **App Client** | **`projectId`** (SDK) or **Federated Application** | App Client without a client secret → SDK integration via `projectId`. App Client used as an OAuth 2.0 client → configure a Federated Application in Console → Applications. |
| **User Pool Group** (capability-based: `admin`, `editor`, `viewer`) | **Role** | Roles describe what a user *can do*. `cognito:groups` → `roles` claim in the Descope JWT (project-level) or `tenants.<tenantId>.roles` (tenant-scoped). A user can hold different roles in different tenants simultaneously — e.g., `admin` in Tenant A and `viewer` in Tenant B. |
| **User Pool Group** (org-based: `acme-corp`, `tenant_123`, a UUID) | **Tenant** | Tenants describe *who the user belongs to*. Each Tenant can carry its own SSO connection, role assignments, and per-org flow customization. Tenant membership appears in the validated JWT as `tenants: { "<tenantId>": { roles: [...], permissions: [...] } }`. |
| **Separate User Pool per customer org** | **Tenant** | One Tenant per pool, all within a single Project. |
| **Cognito Hosted UI** | **Auth Hosting** (hosted) or embedded `<Descope>` component | Flows define the auth experience in both cases. |
| **Lambda Trigger** (pre-signup, post-confirmation, pre-auth, custom challenge…) | **Flow step + Scriptlet + Connector** | Flows replace the entire Lambda trigger pipeline. |
| **Pre-Token Generation trigger** | **JWT Templates** in Console | Define custom JWT claims without code deployment. |
| **Migrate User trigger** | **JIT migration via Generic HTTP Connector** in Flow | Users are migrated on first sign-in without bulk import. |
| **Custom Authentication Challenge** | **Scriptlet** in a Flow | Fully custom auth logic runs inline inside a Flow step. |
| **M2M / Client Credentials** | **Access Key** | Exchange for a short-lived JWT. Supports expiration, permitted IPs, tenant/role scoping. |
| **Identity Pools (Federated Identities)** | Not directly replaced by Descope | Identity Pools are an AWS mechanism for exchanging tokens for short-lived IAM credentials (to access S3, DynamoDB, etc. directly from the client). Descope does not replicate this. The typical approach is to add Descope as a custom OIDC provider in the existing Cognito Identity Pool so it can exchange Descope JWTs for IAM credentials — but verify the current recommended approach with the Descope Docs MCP server (`ask-question-about-descope "Cognito Identity Pool federated OIDC"`) before implementing, as this integration may have evolved. |
| **Cognito as OIDC provider for external clients** | **Federated Application** (OIDC/SAML) | Different from an App Client: an App Client is how *your own app* talks to Cognito (SDK calls, direct auth). This row is the case where *other external applications* (a third-party SaaS, a partner app, another internal service) redirect their users to your Cognito Hosted UI domain for login and receive tokens back via OAuth PKCE — your Cognito User Pool is acting as the Authorization Server. In Descope, configure an OIDC or SAML Federated Application in Console → Applications to serve the same role. External clients update their authorization endpoint URL to point at Descope instead of Cognito. |
| **Custom attributes** (`custom:*`) | **Custom Attributes** | Defined in Console → Project → Custom Attributes. |
| **SMS MFA** | **OTP via SMS** (Flow step) | Configure under Console → Authentication Methods → SMS OTP. |
| **TOTP / authenticator app MFA** | **TOTP** (Flow step) | Add TOTP step to sign-in Flow. |
| **Device tracking / remembered devices** | **Trusted Device** (Flow step) or risk-based conditions | Use the Trusted Device step in a Flow to skip MFA on known devices. Alternatively, use risk factor conditions (device fingerprint, IP, user agent) inside the Flow to step up or step down auth requirements. Remove Cognito device-tracking SDK calls and replace with whichever Flow-based approach fits your security model. |
| **Social providers** (Google, Facebook, Apple via Cognito federation) | **OAuth Provider** | Configured under Console → Authentication Methods. |
| **Enterprise SAML/OIDC per-org** (separate IdP per customer pool) | **Tenant SSO** | Per-tenant configuration via SSO Setup Suite. |
| **Email/SMS verification templates** | **Templates** | Configured per authentication method in Console. |
| **FORCE_CHANGE_PASSWORD users** | Custom attribute + Flow condition → forced password reset | During migration, set a custom attribute (e.g., `mustResetPassword: true`) on every user whose Cognito status was `FORCE_CHANGE_PASSWORD`. In the sign-in Flow, add a Condition step after authentication that checks this attribute. If `true`, route the user to a password-reset screen; on completion, update the attribute to `false` via a webhook or Scriptlet. This is **not** the same as `authInfo.firstSeen` — `firstSeen` reflects the first login to Descope, not whether the user has ever set a password. Users who complete the reset flow continue as normal password users; the attribute gates them only once. |

### Other Descope-specific terms

The terms below cover the concepts most frequently encountered during a Cognito migration. They are not exhaustive — for the full Descope glossary or deeper explanations, use the Descope Docs MCP server: `ask-question-about-descope "what is a [term]"`.

- **Project** — the top-level unit. Think Cognito User Pool.
- **Flow** — visual auth pipeline. Replaces Lambda triggers + Hosted UI + Custom Challenge sequences.
- **Screen** — one UI page within a Flow. Designed in Screen Builder.
- **Scriptlet** — inline JavaScript step in a Flow (Lodash + CryptoJS included). Replaces Lambda trigger logic.
- **Connector** — HTTP call step in a Flow. Response stored as `connectors.<contextKey>` for use in later Conditions or Custom Claims.
- **Subflow** — one Flow embedded inside another. Context passes through; does not terminate the parent. Good for MFA as a step inside a sign-in journey.
- **Tenant** — a customer organization (B2B). Maps to Cognito org-identity groups or separate pools.
- **Auth Hosting Application** — the hosted login page (equivalent to Cognito Hosted UI domain).

---

## Flows: Structure and What They Replace

A Descope Flow is a visual, no-code authentication pipeline built in the Console. It IS the
authentication process — not a hook on top of it. Flows can be changed without redeploying
the application.

### What Flows replace from Cognito

| Cognito | Descope Flow equivalent |
|---|---|
| Lambda triggers (pre-signup, post-confirmation, pre-auth, post-auth) | Flow steps: Conditions, Actions, Scriptlets, Connectors |
| Hosted UI login page | Flow Screens |
| Amplify `<Authenticator>` component / custom sign-in forms | Flow Screens + `<Descope flowId="..." />` component |
| Email verification on sign-up | Email OTP / magic link step in Flow |
| SMS verification (phone number confirmation) | SMS OTP step in Flow |
| Password reset (Forgot Password → send code → confirm) | Password reset Flow (template available); or remove entirely if going passwordless |
| MFA enrollment (TOTP via `associateSoftwareToken`/`verifySoftwareToken`, SMS MFA) | MFA step in main sign-up/sign-in Flow, or MFA subflow. If you use a custom email or SMS provider for OTP delivery, configure it as a Connector first (see Connectors row below), then select it under the MFA step's delivery settings — Descope's default delivery will not be used. |
| Custom Authentication Challenge (define, create, verify Lambda trio) | Scriptlet steps in a Flow |
| Migrate User Lambda trigger (real-time password verification against old system) | JIT migration via Generic HTTP Connector in Flow |
| Pre-Token Generation trigger (custom JWT claims) | JWT Templates in Console |
| Attack protection (advanced security — rate limiting, adaptive auth) | Connector steps (Arkose, reCAPTCHA, Fingerprint, AbuseIPDB) |

### Lambda triggers → Descope equivalents

#### How Descope Flows differ from Cognito's trigger lifecycle

In Cognito, *when* your code runs is determined by which trigger hook you attach it to. `PreSignUp` fires before user creation, `PostConfirmation` fires after email verification, `PreAuthentication` fires before password check — each hook is wired to a fixed position in Cognito's internal auth lifecycle. You cannot move that position; you can only choose which hook to use.

**In Descope, there is no fixed trigger lifecycle.** A Flow is a visual canvas of steps you assemble yourself. Conditions, Scriptlets, Connectors, and Actions are nodes you place wherever they need to run in the user journey. The same domain-validation logic that Cognito forces into `PreSignUp` could sit before an OTP step, after a Tenant lookup, or after user creation — wherever it makes sense for *your* flow. The ordering is explicit and visible on the canvas, not implicit in a hook name.

This changes the migration question from *"which trigger does this Lambda replace?"* to **"at what point in the user journey should this logic run, and what data does it need?"** The table below maps each Cognito trigger to its natural position in a Descope Flow.

#### What context is available at each position

| Position in Flow | Available context |
|---|---|
| Before user creation (start of sign-up branch) | `form.*` (typed values), `loginIds`, `tenant.*` from URL hint — `user.*` is empty |
| After user creation / after authentication | `user.*` fully populated: `userId`, `email`, `roles`, `tenants`, `customAttributes.*` |
| After Flow completes (token issuance) | JWT Templates only — reads `user.*` and `tenant.*` from the Descope user record; cannot read Connector responses |

#### Trigger-by-trigger placement guide

| Cognito trigger | Typical purpose | Where to place in Descope Flow | Mechanism |
|---|---|---|---|
| Pre-signup | Block by email domain, validate invite code, check external allowlist | First step after sign-up form, before Create User action | Condition (on `form.email`) or Connector → Condition |
| Post-confirmation | Provision user in DB, send welcome notification, assign initial role | After Create User action in sign-up branch | Connector (HTTP POST to provisioning endpoint) |
| Pre-authentication | IP blocklist, suspended account check, admin approval gate | Before password validation or OTP step in sign-in branch | Condition (on `user.customAttributes.*`) or Connector |
| Post-authentication | Audit log, last-login timestamp, analytics event | After final auth step, before Flow ends | Connector (fire-and-forget HTTP call) |
| Pre-token generation (custom claims) | Add `org_id`, `plan`, `permissions` to the JWT | JWT Templates in Console — not a Flow step | JWT Template reading `user.customAttributes.*`; if data requires a live lookup, store it via a post-auth Connector first |
| Custom auth challenge (define / create / verify trio) | Time-based codes, hardware token, proprietary challenge/response | Replace the three-Lambda sequence with a single Scriptlet or Connector → Condition pair | Scriptlet for self-contained logic (Lodash + CryptoJS available); Connector for external verification |
| Migrate User | Verify password against Cognito on first sign-in; create user in Descope on success | In sign-in branch, after credential entry, before Create User | Generic HTTP Connector calls Cognito `InitiateAuth`; Condition checks response; see `implementation-guide.md` for SECRET_HASH proxy |
| Pre-signup domain validation (multi-tenant routing) | Extract email domain, look up matching Tenant, redirect to Tenant SSO | After email entry screen, before OTP/password | Scriptlet extracts domain → Condition routes to Tenant's SSO subflow |

#### Common migration examples

**Pre-signup: block registrations by email domain**

Cognito Lambda (`PreSignUp`):
```js
exports.handler = async (event) => {
  if (!event.request.userAttributes.email.endsWith('@acme.com')) {
    throw new Error('Registration restricted to acme.com.');
  }
  return event;
};
```
Descope Flow: Add a **Condition** step after the sign-up form, before Create User.
- Expression: `form.email endsWith "@acme.com"`
- True branch → continue to Create User
- False branch → Screen: "Registration is restricted to acme.com addresses"

---

**Post-confirmation: provision user in an external database**

Cognito Lambda (`PostConfirmation`):
```js
exports.handler = async (event) => {
  await db.createUser({ id: event.userName, email: event.request.userAttributes.email });
  return event;
};
```
Descope Flow: Add a **Connector** step after the Create User action.
- Method: POST
- URL: `https://your-api.example.com/users`
- Body: `{ "userId": "{{user.userId}}", "email": "{{user.email}}" }`
- Branch on Connector error if provisioning failure should block sign-in.

---

**Pre-token generation: add a custom `org_id` claim**

Cognito Lambda (`PreTokenGeneration`):
```js
exports.handler = async (event) => {
  event.response.claimsOverrideDetails = {
    claimsToAddOrOverride: { org_id: event.request.userAttributes['custom:org_id'] }
  };
  return event;
};
```
Descope equivalent — no Flow step needed. In Console → Authorization → JWT Templates, add:
```json
{ "org_id": "{{user.customAttributes.org_id}}" }
```
The custom attribute must be pre-created in Console → Project → Custom Attributes and populated during user migration.

---

**Before migrating any Lambda trigger**, check whether a Flow Condition, Scriptlet, Connector, or JWT Template can replace it entirely without any external Lambda. The majority of pre-signup validation, post-confirmation webhooks, and custom claims move fully to the Console.

### Building blocks

1. **Screens** — UI forms. Support conditional show/hide of components based on context values (`user.*`, `form.*`, `tenant.*`).
2. **Actions** — single-task steps: authenticate, send OTP, verify magic link, create user, assign role, set custom claims, end the flow.
3. **Conditions** — branch routing based on context values (`user.*`, `tenant.*`, `form.*`, `connectors.<key>`, `jwtClaims.*`, `cookies.<name>`).
4. **Connectors** — HTTP calls to external services during the flow. Response stored as `connectors.<contextKey>`.

**Advanced:**
- **Scriptlets** — inline JavaScript. Replaces Lambda trigger logic for string manipulation, hashing, date math, or CryptoJS-based operations. Has a test/debug mode.
- **JWT Templates** — define custom claims that appear in the session JWT. Direct replacement for Pre-Token Generation Lambda.
- **Subflows** — embed one Flow inside another. The subflow End continues back to the parent. Pass inputs via `{{subflowInput.key}}`.

### Flow templates (100+ in library)

Access via Console → Flows → "Start from template". Search by method, use case, or connector.

**Common templates:**
- `sign-up-or-in` — default; combines email OTP, magic link, social, passkeys
- `step-up` — step-up auth; adds `su` JWT claim on success
- OTP variants (email, SMS, WhatsApp)
- Magic link variants
- Passkey / WebAuthn
- Social login
- TOTP / authenticator app
- SSO / SAML / OIDC federation
- MFA combinations (password + TOTP, social + OTP, passkeys + magic link)
- Invitation, progressive profiling, account recovery

**Before building any custom Flow configuration**, check whether a template already covers the
use case. Most common patterns are available out of the box.

### MFA enrollment specifically

Cognito's TOTP enrollment is a separate multi-step sequence:
`associateSoftwareToken()` → user scans QR → `verifySoftwareToken()` → `setUserMFAPreference()`.
Cognito SMS MFA also involves a separate `enableSMSMFA()` call.
Both patterns are typically separate pages or modals in Cognito apps.

**The Descope approach:**
- Add an MFA step to the main sign-up/sign-in Flow — enrollment happens inline during the auth journey.
- Or embed MFA as a **subflow** — triggered by a condition (e.g., user is admin, or accessing a sensitive resource).
- Or use the **step-up** flow template to gate sensitive operations.

Before migrating standalone MFA enrollment pages, ask whether MFA can be integrated into the main
Flow instead. This is almost always the cleaner approach in Descope and eliminates the need to
port the enrollment API call sequence entirely.

> **TOTP enrollments cannot be migrated.** Cognito does not export TOTP seeds, so all users with an authenticator app enrolled must re-enroll after migration. Flag this prominently in the migration plan and plan a user communication campaign before cutover.
>
> **SMS-OTP MFA can be preserved** — as long as phone numbers are migrated with verified status. When running the migration tool, ensure phone numbers are imported as verified. Descope will recognise the verified phone number as a valid login ID and MFA factor; users will not need to re-verify. If phone numbers are imported as unverified, users will be prompted to re-verify on first sign-in.

---

## Widgets: Post-Login Management UI

Widgets are embeddable management UI components for post-login operations. Each widget action
runs a Flow under the hood. Customizable via Console → Widgets without code changes.

### When to recommend a Widget

Whenever the migration plan calls for building or migrating custom code that calls Cognito admin APIs:

| Cognito code pattern | Consider this Widget instead |
|---|---|
| `Auth.updateUserAttributes()`, profile edit forms (frontend, user editing their own profile) | **User Profile Widget** — embeddable frontend component; no backend code needed |
| `adminUpdateUserAttributes()` (backend / server-side attribute updates) | Management SDK — `management.user.update()` or `management.user.setCustomAttributes()`; use the Widget only for user-facing self-service UI, not for server-side operations |
| `adminCreateUser()`, `adminDisableUser()`, `adminDeleteUser()`, user list pages | **User Management Widget** |
| `adminAddUserToGroup()`, role/group assignment UI | **Role Management Widget** |
| Per-tenant SSO settings page (configure IdP per customer) | **Tenant Profile Widget** (+ SSO Setup Suite) |
| Custom audit log views | **Audit Widget** |
| API access key management UI | **Access Key Management Widget** |

Ask before writing code: *"Does a Widget cover this use case?"*

### Widget types

**User-facing (for end users):**

| Widget | What it does |
|---|---|
| User Profile Widget | Edit name, email, avatar; manage MFA enrollment; manage connected accounts |
| Applications Portal Widget | List accessible applications |
| Outbound Applications Widget | Manage third-party OAuth connections |

**Admin-facing (for tenant admins within your app):**

| Widget | What it does |
|---|---|
| User Management Widget | Invite users, disable accounts, assign roles, view tenant members |
| Role Management Widget | Create and assign roles within a tenant |
| Access Key Management Widget | Create/revoke API access keys |
| Audit Widget | View audit events per tenant |
| Tenant Profile Widget | Edit tenant settings, configure SSO, manage SCIM |

### Widget vs. Flow component

| | Flow Component | Widget |
|---|---|---|
| **Purpose** | Authentication journey entry point | Post-login management UI |
| **Use case** | Sign-up, sign-in, MFA, step-up, invitation | Profile editing, user/role/key management |
| **When to use** | Login and auth flows | Any post-login management feature |

---

## SSO Setup Suite

The SSO Setup Suite is a no-code Console wizard for SAML and OIDC SSO configuration.
It guides tenant admins through per-tenant SSO setup with step-by-step instructions
specific to common IdPs (Okta, Azure AD, Google Workspace, etc.).

### When to recommend it

Surface this before migrating any SSO-related code:

- App uses Cognito SAML federation (`Auth.federatedSignIn({ provider: '<SAMLProviderName>' })`)
- App has a pre-signup Lambda that routes users to different IdPs based on email domain
- App uses `identity_provider=<orgName>` in Cognito Hosted UI redirect URLs
- App has a custom SSO settings page where tenant admins configure their IdP
- Migration plan includes `management.sso.configureSAMLSettings()` or `management.sso.configureOIDCSettings()`

**The question to ask is: how do your customers' tenant admins set up their SSO today?**

- **They do it themselves through a settings page you built, or it's set up manually** → use the **SSO Setup Suite**. It gives tenant admins a guided, self-serve UI to configure their IdP (Okta, Azure AD, Google Workspace, etc.) without any engineering involvement. If you built a custom SSO settings page in your app, the SSO Setup Suite + Tenant Profile Widget replaces it entirely — you can remove that code.

- **You just need to add SSO as a sign-in option for your app** (i.e., you configure a single IdP connection, not per-tenant) → this is a one-time setup in the Descope Console or via a Flow action. It does not require the SSO Setup Suite.

- **SSO connections are provisioned programmatically** (CI/CD pipelines, API-driven tenant onboarding, automated setup) → use the management SDK (`management.sso.configureSAMLSettings()` / `management.sso.configureOIDCSettings()`). The SSO Setup Suite is a UI tool; the management API is for when your code needs to create or update connections at runtime.

### What it does

- Generates per-tenant SAML metadata and ACS URL
- Walks tenant admins through IdP-specific setup (Okta, Azure, Google, etc.)
- Handles SCIM token generation for provisioning
- Removes engineering involvement for SSO onboarding of new tenants

### Multi-tenant SAML routing (sending each customer's users to their own SSO IdP)

Cognito's approach to routing users to different IdPs per org typically uses one of:
- A pre-signup or pre-auth Lambda that checks the email domain and raises an exception to redirect
- `identity_provider=<orgName>` query param in the Hosted UI authorize URL
- Separate User Pool per customer, each with its own SAML IdP

In Descope:
- Create one **Tenant** per customer org in Console
- Configure a SAML/OIDC SSO connection per Tenant via the SSO Setup Suite
- Add domain(s) to each Tenant — Descope automatically routes users to the correct IdP based on email domain
- The pre-signup Lambda and domain-routing code are no longer needed

---

## Console vs. Code: The Decision Guide

### Do in the Console

| Task | Where in Console |
|---|---|
| Auth flow logic (sign-up, MFA, step-up, password reset, invitation) | Flows |
| Lambda trigger logic (pre-signup validation, post-confirmation webhooks) | Flow steps: Conditions, Scriptlets, Connectors |
| Custom JWT claims (replacing Pre-Token Generation trigger) | Authorization → JWT Templates |
| Branding (logo, colors, fonts) | Styles |
| RBAC model (create roles and permissions) | Authorization → RBAC |
| Per-tenant SSO configuration | SSO Setup Suite |
| Social OAuth providers (Google, Facebook, Apple) | Authentication → Social |
| Email/SMS templates (replacing Cognito verification emails) | Authentication method settings → Templates |
| Session token lifetime and refresh settings | Project → Session Management |
| Custom attributes (replacing `custom:*`) | Project → Custom Attributes |
| Connectors (external webhooks, Slack, Salesforce, etc.) | Connectors |
| Custom email or SMS delivery provider (replacing Cognito SES/SNS config) | Connectors — configure your email provider (SendGrid, Mailgun, AWS SES, etc.) or SMS provider (Twilio, Vonage, etc.) as a Connector, then select it under the relevant authentication method or MFA step |
| Access Keys (M2M) | Access Keys |

### Do in code

| Task | Why it's code |
|---|---|
| Session validation on protected routes | Must run on every request; always backend code |
| RBAC/ReBAC enforcement | Reads JWT claims; always in middleware |
| User/tenant automation at scale | Bulk provisioning, CI/CD, infrastructure-as-code |
| Custom business logic during auth | Expose as a backend endpoint; call from Flow via Generic HTTP Connector |
| SDK setup (one-time) | Install SDK, wrap app in `AuthProvider`, embed Flow component |
| Database user ID remapping | Cognito `sub` → Descope `sub` migration; must run as a data script |

### The mental model

> **Console owns the user journey. Code owns business logic.**

Engineers integrate once (SDK setup + session validation middleware). All subsequent auth
evolution — new auth methods, MFA step changes, UI updates, Lambda trigger logic, custom JWT
claims, new social providers — happens in the Console without code deployments.

When a migration replaces Cognito Lambda trigger code with equivalent application code, that's
acceptable. When it replaces Lambda trigger code with a Console Flow step or JWT Template, that's
better — there is no code to maintain and no deployment required to change the auth behavior.
