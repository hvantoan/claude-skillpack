# State Management Patterns in VSA

## Decision Tree

```
Need state?
├── Component-local only? → useState / useReducer
├── Shared within feature? → Zustand store in features/{name}/store/
├── Shared across 2-3 features? → Zustand store in features/{primary}/store/ + export hook
├── Shared app-wide (auth, theme)? → React Context in app/providers.tsx
└── Server state? → TanStack Query (no client store needed)
```

## Priority: Local → Feature → Global

### Level 1: Component State (Preferred)

```typescript
// features/products/components/product-filters.tsx
export function ProductFilters({ onFilterChange }: Props) {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  // State lives here, dies here. No global impact.
}
```

### Level 2: Feature Store (Zustand Scoped)

```typescript
// features/cart/store/cart-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CartState {
  items: CartItem[];
  addItem: (product: Product) => void;
  removeItem: (productId: string) => void;
  clearCart: () => void;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (product) => set((s) => ({
        items: [...s.items, { product, quantity: 1 }],
      })),
      removeItem: (id) => set((s) => ({
        items: s.items.filter((i) => i.product.id !== id),
      })),
      clearCart: () => set({ items: [] }),
    }),
    { name: 'cart-storage' }
  )
);
```

### Level 3: Global State (React Context)

```typescript
// app/providers.tsx
import { ThemeProvider } from './theme-provider';
import { QueryClientProvider } from '@tanstack/react-query';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
```

Only use Context for truly global concerns: theme, locale, feature flags. NOT for business data.

## Server State: TanStack Query (Preferred over Client Store)

For API data, use TanStack Query. Don't duplicate server state in Zustand.

```typescript
// features/products/hooks/use-products.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productApi } from '../api/product-api';

export function useProducts(filters?: ProductFilters) {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => productApi.getAll(filters),
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: productApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['products'] }),
  });
}
```

## Cross-Feature Communication

### Pattern 1: Direct Hook Import (via Public API)

```typescript
// features/products/components/product-card.tsx
import { useCart } from '@/features/cart'; // via public API

export function ProductCard({ product }: Props) {
  const { addItem } = useCart();
  return <button onClick={() => addItem(product)}>Add to Cart</button>;
}
```

**When:** Feature A consumes Feature B's public API. Simple, type-safe.

### Pattern 2: Shared State (Zustand)

```typescript
// features/auth/store/auth-store.ts
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: true }),
  clearUser: () => set({ user: null, isAuthenticated: false }),
}));

// features/dashboard/hooks/use-dashboard.ts
import { useAuthStore } from '@/features/auth'; // via public API
```

**When:** Feature needs reactive access to another feature's state.

### Pattern 3: Event-Based (Pub/Sub)

```typescript
// shared/lib/event-bus.ts
type EventMap = Record<string, unknown>;
const listeners = new Map<string, Set<(data: unknown) => void>>();

export const eventBus = {
  on<T>(event: string, callback: (data: T) => void) {
    if (!listeners.has(event)) listeners.set(event, new Set());
    listeners.get(event)!.add(callback as (data: unknown) => void);
    return () => listeners.get(event)!.delete(callback as (data: unknown) => void);
  },
  emit<T>(event: string, data: T) {
    listeners.get(event)?.forEach((cb) => cb(data));
  },
};

// features/cart/hooks/use-cart.ts — emit event
eventBus.emit('cart:updated', { itemCount: items.length });

// features/dashboard/hooks/use-dashboard.ts — listen
useEffect(() => eventBus.on('cart:updated', ({ itemCount }) => {
  setCartCount(itemCount);
}), []);
```

**When:** Loose coupling needed. Feature emits event, doesn't know who listens.

### Pattern 4: URL State

```typescript
// features/products/hooks/use-product-filters.ts
import { useSearchParams } from 'react-router-dom';
// or useSearchParams from 'next/navigation' for Next.js

export function useProductFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const category = searchParams.get('category') ?? 'all';
  const sort = searchParams.get('sort') ?? 'newest';

  const setFilter = (key: string, value: string) => {
    setSearchParams((prev) => { prev.set(key, value); return prev; });
  };

  return { category, sort, setFilter };
}
```

**When:** Filter/pagination state shareable via URL. Bookmarkable, shareable.

## Anti-Patterns

### ❌ Global Store for Everything

```typescript
// ❌ One massive Zustand store for all features
export const useAppStore = create((set) => ({
  user: null, products: [], cart: [], orders: [], settings: {},
  // becomes unmaintainable
}));
```

### ✅ Scoped Stores per Feature

```typescript
// ✅ Each feature manages its own state
// features/auth/store/auth-store.ts
export const useAuthStore = create<AuthState>(...);
// features/cart/store/cart-store.ts
export const useCartStore = create<CartState>(...);
// features/products — no store needed, uses TanStack Query
```

### ❌ Props Drilling Through Layers

```typescript
// ❌ Passing cart through 5 levels of components
<App cart={cart}><Layout cart={cart}><Page cart={cart}><ProductList cart={cart}>...
```

### ✅ Hook at Point of Use

```typescript
// ✅ Each component gets what it needs directly
function ProductCard({ product }: Props) {
  const { addItem } = useCart(); // hook at point of use
}
```
