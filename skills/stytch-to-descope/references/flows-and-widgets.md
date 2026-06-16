# Descope Flows, Widgets, and Console-First Reference

This file covers Descope's no-code/low-code layer — Flows, Widgets, the SSO Setup Suite, and
the Console-vs-code decision guide. Read it when the migration touches auth UI, MFA enrollment,
user management pages, or SSO configuration. In all those areas, a Console/Flow/Widget approach
is usually faster and safer than writing code.

---

## Contents

- [Terminology: Stytch → Descope Lingo](#terminology-stytch--descope-lingo)
- [Flows: Structure and What They Replace](#flows-structure-and-what-they-replace)
- [Widgets: Post-Login Management UI](#widgets-post-login-management-ui)
- [SSO Setup Suite](#sso-setup-suite)
- [Console vs. Code: The Decision Guide](#console-vs-code-the-decision-guide)

---

## Terminology: Stytch → Descope Lingo

### The key mapping: Organization → Tenant

Unlike some migrations, there is **no "tenant" naming collision** between Stytch and Descope —
both call the top-level account a **Project**. The mapping that matters most is the B2B customer:
a Stytch **Organization** becomes a Descope **Tenant**, and a Stytch **Member** becomes a Descope
**User** associated with that tenant.

| Stytch term | Descope term | Notes |
|---|---|---|
| **Project** (with Test/Live environments) | **Project** | Top-level unit. Has auth methods, Flows, users, and settings. In Descope each environment is a separate Project (vs. Stytch's Test/Live split within one project). |
| **Organization** (your B2B customer) | **Tenant** | "For B2B apps, a tenant is your customer." Direct equivalent of a Stytch Organization. |
| Direct SDK integration / **Connected App** (OAuth client) | **Project** (direct SDK integration) or **Federated / Inbound Application** (OIDC/SAML clients) | Use the Project directly for SDK-based integration; use a Federated/Inbound Application when Stytch Connected Apps act as OAuth/OIDC clients. |
| **M2M Client / Client Credentials** | **Access Key** | Presented to exchange for a short-lived JWT. Supports expiration, permitted IPs, tenant/role scoping. |
| **Prebuilt UI components** (Stytch UI, embedded) | **Auth Hosting** (hosted) or embedded **`<descope-wc>` / `<Descope>` component** | Stytch's UI is embedded in your app; Descope Flows define the auth experience whether hosted or embedded. |
| **OAuth / social login** (Google, GitHub…) | **OAuth Provider** | Configured under Authentication Methods in Console. |
| **SSO Connection** (SAML/OIDC per-Organization) | **Tenant SSO** | Per-tenant configuration. Use the SSO Setup Suite for self-service. |
| **UI appearance / customization** | **Styles** | Logo, colors, fonts in Console → Styles. Inherited by all Flow Screens. |
| **RBAC (Roles / Permissions)** | **Roles / Permissions** | Same concepts. Project-level and tenant-level. Stored as strings in JWT. |
| **Backend API** (project ID + secret) | **Management SDK + Management Key** | Same capabilities, different auth (Management Key vs. Stytch project secret). |

### Other Descope-specific terms

- **Project** — the top-level unit. Think Stytch Project (with its Test/Live environments).
- **Flow** — visual auth pipeline. Replaces Stytch's embedded UI plus the auth orchestration you'd otherwise write around the Stytch SDK.
- **Screen** — one UI page within a Flow. Designed in Screen Builder.
- **Scriptlet** — inline JS step in a Flow (Lodash + CryptoJS included). Escape hatch for custom logic.
- **Connector** — HTTP call step in a Flow. Response stored in flow context.
- **Subflow** — one Flow embedded inside another. Context passes through; does not terminate the parent.
- **Descoper** — a person with Console access. Managed in Company Settings → Descopers with custom roles.
- **Auth Hosting Application** — the Descope-hosted login UI (Stytch's UI, by contrast, is embedded in your app).

---

## Flows: Structure and What They Replace

A Descope Flow is a visual, no-code authentication pipeline built in the Console. It IS the
authentication process — not a hook on top of it. Flows can be changed without redeploying
the application.

### What Flows replace from Stytch

| Stytch | Descope Flow equivalent |
|---|---|
| Custom session claims / post-authentication logic (written around the Stytch SDK) | Flow steps (Actions, Scriptlets, Custom Claims) |
| Stytch prebuilt UI components | Flow Screens |
| Email verification (magic link / email OTP) | Email verification Flow step |
| Password reset | Password reset Flow (template available) |
| MFA enrollment (TOTP, SMS OTP) | MFA step in main sign-in Flow, or MFA subflow |
| Member invitation emails | Invitation Flow (template available) |
| Step-up authentication | Step-up Flow (template: `step-up`; adds `su` claim to JWT) |
| Fraud & Risk / Device Fingerprinting (bot detection, brute force) | Connector steps (Arkose, reCAPTCHA, Fingerprint, HaveIBeenPwned, AbuseIPDB) |

### Building blocks

1. **Screens** — UI forms. Designed in Screen Builder. Support conditional show/hide of components based on context values (`user.*`, `form.*`, `tenant.*`).
2. **Actions** — single-task steps: authenticate, send OTP, verify magic link, create user, assign role, set custom claims, end the flow.
3. **Conditions** — branch routing based on context values (`user.*`, `tenant.*`, `form.*`, `connectors.<key>`, `jwtClaims.*`, `cookies.<name>`).
4. **Connectors** — HTTP calls to external services during the flow. Response stored as `connectors.<contextKey>` for use in later Conditions, Actions, or Custom Claims.

**Advanced:**
- **Scriptlets** — inline JavaScript. Useful for string manipulation, hashing, date math, or calling Lodash/CryptoJS utilities. Has a test/debug mode.
- **Subflows** — embed one Flow inside another. The subflow End continues back to the parent instead of generating a JWT. Pass inputs via `{{subflowInput.key}}`. Good for MFA as a step inside a larger sign-in journey.

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
- Invitation, user impersonation, progressive profiling, account recovery

**Before writing any custom Flow configuration:** check whether a template already covers the
use case. Most common patterns are available out of the box.

### MFA enrollment specifically

Many Stytch apps build a separate MFA enrollment page wired to the Stytch MFA endpoints (TOTP, SMS OTP). In Descope, enrollment happens inline in the Flow instead — there is no separate enrollment page to maintain.

**The Descope approach:**
- Add an MFA step to the main sign-up/sign-in Flow — enrollment happens inline during the auth journey
- Or embed MFA as a **subflow** — triggered by a condition (e.g., user is admin, or risk score is high)
- Or use the **step-up** flow template to gate sensitive operations

Before migrating a standalone MFA enrollment page, ask whether MFA can be integrated into the main Flow instead. This is almost always the cleaner approach in Descope.

---

## Widgets: Post-Login Management UI

Widgets are embeddable management UI components for post-login operations. Each widget
action runs a Flow under the hood. Customizable via Console → Widgets without code changes.

### When to recommend a Widget

Whenever the migration plan calls for building or migrating a custom:
- Profile edit page → **User Profile Widget**
- User management page (admin view) → **User Management Widget**
- Role assignment UI → **Role Management Widget**
- Tenant SSO setup page → **Tenant Profile Widget** (+ SSO Setup Suite)
- Audit log view → **Audit Widget**

Ask before writing code: *"Does a Widget cover this use case?"*

### Widget types

**User-facing (for end users):**

| Widget | What it does |
|---|---|
| User Profile Widget | Edit name, email, avatar; manage MFA enrollment; manage connected accounts |
| Applications Portal Widget | List accessible applications |
| Outbound Applications Widget | Manage third-party OAuth connections (Outbound Apps) |

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

Surface this before migrating any SSO-related Management SDK calls:

- App uses Stytch's SSO connection APIs (`sso.saml.createConnection()` / `sso.oidc.createConnection()`)
- Migration plan includes `management.sso.configureSAMLByTenant()` or `configureOIDCByTenant()`
- App has a custom SSO settings page where tenant admins configure their IdP

**The question to ask:**
> "Does this app need programmatic SSO configuration (CI/CD provisioning, API-driven setup), or do tenant admins configure SSO themselves through a settings page? If the latter, the SSO Setup Suite + Tenant Profile Widget may remove the need for that SDK code entirely."

### What it does

- Generates per-tenant SAML metadata and ACS URL
- Walks tenant admins through IdP-specific setup (Okta, Azure, Google, etc.)
- Handles SCIM token generation for provisioning
- Removes engineering involvement for SSO onboarding of new tenants

---

## Console vs. Code: The Decision Guide

### Do in the Console

| Task | Where in Console |
|---|---|
| Auth flow logic (sign-up, MFA, step-up, invitation, reset) | Flows |
| Branding (logo, colors, fonts) | Styles |
| RBAC model (create roles and permissions) | Authorization → RBAC |
| Per-tenant SSO configuration | SSO (or SSO Setup Suite) |
| Social OAuth providers | Authentication → Social |
| Email/SMS templates | Authentication method settings → Templates |
| Session token lifetime and refresh settings | Project → Session Management |
| Custom JWT claims (profile fields, roles in token) | Authorization → JWT Templates |
| Custom tenant/user attributes | Project → Custom Attributes |
| Connectors (Slack, Salesforce, HTTP webhooks, etc.) | Connectors |
| Access Keys (M2M) | Access Keys |
| Descopers (Console access control) | Company Settings → Descopers |

### Do in code

| Task | Why it's code |
|---|---|
| Session validation on protected routes | Must run on every request; always backend code |
| RBAC/ReBAC enforcement | Reads JWT claims; always in middleware |
| Tenant/user automation at scale | Bulk provisioning, CI/CD, infrastructure-as-code |
| Custom business logic during auth | Expose as a backend endpoint; call from Flow via Generic HTTP Connector |
| SDK setup (one-time) | Install SDK, wrap app in `AuthProvider`, embed Flow component |

### The mental model

> **Console owns the user journey. Code owns business logic.**

Engineers integrate once (SDK setup + session validation middleware). All subsequent auth
evolution — new auth methods, MFA step changes, UI updates, connector integrations, new
social providers — happens in the Console without code deployments.

When a migration replaces Stytch code with equivalent Descope SDK calls, that's correct.
When it replaces Stytch code with Console configuration, that's better.