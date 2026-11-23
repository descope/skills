# Descope Flows, Widgets, and Console-First Reference

This file covers Descope's no-code/low-code layer — Flows, Widgets, the SSO Setup Suite, and
the Console-vs-code decision guide. Read it when the migration touches auth UI, MFA enrollment,
user management pages, or SSO configuration. In all those areas, a Console/Flow/Widget approach
is usually faster and safer than writing code.

This matters in a FusionAuth migration for a specific reason. FusionAuth gives you **hosted login
pages you customize through FreeMarker themes**, and **lambdas** (small JavaScript functions FusionAuth
runs at fixed points) for anything the pages and settings can't do. Teams that invested in either
tend to assume the Descope equivalent is code. It usually isn't: themes become a Flow plus Styles, and
most lambdas become a Flow step, a JWT Template, or a Connector.

The other direction matters too. FusionAuth has no end-customer admin portal by default (the newer
**Tenant Manager** is the exception), so B2B apps on FusionAuth often built their own "manage my team"
and "configure SSO" screens against the FusionAuth API. Those custom screens are the biggest
opportunity in this migration to *remove* code: ask whether a Widget or the SSO Setup Suite replaces
each one before porting it.

---

## Contents

- [Terminology: FusionAuth → Descope Lingo](#terminology-fusionauth--descope-lingo)
- [Flows: Structure and What They Replace](#flows-structure-and-what-they-replace)
- [Widgets: Post-Login Management UI](#widgets-post-login-management-ui)
- [Mapping FusionAuth's Self-Service and Admin Surfaces](#mapping-fusionauths-self-service-and-admin-surfaces)
- [SSO Setup Suite](#sso-setup-suite)
- [Console vs. Code: The Decision Guide](#console-vs-code-the-decision-guide)

---

## Terminology: FusionAuth → Descope Lingo

### The key mapping: FusionAuth Tenant → Descope Project *or* Tenant

This is the mapping that trips people up, because the words match and the concepts don't.

A **FusionAuth tenant** is a hard isolation boundary: its own user pool (the same email can be two
unrelated users in two tenants), its own issuer, signing keys, password policy, email server, and
themes. A **Descope tenant** is a *grouping of users inside one project*: users are unique per project
and can belong to many tenants, each with its own roles, SSO, and settings.

So what a FusionAuth tenant becomes depends on what it was used for:

| How the FusionAuth tenant is used | Descope target |
|---|---|
| One tenant per **environment** (dev / staging / prod on one instance) | One Descope **Project** per environment |
| One tenant per **B2B customer** in a multi-tenant SaaS | One Descope **Tenant** per customer, in a single project |
| One tenant per **separate product or brand** with fully separate users | One Descope **Project** per product |
| Only the `Default` tenant | Nothing to map — one project, tenants only if the app has another customer concept |

When FusionAuth tenants become Descope tenants, users that existed separately in several FusionAuth
tenants under the same email become **one** Descope user with several tenant memberships. That merge
is a real decision (whose password, whose profile data) — see SKILL.md Step 4 → *Email uniqueness*.

| FusionAuth term | Descope term | Notes |
|---|---|---|
| **Instance / deployment** (self-hosted or FusionAuth Cloud) | **Company** (with one or more Projects) | There is no server to run with Descope. The FusionAuth database, search engine (Elasticsearch/OpenSearch), and app container go away. |
| **Tenant** | **Project** or **Tenant** | See the table above. Decide this first. |
| **Application** (`applicationId` = OAuth `client_id`) | **Project**, **Federated App**, **Inbound App**, or nothing | Depends on what the Applications represent — see SKILL.md Step 3 → *Applications*. Most single-product apps have one Application, which simply becomes the Descope Project. |
| **Registration** (user ↔ application, carries roles) | **Tenant membership + roles**, a role, or a custom attribute | Descope has no per-application registration. Decide what "registered for app X" meant to the app. |
| **Application roles** (defined per application) | **Roles** (project-wide, assigned project-level or per tenant) | Two applications can both define `admin`. Descope role names are project-wide — namespace or merge them deliberately. |
| **Group** (bundles application roles; users are members) | **Roles** assigned directly; SSO/SCIM group mapping where groups come from an IdP | Descope has no standalone group object for login users. Flatten group roles onto users at import, or map IdP groups to roles. |
| **User** (`id` UUID, unique within a tenant) | **User** (`loginId`, unique within the project) | Email and username are both login identifiers in FusionAuth; Descope supports one `loginId` plus additional login IDs. |
| **user.data** (free-form JSON) | **Custom attributes** | Define each attribute in the Console schema first. Nested JSON needs a flattening decision. |
| **Hosted login pages** + **Themes** (FreeMarker templates) | **Flows** + **Styles** | No template code to port; screens are built in the Flow editor. |
| **Email / message templates** (FreeMarker) | **Messaging Templates** | Rewrite the bodies; the variable syntax differs. |
| **Advanced Registration Forms** | Flow **Screens** + custom attributes | Multi-step registration becomes Flow screens. |
| **Lambdas** (JWT populate, reconcile, validation, …) | **JWT Templates**, Flow **Scriptlets**, **Connectors**, SSO attribute mapping | One mechanism spread across several Descope ones — see the Flows table below. |
| **Webhooks** (`user.create`, `user.login.success`, …) | **Audit Webhook** / **Connectors** / audit events | Transactional webhooks that can *block* an event become Flow steps instead. |
| **Identity Providers** (OIDC, SAML v2, Google, Apple, …) | **Tenant SSO** (enterprise) / **OAuth providers** (social) | Managed domains on an IdP map to tenant email domains. |
| **Connectors** (Generic, LDAP) — FusionAuth's own JIT-migration feature | **Generic HTTP Connector** in a Flow | If the app is *mid-migration into* FusionAuth through a connector, the real source of truth may be elsewhere. |
| **Entities, Entity Types, Grants** (Entity Management, M2M) | **Inbound Apps + Resources + Policies**, or **Access Keys**; FGA where grants model authorization | See SKILL.md Step 3 → *Entities and M2M*. |
| **API keys** | **Management Key** | FusionAuth API keys can be scoped to endpoints and a tenant; Descope Management Keys are scoped by project and can be limited by role. |
| **Self-service account management** (`/account` pages) | **User Profile Widget** | Profile, password, MFA, and passkey management. |
| **Tenant Manager** (tenant-admin UI) | **User Management Widget**, **Role Management Widget**, **Tenant Profile Widget**, **SSO Setup Suite** | Only if the deployment uses it. |
| **Consents** | Custom attributes + a Flow screen | No first-class consent object. |
| **Families** | **No equivalent** | Model with custom attributes or the application database. |
| **Kickstart** (`kickstart.json`) | **Descope Terraform provider** or a Management SDK script | Both describe configuration as code. |

### Other Descope-specific terms

- **Project** — the top-level unit. Think FusionAuth tenant used as an environment.
- **Flow** — visual auth pipeline. Replaces the FusionAuth hosted pages *and* most of what lambdas did around them.
- **Screen** — one UI page within a Flow. Designed in Screen Builder.
- **Scriptlet** — inline JS step in a Flow (Lodash + CryptoJS included). The natural home for a FusionAuth lambda that only transforms data.
- **Connector** — HTTP call step in a Flow. Response stored in flow context. The natural home for a lambda that calls out with `fetch` (FusionAuth's "lambda HTTP connect").
- **Subflow** — one Flow embedded inside another. Context passes through; does not terminate the parent.
- **Descoper** — a person with Console access. Managed in Company Settings → Descopers with custom roles. Compare FusionAuth admin-app users with `fusionauth-app` roles (`admin`, `user_manager`, …).
- **Auth Hosting Application** — the Descope-hosted login UI. The closest analogue to FusionAuth's hosted login pages.

---

## Flows: Structure and What They Replace

A Descope Flow is a visual, no-code authentication pipeline built in the Console. It IS the
authentication process — not a hook on top of it. Flows can be changed without redeploying
the application.

This is the key conceptual shift from FusionAuth. In FusionAuth, the login pages are a fixed
sequence you configure through tenant and application settings and restyle with a theme; anything
custom happens *around* that sequence in lambdas and webhooks. In Descope, the sequence itself is
yours to edit, and the custom logic moves *inside* it as steps, conditions, and connectors.

### What Flows replace from FusionAuth

| FusionAuth | Descope Flow equivalent |
|---|---|
| Hosted login page (`/oauth2/authorize`) | Descope-hosted login via the SDK's `oidcConfig` (or any OIDC client pointed at Descope) — the Flow runs on the hosted page |
| Themes (FreeMarker templates, `theme.css`) | Flow Screens in Screen Builder + **Styles** |
| Self-service registration (basic or advanced forms) | Sign-up Flow with Screens; extra fields become custom attributes |
| Self-service registration **validation lambda** | Scriptlet or Connector step plus a Condition, before user creation |
| Login identifier settings (email / username / phone) | Flow steps per method; `loginId` configuration |
| MFA (TOTP, email, SMS) policy and enrollment | MFA step in the main sign-in Flow, or an MFA subflow |
| **Login validation lambda** (Enterprise) | Condition or Connector step after authentication, with a deny branch |
| **JWT populate** / **Id Token populate** / **UserInfo populate** lambdas | JWT Template, or a Custom Claims action in the Flow |
| **Reconcile lambdas** (OIDC, SAML v2, social IdPs) | SSO attribute mapping, OAuth attribute mapping, or a Flow step after the IdP returns |
| Passwordless (magic link `/oauth2/passwordless`) | Magic Link / Enchanted Link / OTP Flow |
| WebAuthn / passkeys (bootstrap and re-authentication) | Passkey steps in the Flow |
| Forgot / change password pages | Password reset Flow (template available) |
| Email verification and registration verification | Verification steps in the sign-up Flow |
| Breached password detection | Password step with a breached-password check (confirm the current option in docs) |
| Advanced Threat Detection (rate limits, CAPTCHA, impossible travel, IP access control lists) | Connector steps (reCAPTCHA, Arkose, Fingerprint, AbuseIPDB) plus Flow conditions |
| Consent collection on registration | A Screen with a checkbox, stored in a custom attribute |
| Generic / LDAP **Connector** (JIT migration *into* FusionAuth) | Generic HTTP Connector step validating against the old store |
| `idp_hint` / managed domains routing a user to their IdP | Tenant email domains + SSO routing in the Flow |

### Building blocks

1. **Screens** — UI forms. Designed in Screen Builder. Support conditional show/hide of components based on context values (`user.*`, `form.*`, `tenant.*`).
2. **Actions** — single-task steps: authenticate, send OTP, verify magic link, create user, assign role, set custom claims, end the flow.
3. **Conditions** — branch routing based on context values (`user.*`, `tenant.*`, `form.*`, `connectors.<key>`, `jwtClaims.*`, `cookies.<name>`).
4. **Connectors** — HTTP calls to external services during the flow. Response stored as `connectors.<contextKey>` for use in later Conditions, Actions, or Custom Claims.

**Advanced:**
- **Scriptlets** — inline JavaScript. Useful for string manipulation, hashing, date math, or calling Lodash/CryptoJS utilities. Has a test/debug mode.
- **Subflows** — embed one Flow inside another. The subflow End continues back to the parent instead of generating a JWT. Pass inputs via `{{subflowInput.key}}`. Good for MFA as a step inside a larger sign-in journey.

**Lambda translation note.** A FusionAuth lambda that only reshapes data (adds claims, copies
attributes from an IdP response) maps to a **JWT Template**, an attribute mapping, or a **Scriptlet**.
A lambda that calls out with `fetch` maps to a **Connector** step. A lambda that rejects the event
(a login validation lambda returning an error, a registration validation lambda adding field errors)
maps to a **Condition** with a deny branch. Capture what happens on timeout or error: a FusionAuth
lambda that throws fails the event, so the matching Connector should fail closed unless the user says
otherwise.

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

FusionAuth lets users enroll MFA on the self-service `/account` pages, and admins require it through
the tenant's MFA policy or an application's login policy. In Descope, enrollment happens inline in the
Flow instead — there is no separate enrollment page to maintain.

**The Descope approach:**
- Add an MFA step to the main sign-up/sign-in Flow — enrollment happens inline during the auth journey
- Or embed MFA as a **subflow** — triggered by a condition (e.g., user is admin, or the tenant requires it)
- Or use the **step-up** flow template to gate sensitive operations

A FusionAuth application can set a stricter MFA policy than its tenant. Reproduce that as a Flow
condition (on a tenant attribute, or on which app started the flow) rather than as a global setting.

### Migration-specific Flow patterns

Two Flow patterns exist specifically to serve a FusionAuth migration:

- **`freshlyMigrated` branch** — when users are imported *without* their password hashes (FusionAuth
  Cloud without a database export, or an unsupported hash scheme), set a `freshlyMigrated` custom
  attribute on imported users and branch on it in the Flow: verify the password against FusionAuth
  through the JIT connector while FusionAuth is still on, or force a password reset / passwordless
  onboarding after it is off.
- **JIT provisioning branch** — either a Generic HTTP Connector that validates credentials against
  FusionAuth's Login API during a transition window, or FusionAuth configured as a custom OIDC provider
  with a condition that routes already-provisioned users to Descope-native auth so they stop hitting
  FusionAuth. See SKILL.md Step 3 → *User & Tenant Data*.

When hashes *are* imported, neither branch is needed: imported users sign in with their existing
password on day one.

---

## Widgets: Post-Login Management UI

Widgets are embeddable management UI components for post-login operations. Each widget
action runs a Flow under the hood. Customizable via Console → Widgets without code changes.

For a FusionAuth migration, Widgets answer two questions: "what replaces the `/account` self-service
pages?" and "what replaces the team-management and SSO screens we built ourselves against the
FusionAuth API?" Ask both before writing any admin screen.

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
| Tenant Switcher Widget | Switch the active tenant |

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

## Mapping FusionAuth's Self-Service and Admin Surfaces

Work through each surface the app actually exposes to its users. **Inventory what is in use**, not
what FusionAuth offers: self-service account management and Tenant Manager are both opt-in, and many
apps link to neither.

| FusionAuth surface | Descope replacement | Confidence |
|---|---|---|
| `/account` — profile edit | User Profile Widget | Direct |
| `/account` — change password | User Profile Widget, or the password reset Flow | Direct |
| `/account` — TOTP / email / SMS MFA enrollment | User Profile Widget + Flow-driven MFA | Direct |
| `/account` — passkey management | User Profile Widget | Direct |
| Tenant Manager — users (add, edit, lock, delete) | User Management Widget | Direct |
| Tenant Manager — identity providers per tenant | SSO Setup Suite + Tenant Profile Widget | Direct, and a better self-serve experience |
| App-built "my team" page calling `/api/user`, `/api/user/registration` | User Management Widget | Close — confirm the role model first |
| App-built role assignment calling `/api/user/registration` with `roles` | Role Management Widget or User Management Widget | Close |
| App-built group management calling `/api/group/member` | Roles + Role Management Widget | Partial — Descope has no groups for login users |
| App-built SSO setup screen calling `/api/identity-provider` | **SSO Setup Suite** | Direct |
| App-built API-key screen (Entity Management client credentials) | Access Key Management Widget, or Inbound Apps | Close |
| App-built audit view reading `/api/system/audit-log` or `/api/system/event-log` | Audit Widget | Partial — FusionAuth's audit log records admin actions; confirm what the screen actually shows |
| Consents management | **No direct equivalent** | Custom attributes plus an app screen |
| Family management (parental consent) | **No direct equivalent** | Plan to own it in the application |

For every row marked "no direct equivalent," get an explicit decision recorded in
`MIGRATION-PLAN.md`: build it, drop it, or defer it.

---

## SSO Setup Suite

The SSO Setup Suite is a Descope-hosted, no-code self-service setup flow for SAML and OIDC SSO
configuration — tenant admins open it via a link generated per tenant, not through the Descope
Console. It guides them through per-tenant SSO setup with step-by-step instructions
specific to common IdPs (Okta, Microsoft Entra ID (formerly known as Azure AD), Google Workspace, etc.).

### When to recommend it

FusionAuth configures enterprise IdPs centrally (an admin creates an Identity Provider, enables it per
application, and sets managed domains or tenant restrictions). B2B apps that onboard many customers
therefore often built a script or admin screen around `/api/identity-provider`. Surface the SSO Setup
Suite before migrating any of that:

- The app creates or updates FusionAuth Identity Providers programmatically
- Each customer's SAML/OIDC IdP is a separate FusionAuth Identity Provider, scoped by managed domain or tenant
- The migration plan includes `management.sso.configureSAMLSettings()` or `configureOIDCSettings()`
- The app has a custom SSO settings page where tenant admins configure their IdP
- The deployment uses Tenant Manager to let tenant admins configure IdPs

**The question to ask:**
> "Does this app need programmatic SSO configuration (CI/CD provisioning, API-driven setup), or do tenant admins configure SSO themselves? If the latter, the SSO Setup Suite + Tenant Profile Widget may remove the need for that code entirely."

### What it does

- Generates per-tenant SAML metadata and ACS URL
- Walks tenant admins through IdP-specific setup (Okta, Azure, Google, etc.)
- Handles SCIM token generation for provisioning
- Removes engineering involvement for SSO onboarding of new tenants

### Migrating existing connections

Existing FusionAuth SAML and OIDC Identity Providers can usually be moved without making every
customer admin reconfigure their IdP — Descope consumes the existing IdP response and completes
authentication, so end users see no change. Follow [SSO migration](https://docs.descope.com/migrate/sso)
for the tenant setup, DNS redirect, and testing sequence. Export each Identity Provider's settings
(`GET /api/identity-provider`) first: it holds the IdP entity ID, SSO URL, certificate key ID, and
the claim mappings the reconcile lambda relied on.

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
| Anything with no widget equivalent | Consents, families, end-customer webhook subscriptions |

### The mental model

> **Console owns the user journey. Code owns business logic.**

Engineers integrate once (SDK setup + session validation middleware). All subsequent auth
evolution — new auth methods, MFA step changes, UI updates, connector integrations, new
social providers — happens in the Console without code deployments.

When a migration replaces FusionAuth code with equivalent Descope SDK calls, that's correct.
When it replaces FusionAuth code — or a lambda, a FreeMarker theme, or an app-built admin screen —
with Console configuration, that's better.
