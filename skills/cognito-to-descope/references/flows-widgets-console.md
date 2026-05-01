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
| **User Pool Group** (capability-based: `admin`, `editor`, `viewer`) | **Role** | Roles describe what a user *can do*. |
| **User Pool Group** (org-based: `acme-corp`, `tenant_123`, a UUID) | **Tenant** | Tenants describe *who the user belongs to*. |
| **Separate User Pool per customer org** | **Tenant** | One Tenant per pool, all within a single Project. |
| **Cognito Hosted UI** | **Auth Hosting** (hosted) or embedded `<Descope>` component | Flows define the auth experience in both cases. |
| **Lambda Trigger** (pre-signup, post-confirmation, pre-auth, custom challenge…) | **Flow step + Scriptlet + Connector** | Flows replace the entire Lambda trigger pipeline. |
| **Pre-Token Generation trigger** | **JWT Templates** in Console | Define custom JWT claims without code deployment. |
| **Migrate User trigger** | **JIT migration via Generic HTTP Connector** in Flow | Users are migrated on first sign-in without bulk import. |
| **Custom Authentication Challenge** | **Scriptlet** in a Flow | Fully custom auth logic runs inline inside a Flow step. |
| **M2M / Client Credentials** | **Access Key** | Exchange for a short-lived JWT. Supports expiration, permitted IPs, tenant/role scoping. |
| **Identity Pools (Federated Identities)** | Not replaced by Descope | Configure Descope as a federated OIDC provider in the existing Identity Pool. |
| **Cognito as OIDC provider for external clients** | **Federated Application** (OIDC/SAML) | Configure in Console → Applications. |
| **Custom attributes** (`custom:*`) | **Custom Attributes** | Defined in Console → Project → Custom Attributes. |
| **SMS MFA** | **OTP via SMS** (Flow step) | Configure under Console → Authentication Methods → SMS OTP. |
| **TOTP / authenticator app MFA** | **TOTP** (Flow step) | Add TOTP step to sign-in Flow. |
| **Device tracking / remembered devices** | Not available | Cannot be migrated — remove device-tracking code. |
| **Social providers** (Google, Facebook, Apple via Cognito federation) | **OAuth Provider** | Configured under Console → Authentication Methods. |
| **Enterprise SAML/OIDC per-org** (separate IdP per customer pool) | **Tenant SSO** | Per-tenant configuration via SSO Setup Suite. |
| **Email/SMS verification templates** | **Templates** | Configured per authentication method in Console. |
| **FORCE_CHANGE_PASSWORD users** | Route to magic link or OTP in Flow | These users cannot use password sign-in after migration. |

### Other Descope-specific terms

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
| MFA enrollment (TOTP via `associateSoftwareToken`/`verifySoftwareToken`, SMS MFA) | MFA step in main sign-up/sign-in Flow, or MFA subflow |
| Custom Authentication Challenge (define, create, verify Lambda trio) | Scriptlet steps in a Flow |
| Migrate User Lambda trigger (real-time password verification against old system) | JIT migration via Generic HTTP Connector in Flow |
| Pre-Token Generation trigger (custom JWT claims) | JWT Templates in Console |
| Attack protection (advanced security — rate limiting, adaptive auth) | Connector steps (Arkose, reCAPTCHA, Fingerprint, AbuseIPDB) |

### Lambda triggers → Descope equivalents

| Cognito Lambda Trigger | Descope equivalent | Notes |
|---|---|---|
| Pre-signup | Flow Condition | Block or allow based on email domain, custom attribute, or Connector response |
| Post-confirmation | Flow Action + Connector | Call external service after user confirmed; or use Connector with a webhook |
| Pre-authentication | Flow Condition | Block sign-in based on user state, risk score, or IP allowlist check |
| Post-authentication | Flow Connector | Call webhook or update external system after successful sign-in |
| Custom authentication challenge (define / create / verify) | Scriptlet steps | Full custom logic inline in the Flow; use Connector for external calls |
| Migrate User | JIT flow via Generic HTTP Connector | Connector verifies credentials against Cognito; on success, Descope creates the user |
| Pre-token generation | JWT Templates | Defined in Console → Authorization → JWT Templates |
| Pre-signup domain validation (multi-tenant routing) | Flow Condition + Tenant routing | Check email domain in Flow; route to matching Tenant's SSO connection |

**Before migrating any Lambda trigger to code**, check whether a Flow step, Condition, Scriptlet,
or JWT Template can handle it without a Lambda at all. The majority of pre-signup validation,
post-confirmation webhooks, and custom claims can move entirely to the Console.

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

> **MFA enrollments cannot be migrated.** All TOTP and SMS-enrolled users must re-enroll after
> migration. Flag this prominently in the migration plan.

---

## Widgets: Post-Login Management UI

Widgets are embeddable management UI components for post-login operations. Each widget action
runs a Flow under the hood. Customizable via Console → Widgets without code changes.

### When to recommend a Widget

Whenever the migration plan calls for building or migrating custom code that calls Cognito admin APIs:

| Cognito code pattern | Consider this Widget instead |
|---|---|
| `adminUpdateUserAttributes()`, `Auth.updateUserAttributes()`, profile edit forms | **User Profile Widget** |
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

**The question to ask:**
> "Does this app need programmatic SSO configuration (CI/CD provisioning, API-driven setup), or
> do tenant admins configure SSO themselves through a settings page? If the latter, the SSO Setup
> Suite + Tenant Profile Widget may remove the need for that code entirely."

### What it does

- Generates per-tenant SAML metadata and ACS URL
- Walks tenant admins through IdP-specific setup (Okta, Azure, Google, etc.)
- Handles SCIM token generation for provisioning
- Removes engineering involvement for SSO onboarding of new tenants

### Multi-tenant SAML routing

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
