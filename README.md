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
<summary><b>descope-migrate-auth0</b> — Migrate from Auth0 to Descope</summary>

Migrate users, roles, permissions, and tenants from Auth0 to Descope. Supports full cutover or hybrid (Auth0 remains active with Descope as federated IdP).

**Use when:**
- "Migrate my Auth0 tenant to Descope"
- "Move users and roles from Auth0 to Descope"
- "Set up hybrid Auth0 + Descope authentication"
- "Export Auth0 users and import into Descope"

**Covers:**
- **Full Migration** - Complete transition (API-based or JSON export for 1000+ users)
- **Hybrid Migration** - Auth0 stays active; Descope as federated identity provider
- Roles and permissions mapping to Descope RBAC
- Tenant/organization mapping
- `freshlyMigrated` and post-migration flow guidance

**References:**
- `references/full-migration.md` - Bulk export/import
- `references/hybrid-migration.md` - Auth0 + Descope coexistence

</details>

<details>
<summary><b>descope-migrate-cognito</b> — Migrate from AWS Cognito to Descope</summary>

Migrate users, groups, and configuration from AWS Cognito User Pools to Descope. Supports full bulk import (without passwords—Cognito does not export hashes) or just-in-time (JIT) migration.

**Use when:**
- "Migrate my Cognito user pool to Descope"
- "Set up JIT migration from Cognito to Descope"
- "Map Cognito groups to Descope roles"
- "Move users from AWS Cognito to Descope"

**Covers:**
- **Full Migration** - Export users/groups via migration tool or boto3; import into Descope (passwordless or forced reset)
- **JIT Migration** - Users provision on first sign-in (USER_PASSWORD_AUTH via Generic HTTP Connector, or Cognito as OIDC provider)
- Attribute and group-to-role mapping
- Session validation during Cognito + Descope coexistence
- AWS service integration (API Gateway, AppSync)

**References:**
- `references/full-migration.md` - Bulk export/import
- `references/jit-migration.md` - Just-in-time provisioning (Cognito must stay active until users migrate)

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
<summary><b>descope-migrate-auth0 examples</b></summary>

```
Help me migrate users from Auth0 to Descope
```

```
Set up full migration from Auth0 with roles and tenants
```

```
Configure hybrid Auth0 + Descope so Auth0 stays active
```

</details>

<details>
<summary><b>descope-migrate-cognito examples</b></summary>

```
Migrate my AWS Cognito user pool to Descope
```

```
Set up JIT migration from Cognito using USER_PASSWORD_AUTH
```

```
Map Cognito groups to Descope roles and import users
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
├── descope-migrate-auth0/
│   ├── SKILL.md - Auth0-to-Descope migration (full and hybrid)
│   └── references/
│       ├── full-migration.md - Bulk export/import
│       └── hybrid-migration.md - Auth0 + Descope coexistence
└── descope-migrate-cognito/
    ├── SKILL.md - Cognito-to-Descope migration (full and JIT)
    └── references/
        ├── full-migration.md - Bulk export/import
        └── jit-migration.md - Just-in-time provisioning
```

</details>

## Getting Started with Descope

1. **Create a free account** on our [Sign Up page](https://www.descope.com/sign-up)
2. **Get your Project ID** from [Settings → Project](https://app.descope.com/settings/project)
3. **Install the skills** via `npx skills add descope/skills` or the `/plugin` command in Claude Code
4. **Ask your AI agent** to integrate Descope authentication, set up Terraform, or migrate from Auth0/Cognito

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
