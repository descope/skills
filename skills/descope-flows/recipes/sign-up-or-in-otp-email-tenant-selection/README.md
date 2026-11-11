# Email OTP, then choose a tenant

B2B login where a user can belong to several tenants (organizations, workspaces, accounts): after an email OTP, a user
in more than one tenant picks one, and the session is issued for that tenant (the JWT's current tenant, `dct`). Users
in zero or one tenant go straight to the session. Built from
[sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md) without Google; the selector screen is
the console-shaped snippet `references/catalog/screens/snippets/tenant-select.json`, and the `user.tenantCount` check
is the one the console templates `impersonate-within-tenant` and `agentic-hub-tenant-consent` use.

## When to use

"Tenant selection", "choose an organization / workspace / account at login", "switch tenant", "multi-tenant users".
For picking the tenant by the email's domain instead (SSO routing), start from
[sso-by-domain-or-otp-email](../sso-by-domain-or-otp-email/README.md). When the app already knows the tenant, it can
pass it at flow start (`tenant` in the start options) and no screen is needed.

## Flow

```
0 Welcome (email) --> 19 send OTP --> 20 Verify OTP --> 21 verify --> 4 new user? --yes--> 12 User Information --> 7 update user --> 22
                                                                       \--no-------------------------------------------------> 22
22 more than one tenant? --yes--> 23 Tenant selector --Continue--> 8 End (JWT for the chosen tenant)
                         \--no------------------------------------> 8
```

| Task | Type, action | What to know |
|---|---|---|
| `0`-`21`, `4`, `12`, `7` | | The OTP email login of the base recipe. |
| `22` | condition | `user.tenantCount` greater-than `1` (a number predicate). The user is known here: the check must come after the login. |
| `23` | screen | `TenantSwitcherComboBox` `4aMOMaQhTf` with `props.name: "userSelectedTenant"` and empty `data`: the engine fills the list with the user's tenants, but only because the screen task's `allInputKeys` contains `userSelectedTenant` (keep it). Continue `KdWwE_4shE`. |
| `8` | `logged-in` | Reads `userSelectedTenant` and issues the session with that tenant as current (`dct` claim); the JWT's `tenants` claim still lists all of the user's tenants with their roles. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Always ask** (even with one tenant): drop `22` and point `4`'s ELSE and `7` at `23`.
- **No tenant yet**: add a branch on `user.tenantCount` `equal` `0` to a screen that explains it, or to a
  tenant-creation step, as the template `agentic-hub-tenant-consent` (task `9`) does.
- **Remember the last choice**: the app can pass the tenant at the next flow start (`tenant` start option); the
  selector is then not needed for that login.
- **Labels**: edit the `Text` node `BCT_pymQkM` and the `TenantSwitcherComboBox` `label`/`placeholder` props.

## Pitfalls

- Use `TenantSwitcherComboBox`, not `TenantSelector` (the user-profile widget's control).
- Leave the combobox's `data` empty and keep `allInputKeys: ["userSelectedTenant"]`; a hard-coded list doesn't follow
  the user's memberships and the runtime only loads them when that input key is declared.
- `user.tenantCount` is a number: compare with `greater-than` / `equal` and a number predicate (`1`, not `"1"`).
- Put the selector after the user is identified (after verify / OAuth exchange): before login there is no user and no
  tenant list.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Import + export round trip: imports, all tasks and screens kept.
- Checked end to end (`setup.tenants`): a
  user in two tenants picks one and the JWT's `dct` is that tenant; a user with no tenant skips the selector: pass.
