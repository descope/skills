# Descope Flows, Widgets, and Console-First Reference

This file covers Descope's no-code/low-code layer — Flows, Widgets, the SSO Setup Suite, and
the Console-vs-code decision guide. Read it when the migration touches auth UI, MFA enrollment,
user management pages, or SSO configuration. In all those areas, a Console/Flow/Widget approach
is usually faster and safer than writing code.

---

## Contents

- [Terminology: Azure AD B2C → Descope Lingo](#terminology-azure-ad-b2c--descope-lingo)
- [Flows: Structure and What They Replace](#flows-structure-and-what-they-replace)
- [Widgets: Post-Login Management UI](#widgets-post-login-management-ui)
- [SSO Setup Suite](#sso-setup-suite)
- [Console vs. Code: The Decision Guide](#console-vs-code-the-decision-guide)

---

## Terminology: Azure AD B2C → Descope Lingo

### Naming traps

- **"B2C" is a product name, not an audience.** B2C tenants serve consumers *and* business customers who log in with their company SSO. Ask which.
- **"Application" in B2C is an app registration** — the same object type is used for a frontend, an API ("Expose an API"), and a daemon. In Descope these are different things: Inbound App, Resource, Inbound App with client credentials.
- **"Policy" in B2C is a login journey** (user flow or custom policy), not an access rule.
- **"Tenant" in B2C is the whole directory.** A Descope tenant is one of your business customers.

Sources:
- User flows and custom policies: [learn.microsoft.com/azure/active-directory-b2c/user-flow-overview](https://learn.microsoft.com/azure/active-directory-b2c/user-flow-overview)
- API connectors: [learn.microsoft.com/azure/active-directory-b2c/api-connectors-overview](https://learn.microsoft.com/azure/active-directory-b2c/api-connectors-overview)
- Tokens: [learn.microsoft.com/azure/active-directory-b2c/tokens-overview](https://learn.microsoft.com/azure/active-directory-b2c/tokens-overview)

| Azure AD B2C term | Descope term | Notes |
|---|---|---|
| **B2C tenant** (directory) | **Project** | One project per environment. |
| **Business customer** (one IdP connection each) | **Tenant** | Descope tenant = your B2B customer, with its own SSO, domains, roles. |
| **User flow** (`B2C_1_…`) | **Flow** | Visual pipeline; replaces portal-configured journeys. |
| **Custom policy** (`B2C_1A_…`, Identity Experience Framework XML) | **Flow** (+ subflows, Connectors, Scriptlets) | No XML, no policy keys, no upload order. |
| **User journey / orchestration step** | **Flow / Flow step** | Sub-journeys → subflows. |
| **Technical profile (IdP)** | **Social login** or **Tenant SSO** | SAML/OIDC per customer → Tenant SSO. |
| **REST technical profile / API connector** | **Generic HTTP Connector** | Response in `connectors.<contextKey>`. |
| **Claims transformation** | **Scriptlet** or **JWT Template** | |
| **Content definition / page layout** | **Flow Screens + Styles** | |
| **B2C-hosted page** (`b2clogin.com`) | **Auth Hosting** (Descope-hosted login) | Default target for redirect-based apps. |
| **Embedded sign-in** (iframe) | **Descope Flow component** | |
| **App registration (frontend)** | **Inbound App** (scoped tokens) or **Federated App** (login only) | |
| **App registration with "Expose an API"** | **Resource** | Keep the same scope names. |
| **App registration (client credentials)** | **Inbound App** (client credentials) | Not Access Keys. |
| **Custom attribute** (`extension_*`, on `b2c-extensions-app`) | **Custom attribute** | Define before import. |
| **Policy keys** | — | Descope manages signing keys; B2C secrets can't be exported. |
| **Conditional Access** (require MFA / block) | **Flow conditions + risk connectors** | |
| **Custom domain** (Azure Front Door) | **Custom domain** | |

### Other Descope-specific terms

- **Project** — the top-level unit. Think B2C tenant.
- **Flow** — visual auth pipeline. Replaces user flows and custom policy journeys.
- **Screen** — one UI page within a Flow. Designed in Screen Builder.
- **Scriptlet** — inline JS step in a Flow (Lodash + CryptoJS included). Escape hatch for custom logic.
- **Connector** — HTTP call step in a Flow. Response stored in flow context.
- **Subflow** — one Flow embedded inside another. Context passes through; does not terminate the parent.
- **Descoper** — a person with Console access. Managed in Company Settings → Descopers with custom roles.
- **Auth Hosting** — the Descope-hosted login UI (equivalent to the B2C-hosted page).
- **Inbound App** — an OAuth client that receives scoped access tokens for a Resource.
- **Resource** — an API (OAuth resource server) with its scopes.
- **Federated App** — an OIDC/SAML relying party used for login only.

---

## Flows: Structure and What They Replace

A Descope Flow is a visual, no-code authentication pipeline built in the Console. It IS the
authentication process — not a hook on top of it. Flows can be changed without redeploying
the application.

### What Flows replace from Azure AD B2C

| Azure AD B2C | Descope Flow equivalent |
|---|---|
| **B2C-hosted page** (user flow or custom policy, `b2clogin.com`) | **Descope-hosted login** (Auth Hosting) running a Flow — same redirect pattern |
| **Embedded sign-in** (iframe, `JourneyFraming`) | **Descope Flow component** (`<Descope flowId="..." />`) — true in-page embed |
| Sign-up/sign-in user flow, custom policy user journey | Flow steps (screens, conditions, auth methods, Connectors) |
| Orchestration steps / sub-journeys | Flow steps / subflows |
| Password reset user flow (or `AADB2C90118` redirect) | Password reset Flow or branch (template available) |
| Profile edit user flow | User Profile Widget, or a profile Flow |
| MFA (SMS, email OTP, TOTP) and Conditional Access "require MFA" | MFA steps in the sign-in Flow, or an MFA subflow behind a Condition |
| API connectors / REST technical profiles | Generic HTTP Connector at the same journey point |
| Claims transformations | Scriptlet (logic) or JWT Template (token shaping) |
| Page layouts (custom HTML/CSS/JS) | Flow Screens + Styles |
| Email verification during sign-up | Email verification Flow step |
| Step-up authentication | Step-up Flow (template: `step-up`; adds `su` claim to JWT) |
| Progressive profiling | Progressive profiling Flow (template available) |

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

B2C user flows enroll MFA inline (phone or authenticator app) when MFA is set to "Always on" or
"Conditional"; custom policies do it with dedicated orchestration steps. Descope does the same
inline in the Flow.

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
specific to common IdPs (Microsoft Entra ID, Okta, Google Workspace, etc.).

### When to recommend it

Surface this before writing any SSO provisioning code. B2C has no self-service SSO onboarding:
every new business customer means engineers editing custom policy XML (a new SAML or OIDC
technical profile, a `ClaimsProviderSelection`, `domain_hint` routing) and re-uploading policies.

Key indicators:
- Custom policy files contain one technical profile per customer IdP
- Engineers (not customer admins) onboard each customer's SSO
- A custom SSO settings page or script exists to collect customer IdP metadata

**The question to ask:**
> "Does this app need programmatic SSO configuration (CI/CD provisioning, API-driven setup), or do tenant admins configure SSO themselves through a settings page? If the latter, the SSO Setup Suite + Tenant Profile Widget may remove the need for that SDK code entirely."

### What it does

- Generates per-tenant SAML metadata and ACS URL
- Walks tenant admins through IdP-specific setup (Entra ID, Okta, Google, etc.)
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
| M2M clients (client credentials) | Inbound Apps (client credentials) — not Access Keys |
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

When a migration replaces MSAL code with equivalent Descope SDK calls, that's correct.
When it replaces custom policy XML or custom code with Console configuration, that's better.
