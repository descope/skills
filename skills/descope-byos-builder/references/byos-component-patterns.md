# BYOS Component Patterns

Positive patterns for building Descope BYOS React screens. Every snippet
assumes you have already run `parse-flow.mjs` and know the real screen names,
interaction IDs, and form-key `name` props for your flows.

---

## 1. Core wiring

`onScreenUpdate` is the BYOS entry point. Store `{ screenName, context, next }`
in React state; return `true` to own the screen, `false` to fall back to hosted.

```tsx
// src/auth/FlowEntry.tsx
import { AuthProvider, Descope } from '@descope/react-sdk'
import { useState } from 'react'

interface ByosState {
  screenName: string
  context: {
    form?:   Record<string, unknown>
    sentTo?: { maskedEmail?: string; maskedPhone?: string }
    error?:  { code: string; text: string; description?: string; message?: string }
    [key: string]: unknown
  }
  next: (interactionId: string, form?: Record<string, unknown>) => Promise<void>
}

export function FlowEntry({ flowId }: { flowId: string }) {
  const [state, setState] = useState<ByosState | null>(null)

  return (
    <AuthProvider projectId={import.meta.env.VITE_DESCOPE_PROJECT_ID}>
      <Descope
        flowId={flowId}
        onScreenUpdate={(screenName, context, next) => {
          setState({ screenName, context, next })
          return true  // false → let hosted render this screen
        }}
        onSuccess={(e) => {
          if (import.meta.env.DEV) {
            console.info('[byos] success', {
              userClaimKeys: Object.keys(e.detail.user ?? {}),
              sessionToken: e.detail.sessionJwt ? '(set)' : '(absent)',
            })
          }
          // invalidate auth caches here, then navigate (see § 5)
        }}
        onError={(e) => console.error('[byos] error', e.detail)}
      >
        {state && <ScreenRouter state={state} />}
      </Descope>
    </AuthProvider>
  )
}
```

---

## 2. Screen router

Map screen names to components. Return `null` for any screen you let hosted render.

```tsx
// src/auth/ScreenRouter.tsx
const SCREENS: Record<string, React.ComponentType<{ state: ByosState }>> = {
  'Email Entry':  EmailEntryScreen,
  'Verify OTP':   OtpScreen,
  'Enter Phone':  PhoneScreen,
  // one entry per unique screen name across ALL flows (main + subflows)
}

export function ScreenRouter({ state }: { state: ByosState }) {
  const Screen = SCREENS[state.screenName]
  return Screen ? <Screen state={state} /> : null
}
```

---

## 3. Screen component skeleton

Every BYOS screen: `<div>` (never `<form>`), controlled input, button with `onClick`
+ Enter handler, error display. Replace `SUBMIT` and `fieldName` with values from
`parse-flow.mjs` output.

```tsx
const SUBMIT = 'submit'  // ← interactionId from flow JSON

export function TemplateScreen({ state }: { state: ByosState }) {
  const [value, setValue] = useState('')
  const [busy, setBusy]   = useState(false)

  const submit = async () => {
    if (busy) return
    setBusy(true)
    await state.next(SUBMIT, { fieldName: value })
    setBusy(false)
  }

  return (
    <div>
      <input
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); submit() } }}
        disabled={busy}
      />
      <button onClick={submit} disabled={busy || !value}>
        {busy ? 'Please wait…' : 'Continue'}
      </button>
      {state.context.error?.text && (
        <p role="alert">{state.context.error.text}</p>
      )}
    </div>
  )
}
```

---

## 4. Common screen patterns

### 4a. Email entry

```tsx
const SUBMIT_EMAIL = 'submit-email'  // from flow JSON

export function EmailEntryScreen({ state }: { state: ByosState }) {
  const [email, setEmail] = useState('')
  const submit = () => state.next(SUBMIT_EMAIL, { email })
  return (
    <div>
      <input value={email} onChange={e => setEmail(e.target.value)}
             onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); submit() } }}
             type="email" autoComplete="email" />
      <button onClick={submit} disabled={!email}>Continue</button>
      {state.context.error?.text && <p role="alert">{state.context.error.text}</p>}
    </div>
  )
}
```

### 4b. OTP entry with resend guard

Resend must fire once per screen mount, not on every render — `state.next` is a
fresh reference on every update, so depend only on the stable error code.

```tsx
const VERIFY = 'verify-code'  // from flow JSON
const RESEND = 'resend-code'  // from flow JSON

export function OtpScreen({ state }: { state: ByosState }) {
  const [code, setCode] = useState('')
  const firedRef = useRef(false)
  const nextRef  = useRef(state.next); nextRef.current = state.next

  useEffect(() => {
    if (state.context.error?.code === 'E061104') {
      if (!firedRef.current) { firedRef.current = true; nextRef.current(RESEND, {}) }
    } else {
      firedRef.current = false
    }
  }, [state.context.error?.code])  // only the stable code, not state.next

  const submit = () => state.next(VERIFY, { code })
  return (
    <div>
      <p>Code sent to {state.context.sentTo?.maskedEmail ?? state.context.sentTo?.maskedPhone}</p>
      <input value={code} onChange={e => setCode(e.target.value)}
             onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); submit() } }}
             inputMode="numeric" autoComplete="one-time-code" />
      <button onClick={submit} disabled={code.length < 4}>Verify</button>
      <button onClick={() => state.next(RESEND, {})}>Resend</button>
      {state.context.error?.text && <p role="alert">{state.context.error.text}</p>}
    </div>
  )
}
```

### 4c. Phone entry with E.164 normalization

Gate the button on the normalized value — `" - - "` is truthy but produces `''`.

```tsx
const SUBMIT_PHONE = 'submit-phone'  // from flow JSON

function toE164(raw: string): string {
  const trimmed = (raw ?? '').trim()
  if (!trimmed) return ''
  const digits = trimmed.replace(/[^\d]/g, '')
  if (!digits) return ''
  if (trimmed.startsWith('+')) return `+${digits}`
  if (digits.length === 10) return `+1${digits}`  // adjust default country
  return `+${digits}`
}

export function PhoneScreen({ state }: { state: ByosState }) {
  const [phone, setPhone] = useState('')
  const phoneE164 = toE164(phone)
  const submit = () => state.next(SUBMIT_PHONE, { phone: phoneE164 })
  return (
    <div>
      <input value={phone} onChange={e => setPhone(e.target.value)}
             onKeyDown={e => { if (e.key === 'Enter' && phoneE164) { e.preventDefault(); submit() } }}
             type="tel" autoComplete="tel" placeholder="+1 555 000 0000" />
      <button onClick={submit} disabled={!phoneE164}>Send code</button>
      {state.context.error?.text && <p role="alert">{state.context.error.text}</p>}
    </div>
  )
}
```

### 4d. OAuth social buttons

`provider` must be in the payload — it is not inferred from the interaction ID.

```tsx
const OAUTH = 'oauth-start'  // from flow JSON

export function SocialButtons({ state }: { state: ByosState }) {
  const oauthWith = (provider: string) => state.next(OAUTH, { provider })
  return (
    <div>
      <button onClick={() => oauthWith('google')}>Continue with Google</button>
      <button onClick={() => oauthWith('github')}>Continue with GitHub</button>
      <button onClick={() => oauthWith('apple')}>Continue with Apple</button>
      {state.context.error?.text && <p role="alert">{state.context.error.text}</p>}
    </div>
  )
}
```

---

## 5. onSuccess — `e.detail` shape and cache invalidation

Anonymous-to-verified upgrades can reuse the same `sub`, so userId-keyed caches
never auto-invalidate. Call `invalidate` unconditionally before navigating.

```tsx
// e.detail shape:
// {
//   user:       { userId, name, email, loginIds, ... }
//   sessionJwt: string
//   refreshJwt: string
// }

import { useQueryClient } from '@tanstack/react-query'

function useByosSuccess() {
  const queryClient = useQueryClient()
  const navigate    = useNavigate()

  return (e: CustomEvent) => {
    if (import.meta.env.DEV) {
      console.info('[byos] success', {
        userClaimKeys: Object.keys(e.detail.user ?? {}),
        sessionToken: e.detail.sessionJwt ? '(set)' : '(absent)',
      })
    }
    queryClient.invalidateQueries()  // unconditional — sub may be unchanged
    navigate('/dashboard')
  }
}
```

---

## 6. Screen name collision router

When two tasks share a screen name, dispatch on a context field that only one
path populates. Trace both paths with `parse-flow.mjs` before picking the field.
Document the heuristic at the top of every router — see SKILL.md § Heuristics.

```tsx
// "Welcome Screen": task-A = email entry (no prior form.email)
//                   task-B = password entry (form.email already in context)
// Signal: Boolean(state.context.form?.email)
export function WelcomeRouter({ state }: { state: ByosState }) {
  const Screen = state.context.form?.email ? PasswordScreen : EmailEntryScreen
  return <Screen state={state} />
}
```

---

## 7. ctxKey prefill

When `parse-flow.mjs` reports `ctxKey="someKey"` on an input node, seed the
local field from context once on mount — never overwrite user keystrokes.

```tsx
// Input node: ctxKey="displayName" → seed form.fullName
useEffect(() => {
  const seed = state.context.displayName as string | undefined
  if (seed && !form.fullName) setForm(f => ({ ...f, fullName: seed }))
}, [state.context.displayName])
```

---

## Reference

Official BYOS sample app: https://github.com/descope-sample-apps/byos-sample-app
