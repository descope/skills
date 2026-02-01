# Backend Session Validation

Always validate sessions server-side. NEVER trust client-side auth alone.

## Node.js

Install the SDK:

```bash
npm install @descope/node-sdk
```

Validate session tokens:

```typescript
import DescopeClient from '@descope/node-sdk';

const descope = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });

async function validateRequest(req: Request) {
  const token = req.headers.get('Authorization')?.replace('Bearer ', '');
  if (!token) return null;
  
  try {
    const authInfo = await descope.validateSession(token);
    return authInfo; // Contains user info, permissions, etc.
  } catch {
    return null;
  }
}
```

## Python

Install the SDK:

```bash
pip install descope
```

Validate session tokens:

```python
from descope import DescopeClient
import os

descope = DescopeClient(project_id=os.environ["DESCOPE_PROJECT_ID"])

def validate_session(token: str):
    try:
        jwt_response = descope.validate_session(token)
        return jwt_response  # Contains user info
    except Exception:
        return None
```

## DO NOT

- DO NOT decode JWTs manually with `jsonwebtoken` or `PyJWT`
- DO NOT skip validation on "internal" endpoints
- DO NOT cache validation results for too long (tokens expire)
- DO NOT trust client-provided user data without server-side validation
