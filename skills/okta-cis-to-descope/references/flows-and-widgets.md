# Descope Flows, Widgets, and Console-First Reference

This file covers Descope's no-code/low-code layer — Flows, Widgets, the SSO Setup Suite, and
the Console-vs-code decision guide. Read it when the migration touches auth UI, MFA enrollment,
user management pages, or SSO configuration. In all those areas, a Console/Flow/Widget approach
is usually faster and safer than writing code.

---

## Contents

- [Terminology: Okta CIS → Descope Lingo](#terminology-okta-cis--descope-lingo)
- [Flows: Structure and What They Replace](#flows-structure-and-what-they-replace)
- [Widgets: Post-Login Management UI](#widgets-post-login-management-ui)
- [SSO Setup Suite](#sso-setup-suite)
- [Console vs. Code: The Decision Guide](#console-vs-code-the-decision-guide)

---

## Terminology: Okta CIS → Descope Lingo

### Critical naming inversion

Okta and Descope use different words for overlapping concepts. The table below is the
authoritative reference — always check here before using an Okta term in a Descope context.

Sources:
- Authenticators: [developer.okta.com/docs/guides/authenticators-overview](https://developer.okta.com/docs/guides/authenticators-overview/main/)
- Policies: [developer.okta.com/docs/concepts/policies](https://developer.okta.com/docs/concepts/policies/)
- Authorization Servers: [developer.okta.com/docs/concepts/auth-servers](https://developer.okta.com/docs/concepts/auth-servers/)
- Identity Providers: [help.okta.com/oie/topics/security/identity_providers](https://help.okta.com/oie/en-us/content/topics/security/identity_providers.htm)
- Log Streams: [help.okta.com/oie/topics/Reports/log-streaming](https://help.okta.com/oie/en-us/Content/Topics/Reports/log-streaming/about-log-streams.htm)

| Okta CIS term | Descope term | Notes |
|---|---|---|
| **Okta org** (your Okta account) | **Project** | Top-level unit. Multiple environments → multiple Projects. |
| **Customer / B2B org** | **Tenant** | Descope tenant = your B2B customer. Direct equivalent. |
| **Okta Sign-In Widget** (`@okta/okta-signin-widget`) | **Descope Flow component** | Drop-in embedded replacement. Swap `new OktaSignIn(...)` for `<Descope flowId="sign-up-or-in" />`. No redirect needed. |
| **Hosted Sign-In Page** (Okta-hosted redirect) | **Auth Hosting Application** | Descope's hosted login page. Same redirect pattern; customize via Flow Screens and Styles. |
| **Application** (Web, SPA, Native) | **Federated App** or **Inbound App** | Federated = OIDC/SAML federation only; Inbound = OAuth with scope enforcement. Use Inbound when the backend validates scopes. |
| **Sign-On Policy** (per-app) | **Flow** | Visual auth pipeline; replaces Okta's per-app policy rule chain. |
| **Authenticator Enrollment Policy** | **Flow** (MFA step or subflow) | Inline enrollment replaces Okta's separate enrollment journey. |
| **Global Session Policy** | **Project session config** | Lifetime and refresh settings in Console → Project Settings → Session Management. |
| **Authenticator** (Passkeys/FIDO2, TOTP, Okta Verify, Password, SMS, Phone, Security Question) | **Auth Method** | Configured in Console → Authentication. One auth method per authenticator type. |
| **Token Inline Hook** | **Flow Scriptlet** or **Generic HTTP Connector** | Custom logic during auth. Scriptlet = inline JS; Connector = external HTTP call. |
| **Group** | **Role** (flat or tenant-scoped) | Project-level or per-tenant RBAC. |
| **Log Stream → Splunk Cloud** | **Splunk Audit Connector** | OOTB Descope connector. |
| **Log Stream → Amazon EventBridge** | **Audit Webhook Connector** | Custom HTTP sink. (Datadog is NOT a direct Okta Log Stream destination — integrates indirectly.) |
| **Authorization Server** (custom or org-level) | **Resource** | Descope's new Resources feature. Audience is immutable in both. |
| **Service App / API Services** (M2M) | **Access Key** | Client credentials flow → Access Key exchange. |
| **Identity Provider** (external SAML/OIDC per-org) | **Tenant SSO** | Per-tenant. Use SSO Setup Suite for self-service setup. |
| **Custom Claims** (Expression Language on Authorization Server) | **JWT Template** | On Inbound App or project level — NOT on the Resource in Descope. |
| **Resource policy** (scope-based access control) | **Inbound App authorization rules** | Scope-based access logic lives at the Inbound App, not the Resource. |
| **Okta Marketplace integration** | **Connector** | HTTP call step in a Flow. Response stored as `connectors.<contextKey>`. |

### Other Descope-specific terms

- **Project** — the top-level unit. Think Okta org.
- **Flow** — visual auth pipeline. Replaces Okta Sign-On Policies + authentication UI.
- **Screen** — one UI page within a Flow. Designed in Screen Builder.
- **Scriptlet** — inline JS step in a Flow (Lodash + CryptoJS included). Escape hatch for custom logic.
- **Connector** — HTTP call step in a Flow. Response stored in flow context.
- **Subflow** — one Flow embedded inside another. Context passes through; does not terminate the parent.
- **Descoper** — a person with Console access. Managed in Company Settings → Descopers with custom roles.
- **Auth Hosting Application** — the hosted login UI (equivalent to Okta's hosted sign-in page).
- **Inbound App** — an OAuth client with scope enforcement; use when the backend validates scopes.
- **Federated App** — an OIDC/SAML relying party; use when Okta is used purely for authentication.

---

## Flows: Structure and What They Replace

A Descope Flow is a visual, no-code authentication pipeline built in the Console. It IS the
authentication process — not a hook on top of it. Flows can be changed without redeploying
the application.

### What Flows replace from Okta CIS

| Okta CIS | Descope Flow equivalent |
|---|---|
| **Okta Sign-In Widget** (embedded `@okta/okta-signin-widget`) | **Descope Flow component** (`<Descope flowId="..." />`) — same embed, no redirect |
| Sign-On Policy (per-app auth rule chain) | Flow steps (conditions, auth methods, Connectors) |
| Authenticator Enrollment Policy (MFA enrollment logic) | MFA step in main sign-in Flow, or MFA subflow |
| Global Session Policy (session duration, re-auth) | Flow → End action settings + Project session config |
| Hosted sign-in page UI | Flow Screens + Auth Hosting Application |
| Email verification sequence | Email verification Flow step |
| Password reset sequence | Password reset Flow (template available) |
| Invitation emails | Invitation Flow (template available) |
| Step-up authentication | Step-up Flow (template: `step-up`; adds `su` claim to JWT) |
| Progressive profiling | Progressive profiling Flow (template available) |
| Token Inline Hook (custom claim injection, external call) | Flow Scriptlet (inline logic) or Generic HTTP Connector |

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

Okta's Authenticator Enrollment Policies trigger a separate enrollment journey when a required
factor is missing. That separate journey has no direct Descope equivalent.

**The Descope approach:**
- Add a second auth method step after the primary step in the sign-in Flow — there is no single "MFA step" button; MFA is two sequential auth method steps. If the user hasn't enrolled in the second method, the Flow prompts enrollment inline.
- Or embed the MFA sequence as a **subflow** — triggered by a Condition (e.g., user role is admin, or a risk signal is present)
- Or use the **step-up** Flow template to gate sensitive operations after initial sign-in

Before migrating a standalone MFA enrollment flow, ask whether MFA can be integrated into the
main sign-in Flow. This is almost always the cleaner approach in Descope.

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

Surface this before writing any SSO provisioning code. The signal to look for is programmatic
SSO setup in the existing Okta integration — i.e., your engineers currently call Okta's Identity
Provider API (`POST /api/v1/idps`) to create per-tenant SAML or OIDC connections, and the
migration plan includes equivalent Descope SDK calls like `management.sso.configureSAMLByTenant()`
or `configureOIDCByTenant()`.

Key indicators:
- Engineers currently provision new tenant SSO connections in Okta (not tenant admins)
- There is a backend service or script that calls `POST /api/v1/idps` to create IdPs
- There is a custom SSO settings page where tenant admins configure their IdP via your app's backend

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
| Session token lifetime and refresh settings | Project Settings → Session Management |
| Custom JWT claims (profile fields, roles in token) | Project Settings → JWT Templates |
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

When a migration replaces Okta code with equivalent Descope SDK calls, that's correct.
When it replaces Okta code with Console configuration, that's better.
