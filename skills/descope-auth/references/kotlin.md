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

Requires `minSdk` 24+.

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
  `onUpdateTokens(session)` and `onUpdateUser(session)`.

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
