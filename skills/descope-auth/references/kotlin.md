# Kotlin Integration

Uses the Descope Android SDK (`com.descope:descope-kotlin`). Flows run inside a
`DescopeFlowView` (an embedded WebView) and the SDK's session manager persists and
refreshes the session.

## Install

```kotlin
// app/build.gradle.kts
android {
    buildFeatures { buildConfig = true } // needed for BuildConfig.DEBUG below
}

dependencies {
    implementation("com.descope:descope-kotlin:0.23.0")
}
```

Requires `minSdk` 24+. `0.23.0` is the version this reference was verified against, not necessarily the latest. Check the latest release on [Maven Central](https://central.sonatype.com/artifact/com.descope/descope-kotlin) and pin that exact version. 

## 1. Initialize the SDK in the Application Class

```kotlin
// app/src/main/java/com/example/app/MyApplication.kt
package com.example.app // BuildConfig resolves from the app's namespace

import android.app.Application
import com.descope.Descope
import com.descope.sdk.DescopeLogger

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        Descope.setup(this, projectId = "<project-id>") {
            // baseUrl = "https://auth.example.com" // only if using a custom domain
            if (BuildConfig.DEBUG) logger = DescopeLogger.debugLogger
        }
    }
}
```

Register the class in `AndroidManifest.xml` with `<application android:name=".MyApplication" ...>`.
Call `Descope.setup()` once, before any other Descope API. It creates the session manager,
which loads any saved session.

## 2. Run a Flow

`DescopeFlowView` is an Android `View`. Add it to the UI with Compose, XML or code, always with
an Activity context. Pick the option that matches the app:

| If the app... | Use |
|---|---|
| builds its UI with Jetpack Compose (`setContent { ... }`) | Option A: Compose |
| uses XML layouts / Views | Option B: a separate `LoginActivity` |

Either way, in `onSuccess` hand the session to the session manager and switch the UI to the
signed-in state right there. The launch check (section 3) only runs when a screen is created,
and the session manager calls no listener for a new sign-in.

`DescopeFlow.hosted(flowId)` runs a Descope-hosted flow. Use a flow ID from the Valid Flow
IDs table in SKILL.md. For a self-hosted flow, use `DescopeFlow("<flow-url>")`. The
listener's fourth method, `onNavigation(uri)`, is optional.

To verify, confirm `onReady()` fires. With `DescopeLogger.debugLogger` enabled, SDK logs
appear in Logcat prefixed `[DescopeAndroid]`.

Magic Link, browser-based OAuth and SSO need a verified
[Android App Link](https://developer.android.com/training/app-links) to return to the app.
Set the matching `*Redirect` property below, and pass the incoming link to
`Descope.handleUri(uri)` in the activity that receives it.

Optional `DescopeFlow` properties: `oauthNativeProvider` (native Sign in with Google, e.g.
`OAuthProvider.Google`), `oauthRedirect`, `ssoRedirect`, `magicLinkRedirect`,
`externalAuthRedirect` (`oauthRedirect`, `ssoRedirect` and `externalAuthRedirect` also have a
`*CustomScheme` variant, a less secure fallback for browsers that ignore App Links),
`clientInputs`, `sessionProvider`, `hooks`, `presentation`, `sdk`.

### Option A: Jetpack Compose

Show the flow inside the app's own Activity with `AndroidView`, and keep the signed-in state in
Compose state that `onSuccess` updates.

```kotlin
// app/src/main/java/com/example/app/SignInScreen.kt
package com.example.app

import android.util.Log
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import com.descope.Descope
import com.descope.android.DescopeFlow
import com.descope.android.DescopeFlowView
import com.descope.session.DescopeSession
import com.descope.types.AuthenticationResponse
import com.descope.types.DescopeException

@Composable
fun SignInScreen(onSignedIn: () -> Unit, modifier: Modifier = Modifier) {
    val currentOnSignedIn by rememberUpdatedState(onSignedIn)
    AndroidView(
        modifier = modifier.fillMaxSize(),
        // under setContent in an Activity, this context is that Activity
        factory = { context ->
            DescopeFlowView(context).apply {
                listener = object : DescopeFlowView.Listener {
                    override fun onReady() {
                        // hide any loading indicator
                    }

                    override fun onSuccess(response: AuthenticationResponse) {
                        Descope.sessionManager.manageSession(DescopeSession(response))
                        currentOnSignedIn() // switch to the signed-in UI now
                    }

                    override fun onError(exception: DescopeException) {
                        Log.e("Descope", "Flow failed: ${exception.desc}", exception)
                    }
                }
                startFlow(DescopeFlow.hosted("sign-up-or-in"))
            }
        },
    )
}
```

```kotlin
// app/src/main/java/com/example/app/MainActivity.kt
package com.example.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.descope.Descope

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            // the launch check from section 3, kept in state so the UI can change after sign-in
            var signedIn by remember {
                val session = Descope.sessionManager.session
                mutableStateOf(session != null && !session.refreshToken.isExpired)
            }
            if (signedIn) {
                // your signed-in UI; after logging out (section 5), set signedIn = false
            } else {
                SignInScreen(onSignedIn = { signedIn = true })
            }
        }
    }
}
```

Declare this Activity in `AndroidManifest.xml` with the `android:configChanges` attribute
described under Option B, for the same reason.

### Option B: a separate LoginActivity

```kotlin
// app/src/main/java/com/example/app/LoginActivity.kt
package com.example.app

import android.content.Intent
import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import com.descope.Descope
import com.descope.android.DescopeFlow
import com.descope.android.DescopeFlowView
import com.descope.session.DescopeSession
import com.descope.types.AuthenticationResponse
import com.descope.types.DescopeException

class LoginActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val flowView = DescopeFlowView(this) // must be an Activity context
        setContentView(flowView)

        flowView.listener = object : DescopeFlowView.Listener {
            override fun onReady() {
                // hide any loading indicator
            }

            override fun onSuccess(response: AuthenticationResponse) {
                Descope.sessionManager.manageSession(DescopeSession(response))
                startActivity(Intent(this@LoginActivity, MainActivity::class.java))
                finish()
            }

            override fun onError(exception: DescopeException) {
                Log.e("Descope", "Flow failed: ${exception.desc}", exception)
            }
        }

        flowView.startFlow(DescopeFlow.hosted("sign-up-or-in"))
    }
}
```

After sign-in, this example opens a new `MainActivity`. A new screen runs the session check from
section 3, finds the session, and shows the signed-in UI.

Do not just call `finish()` to go back to a screen that is already open. That screen does not
re-check the session, so it keeps showing the signed-out UI. If you must go back to an open
screen, have it read `Descope.sessionManager.session` again in `onResume()` and update its UI.

Declare `LoginActivity` in `AndroidManifest.xml` with
`android:configChanges="orientation|screenSize|screenLayout|keyboardHidden|uiMode"`. Otherwise
rotating the device or switching dark mode recreates the activity and restarts the flow.

## 3. Check the Session on Launch

```kotlin
// e.g. in your launcher Activity's onCreate()
val session = Descope.sessionManager.session
if (session != null && !session.refreshToken.isExpired) {
    // show the logged-in UI
} else {
    // show LoginActivity
}
```

Check `refreshToken`, not `sessionToken`. The session JWT is short-lived and may already be
expired at launch. The session manager refreshes it automatically while the app is in the
foreground.

This check only runs when the screen is created. After a flow succeeds while the app is open,
update the UI from `onSuccess`, as in section 2. `manageSession()` calls no listener when it
stores a new sign-in, so a listener added with `addListener()` won't fire.

> **Important:** `DescopeSessionManager` has no `isAuthenticated`, `user`, `me()` or
> `logout()` members. Use the check above, `session.user`, `Descope.auth.me()` and
> `Descope.auth.revokeSessions()` instead.

## 4. Access User Data

```kotlin
// e.g. in MainActivity, where nameText and emailText are TextViews
val user = Descope.sessionManager.session?.user
nameText.text = user?.name
emailText.text = user?.email
```

`user` is a `DescopeUser` with these fields: `userId`,
`loginIds`, `name`, `givenName`, `middleName`, `familyName`, `email`, `isVerifiedEmail`,
`phone`, `isVerifiedPhone`, `picture`, `customAttributes`, `status`, `authentication`,
`authorization`, `isUpdateRequired`, `createdAt`. Read roles and permissions with
`session.roles(tenantId)` and `session.permissions(tenantId)` (pass `null` for
project-level). `session.claims` has the custom claims.

The saved user doesn't update on its own. To get the latest user details after they change
outside the app (e.g. an admin edit in the Descope console):

```kotlin
import androidx.lifecycle.lifecycleScope
import com.descope.Descope
import com.descope.types.DescopeException
import kotlinx.coroutines.launch

// in an Activity or Fragment (lifecycleScope runs on the main thread)
lifecycleScope.launch {
    val session = Descope.sessionManager.session ?: return@launch
    try {
        val user = Descope.auth.me(session.refreshJwt)
        Descope.sessionManager.updateUser(user)
    } catch (e: DescopeException) {
        // keep showing the saved user, e.g. when offline
    }
}
```

## 5. Log Out

```kotlin
import androidx.lifecycle.lifecycleScope
import com.descope.Descope
import com.descope.types.DescopeException
import com.descope.types.RevokeType
import kotlinx.coroutines.launch

// in an Activity or Fragment
fun logout() {
    // read the refresh JWT before clearing, otherwise there is nothing left to revoke
    val refreshJwt = Descope.sessionManager.session?.refreshJwt ?: return
    Descope.sessionManager.clearSession()
    // use a scope that outlives this screen if you finish() right after logout
    lifecycleScope.launch {
        try {
            Descope.auth.revokeSessions(RevokeType.CurrentSession, refreshJwt)
        } catch (e: DescopeException) {
            // best effort: the local session is already cleared
        }
    }
}
```

Use `RevokeType.AllSessions` to sign the user out on every device.

## 6. Call Your Backend

To send the session to your API, call `connection.setAuthorization(Descope.sessionManager)`
(import `com.descope.extensions.setAuthorization`) on a `URLConnection` from a coroutine. It
refreshes the session if needed and sets the `Authorization: Bearer` header. Always validate
the token server-side. See `references/backend.md`.

## Session Manager API

Main `Descope.sessionManager` members:

- `session` — the current `DescopeSession?` (`sessionJwt`, `refreshJwt`, `sessionToken`,
  `refreshToken`, `user`, `claims`, `roles()`, `permissions()`)
- `manageSession(session)`, `clearSession()`, `updateUser(user)`, `updateTokens(refreshResponse)`
- `refreshSessionIfNeeded()` (suspend)
- `addListener(listener)` / `removeListener(listener)`. `Listener` has
  `onUpdateTokens(session)` and `onUpdateUser(session)`. They fire when an existing session's
  tokens are refreshed or updated, or its user is updated, not when a flow signs a user in.

Call the non-suspend members from the main thread.

`Descope.auth` has `me`, `tenants`, `refreshSession`, `migrateSession` and `revokeSessions`.

## DO NOT (Android)

- DO NOT call `Descope.setup()` in an Activity. Call it once in `Application.onCreate()`.
- DO NOT persist `sessionJwt`/`refreshJwt` yourself (SharedPreferences, DataStore, Room).
  The session manager already stores them in `EncryptedSharedPreferences`.
- DO NOT use deprecated or invented APIs: use `DescopeFlowView` (not `Descope.flow`),
  `startFlow()` (not `run()`), `revokeSessions()` (not `auth.logout()`),
  `DescopeLogger.debugLogger` (not `DescopeLogger()`), and `oauthNativeProvider`
  (not `oauthProvider`).
- DO NOT create `DescopeFlowView` with the application context.
- DO NOT ship `DescopeLogger.unsafeLogger` in release builds.
- DO NOT rely on the launch check or a session listener to show the signed-in UI after a flow.
  Switch the UI in `onSuccess`, or start a screen that runs the launch check (section 2).
