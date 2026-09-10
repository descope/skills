# Descope Flows, Widgets, and Console-First Reference

This file covers Descope's no-code/low-code layer — Flows, Widgets, the SSO Setup Suite, and
the Console-vs-code decision guide. Read it when the migration touches auth UI, MFA enrollment,
user management pages, or SSO configuration. In all those areas, a Console/Flow/Widget approach
is usually faster and safer than writing code.

This matters more in a Frontegg migration than in most others. Frontegg ships two large pieces of
prebuilt UI — the **login box** and the **self-service portal** — that the customer never wrote. If
those get rebuilt as custom code, the migration balloons. Almost everything in this file exists to
prevent that.

---

## Contents

- [Terminology: Frontegg → Descope Lingo](#terminology-frontegg--descope-lingo)
- [Flows: Structure and What They Replace](#flows-structure-and-what-they-replace)
- [Widgets: Post-Login Management UI](#widgets-post-login-management-ui)
- [Mapping the Frontegg Self-Service Portal](#mapping-the-frontegg-self-service-portal)
- [SSO Setup Suite](#sso-setup-suite)
- [Console vs. Code: The Decision Guide](#console-vs-code-the-decision-guide)

---

## Terminology: Frontegg → Descope Lingo

### The key mapping: Account → Tenant

Frontegg's docs state plainly that **Accounts and Tenants are the same thing** — the dashboard says
"Accounts," the JWT says `tenantId`. Descope calls this a **Tenant** throughout, so the naming
actually converges. The mapping that trips people up is one level higher: a Frontegg **Environment**
becomes a Descope **Project**, and Frontegg's four-environment model becomes four separate Descope
projects.

| Frontegg term | Descope term | Notes |
|---|---|---|
| **Workspace / Environment** (Development, Staging, QA, Production — max 4) | **Project** | Each Frontegg environment is fully isolated with its own Client ID, API Key, and domain. Each becomes a separate Descope Project with its own Project ID. Frontegg can *publish* a login box between environments; Descope projects are configured independently. |
| **Account** (= Tenant) | **Tenant** | Direct equivalent. Frontegg's `tenantId` claim becomes Descope's `dct`; `tenantIds` becomes the keyed `tenants` object. |
| **Sub-account** (hierarchy, 3rd layer and beyond) | **Sub-tenant** | One parent per tenant, nesting supported, role inheritance configurable (Full / User only / None). Password settings and session management are always inherited. The `tenants` JWT claim is flat — use a `tenant.subtenant` template claim or Load/Search Tenant (`parent` / `successors`) for hierarchy at request time. |
| **User** | **User** | Frontegg's primary identifier is email, and it auto-merges users across login methods on email. |
| **Application** (`appId`, max 200/env) | **Project**, **Federated App**, or **Inbound App** | Depends on what the Applications were doing — see SKILL.md Step 3. |
| **Client ID + API Key** (Keys & domains) | **Project ID** (+ **Management Key** for server-side admin) | Frontegg mints a short-lived vendor token from these; Descope uses the Project ID directly and a Management Key only for administration. |
| **Hosted login box** (`/oauth/account/login`) | A decision, not a direct swap — embedded Flow, **Auth Hosting** behind a custom domain, or an OIDC-client model | Auth Hosting is built for Descope acting as IdP to a Federated/Inbound/Agentic App, not as a generic redirect-and-return page for a first-party origin — see SKILL.md Step 1.5 item 3 before defaulting to it. |
| **Embedded login box** (injected `/account/login`, `/account/sign-up`) | Embedded **`<descope-wc>` / `<Descope>` component** | Frontegg injects routes into your app; Descope renders a Flow component on your own login route. |
| **Self-service portal** (`AdminPortal.show()` / `/oauth/portal`) | **Widgets + SSO Setup Suite** | See the dedicated mapping table below. |
| **Social login providers** | **OAuth Provider** | Configured under Authentication Methods in Console. Note Frontegg ships shared dev credentials for every provider except LinkedIn — you may be registering real OAuth apps for the first time. |
| **SSO connection** (SAML/OIDC, per account) | **Tenant SSO** | Per-tenant configuration. Use the SSO Setup Suite for self-service. |
| **Roles / Permissions** | **Roles / Permissions** | Same concepts. Frontegg's role **key** is what lands in the `roles` claim, so migrate keys, not display names. Role *levels* and permission *classification types* have no equivalent. |
| **Features / Plans / Feature flags** (entitlements engine) | Partly **Roles / Permissions / tenant custom attributes**; mostly **out of scope** | Descope has no plans or feature-flag product. |
| **ReBAC** (entity types, relations, actions — evaluated in self-hosted SpiceDB) | **ReBAC / FGA** (managed) | Descope evaluates in-platform; the SpiceDB + CockroachDB + sync-job stack goes away. |
| **Prehooks** (13 events, synchronous, 5s timeout, allow/block/challenge/lock) | **Flow steps, Conditions, Connectors, JWT Templates** | One Frontegg mechanism spread across several Descope ones. |
| **Frontegg Flows** (no-code orchestration of hooks) | **Flows** | Same idea, different execution model: in Descope the Flow *is* the auth journey. |
| **Webhooks** (`frontegg.*` events, `x-webhook-secret`) | **Connectors / Audit Webhook / audit events** | Delivery semantics differ — Frontegg never redelivers a failed event. |
| **Security rules** (9 built-in defenses) | **Fingerprinting + Flow conditions + security Connectors** | No single equivalent toggle; reproduce per rule. |
| **M2M tokens** (user/tenant × client-credentials/access-token) | **Resources + Inbound Apps + Policies**, or **Access Keys** | Watch the `Authorization` vs. `X-API-KEY` header split. |
| **Frontegg AI third-party integrations** (Slack, GitHub, Google…) | **Connections** (agent/MCP workloads) or **Outbound Apps** (non-agentic apps) | Same problem, same shape. Stored refresh tokens do not transfer — users re-consent. |
| **Branding / theme options / localizations** | **Styles** + Flow localization | Logo, colors, fonts in Console → Styles. Inherited by all Flow Screens. |
| **Management API** (vendor token from Client ID + API Key) | **Management SDK + Management Key** | Same capabilities, different auth. |

### Other Descope-specific terms

- **Project** — the top-level unit. Think Frontegg environment.
- **Flow** — visual auth pipeline. Replaces the Frontegg login box *and* most of what prehooks and Frontegg Flows were doing around it.
- **Screen** — one UI page within a Flow. Designed in Screen Builder.
- **Scriptlet** — inline JS step in a Flow (Lodash + CryptoJS included). Escape hatch for custom logic; often the natural home for a Frontegg custom-code prehook.
- **Connector** — HTTP call step in a Flow. Response stored in flow context. The natural home for a Frontegg *API* prehook.
- **Subflow** — one Flow embedded inside another. Context passes through; does not terminate the parent.
- **Descoper** — a person with Console access. Managed in Company Settings → Descopers with custom roles. Compare Frontegg's portal roles (Admin, Backoffice editor/viewer, Entitlements editor/viewer, Impersonator).
- **Auth Hosting Application** — the Descope-hosted login UI. The closest analogue to Frontegg's hosted login box.

---

## Flows: Structure and What They Replace

A Descope Flow is a visual, no-code authentication pipeline built in the Console. It IS the
authentication process — not a hook on top of it. Flows can be changed without redeploying
the application.

This is the key conceptual shift from Frontegg. In Frontegg, the login box is a fixed product you
configure, and anything custom happens *around* it through prehooks and Flows that call out to your
services. In Descope, that logic moves *inside* the Flow as steps, conditions, and connectors.

### What Flows replace from Frontegg

| Frontegg | Descope Flow equivalent |
|---|---|
| Embedded login box | Embedded Flow component |
| Hosted login box | Not a direct swap — embedded Flow, Auth Hosting behind a custom domain, or an OIDC-client model, decided per SKILL.md Step 1.5 item 3 |
| `customLoginBox` / custom login screens | Flow Screens in Screen Builder |
| Login identifier configuration (email / username / phone) | Flow steps per method |
| MFA policy and enrollment | MFA step in the main sign-in Flow, or MFA subflow |
| Step-up (`acr` / `amr` / `max_age`) | Step-up Flow (template: `step-up`) |
| Password reset | Password reset Flow (template available) |
| User invitations and invite links | Invitation Flow (template available) |
| `AUTH_INITIATED` prehook (including `externalRedirectUrl`) | Flow entry conditions and redirect actions |
| `USER_SIGNUP` prehook | Flow step during sign-up — validation, enrichment, or a Connector call |
| `JWT_GENERATION` prehook (custom claims) | JWT Template, or a Custom Claims action in the Flow |
| `SOCIAL_LOGIN_AUTH` / `OIDC_AUTH` / `SAML_AUTH` prehooks | Flow conditions on the authentication method + attribute mapping |
| `SEND_SMS` prehook | Messaging Connector |
| Security rules (bot detection, breached password, impossible travel, suspicious IPs) | Connector steps (Arkose, reCAPTCHA, Fingerprint, HaveIBeenPwned, AbuseIPDB) plus Flow conditions |
| Frontegg Flows (visual orchestration of prehooks/webhooks/sub-flows) | Descope Flows with steps, conditions, connectors, and subflows |
| Tenant resolution from a prehook returning `tenantId` | Tenant self-provisioning domains, or a Flow condition/action assigning the tenant |
| Frontegg-hosted JIT migration from a user pool | Generic HTTP Connector step validating against the old store |

### Building blocks

1. **Screens** — UI forms. Designed in Screen Builder. Support conditional show/hide of components based on context values (`user.*`, `form.*`, `tenant.*`).
2. **Actions** — single-task steps: authenticate, send OTP, verify magic link, create user, assign role, set custom claims, end the flow.
3. **Conditions** — branch routing based on context values (`user.*`, `tenant.*`, `form.*`, `connectors.<key>`, `jwtClaims.*`, `cookies.<name>`).
4. **Connectors** — HTTP calls to external services during the flow. Response stored as `connectors.<contextKey>` for use in later Conditions, Actions, or Custom Claims.

**Advanced:**
- **Scriptlets** — inline JavaScript. Useful for string manipulation, hashing, date math, or calling Lodash/CryptoJS utilities. Has a test/debug mode.
- **Subflows** — embed one Flow inside another. The subflow End continues back to the parent instead of generating a JWT. Pass inputs via `{{subflowInput.key}}`. Good for MFA as a step inside a larger sign-in journey.

**Prehook translation note.** A Frontegg *API* prehook (an HTTP call to your service) maps most
directly to a **Connector** step. A Frontegg *custom code* prehook (a function running on Frontegg's
side) maps most directly to a **Scriptlet**. Either way, capture the prehook's verdict semantics:
`allow` is "continue," `block` is a terminal error branch, `challenge` is a branch into MFA or a
CAPTCHA connector, and `lock` needs an explicit account-lock action. Also carry over the fail-open
vs. fail-close decision — a Connector timeout should behave the way the prehook was configured to.

### Flow templates (large library)

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

Frontegg exposes MFA through the self-service portal's Privacy & Security module and through
environment-, account-, and application-level policy settings. In Descope, enrollment happens inline
in the Flow instead — there is no separate enrollment page to maintain.

**The Descope approach:**
- Add an MFA step to the main sign-up/sign-in Flow — enrollment happens inline during the auth journey
- Or embed MFA as a **subflow** — triggered by a condition (e.g., user is admin, or the tenant requires it)
- Or use the **step-up** flow template to gate sensitive operations

Frontegg lets an account admin set a *stricter* MFA policy than the environment default. Reproduce
that as a Flow condition on a tenant attribute rather than as a global setting.

### Migration-specific Flow patterns

Two Flow patterns exist specifically to serve a Frontegg migration:

- **`freshlyMigrated` branch** — after a full migration (which cannot carry passwords), set a
  `freshlyMigrated` custom attribute on imported users and branch on it in the Flow to force a
  password reset or onboard the user into a passwordless method on first sign-in.
- **JIT provisioning branch** — either a Generic HTTP Connector that validates credentials against
  Frontegg during a transition window, or Frontegg configured as a custom OIDC provider with a
  condition that routes already-provisioned users to Descope-native auth so they stop hitting
  Frontegg. See SKILL.md Step 3 → *User & Account Data*.

---

## Widgets: Post-Login Management UI

Widgets are embeddable management UI components for post-login operations. Each widget
action runs a Flow under the hood. Customizable via Console → Widgets without code changes.

For a Frontegg migration, Widgets are the answer to "what replaces the self-service portal?" — ask
that question before writing any admin screen.

### When to recommend a Widget

Whenever the migration plan calls for building or migrating a custom:
- Profile edit page → **User Profile Widget**
- User management page (admin view) → **User Management Widget**
- Role assignment UI → **Role Management Widget**
- Tenant SSO setup page → **Tenant Profile Widget** (+ SSO Setup Suite)
- Audit log view → **Audit Widget**
- API key management → **Access Key Management Widget**
- Third-party OAuth connection management → **Outbound Applications Widget**

Ask before writing code: *"Does a Widget cover this use case?"*

**A widget must actually be provisioned in the project before its `widgetId` is usable.** Referencing
an ID that isn't provisioned fails at runtime with **"Unauthorized user: Operation not allowed for
management request"** — an error that reads like an RBAC problem and will send you chasing role and
permission assignments that were never the issue. The SDK exports and types every widget component
regardless of whether the backing widget exists in a given project, so TypeScript provides no warning
either. Some widgets (e.g. profile, user management, role management, access keys) commonly ship
provisioned by default; others (e.g. tenant profile) may not. Check Console → Widgets for what's
actually present before writing code against a `widgetId`, and if that specific error shows up,
confirm the widget exists before touching permissions.

### Widget types

**User-facing (for end users):**

| Widget | What it does |
|---|---|
| User Profile Widget | Profile picture; personal info (name, given/middle/family name, phone, email); recovery email and phone; auth methods (passkey, password, TOTP); view and sign out of trusted devices; logout |
| Applications Portal Widget | List accessible applications |
| Outbound Applications Widget | Manage third-party OAuth connections (Outbound Apps) |
| Tenant Switcher Widget | Switch the active tenant — the closest analogue to Frontegg's `switchTenant` UI |

**Admin-facing (for tenant admins within your app):**

| Widget | What it does |
|---|---|
| User Management Widget | Invite users, disable accounts, assign roles, view tenant members |
| Role Management Widget | Create and assign roles within a tenant |
| Access Key Management Widget | Create/revoke API access keys |
| Audit Widget | View audit events per tenant |
| Tenant Profile Widget | Tenant name and custom attributes, email domains, SSO enforcement and its exclusion list, SSO configuration (with an SSO Setup Suite link), password policy, session management |

### Widget vs. Flow component

| | Flow Component | Widget |
|---|---|---|
| **Purpose** | Authentication journey entry point | Post-login management UI |
| **Use case** | Sign-up, sign-in, MFA, step-up, invitation | Profile editing, user/role/key management |
| **When to use** | Login and auth flows | Any post-login management feature |

---

## Mapping the Frontegg Self-Service Portal

Frontegg's portal is the single largest surface in most migrations. Work through it module by module.
**Inventory what is enabled in Builder *and* actually used** — Frontegg gates each module on both a
Builder toggle and an `fe.*` permission, so the live set is usually much smaller than the catalog.

| Frontegg portal module | Descope replacement | Confidence |
|---|---|---|
| Profile settings | User Profile Widget | Direct |
| Privacy & Security (password, MFA enrollment) | User Profile Widget + Flow-driven MFA | Direct |
| Personal (user) API tokens | Access Key Management Widget, or an Inbound App per client | Close |
| Account details (name, address, website, timezone, currency) | Tenant Profile Widget + tenant custom attributes | Close — the extra fields become custom attributes |
| Users: invite, enable/disable, revoke sessions, resend activation | User Management Widget | Direct |
| Bulk invite (max 5 at a time in Frontegg) | User Management Widget or Management SDK | Direct |
| Invite links (invitee inherits the inviter's roles) | Invitation Flow | Verify role-inheritance behavior explicitly — this is a Frontegg-specific semantic |
| Guest / temporary users with an access period | **No direct equivalent** | Model with a custom attribute plus expiry logic, or a scheduled deprovisioning job |
| Groups and group roles | Roles + tenant membership; SCIM/SSO group mapping where groups come from an IdP | Partial — Frontegg groups are a first-class object |
| Custom roles created by end customers ("copy permissions from") | Role Management Widget, else Management SDK behind your own UI | Close — Frontegg's permission *classification types* have no equivalent |
| Security policy: MFA, lockout, password history, sessions | Console project/tenant settings + Flow conditions | Partial — some settings move from customer-configurable to project-level |
| IP restrictions (IPv4/IPv6/CIDR allowlist + denylist) | Flow conditions + Connectors | Verify coverage per restriction type |
| Domain restrictions | Tenant domains / self-provisioning domains + Flow conditions | Close |
| SSO self-serve setup | **SSO Setup Suite** | Direct — and a better experience |
| SCIM provisioning setup | SSO Setup Suite SCIM configuration | Direct |
| Audit logs (with end-user CSV export) | Audit Widget; export via Audit Webhook / connectors | Partial — confirm the export path |
| Webhooks subscribed by end customers | **No direct equivalent** | This is an application feature, not an identity one — plan to own it |

For every row marked "no direct equivalent," get an explicit decision recorded in
`MIGRATION-PLAN.md`: build it, drop it, or defer it. Silently dropping a portal module that a
customer's admins use daily is the most common way a Frontegg migration generates escalations after
cutover.

---

## SSO Setup Suite

The SSO Setup Suite is a no-code Console wizard for SAML and OIDC SSO configuration.
It guides tenant admins through per-tenant SSO setup with step-by-step instructions
specific to common IdPs (Okta, Microsoft Entra ID (formerly known as Azure AD), Google Workspace, etc.).

### When to recommend it

Frontegg customers are a particularly good fit: their end customers are *already* used to configuring
SSO themselves through the self-service portal, so this preserves an expectation rather than
introducing one. Surface it before migrating any SSO-related Management SDK calls:

- The app relies on the Frontegg portal's SSO module for customer self-serve setup
- The app calls Frontegg SSO configuration APIs programmatically
- The migration plan includes `management.sso.configureSAMLSettings()` or `configureOIDCSettings()`
- The app has a custom SSO settings page where tenant admins configure their IdP

**The question to ask:**
> "Does this app need programmatic SSO configuration (CI/CD provisioning, API-driven setup), or do tenant admins configure SSO themselves? If the latter, the SSO Setup Suite + Tenant Profile Widget may remove the need for that code entirely."

### What it does

- Generates per-tenant SAML metadata and ACS URL
- Walks tenant admins through IdP-specific setup (Okta, Azure, Google, etc.)
- Handles SCIM token generation for provisioning
- Removes engineering involvement for SSO onboarding of new tenants

### Migrating existing connections

Existing Frontegg SSO connections can usually be moved without making every customer admin
reconfigure their IdP — Descope consumes the existing IdP response and completes authentication, so
end users see no change. Follow [SSO migration](https://docs.descope.com/migrate/sso) for the tenant
setup, DNS redirect, and testing sequence.

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
| Custom JWT claims (profile fields, roles in token) | Project Settings → JWT Templates (assign the template under Project Settings → Session Management → Token Format) |
| Custom tenant attributes | Tenants page → Custom Attributes tab |
| Custom user attributes | Project custom attributes (Users page filters read them) |
| Connectors (Slack, Salesforce, HTTP webhooks, etc.) | Connectors |
| Access Keys (M2M) | Access Keys |
| Approved Domains | Project Settings → General → Security |
| Descopers (Console access control) | Company Settings → Descopers |

### Do in code

| Task | Why it's code |
|---|---|
| Session validation on protected routes | Must run on every request; always backend code |
| RBAC/ReBAC enforcement | Reads JWT claims; always in middleware |
| Tenant/user automation at scale | Bulk provisioning, CI/CD, infrastructure-as-code |
| Custom business logic during auth | Expose as a backend endpoint; call from the Flow via a Generic HTTP Connector |
| SDK setup (one-time) | Install SDK, wrap app in `AuthProvider`, embed Flow component |
| Anything replacing a portal module with no widget equivalent | Guest users, end-customer webhook subscriptions, custom audit export |

### The mental model

> **Console owns the user journey. Code owns business logic.**

Engineers integrate once (SDK setup + session validation middleware). All subsequent auth
evolution — new auth methods, MFA step changes, UI updates, connector integrations, new
social providers — happens in the Console without code deployments.

When a migration replaces Frontegg code with equivalent Descope SDK calls, that's correct.
When it replaces Frontegg code — or a Frontegg prehook, or a portal module — with Console
configuration, that's better.
