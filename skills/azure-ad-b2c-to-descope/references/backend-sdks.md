# Descope Migration: Backend Reference (Azure AD B2C)

This file covers API and backend migration for Azure AD B2C → Descope: .NET (the most common B2C
backend), Node.js, Python, and Java. Read it when the codebase has an API that validates B2C
access tokens (`Microsoft.Identity.Web`, `passport-azure-ad`, `jsonwebtoken` + B2C JWKS, PyJWT,
Spring resource server) or calls Microsoft Graph to manage B2C users.

## Contents

- [Which token does the API receive?](#which-token-does-the-api-receive)
- [.NET / ASP.NET Core](#net--aspnet-core)
- [Node.js](#nodejs)
- [Python](#python)
- [Java / Spring](#java--spring)
- [Client credentials (M2M) callers](#client-credentials-m2m-callers)
- [Dual-token validation during rollout](#dual-token-validation-during-rollout)
- [Microsoft Graph user management → Descope Management SDK](#microsoft-graph-user-management--descope-management-sdk)

---

## Which token does the API receive?

| Frontend setup (Decision 1) | Token the API validates | Validate with |
|---|---|---|
| Inbound App + Resource (default for B2C apps with scoped APIs) | Inbound App **access token**: `iss` = `https://api.descope.com/v1/apps/<ProjectID>`, `aud` = Resource, `scope` = space-separated | Standard JWT validation using `issuer` and `jwks_uri` from the Inbound App discovery document. Confirm with the Docs MCP whether the Descope backend SDK's session validation accepts Inbound App tokens before using it for these. |
| Plain Descope SDK / embedded Flow | Descope **session token** (`DS`): `iss` = `https://api.descope.com/<ProjectID>`, `aud` = project ID | Descope backend SDK (`validateSession`) |
| Federated App via OIDC library | ID/access tokens from the project-level OIDC endpoints | Standard JWT validation with `https://api.descope.com/<ProjectID>` |

Always check `aud` against the Resource identifier for Inbound App tokens — by default other
Descope tokens carry the project ID, and accepting that would accept tokens issued for other
apps. Check `azp` if only some clients may call the API.

Keep the B2C scope **names** (`tasks.read`) on the Descope Resource so only the claim name changes
(`scp` → `scope`).

---

## .NET / ASP.NET Core

### Remove

- NuGet: `Microsoft.Identity.Web` (and `Microsoft.Identity.Web.UI` if only used for B2C)
- `builder.Services.AddMicrosoftIdentityWebApiAuthentication(Configuration, "AzureAdB2C")` / `AddMicrosoftIdentityWebApi(...)`
- `[RequiredScope(...)]`, `[RequiredScopeOrAppPermission(...)]`, `HttpContext.VerifyUserHasAnyAcceptedScope(...)` — these read `scp` and `http://schemas.microsoft.com/identity/claims/scope`, **not** `scope`
- `appsettings.json` → `AzureAdB2C` section (`Instance`, `Domain`, `ClientId`, `SignUpSignInPolicyId`, `Scopes`)
- `User.GetObjectId()` and other `Microsoft.Identity.Web` claim helpers

### Option A — Inbound App access tokens (default)

Standard `JwtBearer` against the Descope Inbound App issuer:

```csharp
using Microsoft.AspNetCore.Authentication.JwtBearer;

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(o =>
    {
        o.Authority = builder.Configuration["Descope:Issuer"];      // Inbound App issuer from the Console
        // If the discovery document is not at {Authority}/.well-known/openid-configuration,
        // set o.MetadataAddress to the discovery URL shown in the Console.
        o.Audience = builder.Configuration["Descope:Resource"];     // Resource identifier
        o.MapInboundClaims = false;                                 // keep "sub", "scope" as issued
        o.TokenValidationParameters.NameClaimType = "sub";
    });

builder.Services.AddAuthorization(o =>
{
    o.AddPolicy("tasks.read", p => p.RequireAssertion(ctx =>
        (ctx.User.FindFirst("scope")?.Value ?? "")
            .Split(' ', StringSplitOptions.RemoveEmptyEntries)
            .Contains("tasks.read")));
});
```

```csharp
// Before
[Authorize]
[RequiredScope("tasks.read")]
public class TasksController : ControllerBase { }

// After
[Authorize(Policy = "tasks.read")]
public class TasksController : ControllerBase { }
```

`appsettings.json`:
```json
"Descope": {
  "ProjectId": "P...",
  "Issuer": "https://api.descope.com/v1/apps/P...",
  "Resource": "https://api.example.com"
}
```

### Option B — Descope session tokens (plain SDK / embedded Flow)

Use the Descope .NET SDK (NuGet package `Descope`, [docs](https://docs.descope.com/getting-started/dotnet)):

```bash
dotnet add package Descope
```

```csharp
builder.Services.AddDescopeClient(new DescopeClientOptions
{
    ProjectId = builder.Configuration["Descope:ProjectId"]!,
});

// Minimal middleware: validate the Bearer session token on API routes only
app.UseWhen(c => c.Request.Path.StartsWithSegments("/api"), api => api.Use(async (ctx, next) =>
{
    var header = ctx.Request.Headers.Authorization.ToString();
    if (!header.StartsWith("Bearer ")) { ctx.Response.StatusCode = 401; return; }
    var descope = ctx.RequestServices.GetRequiredService<IDescopeClient>();
    try
    {
        var token = await descope.Auth.ValidateSessionAsync(header["Bearer ".Length..]);
        ctx.Items["descopeToken"] = token;
        await next();
    }
    catch (DescopeException)
    {
        ctx.Response.StatusCode = 401;
    }
}));
```

Verify namespaces, option names, and the returned token type against the installed package or
the Docs MCP before writing the code. The SDK validates locally against cached keys
(`JwksCacheDuration`, default 5 minutes). By default `aud` is the project ID; check claims after
validation if the project serves more than one app.

### Claims in controllers

| B2C (`Microsoft.Identity.Web`) | Descope |
|---|---|
| `User.GetObjectId()` / `oid` | `User.FindFirst("b2cObjectId")` (JWT Template) for legacy keys; `sub` for the Descope user ID |
| `User.FindFirst("emails")` | `User.FindFirst("email")` (JWT Template) |
| `User.FindFirst("tfp")` | Delete |
| `User.FindFirst("extension_Role")` | `roles` claim, or the custom attribute via JWT Template |

---

## Node.js

### Remove

- `passport-azure-ad` (`BearerStrategy` with `identityMetadata` / `policyName` / `scope`), or `jsonwebtoken` + `jwks-rsa` pointed at `…b2clogin.com/…/discovery/v2.0/keys`
- `@azure/msal-node` used only for token validation

### Inbound App access tokens

```js
import { createRemoteJWKSet, jwtVerify } from 'jose';

const JWKS = createRemoteJWKSet(new URL(process.env.DESCOPE_JWKS_URI)); // jwks_uri from discovery

export async function requireAuth(req, res, next) {
  const token = req.headers.authorization?.replace(/^Bearer /, '');
  if (!token) return res.sendStatus(401);
  try {
    const { payload } = await jwtVerify(token, JWKS, {
      issuer: process.env.DESCOPE_ISSUER,      // Inbound App issuer
      audience: process.env.DESCOPE_RESOURCE,  // Resource identifier
    });
    req.auth = payload;
    next();
  } catch {
    res.sendStatus(401);
  }
}

export const requireScope = (scope) => (req, res, next) =>
  (req.auth?.scope ?? '').split(' ').includes(scope) ? next() : res.sendStatus(403);
```

```js
// Before (passport-azure-ad BearerStrategy with scope: ['tasks.read'])
app.get('/api/tasks', passport.authenticate('oauth-bearer', { session: false }), handler);

// After
app.get('/api/tasks', requireAuth, requireScope('tasks.read'), handler);
```

### Descope session tokens

```js
import DescopeClient from '@descope/node-sdk';

const descopeClient = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID });

const authInfo = await descopeClient.validateSession(sessionToken /*, { audience } */);
req.auth = authInfo.token;
```

`validateSession` accepts an optional `audience` (string or array).

---

## Python

### Remove

- `msal` used for validation, `PyJWT` / `python-jose` configured with B2C metadata (`…/<policy>/v2.0/.well-known/openid-configuration`), `flask-azure-oauth` / `fastapi-azure-auth` B2C settings

### Inbound App access tokens

```python
import os
import jwt

jwks_client = jwt.PyJWKClient(os.environ["DESCOPE_JWKS_URI"])

def verify(token: str) -> dict:
    key = jwks_client.get_signing_key_from_jwt(token).key
    return jwt.decode(
        token, key, algorithms=["RS256"],
        audience=os.environ["DESCOPE_RESOURCE"],
        issuer=os.environ["DESCOPE_ISSUER"],
    )

def has_scope(claims: dict, scope: str) -> bool:
    value = claims.get("scope", "")
    scopes = value if isinstance(value, list) else value.split()
    return scope in scopes
```

FastAPI dependency:
```python
from fastapi import Depends, HTTPException, Header

async def current_claims(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401)
    try:
        return verify(authorization.removeprefix("Bearer "))
    except jwt.PyJWTError:
        raise HTTPException(401)

def require_scope(scope: str):
    def checker(claims: dict = Depends(current_claims)):
        if not has_scope(claims, scope):
            raise HTTPException(403)
        return claims
    return checker
```

### Descope session tokens

```python
import os
from descope import DescopeClient, AuthException

descope_client = DescopeClient(project_id=os.environ["DESCOPE_PROJECT_ID"])

try:
    jwt_response = descope_client.validate_session(session_token)
except AuthException:
    ...  # 401
```

---

## Java / Spring

### Remove

- `spring-cloud-azure-starter-active-directory-b2c` (or the older `azure-spring-boot-starter-active-directory-b2c`) and its `spring.cloud.azure.active-directory.b2c.*` properties
- B2C `issuer-uri` / `jwk-set-uri` pointing at `b2clogin.com`

### Inbound App access tokens — Spring Security resource server

```properties
spring.security.oauth2.resourceserver.jwt.issuer-uri=${DESCOPE_ISSUER}
spring.security.oauth2.resourceserver.jwt.audiences=${DESCOPE_RESOURCE}
```

(`jwt.audiences` requires a recent Spring Boot 3.x; on older versions add an audience
`OAuth2TokenValidator`.) Spring's default `JwtGrantedAuthoritiesConverter` reads the `scope` claim (and `scp`), so
`hasAuthority('SCOPE_tasks.read')` / `@PreAuthorize("hasAuthority('SCOPE_tasks.read')")` keeps
working once the Resource uses the same scope names. If issuer discovery does not resolve from
the issuer URL, set `jwk-set-uri` to the discovery document's `jwks_uri` and validate the issuer
with a custom `JwtDecoder`.

### Descope session tokens — Java SDK

```xml
<dependency>
  <groupId>com.descope</groupId>
  <artifactId>java-sdk</artifactId>
  <version>[1.0.0,)</version>
</dependency>
```

```java
DescopeClient descopeClient = new DescopeClient(
    Config.builder().projectId(System.getenv("DESCOPE_PROJECT_ID")).build());
AuthenticationService authService = descopeClient.getAuthenticationServices().getAuthService();

try {
    Token token = authService.validateSessionWithToken(sessionToken);
} catch (DescopeException e) {
    // 401
}
```

---

## Client credentials (M2M) callers

B2C daemon app registrations (client credentials against
`…/<tenant>.onmicrosoft.com/<policy>/oauth2/v2.0/token` with `scope=<App ID URI>/.default`)
become **Inbound Apps with client credentials** (not Access Keys):

```http
POST https://api.descope.com/oauth2/v1/apps/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=<inbound-app-client-id>&client_secret=<secret>&scope=tasks.read
```

The token's `sub` is the app ID (no user). The API validates it like any Inbound App access token.
B2C client-credentials tokens may carry app permissions in `roles` (Entra-style) rather than
`scp` — check how the API authorizes daemons today and map those checks to Inbound App scopes.
Confirm the exact token request parameters (scope format, resource) with the Docs MCP.

---

## Dual-token validation during rollout

During a phased cutover the API receives B2C and Descope tokens. Route by `iss`:

```csharp
using Microsoft.IdentityModel.JsonWebTokens;

var b2cIssuers = builder.Configuration.GetSection("AzureAdB2C:Issuers").Get<string[]>()!; // incl. custom-domain / tfp variants

builder.Services.AddAuthentication("Bearer")
    .AddJwtBearer("B2C", o =>
    {
        o.Authority = "https://<tenant>.b2clogin.com/<tenant>.onmicrosoft.com/<policy>/v2.0/";
        o.Audience = "<api-app-client-id>";
        o.MapInboundClaims = false;                 // keep "scp" as issued
    })
    .AddJwtBearer("Descope", o =>
    {
        o.Authority = builder.Configuration["Descope:Issuer"];
        o.Audience = builder.Configuration["Descope:Resource"];
        o.MapInboundClaims = false;
    })
    .AddPolicyScheme("Bearer", "Bearer", o =>
    {
        o.ForwardDefaultSelector = ctx =>
        {
            var header = ctx.Request.Headers.Authorization.ToString();
            if (!header.StartsWith("Bearer ")) return "Descope";       // let [AllowAnonymous] endpoints pass
            var handler = new JsonWebTokenHandler();
            var raw = header["Bearer ".Length..];
            if (!handler.CanReadToken(raw)) return "Descope";            // fails validation → 401
            var iss = handler.ReadJsonWebToken(raw).Issuer;
            return b2cIssuers.Contains(iss) ? "B2C" : "Descope";
        };
    });

// Scope policy that accepts both tokens during the window
builder.Services.AddAuthorization(o => o.AddPolicy("tasks.read", p => p.RequireAssertion(ctx =>
    (ctx.User.FindFirst("scope")?.Value ?? ctx.User.FindFirst("scp")?.Value ?? "")
        .Split(' ', StringSplitOptions.RemoveEmptyEntries).Contains("tasks.read"))));
```

Match on the exact B2C issuer values (the `b2clogin.com`, custom-domain, and `tfp` variants the
API sees), not a substring. Remove the B2C scheme only after every client has moved to Descope and
remaining B2C sessions are revoked or expired — B2C refresh tokens slide (default 14-day lifetime,
up to a 90-day sliding window; SPAs 24 hours).
Same pattern in Node/Python: decode the unverified `iss`, then pick the verifier.

---

## Microsoft Graph user management → Descope Management SDK

| Graph (B2C) | Descope |
|---|---|
| `POST /users` with `identities` | Create user (login ID = sign-in name) |
| `PATCH /users/{id}` with `extension_<appId>_<name>` | Update user custom attributes |
| `DELETE /users/{id}` | Delete user |
| `GET /users?$filter=identities/any(...)` | Load / search users by login ID |
| `POST /groups/{id}/members/$ref` (group-based roles) | Assign roles (per tenant if needed) |

Requires `DESCOPE_MANAGEMENT_KEY` (server-side only). Verify SDK method names per language with
the Docs MCP. Before migrating a custom admin page, check whether the User Management Widget
covers it.
