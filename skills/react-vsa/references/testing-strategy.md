# Testing Strategy for VSA React Projects

## Test Pyramid per Feature

```
        ┌─────────┐
        │   E2E   │  ← Cross-feature flows (Cypress/Playwright)
        │  (few)  │     in e2e/ directory
        ├─────────┤
        │Integr.  │  ← Feature integration (component + store + API mock)
        │ (some)  │     colocated in features/{name}/
        ├─────────┤
        │  Unit   │  ← Individual hooks, components, utils
        │ (many)  │     colocated with source files
        └─────────┘
```

## Colocation Rule

Test files live NEXT TO source files:

```
features/auth/
├── components/
│   ├── login-form.tsx
│   └── login-form.test.tsx        ← unit test
├── hooks/
│   ├── use-auth.ts
│   └── use-auth.test.ts           ← unit test
├── api/
│   └── auth-api.ts
│   └── auth-api.test.ts           ← unit test (mock axios)
├── store/
│   └── auth-store.test.ts         ← unit test (no React)
└── integration/
    └── auth-flow.test.tsx          ← integration (component + store + MSW)
```

## Unit Testing Patterns

### Component Testing

```typescript
// features/auth/components/login-form.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './login-form';

describe('LoginForm', () => {
  it('calls onSubmit with credentials', async () => {
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    await userEvent.type(screen.getByLabelText('Email'), 'test@example.com');
    await userEvent.type(screen.getByLabelText('Password'), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });
});
```

### Hook Testing

```typescript
// features/auth/hooks/use-auth.test.ts
import { renderHook, act } from '@testing-library/react';
import { useAuth } from './use-auth';

// Mock the store
vi.mock('../store/auth-store', () => ({
  useAuthStore: vi.fn(() => ({
    user: null,
    isAuthenticated: false,
    setUser: vi.fn(),
    clearUser: vi.fn(),
  })),
}));

describe('useAuth', () => {
  it('provides auth state and actions', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(typeof result.current.login).toBe('function');
    expect(typeof result.current.logout).toBe('function');
  });
});
```

### Store Testing (No React Needed)

```typescript
// features/cart/store/cart-store.test.ts
import { useCartStore } from './cart-store';
import type { Product } from '../types/cart.types';

const mockProduct: Product = { id: '1', name: 'Test', price: 10 };

describe('cart-store', () => {
  beforeEach(() => useCartStore.setState({ items: [] }));

  it('adds item to cart', () => {
    const { addItem } = useCartStore.getState();
    addItem(mockProduct);
    expect(useCartStore.getState().items).toHaveLength(1);
  });

  it('removes item from cart', () => {
    useCartStore.setState({ items: [{ product: mockProduct, quantity: 1 }] });
    const { removeItem } = useCartStore.getState();
    removeItem('1');
    expect(useCartStore.getState().items).toHaveLength(0);
  });

  it('clears all items', () => {
    useCartStore.setState({ items: [{ product: mockProduct, quantity: 1 }] });
    const { clearCart } = useCartStore.getState();
    clearCart();
    expect(useCartStore.getState().items).toHaveLength(0);
  });
});
```

## Integration Testing with MSW

```typescript
// features/products/integration/product-flow.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { ProductGrid } from '../components/product-grid';

const server = setupServer(
  http.get('/api/products', () => HttpResponse.json([
    { id: '1', name: 'Widget A', price: 29.99 },
    { id: '2', name: 'Widget B', price: 49.99 },
  ]))
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe('ProductGrid integration', () => {
  it('loads and displays products', async () => {
    renderWithProviders(<ProductGrid />);
    await waitFor(() => {
      expect(screen.getByText('Widget A')).toBeInTheDocument();
      expect(screen.getByText('Widget B')).toBeInTheDocument();
    });
  });
});
```

## E2E Testing (Cross-Feature)

```
e2e/
├── auth.spec.ts          # Login → Dashboard flow
├── shopping.spec.ts      # Browse → Add to cart → Checkout
└── smoke.spec.ts         # Critical paths
```

```typescript
// e2e/shopping.spec.ts (Playwright example)
import { test, expect } from '@playwright/test';

test('user can browse products and add to cart', async ({ page }) => {
  await page.goto('/products');
  await expect(page.getByText('Widget A')).toBeVisible();

  await page.getByRole('button', { name: /add to cart/i }).first().click();
  await expect(page.getByTestId('cart-badge')).toHaveText('1');

  await page.getByTestId('cart-button').click();
  await expect(page.getByText('Widget A')).toBeVisible();
});
```

## Outside-In TDD Workflow (from outsidein.dev)

1. **Write E2E test** for feature flow → watch it fail
2. **Step down to unit test** for component logic
3. **Red-green-refactor** until unit tests pass
4. **Step back up** to E2E → should pass now
5. **Refactor** with confidence (tests protect)

## MSW Setup for Feature Testing

```typescript
// shared/test/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);

// shared/test/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/health', () => HttpResponse.json({ status: 'ok' })),
  // Add default handlers; override per test with server.use()
];
```

## Testing Checklist per Feature

- [ ] Unit tests for each component (rendering + interactions)
- [ ] Unit tests for each hook (state + side effects)
- [ ] Unit tests for store (actions + state transitions)
- [ ] Unit tests for API functions (mock axios)
- [ ] Integration test for main feature flow (component + store + MSW)
- [ ] E2E test for cross-feature flow (if feature interacts with others)
