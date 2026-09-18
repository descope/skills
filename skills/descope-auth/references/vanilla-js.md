# Vanilla JavaScript / HTML Integration

This covers apps with no frontend framework (plain HTML/JS). It uses two packages:

- `@descope/web-component` — the `<descope-wc>` custom element that renders a Descope
  Flow (login/signup screens). Framework-agnostic; this is the same element the
  React SDK renders internally, but used directly it does not provide session
  management or hooks.
- `@descope/web-js-sdk` — the client SDK for session storage, refresh, logout, and
  (optionally) driving your own custom login UI without Descope Flows.

## Install

```bash
npm install @descope/web-component @descope/web-js-sdk
```

Or via CDN script tags, with no build step:

```html
<head>
  <script src="https://descopecdn.com/npm/@descope/web-component@4.3.3/dist/index.js"></script>
  <script src="https://descopecdn.com/npm/@descope/web-js-sdk@1.53.0/dist/index.umd.js"></script>
</head>
```

Pin to whatever current versions are published on npm for `@descope/web-component`
and `@descope/web-js-sdk` — the CDN URLs above are illustrative.

## 1. Render a Flow with the Custom Element

```html
<!DOCTYPE html>
<html>
  <head>
    <script src="https://descopecdn.com/npm/@descope/web-component@4.3.3/dist/index.js"></script>
  </head>
  <body>
    <descope-wc project-id="<project-id>" flow-id="sign-up-or-in"></descope-wc>

    <script>
      const wcElement = document.querySelector('descope-wc');

      wcElement.addEventListener('success', (e) => {
        console.log('Authenticated:', e.detail);
        window.location.href = '/dashboard';
      });

      wcElement.addEventListener('error', (e) => {
        console.error('Auth failed:', e.detail.errorMessage);
      });

      wcElement.addEventListener('ready', () => {
        // remove/hide a loading indicator
      });
    </script>
  </body>
</html>
```

When using the SDK's `autoRefresh` feature, call `sdk.refresh()` inside your
`success` handler.

### Useful `<descope-wc>` attributes

| Attribute | Values | Default |
|---|---|---|
| `base-url` | custom Descope base URL (custom domain) | `""` |
| `theme` | `light` \| `dark` \| `os` | `light` |
| `debug` | `true` \| `false` | `false` |
| `auto-focus` | `true` \| `false` \| `skipFirstScreen` | `true` |
| `validate-on-blur` | `true` \| `false` | `false` |
| `send-session-token` | `true` \| `false` — expose the current session JWT's claims to the flow via `sessionJwtClaims` | `false` |
| `storage-prefix` | string prefix for localStorage keys | `""` |

Full attribute list, `errorTransformer`/`logger`/`onScreenUpdate` properties, and the
`context` object shape are in the
[`@descope/web-component` docs](https://www.npmjs.com/package/@descope/web-component).

## 2. Initialize the Client SDK for Session Management

```javascript
import createSdk from '@descope/web-js-sdk';
// or, via the UMD build loaded from a <script> tag: window.createSdk / global `sdk`

const sdk = createSdk({ projectId: '<project-id>' });
```

`createSdk` accepts the same options as `AuthProvider` in the React SDK: `baseUrl`,
`baseCdnUrl`, `persistTokens` (default `true`), `autoRefresh` (default `true`),
`sessionTokenViaCookie`, `storeLastAuthenticatedUser`.

### Persist the session across every page

On every authenticated page (in a `<script>` tag near the top), call `refresh()` so
the session stays valid as the user navigates:

```html
<script src="https://descopecdn.com/npm/@descope/web-js-sdk@1.53.0/dist/index.umd.js"></script>
<script>
  sdk.refresh({ skipIfNoSession: true }); // avoids a network call when no session exists yet
</script>
```

### Session helpers

```javascript
sdk.getSessionToken();
sdk.getRefreshToken();      // unavailable if refresh tokens are stored in httpOnly cookies
sdk.isSessionTokenExpired(token);
sdk.isRefreshTokenExpired(token);
sdk.getJwtRoles(token, tenantId);       // tenantId optional
sdk.getJwtPermissions(token, tenantId); // tenantId optional
sdk.getCurrentTenant(token);
sdk.logout();
sdk.logoutAll();
sdk.me();       // refetch current user
sdk.selectTenant(tenantId);
```

## 3. Custom Login UI Without Flows (Optional)

If you're not using a Descope Flow and want to build your own login screen, the SDK
exposes auth-method namespaces directly, e.g. OTP:

```javascript
// Sign up (or use signIn / signUpOrIn)
const resp = await sdk.otp.signUp.email(
  'email@company.com',
  { name: 'Joe Person', email: 'email@company.com' },
);
if (!resp.ok) {
  console.error(resp.error.errorMessage);
}

// Verify the code the user received
const verifyResp = await sdk.otp.verify.email('email@company.com', '123456');
if (verifyResp.ok) {
  // verifyResp.data has sessionJwt / refreshJwt / user
}
```

The same pattern (`signUp` / `signIn` / `signUpOrIn` / `verify`, keyed by delivery
method `email` | `sms` | `voice`) applies to `sdk.otp`, and analogous namespaces exist
for other methods (`sdk.magicLink`, `sdk.password`, `sdk.oauth`, etc.) — check the
[Descope docs](https://docs.descope.com/auth-methods) for the specific method you
need. **Prefer rendering a Descope Flow with `<descope-wc>` over hand-building this
UI** — Flows keep auth logic centrally configurable without a redeploy.

## Server-Side Session Validation

Always validate the session token server-side before trusting a request — see
`references/backend.md`.
