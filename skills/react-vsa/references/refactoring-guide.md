# Refactoring Guide — Layered to VSA

## Pre-Flight Check

Before migrating, assess current state:

1. **Identify features** from routes/pages → each route ≈ 1 feature
2. **Map dependencies** → which components import which hooks/services
3. **Identify shared code** → what's used across 3+ features
4. **Estimate effort** → features count × 30min per feature for migration

## Migration Strategy

### Phase 1: Setup Structure (30 min)

```bash
# Create VSA directories
mkdir -p src/features src/shared/{ui,hooks,lib,api,types} src/app

# Create path aliases in tsconfig.json
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@/features/*": ["./src/features/*"],
      "@/shared/*": ["./src/shared/*"]
    }
  }
}
```

### Phase 2: Extract Shared Code (1-2 hours)

Move generic, feature-agnostic code to `shared/`:

```
BEFORE (layered):                    AFTER (VSA):
src/                                 src/
├── components/                      ├── shared/
│   ├── Button.tsx                   │   ├── ui/
│   ├── Card.tsx                     │   │   ├── button.tsx
│   ├── Modal.tsx                    │   │   ├── card.tsx
│   ├── UserMenu.tsx  ← feature!    │   │   └── modal.tsx
│   └── LoginForm.tsx  ← feature!   │   ├── hooks/
├── hooks/                           │   │   ├── use-debounce.ts
│   ├── useDebounce.ts               │   │   └── use-media-query.ts
│   ├── useAuth.ts     ← feature!   │   ├── lib/
│   └── useProducts.ts ← feature!   │   │   ├── format-currency.ts
├── services/                        │   │   └── cn.ts
│   ├── api.ts                       │   └── api/
│   ├── authService.ts ← feature!   │       └── client.ts
│   └── productService.ts ← feature!│
├── utils/                           ├── features/    ← Phase 3
│   ├── formatDate.ts                │
│   └── formatCurrency.ts            │
└── types/                           │
    ├── User.ts        ← feature!   │
    └── Product.ts     ← feature!   │
```

### Phase 3: Migrate Features One-by-One (30 min each)

For each feature (auth, products, cart, etc.):

1. **Create feature directory:**
   ```bash
   mkdir -p src/features/auth/{components,hooks,api,types,store}
   ```

2. **Move feature-specific files:**
   ```bash
   # Components
   mv src/components/LoginForm.tsx src/features/auth/components/login-form.tsx
   mv src/components/UserMenu.tsx src/features/auth/components/user-menu.tsx

   # Hooks
   mv src/hooks/useAuth.ts src/features/auth/hooks/use-auth.ts

   # API
   mv src/services/authService.ts src/features/auth/api/auth-api.ts

   # Types
   mv src/types/User.ts src/features/auth/types/auth.types.ts
   ```

3. **Create public API:**
   ```typescript
   // src/features/auth/index.ts
   export { LoginForm } from './components/login-form';
   export { UserMenu } from './components/user-menu';
   export { useAuth } from './hooks/use-auth';
   export type { User, AuthCredentials } from './types/auth.types';
   ```

4. **Update all imports** that reference this feature:
   ```typescript
   // BEFORE
   import { LoginForm } from '../../components/LoginForm';
   import { useAuth } from '../../hooks/useAuth';

   // AFTER
   import { LoginForm, useAuth } from '@/features/auth';
   ```

5. **Verify:** Run tests, check TypeScript compilation

### Phase 4: Verify & Clean Up (1 hour)

1. Run `scripts/verify-vsa-architecture.py src/`
2. Fix any cross-feature deep imports
3. Remove empty directories from old structure
4. Update any remaining relative imports to path aliases
5. Run full test suite

## Common Migration Patterns

### Pattern: Service → Feature API

```typescript
// BEFORE: src/services/authService.ts
export const authService = {
  login: (credentials) => axios.post('/auth/login', credentials),
  logout: () => axios.post('/auth/logout'),
  me: () => axios.get('/auth/me'),
};

// AFTER: src/features/auth/api/auth-api.ts
import { apiClient } from '@/shared/api/client';
import type { AuthCredentials, User, AuthResponse } from '../types/auth.types';

export const authApi = {
  login: (credentials: AuthCredentials) =>
    apiClient.post<AuthResponse>('/auth/login', credentials),
  logout: () => apiClient.post('/auth/logout'),
  me: () => apiClient.get<User>('/auth/me'),
};
```

### Pattern: God Component → Feature Components

```typescript
// BEFORE: src/components/ProductPage.tsx (500 lines)
// Contains: product list, filters, detail, cart button, reviews

// AFTER: Split into features
// features/products/components/product-grid.tsx
// features/products/components/product-filters.tsx
// features/products/components/product-detail.tsx
// features/cart/components/add-to-cart-button.tsx
// features/reviews/components/product-reviews.tsx
```

### Pattern: Redux Root → Zustand Feature Stores

```typescript
// BEFORE: src/store/index.ts (single Redux store with all slices)
// AFTER: Each feature manages its own Zustand store

// features/auth/store/auth-store.ts
export const useAuthStore = create<AuthState>(...);

// features/cart/store/cart-store.ts
export const useCartStore = create<CartState>(...);

// No global store needed — each feature owns its state
```

## Handling Large Refactors

For projects >20 features, migrate incrementally:

1. **Week 1:** Setup structure + shared code
2. **Week 2-3:** Migrate 2-3 features per sprint
3. **Week 4:** Verify all features migrated, clean up
4. **Ongoing:** New features follow VSA convention from day 1

**Rule:** Old features work until migrated. Don't break existing code during migration.

## Verification Script

Run after migration:

```bash
python3 scripts/verify-vsa-architecture.py src/
```

Checks:
- No direct feature-to-feature deep imports (bypassing index.ts)
- No feature code in shared/ (should be generic)
- All features have index.ts barrel exports
- No circular dependencies between features
- shared/ files have no feature-specific imports
