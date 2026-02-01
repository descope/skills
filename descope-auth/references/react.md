# React Integration

## Install

```bash
npm install @descope/react-sdk
```

## Environment Variables

```bash
REACT_APP_DESCOPE_PROJECT_ID=<project-id>
```

## 1. Wrap App with AuthProvider

```tsx
// src/App.tsx
import { AuthProvider } from '@descope/react-sdk';

function App() {
  return (
    <AuthProvider projectId={process.env.REACT_APP_DESCOPE_PROJECT_ID}>
      <Router />
    </AuthProvider>
  );
}
```

## 2. Create Login Page

```tsx
// src/pages/Login.tsx
import { Descope } from '@descope/react-sdk';
import { useNavigate } from 'react-router-dom';

function LoginPage() {
  const navigate = useNavigate();

  return (
    <Descope
      flowId="sign-up-or-in"
      onSuccess={(e) => {
        console.log('Authenticated:', e.detail.user);
        navigate('/dashboard');
      }}
      onError={(e) => console.error('Auth failed:', e.detail)}
    />
  );
}
```

## 3. Protect Routes

```tsx
// src/components/ProtectedRoute.tsx
import { useSession } from '@descope/react-sdk';
import { Navigate } from 'react-router-dom';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isSessionLoading } = useSession();

  if (isSessionLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <Navigate to="/login" />;

  return <>{children}</>;
}
```

## 4. Access User Data

```tsx
// src/components/UserProfile.tsx
import { useUser, useDescope } from '@descope/react-sdk';

function UserProfile() {
  const { user, isUserLoading } = useUser();
  const { logout } = useDescope();

  if (isUserLoading) return <div>Loading...</div>;

  return (
    <div>
      <p>Welcome, {user?.name}</p>
      <p>Email: {user?.email}</p>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}
```

## 5. Router Setup

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@descope/react-sdk';
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AuthProvider projectId={process.env.REACT_APP_DESCOPE_PROJECT_ID}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```
