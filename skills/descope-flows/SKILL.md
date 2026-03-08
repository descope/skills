---
name: descope-flows
description: Create, modify, and validate Descope authentication flows. Use when building or editing flow JSON files, validating flow structure, exporting/importing flows between projects, or troubleshooting broken flows.
---

# Descope Flows

Create, modify, and validate Descope authentication flows using the Management API.

**CRITICAL**: Never generate flow JSON from scratch. Always export an existing flow first, then modify the export. Flow JSON has complex internal structure with node IDs, edges, and screen references that cannot be reliably authored by hand.

## Prerequisites

- Descope Project ID from https://app.descope.com/settings/project
- Management Key from https://app.descope.com/company (Company > Management Keys)
- Set environment variables:
  ```bash
  export DESCOPE_PROJECT_ID="<your-project-id>"
  export DESCOPE_MANAGEMENT_KEY="<your-management-key>"
  ```

## Valid Flow IDs (CRITICAL - do not invent others)

| Flow ID | Purpose |
|---------|---------|
| `sign-up-or-in` | Combined signup/login (RECOMMENDED) |
| `sign-up` | Registration only |
| `sign-in` | Login only |
| `step-up` | MFA step-up authentication |
| `update-user` | Profile updates, add auth methods |

## Workflow: Export, Modify, Validate

### Step 1 - Export the current flow

Always start from an existing flow. Never author flow JSON from scratch.

```bash
curl -s -X POST "https://api.descope.com/v1/mgmt/flow/export" \
  -H "Authorization: Bearer ${DESCOPE_PROJECT_ID}:${DESCOPE_MANAGEMENT_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"flowId\": \"sign-up-or-in\"}" \
  -o flow-export.json
```

The exported JSON has two top-level keys:
- `flow`: Flow definition (metadata, nodes, edges, logic)
- `screens`: List of screen definitions (UI widgets and layout)

### Step 2 - Modify the exported flow

Make targeted changes to the exported JSON. Preserve all internal IDs and structure you don't intend to change.

### Step 3 - Validate locally

Run the validation script from `references/validate-flow.sh` to check:
- JSON syntax
- Required top-level keys (`flow`, `screens`)
- Flow metadata fields (`id`, `name`, `version`)
- Screen references (every screen step references a screen that exists)
- No orphan screens (every screen is referenced by at least one step)
- Connector context key format

```bash
bash validate-flow.sh flow-modified.json
```

See `references/validate-flow.sh` for the full validation script.

### Step 4 - Test in staging project (recommended)

Import to a **separate staging project** — never directly to production:

```bash
curl -s -X POST "https://api.descope.com/v1/mgmt/flow/import" \
  -H "Authorization: Bearer ${DESCOPE_STAGING_PROJECT_ID}:${DESCOPE_MANAGEMENT_KEY}" \
  -H "Content-Type: application/json" \
  -d @flow-modified.json
```

Then test the flow using the Descope console flow runner in the staging project.

### Step 5 - Deploy to production

Only after staging validation succeeds, import to the production project.

## Terraform Workflow

When managing flows with Terraform, use `terraform plan` as a non-destructive validation step:

```hcl
flows = {
  "sign-up-or-in" = {
    data = file("flows/sign-up-or-in.json")
  }
}
```

```bash
terraform plan    # Validates flow JSON and connector dependencies — does NOT apply
terraform apply   # Only after plan succeeds and is reviewed
```

The Terraform provider validates that connectors referenced by the flow exist in the project configuration.

## Flow Components

| Component | Purpose | Key Considerations |
|-----------|---------|-------------------|
| **Screens** | User-facing UI (forms, buttons, inputs) | Must be referenced by a screen step in the flow |
| **Actions** | Backend ops (send OTP, verify, update user) | Parameters must match action type schema |
| **Connectors** | Third-party integrations (HTTP, email, SMS) | Must reference a connector configured in the project |
| **Conditions** | Decision branching on attributes/results | Must have both true and false branches connected |
| **Subflows** | Reusable flow references | Referenced flow ID must exist in the project |

## Listing Available Flows

```bash
curl -s -X POST "https://api.descope.com/v1/mgmt/flow/list" \
  -H "Authorization: Bearer ${DESCOPE_PROJECT_ID}:${DESCOPE_MANAGEMENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{}'
```

To search specific flows:
```bash
curl -s -X POST "https://api.descope.com/v1/mgmt/flow/list" \
  -H "Authorization: Bearer ${DESCOPE_PROJECT_ID}:${DESCOPE_MANAGEMENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["sign-up-or-in", "sign-in"]}'
```

## DO NOT

- DO NOT generate flow JSON from scratch — always export an existing flow first and modify it
- DO NOT import directly to production — always validate in a staging project first
- DO NOT invent flow IDs — only use IDs from the table above
- DO NOT assume a flow is valid because the JSON parses — run the validation script
- DO NOT hardcode management keys in files — use environment variables
- DO NOT modify internal node `id` fields unless you understand the full graph structure
- DO NOT remove screens that are referenced by screen steps in the flow
- DO NOT reference connectors that aren't configured in the target project
- DO NOT skip `terraform plan` before `terraform apply` when using Terraform

## References

- `references/validate-flow.sh` - Local validation script for flow JSON
- `references/flow-api.md` - Complete Management API reference for flows
- `references/flow-structure.md` - Flow JSON structure and validation rules
