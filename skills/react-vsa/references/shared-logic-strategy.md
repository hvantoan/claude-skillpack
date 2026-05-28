# Shared Logic Strategy — 3-Tier Model & Anti-Patterns

## Three-Tier Sharing Model

| Tier | What | Share? | Location | Example |
|------|------|--------|----------|---------|
| **1 (Infrastructure)** | Base API client, UI kit, formatters, test utils | Freely | `shared/` | `Button`, `apiClient`, `formatDate` |
| **2 (Domain)** | Entity types, domain hooks, validation schemas | With care | `shared/` or feature | `User` type, `useUser` hook |
| **3 (Feature-specific)** | Components, hooks, API calls, types per feature | Never | `features/{name}/` | `LoginForm`, `useAuth`, `authApi` |

## Rule of Three

Don't extract to `shared/` until the **same code appears in 3+ features**:

1. **1 copy** — write it in the feature, no abstraction needed
2. **2 copies** — tolerable, they may diverge based on feature needs
3. **3 copies** — extract to Tier 1 (infrastructure) or Tier 2 (domain)

**Why:** Two identical snippets may evolve differently. Premature extraction creates coupling between features that should change independently.

## What Belongs in shared/

### shared/ui/ — Generic UI Components

```typescript
// shared/ui/button.tsx — no business logic, fully reusable
export function Button({ variant, size, children, ...props }: ButtonProps) {
  return <button className={cn(styles[variant], styles[size])} {...props}>{children}</button>;
}
```

Criteria: No business logic, no feature-specific types, used across 2+ features.

### shared/lib/ — Pure Utilities

```typescript
// shared/lib/format-currency.ts — no React, no state, pure function
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
}
```

Criteria: Pure functions, no side effects, no React dependencies, no feature knowledge.

### shared/api/ — Base Client Configuration

```typescript
// shared/api/client.ts — axios instance, interceptors, base config
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10_000,
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken(); // from secure storage
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

Criteria: HTTP config, interceptors, error transformers. No feature-specific endpoints.

### shared/types/ — Cross-Feature Types

```typescript
// shared/types/api.types.ts
export interface ApiResponse<T> { data: T; meta?: { total: number; page: number } }
export interface ApiError { code: string; message: string; details?: Record<string, string[]> }
```

Criteria: Types used by 2+ features. Not feature-specific DTOs.

### shared/hooks/ — Generic Hooks

```typescript
// shared/hooks/use-debounce.ts — no business logic
export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => { const timer = setTimeout(() => setDebounced(value), delay); return () => clearTimeout(timer); }, [value, delay]);
  return debounced;
}
```

Criteria: No feature-specific logic, no API calls, no business state.

## What NOT to Put in shared/

| Code | Where It Belongs | Why |
|------|-----------------|-----|
| `LoginForm` component | `features/auth/components/` | Feature-specific UI |
| `useProducts` hook | `features/products/hooks/` | Tied to product API |
| `Product` type | `features/products/types/` | Feature-specific domain |
| `authApi.login()` | `features/auth/api/` | Feature-specific endpoint |
| `UserMenu` component | `features/auth/components/` | Requires auth context |
| Business validation | Feature slice | Business logic, not utility |

## Junk Drawer Anti-Pattern

### ❌ shared/ Becomes Junk Drawer

```
shared/
├── utils.ts              ← 500 lines, what's in here?
├── helpers/              ← vague name
│   ├── general.ts        ← "general" = junk
│   └── stuff.ts          ← unnamed purpose
├── components/           ← no categorization
│   ├── Header.tsx        ← app-specific, not shared
│   └── Footer.tsx        ← app-specific, not shared
└── constants.ts          ← 300 lines of unrelated constants
```

### ✅ Organized shared/

```
shared/
├── ui/                   ← Tier 1: Generic components
│   ├── button.tsx
│   ├── card.tsx
│   ├── modal.tsx
│   ├── input.tsx
│   └── skeleton.tsx
├── hooks/                ← Tier 1: Generic hooks
│   ├── use-debounce.ts
│   ├── use-media-query.ts
│   └── use-local-storage.ts
├── lib/                  ← Tier 1: Pure utilities
│   ├── format-currency.ts
│   ├── format-date.ts
│   ├── cn.ts             ← classname merger
│   └── validate.ts       ← generic validation (zod schemas)
├── api/                  ← Tier 1: Base client
│   ├── client.ts         ← axios instance
│   └── types.ts          ← ApiResponse, ApiError
└── types/                ← Tier 2: Cross-feature types
    ├── user.types.ts     ← User type used by 3+ features
    └── pagination.types.ts
```

## Extraction Checklist

Before moving code to `shared/`:

- [ ] Used by 2+ features? (If not, keep in feature)
- [ ] No feature-specific business logic?
- [ ] No feature-specific types in signature?
- [ ] Can name it precisely? (If vague → not ready for shared)
- [ ] Abstraction is stable? (API unlikely to change)
- [ ] Extraction reduces coupling, not increases it?

## Push Logic Down — Avoid Anemic Feature Slices

### ❌ Anemic — Logic in Parent/Shared

```typescript
// shared/hooks/use-data-fetch.ts — god hook, too generic
export function useDataFetch(url: string) {
  // handles everything: auth, retry, caching, error
  // becomes unmaintainable as features grow
}
```

### ✅ Rich — Logic in Feature

```typescript
// features/products/hooks/use-products.ts
export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => productApi.getAll(filters),
    staleTime: 5 * 60 * 1000,
    select: (data) => filterByStock(data, filters.inStock),
  });
}
```

Benefit: feature-specific caching, transformation, error handling. No shared coupling.
