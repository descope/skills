# Sign up or in with a magic link

Passwordless sign-up or sign-in by email magic link; new users are asked for their full name. From the
console template `magiclink-template-sign-up-or-in`.

## When to use

The user wants email-only, passwordless login by link ("magic link", "email link", "passwordless email"). For a code
the user types instead of a link, start from `sign-up-or-in-otp-email-google`. For a link that must be clicked on the
same device that asked for it, or "enchanted link", this recipe is the wrong base: enchanted link uses
`sign-up-or-in-enchanted-link-email` and a different waiting screen.

## Flow

```
0 Welcome (email) --Continue--> 7 send magic link --success--> 8 Magic Link Sent --polling--> 9 Verified Successfully
                                      |                           \--resend--> 7
                                      \--success--> 7.end verify --> 3 new user? --yes--> 4 User Information --> 5 update user --> 6 JWT
                                                                                 \--no----------------------------------------------> 6 JWT
```

| Task | Type, action | What to know |
|---|---|---|
| `0` | screen | `EmailInput` with `name: email`; the button `oQK_Zn381E` submits. |
| `7` | `sign-up-or-in-magic-linkv3-email` | Reads `email` from the screen. `verifyStepId` must name the verify task (`7.end`). Two `success` rules: one to the waiting screen, one to `7.end`. |
| `7.end` | `verify-magic-link` | Runs in the tab opened from the email link. Everything after it runs there. |
| `8` | screen | The original tab waits here. `PollingLoader` gives the `polling` interaction (fires once the link is verified); `resend` goes back to `7`; `polling-error` (link expired) back to `0`. Shows `{{sentTo.maskedEmail}}`. |
| `9` | screen | Shown in the original tab after the link was used elsewhere. No next: the session lives in the link's tab. |
| `3` | condition | `authInfo.firstSeen` is-true -> new user. |
| `4`, `5` | screen, `update-user-properties` | Collects `fullName`; `userPropertiesDefinitions` maps `form.fullName` to the user's `displayName`. |
| `6` | `logged-in` | Issues the session. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Redirect URL** (do this first): set `tasks.7.arguments.uri.value` to the page of the user's app that hosts the
  flow, e.g. `https://app.example.com/login`. Leaving it `""` works only if the project has a magic link redirect URL
  configured (Project settings -> Authentication methods -> Magic Link) or the app passes `redirectUrl` when it starts
  the flow; otherwise the action fails at runtime with `MagicLinkMisconfiguration`.
- **Sign-in only** (no self sign-up): start from [sign-in-magic-link](../sign-in-magic-link/README.md), which
  also shows an explicit message to an email with no account.
- **More profile fields**: add an input to task `4`'s screen and a row to
  `tasks.5.arguments.userPropertiesDefinitions.value`. A built-in input keeps its bare name and is read as
  `form.<name>` (`givenName` -> `{"key": "givenName", "type": "context", "value": "form.givenName"}`); any other
  input must be named `form.<key>` itself (`props.name: "form.company"` ->
  `{"key": "customAttributes.company", "type": "context", "value": "form.company"}`; a bare `company` is never
  readable as `form.company`). The custom attribute must exist in the project. Then add the name to task `4`'s
  `inputKeys` and `allInputKeys`
  ([flow-structure](../../references/flow-structure.md), screen tasks).
- **Drop profile collection**: point `7.end` at `6` and delete `3`, `4`, `5` and task `4`'s screen.
- **Texts**: edit `props.children` of the `Text` nodes in each screen.

## Pitfalls

- `verifyStepId` and the `<id>.end` task id must match the send task id. Renumbering `7` without renaming `7.end` and
  `verifyStepId` breaks verification silently.
- Both `success` rules on `7` are required; with only the `7.end` rule the user never sees the waiting screen.
- The tab that opened the link, not the waiting tab, gets the session. An app that needs the session in the original
  tab wants enchanted link or OTP instead.
- `update-user-properties` with no `userPropertiesDefinitions` falls back to a deprecated path that sets only the
  display name (from a `fullName` input); always write the mapping, as here.
- `polling-error` (the link expired while this tab waited) goes back to `0`. The screen lists it, so it needs a rule:
  without one the flow fails with NextTaskNotFound when the link expires.

## Checked

- `scripts/validate_flow.py` (this skill's checker): ok, no errors or
  warnings, no style notes.
- Local stack import + export round trip (`/v2/mgmt/flow/import`): imports, all tasks and screens kept.
- Checked end to end: a new user signs
  up through the link, an existing user signs in: pass. The expired-link path (`polling-error`): not run.
