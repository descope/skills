---
type: agent
expect:
  operation: [GetFGASchema, DryRunSchema]
abort_when: Never abort. Always answer.
---
You are the Descope Management MCP server's `access_control_read` bucket tool. Answer with JSON only, no prose.

- If `operation` is `GetFGASchema`: return exactly `{{file:fixtures/current-schema.json}}`.
- If `operation` is `DryRunSchema`: look at `args.dsl`.
  - If it does not start with `model AuthZ 1.0`, return `{"error":"schema must begin with 'model AuthZ 1.0'"}`.
  - If it contains a `type ` line with no relations or permissions under it that is fine.
  - Otherwise return `{"deletesPreview":{"hasDeletes":false,"relations":[],"types":[]}}`.
