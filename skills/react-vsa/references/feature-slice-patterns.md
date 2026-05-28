# Feature Slice Patterns — Complete Examples

## Auth Feature Slice

```
features/auth/
├── components/
│   ├── login-form.tsx
│   ├── register-form.tsx
│   ├── auth-guard.tsx
│   └── user-menu.tsx
├── hooks/
│   ├── use-auth.ts           # Main auth hook
│   ├── use-auth-redirect.ts  # Redirect if not authenticated
│   └── use-session.ts        # Session management
├── api/
│   └── auth-api.ts           # login, register, logout, refresh
├── types/
│   └── auth.types.ts         # User, AuthCredentials, AuthToken
├── store/
│   └── auth-store.ts         # Zustand store for auth state
└── index.ts                  # Public API
```

```typescript
// features/auth/api/auth-api.ts
import { apiClient } from '@/shared/api/client';
import type { AuthCredentials, User, AuthResponse } from '../types/auth.types';

export const authApi = {
  login: (credentials: AuthCredentials) =>
    apiClient.post<AuthResponse>('/auth/login', credentials),
  register: (data: RegisterData) =>
    apiClient.post<AuthResponse>('/auth/register', data),
  logout: () => apiClient.post('/auth/logout'),
  refresh: () => apiClient.post<AuthResponse>('/auth/refresh'),
  me: () => apiClient.get<User>('/auth/me'),
};
```

```typescript
// features/auth/hooks/use-auth.ts
import { useAuthStore } from '../store/auth-store';
import { authApi } from '../api/auth-api';
import type { AuthCredentials, User } from '../types/auth.types';

export function useAuth() {
  const { user, isAuthenticated, setUser, clearUser } = useAuthStore();

  const login = async (credentials: AuthCredentials) => {
    const { data } = await authApi.login(credentials);
    setUser(data.user);
    return data.user;
  };

  const logout = async () => {
    await authApi.logout();
    clearUser();
  };

  return { user, isAuthenticated, login, logout };
}
```

```typescript
// features/auth/index.ts
export { LoginForm } from './components/login-form';
export { RegisterForm } from './components/register-form';
export { AuthGuard } from './components/auth-guard';
export { UserMenu } from './components/user-menu';
export { useAuth } from './hooks/use-auth';
export { useAuthRedirect } from './hooks/use-auth-redirect';
export { useSession } from './hooks/use-session';
export type { User, AuthCredentials, RegisterData } from './types/auth.types';
```

## Product Listing Feature Slice

```
features/products/
├── components/
│   ├── product-card.tsx
│   ├── product-grid.tsx
│   ├── product-filters.tsx
│   ├── product-detail.tsx
│   └── product-skeleton.tsx
├── hooks/
│   ├── use-products.ts       # Fetch + cache products
│   ├── use-product-filters.ts # Filter state
│   └── use-product-detail.ts  # Single product
├── api/
│   └── product-api.ts
├── types/
│   └── product.types.ts
├── store/
│   └── product-store.ts
└── index.ts
```

```typescript
// features/products/hooks/use-products.ts
import { useQuery } from '@tanstack/react-query';
import { productApi } from '../api/product-api';
import { useProductFilters } from './use-product-filters';

export function useProducts() {
  const { filters } = useProductFilters();
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => productApi.getAll(filters),
    staleTime: 5 * 60 * 1000,
  });
}
```

## Cart Feature Slice (Cross-Feature Communication)

```
features/cart/
├── components/
│   ├── cart-drawer.tsx
│   ├── cart-item.tsx
│   └── cart-summary.tsx
├── hooks/
│   ├── use-cart.ts
│   └── use-cart-count.ts     # Lightweight hook for badge
├── api/
│   └── cart-api.ts
├── types/
│   └── cart.types.ts
├── store/
│   └── cart-store.ts         # Zustand — accessible from other features
└── index.ts
```

```typescript
// features/cart/index.ts
export { CartDrawer } from './components/cart-drawer';
export { CartSummary } from './components/cart-summary';
export { useCartCount } from './hooks/use-cart-count';
export { useCart } from './hooks/use-cart';
export type { CartItem } from './types/cart.types';
```

```typescript
// In product-card.tsx (inside products feature):
import { useCart } from '@/features/cart'; // via public API only

export function ProductCard({ product }: { product: Product }) {
  const { addItem } = useCart();
  return (
    <div>
      <h3>{product.name}</h3>
      <button onClick={() => addItem(product)}>Add to Cart</button>
    </div>
  );
}
```

## Dashboard Feature Slice (Composition)

```
features/dashboard/
├── components/
│   ├── dashboard-page.tsx    # Composes widgets from other features
│   ├── stats-card.tsx
│   └── recent-activity.tsx
├── hooks/
│   ├── use-dashboard-stats.ts
│   └── use-recent-activity.ts
├── api/
│   └── dashboard-api.ts
├── types/
│   └── dashboard.types.ts
└── index.ts
```

```typescript
// features/dashboard/components/dashboard-page.tsx
import { useAuth } from '@/features/auth';
import { useCartCount } from '@/features/cart';
import { StatsCard } from './stats-card';
import { RecentActivity } from './recent-activity';
import { useDashboardStats } from '../hooks/use-dashboard-stats';

export function DashboardPage() {
  const { user } = useAuth();
  const cartCount = useCartCount();
  const { data: stats } = useDashboardStats();

  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      <StatsCard stats={stats} />
      <RecentActivity />
      {cartCount > 0 && <p>You have {cartCount} items in cart</p>}
    </div>
  );
}
```

## Feature Slice Checklist

When creating a new feature slice, verify:

- [ ] `features/{name}/` directory exists
- [ ] `components/` — feature-specific React components
- [ ] `hooks/` — feature-specific custom hooks
- [ ] `api/` — feature-specific API functions
- [ ] `types/` — feature-specific TypeScript types
- [ ] `index.ts` — explicit named exports only (no `export *`)
- [ ] No direct imports from other feature internals
- [ ] Tests colocated with source files
- [ ] Zustand store scoped to feature (if needed)
- [ ] Consumer imports use `@/features/{name}` not deep paths
