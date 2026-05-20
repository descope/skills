# Descope Migration: Python and Java Backend Reference (Okta CIS)

This file covers Python and Java backend migration patterns for Okta CIS → Descope.
Read it when the codebase has a Python or Java backend that currently validates Okta JWTs,
uses Okta management APIs, or integrates with Okta via Flask, FastAPI, Django, or Spring Boot.

> **See also:** `implementation-nuances.md` for architecture decisions (Inbound vs. Federated Apps,
> scp vs. scope claim, user migration paths) that apply regardless of backend language.

---

## Contents

- [Python](#python)
  - [Package changes](#package-changes-python)
  - [Client setup](#client-setup-python)
  - [Session validation middleware](#session-validation-middleware)
  - [Flask](#flask)
  - [FastAPI](#fastapi)
  - [Django](#django)
  - [Management SDK (Python)](#management-sdk-python)
  - [Access keys / M2M (Python)](#access-keys--m2m-python)
- [Java](#java)
  - [Package changes](#package-changes-java)
  - [Client setup](#client-setup-java)
  - [Session validation](#session-validation-java)
  - [Spring Boot integration](#spring-boot-integration)
  - [Management SDK (Java)](#management-sdk-java)
  - [Access keys / M2M (Java)](#access-keys--m2m-java)
- [scp → scope across both languages](#scp--scope-across-both-languages)

---

## Python

### Package changes (Python)

| Okta package | Remove | Descope replacement |
|---|---|---|
| `okta-jwt-verifier` | Yes | `descope` |
| `python-jose` (used for Okta JWKS validation) | Yes | `descope` |
| `authlib` (OIDC client for Okta) | Depends | Keep if using OIDC compatibility path (update endpoints only) |
| `flask-oidc` | Yes | Custom middleware using `descope` SDK |
| `social-auth-app-django` with Okta backend | Yes | `descope` + custom auth backend |
| `okta` (management SDK) | Yes | `descope` management via `descope_client.mgmt.*` |

```bash
pip uninstall okta-jwt-verifier python-jose flask-oidc okta
pip install descope
```

---

### Client setup (Python)

```python
import os
from descope import DescopeClient, AuthException

# Reads DESCOPE_PROJECT_ID from environment automatically
descope_client = DescopeClient(project_id=os.environ.get("DESCOPE_PROJECT_ID"))
```

Set env vars:
- Remove: `OKTA_CLIENT_ID`, `OKTA_CLIENT_SECRET`, `OKTA_ISSUER`, `OKTA_AUDIENCE`, `OKTA_DOMAIN`
- Add: `DESCOPE_PROJECT_ID` (+ `DESCOPE_MANAGEMENT_KEY` for management operations)

---

### Session validation middleware

The core validation call is the same across frameworks. The token comes from the `DS` cookie or the `Authorization: Bearer` header.

```python
# Validate (raises on invalid/expired)
try:
    jwt_response = descope_client.validate_session(session_token)
    # jwt_response contains decoded claims: sub, email, roles, permissions, tenants, etc.
except AuthException as e:
    # 401 — token invalid or expired
    pass

# Validate and auto-refresh (preferred — handles token expiry transparently)
try:
    jwt_response = descope_client.validate_and_refresh_session(session_token, refresh_token)
except AuthException as e:
    pass
```

`jwt_response` is a dict of JWT claims. Access fields directly: `jwt_response["sub"]`, `jwt_response["email"]`, etc.

---

### Flask

```python
from functools import wraps
from flask import Flask, request, jsonify, g
from descope import DescopeClient, AuthException

app = Flask(__name__)
descope_client = DescopeClient(project_id=os.environ.get("DESCOPE_PROJECT_ID"))

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_token = request.cookies.get("DS") or \
            request.headers.get("Authorization", "").removeprefix("Bearer ")
        refresh_token = request.cookies.get("DSR")
        if not session_token:
            return jsonify({"error": "Unauthorized"}), 401
        try:
            g.user = descope_client.validate_and_refresh_session(session_token, refresh_token)
        except AuthException:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/api/protected")
@require_auth
def protected():
    # Access claims via "sessionToken" — reliable whether the session was validated or refreshed
    claims = g.user.get("sessionToken", g.user)
    return jsonify({"user": claims.get("email")})
```

**What changed vs. Okta:**
- Remove `flask-oidc` and its `@oidc.require_login` decorator
- Remove the `/callback` route (`/authorization-code/callback`)
- Remove `oidc.get_userinfo()` — user info is in `g.user` (decoded JWT claims) after `validate_and_refresh_session`
- `current_user.profile.login` → `g.user.get("sessionToken", {}).get("email")` — use `sessionToken` for reliable access across both validate and refresh paths (must be in JWT Template)

---

### FastAPI

```python
from fastapi import FastAPI, Depends, HTTPException, Cookie, Header
from descope import DescopeClient, AuthException
from typing import Optional

app = FastAPI()
descope_client = DescopeClient(project_id=os.environ.get("DESCOPE_PROJECT_ID"))

async def get_current_user(
    ds: Optional[str] = Cookie(None),
    dsr: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
):
    session_token = ds or (authorization.removeprefix("Bearer ") if authorization else None)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return descope_client.validate_and_refresh_session(session_token, dsr)
    except AuthException:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.get("/api/protected")
async def protected(user: dict = Depends(get_current_user)):
    claims = user.get("sessionToken", user)
    return {"email": claims.get("email")}
```

**What changed vs. Okta:**
- Remove `python-jose` / `okta-jwt-verifier` and their JWKS fetch+verify patterns
- Remove manual JWKS URL calls and key caching — the Descope SDK handles this
- Remove `Depends(oauth2_scheme)` + manual `jwt.decode()` — replace with `Depends(get_current_user)`
- `token["scp"]` → `token["scope"]` (may be array or space-separated string — see [scp vs scope](#scp--scope-across-both-languages))

**Alternative — JWKS swap only (no SDK):**
If the existing app uses `PyJWT` with Okta's JWKS URL directly, update to:
```python
jwks_url = f"https://api.descope.com/{os.environ['DESCOPE_PROJECT_ID']}/.well-known/jwks.json"
```
Then update scope-checking logic from `token["scp"]` to `token["scope"]`. No other code changes needed.

> **Note on PyJWKClient and User-Agent:** If using `PyJWT`'s `PyJWKClient` directly, add a custom
> User-Agent to JWKS requests — Descope's JWKS endpoint may reject the default `Python-urllib` UA:
> ```python
> import urllib.request
> opener = urllib.request.build_opener()
> opener.addheaders = [('User-agent', 'Mozilla/5.0')]
> urllib.request.install_opener(opener)
> ```

---

### Django

```python
# auth_middleware.py
from descope import DescopeClient, AuthException

descope_client = DescopeClient(project_id=os.environ.get("DESCOPE_PROJECT_ID"))

class DescopeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_token = request.COOKIES.get("DS")
        refresh_token = request.COOKIES.get("DSR")
        if session_token:
            try:
                request.user_claims = descope_client.validate_and_refresh_session(
                    session_token, refresh_token
                )
            except AuthException:
                request.user_claims = None
        else:
            request.user_claims = None
        return self.get_response(request)

# settings.py — add to MIDDLEWARE after SessionMiddleware
MIDDLEWARE = [
    ...
    "myapp.auth_middleware.DescopeMiddleware",
]
```

**What changed vs. Okta:**
- Remove `social-auth-app-django` with Okta backend from `INSTALLED_APPS` and `AUTHENTICATION_BACKENDS`
- Remove `SOCIAL_AUTH_OKTA_OAUTH2_*` settings
- Remove `OKTA_OIDC_*` settings
- Replace `request.user.social_auth.get(provider='okta-oauth2')` with `request.user_claims`
- No Django `User` model integration by default — manage user identity via JWT claims

---

### Management SDK (Python)

Use `descope_client.mgmt.*` for all management operations. Requires `DESCOPE_MANAGEMENT_KEY`.

**User batch import (migration):**
```python
from descope import DescopeClient, UserObj, AssociatedTenant

users = [
    UserObj(
        login_id="user@example.com",
        email="user@example.com",
        display_name="User Name",
        user_tenants=[AssociatedTenant("tenant-id", ["role-name"])],
        custom_attributes={"freshlyMigrated": True},
    ),
    # ... more users
]

try:
    resp = descope_client.mgmt.user.invite_batch(
        users=users,
        invite_url=None,
        send_mail=False,  # suppress invite emails during migration
        send_sms=False,
    )
except AuthException as e:
    print(f"Batch failed: {e}")
```

**Okta attribute mapping:**

| Okta `profile.*` field | `UserObj` parameter | Notes |
|---|---|---|
| `login` or `email` | `login_id` | Required; must be unique |
| `email` | `email` | |
| `firstName` | `given_name` | |
| `lastName` | `family_name` | |
| Custom profile fields | `custom_attributes` dict | Define schema in Console first |

**Individual user operations:**
```python
# Create single user
descope_client.mgmt.user.create(
    login_id="user@example.com",
    email="user@example.com",
    display_name="User Name",
)

# Update
descope_client.mgmt.user.update(
    login_id="user@example.com",
    display_name="New Name",
)

# Delete
descope_client.mgmt.user.delete("user@example.com")

# Search
resp = descope_client.mgmt.user.search_all(tenant_ids=["my-tenant-id"])
users = resp["users"]
```

**Roles:**
```python
# Check matched roles
matched_roles = descope_client.get_matched_roles(jwt_response, ["admin", "editor"])
matched_perms = descope_client.get_matched_permissions(jwt_response, ["read:data", "write:data"])
```

---

### Access keys / M2M (Python)

```python
# Exchange access key for a session (returns decoded JWT claims, not a raw string)
try:
    jwt_response = descope_client.exchange_access_key(access_key=access_key)
    # jwt_response["sessionToken"] — decoded JWT claims dict
    # Use with validate_permissions / validate_roles helpers:
    can_read = descope_client.validate_permissions(jwt_response, ["read:data"])
except AuthException as e:
    print(f"Exchange failed: {e}")
```

Create and manage access keys via `descope_client.mgmt.access_key.create(name=..., expire_time=...)`.

---

## Java

### Package changes (Java)

**Remove from pom.xml / build.gradle:**

```xml
<!-- Remove -->
<dependency>
    <groupId>com.okta.spring</groupId>
    <artifactId>okta-spring-boot-starter</artifactId>
</dependency>
<dependency>
    <groupId>com.okta.jwt</groupId>
    <artifactId>okta-jwt-verifier</artifactId>
</dependency>
<dependency>
    <groupId>com.okta.sdk</groupId>
    <artifactId>okta-sdk-api</artifactId>
</dependency>
```

**Add:**

```xml
<!-- Maven -->
<dependency>
    <groupId>com.descope</groupId>
    <artifactId>java-sdk</artifactId>
    <version>[1.0.0,)</version>
</dependency>
```

```groovy
// Gradle
implementation 'com.descope:java-sdk:[1.0.0,)'
```

**Remove from `application.properties` / `application.yml`:**
- `okta.oauth2.issuer`, `okta.oauth2.client-id`, `okta.oauth2.client-secret`
- `okta.oauth2.audience`, `okta.oauth2.scopes`
- `spring.security.oauth2.*` (Okta-specific)

**Add:**
```properties
DESCOPE_PROJECT_ID=YOUR_PROJECT_ID
DESCOPE_MANAGEMENT_KEY=YOUR_MANAGEMENT_KEY  # management operations only
```

---

### Client setup (Java)

```java
import com.descope.client.DescopeClient;
import com.descope.client.Config;
import com.descope.exception.DescopeException;
import com.descope.model.jwt.Token;
import com.descope.sdk.auth.AuthenticationService;

// Reads DESCOPE_PROJECT_ID from env automatically
DescopeClient descopeClient = new DescopeClient();

// Or explicitly
DescopeClient descopeClient = new DescopeClient(
    Config.builder().projectId(System.getenv("DESCOPE_PROJECT_ID")).build()
);

// With management key (for management operations)
DescopeClient descopeClient = new DescopeClient(
    Config.builder()
        .projectId(System.getenv("DESCOPE_PROJECT_ID"))
        .managementKey(System.getenv("DESCOPE_MANAGEMENT_KEY"))
        .build()
);

AuthenticationService authService = descopeClient.getAuthenticationServices().getAuthService();
```

---

### Session validation (Java)

```java
// Validate only (throws DescopeException if invalid or expired)
try {
    Token token = authService.validateSessionWithToken(sessionToken);
    String userId = token.getId();
} catch (DescopeException de) {
    // 401
}

// Refresh only (when you know the session is expired)
try {
    Token token = authService.refreshSessionWithToken(refreshToken);
} catch (DescopeException de) {
    // 401
}

// Validate and auto-refresh (preferred — handles expiry transparently)
try {
    Token token = authService.validateAndRefreshSessionWithTokens(sessionToken, refreshToken);
} catch (DescopeException de) {
    // 401
}
```

`Token` exposes decoded claims: `token.getId()` (sub), `token.getClaims()` (full claims map), etc.

---

### Spring Boot integration

#### Replacing `okta-spring-boot-starter`

Remove `@EnableOAuth2Sso` and the Okta starter autoconfiguration. Replace with a Descope
`HandlerInterceptor`:

```java
// DescopeAuthInterceptor.java
import com.descope.client.DescopeClient;
import com.descope.exception.DescopeException;
import com.descope.model.jwt.Token;
import com.descope.sdk.auth.AuthenticationService;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import java.util.Arrays;

@Component
public class DescopeAuthInterceptor implements HandlerInterceptor {

    private final AuthenticationService authService;

    public DescopeAuthInterceptor(DescopeClient descopeClient) {
        this.authService = descopeClient.getAuthenticationServices().getAuthService();
    }

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response,
                             Object handler) throws Exception {
        String sessionToken = extractToken(request);
        if (sessionToken == null) {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED);
            return false;
        }
        try {
            Token token = authService.validateAndRefreshSessionWithTokens(
                sessionToken, extractCookie(request, "DSR")
            );
            request.setAttribute("descopeToken", token);
            return true;
        } catch (DescopeException de) {
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED);
            return false;
        }
    }

    private String extractToken(HttpServletRequest request) {
        // Try DS cookie first
        String cookie = extractCookie(request, "DS");
        if (cookie != null) return cookie;
        // Fall back to Authorization header
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            return header.substring(7);
        }
        return null;
    }

    private String extractCookie(HttpServletRequest request, String name) {
        if (request.getCookies() == null) return null;
        return Arrays.stream(request.getCookies())
            .filter(c -> name.equals(c.getName()))
            .map(Cookie::getValue)
            .findFirst()
            .orElse(null);
    }
}
```

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final DescopeAuthInterceptor descopeAuthInterceptor;

    public WebConfig(DescopeAuthInterceptor descopeAuthInterceptor) {
        this.descopeAuthInterceptor = descopeAuthInterceptor;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(descopeAuthInterceptor)
            .addPathPatterns("/api/**")       // protect API routes
            .excludePathPatterns("/api/public/**", "/login", "/logout");
    }
}
```

Access claims in controllers:
```java
@GetMapping("/api/profile")
public ResponseEntity<?> profile(HttpServletRequest request) {
    Token token = (Token) request.getAttribute("descopeToken");
    return ResponseEntity.ok(token.getClaims());
}
```

#### Replacing Spring Security OAuth2 resource server

If the app used `spring-security-oauth2-resource-server` to validate Okta JWTs, the minimal
change is updating the JWKS URI and issuer in `application.properties`:

```properties
# Remove:
spring.security.oauth2.resourceserver.jwt.issuer-uri=https://YOUR_DOMAIN.okta.com/oauth2/default

# Add:
spring.security.oauth2.resourceserver.jwt.jwk-set-uri=https://api.descope.com/${DESCOPE_PROJECT_ID}/.well-known/jwks.json
spring.security.oauth2.resourceserver.jwt.issuer-uri=https://api.descope.com/${DESCOPE_PROJECT_ID}
```

Then update scope-checking code from `token.getClaimAsStringList("scp")` to
`token.getClaimAsStringList("scope")` (or handle space-separated string — see [scp vs scope](#scp--scope-across-both-languages)).

**For a Spring Filter approach:** See [github.com/descope/java-spring](https://github.com/descope/java-spring)
for the official Descope Spring Framework middleware example.

---

### Management SDK (Java)

```java
import com.descope.sdk.mgmt.UserService;
import com.descope.model.user.request.UserRequest;
import com.descope.model.user.request.BatchUserRequest;
import com.descope.model.user.response.UsersBatchResponse;

UserService us = descopeClient.getManagementServices().getUserService();

// Create single user
try {
    us.create("user@example.com",
        UserRequest.builder()
            .email("user@example.com")
            .displayName("User Name")
            .build());
} catch (DescopeException de) { /* handle */ }

// Batch create (for migration — does not send invite emails)
try {
    List<BatchUserRequest> users = new ArrayList<>();
    users.add(BatchUserRequest.builder()
        .loginId("user@example.com")
        .email("user@example.com")
        .displayName("User Name")
        .givenName("First")
        .familyName("Last")
        .build());
    UsersBatchResponse result = us.createBatch(users);
    // result.getCreatedUsers() / result.getFailedUsers()
} catch (DescopeException de) { /* handle */ }

// Update
try {
    us.update("user@example.com",
        UserRequest.builder().displayName("New Name").build());
} catch (DescopeException de) { /* handle */ }

// Delete
try {
    us.delete("user@example.com");
} catch (DescopeException de) { /* handle */ }
```

**Okta attribute mapping:**

| Okta `profile.*` field | `UserRequest.builder().*` method | Notes |
|---|---|---|
| `login` or `email` | `BatchUserRequest.builder().loginId(...)` | Required; must be unique |
| `email` | `.email(...)` | |
| `firstName` | `.givenName(...)` | |
| `lastName` | `.familyName(...)` | |
| Display name | `.displayName(...)` | Optional; combine first+last if no separate field |
| Custom profile fields | `.customAttributes(Map)` | Define schema in Console first |

---

### Access keys / M2M (Java)

```java
import com.descope.sdk.auth.AuthenticationService;
import com.descope.model.jwt.Token;

AuthenticationService as = descopeClient.getAuthenticationServices().getAuthService();

try {
    Token token = as.exchangeAccessKey(accessKey);
    String jwt = token.getJwt();
} catch (DescopeException de) {
    // Handle
}
```

Manage access keys (create, deactivate, delete):
```java
AccessKeyService aks = descopeClient.getManagementServices().getAccessKeyService();
try {
    AccessKeyResponse resp = aks.create("my-service-key", 0,
        Arrays.asList("RoleName"), null);
    String cleartext = resp.getCleartext(); // save securely — not returned again
} catch (DescopeException de) { /* handle */ }
```

---

## scp → scope across both languages

Okta access tokens use `scp` (JSON array). Descope uses `scope` (array or space-separated string).
Any backend code that reads the scope claim must be updated — this is a silent correctness bug.

**Python:**
```python
# Remove
scopes = jwt_response.get("scp", [])

# Add (handle both array and string)
scope_val = jwt_response.get("scope", "")
scopes = scope_val if isinstance(scope_val, list) else scope_val.split()
```

**Java (manual claim reading):**
```java
// Remove
List<String> scopes = (List<String>) claims.get("scp");

// Add (handle both array and space-separated string)
Object scopeVal = claims.get("scope");
List<String> scopes;
if (scopeVal instanceof List) {
    scopes = (List<String>) scopeVal;
} else if (scopeVal instanceof String) {
    scopes = Arrays.asList(((String) scopeVal).split(" "));
} else {
    scopes = Collections.emptyList();
}
```

**Java (Spring Security OAuth2):**
Spring Security's `JwtGrantedAuthoritiesConverter` reads `scope` by default (not `scp`), so it
already handles the Descope format. No change needed if you use `@PreAuthorize("hasAuthority('SCOPE_read:data')")`.
If you had a custom converter reading `scp`, update it to read `scope`.
