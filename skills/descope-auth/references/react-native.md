# React Native Integration

Uses the Descope React Native SDK (`@descope/react-native-sdk`). Flows run inside a `FlowView`
(a native view that hosts the flow in a WebView on Android and iOS) and the SDK's session
manager persists and refreshes the session. This reference covers a bare React Native app and
an Expo app built with a development build, using in-flow email one-time-code sign-in.
Magic Link, OAuth and SSO need extra deep-link setup (see section 2).

## Files to Change

| File | Change |
|---|---|
| `package.json` | add `@descope/react-native-sdk` |
| `App.tsx` (or your root component) | wrap the app in `AuthProvider` |
| a sign-in screen | render `FlowView` and call `manageSession` in `onSuccess` |
| a signed-in screen | read `session.user`, call your backend, log out |

In-flow email OTP should not need edits to `MainActivity`, `AndroidManifest.xml`, `AppDelegate`
or the Xcode project (autolinking handles the native side); if the build fails, check native
linking first. These are the exported names; you do not need to read anything under
`node_modules/` to confirm them (see "Session API").

## Install

```bash
npm install @descope/react-native-sdk
cd ios && pod install && cd ..   # iOS only
```

`0.13.1` is the version this reference was verified against, not necessarily the latest. Check
the latest on npm and pin that exact version. The package is `@descope/react-native-sdk` (the
repo is called `descope-react-native`). It needs iOS 13+ and Android `minSdk` 24+. On Xcode 26+
with React Native older than 0.84, an `fmt` build error that is not specific to this SDK can
appear; the SDK README has a Podfile workaround.

**Expo:** the SDK contains native code and requires a development build:

```bash
npx expo prebuild
npx expo run:ios       # or: npx expo run:android
npx expo start --dev-client
```

The SDK itself requires no Descope config plugin and no `app.json` change.

## 1. Wrap the App with AuthProvider

```tsx
import { AuthProvider } from '@descope/react-native-sdk';

export default function App() {
  return (
    <AuthProvider
      projectId="<project-id>"
      // baseUrl="https://auth.example.com" // only if using a custom domain
    >
      <Main />
    </AuthProvider>
  );
}
```

Get the Project ID from the Descope console. It is public, not a secret; keep it in whatever
config your app already uses. `AuthProvider` loads any saved session on start and refreshes it
in the background (`autoRefresh` is on by default). `useSession`, `useDescope`,
`useHostedFlowUrl` and `FlowView` only work inside it.

## 2. Run a Flow

`useHostedFlowUrl(flowId)` builds the URL of a Descope-hosted flow. Use the flow ID the user or task
gives you; the IDs in SKILL.md are examples. For a flow you host yourself, pass your own URL in
`flowOptions.url`.

```tsx
import { FlowView, useHostedFlowUrl, useSession } from '@descope/react-native-sdk';
import type { DescopeError } from '@descope/react-native-sdk';

function SignInScreen() {
  const { manageSession } = useSession();
  const flowUrl = useHostedFlowUrl('sign-up-or-in');

  return (
    <FlowView
      style={{ flex: 1 }}
      flowOptions={{ url: flowUrl }}
      onReady={() => {
        // hide any loading indicator
      }}
      onSuccess={async (jwtResponse) => {
        try {
          await manageSession(jwtResponse); // saves the session and updates `session`
        } catch (e) {
          console.error('Could not save the session', e);
        }
      }}
      onError={(error: DescopeError) => {
        console.error('Flow failed', error.errorCode, error.errorDescription);
      }}
    />
  );
}
```

`manageSession` stores the session and updates the `session` value from `useSession()`, so a
screen that renders from `session` switches to the signed-in UI by itself. Give `FlowView` a
size (`flex: 1`); a native view with no size can collapse to zero height.

Redirect methods (Magic Link, OAuth, SSO) need deep links and are out of scope here; see the SDK docs.

## 3. Check the Session on Launch

```tsx
function Main() {
  const { session, isSessionLoading } = useSession();

  if (isSessionLoading) return <ActivityIndicator />; // saved session still loading
  return session ? <HomeScreen /> : <SignInScreen />;
}
```

Always wait for `isSessionLoading` to be `false` before choosing a screen; otherwise a signed-in
user briefly sees the signed-out UI. `session` is `undefined` when nobody is signed in. Render
from `session`, not from your own "signed in" state.

## 4. Access User Data

```tsx
const { session } = useSession();
const user = session?.user;
// user?.email, user?.name, user?.loginIds[0], user?.userId
```

`user` has `userId`, `loginIds`, and optional `email`, `name`, `givenName`, `middleName`,
`familyName`, `phone`, `picture`, `customAttributes`, `status`. Show the email as
`user?.email ?? user?.loginIds?.[0]`. The saved user does not update on its own. To refresh it:

```tsx
const descope = useDescope();
const { session, updateUser } = useSession();

const me = await descope.me(session?.refreshJwt);
if (me.ok && me.data) await updateUser(me.data);
```

## 5. Log Out

```tsx
const descope = useDescope();
const { session, clearSession } = useSession();

async function logout() {
  try {
    await descope.logout(session?.refreshJwt); // ends the session on the server
  } catch (e) {
    // best effort: still clear the local session below
  }
  await clearSession(); // removes the saved session; `session` becomes undefined
}
```

Use `descope.logoutAll(...)` to sign the user out on every device.

## 6. Call Your Backend

```tsx
const { refreshSessionIfAboutToExpire } = useSession();

async function callBackend(path: string) {
  const session = await refreshSessionIfAboutToExpire(); // refreshes if it expires within 60 s
  if (!session) throw new Error('Not signed in');
  return fetch(`https://api.example.com${path}`, {
    headers: { Authorization: `Bearer ${session.sessionJwt}` },
  });
}
```

Send the **session** JWT (`sessionJwt`), never the refresh JWT. Outside a component,
`getCurrentSessionToken()` returns the latest session JWT. Always validate the token on the
server. See `references/backend.md`.

## Putting it together

```tsx
// App.tsx
import React from 'react';
import { ActivityIndicator, Button, StyleSheet, Text, View } from 'react-native';
import {
  AuthProvider,
  FlowView,
  useDescope,
  useHostedFlowUrl,
  useSession,
} from '@descope/react-native-sdk';
import type { DescopeError } from '@descope/react-native-sdk';

function SignInScreen() {
  const { manageSession } = useSession();
  const flowUrl = useHostedFlowUrl('sign-up-or-in');

  return (
    <FlowView
      style={styles.flow}
      flowOptions={{ url: flowUrl }}
      onSuccess={async (jwtResponse) => {
        try {
          await manageSession(jwtResponse);
        } catch (e) {
          console.error('Could not save the session', e);
        }
      }}
      onError={(error: DescopeError) => console.error('Flow failed', error.errorCode)}
    />
  );
}

function HomeScreen() {
  const descope = useDescope();
  const { session, clearSession, refreshSessionIfAboutToExpire } = useSession();
  const user = session?.user;

  async function callBackend(path: string) {
    const fresh = await refreshSessionIfAboutToExpire();
    if (!fresh) throw new Error('Not signed in');
    return fetch(`https://api.example.com${path}`, {
      headers: { Authorization: `Bearer ${fresh.sessionJwt}` },
    });
  }

  async function logout() {
    try {
      await descope.logout(session?.refreshJwt);
    } catch (e) {
      // best effort
    }
    await clearSession();
  }

  return (
    <View style={styles.center}>
      <Text>{user?.email ?? user?.loginIds?.[0]}</Text>
      <Button title="Call backend" onPress={() => callBackend('/me')} />
      <Button title="Log out" onPress={logout} />
    </View>
  );
}

function Main() {
  const { session, isSessionLoading } = useSession();
  if (isSessionLoading) return <ActivityIndicator style={styles.center} />;
  return session ? <HomeScreen /> : <SignInScreen />;
}

export default function App() {
  return (
    <AuthProvider projectId="<project-id>">
      <Main />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  flow: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
```

## Session API

`useSession()` returns:

- `session` — the current `DescopeSession | undefined` (`sessionJwt`, `refreshJwt`, `user`)
- `isSessionLoading` — `true` until the saved session has been loaded
- `manageSession(jwtResponse)` — save a new sign-in; throws if the response has no refresh JWT or user
- `refreshSessionIfAboutToExpire()` — returns the session, refreshed if it expires within 60 s;
  if the refresh fails it returns the unchanged session, and `undefined` when nobody is signed in
- `clearSession()`, `updateUser(user)`, `updateTokens(sessionJwt, refreshJwt)`

Also exported: `AuthProvider`, `FlowView`, `useDescope`, `useHostedFlowUrl`, and
`getCurrentSessionToken()`, `getCurrentRefreshToken()`, `getCurrentUser()` (usable outside
components). `useDescope()` returns the core SDK: `logout`, `logoutAll`, `me`, `refresh`,
`selectTenant`, and the auth-method namespaces such as `otp` and `magicLink`.

## Verify

**JavaScript compiles:**

```bash
npx tsc --noEmit    # or: npm run typecheck
```

**The app is wired and the native side is linked.** A typecheck never reads native projects:

- `package.json` lists `@descope/react-native-sdk`
- the root component is wrapped in `AuthProvider`
- the sign-in screen shows `FlowView` and `onSuccess` calls `manageSession`
- iOS: `pod install` has run (`Podfile.lock` lists `descope-react-native`)
- Expo: the app runs as a development build

For in-flow email OTP, no native file needs editing. Running the app on a simulator or device is
the only way to prove the flow renders; do it only when asked. To debug, pass `logger` to
`AuthProvider` (an object with `log`, `debug`, `warn`, `error`) and confirm `onReady` fires.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Using `useSession`, `useDescope`, `useHostedFlowUrl` or `FlowView` outside `AuthProvider` | They throw (`useDescope` throws when you call one of its methods). Wrap the whole app |
| Choosing a screen before `isSessionLoading` is `false` | Show a loader first, then render from `session` |
| `FlowView` has no size and the flow is not visible | Give it `style={{ flex: 1 }}` inside a sized parent |
| Flow finishes but the app stays signed out | Call `await manageSession(jwtResponse)` in `onSuccess` |
| Holding your own "signed in" state | Render from `session`; it updates after `manageSession` and `clearSession` |
| Sending `refreshJwt` to your backend | Send `sessionJwt`, after `refreshSessionIfAboutToExpire()` |
| Installing a web package (`@descope/react-sdk`, `@descope/web-component`, `@descope/nextjs-sdk`) | Use `@descope/react-native-sdk` |
| Guessing the package name `descope-react-native` | The npm package is `@descope/react-native-sdk` |
| iOS build fails after install, or the native view is missing | Run `pod install` and rebuild; an Expo app requires a development build |
| `descope.logout` can reject (for example offline) and leave the user signed in locally | Wrap `logout` in try/catch and always call `clearSession()` |
| Backend returns 401 after the refresh token expired | Call `clearSession()` so the user returns to sign-in (the SDK does not clear an expired session on launch) |

## DO NOT

- DO NOT use any SDK hook or `FlowView` outside `AuthProvider`.
- DO NOT store the session or tokens yourself (AsyncStorage, MMKV, files, Redux persist). The
  SDK already saves them in the Keychain (iOS) and `EncryptedSharedPreferences` (Android).
- DO NOT invent flow IDs. Use the flow ID you were given; the table in SKILL.md only lists examples.
- DO NOT use `@descope/react-sdk`, `@descope/web-component` or `@descope/web-js-sdk` in a
  React Native app, and do not render the flow in your own `WebView` or open its URL with
  `Linking`. Use `FlowView`.
- DO NOT use the deprecated `useFlow` hook.
- DO NOT put `DESCOPE_MANAGEMENT_KEY` in the app.
- DO NOT log session or refresh tokens.
- DO NOT skip the development build in Expo: the SDK contains native code and requires one.
