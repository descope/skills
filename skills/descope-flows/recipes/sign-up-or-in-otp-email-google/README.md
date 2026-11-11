# Sign up or in with email OTP or Google

One flow for both new and returning users: a one-time code by email, or Google. New users are asked for their name.

File: [`flow.json`](flow.json). Derived from the Descope template "Sign up or in - OTP or social"
(`otp-template-socials-sign-up-or-in`) with SMS switched to email. Copy it, change `flowId` and `metadata.name`, and
import.

## When to use

The user wants passwordless sign-up/sign-in with email codes, social login, or both. Start here for any single
social provider too (see Adapt). Not for magic links, passwords or passkeys.

## Flow

```
start -> 0 welcome screen   (startTask is 0; "start" is the editor's Start node)
           |- Continue (email)  -> 19 sign-up-or-in-otp-email -> 20 verify-otp screen
           |                                                       |- code entered    -> 21 verify-code-otp-email -> 4
           |                                                       |- Send again       -> 19
           |                                                       |- different email / other method -> 0
           |- Continue with Google -> 3 oauth-start -> 3.end exchange-oauth-code -> 4
4 condition "Is new user?" (authInfo.firstSeen)
           |- new      -> 12 user-information screen -> 7 update-user-properties (displayName = form.fullName) -> 8
           |- existing -> 8
8 End (logged-in: ends the flow, issues the session)
```

| Task | Type | What to know |
|---|---|---|
| `0` | screen "Welcome" (`SC34mQ8rTzKvN2bW6xHjLpE9aYcFd`) | `EmailInput` named `email` (so `allInputKeys: ["email"]`), Continue button `S-VOZ5i7gc`, `GoogleButton` `t1ZEVL_dUC` |
| `19` | `sign-up-or-in-otp-email` | Reads `email` from the form. Creates the user if new. `providerId`/`templateId` empty = Descope's default email sender and template |
| `20` | screen "Verify OTP" (`SC34mQ8sVb7GkR3nXwZ5tJhUoPq1e`) | `CodeInput` `L1T9iO4p5U` submits when the 6 digits are in; `resend` button goes back to `19` |
| `21` | `verify-code-otp-email` | Reads `code` from the form |
| `3` / `3.end` | `oauth-start` / `exchange-oauth-code` | `3`'s `exchangeStepId` must be the exchange task's id (`3.end`); the copy on `3.end` is inert. `defaultProvider` empty = the provider of the button clicked |
| `4` | condition | `authInfo.firstSeen` is true right after sign-up |
| `12` / `7` | screen "User Information" (`SC34mQ8tLx2CfY9pM4vDs8KaNgB6r`) / `update-user-properties` | Asks new users for their name, saves it as the user's `displayName` |
| `8` | `logged-in` | The only end; `metadata.sharedInteractions` is `8.success` |

## Adapt

- **Email OTP only:** delete the `Divider` (`iOknQU_epq`) and the container holding the `GoogleButton`
  (`RyikeiQ3GT`, with `t1ZEVL_dUC` inside) from task `0`'s screen `contents` and from `ROOT`'s `nodes`, remove
  `t1ZEVL_dUC` from the screen's `interactions` and from task `0`'s rules, and delete tasks `3` and `3.end`.
- **Google only:** the reverse: drop the `EmailInput`, the Continue button and its interaction and rule, and tasks
  `19`, `20`, `21`; update task `0`'s `allInputKeys` and `inputKeys` to `[]`.
- **Another social provider** (GitHub, Microsoft, Apple, ...): copy the `GoogleButton` node, give it a new id, set
  `type.resolvedName` and `displayName` to the provider's button (`GithubButton`, `MicrosoftButton`, `AppleButton`),
  `props.data-descope-provider` and `props.startIcon` to the provider name, add it to its parent's `nodes` and to the
  screen's `interactions` with `"subType": "social"`, and add a rule from task `0` to `3`. One `oauth-start` serves
  all providers.
- **Skip the name screen:** point the `4` -> new user rule at `8` and delete tasks `12` and `7` and task `12`'s
  screen.
- **Collect more at sign-up:** add inputs to task `12`'s screen (a custom input is named `form.<key>`; see
  `references/flow-structure.md`, "Input names"), their names to task `12`'s `inputKeys`
  and `allInputKeys`, and rows to task `7`'s `userPropertiesDefinitions` (`{"key": "<user field or
  customAttributes.<key>>", "type": "context", "value": "form.<key>"}`). Built-in inputs (`givenName`,
  `familyName`, `phone`, ...) keep their bare name; any other input must be named `form.<key>` on the screen.
- **Magic link instead of OTP:** not a one-line swap: the send and verify actions, and the screen that waits for the
  click, all differ. Use a magic link recipe from `../README.md` if there is one.

## Pitfalls

- Social providers other than Google may need configuring in the project; import gives no warning for a missing one
  ([guardrails](../../references/guardrails.md#auth-methods-dont-need-enabling-for-flows)).
- Don't tell the user to switch on email OTP or Google under Authentication Methods: flows don't need it.
- Task `3`'s `exchangeStepId` must stay equal to the exchange task's id if you renumber them.

## Checked

- Passes Descope's flow validation (the `ValidateFlow` checks). That covers the task graph, not screen
  contents.
- Checked end to end on a Descope test project: email OTP sign-up (name screen, user created with verified
  email) and sign-in of the same user both reach `logged-in`; the Google button redirects to Google's sign-in page.
- Checked end to end (a test project whose Google
  provider points at a local mock): passes 2/2 past the redirect. A new user signs up with Google (session with
  the Google email, amr oauth), and an existing user with that email signs in as themselves.
- Project prerequisites: none for testing (Google through Descope's own OAuth app). For production, configure Google
  under Authentication Methods -> Social Login with the user's own client id and secret.
