# Descope Flows, Widgets, and Console-First Reference

This file covers Descope's no-code/low-code layer — Flows, Widgets, the SSO Setup Suite, and
the Console-vs-code decision guide. Read it when the migration touches auth UI, MFA enrollment,
user management pages, or SSO configuration. In all those areas, a Console/Flow/Widget approach
is usually faster and safer than writing code.

---

## Contents

- [Terminology: WorkOS → Descope Lingo](#terminology-workos--descope-lingo)
- [Flows: Structure and What They Replace](#flows-structure-and-what-they-replace)
- [Widgets: Post-Login Management UI](#widgets-post-login-management-ui)
- [SSO Setup Suite](#sso-setup-suite)
- [Console vs. Code: The Decision Guide](#console-vs-code-the-decision-guide)

---

## Terminology: WorkOS → Descope Lingo

### Critical naming mapping

The most common migration mistake: assuming WorkOS terms map one-to-one onto identically named
Descope terms. They don't. WorkOS's **Organization** (your B2B customer) becomes a Descope
**Tenant** — Descope has no object called "Organization." And a WorkOS **Environment** maps to a
Descope **Project**.

| WorkOS term | Descope term | Notes |
|---|---|---|
| **Environment** (dev / staging / prod) | **Project** | Top-level unit. Each WorkOS environment → its own Descope Project with its own Project ID. |
| **Organization** (your B2B customer) | **Tenant** | Direct equivalent. WorkOS Organizations group users and scope SSO, SCIM, roles, and domains per customer; Descope Tenants do the same. |
| Client ID + API key | **Project ID** (+ **Management Key** for server-side admin) | WorkOS uses a public client ID and a secret API key; Descope uses a public Project ID and an optional Management Key. |
| AuthKit (hosted or embedded login UI) | **Auth Hosting** (hosted) or embedded **`<descope-wc>` / `<Descope>` component** | Flows define the auth experience in both cases. |
| Social / OAuth login | **OAuth Provider** | Configured under Authentication Methods in Console. |
| Enterprise SSO Connection (SAML/OIDC, per Organization) | **Tenant SSO** | Per-tenant configuration. Use the SSO Setup Suite for self-service. |
| Directory Sync (SCIM, per Organization) | **SCIM / Tenant provisioning** | Per-tenant directory provisioning lifecycle. |
| Admin Portal | **SSO Setup Suite + Widgets** | Hosted self-serve admin UI for SSO, SCIM, and domain setup. |
| Radar (bot/fraud detection) | **Fingerprinting + Flow security Connectors** | Detection signals (`riskInfo`) consumed inside Flows; CAPTCHA/fraud Connectors for challenges. |
| AuthKit MFA (TOTP / SMS, dashboard-configured) | **MFA Flow step** / **step-up** template | MFA runs inline in the Flow rather than as a separate page. |
| Branding | **Styles** | Logo, colors, fonts in Console → Styles. Inherited by all Flow Screens. |
| Roles / Permissions | **Roles / Permissions** | Same concepts. Project-level and tenant-level. Stored as strings in JWT. |
| Management API (API key) | **Management SDK + Management Key** | Same capabilities, different auth (Management Key vs. WorkOS API key). |
| M2M / API authentication | **Access Key** | Presented to exchange for a short-lived JWT. Supports expiration, permitted IPs, tenant/role scoping. |
| Audit Logs | **Audit / Audit Widget** | Per-tenant audit events. |
| WorkOS integration / webhook | **Connector** | Added as a step inside a Flow. Response available in flow context as `connectors.<contextKey>`. |

### Other Descope-specific terms

- **Project** — the top-level unit. Think WorkOS environment.
- **Flow** — visual auth pipeline. Replaces AuthKit's hosted/embedded login UI and any custom post-login logic.
- **Screen** — one UI page within a Flow. Designed in Screen Builder.
- **Scriptlet** — inline JS step in a Flow (Lodash + CryptoJS included). Escape hatch for custom logic.
- **Connector** — HTTP call step in a Flow. Response stored in flow context.
- **Subflow** — one Flow embedded inside another. Context passes through; does not terminate the parent.
- **Descoper** — a person with Console access. Managed in Company Settings → Descopers with custom roles.
- **Auth Hosting Application** — the hosted login UI (equivalent to AuthKit's hosted login domain).

---

## Flows: Structure and What They Replace

A Descope Flow is a visual, no-code authentication pipeline built in the Console. It IS the
authentication process — not a hook on top of it. Flows can be changed without redeploying
the application.

### What Flows replace from WorkOS

| WorkOS | Descope Flow equivalent |
|---|---|
| AuthKit hosted/embedded login UI | Flow Screens |
| AuthKit redirect + callback login cycle | Embedded Flow component (no server redirect needed) |
| Email verification (AuthKit) | Email verification Flow step |
| Password reset (AuthKit) | Password reset Flow (template available) |
| Magic Auth | Magic link Flow step |
| AuthKit MFA (TOTP / SMS) | MFA step in main sign-in Flow, or MFA subflow |
| Custom post-login logic in callback handlers (claims, role assignment) | Flow steps (Actions, Scriptlets, Custom Claims) |
| Step-up authentication | Step-up Flow (template: `step-up`; adds `su` claim to JWT) |
| Radar (bot detection, brute force) | Connector steps (Arkose, reCAPTCHA, Fingerprint, HaveIBeenPwned, AbuseIPDB) + Flow conditions on `riskInfo` |

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

WorkOS AuthKit handles MFA (TOTP and SMS) inline within its hosted/embedded login flow, enabled
from the WorkOS dashboard — so there's usually no standalone enrollment page to migrate. Descope
follows the same inline model, so keep MFA inside the auth journey rather than rebuilding a
separate page.

**The Descope approach:**
- Add an MFA step to the main sign-up/sign-in Flow — enrollment happens inline during the auth journey
- Or embed MFA as a **subflow** — triggered by a condition (e.g., user is admin, or risk score is high)
- Or use the **step-up** flow template to gate sensitive operations

If the WorkOS app does have a custom standalone MFA page, ask whether MFA can be integrated into the
main Flow instead. This is almost always the cleaner approach in Descope.

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
specific to common IdPs (Okta, Microsoft Entra ID, Google Workspace, etc.).

### When to recommend it

Surface this before migrating any SSO-related Management SDK calls:

- App configures WorkOS SSO connections per Organization (via the WorkOS dashboard or the `workos.sso` API)
- Migration plan includes `management.sso.configureSAMLByTenant()` or `configureOIDCByTenant()`
- App has a custom SSO settings page where tenant admins configure their IdP
- App uses the WorkOS **Admin Portal** for customer-admin SSO/SCIM setup

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
| Custom user attributes | Project → Custom Attributes |
| Custom tenant attributes | Tenants → Custom Attributes |
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

When a migration replaces WorkOS code with equivalent Descope SDK calls, that's correct.
When it replaces WorkOS code with Console configuration, that's better.
