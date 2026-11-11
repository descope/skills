# SSO by email domain, else email OTP

The user types an email; if its domain belongs to a tenant with SSO (SAML or OIDC) configured, they go to their IdP
(straight away when the tenant enforces SSO, else after choosing SSO or an email code), otherwise they sign up or in
with a one-time code by email. IdP-initiated logins (the user starts from the IdP's app
portal) are handled first. Built from [sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md)
(content template `otp-template-socials-sign-up-or-in`) with the SSO tasks of `magiclink-sso-template-sign-up-or-in`.

## When to use

B2B apps where some customers' employees must use their company IdP and everyone else gets a passwordless fallback:
"SSO for enterprise customers", "route to SSO by domain", "home realm discovery", "SAML/OIDC with email fallback". For
a fallback other than OTP, keep tasks `22`, `24`, `23` and swap the `19` -> `20` -> `21` branch for the other method's
tasks (magic link: [sign-up-or-in-magic-link](../sign-up-or-in-magic-link/README.md); password:
[passwords-sign-up-or-in-verify-email](../passwords-sign-up-or-in-verify-email/README.md)).

## Flow

```
22 IdP initiated? --yes--------------------------------------------------> 23 SSO start --> 23.end SSO exchange --> 8 JWT
   \--no--> 0 Welcome (email) --Continue--> 24 SSO for domain? --yes--> 25 SSO policy --> 26 must use SSO? --yes--> 23
                                              |                                              \--no--> 27 Choose: SSO --> 23 / Email me a code --> 19
                                              |                     23, 23.end errors --> 28 SSO failed --Back--> 0
                                              \--no--> 19 send OTP --> 20 Verify OTP --> 21 verify --> 4 new user? --yes--> 12 User Information --> 7 update user --> 8 JWT
                                                                                                         \--no----------------------------------------------> 8 JWT
```

| Task | Type, action | What to know |
|---|---|---|
| `22` | condition | `idpInitiated` is-true. It must be the start task: an IdP-initiated login arrives with a SAML response and no screen should run first. |
| `0` | screen | `EmailInput` (`email`), Continue `S-VOZ5i7gc`. |
| `24` | condition | `ssoEnabled` is-true. The engine loads it on first use from the tenant found for the flow: the user's tenant, else `startOptions.tenant` (the app passes a tenant), else the tenant that owns the email's domain. True only when that tenant has SSO configured. |
| `25` | `scriptlet` | `ssoPolicy.mustUseSSO` = the tenant enforces SSO (`loadedTenant.enforceSSO`) and the email is not on its exclusion list (`loadedTenant.enforceSSOExclusions`, compared case-insensitively). `loadedTenant.*` loads before login from the same tenant lookup as `ssoEnabled`. A condition can't compare two context values, hence the script (as in the content template `sign-up-or-in-with-sso-exclusion-list`). `ScriptletFailed` -> `23` (SSO, the safe side). |
| `26` | condition | `scripts.ssoPolicy.mustUseSSO` is-true -> `23`; else -> `27`. |
| `27` | screen | "Continue with SSO" `S-VOZ5i7gc` -> `23`, "Email me a code" `Cd4nR8pLwZ` -> `19`: for tenants with SSO that don't enforce it, and for excluded addresses. |
| `23` / `23.end` | `saml-start` / `exchange-saml-code` | Despite the `saml-` name, this pair runs both SAML and OIDC SSO, whatever the tenant has. `exchangeStepId` must name `23.end` on both. `23.end` signs the user up on their first SSO login. Every error each declares (`SSOStartFailed`, `SAMLStartFailed`, `OAuthStartFailed`, `ActionErrorTenantDisabled`; `SAMLExchangeCodeFailed`, `OAuthExchangeCodeFailed`, `ConcurrentSessionsExceeded`, ...) has `errorHandlingV2: custom` and a rule to `28`. |
| `28` | screen | "We couldn't sign you in with SSO", the error message, "Back to sign in" -> `0`. |
| `19`, `20`, `21` | `sign-up-or-in-otp-email`, screen, `verify-code-otp-email` | The OTP fallback. `20` has "Use a different email" `xFKyTBaTQn` and "Choose another method" `pnOqEGpL1b`, both back to `0`; the code input `L1T9iO4p5U` auto-submits. `19` routes `ActionErrorTenantRequiresSSO` (a tenant that enforces SSO) to `23`, not to an error. |
| `4`, `12`, `7` | condition, screen, `update-user-properties` | New OTP users give a full name (`form.fullName` -> `displayName`). SSO users skip it: the IdP sends their name. |
| `8` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **SSO always, never a choice**: point `26`'s ELSE at `23` (or drop `25`-`27` and point `24` at `23`); then only the
  tenant's exclusion list decides who may use a code, and `sign-up-or-in-otp-email` refuses the others with
  `ActionErrorTenantRequiresSSO`.
- **Redirect URL**: set `arguments.redirectUrl.value` on `23` and `23.end` to the app page that hosts the flow when the
  app does not pass `redirectUrl` at flow start and the project has no default.
- **Pick the SSO connection explicitly** (a tenant with several): pass `ssoId` in the start options from the app, or
  set `arguments.ssoId` on `23`.
- **Different welcome text**: edit `props.children` of the `Text` nodes in task `0`'s screen.

## Pitfalls

- Don't put a screen before `22`: an IdP-initiated login would stop at it and lose the SAML response.
- An action reached before any screen (here `23` / `23.end` on the IdP-initiated path) must route its errors with
  custom handling to a screen: automatic handling shows the error on the last screen, and there is none.
- Never offer another method to users of a tenant that enforces SSO: the engine refuses it anyway
  (`ActionErrorTenantRequiresSSO`), so the screen would promise a login that fails.
- `ssoEnabled` is false when the domain matches no tenant, and also when the tenant exists but has no SSO set up, so
  the ELSE branch must be a complete login on its own.
- Task ids `22`-`28` were appended after the base recipe's highest id (`21`), as the console numbers new tasks; reuse
  that rule when adding tasks.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end, each case once:
  - `sign-up-or-in-otp-email`: the OTP branch (`ssoEnabled` false) for a new and an existing user: pass.
  - `sso-domain-routing` (`setup.sso: saml`): an email of a SAML tenant's domain picks "Continue with SSO" on `27` and
    redirects to that tenant's IdP; another email signs up with an OTP: pass.
  - `enforce-sso-tenants` (`setup.enforceSSO: true`): an email at the enforcing tenant redirects to its IdP with no
    choice screen and no email code; another domain signs up with an OTP: pass.
  - Not run: the IdP's response (`exchange-saml-code`, no IdP mock), the exclusion list, and the error screen `28`.
