# Next.js Integration with VSA

## App Router Pattern

Next.js `app/` directory handles routing ONLY. All logic lives in `features/`.

```
src/
├── app/                          # Next.js routing (thin wrappers)
│   ├── layout.tsx                # Root layout → import Providers
│   ├── (auth)/                   # Route group
│   │   ├── login/
│   │   │   └── page.tsx          # → import { LoginForm } from '@/features/auth'
│   │   └── register/
│   │       └── page.tsx          # → import { RegisterForm } from '@/features/auth'
│   ├── (dashboard)/
│   │   ├── page.tsx              # → import { DashboardPage } from '@/features/dashboard'
│   │   └── products/
│   │       └── page.tsx          # → import { ProductGrid } from '@/features/products'
│   └── api/                      # Next.js API routes (if any)
│       └── webhooks/
│           └── route.ts
├── features/                     # VSA core
│   ├── auth/
│   ├── products/
│   ├── dashboard/
│   └── cart/
└── shared/
```

## Route Page Pattern

```typescript
// app/(dashboard)/products/page.tsx
import { ProductGrid } from '@/features/products';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Products',
  description: 'Browse our product catalog',
};

export default function ProductsPage() {
  return <ProductGrid />;
}
```

**Rule:** Page files are <10 lines. Metadata + component import only. No logic.

## Layout Pattern

```typescript
// app/layout.tsx
import { Providers } from './providers';
import { Header } from '@/features/shell/components/header';
import './globals.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Header />
          <main>{children}</main>
        </Providers>
      </body>
    </html>
  );
}
```

## Providers Pattern

```typescript
// app/providers.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 60_000, retry: 1 },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

## Server Components Boundary

### Strategy: Server at Route, Client in Features

```
app/(dashboard)/products/[id]/page.tsx   ← Server Component (data fetching)
  └── import { ProductDetail } from '@/features/products'  ← Client Component
```

```typescript
// app/(dashboard)/products/[id]/page.tsx (Server Component)
import { productApi } from '@/features/products/api/product-api';
import { ProductDetail } from '@/features/products';

export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await productApi.getById(params.id); // direct server-side fetch
  return <ProductDetail initialData={product} />;
}
```

```typescript
// features/products/components/product-detail.tsx
'use client'; // Explicit boundary

export function ProductDetail({ initialData }: { initialData: Product }) {
  const [product, setProduct] = useState(initialData);
  // Client-side interactivity here
}
```

### Rules for 'use client' Boundaries

1. **Route pages** = Server Components by default (Next.js App Router)
2. **Feature components** = Add `'use client'` when they need interactivity
3. **Feature hooks** = Always `'use client'` (hooks require client)
4. **Feature API** = Can be server-side (direct fetch without axios)
5. **shared/lib** = Pure functions = universal (works both sides)

### Data Fetching Strategy

| Data Type | Server Component | Client Component |
|-----------|-----------------|------------------|
| Initial page data | Direct `fetch()` or ORM | Pass as `initialData` prop |
| Interactive data | N/A | TanStack Query |
| Form submissions | Server Actions | TanStack Mutation |
| Real-time updates | N/A | WebSocket / SSE |

## Middleware Pattern (Auth)

```typescript
// middleware.ts (root)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const protectedRoutes = ['/dashboard', '/settings', '/profile'];
const authRoutes = ['/login', '/register'];

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value;
  const isProtected = protectedRoutes.some((r) => request.nextUrl.pathname.startsWith(r));
  const isAuthRoute = authRoutes.some((r) => request.nextUrl.pathname.startsWith(r));

  if (isProtected && !token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

## Route Organization Convention

Map Next.js routes to features:

| Route | Feature |
|-------|---------|
| `/login`, `/register`, `/forgot-password` | `features/auth` |
| `/dashboard` | `features/dashboard` |
| `/products`, `/products/[id]` | `features/products` |
| `/cart`, `/checkout` | `features/cart` |
| `/settings/*` | `features/settings` |
| `/admin/*` | `features/admin` |

**Rule:** 1 route group → 1 feature. Complex routes can span features via composition.
