# Email OTP, then TOTP MFA as a subflow

The two-factor login of [sign-up-or-in-otp-email-totp-mfa](../sign-up-or-in-otp-email-totp-mfa/README.md), split in
two flows: the login flow runs the TOTP part as a subflow, a separate flow (`totp-mfa`) that other flows can call too.
Users who have TOTP enter a code; everyone else enrolls by QR code. Two files: `flow.json` (the login) and
`subflow-totp-mfa.json` (the subflow).

## When to use

"Subflow", "reuse the same MFA in several flows", "one place to change the second factor", "call a flow from a flow".
A step shared by sign-in, step-up and sign-up flows (MFA, terms acceptance, profile completion) is the common case.
For a single login flow with no reuse, the one-file
[sign-up-or-in-otp-email-totp-mfa](../sign-up-or-in-otp-email-totp-mfa/README.md) is simpler.

## Flow

```
flow.json (sign-up-or-in-otp-email-mfa-subflow):
0 Welcome (email) --> 19 send OTP --> 20 Verify OTP --> 21 verify --> 4 new user? --yes--> 12 User Information --> 7 update user --> 22
                                                                       \--no-------------------------------------------------> 22
22 TOTP MFA (subflow totp-mfa) --24.success / 27.success--> 8 End (JWT)

subflow-totp-mfa.json (totp-mfa):
22 Has TOTP? --yes--> 23 Verify TOTP --> 24 verify-totp-code (exit 24.success)
             \--no--> 25 update-user-totp --> 26 Connect an authenticator app (QR) --> 27 verify-totp-code (exit 27.success)
```

| Task | Type, action | What to know |
|---|---|---|
| `0`-`21`, `4`, `12`, `7` | | The OTP email login of [sign-up-or-in-otp-email-google](../sign-up-or-in-otp-email-google/README.md), without Google. |
| `22` (login) | `flow` | `arguments.flowId` (inline) names the subflow; the task is named after it ("TOTP MFA"). It runs the subflow with the same user and context, and continues on the subflow's exits. |
| `22` rules | | One rule per exit of the subflow: `interactionId` is an id from the subflow's `metadata.sharedInteractions` (`24.success`, `27.success`), both -> `8`. |
| `22`-`27` (subflow) | | The TOTP tasks of the one-file recipe. `24` and `27` have no next: a task with no rules ends the subflow, and the subflow lists it in `sharedInteractions` as `<task>.success`. |
| `8` | `logged-in` | Issues the session, in the login flow only. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Call it from another flow**: add a task `{"type": "flow", "name": "TOTP MFA", "arguments": {"flowId": {"type":
  "inline", "value": "totp-mfa"}}}` with the two rules above, after the user is identified.
- **Another subflow**: its exits are its automated tasks with no next; list each in its `metadata.sharedInteractions`
  as `{"id": "<task>.success", "type": "success"}` and add one rule per exit in the calling task.
- **Different subflow id**: change the subflow's `flowId` and every caller's `arguments.flowId` together.
- **More TOTP**: recovery codes and optional enrollment go in the subflow, as in the one-file recipe's Adapt; callers
  don't change unless the exits do.

## Pitfalls

- Import `subflow-totp-mfa.json` (flow id `totp-mfa`) as well as the login flow, the subflow first: the login calls
  it by id, and the project must have it.
- The subflow id goes in `arguments.flowId`; a `flowId` key at the task's top level is dropped by import.
- Rules of the calling task must use the subflow's `sharedInteractions` ids; a `success` rule never matches.
- No `logged-in` in the subflow: the caller issues the session, so the subflow works in any calling flow.

## Checked

- `scripts/validate_flow.py` (this skill's checker), on both files: ok, no
  errors or warnings, no style notes.
- Import: the subflow as `totp-mfa`, then the login flow; all tasks and screens kept.
- Checked end to end, with the subflow imported too: a new user enrolls TOTP inside the subflow and a user
  with TOTP verifies a code there; both end with TOTP stored: pass.
