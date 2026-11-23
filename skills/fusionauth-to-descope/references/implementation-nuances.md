# Descope Migration: Implementation Notes (FusionAuth → Descope)

## Contents

**General Insights — Architecture & Flow**
- [FusionAuth runs the OAuth server; Descope replaces it, not just the SDK](#fusionauth-runs-the-oauth-server-descope-replaces-it-not-just-the-sdk)
- [Four integration styles](#four-integration-styles)
- [Keep the OIDC library, or adopt the Descope SDK](#keep-the-oidc-library-or-adopt-the-descope-sdk)
- [No drop-in middleware](#no-drop-in-middleware)
- [What disappears entirely](#what-disappears-entirely)

**General Insights — Feature Mapping: FusionAuth → Descope**
- [Migrating users and tenants](#migrating-users-and-tenants)
- [Password hash mapping](#password-hash-mapping)
- [Token claim mapping](#token-claim-mapping)
- [Tenants: Projects or Tenants](#tenants-projects-or-tenants)
- [Applications, registrations, roles, and groups](#applications-registrations-roles-and-groups)
- [Lambdas](#lambdas)
- [Webhooks](#webhooks)
- [Identity providers, SSO, and SCIM](#identity-providers-sso-and-scim)
- [Entities and M2M](#entities-and-m2m)
- [Management API mapping](#management-api-mapping)

**Framework Recipes**
- [Next.js](#nextjs)
- [React](#react)
- [Node.js backend](#nodejs-backend)
- [Python backend](#python-backend)
- [Go backend](#go-backend)
- [Java (Spring) and .NET](#java-spring-and-net)
- [Mobile](#mobile)

**General Insights — Common Gotchas**
- [Cookie names: DS and DSR](#cookie-names-ds-and-dsr)
- [Audience validation requires explicit setup](#audience-validation-requires-explicit-setup)
- [Logout requires two steps](#logout-requires-two-steps)
- [Env var reduction](#env-var-reduction)
- [Approved Domains: domain only](#approved-domains-domain-only)
- [Testing checklist](#testing-checklist)

> **See also:** `flows-and-widgets.md` in this directory — FusionAuth→Descope lingo map, Flow structure and templates, the self-service and admin surface mapping table, Widget types, SSO Setup Suite, and the Console-vs-code decision guide.

> **Source of truth:** for anything FusionAuth-specific, verify against
> [fusionauth.io/docs](https://fusionauth.io/docs). The docs source is public at
> [github.com/FusionAuth/fusionauth-site](https://github.com/FusionAuth/fusionauth-site)
> (`astro/src/content/docs/`), which is easier to read than the rendered pages. FusionAuth's database
> schema changes between versions — check the schema for the customer's exact version before running
> any SQL below. For anything Descope-specific, use the Descope MCP or
> [docs.descope.com](https://docs.descope.com).

---

## General Insights

**— Architecture & Flow —**

### FusionAuth runs the OAuth server; Descope replaces it, not just the SDK

FusionAuth is a full OAuth 2.0 / OIDC authorization server. Apps redirect to `/oauth2/authorize`,
exchange codes at `/oauth2/token`, read `/oauth2/userinfo`, and validate tokens against
`/.well-known/jwks.json` (or a shared HMAC secret). FusionAuth's own frontend SDKs add a thin layer on
top: they redirect to the hosted login, and a **Hosted Backend** (`/app/login`, `/app/callback`,
`/app/refresh`, `/app/me`, `/app/logout`) — built into FusionAuth since 1.45.0, or run by the app —
exchanges the code and keeps tokens in `app.at` / `app.rt` / `app.idt` / `app.at_exp` cookies.

Descope plays the same role. The frontend
([Descope Flows](https://docs.descope.com/flows) via
[web components](https://docs.descope.com/client-sdk/descope-components) or
[client SDKs](https://docs.descope.com/client-sdk/initialize-sdk)) runs the ceremony and stores JWTs
in `DS` (session) and `DSR` (refresh) cookies; the backend
[validates those JWTs](https://docs.descope.com/sessions/validation/backend). Descope is also an OIDC
provider, so a standard OIDC client can talk to it directly.

The practical consequence: a FusionAuth migration replaces a server the team may operate (app
container, database, search cluster) as well as SDK calls. Count the decommission as part of the plan.

### Four integration styles

Identify which of these the app uses — often more than one:

| Style | Signals | Descope target |
|---|---|---|
| FusionAuth frontend SDK + Hosted Backend | `@fusionauth/react-sdk` / `vue-sdk` / `angular-sdk`, `serverUrl`, `app.at` cookie reads | Descope client SDK (`oidcConfig` hosted login or embedded Flow) + backend `validateSession()` |
| FusionAuth frontend SDK with DPoP | `useDpop: true`, `dpopFetch` | Same as above; DPoP plumbing goes away |
| Generic OIDC library | `next-auth`, `openid-client`, Passport, Spring Security, ASP.NET, `authlib`, AppAuth | Keep the library and repoint it at Descope, or adopt the Descope SDK |
| Custom form on the Login API | `POST /api/login`, `client.login(...)` | Embedded Flow (recommended), or SDK password methods / BYOS |

A fifth, orthogonal surface is **Management API usage** (`FusionAuthClient`), which maps to the
Descope Management SDK regardless of the login style.

### Keep the OIDC library, or adopt the Descope SDK

For generic-OIDC apps this is the biggest decision, and it belongs to the user. Ask it explicitly.

- **Keep the library.** Register a Descope
  [OIDC Federated Application](https://docs.descope.com/identity-federation/applications/oidc-apps).
  The issuer is `https://api.descope.com/<ProjectID>` (or the custom domain), discovery is at
  `<issuer>/.well-known/openid-configuration`, the client ID is the Project ID, and the client secret
  is a Descope Access Key. Register the app's existing callback URL on the Federated App. Code changes
  shrink to configuration plus claim reads (Descope's claims differ). Verify these values with the MCP
  before writing them — they are the kind of detail that changes.
- **Adopt the Descope SDK.** More code changes up front, but the app gets Flows embedded in-page,
  Widgets, `useSession()` / `useUser()`, and SDK session validation. Use `oidcConfig` on the provider
  to keep the redirect-style UX.

Either way, match the existing login model: an app whose users leave to FusionAuth's hosted page
should land on Descope's hosted page, not an embedded Flow, unless the user asks to change it.

### No drop-in middleware

Most FusionAuth backends validate tokens with a generic JWT library (`jose`, `jsonwebtoken`, `PyJWT`,
`golang-jwt`, Spring resource server, `AddJwtBearer`) or the client library's `validateJWT`. Descope
publishes a middleware only for Next.js (`authMiddleware` from `@descope/nextjs-sdk/server`). For
everything else, each becomes custom code:

1. Read the `DS` cookie (or the `Authorization` header for API clients).
2. Call `validateSession()` / `validate_session()` / `ValidateSessionWithToken()`.
3. Attach the resulting claims to the request context.
4. Check roles/permissions with the SDK's validation helpers.

Standards-based resource servers (Spring, ASP.NET) can instead be repointed at Descope's issuer and
JWKS — a config change — as long as the role-claim mapping is updated.

### What disappears entirely

Worth calling out in the plan, because it is real scope *removal*:

- **The FusionAuth server** — the `fusionauth/fusionauth-app` container or VM, its PostgreSQL/MySQL database, and its Elasticsearch/OpenSearch cluster (self-hosted), or the FusionAuth Cloud subscription. Decommission after the transition, not at code cutover.
- **Kickstart** — `kickstart.json`, `FUSIONAUTH_APP_KICKSTART_FILE`, and any local-dev compose service on port 9011.
- **Hosted Backend plumbing** — `/app/*` routes in the app's own server (e.g. from `fusionauth-javascript-sdk-express`), `app.*` cookie handling, `autoRefreshSecondsBeforeExpiry` timers.
- **DPoP key handling** — `useDpop`, `dpopFetch`, proof generation.
- **FreeMarker themes and email templates** — replaced by Flows, Styles, and Messaging Templates.
- **FusionAuth Terraform** — replaced by Descope Terraform if the team wants IaC.

**— Feature Mapping —**

### Migrating users and tenants

**The agent writes the migration script.** Build it from the queries, endpoints, and mapping below,
fitted to the user's own tenants, applications, and `user.data` fields. Descope's
[descope-migration](https://github.com/descope/descope-migration) repo has no FusionAuth module, and
there is no FusionAuth guide in Descope's migration docs at the time of writing — check before linking
to one. **Never tell the user to open a guide you have not confirmed exists.**

#### The constraint that shapes everything

FusionAuth's API **never returns password hashes** — the user response has no `password`, `salt`,
`encryptionScheme`, or `factor` fields. Hashes can only be *written* through the API (`POST
/api/user/import`). FusionAuth's own [export guide](https://fusionauth.io/docs/migrate/export) says to
read the database:

- **Self-hosted:** query the database directly. In current versions the hash lives in the
  **`identities`** table, joined to `users`.
- **FusionAuth Cloud:** open a support ticket for a database export. FusionAuth documents that a
  support request is required because the export contains password hashes, and that it is free for
  customers leaving FusionAuth on any plan. The result is a PostgreSQL dump — restore it into a local
  PostgreSQL and run the same queries.

So unlike most providers, the default plan **keeps passwords**. The open questions are how long the
export takes to obtain, and which hash schemes are present.

#### First queries to run (self-hosted, or against the restored Cloud dump)

```sql
-- Users per hash scheme and factor (sizes the JIT fallback)
SELECT i.encryption_scheme, i.factor, COUNT(*)
FROM identities i
GROUP BY i.encryption_scheme, i.factor
ORDER BY COUNT(*) DESC;

-- Users per tenant
SELECT t.name, COUNT(*)
FROM users u JOIN tenants t ON t.id = u.tenants_id
GROUP BY t.name;

-- Same email in more than one tenant (the merge question)
SELECT lower(i.email) AS email, COUNT(DISTINCT u.tenants_id) AS tenants
FROM identities i JOIN users u ON u.id = i.users_id
WHERE i.email IS NOT NULL
GROUP BY lower(i.email)
HAVING COUNT(DISTINCT u.tenants_id) > 1;
```

Column and table names vary by FusionAuth version (older versions kept credentials on `users`, and
newer versions may store more than one identity per user). Read the schema for the customer's version
first, and adjust. Never print hashes to the terminal or into the conversation; write them only to the
import file.

#### Path 1 — Full migration with password hashes (default)

Create objects in Descope in **dependency order: tenants → permissions → roles → users**. Users cannot
be created with tenant and role assignments that do not exist yet.

The user export query, from FusionAuth's export guide, extended with the fields the import needs:

```sql
SELECT u.id, u.tenants_id, u.active, u.first_name, u.middle_name, u.last_name, u.full_name,
       u.image_url, u.mobile_phone, u.data, u.insert_instant,
       i.email, i.username, i.verified,
       i.encryption_scheme, i.password, i.salt, i.factor
FROM identities i
JOIN users u ON u.id = i.users_id;
```

Role assignments — registration roles, then group roles that apply because the user is registered:

```sql
-- Registrations and their roles
SELECT ur.users_id, ur.applications_id, ar.name AS role
FROM user_registrations ur
LEFT JOIN user_registrations_application_roles urar ON urar.user_registrations_id = ur.id
LEFT JOIN application_roles ar ON ar.id = urar.application_roles_id;

-- Group roles (apply only for applications the user is registered to)
SELECT gm.users_id, ar.applications_id, ar.name AS role
FROM group_members gm
JOIN group_application_roles gar ON gar.groups_id = gm.groups_id
JOIN application_roles ar ON ar.id = gar.application_roles_id;
```

Verify each join column against the schema before running. The script then:

- Filters to the Application(s) being migrated, and to users registered for them (unless the team decided otherwise).
- Unions registration roles and group roles per user, dropping group roles for unregistered applications, then maps each role name through the agreed rename table (for cross-application collisions).
- Maps tenants per the triage decision; merges same-email users by the agreed rule.
- Maps each hash through the table in [Password hash mapping](#password-hash-mapping). Unsupported schemes: no `hashedPassword`, set `freshlyMigrated: true`.
- Sets `customAttributes.fusionauthId` to the FusionAuth user UUID, plus one attribute per migrated `user.data` field.
- Imports `active = false` users as disabled.

Before the first run: **pre-define every custom attribute in the Descope Console.** Descope rejects
custom attributes that are not in the project schema, and values must match the declared type (send
`true`, not `"true"`, for a boolean). Then dry-run against a **dev** project and sign in as test users
covering each hash scheme before running staging and production.

Users created or changed in FusionAuth after the export need a **delta import** right after the
switch (filter on `insert_instant` / `last_update_instant` greater than the export time), or a
sign-up freeze during the switch.

#### Path 2 — JIT migration with a Generic HTTP Connector

For users whose hash scheme doesn't import, when the hash export is delayed, or as the whole strategy:

1. The user enters email (or username) and password in the Descope Flow.
2. A [Generic HTTP Connector](https://docs.descope.com/connectors/connector-configuration-guides/network/generic-http)
   step calls `POST {FUSIONAUTH_URL}/api/login` with `{ "loginId", "password", "applicationId" }`,
   authenticated with a FusionAuth API key limited to `/api/login` (add `X-FusionAuth-TenantId` when
   several tenants exist).
3. On success, the Flow creates or updates the Descope user, stores the password, and issues a
   Descope session.
4. Subsequent sign-ins authenticate directly against Descope.

FusionAuth's Login API status codes matter here. **200** is a full success. **202** (user not
registered for the application), **203** (password change required), **212** (email not verified),
**213** (registration not verified), and **242** (two-factor required) all mean the password was
correct — decide per code whether to accept the sign-in (242 in particular: Descope's Flow should then
run its own MFA step). **404** is unknown user *or* wrong password; **409** blocked by a user action;
**410** expired; **423** locked. Map each to a Flow branch rather than treating "not 200" as a wrong
password. Note that each successful call also records a FusionAuth login (and fires
`user.login.success` webhooks) — tell the user if webhook consumers care.

Which action stores the password depends on whether the user already exists in Descope:

- **User new to Descope** (created in FusionAuth after the export, or a JIT-only migration): on a
  successful connector response the Flow runs **Sign Up / Password**.
- **Imported user (`freshlyMigrated`)**: **Sign Up / Password fails** because the user exists. After
  FusionAuth accepts the password, sign the user in with OTP or magic link, then run **Update
  Password**, then clear `freshlyMigrated`.

Descope documents this pattern for [Keycloak](https://docs.descope.com/migrate/guides/keycloak),
[Cognito](https://docs.descope.com/migrate/guides/cognito), and
[Azure AD B2C](https://docs.descope.com/migrate/guides/azure-ad-b2c). The FusionAuth shape is
identical; only the validating endpoint changes. Confirm current Flow action names against the docs.

#### Path 3 — JIT migration with FusionAuth as a custom OIDC provider

Configure FusionAuth as a
[custom OAuth/OIDC provider](https://docs.descope.com/auth-methods/oauth/providers/custom-provider)
using a FusionAuth Application's client ID and secret and the tenant's discovery document
(`/.well-known/openid-configuration/{tenantId}`). Users authenticate through FusionAuth's hosted login
— MFA included — and Descope provisions them from the ID token. Add a
[condition](https://docs.descope.com/flows/conditions) routing already-provisioned users to
Descope-native auth. Note that the default ID token carries no roles; read them from the access token
claims or a UserInfo populate lambda, or import roles separately.

#### Configuration export (Management API)

```bash
# FusionAuth API keys go in Authorization AS-IS — no "Bearer" prefix.
# Add X-FusionAuth-TenantId when the instance has several tenants and the call is tenant-scoped.
FA=https://auth.example.com

curl -s "$FA/api/tenant"            -H "Authorization: $FUSIONAUTH_API_KEY"   # tenants (policies, keys, themes)
curl -s "$FA/api/application"       -H "Authorization: $FUSIONAUTH_API_KEY"   # applications incl. roles, OAuth config
curl -s "$FA/api/group"             -H "Authorization: $FUSIONAUTH_API_KEY"   # groups incl. application roles
curl -s "$FA/api/identity-provider" -H "Authorization: $FUSIONAUTH_API_KEY"   # social + enterprise IdPs
curl -s "$FA/api/lambda"            -H "Authorization: $FUSIONAUTH_API_KEY"   # lambda source code
curl -s "$FA/api/webhook"           -H "Authorization: $FUSIONAUTH_API_KEY"   # webhooks and their events
curl -s "$FA/api/connector"         -H "Authorization: $FUSIONAUTH_API_KEY"   # connectors (global key)
curl -s "$FA/api/entity/type"       -H "Authorization: $FUSIONAUTH_API_KEY"   # entity types + permissions

# User profiles without hashes (only when the database route isn't available):
curl -s -X POST "$FA/api/user/search" \
  -H "Authorization: $FUSIONAUTH_API_KEY" -H "Content-Type: application/json" \
  -H "X-FusionAuth-TenantId: $TENANT_ID" \
  -d '{"search":{"queryString":"*","numberOfResults":500,"startRow":0,"sortFields":[{"name":"email","order":"asc"}],"accurateTotal":true}}'
```

User search paging depends on the search engine. The **database** engine (the default since 1.16.0)
pages with `startRow` / `numberOfResults`. **Elasticsearch** before 1.48.0 stops at 10,000 results;
from 1.48.0, each response carries a `nextResults` token — send `{"search":{"numberOfResults":N,
"nextResults":"<token>"}}` (nothing else alongside it) until it is absent. Always compare the exported
count to the total. Users and registrations come back embedded (`user.registrations[]`), and group
memberships as `user.memberships[]`.

#### Field mapping into Descope

| FusionAuth | Descope (`/v1/mgmt/user/create/batch`) |
|---|---|
| `email` (or `username` if users sign in with it) | `loginId` (required, unique per project) |
| `email` | `email` |
| `username` (when `email` is the login ID) | `additionalIdentifiers` (verify the current field name) |
| `verified` | `verifiedEmail` |
| `mobilePhone` | `phone` (E.164 only), `verifiedPhone` only if FusionAuth verified it |
| `firstName` / `middleName` / `lastName` / `fullName` | `givenName` / `middleName` / `familyName` / `name` |
| `imageUrl` | `picture` |
| `id` (UUID) | `customAttributes.fusionauthId` |
| `data.*` | `customAttributes.*` (define first; flatten nested objects) |
| `tenantId` (B2B mapping) | `userTenants[].tenantId` |
| Registration roles + applicable group roles | `roleNames` (project-level) or `userTenants[].roleNames` |
| `active = false` | Disabled status (verify the batch field, or disable after create) |
| Hash, salt, scheme, factor | `hashedPassword` (see below) |
| TOTP authenticator secret | `seed` (base32) |
| `insertInstant` | `createdTime` (unix seconds; batch endpoint) |

Import with `POST https://api.descope.com/v1/mgmt/user/create/batch` and
`Authorization: Bearer <ProjectID>:<ManagementKey>`, minding the
[rate limits](https://docs.descope.com/rate-limiting). The payload fields are in the
[Batch Create Users](https://docs.descope.com/api/management/users/batch-create-users) API reference;
the [custom migration guide](https://docs.descope.com/migrate/custom) shows the hash formats. Batches
that set a cleartext `password` are capped at 100 users; `hashedPassword` batches are not.

#### Data-quality issues to expect

- **Same email in several tenants.** Separate users in FusionAuth; one user in Descope if tenants become Descope tenants. Merge by rule.
- **Mixed hash schemes.** Tenants can change the default scheme, and `modifyEncryptionSchemeOnLogin` (off by default) re-hashes only users who sign in. Expect several schemes and factors in one database.
- **Users registered for nothing.** They authenticate in FusionAuth but get no roles. Decide whether to import them.
- **Username-only users.** No email; `loginId` must be the username.
- **Unverified emails.** Import with `verifiedEmail: false`; a Flow that requires verified email will prompt them.
- **Connector-sourced users.** If a Connector authenticates against a legacy system on every login, FusionAuth may hold no usable hash for those users.
- **Phone numbers.** FusionAuth doesn't enforce E.164 on `mobilePhone`; normalize or drop.

#### Dual token validation

Unless the cutover is a hard big-bang switch, validate **both** Descope and FusionAuth tokens during
the transition: inspect `iss` (or `kid`) to pick the verifier, then verify. This is mandatory when
FusionAuth sessions must keep working during a JIT transition. See
[session migration](https://docs.descope.com/migrate/session-migration) — currently **beta** and
documented only for Auth0, Okta, or a custom-built solution; otherwise hand-roll the check.

**Security caveat:** reading `iss` / `kid` from the *unverified* token is acceptable **only to choose
which verifier to run**. Each branch must then verify the signature (FusionAuth: its JWKS, or the HMAC
secret for HS256 installs; Descope: its SDK) and pin the expected issuer and audience. Never route on
`alg` — that invites algorithm-confusion attacks. Never fall through from a failed Descope verification
to the FusionAuth branch without that branch fully verifying. Schedule the removal of the FusionAuth
branch as an explicit follow-up after cutover.

### Password hash mapping

FusionAuth stores hash and salt as **base64**, with `factor` as the iteration count (or bcrypt cost).
Descope's `hashedPassword` formats are documented in the
[custom migration guide](https://docs.descope.com/migrate/custom#importing-passwords).

| FusionAuth `encryption_scheme` | Descope `hashedPassword` | Notes |
|---|---|---|
| `salted-pbkdf2-hmac-sha256` (default, factor usually 24000) | `{"pbkdf2":{"hash":"<base64>","salt":"<base64>","iterations":<factor>,"type":"sha256"}}` | Direct. 256-bit derived key. |
| `salted-pbkdf2-hmac-sha512-512` | `{"pbkdf2":{..., "type":"sha512"}}` | Direct. 512-bit key from HMAC-SHA512. |
| `salted-pbkdf2-hmac-sha256-512` | `{"pbkdf2":{..., "type":"sha256"}}` | **Test first.** HMAC-SHA256 with a 512-bit derived key; Descope has no key-length field and likely infers it from the hash length. If test sign-ins fail, use JIT. |
| `bcrypt` | `{"bcrypt":{"hash":"$2a$<cost>$<22-char salt><31-char hash>"}}` | FusionAuth stores the bcrypt salt and hash in separate columns, in bcrypt's own base64 alphabet, with `factor` = cost. Rebuild the full string (zero-pad cost to two digits). Test with a real sign-in. |
| `phpass-md5`, `phpass-sha512` | `{"phpass":{"hash","salt","iterations","type":"md5"|"sha512"}}` | Typically users FusionAuth imported from WordPress/PHP apps. Test first. |
| `salted-md5` | — | Descope documents no salted MD5 support. JIT or reset. |
| `salted-sha256` | `{"sha":{...}}` only if factor = 1 | FusionAuth hashes `password + base64Decode(salt)`, iterated `factor` times. Descope's `sha` format is single-pass with a prefix/suffix salt; usable only when factor is 1, and test first. Otherwise JIT. |
| `salted-hmac-sha256` | — | No documented Descope equivalent. JIT or reset. |
| Custom plugin schemes | — | JIT or reset. |

The safest check is empirical: for each scheme present, import one test user whose password you know
into a dev project and sign in. Never use a real user's password for this.

**TOTP secrets.** Descope's batch import accepts a base32 `seed`. Find where the customer's FusionAuth
version stores authenticator secrets, and check the encoding — FusionAuth's two-factor APIs expose
secrets as base64 with a separate base32 form, so convert to base32 if the stored value is base64.
Test one user with a real authenticator before importing everyone.

### Token claim mapping

| Field | FusionAuth claim | Descope |
|---|---|---|
| User ID | `sub` (FusionAuth UUID) | `sub` — a **different ID**; keep `fusionauthId` as a custom attribute |
| Email | `email` | **Not in JWT by default.** Add via [JWT Templates](https://docs.descope.com/management/token/jwt-templates). |
| Email verified | `email_verified` | Not in JWT by default; on the user object as `verifiedEmail`. |
| Username | `preferred_username` | Not in JWT by default; add via JWT Template if read. |
| Roles | `roles` (for the requesting application) | `roles` (project-level) or `tenants.<id>.roles` |
| Tenant | `tid` | `dct` (active tenant) / `tenants` (memberships) |
| Application | `applicationId`, `aud` | **Not present by default.** Add via JWT Template only if the app reads it. |
| Auth method | `authenticationType` (`PASSWORD`, `PASSWORDLESS`, `GOOGLE`, …) | `amr` |
| Session | `sid` | Not present by default. |
| Token type / grant | `tty`, `gty` | Not present. |
| Scope | `scope` | Present for Inbound App tokens; not on standard session tokens. |
| Custom claims | Added by the JWT populate lambda | JWT Template claims or Flow custom claims |
| — | — | `drn` (Descope-specific) |

Grep for the populate lambda, not just for claim reads — its source is the only complete list of
custom claims.

### Tenants: Projects or Tenants

See SKILL.md Step 3 → *Tenants*. Implementation notes:

- **Environment tenants → Projects.** Run the import once per project, filtered by `tenants_id`. Users don't merge.
- **Customer tenants → Descope tenants.** Create each Descope tenant with the FusionAuth tenant UUID as its ID (Descope lets you set the tenant ID at creation — verify) or store the UUID in a tenant custom attribute, so the app's own tables can keep referencing it.
- Per-tenant FusionAuth settings to inventory: password policy, MFA policy, session/token lifetimes, email templates, theme, issuer, signing keys, connector policies, registration settings. Each becomes a Descope tenant setting, a Flow condition on the tenant, or "not supported per tenant."

### Applications, registrations, roles, and groups

- `GET /api/application` returns each Application's `roles[]` (`name`, `isDefault`, `isSuperRole`, `description`). Build the role list from it, grouped by Application, and resolve name collisions before creating anything.
- A registration with no roles still means "may use this app." If that gate matters, create an explicit role for it.
- Groups grant roles from one or more Applications to members, **only for Applications the member is registered to**. Flatten accordingly.
- If the app reads `memberships` or a lambda put group names into the token, store group names in a custom attribute (array) and expose them via JWT Template.

### Lambdas

Export with `GET /api/lambda` and read every body. Typical translations:

```javascript
// FusionAuth JWT populate lambda
function populate(jwt, user, registration, context) {
  jwt.plan = user.data.plan;
  jwt.orgId = registration.data.orgId;
}
```

becomes a JWT Template with `"plan": "{{user.customAttributes.plan}}"` (verify the placeholder syntax
in the project's templates) and a decision about `registration.data.orgId` — usually a tenant ID or a
user custom attribute after migration.

```javascript
// FusionAuth login validation lambda
function validate(result, user, registration, context) {
  if (user.data.suspended) {
    result.errors.generalErrors = [{ code: "[Suspended]", message: "Account suspended" }];
  }
}
```

becomes a Flow Condition after authentication on `user.customAttributes.suspended`, branching to an
error screen — or, simpler, disabling those users at import.

Lambdas that call out (`fetch`, FusionAuth's "lambda HTTP connect") become Connector steps. Preserve
the failure behavior: a lambda that throws fails the event, so the Connector should fail closed unless
the user decides otherwise.

### Webhooks

- Export with `GET /api/webhook`; note `eventsEnabled`, which tenants each webhook applies to, and whether events are **transactional**.
- Non-transactional consumers (sync to the app DB, analytics) → Descope Audit Webhook or a Connector. Rewrite the signature check: FusionAuth signs with a JWT in `X-FusionAuth-Signature-JWT` carrying `request_body_sha256`; Descope uses its own scheme.
- Transactional consumers (can block user creation, registration, login) → a Connector + Condition inside the Flow that performs the action.
- Map event payloads deliberately: FusionAuth's `event.user` shape differs from Descope's audit event shape, so handlers need rewriting, not just repointing.

### Identity providers, SSO, and SCIM

- `GET /api/identity-provider` returns each IdP's type, enabled applications, managed domains, tenant configuration, claim mappings, reconcile lambda ID, and (for SAML) IdP endpoint and certificate key ID. Export the certificate from `GET /api/key/{id}`.
- Social IdPs: copy client ID and secret into the matching Descope OAuth provider; add Descope's callback URL at the provider.
- Enterprise OIDC/SAML: one Descope tenant SSO configuration per customer IdP. Follow [SSO migration](https://docs.descope.com/migrate/sso) to avoid customer-side reconfiguration where possible.
- Reconcile lambdas that map IdP claims to roles → Descope SSO group/attribute-to-role mapping.
- SCIM: re-point each customer directory to Descope's SCIM endpoint for its tenant; translate converter lambdas into Descope SCIM attribute mapping; verify group-to-role behavior.

### Entities and M2M

- Export entity types (with permissions), entities, and grants (`POST /api/entity/search`, `POST /api/entity/grant/search`).
- Entity used as an API client → Inbound App (confidential) + Resource scopes + Policy. Entity Type permissions → Resource scopes.
- Grants that model data-level authorization (user X may access thing Y) → Descope FGA relations; use the `descope-fga-schema` skill to model them.
- Client secrets don't transfer; plan a rotation window where both old and new credentials work.

### Management API mapping

| FusionAuth (`FusionAuthClient`) | Descope Management SDK (Node names; verify per language) |
|---|---|
| `createUser` / `updateUser` / `patchUser` | `management.user.create` / `update` / `patch` |
| `deleteUser` / `deactivateUser` / `reactivateUser` | `management.user.delete` / `deactivate` / `activate` |
| `retrieveUser` / `retrieveUserByEmail` | `management.user.load` / `loadByUserId` |
| `searchUsersByQuery` | `management.user.search` |
| `register` / `createRegistration` / `updateRegistration` (roles) | `management.user.setRoles` / `addTenantRoles` / `addTenant` |
| `createGroupMembers` / `deleteGroupMembers` | Role assignment (no groups) |
| `createTenant` / `updateTenant` | `management.tenant.create` / `update` (if tenants map to Descope tenants) |
| `createApplicationRole` | `management.role.create` |
| `createIdentityProvider` | `management.sso.*` per tenant, or the SSO Setup Suite |
| `sendPasswordlessCode`, `forgotPassword`, `sendEmail` | Flows (magic link / OTP / reset) and Messaging Templates |
| `validateJWT` / `retrieveJWTPublicKeys` | `validateSession()` |
| `exchangeOAuthCodeForAccessToken` / `exchangeRefreshTokenForAccessToken` | SDK-managed, or the kept OIDC library |
| `issueJWT` (token for another application) | Inbound App token exchange — verify fit |
| `login` (custom form) | Flow, or SDK password sign-in |

Every Descope management call requires the Management Key and runs server-side only.

---

## Framework Recipes

Recipes below cover the most common stacks. For each, read the "Keep the OIDC library, or adopt the
Descope SDK" decision first.

### Next.js

**With `next-auth` (the common FusionAuth setup).** FusionAuth's own Next.js quickstart uses
`next-auth` v4 with `FusionAuthProvider` from `next-auth/providers/fusionauth`, configured with
`issuer`, `clientId`, `clientSecret`, `tenantId`, and `wellKnown:
${FUSIONAUTH_URL}/.well-known/openid-configuration/${FUSIONAUTH_TENANT_ID}`.

- *Keep `next-auth`:* replace the provider with a generic OIDC provider (`type: "oidc"`, `issuer`,
  `clientId`, `clientSecret`), or a Descope provider if the installed Auth.js version ships one (check
  `node_modules/next-auth/providers` or `@auth/core/providers`). Point it at the Descope issuer,
  register `/api/auth/callback/<provider-id>` on the Descope Federated App, and update the `jwt` /
  `session` callbacks that copy `roles` or `tid` from the FusionAuth profile/token. `getServerSession`,
  `auth()`, `useSession`, and `middleware.ts` keep working.
- *Adopt `@descope/nextjs-sdk`:* remove `[...nextauth]`, `SessionProvider`, and `NEXTAUTH_SECRET`;
  add Descope `AuthProvider` in the root layout (with `NEXT_PUBLIC_DESCOPE_PROJECT_ID`), a sign-in page
  rendering `<Descope flowId="sign-up-or-in" />` (or hosted login via `oidcConfig`), `session()` from
  `@descope/nextjs-sdk/server` in server components and route handlers, and `authMiddleware` in
  `middleware.ts` with API routes **excluded** from the matcher.

**With the FusionAuth React SDK + `nextCookieAdapter`:** treat as React (below) plus the Descope
Next.js SDK for server-side reads.

Next.js 15+: `cookies()` / `headers()` are async — see SKILL.md Step 4.

### React

- `<FusionAuthProvider {...config}>` → `<AuthProvider projectId={...}>` (with `oidcConfig` for hosted login).
- `const { isLoggedIn, userInfo, startLogin, startLogout } = useFusionAuth()` →
  `const { isAuthenticated, isSessionLoading } = useSession(); const { user } = useUser(); const sdk = useDescope();`
- `startLogin()` → `sdk.oidc.loginWithRedirect({ redirect_uri: window.location.origin })` (hosted) or navigate to a page rendering `<Descope flowId="sign-up-or-in" onSuccess={...} />`.
- `startLogout()` → `sdk.oidc.logout({ post_logout_redirect_uri })` (hosted) or `sdk.logout()`.
- `<RequireAuth withRole={['admin']}>` → `isAuthenticated && hasRole(...)` using a helper over the session token's roles (UI gating only).
- Remove any Hosted Backend server routes and `app.*` cookie reads.
- Descope hooks return new object identities every render — depend on primitives in `useEffect`.
- `useUser()` returns `userTenants` fetched live; use it for display rather than decoding claims.

Verify each hook's exact return shape with the MCP before writing code.

### Node.js backend

```typescript
// Before (typical FusionAuth Express middleware)
import { createRemoteJWKSet, jwtVerify } from 'jose';
const JWKS = createRemoteJWKSet(new URL(`${process.env.FUSIONAUTH_URL}/.well-known/jwks.json`));
const { payload } = await jwtVerify(req.cookies['app.at'], JWKS, {
  issuer: process.env.FUSIONAUTH_ISSUER, audience: process.env.FUSIONAUTH_CLIENT_ID,
});
if (!(payload.roles as string[]).includes('admin')) return res.sendStatus(403);
```

```typescript
// After — verify method names against @descope/node-sdk before shipping
import DescopeClient from '@descope/node-sdk';
const descope = DescopeClient({ projectId: process.env.DESCOPE_PROJECT_ID! });
const authInfo = await descope.validateSession(req.cookies['DS']); // throws if invalid
if (!descope.validateRoles(authInfo, ['admin'])) return res.sendStatus(403);
```

- Also check the `Authorization: Bearer` header for API clients.
- `audience` validation disappears unless a JWT Template adds `aud` — see the gotcha below.
- `FusionAuthClient` admin calls → `DescopeClient({ projectId, managementKey })` + `management.*`.

### Python backend

- `PyJWT`/`authlib` validation against FusionAuth JWKS → `descope_client.validate_session(session_token=token)` in a Flask decorator, FastAPI dependency, or Django middleware; role checks with the SDK's `validate_roles`.
- `FusionAuthClient(api_key, url)` → `DescopeClient(project_id=..., management_key=...)` and `descope_client.mgmt.user.*`.
- `authlib` OAuth registrations (`oauth.register('fusionauth', server_metadata_url=...)`) → keep and repoint at Descope's discovery URL, or replace.

### Go backend

- `go-oidc` `provider.Verifier(...)` / `golang-jwt` parsing → `descopeClient.Auth.ValidateSessionWithToken(ctx, token)` returning `(bool, *descope.Token, error)`.
- `fusionauth.NewClient(httpClient, baseURL, apiKey)` → `client.NewWithConfig(&client.Config{ProjectID: ..., ManagementKey: ...})`.
- Role checks → Descope's role validation helpers on the returned token.

### Java (Spring) and .NET

**Spring Boot.** Typical FusionAuth config:

```yaml
spring:
  security:
    oauth2:
      client:
        provider:
          fusionauth:
            issuer-uri: https://auth.example.com
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
```

Keeping Spring Security: change `issuer-uri` to the Descope issuer, update the client registration
(client ID = Project ID, secret = Access Key, for a Federated App), and update the authorities
converter — FusionAuth's `roles` is a flat array; Descope's project roles are a flat `roles` array but
tenant roles live under `tenants`. Remove any audience validator unless a JWT Template adds `aud`. Or
replace with `descope-java`'s `validateSessionWithToken`.

**.NET.** `AddOpenIdConnect` / `AddJwtBearer` with `Authority` = FusionAuth, `Audience` = Application ID,
`RoleClaimType = "roles"`: change `Authority` to Descope's issuer, drop or reconfigure `Audience`, and
adjust role-claim mapping. Or replace with `descope-dotnet`.

### Mobile

- FusionAuth's Swift and Android SDKs (`AuthorizationManager`) wrap AppAuth-style OAuth. Replace with the Descope Swift/Kotlin SDK running a Flow, or keep AppAuth and point it at Descope's OIDC endpoints.
- React Native (`react-native-app-auth`) and Flutter (`flutter_appauth`) apps: repoint the issuer, client ID, and redirect URL, or adopt `@descope/react-native-sdk` / `descope-flutter`.
- Redirect URIs registered on the FusionAuth Application must be re-registered for Descope; update URL schemes, associated domains, and Android intent filters.
- Verify every SDK method via the MCP — mobile SDK surfaces change between majors.

---

## Common Gotchas

### Cookie names: DS and DSR

FusionAuth's Hosted Backend uses `app.at` (access token, HttpOnly), `app.rt` (refresh, HttpOnly),
`app.idt` (ID token, JS-readable), and `app.at_exp` (expiry, JS-readable), all `SameSite=Lax` and
scoped to the registrable domain. `next-auth` apps use their own session cookie instead. Descope uses
`DS` (session) and `DSR` (refresh). Grep for every `app.` cookie read — server code reading `app.at`
and client code reading `app.idt` both break.

**Third-party cookies.** FusionAuth's Hosted Backend does not work cross-site (a Cloud
`*.fusionauth.io` host returns 403 to apps on other domains), so many deployments put FusionAuth on a
custom domain under the app's domain. Descope has the same class of issue with refresh across sites;
configure a [Descope custom domain](https://docs.descope.com/how-to-deploy-to-production/custom-domain)
on the same registrable domain as the app.

### Audience validation requires explicit setup

FusionAuth tokens carry `aud` = the Application ID, and backends often validate it. Descope session
tokens have no `aud` by default. To keep audience checks: add an `aud` claim in a JWT Template and pass
`audience` to the Descope validation call. Otherwise remove the audience option knowingly.

### Logout requires two steps

1. Invalidate the session server-side (`descopeClient.logout(refreshToken)`, or the client SDK's `logout()`).
2. Clear `DS` and `DSR`.

FusionAuth logout was usually a link to `/app/logout/{client_id}` or `/oauth2/logout`. Replace links,
not just method calls. With Descope-hosted login, use `sdk.oidc.logout({ post_logout_redirect_uri })`.

### Env var reduction

Typical net change: `FUSIONAUTH_URL`, `FUSIONAUTH_ISSUER`, `FUSIONAUTH_CLIENT_ID`,
`FUSIONAUTH_CLIENT_SECRET`, `FUSIONAUTH_API_KEY`, `FUSIONAUTH_TENANT_ID` (and `next-auth` FusionAuth
variants) removed; `DESCOPE_PROJECT_ID`, its public twin, and `DESCOPE_MANAGEMENT_KEY` added (plus a
client secret only if a confidential OIDC client is kept). Server-side `FUSIONAUTH_APP_*`, `DATABASE_*`,
and `SEARCH_*` variables belong to the FusionAuth deployment being retired.

### Approved Domains: domain only

FusionAuth Applications list full "Authorized redirect URLs" and "Authorized request origin URLs".
Descope Approved Domains take the domain only (`localhost:3000`, `app.example.com`). A kept OIDC
library registers its callback URL on the Descope Federated App.

### Testing checklist

- [ ] Imported user signs in with their existing password — one test user per hash scheme
- [ ] User on an unsupported scheme goes through the JIT branch (if FusionAuth is still on) or the reset branch
- [ ] Merged same-email user sees all their tenants
- [ ] Roles match FusionAuth (registration roles + group roles)
- [ ] `email` and custom claims present in the token (JWT Template)
- [ ] Code that joins on `sub` uses the Descope ID or `fusionauthId`
- [ ] Unauthenticated API route returns 401, not a redirect
- [ ] Logout clears the session and the `DS`/`DSR` cookies
- [ ] Social and enterprise SSO sign-in work for at least one provider/tenant each
- [ ] TOTP users (if seeds imported) can sign in with their existing authenticator
- [ ] No request reaches the FusionAuth host (except the JIT connector, if in use)
