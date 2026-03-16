# Cognito Full Migration

Bulk export users from AWS Cognito and import into Descope. Since Cognito does NOT export password hashes, this is always a without-passwords migration.

## Option A: Descope Migration Tool (Recommended)

### Setup

```bash
git clone git@github.com:descope/descope-migration.git
cd descope-migration
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Configure Environment Variables

Rename `.env.example` to `.env` and populate:

```bash
DESCOPE_PROJECT_ID=<Your Descope Project ID>
DESCOPE_MANAGEMENT_KEY=<Your Descope Management Key>
AWS_ACCESS_KEY_ID=<Your AWS Access Key>
AWS_SECRET_ACCESS_KEY=<Your AWS Secret Key>
COGNITO_USER_POOL_ID=<Your Cognito User Pool ID>
```

### Run Migration

```bash
# Dry run — preview what will be migrated without making changes
python3 src/main.py cognito --dry-run

# Live run — execute the migration
python3 src/main.py cognito
```

Add `-v` or `--verbose` for detailed output.

The tool automatically:
- Converts Cognito User Groups to Descope Roles
- Imports users with profile data and custom attributes
- Assigns users to roles based on group membership
- Sets `freshlyMigrated = true` on all imported users

## Option B: Manual Export via Cognito API

For complete control over the export and transformation process.

### Prerequisites

```bash
pip install boto3 requests
```

IAM user must have these permissions:
- `cognito-idp:ListUsers`
- `cognito-idp:ListGroups`
- `cognito-idp:AdminListGroupsForUser`

### Step 1: Export Users with Pagination

```python
import boto3
import json

cognito = boto3.client('cognito-idp', region_name='us-east-1')
user_pool_id = 'us-east-1_XXXXXXXXX'

users = []
pagination_token = None

while True:
    params = {
        'UserPoolId': user_pool_id,
        'Limit': 60  # Max 60 per page
    }
    if pagination_token:
        params['PaginationToken'] = pagination_token

    response = cognito.list_users(**params)
    users.extend(response['Users'])

    if 'PaginationToken' in response:
        pagination_token = response['PaginationToken']
    else:
        break

print(f"Total users retrieved: {len(users)}")
```

**Important:** Cognito rate limits `ListUsers` to 5 requests/second. Implement exponential backoff and retry logic for large user pools.

### Step 2: Export User Groups

```python
groups_response = cognito.list_groups(UserPoolId=user_pool_id)
groups = groups_response['Groups']

for user in users:
    username = user['Username']
    user_groups_response = cognito.admin_list_groups_for_user(
        Username=username,
        UserPoolId=user_pool_id
    )
    user['Groups'] = [g['GroupName'] for g in user_groups_response['Groups']]
```

### Step 3: Transform to Descope Format

```python
def map_cognito_user_to_descope(cognito_user):
    def get_attr(name):
        for attr in cognito_user.get('Attributes', []):
            if attr['Name'] == name:
                return attr['Value']
        return None

    email = get_attr('email')
    phone = get_attr('phone_number')

    descope_user = {
        "loginIds": [email] if email else [cognito_user['Username']],
        "email": email,
        "phone": phone,
        "name": get_attr('name'),
        "givenName": get_attr('given_name'),
        "familyName": get_attr('family_name'),
        "verifiedEmail": get_attr('email_verified') == 'true',
        "verifiedPhone": get_attr('phone_number_verified') == 'true',
        "customAttributes": {},
        "roleNames": cognito_user.get('Groups', [])
    }

    # Map custom attributes (custom:* prefix)
    for attr in cognito_user.get('Attributes', []):
        if attr['Name'].startswith('custom:'):
            attr_name = attr['Name'].replace('custom:', '')
            descope_user['customAttributes'][attr_name] = attr['Value']

    descope_user['customAttributes']['freshlyMigrated'] = True

    return descope_user

descope_users = [map_cognito_user_to_descope(u) for u in users]
```

### Step 4: Import to Descope

```python
import requests

DESCOPE_PROJECT_ID = 'your-project-id'
DESCOPE_MANAGEMENT_KEY = 'your-management-key'

def import_users_to_descope(users):
    url = 'https://api.descope.com/v1/mgmt/user/create/batch'
    headers = {
        'Authorization': f'Bearer {DESCOPE_PROJECT_ID}:{DESCOPE_MANAGEMENT_KEY}',
        'Content-Type': 'application/json'
    }

    batch_size = 100
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        response = requests.post(url, json={'users': batch}, headers=headers)

        if response.status_code == 200:
            print(f"Successfully imported batch {i // batch_size + 1}")
        else:
            print(f"Error importing batch {i // batch_size + 1}: {response.text}")

import_users_to_descope(descope_users)
```

**API endpoints:**
- Single user: `POST /v1/mgmt/user/create`
- Batch (up to 100): `POST /v1/mgmt/user/create/batch`

Ensure all `loginId` values are unique across users.

## Dual Token Validation (During Migration)

During the migration window, backends must validate tokens from both Cognito and Descope:

```python
import jwt
import requests

COGNITO_REGION = 'us-east-1'
COGNITO_USER_POOL_ID = 'us-east-1_XXXXXXXXX'
DESCOPE_PROJECT_ID = 'your-project-id'

def validate_token(token):
    header = jwt.get_unverified_header(token)
    decoded = jwt.decode(token, options={"verify_signature": False})
    issuer = decoded.get('iss', '')

    if 'amazoncognito.com' in issuer:
        return validate_cognito_token(token)
    elif 'descope.com' in issuer:
        return validate_descope_token(token)
    else:
        raise ValueError('Unknown token issuer')

def validate_cognito_token(token):
    jwks_url = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'
    jwks = requests.get(jwks_url).json()
    # Use python-jose or PyJWT with JWKS for full validation
    return True

def validate_descope_token(token):
    from descope import DescopeClient
    descope_client = DescopeClient(project_id=DESCOPE_PROJECT_ID)
    return descope_client.validate_session(token)
```

This enables gradual rollout — existing Cognito sessions remain valid while new signups use Descope.

## Application Code Updates

### Environment Variables

Remove:
```
AWS_COGNITO_USER_POOL_ID, AWS_COGNITO_CLIENT_ID, AWS_COGNITO_REGION
```

Add:
```
DESCOPE_PROJECT_ID=<your-project-id>
```

### SDK Replacement Patterns

| Cognito SDK | Descope SDK |
|-------------|-------------|
| `amazon-cognito-identity-js` | `@descope/web-js-sdk` or `@descope/react-sdk` |
| `@aws-sdk/client-cognito-identity-provider` | `@descope/node-sdk` |
| `boto3` (cognito-idp) | `descope-python` |

### React Example

**Before (Cognito):**
```jsx
import { CognitoUser, AuthenticationDetails } from 'amazon-cognito-identity-js';

const authDetails = new AuthenticationDetails({ Username: email, Password: password });
cognitoUser.authenticateUser(authDetails, { onSuccess: (session) => { ... } });
```

**After (Descope):**
```jsx
import { useSession, useUser, useDescope } from '@descope/react-sdk';
const { isAuthenticated, isSessionLoading } = useSession();
const { user } = useUser();
const { logout } = useDescope();
```

### Backend Token Validation

**Before (Cognito):**
```python
import boto3
cognito = boto3.client('cognito-idp')
response = cognito.get_user(AccessToken=token)
```

**After (Descope):**
```python
from descope import DescopeClient
descope_client = DescopeClient(project_id="your-project-id")
jwt_response = descope_client.validate_session(session_token)
```

## Post-Migration Cleanup

1. **Verify** user count and data parity between Cognito and Descope
2. **Test** all authentication flows end-to-end
3. **Update** AWS service JWT authorizers (API Gateway, AppSync, ALB)
4. **Monitor** `freshlyMigrated` attribute to track user transitions
5. **Disable** (do not delete) the Cognito User Pool for 30-90 days
6. **Remove** AWS Cognito SDK dependencies from your application
7. **Archive** export data and migration logs for compliance
