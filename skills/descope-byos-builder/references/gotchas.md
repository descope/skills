# Descope BYOS — Failure Catalog

Each entry: **Problem → Symptom → Root cause → Fix**. All from real sessions; the symptom strings are what you'll actually see in browser console or network tab.

---

## 1. Nested `<form>` hydration error → page reloads on submit

**Symptom:** React warning `In HTML, <form> cannot be a descendant of <form>`. Clicking Continue / Sign in does nothing visible, page silently reloads, form state lost.

**Root cause:** The Descope web component (`<descope-wc>`) wraps its children in a `<form>`. Your BYOS screen also renders `<form onSubmit={...}>`. The outer form catches the submit → default GET action → page reload before `state.next()` can fire.

**Fix:** Never render `<form>` inside a BYOS screen. Use `<div>`. Wire the button with `onClick={submit}` and enable Enter-to-submit via:

```jsx
const onKeyDown = (e) => {
  if (e.key === 'Enter') { e.preventDefault(); submit() }
}
```

---

## 2. Form key mismatch → "The newPassword field is required"

**Symptom:** Descope returns `[E011003]: Request is invalid` with message like "The X field is required", even though you're sending `X` in the payload.

**Root cause:** You used the key from `allInputKeys` or `inputsMetadata.key`, which is Descope's **internal** routing identifier. The wire-level form key comes from the input node's **`name` prop**.

Example from the Set Password screen: `allInputKeys: ["newPassword_noPolicyOverrides"]` but the input node has `name="newPassword"`. Payload must be `{ newPassword: "..." }`.

**Fix:** When parsing, always look at the input node's `props.name`. Not `allInputKeys`. Not `inputsMetadata[i].key`.

---

## 3. OAuth button "clicking Google does nothing"

**Symptom:** `[Descope] [E011003]: Request is invalid ... The provider field is required`.

**Root cause:** Hosted Descope OAuth buttons set `provider` via a `data-descope-provider` attribute that the web component reads into form state before firing. BYOS bypasses that — you must include `provider` in the payload yourself.

**Fix:**
```jsx
onClick={() => run(OAUTH_GOOGLE, 'google', { ...form, provider: 'google' })}
onClick={() => run(OAUTH_APPLE,  'apple',  { ...form, provider: 'apple'  })}
```

---

## 4. Shared screen names pin UI to first task

**Symptom:** User types email, clicks Continue, console logs `Step "Welcome Screen" is waiting stepId: '21'` — but the UI still shows the email screen. Nothing advances.

**Root cause:** Two flow tasks share the same screen name (e.g., task 0 "Welcome Screen" for email-entry and task 21 "Welcome Screen" for password-entry). A `setState` bailout guard that compares only `screenName` sees both as "the same screen" and skips the state update.

**Fix:** Always update state on `onScreenUpdate`. Disambiguate which task is rendering via `state.context.form.*` heuristics, not via setState short-circuits. Example:

```jsx
function WelcomeRouter({ state, form, setForm }) {
  const hasEmailContext = Boolean(state?.context?.form?.email)
  const Screen = hasEmailContext ? PasswordEntryByos : WelcomeEmailByos
  return <Screen state={state} form={form} setForm={setForm} />
}
```

**Common mistake inside this gotcha:** Picking a heuristic field that's actually populated on **both** colliding paths. You must trace every preceding screen's `allInputKeys` on each path. Always run `parse-flow.mjs` and follow `next.rules` backwards from both tasks to the parent-flow entry point before picking a field.

> **Note:** The example below is from one specific flow set — subflow names and field names will differ in your project. The method is universal; the instantiation is not.
>
> Example: on "Verify OTP" shared between `sign-in-sms-otp` and `progressive-profile-sms`, `form.phone` looks like the natural signal — but **both** subflows have a phone-input screen before the OTP step, so both populate `form.phone`. The correct signal is `form.password`, which is only set when the user came from the parent flow's password screen (entering sign-in-sms-otp) and never set when they came from the post-magic-link path (entering progressive-profile-sms).

---

## 5. Session stays anonymous after successful sign-in

**Symptom:** Flow completes. `onSuccess` fires. App navigates. User lands on profile page — but UI still shows anonymous state (guest banner, unverified badge, etc.).

**Root cause:** Two possible causes — verify which:

**5a. Anonymous-to-verified upgrade reused the same `sub`.** If your auth-state hook caches per `userId` (common pattern), the cache never invalidates because `userId` didn't change. JWT claims (email verification status, custom attributes) did change, but the cache doesn't know.

**Fix:** Invalidate the cache in the flow's `onSuccess` handler, unconditionally.

**5b. The flow itself doesn't actually upgrade the session** — e.g., a subflow contains an `update-user-*` action that was designed for already-authenticated users, and it silently no-ops for anonymous users. Flow ends via `End/logged-in` action, but no new session JWT was issued.

**Fix:** Diagnose by logging `e.detail` in `onSuccess` (dev-only): `console.info({ userClaimKeys: Object.keys(e.detail.user ?? {}), sessionToken: e.detail.sessionJwt ? '(set)' : '(absent)' })`. If `sessionToken` is `(absent)`, it's a flow-config problem — fix in the Descope console, not in BYOS code.

---

## 6. SMS flow completes but no code arrives

**Symptom:** User types phone, clicks Send code, UI advances to Verify OTP screen. No SMS ever arrives. Enter any code → flow either stalls or silently errors.

**Root cause:** Phone number is not in E.164 format. Descope's SMS connector rejects silently — the flow advances optimistically.

**Fix:** Normalize on submit. Minimal implementation:

```js
function toE164(raw) {
  const trimmed = (raw ?? '').trim()
  if (!trimmed) return ''
  const digits = trimmed.replace(/[^\d]/g, '')
  if (!digits) return ''
  if (trimmed.startsWith('+')) return `+${digits}`
  if (digits.length === 10) return `+1${digits}` // default country: adjust per app
  return `+${digits}`
}
```

And gate the submit button on the normalized value: `disabled={!toE164(phone)}`, not `disabled={!phone}`. Otherwise a user typing `" - - "` gets an enabled button whose click silently no-ops.

---

## 7. Subflow screens trigger `[byos] no handler for screen "..."`

**Symptom:** Main flow BYOS works. User clicks "Forgot password?" or "Sign in with a code" → subflow kicks in → first subflow screen renders the hosted widget, not BYOS.

**Root cause:** Subflow screens share the parent `<Descope>`'s `onScreenUpdate` but have different screen names. Your screen map only knows main-flow names.

**Fix:** Export every invoked subflow JSON. Add each subflow's unique screen names to the same `byosScreens` map — subflow screens ARE siblings of main-flow screens in the dispatch.

---

## 8. "Choose another method" button dead-ends silently

**Symptom:** User clicks a button that does nothing. No visible response. Console might show a swallowed error.

**Root cause:** Two screens share a name but have different interaction sets. Your BYOS component renders all buttons for one variant; a click on an interaction the current flow doesn't route silently fails.

**Fix:** Either:
- **Hide** the button via context heuristic when its interaction isn't supported. Best pattern:

  ```jsx
  // Only show "Use a different number" on sign-in-sms-otp (came from password screen).
  // progressive-profile-sms flow lacks that interaction.
  const supportsChangeNumber = Boolean(state?.context?.form?.password || form.password)
  ```

- **Or rename screens in the Descope console** so they don't collide. Each gets its own BYOS component, no heuristic needed.

---

## 9. `componentsConditions` hide rules not mirrored

**Symptom:** Hosted flow hides a button when some server-side state is false (e.g., hides "Sign in with a code" when user has no verified phone). BYOS always shows it. User clicks → subflow launches → fails mid-way.

**Root cause:** Screen JSON has a `componentsConditions` array with rules like `{ operator: "is-false", target: { type: "context", value: "unauthUser.verifiedPhone" } } → action: hide → componentIds: [...]`. BYOS components ignore this by default.

**Fix:** Read the same context key and gate the component:

```jsx
const hasVerifiedPhone = Boolean(state?.context?.unauthUser?.verifiedPhone)
// ...
{hasVerifiedPhone && <button onClick={() => run(SMS_CODE_INTERACTION, ...)}>...</button>}
```

Default to hidden when the context key is absent — safer than showing a button whose subflow would dead-end.

---

## 10. Auto-resend effect fires on every keystroke

**Symptom:** User typing OTP code triggers network requests to the resend endpoint. SMS bombardment.

**Root cause:** `useEffect` has `[form]` or `[state.next]` in deps. Both change on every keystroke / every screen update. Guard ref didn't help because `state.next` is a fresh function reference on every render.

**Fix:** Snapshot via ref, gate by a "fired once" ref, include only stable values in deps:

```jsx
const nextRef = useRef(state?.next); nextRef.current = state?.next
const formRef = useRef(form);        formRef.current = form
const firedRef = useRef(false)

useEffect(() => {
  if (state?.error?.code === 'E061104') {
    if (!firedRef.current) {
      firedRef.current = true
      nextRef.current?.(RESEND, formRef.current)
    }
  } else {
    firedRef.current = false
  }
}, [state?.error?.code]) // ONLY the stable signal
```

---

## 11. `context` keys not what you expect

**Symptom:** Template strings in the hosted screen like `{{sentTo.maskedEmail}}` render, but in your BYOS `state.context.sentTo?.maskedEmail` is `undefined`.

**Root cause:** Context key paths are specific to the screen. The flow builder shows them in the screen details panel as "Context Keys". Same task's `task.contextKeys` array lists what that screen reads. Different flows use different paths:

- Email magic link: `sentTo.maskedEmail`
- SMS OTP: `sentTo.maskedPhone`
- New-user signup: `inputs.email`
- Existing-user password: `form.email`

**Fix:** Read the JSON's `task.contextKeys` and cross-reference with screen node text (any `{{something}}` template substring is a context path). Code defensively with fallback to `form.*`:

```jsx
const email = state?.context?.form?.email ?? form.email ?? 'your account'
```

---

## 12. `onScreenUpdate` change-guard breaks multi-task flows

**Symptom:** Works fine for one user journey. A second path through the flow silently pins on one screen.

**Root cause:** You tried to optimize `onScreenUpdate` by bailing out of `setState` when `screenName` didn't change. But any collision-pair (see #4) will silently fail. And `next` is always a new function ref so the old state has a stale closure.

**Fix:** Don't optimize `onScreenUpdate`. Always update state. React can handle the renders. Autofocus concerns are false alarms — `autoFocus` only fires on mount, not on prop updates.

---

## 13. Form payload accumulates PII across subflow boundaries

**Symptom:** Inside a subflow, Descope's logs show form fields (`password`, `fullName`, `keepMeSignedIn`) that the subflow's current screen doesn't need. Occasional "Request is invalid" errors with cryptic messages.

**Root cause:** BYOS components spread `{ ...form, localKey: value }` on every submit. The form state is shared across the entire `<FlowOrByos>` lifetime. Parent-flow form values leak into subflow submissions.

**Fix:** Send only the current screen's outputs in payloads:

```jsx
// On a phone-input screen, output is just `phone`:
run(SUBMIT, 'submit', { phone: phoneE164 })
// NOT: run(SUBMIT, 'submit', { ...form, phone: phoneE164 })
```

Per BYOS docs: "Each screen must update the form with all values listed in the 'Outputs' section." All, not more.

---

## 14. Password confirm error clears on every keystroke

**Symptom:** Password-mismatch error disappears while the user is still typing the wrong value. Never reappears until submit.

**Root cause:** `onChange={...setShowConfirmError(false)}` — clears too eagerly.

**Fix:** Use a "touched" flag. Derive display from `touched && !match`:

```jsx
const [confirmTouched, setConfirmTouched] = useState(false)
const showConfirmError = confirmTouched && confirm.length > 0 && !passwordsMatch
// onChange: just setForm
// onBlur:   setConfirmTouched(true)
```

---

## 15. Diagnostic logs leak PII to browser console

**Symptom:** During a demo screen-share, the console shows JWT user claim values (email, name, sub, custom attributes). Stakeholder sees it.

**Root cause:** You added `console.info('success', { userClaims: e.detail.user })` for debugging and forgot to gate it.

**Fix:** Gate on `import.meta.env.DEV`. And log only keys, not values:

```jsx
if (import.meta.env.DEV) {
  console.info('[byos] success', {
    userClaimKeys: Object.keys(e?.detail?.user ?? {}),
    sessionToken: e?.detail?.sessionJwt ? '(set)' : '(absent)',
  })
}
```

Prod builds (`import.meta.env.DEV === false`) are silent. Dev-mode console shows structure, not data.

---

## 16. Phone input silently accepts non-phone characters

**Symptom:** User clicks submit on what looks like a valid phone. Nothing happens. No error.

**Root cause:** Your normalizer returned `''` for garbage input (e.g., `" - - "` → digits extracted = `""`). Button was enabled because raw `phone` was truthy. Click runs `submit() → phoneE164 = '' → early return, no user feedback.`

**Fix:** Compute the normalized value in render scope. Gate the button on the normalized value:

```jsx
const phoneE164 = toE164(phone)
// ...
<button disabled={!phoneE164 || Boolean(busyKey)}>Send code</button>
```

---

## 17. Calling `navigator.credentials.*` from BYOS for passkeys

**Symptom:** Passkey button click triggers two prompts in a row, ceremony aborts mid-flow with `NotAllowedError`, or hangs forever after the OS dialog. Sometimes works on one device, fails on another.

**Root cause:** You called `navigator.credentials.create()` / `get()` from a BYOS click handler. But the Descope flow contains a webauthn action task (e.g. `webauthn-update-user-start`/`finish`, or `Sign Up or In / Passkeys`). When the SDK observes that action on `onScreenUpdate`, it runs the WebAuthn ceremony itself. Two callers, one credential ceremony → conflict.

**Fix:** BYOS button just fires the interaction. Don't touch `navigator.credentials.*`.

```jsx
const PASSKEY = 'ilg_QijmHW' // interaction id from flow JSON
// ...
<button onClick={() => run(PASSKEY, 'passkey', form)}>
  {busyKey === 'passkey' ? 'Waiting for device…' : 'Sign in with a Passkey'}
</button>
```

User cancel / device error surfaces on the next `onScreenUpdate` as `state.error.text`. Render it the same way as any other flow error.

---

## 18. Skipping post-auth promotion subflows

**Symptom:** Main sign-in flow works end-to-end. After login, hosted Descope screens flash for a second on top of your app (the passkey promotion). Or `[byos] no handler for screen "Promote Passkeys (WebAuthn)"` after the session is already issued.

**Root cause:** The main flow issued `logged-in` and *then* invoked a promotion subflow (e.g. `add-passkeys`) before terminal. You assumed nothing renders after `logged-in` and didn't export the subflow JSON.

**Fix:** Treat any subflow invoked after a `logged-in` action as a normal subflow — export its JSON, add BYOS components for every screen task, including the `Device Not Supported` branch (`deviceInfo.webAuthnSupport === false`). The "Skip" / "Close" interaction terminates the subflow; it doesn't re-issue the session (you're already authenticated).

---

## 19. Input `ctxKey` ignored — name field doesn't prefill

**Symptom:** Hosted screen's name input shows "Steven Barash" pre-filled (from a previous OAuth or a returning user). BYOS shows an empty input. User types their name again, possibly differently, and the flow stores the new value.

**Root cause:** Input node has `props.ctxKey="displayName"` (or similar). Hosted screen reads `state.context.displayName` and seeds the input. BYOS components default to `form[name] ?? ''` and never look at `ctxKey`.

**Fix:** When parsing, watch for `ctxKey` on input nodes. Wire a one-shot prefill effect:

```jsx
useEffect(() => {
  const seed = state?.context?.displayName // ctxKey from JSON
  if (seed && !form.fullName) {
    setForm({ ...form, fullName: seed })
  }
}, [state?.context?.displayName])
```

Only seed when local field is empty — never overwrite user keystrokes.

---

## Checklist Before Shipping

- [ ] Every flow (main + every invoked subflow, **including post-auth promotion subflows like `add-passkeys`**) has an exported JSON
- [ ] Every unique screen name across all flows has a BYOS component OR an intentional hosted fallback
- [ ] No `<form>` tags inside BYOS components
- [ ] Form keys match input `name` props, verified against JSON
- [ ] OAuth buttons send `provider` in payload
- [ ] Phone inputs normalize to E.164 and gate submit on normalized value
- [ ] `componentsConditions` hide rules mirrored via context reads
- [ ] Shared screen names disambiguated via context, with heuristic documented at top of router (or screens renamed in console)
- [ ] WebAuthn screens fire `state.next(interaction)` only — no `navigator.credentials.*` calls
- [ ] Input `ctxKey` prefills wired (one-shot effect, only seed empty fields)
- [ ] `Device Not Supported` branch has its own BYOS component
- [ ] `onSuccess` calls auth-cache invalidation
- [ ] Diagnostic logs gated on `import.meta.env.DEV`
- [ ] Walk every user journey: no `[byos] no handler` warnings
