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
├── descope-terraform/
│   ├── SKILL.md - Provider setup, common configurations, and guardrails
│   └── references/
│       ├── project-resource.md - Full descope_project schema
│       ├── other-resources.md - descope_management_key and descope_descoper schemas
│       └── connectors.md - All 60+ supported connector types
└── auth-review/
    ├── SKILL.md - Four-phase workflow, severity scale, guardrails
    └── references/
        ├── enumeration.md - Entrypoint patterns across HTTP/GraphQL/WebSocket/RPC/serverless/queues
        ├── vulnerability-catalog.md - AuthN, tokens, sessions, IDOR/BOLA, OAuth, recovery, MFA, CSRF/CORS
        ├── authz-matrix.md - Matrix schema and expected-principal inference rules
        └── report-template.md - Exact report structure and issue-ready finding format
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

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## About Descope

[Descope](https://www.descope.com) provides passwordless authentication and user management for developers. Build secure, frictionless authentication flows with our no-code Flow Builder and developer-friendly SDKs.

## Support

- [Descope Community Slack](https://www.descope.com/community)
- [GitHub Discussions](https://github.com/descope/descope-js/discussions)
- [Email Support](mailto:support@descope.com)

---

Made with 💜 by [Descope](https://www.descope.com)
