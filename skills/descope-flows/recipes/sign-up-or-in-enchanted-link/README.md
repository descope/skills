# Sign up or in with an enchanted link

Passwordless login by email link that can't be completed by whoever merely has the email: the email holds three
numbered links, the waiting screen shows one number, and only that link signs the user in. The original tab polls
and continues once the right link is clicked, on any device. New users give their name. The console
template `enchantedlink-template-sign-up-or-in`, with an explicit name mapping and a rule for an expired link.

## When to use

"Enchanted link", "magic link that works across devices", "click the matching number", "link login that resists
email scanners and forwarded links". For a plain one-click link, use
[sign-up-or-in-magic-link](../sign-up-or-in-magic-link/README.md); magic links are far more common (20 of 31
active large projects log in by magic link, 3 of 32 have an enchanted link flow).

## Flow

```
0 Welcome (email) --> 18 send enchanted link --> 19 Enchanted Link Sent ({{linkId}}, polling) --polling--> 21 new user? --yes--> 16 User Information --> 17 update user --> 6 End
                          ^                         |   \--resend--> 18                                       \--no-------------------------------------> 6
                          |                         \--polling-error (link expired)--> 0
                          \--(link clicked, other tab)--> 18.end verify --> 20 Verified Successfully
```

| Task | Type, action | What to know |
|---|---|---|
| `0` | screen | `EmailInput` `YsKt52415F` (`email`); Continue `COcMh1vzSn` -> `18`. |
| `18` / `18.end` | `sign-up-or-in-enchanted-link-email` / `verify-enchanted-link` | A pair: `verifyStepId` names `18.end`, and both share the name. Two `success` rules on `18`: one to the waiting screen `19`, one to `18.end` (where the clicked link lands). `uri`: the page that opens from the link. |
| `19` | screen | Shows `{{linkId}}` (the number to click) and `{{sentTo.maskedEmail}}`. Its `PollingLoader` posts `polling` until the link is verified (-> `21`) and `polling-error` when the link expires (-> `0`); "Send again" `resend` -> `18`. |
| `20` | screen | Shown in the tab the link opened: "Verified Successfully". That tab ends here; the original tab carries on from `19`. |
| `21` | condition | `authInfo.firstSeen` is-true: a new user. |
| `16`, `17` | screen, `update-user-properties` | `FullNameInput` `fullName`; `userPropertiesDefinitions` maps `displayName` from `form.fullName`. |
| `6` | `logged-in` | Issues the session in the original tab. |

General flow anatomy: [flow-structure](../../references/flow-structure.md).

## Adapt

- **Redirect URL** (do this first): set `tasks.18.arguments.uri.value` to the app page that hosts the flow, e.g.
  `https://app.example.com/login`. Empty works only if the project has a redirect URL for enchanted links configured
  or the app passes `redirectUrl` when it starts the flow.
- **Sign-in only**: template `enchantedlink-template-sign-in`.
- **More profile fields**: an input on `16` and a `userPropertiesDefinitions` row on `17` per field.

## Pitfalls

- Keep the `18` / `18.end` pair together: same name, `verifyStepId` = `18.end`, both `success` rules on `18`.
  Renumbering one without the other breaks verification.
- Every interaction the waiting screen lists needs a rule. Without the `polling-error` rule an expired link ends the
  run with "Could not get next task", the most common runtime failure of link-sent screens in production.
- The link opens a second tab: the session is issued in the original tab (the one polling at `19`), not where the
  link was clicked.

## Checked

- `scripts/validate_flow.py` (this skill's checker) and `scripts/flow_style.py`: ok, no errors, warnings or style
  notes.
- Import + export round trip: imports, all tasks and screens kept.
- e2e: not run (the test runner doesn't follow enchanted links yet).
