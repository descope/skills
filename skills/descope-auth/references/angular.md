# Angular Integration

## Install

```bash
npm install @descope/angular-sdk
```

Add Descope's type definitions to `tsconfig.json`:

```json
{
  "compilerOptions": {
    "typeRoots": ["./node_modules/@descope"]
  }
}
```

## 1. Register the Descope Angular Module

```typescript
// app.module.ts
import { NgModule, APP_INITIALIZER } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { DescopeAuthModule, DescopeAuthService, descopeInterceptor } from '@descope/angular-sdk';
import {
  HttpClientModule,
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import { zip } from 'rxjs';
import { AppComponent } from './app.component';

export function initializeApp(authService: DescopeAuthService) {
  return () => zip([authService.refreshSession(), authService.refreshUser()]);
}

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    DescopeAuthModule.forRoot({
      projectId: 'YOUR_PROJECT_ID',
      // baseUrl: 'https://auth.app.example.com', // only if using a custom domain
    }),
  ],
  providers: [
    {
      provide: APP_INITIALIZER,
      useFactory: initializeApp,
      deps: [DescopeAuthService],
      multi: true,
    },
    provideHttpClient(withInterceptors([descopeInterceptor])),
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
```

`descopeInterceptor` is an Angular `HttpClient` interceptor the SDK ships for
attaching the session token to outgoing requests; register it via
`withInterceptors([descopeInterceptor])` as shown above rather than wiring your own
`Authorization` header logic.

`DescopeAuthModule.forRoot()` accepts the same client options documented for the
React SDK's `AuthProvider` (see `references/react.md`): `persistTokens`,
`autoRefresh`, `sessionTokenViaCookie`, `storeLastAuthenticatedUser`,
`keepLastAuthenticatedUserAfterLogout`.

## 2. Add the Flow Component to Your Template

```html
<!-- app.component.html -->
<div style="max-width: 1000px; margin: 0 auto; place-items: center;">
  <descope
    flowId="sign-up-or-in"
    (success)="onSuccess($event)"
    (error)="onError($event)"
  ></descope>
</div>
```

## 3. Use the Auth Service

```typescript
// app.component.ts
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { DescopeAuthService } from '@descope/angular-sdk';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
})
export class AppComponent implements OnInit {
  isAuthenticated = false;
  userName = '';

  constructor(
    private router: Router,
    private authService: DescopeAuthService,
  ) {}

  ngOnInit() {
    this.authService.session$.subscribe((session) => {
      this.isAuthenticated = session.isAuthenticated;
    });

    this.authService.user$.subscribe((descopeUser) => {
      if (descopeUser.user) {
        this.userName = descopeUser.user.name ?? '';
      }
    });
  }

  onSuccess(event: CustomEvent) {
    this.router.navigate(['/dashboard']);
  }

  onError(event: CustomEvent) {
    console.error('Auth failed:', event.detail);
  }

  logout() {
    this.authService.descopeSdk.logout();
  }
}
```

`DescopeAuthService` exposes:

- `session$` — observable of `{ isAuthenticated, ... }`.
- `user$` — observable of `{ user, isUserLoading }`.
- `descopeSdk` — the underlying core SDK instance (same shape as `useDescope()` in
  React: `logout()`, `logoutAll()`, `refresh()`, `selectTenant()`, `me()`, etc. — see
  `references/react.md`'s Core SDK Functions section for the full list).
- `refreshSession()` / `refreshUser()` — used above in `APP_INITIALIZER` to hydrate
  the session/user before the app renders.

## Protecting Routes

Use `session$` (or `descopeSdk`'s session helpers) inside an Angular route guard to
redirect unauthenticated users, the same way `ProtectedRoute` does in the React
reference — there is no framework-specific guard shipped by the SDK, so gate routes
with a standard Angular `CanActivate` guard that checks `isAuthenticated` from
`session$`.

## Server-Side Session Validation

Always validate the session token server-side before trusting a request — see
`references/backend.md`. The Angular SDK only manages the client-side session; it
does not replace backend validation.
