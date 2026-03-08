# Flow Management API

All endpoints require a Management Key. Authentication header format:
```
Authorization: Bearer <ProjectId>:<ManagementKey>
```

Base URL: `https://api.descope.com`

## List / Search Flows

**POST** `/v1/mgmt/flow/list`

List all flows or search by ID.

```json
// List all
{}

// Search specific flows
{"ids": ["sign-up-or-in", "sign-in"]}
```

**Response**: Array of flow metadata (id, name, description, disabled status).

## Export Flow

**POST** `/v1/mgmt/flow/export`

Export a complete flow with all screens.

```json
{"flowId": "sign-up-or-in"}
```

**Response**:
```json
{
  "flow": {
    "id": "sign-up-or-in",
    "name": "Sign Up or In",
    "version": 1,
    ...
  },
  "screens": [
    {
      "id": "screen-id",
      ...
    }
  ]
}
```

The `flow` object contains the full flow definition: metadata, nodes (steps), edges (connections between steps), and configuration for each step.

The `screens` array contains all screen definitions referenced by screen steps in the flow.

## Import Flow

**POST** `/v1/mgmt/flow/import`

Import a flow and its screens. **Overwrites the existing flow with the same ID.**

```json
{
  "flowId": "sign-up-or-in",
  "flow": { ... },
  "screens": [ ... ]
}
```

**IMPORTANT**: Import overwrites the existing flow. Always import to a staging project first for validation, never directly to production.

If the import fails (HTTP 4xx/5xx), the response body contains error details about what's invalid in the flow.

## Delete Flow

**POST** `/v1/mgmt/flow/delete`

```json
{"flowId": "sign-up-or-in"}
```

## Export Theme

**POST** `/v1/mgmt/flow/theme/export`

Export the project's flow theme/styles.

```json
{}
```

## Import Theme

**POST** `/v1/mgmt/flow/theme/import`

Import a flow theme/styles.

```json
{"theme": { ... }}
```

## SDK Usage

### Node.js

```javascript
import DescopeClient from '@descope/node-sdk';

const sdk = DescopeClient({
  projectId: process.env.DESCOPE_PROJECT_ID,
  managementKey: process.env.DESCOPE_MANAGEMENT_KEY,
});

// List flows
const flows = await sdk.management.flow.list();

// Export
const { data } = await sdk.management.flow.export('sign-up-or-in');
const { flow, screens } = data;

// Import (to staging project - use a separate SDK instance)
await stagingSdk.management.flow.import('sign-up-or-in', flow, screens);
```

### Python

```python
from descope import DescopeClient

sdk = DescopeClient(
    project_id=os.environ["DESCOPE_PROJECT_ID"],
    management_key=os.environ["DESCOPE_MANAGEMENT_KEY"],
)

# List flows
flows = sdk.mgmt.flow.list_flows()

# Export
export = sdk.mgmt.flow.export_flow(flow_id="sign-up-or-in")
flow = export["flow"]
screens = export["screens"]

# Import (to staging project - use a separate SDK instance)
staging_sdk.mgmt.flow.import_flow(
    flow_id="sign-up-or-in",
    flow=flow,
    screens=screens,
)
```

## Environment Promotion Pattern

Descope projects map to environments (dev, staging, production). Promote flows safely:

1. **Develop** in dev project
2. **Export** from dev: `POST /v1/mgmt/flow/export` (using dev credentials)
3. **Validate** locally: `bash validate-flow.sh flow-export.json`
4. **Import to staging**: `POST /v1/mgmt/flow/import` (using staging credentials)
5. **Test** in staging using the console flow runner
6. **Import to production**: `POST /v1/mgmt/flow/import` (using production credentials)

Each project uses its own `DESCOPE_PROJECT_ID` and `DESCOPE_MANAGEMENT_KEY`.
