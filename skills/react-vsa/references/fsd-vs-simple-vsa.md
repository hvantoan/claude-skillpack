# FSD vs Simple VSA — Decision Matrix

## Quick Decision

```
Project size?
├── Small (<10 features, <3 devs) → Simple VSA
├── Medium (10-30 features, 3-8 devs) → Simple VSA + shared/domain/
├── Large (30-50 features, 8+ devs) → FSD
└── Enterprise (50+ features, multiple teams) → Full FSD with strict rules
```

## Simple VSA

```
src/
├── app/
├── features/          # All features live here
│   ├── auth/
│   ├── products/
│   └── cart/
└── shared/            # Truly shared code
```

**Pros:** Low complexity, easy to understand, fast to set up, flexible.
**Cons:** No strict import rules, shared/ can grow unbounded, features can couple.

**Best for:** Startups, MVPs, small teams, projects <30 features.

## Feature-Sliced Design (FSD)

```
src/
├── app/               # App layer: entry point, providers
├── pages/             # Page-level compositions
├── widgets/           # Composite UI blocks (header, sidebar)
├── features/          # User scenarios (like, review, filter)
├── entities/          # Business entities (user, product, order)
├── shared/            # UI kit, lib, api config
└── [deprecated] processes/  # Cross-page flows
```

### FSD Layers (High → Low)

| Layer | Purpose | Can Import From | Example |
|-------|---------|----------------|---------|
| `app/` | Entry point, global providers | All layers below | `App.tsx`, `providers.tsx` |
| `pages/` | Route-level compositions | widgets, features, entities, shared | `DashboardPage.tsx` |
| `widgets/` | Composite UI blocks | features, entities, shared | `Header.tsx`, `Sidebar.tsx` |
| `features/` | User scenarios | entities, shared | `LikeProduct`, `FilterProducts` |
| `entities/` | Business domain | shared | `User`, `Product`, `Order` |
| `shared/` | Generic, reusable | Nothing (lowest layer) | `Button`, `apiClient`, `formatDate` |

**Import Rule:** Each layer can ONLY import from layers BELOW it. Never upward.

### FSD Slice Structure

Each slice within a layer has segments:

```
features/like-product/
├── api/               # API calls for this feature
├── ui/                # Components (NOT "components" — FSD uses "ui")
├── model/             # Business logic, state, selectors
├── lib/               # Helper functions
├── config/            # Feature configuration
└── index.ts           # Public API (MANDATORY)
```

### FSD Public API (Mandatory)

Every slice MUST have `index.ts` exposing only its public API:

```typescript
// features/like-product/index.ts
export { LikeButton } from './ui/like-button';
export { useLikeStatus } from './model/use-like-status';
export type { LikeData } from './model/types';
// NOT exported: internal helpers, API details, model internals
```

## Comparison Table

| Aspect | Simple VSA | FSD |
|--------|-----------|-----|
| Layers | 3 (app, features, shared) | 7 (app → shared) |
| Import rules | Loose (convention) | Strict (enforced) |
| Public API | Recommended | Mandatory per slice |
| Segments | Free naming | Standardized (api, ui, model, lib) |
| Learning curve | 1 hour | 1-2 days |
| Setup time | 5 minutes | 30 minutes |
| Enforces boundaries | By convention | By architecture |
| Best team size | 1-5 | 5+ |
| Refactoring safety | Medium | High |
| Newbie onboarding | Fast | Slower but clearer |

## Migration Path: Simple VSA → FSD

1. **Phase 1:** Start with Simple VSA (`features/` + `shared/`)
2. **Phase 2:** Extract `entities/` when features share domain types
3. **Phase 3:** Add `widgets/` when composite UI blocks emerge
4. **Phase 4:** Add `pages/` layer for route-level compositions
5. **Phase 5:** Enforce import rules (use `scripts/verify-vsa-architecture.py`)

**Don't jump to FSD prematurely.** Simple VSA works well for most projects.

## When NOT to Use VSA at All

- Prototype / proof of concept (<1 week lifetime)
- Single-page app with <3 features
- Learning/tutorial project (classic structure easier to follow)
- Static site with no business logic

**VSA adds value when:** 3+ features, team >1, codebase >2 months old, ongoing maintenance.
