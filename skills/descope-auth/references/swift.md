# Swift Integration

Uses the Descope Swift SDK (`DescopeKit`). Flows run inside a `DescopeFlowView` or
`DescopeFlowViewController` (an embedded `WKWebView`) and the SDK's session manager persists
the session in the Keychain and refreshes it.

## Install

In Xcode, go to **File > Add Package Dependencies**, enter
`https://github.com/descope/descope-swift`, set the dependency rule to **Exact Version**
`0.12.0`, and add the `DescopeKit` product to the app target. In a `Package.swift`:

```swift
dependencies: [
    .package(url: "https://github.com/descope/descope-swift", exact: "0.12.0"),
],
targets: [
    .target(name: "MyApp", dependencies: [
        .product(name: "DescopeKit", package: "descope-swift"),
    ]),
]
```

Requires iOS 13+ (iOS 14+ for the SwiftUI examples below) and Xcode 16+ (Swift 6 tools). `0.12.0` is the version this reference was
verified against, not necessarily the latest. Check the latest release on
[GitHub](https://github.com/descope/descope-swift/releases) and pin that exact version.
Minor releases before 1.0 can contain breaking changes.

## 1. Initialize the SDK at Launch

SwiftUI:

```swift
// MyApp.swift
import SwiftUI
import DescopeKit

@main
struct MyApp: App {
    init() {
        Descope.setup(projectId: "<project-id>") { config in
            // config.baseURL = "https://auth.example.com" // only if using a custom domain
            #if DEBUG
            config.logger = .debugLogger
            #endif
        }
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .onOpenURL { url in
                    Descope.handleURL(url) // only needed for Magic Link, see below
                }
        }
    }
}
```

UIKit: call the same `Descope.setup(...)` at the top of
`application(_:didFinishLaunchingWithOptions:)` in your `AppDelegate`.

Call `Descope.setup()` once, before any other Descope API. It creates the session manager,
which loads any saved session from the Keychain.

## 2. Run a Flow

SwiftUI has no built-in flow view, so wrap `DescopeFlowView` in a `UIViewRepresentable`:

```swift
// DescopeFlowScreen.swift
import SwiftUI
import UIKit
import DescopeKit

struct DescopeFlowScreen: UIViewRepresentable {
    let flowId: String
    var onReady: () -> Void = {}
    let onSuccess: (AuthenticationResponse) -> Void
    let onError: (DescopeError) -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(onReady: onReady, onSuccess: onSuccess, onError: onError)
    }

    func makeUIView(context: Context) -> DescopeFlowView {
        let flowView = DescopeFlowView()
        flowView.delegate = context.coordinator
        flowView.start(flow: DescopeFlow(flowId: flowId))
        return flowView
    }

    func updateUIView(_ flowView: DescopeFlowView, context: Context) {}

    @MainActor
    final class Coordinator: NSObject, DescopeFlowViewDelegate {
        let onReady: () -> Void
        let onSuccess: (AuthenticationResponse) -> Void
        let onError: (DescopeError) -> Void

        init(onReady: @escaping () -> Void, onSuccess: @escaping (AuthenticationResponse) -> Void, onError: @escaping (DescopeError) -> Void) {
            self.onReady = onReady
            self.onSuccess = onSuccess
            self.onError = onError
        }

        func flowViewDidUpdateState(_ flowView: DescopeFlowView, to state: DescopeFlowState, from previous: DescopeFlowState) {}

        func flowViewDidBecomeReady(_ flowView: DescopeFlowView) {
            onReady() // the flow is loaded and rendered
        }

        func flowViewDidInterceptNavigation(_ flowView: DescopeFlowView, url: URL, external: Bool) {
            UIApplication.shared.open(url) // open links in the user's browser
        }

        func flowViewDidFail(_ flowView: DescopeFlowView, error: DescopeError) {
            onError(error)
        }

        func flowViewDidFinish(_ flowView: DescopeFlowView, response: AuthenticationResponse) {
            onSuccess(response)
        }
    }
}
```

Use it from a view, show a loading indicator until the flow is ready, and hand the response
to the session manager:

```swift
// LoginView.swift
import SwiftUI
import DescopeKit

struct LoginView: View {
    let onLogin: () -> Void

    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        if let errorMessage {
            VStack(spacing: 16) {
                Text(errorMessage)
                    .multilineTextAlignment(.center)
                Button("Try Again") {
                    // showing the flow again creates a new flow view
                    isLoading = true
                    self.errorMessage = nil
                }
            }
            .padding()
        } else {
            ZStack {
                DescopeFlowScreen(
                    flowId: "sign-up-or-in",
                    onReady: { isLoading = false },
                    onSuccess: { response in
                        Descope.sessionManager.manageSession(DescopeSession(from: response))
                        onLogin()
                    },
                    onError: { error in
                        print("Flow failed: \(error.desc)") // error.traceId helps Descope support
                        errorMessage = error.localizedDescription
                    }
                )
                .ignoresSafeArea()

                if isLoading {
                    ProgressView()
                }
            }
        }
    }
}
```

All five `DescopeFlowViewDelegate` methods are required. The view is created once per
`DescopeFlowScreen` identity, so the flow keeps its state across SwiftUI re-renders. A failed
flow can't be restarted. To retry, remove the `DescopeFlowScreen` and show it again (as
above), or change its `.id(_:)`, so SwiftUI creates a new flow view.

UIKit: push or present a `DescopeFlowViewController`, which adds a Cancel button when it
is the root of a navigation stack:

```swift
let flowViewController = DescopeFlowViewController()
flowViewController.delegate = self // implement all six DescopeFlowViewControllerDelegate methods
flowViewController.start(flow: DescopeFlow(flowId: "sign-up-or-in"))
navigationController?.pushViewController(flowViewController, animated: true)

// in the delegate
func flowViewControllerDidFinish(_ controller: DescopeFlowViewController, response: AuthenticationResponse) {
    Descope.sessionManager.manageSession(DescopeSession(from: response))
    // show the logged-in UI
}
```

Its delegate methods are `flowViewControllerDidUpdateState`, `flowViewControllerDidBecomeReady`,
`flowViewControllerShouldShowURL` (return `true` to open links in the browser),
`flowViewControllerDidCancel`, `flowViewControllerDidFail` and `flowViewControllerDidFinish`.

`DescopeFlow(flowId:)` runs a Descope-hosted flow. Use a flow ID from the Valid Flow IDs table
in SKILL.md, and create the `DescopeFlow` only after `Descope.setup()`. For a self-hosted flow,
use `DescopeFlow(url: "<flow-url>")`.

To verify, confirm `onReady` (`flowViewDidBecomeReady`) fires. With `.debugLogger` enabled, SDK logs
appear in the Xcode console prefixed `[DescopeKit]`.

Browser-based OAuth, SSO and external auth inside a flow need no app setup. The SDK opens
them in an `ASWebAuthenticationSession` and returns to the flow on its own. nOTP is not
supported in native flows.

`DescopeFlowView` and `DescopeFlowViewController` are iOS-only. On macOS, `DescopeKit`
provides the auth APIs (`Descope.otp`, `Descope.passkey`, etc.) and the session manager, but no
flow views.

Some methods need app setup:

- **Magic Link**: the email link has to open the app as a
  [Universal Link](https://developer.apple.com/documentation/xcode/supporting-universal-links-in-your-app)
  (Associated Domains capability with `applinks:<your-domain>`). Pass the link to
  `Descope.handleURL(url)`, in `.onOpenURL` (SwiftUI) or
  `application(_:continue:restorationHandler:)` (UIKit). Set `flow.magicLinkRedirect` only
  to override the redirect URL configured in the flow or project.
- **Native Sign in with Apple**: set `flow.oauthNativeProvider = .apple`, add the Sign in
  with Apple capability, and set the app's Bundle ID as the Client ID of the Apple provider
  in the [Descope Console](https://app.descope.com/settings/authentication/social).
- **Passkeys**: add an Associated Domains entry `webcredentials:<domain>`, matching the
  domain configured in the Descope Console's Passkeys settings.

Optional `DescopeFlow` properties: `oauthNativeProvider`, `magicLinkRedirect`, `clientInputs`,
`sessionProvider`, `hooks` (e.g. `.setTransparentBody`), `requestTimeoutInterval`, `descope`.

## 3. Check the Session on Launch

```swift
// RootView.swift
import SwiftUI
import DescopeKit

struct RootView: View {
    @State private var isLoggedIn = Self.hasValidSession()

    // HomeView is the app's logged-in screen

    var body: some View {
        if isLoggedIn {
            HomeView(onLogout: { isLoggedIn = false })
        } else {
            LoginView(onLogin: { isLoggedIn = true })
        }
    }

    static func hasValidSession() -> Bool {
        guard let session = Descope.sessionManager.session else { return false }
        return !session.refreshToken.isExpired
    }
}
```

Check `refreshToken`, not `sessionToken`. The session JWT is short-lived and may already be
expired at launch. The session manager refreshes it automatically while the app is running.

> **Important:** `DescopeSessionManager` has no `isAuthenticated`, `user`, `me()` or
> `logout()` members. Use the check above, `session.user`, `Descope.auth.me(refreshJwt:)` and
> `Descope.auth.revokeSessions(_:refreshJwt:)` instead.

## 4. Access User Data

```swift
let user = Descope.sessionManager.session?.user
Text(user?.name ?? "")
Text(user?.email ?? "")
```

`user` is a `DescopeUser` with these fields: `userId`, `loginIds`, `name`, `givenName`,
`middleName`, `familyName`, `email`, `isVerifiedEmail`, `phone`, `isVerifiedPhone`,
`picture`, `customAttributes`, `status`, `authentication`, `authorization`,
`isUpdateRequired`, `createdAt`. Read roles and permissions with
`session.roles(tenant: tenantId)` and `session.permissions(tenant: tenantId)` (pass `nil`
for project-level). `session.claims` has the custom claims.

The saved user doesn't update on its own. To get the latest user details after they change
outside the app (e.g. an admin edit in the Descope console):

```swift
// e.g. call from a SwiftUI .task { await refreshUser() } modifier
@MainActor
func refreshUser() async {
    guard let session = Descope.sessionManager.session else { return }
    do {
        let user = try await Descope.auth.me(refreshJwt: session.refreshJwt)
        Descope.sessionManager.updateUser(with: user)
    } catch {
        // keep showing the saved user, e.g. when offline
    }
}
```

## 5. Log Out

```swift
@MainActor
func logout() {
    // read the refresh JWT before clearing, otherwise there is nothing left to revoke
    guard let refreshJwt = Descope.sessionManager.session?.refreshJwt else { return }
    Descope.sessionManager.clearSession()
    Task {
        // best effort: the local session is already cleared
        try? await Descope.auth.revokeSessions(.currentSession, refreshJwt: refreshJwt)
    }
}
```

Use `.allSessions` to sign the user out on every device.

## 6. Call Your Backend

To send the session to your API, call
`try await request.setAuthorizationHTTPHeaderField(from: Descope.sessionManager)` on a
`URLRequest`. It refreshes the session if needed and sets the
`Authorization: Bearer` header. Always validate the token server-side. See
`references/backend.md`.

## Session Manager API

Main `Descope.sessionManager` members:

- `session` — the current `DescopeSession?` (`sessionJwt`, `refreshJwt`, `sessionToken`,
  `refreshToken`, `user`, `claims`, `roles(tenant:)`, `permissions(tenant:)`)
- `manageSession(_:)`, `clearSession()`, `updateUser(with:)`, `updateTokens(with:)`
- `refreshSessionIfNeeded()` (async)
- `addDelegate(_:)` / `removeDelegate(_:)`. `DescopeSessionManagerDelegate` has
  `sessionManagerDidUpdateTokens(_:session:)` and `sessionManagerDidUpdateUser(_:session:)`.

`DescopeSessionManager` is `@MainActor`, so use it from the main actor.

`Descope.auth` has `me`, `tenants`, `refreshSession`, `migrateSession` and `revokeSessions`.

## DO NOT (iOS)

- DO NOT call `Descope.setup()` in a view's `body` or `onAppear`. Call it once in the `App`
  initializer or `application(_:didFinishLaunchingWithOptions:)`.
- DO NOT persist `sessionJwt`/`refreshJwt` yourself (`UserDefaults`, `@AppStorage`, files,
  Core Data, SwiftData). The session manager already stores them in the Keychain.
- DO NOT use deprecated or invented APIs: use `revokeSessions(.currentSession, refreshJwt:)`
  (not `auth.logout()`), `oauthNativeProvider` (not `oauthProvider`), `oauth.webStart` /
  `oauth.webExchange` (not `oauth.start` / `oauth.exchange`), and `.debugLogger`
  (not `DescopeLogger()`). Some Descope docs pages still show `auth.logout()`, which no
  longer compiles.
- DO NOT add an `ASWebAuthenticationSession` or URL scheme for OAuth/SSO inside a flow.
  The SDK handles it.
- DO NOT ship `.unsafeLogger` in release builds.
