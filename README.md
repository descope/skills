# Descope Skills

A collection of AI agent skills for integrating Descope authentication into your applications. Skills follow the [Agent Skills](https://agentskills.io/) format and work with any compatible AI coding assistant.

## Available Skills

<details>
<summary><b>descope-auth</b> — Integrate Descope authentication into applications</summary>

Integrate Descope authentication into applications with support for passwordless auth, OAuth, SSO, and MFA. Uses a smart router pattern to detect your framework and provide targeted integration guidance.

**Use when:**
- "Add authentication to my app"
- "Implement login with Descope"
- "Set up passwordless auth"
- "Add OAuth/SSO to my application"
- "Integrate passkeys"

**Frameworks supported:**
- Next.js (App Router with middleware)
- React (SPA with protected routes)
- Node.js (backend session validation)
- Python (backend session validation)

**Features:**
- **Framework detection** - Automatically routes to appropriate integration guide
- **Security guardrails** - Prevents common authentication mistakes
- **Skills.sh compliant** - Follows official specification
- **Copy-paste ready** - All code examples use correct SDK imports

**Authentication methods covered:**
- OTP (Email/SMS) - Quick verification codes
- Magic Link - Passwordless email links
- Passkeys - Biometric/WebAuthn (most secure)
- OAuth - Social login (Google, GitHub, etc.)
- SSO - Enterprise SAML/OIDC
- TOTP - Authenticator app MFA
- Passwords - Traditional auth (fallback)

</details>

<details>
<summary><b>auth-review</b> — Static security review for authentication and authorization vulnerabilities</summary>

Framework- and vendor-agnostic static review that enumerates every route/endpoint in a codebase, builds an authorization matrix, applies a vulnerability catalog (OWASP Web + API Top 10 identity categories), and writes a triage report ready to slice into GitHub issues or PRs.

**Use when:**
- "/auth-review"
- "Audit authentication in my app"
- "Find authorization bugs / IDOR / BOLA"
- "Review access control"
- "Identity security review before release"

**Covers:**
- Broken authentication (missing auth, weak password handling, SQLi-in-login, enumeration)
- JWT / token flaws (`alg:none`, algorithm confusion, unverified decode, missing claim validation)
- Session management (cookie flags, fixation, logout invalidation, predictable IDs)
- Broken access control (IDOR / BOLA, BFLA, tenant crossing, client-trusted input)
- Privilege escalation & mass assignment
- OAuth / OIDC / SAML (state/PKCE, open redirect, ID-token validation, SAML XSW)
- Password reset & account recovery (predictable/non-expiring tokens, host poisoning, MFA bypass)
- MFA bypass and step-up gaps
- Rate limiting & enumeration on auth surfaces
- CSRF, CORS, identity-adjacent SSRF

**Output:**
- Triage report in `./auth-review/report-YYYY-MM-DD.md`
- Endpoint inventory and authorization matrix
- Findings with severity (High/Medium/Low), CWE, `file:line`, evidence, remediation
- Pre-formatted issue bodies ready to paste into GitHub

**Scope:** static and read-only. Does not run the target application, make network probes, modify code, or file issues directly.

</details>

<details>
<summary><b>descope-terraform</b> — Manage Descope projects as infrastructure-as-code</summary>

Manage Descope projects as infrastructure-as-code using the official [Terraform provider](https://registry.terraform.io/providers/descope/descope/latest/docs). Generates valid HCL configurations for authentication methods, RBAC, connectors, and project settings.

**Use when:**
- "Set up Terraform for my Descope project"
- "Manage Descope authentication config as code"
- "Create roles and permissions with Terraform"
- "Add connectors to my Descope Terraform config"
- "Deploy Descope project settings across environments"

**Resources managed:**
- `descope_project` - Full project configuration (auth methods, RBAC, connectors, flows, settings)
- `descope_management_key` - Management keys with RBAC scoping
- `descope_descoper` - Console user accounts with role assignments

**Covers:**
- Provider setup and management key configuration
- Authentication methods (OTP, Magic Link, Passkeys, OAuth, SSO, Password, TOTP)
- Authorization (roles and permissions)
- 60+ connector types (email, SMS, HTTP, observability, fraud detection, CRM, etc.)
- Project settings, applications (OIDC/SAML), flows, JWT templates, and custom attributes

**Requirements:**
- Terraform CLI installed
- Paid Descope License (Pro +)
- Management Key from [Company Settings](https://app.descope.com/company)

</details>

<details>
<summary><b>auth0-to-descope</b> — Migrate applications from Auth0 to Descope</summary>

Guides self-service migrations from Auth0 to Descope across any language or framework. Analyzes auth touchpoints, produces a reviewed `MIGRATION-PLAN.md`, then executes the migration. Uses the Descope Docs MCP when available to verify SDK method names and option shapes.

**Use when:**
- "Migrate my app from Auth0 to Descope"
- "Replace Auth0 with Descope"
- "Our app uses nextjs-auth0 / express-openid-connect / auth0-fastapi — switch to Descope"
- "How do Auth0 Actions / Organizations / Token Vault map to Descope?"
- "We're moving off Auth0"

**Covers:**
- SDK replacement for all major frameworks (Next.js, React, Express, Python, etc.)
- Auth0 feature mappings: Actions → Descope flows, Organizations → Tenants, Token Vault, CIBA
- Descope Flow and Widget setup (console-first approach)
- SSO and OIDC compatibility
- Session validation patterns

**Output:**
- `MIGRATION-PLAN.md` for human review before any code changes
- SDK replacement across all auth touchpoints in the codebase
- Descope Flow and Widget integration

**Workflow:** MCP check → migration plan (human review) → execution. Never skips ahead.

</details>

<details>
<summary><b>okta-cis-to-descope</b> — Migrate applications from Okta CIS to Descope</summary>

Guides self-service migrations from Okta Customer Identity Service (CIS) to Descope across any language or framework. Detects whether the app uses hosted/redirect login or an embedded widget and defaults to the appropriate migration path. Analyzes auth touchpoints, produces a reviewed `MIGRATION-PLAN.md`, then executes the migration. Uses the Descope Docs MCP when available to verify SDK method names and option shapes.

**Use when:**
- "Migrate my app from Okta to Descope"
- "Replace Okta CIS with Descope"
- "Our app uses okta-auth-js / @okta/okta-react / @okta/oidc-middleware / okta-jwt-verifier — switch to Descope"
- "How do Okta Sign-On Policies / Authorization Servers / Authenticators / Log Streams map to Descope?"
- "We're moving off Okta"

**Covers:**
- SDK replacement for all major frameworks (React, Angular, Vue, Next.js, Express, Python, Java, and more)
- OIDC compatibility path for hosted/redirect login (swap issuer config, keep redirect flow intact)
- Okta CIS feature mappings: Sign-On Policies → Flows, Authorization Servers → Resources/Inbound Apps, Authenticators → Auth Methods, Identity Providers → Tenant SSO, Log Streams → Audit Connectors
- Inbound Apps vs. Federated Apps decision (scope-enforcing vs. identity-only)
- `scp` → `scope` claim migration
- Session validation patterns and dual-token validation for phased rollouts

**Output:**
- `MIGRATION-PLAN.md` for human review before any code changes
- SDK replacement across all auth touchpoints in the codebase
- Descope Flow and Console configuration guidance

**Workflow:** MCP check → migration plan (human review) → execution. Never skips ahead.

</details>

<details>
<summary><b>workos-to-descope</b> — Migrate applications from WorkOS to Descope</summary>

Guides self-service migrations from WorkOS to Descope across any language or framework. WorkOS is a B2B/enterprise-readiness platform — not just auth — so the skill first identifies which WorkOS features are in use, maps each to Descope, analyzes auth touchpoints, produces a reviewed `MIGRATION-PLAN.md`, then executes the migration. Uses the Descope Docs MCP when available to verify SDK method names and option shapes.

**Use when:**
- "Migrate my app from WorkOS to Descope"
- "Replace WorkOS with Descope"
- "Our app uses @workos-inc/node / @workos-inc/authkit-nextjs / AuthKit — switch to Descope"
- "How do WorkOS Organizations / Enterprise SSO / Directory Sync / Admin Portal map to Descope?"
- "We're moving off WorkOS"

**Covers:**
- SDK replacement for all major frameworks (Next.js, React, Express, Python, Go, Ruby, etc.)
- WorkOS feature mappings: AuthKit → Descope Flows, Organizations → Tenants, Enterprise SSO → Tenant SSO, Directory Sync/SCIM → Descope SCIM, Admin Portal → SSO Setup Suite / Widgets, RBAC, FGA → ReBAC/AuthZ, Audit Logs, Radar, Pipes → Outbound Apps
- Tenant routing / home realm discovery (domain-based vs. explicit tenant slug)
- Descope Flow, Widget, and SSO Setup Suite setup (console-first approach)
- OIDC compatibility path for incremental migration
- Session validation patterns and WorkOS-specific gotchas (JWT claims, sealed sessions, SCIM lifecycle)

**Output:**
- `MIGRATION-PLAN.md` for human review before any code changes
- SDK replacement across all auth touchpoints in the codebase
- Descope Flow, Widget, and Console configuration guidance

**Workflow:** MCP check → migration plan (human review) → execution. Never skips ahead.

</details>


<details>
<summary><b>descope-fga-schema</b> — Author and apply Descope FGA authorization schemas</summary>

Author, edit, and apply Descope FGA schemas using the ReBAC/ABAC DSL. Validates changes via dry run before applying, warns on data loss, and requires user confirmation before modifying live schema. Requires the Descope Management MCP.

**Use when:**
- "/descope-fga-schema"
- "Set up authorization / define roles and permissions"
- "Add team-based access control"
- "Create a new FGA schema"
- "Update my authorization model"
- "Add types/relations/permissions/conditions to my schema"

**Covers:**
- Full DSL grammar (`model AuthZ 1.0`, types, relations, permissions, conditions)
- ReBAC (relationship-based) and ABAC (attribute-based) patterns
- Dry-run validation before applying
- Data loss detection and warnings
- Reading current schema before edits

**Requirements:**
- Descope Management MCP installed and authorized

</details>

<details>
<summary><b>descope-byos-builder</b> — Build React BYOS custom UI on top of Descope flows</summary>

Translate Descope flow JSON exports into working React BYOS screens that call `state.next(interactionId, form)`. Parses real interaction IDs, form-key `name` props, screen names, and subflow loaders from your exported flow JSON — so every generated component is grounded in the actual flow, not guesswork. Includes a 19-entry failure catalog covering every silent-failure mode observed in real BYOS sessions.

**Use when:**
- "Build custom UI over my Descope flow"
- "My BYOS button does nothing" / "session is still anonymous after sign-in"
- "no handler for screen" errors at runtime
- "passkey ceremony aborts" / "WebAuthn hangs"
- Updating a BYOS implementation after the flow changed in the Descope console
- Adding post-auth promotion subflows (e.g. passkey enrollment after login)

**What the skill does:**
- Asks for exported flow JSONs (main flow + every subflow) before generating anything
- Runs `parse-flow.mjs` to extract screen names, interaction IDs, input `name` props, next-rules, and subflow loaders
- Generates per-screen React components with correct `state.next(interactionId, payload)` signatures
- Detects shared screen-name collisions and writes router components with documented disambiguation heuristics
- References the failure catalog before diagnosing any "doesn't work" symptom

**Required inputs (skill asks for these before starting):**
- Flow JSON exports — main flow + every invoked subflow, including post-auth promotion subflows
- Descope Project ID + base URL
- Mount point in the React app
- Existing BYOS code paths (if modifying)

**Iron rule:** Ground every BYOS component in the exported flow JSON. Do not guess interaction IDs, output key names, or screen names.

</details>

## Installation

<details>
<summary><b>Using skills CLI</b></summary>

```bash
npx skills add descope/skills
```

</details>

<details open>
<summary><b>Using Claude Code</b></summary>

Add the marketplace and install the plugin:

```
/plugin marketplace add descope/skills
/plugin install descope-skills
```

</details>

## Usage

Skills are automatically loaded by compatible AI agents once installed. Simply describe what you need:

<details>
<summary><b>descope-auth examples</b></summary>

```
Add Descope authentication to my Next.js app
```

```
Help me implement passkey login with Descope
```

```
Set up backend session validation for my Node.js API
```

```
Add OAuth login (Google and GitHub) using Descope
```

</details>

<details>
<summary><b>auth0-to-descope examples</b></summary>

```
Migrate my Next.js app from nextjs-auth0 to Descope
```

```
How do I replace Auth0 Actions with Descope?
```

```
Help me migrate our Auth0 Organizations setup to Descope
```

```
Our Express API uses express-openid-connect — how do we switch to Descope?
```

</details>

<details>
<summary><b>okta-cis-to-descope examples</b></summary>

```
Migrate my React app from @okta/okta-react to Descope
```

```
Our Express app uses @okta/oidc-middleware — how do we switch to Descope?
```

```
How do Okta Sign-On Policies and Authorization Servers map to Descope?
```

```
Help me migrate our Okta Identity Providers (per-tenant SSO) to Descope
```

</details>

<details>
<summary><b>descope-terraform examples</b></summary>

```
Set up Terraform to manage my Descope project
```

```
Create a Descope project with password auth and RBAC using Terraform
```

```
Add an HTTP connector and S3 audit logging to my Descope Terraform config
```

</details>

<details>
<summary><b>descope-byos-builder examples</b></summary>

```
Build custom login screens over my Descope sign-up-or-in flow
```

```
My BYOS submit button does nothing — no errors in the console
```

```
Getting "no handler for screen" after the user clicks Forgot Password
```

```
Session is still anonymous after onSuccess fires
```

```
Add passkey promotion screens that run after the user logs in
```

</details>

<details>
<summary><b>auth-review examples</b></summary>

```
/auth-review
```

```
Audit my app for authentication and authorization vulnerabilities
```

```
Find IDOR and broken access control bugs in this repo
```

```
Run an identity security review before I ship
```

</details>

<details>
<summary><b>descope-fga-schema examples</b></summary>

```
/descope-fga-schema
```

```
Define an FGA schema with users, organizations, and resource-level permissions
```

```
Add a condition to my FGA schema that checks attribute values
```

```
Update my authorization model to support team-based access control
```

</details>

## Compatible Agents

Works with any agent supporting the Agent Skills format:

- [Claude Code](https://code.claude.com) (Anthropic)
- [OpenCode](https://opencode.ai) (OhMyOpenCode)
- [Cursor](https://cursor.com)
- [Cline](https://cline.bot)
- [GitHub Copilot](https://github.com/features/copilot)
- [Windsurf](https://windsurf.com)
- And [36+ more agents](https://github.com/vercel-labs/skills#supported-agents)

<details>
<summary><b>Skill Structure</b></summary>

```
skills/
├── descope-auth/
│   ├── SKILL.md - Main instructions with framework detection
│   └── references/
│       ├── nextjs.md - Next.js App Router patterns
│       ├── react.md - React SPA patterns
│       └── backend.md - Node.js/Python validation
├── auth0-to-descope/
│   ├── SKILL.md - Three-phase migration workflow (MCP check, plan, execution)
│   └── references/
│       ├── implementation-nuances.md - Per-framework migration patterns and gotchas
│       └── flows-and-widgets.md - Descope terminology, Flow/Widget guides, console-vs-code
├── okta-cis-to-descope/
│   ├── SKILL.md - Three-phase migration workflow (MCP check, plan, execution)
│   └── references/
│       ├── implementation-nuances.md - Per-framework patterns, OIDC path, scp/scope, gotchas
│       ├── flows-and-widgets.md - Okta→Descope lingo map, Flow/Widget guides, console-vs-code
│       └── backend-sdks.md - Python and Java backend migration patterns
├── descope-terraform/
│   ├── SKILL.md - Provider setup, common configurations, and guardrails
│   └── references/
│       ├── project-resource.md - Full descope_project schema
│       ├── other-resources.md - descope_management_key and descope_descoper schemas
│       └── connectors.md - All 60+ supported connector types
├── auth-review/
│   ├── SKILL.md - Four-phase workflow, severity scale, guardrails
│   └── references/
│       ├── enumeration.md - Entrypoint patterns across HTTP/GraphQL/WebSocket/RPC/serverless/queues
│       ├── vulnerability-catalog.md - AuthN, tokens, sessions, IDOR/BOLA, OAuth, recovery, MFA, CSRF/CORS
│       ├── authz-matrix.md - Matrix schema and expected-principal inference rules
│       └── report-template.md - Exact report structure and issue-ready finding format
├── descope-fga-schema/
│   └── SKILL.md - DSL grammar, dry-run workflow, data loss guards
└── descope-byos-builder/
    ├── SKILL.md - Workflow, iron rule, critical rules, collision heuristics, red flags
    ├── parse-flow.mjs - Node parser: extracts screen tasks, interaction IDs, form-key name props, subflow loaders
    └── references/
        ├── byos-component-patterns.md - Core wiring, screen router, skeleton, and common screen examples
        └── gotchas.md - 19 silent-failure modes with symptom → root cause → fix, plus pre-ship checklist
```

</details>

## Getting Started with Descope

1. **Create a free account** on our [Sign Up page](https://www.descope.com/sign-up)
2. **Get your Project ID** from [Settings → Project](https://app.descope.com/settings/project)
3. **Install the skills** via `npx skills add descope/skills` or the `/plugin` command in Claude Code
4. **Ask your AI agent** to integrate Descope authentication or set up Terraform

## Documentation

- [Descope Documentation](https://docs.descope.com)
- [Descope Flows Guide](https://docs.descope.com/flows)
- [Authentication Methods](https://docs.descope.com/auth-methods)
- [API Reference](https://docs.descope.com/api)
- [Terraform Provider](https://registry.terraform.io/providers/descope/descope/latest/docs)
- [Managing Environments with Terraform](https://docs.descope.com/managing-environments/terraform)
- [BYOS (Bring Your Own Screen)](https://docs.descope.com/build/guides/byos/)
- [BYOS Sample App](https://github.com/descope-sample-apps/byos-sample-app)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## About Descope

[Descope](https://www.descope.com) provides passwordless authentication and user management for developers. Build secure, frictionless authentication flows with our no-code Flow Builder and developer-friendly SDKs.

## Support

- [Descope Community Slack](https://www.descope.com/community)
- [Email Support](mailto:support@descope.com)

---

Made with 💜 by [Descope](https://www.descope.com)
