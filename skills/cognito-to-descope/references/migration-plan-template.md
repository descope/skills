# Migration Plan Template

## Agent Instructions

Generate each section by populating the templates below from Phase 1 and Phase 2 analysis. Do not use generic boilerplate — every row in every table must reference actual files found in this codebase. Every file reference must include `file:line`. Every risk must name the specific file that creates it.

This is a template. Replace all `[placeholder]` values with codebase-specific information before writing `migration-plan.md` to the repository root.

---

```markdown
# Cognito → Descope Migration Plan

> Generated: [date]
> Repository: [detected from git config or directory name]
> Architecture: [one-line summary]

---

## 1. Executive Summary

### Current State
[Describe how Cognito is used today — patterns detected (A–K), auth flows, user volume if discoverable, infra dependencies]

### Target State
[Describe the Descope architecture that replaces it — which flows, which SDK, how tokens change]

### Migration Strategy
[Recommend incremental (passive expiry + dual-validation) or big-bang based on risk analysis. State why.]

### Key Risks
[Top 3 risks specific to this codebase — not generic boilerplate. Name the file and line for each.]

---

## 2. Current Architecture Analysis

### System Architecture
[Architecture type, services, tech stack — derived from Phase 1.1]

### Authentication Flow (Current)
[Textual flow diagram, e.g.:]
```
User → [React SPA] → Amplify.configure → Cognito Hosted UI
                  ← id_token + access_token ←
     → [API Gateway] → Cognito JWT Authorizer → [Lambda / ECS service]
                                              → [DynamoDB — user_id = cognito:sub]
```

### Auth Integration Points

| Layer | File(s) | What It Does with Auth | Change Required |
|---|---|---|---|
| Frontend auth state | [file:line] | [e.g., stores Amplify user in React context] | [e.g., replace with useSession()] |
| API middleware | [file:line] | [e.g., verifies Cognito JWT, attaches req.user] | [e.g., swap CognitoJwtVerifier for Descope SDK] |
| Database scoping | [file:line] | [e.g., WHERE user_id = req.user.sub] | [e.g., sub changes — DB remapping needed] |
| [add rows for each layer found] | | | |

### Key Dependencies and Risks
[Specific risks for this codebase — enumerate each risk with the file and line that creates it]

---

## 3. Concept Mapping

[Insert full tables from Phase 2, tailored to what was actually found. Omit rows for concepts not present in this codebase.]

### Core Identity Concepts

| Cognito Concept | Found in Codebase | Descope Equivalent | Maps Directly? | Notes |
|---|---|---|---|---|
| User Pool | [Y/N + file] | Descope Project | Yes | One Project ≈ one User Pool |
| User Pool (multi-tenant) | [Y/N + file] | Descope Tenants | Redesign needed | Each Pool → one Tenant |
| App Client | [Y/N + file] | Descope Application | Yes | Created in Console → Applications |
| User Pool Groups | [Y/N + file] | Descope Roles / Tenants | Partial | Roles for RBAC; Tenants for org isolation |
| Custom Attributes | [Y/N + file] | Descope User Custom Attributes | Yes | Must pre-create schema before import |
| `cognito:sub` | [Y/N + file] | `sub` claim in Descope JWT | Yes | New sub values issued — DB remapping needed if used as FK |
| `cognito:username` | [Y/N + file] | `loginIds[0]` or `sub` | Partial | Username concept differs |
| `cognito:groups` | [Y/N + file] | `roles` claim or tenant membership | Partial | Depends on usage (RBAC vs. tenancy) |

### Authentication Methods

| Cognito Method | Found in Codebase | Descope Equivalent | Migration Effort |
|---|---|---|---|
| Email + Password | [Y/N] | Email + Password via Flow | Low |
| Magic Link / OTP | [Y/N] | Magic Link / OTP via Flow | Low |
| TOTP MFA | [Y/N] | TOTP MFA — re-enrollment required | Medium |
| SMS MFA | [Y/N] | SMS OTP — re-enrollment required | Medium |
| Hosted UI | [Y/N] | Descope Hosted Flows | Low–Medium |
| Google / Facebook / Apple | [Y/N + providers] | Descope Social Connectors | Medium (credential re-setup) |
| SAML (single IdP) | [Y/N] | Descope SSO Application | Medium |
| SAML (multi-tenant) | [Y/N] | Descope Tenant SSO | Medium |
| Custom Auth Challenge | [Y/N] | Descope Flow custom steps | High |
| Client Credentials (M2M) | [Y/N] | Descope Access Keys | Medium |
| Device tracking | [Y/N] | No equivalent | Workaround required |

### Token Claims That Change

[For every claim accessed in this codebase (from Phase 1.9), show the before/after:]

| Claim | Cognito Value | Descope Equivalent | Files Affected |
|---|---|---|---|
| `sub` | Cognito user UUID | New Descope `sub` | [list all files at file:line] |
| `cognito:groups` | `['admin', 'users']` | `roles: ['admin', 'users']` | [list] |
| `iss` | `https://cognito-idp.<region>.amazonaws.com/<poolId>` | `https://api.descope.com/<projectId>` | [list] |
| `aud` | Cognito App Client ID | Descope Project ID | [list] |
| `cognito:username` | username string | `loginIds[0]` or `sub` | [list] |
| [add rows for every claim accessed in this codebase] | | | |

### Lambda Triggers → Descope Equivalents

[Only include triggers found in Phase 1.6:]

| Cognito Trigger | Purpose (from code) | Descope Equivalent | Notes |
|---|---|---|---|
| Pre-signup | [e.g., domain validation] | Flow condition / webhook | [from MCP docs] |
| Post-confirmation | [e.g., provision user in DB] | Post-login webhook | [from MCP docs] |
| Pre-authentication | [e.g., IP blocklist] | Flow condition | [from MCP docs] |
| Post-authentication | [e.g., audit log] | Post-login webhook | [from MCP docs] |
| Pre-token-generation | [e.g., custom claims] | JWT Template | [from MCP docs] |
| Custom message | [e.g., branded email] | Email template customization | [from MCP docs] |
| User migration | [e.g., JIT from legacy] | HTTP Connector in Flow | [from MCP docs] |
| Define/Create/Verify auth challenge | [custom challenge logic] | Custom Flow steps | High complexity — detail separately |

### Infrastructure Components

| Cognito Component | Found | Descope Equivalent | Maps Directly? |
|---|---|---|---|
| User Pool | [Y/N] | Descope Project | Yes |
| Identity Pool (IAM credentials) | [Y/N] | Not replaced by Descope | Separate handling needed |
| API Gateway Cognito Authorizer | [Y/N] | API Gateway JWT Authorizer | Yes (with JWT Template) |
| Cognito as OIDC Provider (D2) | [Y/N] | Descope OIDC Application | Yes |

---

## 4. System Impact Analysis

### APIs and Authorization Layers
[For each middleware/guard/filter found — state the exact change needed with file:line references]

### Frontend Applications
[For each frontend app — state what changes: Provider, hooks, auth calls, route protection]

### Backend Services
[For each backend service — state what changes: token validation, user context, management API calls]

### Data Layer
[If Cognito sub is used as FK — state the remapping requirement, affected tables/columns, and approach. The migration tool stores the old `sub` as a `cognitoSub` custom attribute in Descope. A DB script is needed post-migration.]

### Third-Party Integrations
[For each integration found in Phase 1.9 — state whether it's affected and what changes]

---

## 5. Step-by-Step Migration Plan

### Phase A: Descope Project Setup
1. Create Descope project at https://app.descope.com
2. Configure authentication methods: [list based on patterns detected]
3. [If social/SAML] Configure connectors: [list each with credentials needed]
4. [If custom attributes] Create attribute schema in Console → Users → Attributes: [list each]
5. [If pre-token Lambda] Recreate claims in JWT Templates: [list claims]
6. [If API Gateway] Enable AWS API Gateway JWT Template

### Phase B: User Migration
[Full migration vs. JIT — recommend based on risk analysis or confirmed preference]

**Full migration**:
- Run descope-migration tool (dry run → confirm → live run)
- Handle FORCE_CHANGE_PASSWORD users: [count from dry run, plan for magic link / OTP routing]
- MFA re-enrollment: [if MFA detected — all users must re-enroll; communication plan needed]

**JIT migration** (if preferred):
- Configure HTTP Connector in Descope Console pointing at Cognito
- [If client secret detected] Deploy proxy service to compute SECRET_HASH
- Modify Sign-Up or In Flow with JIT migration steps

### Phase C: Backend Token Validation
[For each backend service — specific files to update and changes to make]

### Phase D: Frontend Auth Integration
[For each frontend app — specific files to update and changes to make]

### Phase E: Authorization Layer Updates
[For each middleware/guard — specific changes needed, file:line]

### Phase F: Data Layer Migration
[If needed — DB remapping script approach for Cognito sub → Descope sub]

### Phase G: Infrastructure
[API Gateway authorizer swap, env var updates, Lambda trigger decommissioning]

### Phase H: Session Cutover Strategy
**Recommended**: [Passive expiry / Forced re-auth / Cookie clearing — state recommendation and why]

Deploy dual-validation middleware before cutover. Remove Cognito verifier after transition window (monitor `source: 'cognito'` log entries — remove when zero for a full business day).

---

## 6. Code-Level Changes

### Files to Modify

[For each file identified — state the specific change, not just "update auth"]

| File | Change | Complexity |
|---|---|---|
| [file:line] | [e.g., Replace CognitoJwtVerifier with descopeClient.validateSession()] | Low |
| [file:line] | [e.g., Replace useEffect Hub.listen + manual state with useSession() hook] | Low |
| [file:line] | [e.g., Remap payload['cognito:groups'] → token.roles in 3 places] | Low |
| [file:line] | [e.g., Pre-token Lambda claims — recreate in JWT Template, then remove file] | Medium |
| [add rows for every file that changes] | | |

### Cross-Cutting Patterns

[Patterns that appear in multiple files — show before/after once, list all affected files]

**Token validation (Node.js)**
```js
// Before (every backend service)
const decoded = await cognitoVerifier.verify(token);
req.user = { id: decoded.sub };

// After
const authInfo = await descopeClient.validateSession(token);
req.user = { id: authInfo.token.sub };
```
Affected files: [list at file:line]

**User context claim access (Frontend)**
```js
// Before
user.attributes.email
user.attributes['custom:department']
user.username

// After
user.email
user.customAttributes['department']
user.userId
```
Affected files: [list at file:line]

[Add other cross-cutting patterns specific to this codebase]

---

## 7. Risk & Edge Cases

### Risk Register

| Risk | Severity | Trigger | Mitigation |
|---|---|---|---|
| Cognito `sub` used as DB FK | [HIGH if found at file:line] | User lookups break post-migration | DB remapping script before cutover |
| MFA re-enrollment | [HIGH if MFA enabled] | All enrolled users lose MFA on cutover | User communication + grace period |
| Active sessions during cutover | MEDIUM | API calls fail mid-session | Dual-validation middleware + passive expiry |
| Custom JWT claims disappear | [HIGH if claims found at file:line] | Authorization checks fail | Recreate in JWT Templates before cutover |
| Token issuer/audience checks hardcoded | [HIGH if found at file:line] | Token validation rejects new tokens | Update all iss/aud checks |
| [Add codebase-specific risks with file:line] | | | |

### Hidden Dependencies
[Things found in Phase 1.9 that aren't obvious from the auth files alone — service-to-service token forwarding, third-party integrations, RLS policies, etc.]

---

## 8. Testing Strategy

### Unit Tests
- Token validation middleware: mock Descope JWT, verify `req.user` populated correctly
- Role checks: verify `token.roles` used where `cognito:groups` was
- User attribute access: verify new `user.email` / `user.customAttributes.*` paths

### Integration Tests
- Sign-in with migrated user (password or magic link)
- Protected route blocks unauthenticated request
- Protected route allows valid Descope token
- Role-based access: admin vs. non-admin endpoints
- [If multi-tenant] Tenant context correct on requests

### Auth Flow Tests (manual)
- [ ] Sign-up: new user
- [ ] Sign-in: migrated user (password reset or JIT path)
- [ ] Social login: [each provider found]
- [ ] SAML / enterprise SSO: [each IdP found]
- [ ] MFA enrollment + sign-in
- [ ] Session persistence across page refresh
- [ ] Token sent to backend and validated correctly
- [ ] Logout (local session)
- [ ] Global sign-out (all sessions)
- [ ] Password change flow
- [ ] Protected routes block unauthenticated users
- [ ] FORCE_CHANGE_PASSWORD users routed to reset flow
- [ ] [If dual-validation deployed] Both Cognito and Descope tokens accepted during transition window

### Regression Areas
[Parts of the system that use auth context indirectly — from Phase 1.9 cross-cutting analysis]

---

## 9. Rollout Plan

### Recommended Approach: [Incremental / Big Bang — with rationale]

**Pre-cutover**:
1. Descope project configured and tested in staging
2. Users migrated (or JIT flow deployed) and verified
3. Dual-validation middleware deployed to production
4. Feature flag or env var to switch frontend auth provider

**Cutover**:
1. Deploy frontend with Descope SDK (flip feature flag or env var)
2. Old Cognito sessions expire passively over the next [Cognito token expiry window]
3. Monitor `source: 'cognito'` log entries

**Post-cutover**:
1. Remove dual-validation middleware once Cognito entries gone from logs
2. Decommission Cognito User Pool
3. Remove Cognito packages and dead code

### Monitoring
- Log `source` field on every token validation (cognito vs. descope)
- Alert on auth failure rate spike at cutover
- Descope Console → Audit Log for sign-in activity

### Fallback
If critical issues arise post-cutover: revert frontend to Cognito SDK (dual-validation middleware still accepts Cognito tokens). Users do not lose sessions. Fix issues; re-cutover.

---

## 10. Manual Steps Checklist

These items require action in the Descope Console or external systems. The app will not work correctly until at least items A and B are done.

**A. Descope Console Setup (required before app works)**
- [ ] Fill in `DESCOPE_PROJECT_ID` in all `.env` files
- [ ] Fill in `DESCOPE_MANAGEMENT_KEY` (for backend management operations)
- [ ] Configure "Sign-Up or In" flow with: [list auth methods]
- [ ] Add redirect URLs: [list from codebase]
- [ ] [If MFA] Add MFA enrollment step; plan user re-enrollment communication

**B. [If social/SAML] Connectors (app broken until done)**
[List each provider and credentials needed]

**C. [If custom attributes] Attribute schema**
[List each — must exist before user import]

**D. [If Lambda triggers] Trigger recreation**
[List each trigger, its purpose, and its Descope equivalent]

**E. [If pre-token Lambda] JWT Template**
[List claims to recreate]

**F. [If API Gateway] Authorizer swap**
- [ ] Enable AWS API Gateway JWT Template in Descope Console
- [ ] Create JWT Authorizer in API Gateway (issuer, audience, token source)
- [ ] Remove Cognito User Pool authorizer

**G. [If Identity Pools] AWS IAM credential source**
[Options: federate Descope as OIDC provider into existing Identity Pool]

**H. [If M2M] Access Keys**
[Replace client credentials flow with Descope Access Keys]

**I. Email templates**
[Recreate custom templates in Descope Console → Authentication Methods → Email]
```
