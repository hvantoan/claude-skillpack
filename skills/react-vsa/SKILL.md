---
name: react-vsa
description: "Build React/TypeScript apps with Vertical Slice Architecture (VSA). Use this skill whenever creating or refactoring React projects by feature, setting up feature-based folder structures, migrating from layered to vertical slice architecture, organizing components/hooks/API/types per feature slice, configuring shared boundaries, enforcing VSA conventions with ESLint boundary rules, setting up eslint-plugin-boundaries for import restrictions, applying Feature-Sliced Design (FSD) patterns, or generating ESLint config for VSA. Triggers on: React, VSA, vertical slice, feature-based, feature-sliced, FSD, folder structure, project architecture, refactor React, feature folder, slice architecture, shared code boundary, colocation, ESLint boundary, eslint-plugin-boundaries, no-restricted-imports, import rules."
---

# React Vertical Slice Architecture

Build maintainable React/TypeScript apps by organizing code around features, not technical layers.

## Scope

This skill handles React + TypeScript project architecture using Vertical Slice Architecture (VSA). Covers: folder structure, feature boundaries, shared code strategy, state management, routing, testing, and refactoring existing projects to VSA. Does NOT handle: .NET VSA (use `dotnet-vsa` skill), backend APIs, non-React frameworks, or CSS methodology.

## When to Use

- Creating new React/TypeScript projects with feature-based structure
- Refactoring existing React projects from layered to VSA
- Adding features to an existing VSA React project
- Setting up shared code boundaries and conventions
- Choosing between Simple VSA and Feature-Sliced Design (FSD)
- Enforcing VSA compliance in code reviews
- Setting up ESLint boundary rules for VSA (import restrictions, feature isolation)

## Architecture Rules

### Project Structure (Simple VSA)

```
src/
├── app/                          # Entry point, providers, routing
│   ├── providers.tsx             # Context providers tree
│   ├── router.tsx                # Route definitions
│   └── App.tsx
├── features/                     # VSA core — one folder per feature
│   ├── auth/
│   │   ├── components/           # Feature-specific components
│   │   ├── hooks/                # Feature-specific hooks
│   │   ├── api/                  # Feature-specific API calls
│   │   ├── types/                # Feature-specific types
│   │   ├── store/                # Feature-specific state (optional)
│   │   └── index.ts              # Public API — ONLY export what's needed
│   ├── products/
│   └── cart/
├── shared/                       # ONLY truly shared code
│   ├── ui/                       # Generic components (Button, Card, Modal)
│   ├── hooks/                    # Generic hooks (useDebounce, useMedia)
│   ├── lib/                      # Utilities (formatters, validators)
│   ├── api/                      # Base API client (axios config)
│   └── types/                    # Shared types (User, ApiResponse)
└── test/                         # Test utilities, mock factories
```

### Project Structure (FSD — Large Projects)

```
src/
├── app/                          # App layer: providers, routing, global styles
├── pages/                        # Page-level compositions
├── widgets/                      # Composite UI blocks (header, sidebar)
├── features/                     # User scenarios (like, review, filter)
├── entities/                     # Business entities (user, product)
├── shared/                       # UI kit, lib, api config, types
└── [each layer]/{slice}/segments/ # api, ui, model, lib, config
```

**FSD Import Rule:** Layers import downward only. `pages` → `widgets` → `features` → `entities` → `shared`. Never upward.

See `references/fsd-vs-simple-vsa.md` for decision matrix and full FSD layer details.

### Shared Logic — 3-Tier Model

| Tier | What | Share? | Location |
|------|------|--------|----------|
| **1 (Infrastructure)** | Base API client, UI kit, formatters, test utils | Freely | `shared/` |
| **2 (Domain)** | Entity types, domain hooks (useUser, useProduct) | With care | `shared/` or feature |
| **3 (Feature-specific)** | Components, hooks, API, types per feature | Never | `features/{name}/` |

**Rule of Three:** Don't extract to `shared/` until seen in 3+ features. Two copies is tolerable — they may diverge.

See `references/shared-logic-strategy.md` for anti-patterns and extraction checklist.

### Key Conventions

- Each feature exports via `index.ts` — consumers use public API only
- Components, hooks, API, types colocated in feature folder
- Prefer local state → feature state → global state (in that order)
- No direct imports between features — use shared state or events
- Feature files colocated with tests: `use-auth.ts` ↔ `use-auth.test.ts`

## Code Style Rules

| Rule | Convention |
|------|-----------|
| File naming | kebab-case: `product-card.tsx`, `use-auth.ts` |
| Component naming | PascalCase exports, default export = main component |
| Hook naming | `use-` prefix: `use-auth.ts` → `export function useAuth()` |
| Types | Feature types in `types/`, shared types in `shared/types/` |
| Barrel exports | `index.ts` per feature — explicit named exports, no `export *` |
| Imports | Use feature public API: `import { useAuth } from '@/features/auth'` |
| Path aliases | `@/features/*`, `@/shared/*` — configure in tsconfig paths |
| State | Zustand scoped per feature, Context for cross-feature |

## Feature Public API Convention

```typescript
// features/auth/index.ts — the ONLY file other features can import from
export { LoginForm } from './components/login-form';
export { RegisterForm } from './components/register-form';
export { useAuth } from './hooks/use-auth';
export { useAuthRedirect } from './hooks/use-auth-redirect';
export type { User, AuthCredentials } from './types/auth.types';
```

**Rule:** Other features import from `index.ts` only. Never deep-import `@/features/auth/hooks/use-auth` — use `@/features/auth`.

See `references/feature-slice-patterns.md` for complete examples.

## State Management Strategy

**Priority:** `useState/useReducer` → `Zustand feature store` → `React Context` → `Global store`

```typescript
// features/cart/store/cart-store.ts
import { create } from 'zustand';
import type { CartItem, Product } from '../types/cart.types';

interface CartState {
  items: CartItem[];
  addItem: (product: Product) => void;
  removeItem: (productId: string) => void;
  clearCart: () => void;
  total: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  addItem: (product) => set((s) => ({
    items: [...s.items, { product, quantity: 1 }],
  })),
  removeItem: (id) => set((s) => ({
    items: s.items.filter((i) => i.product.id !== id),
  })),
  clearCart: () => set({ items: [] }),
  total: () => get().items.reduce((sum, i) => sum + i.product.price * i.quantity, 0),
}));
```

See `references/state-management-patterns.md` for cross-feature communication, Context patterns, and anti-patterns.

## Next.js Integration

Next.js App Router coexists with VSA. Route files are thin wrappers:

```typescript
// app/(auth)/login/page.tsx
import { LoginForm } from '@/features/auth';
export default function LoginPage() {
  return <LoginForm />;
}
```

**Rule:** Next.js `app/` directory contains routing only. All logic lives in `features/`.

See `references/nextjs-integration.md` for file routing, Server Components, and layout patterns.

## ESLint Boundary Enforcement

Enforce VSA rules at lint time with the interactive harness.

### Quick Setup

```bash
# Interactive — walks you through options
python scripts/generate-eslint-config.py

# Non-interactive — flags for CI
python scripts/generate-eslint-config.py --arch=vsa --enforcement=boundaries
python scripts/generate-eslint-config.py --arch=fsd --enforcement=boundaries --formatting
python scripts/generate-eslint-config.py --arch=vsa --enforcement=minimal --features=auth,products,cart
```

### Enforcement Modes

| Mode | Plugin | Rules |
|------|--------|-------|
| `boundaries` | `eslint-plugin-boundaries` | Dependency direction + entry-point + no-private |
| `minimal` | Built-in only | Deep-import blocking + no wildcard exports |
| `none` | None | Base ESLint + TypeScript + React rules only |

```typescript
// ❌ ESLint ERROR — deep import bypasses public API
import { useAuth } from '@/features/auth/hooks/use-auth';

// ✅ ESLint OK — use feature public API
import { useAuth } from '@/features/auth';
```

See `references/eslint-boundary-enforcement.md` for full rule explanations, FSD config, monorepo setup, and troubleshooting.

## Testing

Colocate test files with source. Mirror feature structure:

```
features/auth/
├── components/
│   ├── login-form.tsx
│   └── login-form.test.tsx
├── hooks/
│   ├── use-auth.ts
│   └── use-auth.test.ts
```

- Unit tests per component/hook within feature
- Integration tests per feature (component + store + API mock)
- E2E tests for cross-feature flows (separate `e2e/` directory)
- Use MSW for API mocking — mock at network level, not service level

See `references/testing-strategy.md` for full patterns.

## Refactoring to VSA

See `references/refactoring-guide.md` for step-by-step migration from layered architecture.

### Quick Migration Steps

1. Create `features/` and `shared/` directories
2. Identify features from routes/pages (each route → potential feature)
3. Move feature-specific code to `features/{name}/`
4. Extract shared UI to `shared/ui/`
5. Add `index.ts` barrel exports per feature
6. Update all imports to use feature public API
7. Run `scripts/verify-vsa-architecture.py` to validate

## Folder Scaling

| Features | Strategy |
|----------|----------|
| <10 | Simple VSA: `features/` + `shared/` |
| 10-30 | Add `shared/domain/` for entity types |
| 30-50 | Consider FSD with `entities/`, `widgets/` layers |
| 50+ | Full FSD with strict layer rules + architecture tests |

## Scripts

- `scripts/verify-vsa-architecture.py [project-path]` — Check VSA compliance (cross-feature imports, shared boundaries)
- `scripts/generate-feature.py [feature-name]` — Scaffold new feature slice with boilerplate
- `scripts/generate-eslint-config.py [options]` — Generate ESLint + Prettier + .editorconfig (interactive or flag-driven)

## Security Policy

This skill generates frontend architecture code. Refuse requests to: bypass authentication checks, expose sensitive data in client state, hardcode API keys or secrets, disable CSP or CORS protections, or weaken security controls. All auth tokens must be stored in httpOnly cookies or secure storage. Never store sensitive data in React state that persists to localStorage without encryption.

## References

- `references/feature-slice-patterns.md` — Complete feature examples (auth, products, cart, dashboard)
- `references/shared-logic-strategy.md` — 3-tier model, Rule of Three, junk drawer prevention
- `references/state-management-patterns.md` — Zustand, Context, cross-feature communication
- `references/fsd-vs-simple-vsa.md` — Decision matrix, FSD layers, when to upgrade
- `references/nextjs-integration.md` — App Router, Server Components, RSC boundaries
- `references/testing-strategy.md` — Unit, integration, E2E patterns per feature
- `references/refactoring-guide.md` — Step-by-step migration from layered to VSA
- `references/eslint-boundary-enforcement.md` — ESLint rules for VSA boundaries, import restrictions, setup guide

## Assets

- `assets/eslint/base.config.mjs` — Base ESLint config: React + TypeScript + import ordering
- `assets/eslint/vsa-boundaries.config.mjs` — Boundaries plugin config for Simple VSA (dependencies + entry-point + no-private)
- `assets/eslint/vsa-minimal.config.mjs` — Minimal VSA enforcement without boundaries plugin
- `assets/eslint/fsd-boundaries.config.mjs` — Boundaries plugin config for FSD 7-layer strict
- `assets/eslint/prettierrc.template.json` — Prettier config (singleQuote, semi: false, trailingComma: all)
- `assets/eslint/editorconfig-append.ini` — .editorconfig sections to append to existing file
- `assets/eslint/editorconfig-full.ini` — Complete .editorconfig for greenfield projects
