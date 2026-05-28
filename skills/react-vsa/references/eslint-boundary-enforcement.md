# ESLint Boundary Enforcement for VSA

## Quick Setup

Run the harness to generate config interactively:

```bash
python scripts/generate-eslint-config.py
```

Or with flags:

```bash
python scripts/generate-eslint-config.py --arch=vsa --enforcement=boundaries
python scripts/generate-eslint-config.py --arch=fsd --enforcement=boundaries --formatting
python scripts/generate-eslint-config.py --arch=vsa --enforcement=minimal --features=auth,products,cart
```

Install dependencies:

```bash
# For boundaries plugin mode
npm i -D eslint typescript-eslint eslint-plugin-react-hooks \
  eslint-plugin-react-refresh eslint-plugin-import \
  eslint-plugin-boundaries eslint-import-resolver-typescript

# For minimal mode (no boundaries plugin)
npm i -D eslint typescript-eslint eslint-plugin-react-hooks \
  eslint-plugin-react-refresh eslint-plugin-import \
  eslint-import-resolver-typescript
```

## Enforcement Modes

| Mode | Plugin | What It Does |
|------|--------|-------------|
| `boundaries` | `eslint-plugin-boundaries` | Full enforcement: dependency direction, entry-point, no-private |
| `minimal` | Built-in only | `no-restricted-imports` + `no-restricted-syntax` — no plugin needed |
| `none` | None | Base ESLint config only — no boundary rules |

## Boundary Rules (Boundaries Plugin)

### Rule 1: `boundaries/dependencies` — Import Direction

Controls who can import whom based on element types.

```typescript
// ❌ ERROR — shared importing from features (VSA)
// shared/lib/format-user.ts
import { User } from '@/features/auth/types/auth.types';

// ✅ OK — shared defines types, features re-export
// shared/types/user.types.ts
export interface User { id: string; name: string; email: string; }
```

**VSA allowed directions:**

| From | Allowed |
|------|---------|
| `app` | `feature`, `shared` |
| `feature` | `feature`, `shared` |
| `shared` | `shared` only |

**FSD allowed directions (strict downward):**

| From | Allowed |
|------|---------|
| `app` | `page`, `shared` |
| `page` | `widget`, `feature`, `entity`, `shared` |
| `widget` | `feature`, `entity`, `shared` |
| `feature` | `entity`, `shared` |
| `entity` | `shared` |
| `shared` | `shared` only |

### Rule 2: `boundaries/entry-point` — Public API Only

Forces consumers to use `index.ts` barrel exports, not deep imports.

```typescript
// ❌ ERROR — deep import bypasses public API
import { useAuth } from '@/features/auth/hooks/use-auth';

// ✅ OK — use feature public API
import { useAuth } from '@/features/auth';
```

**Why:** Makes refactoring safe — move files inside a feature without breaking external imports.

### Rule 3: `boundaries/no-private` — Internal Encapsulation

Blocks access to non-public files within a feature. Only `index.ts` is the public entry point.

```typescript
// ❌ ERROR — accessing internal file
import { helperFn } from '@/features/auth/utils/helper';

// ✅ OK — if helperFn is exported from index.ts
import { helperFn } from '@/features/auth';
```

`allowUncles: true` — allows imports from sibling folders within the same feature (e.g., `components/` importing from `hooks/` within `features/auth/`).

### Rule 4: Capture Groups (Dynamic Feature Matching)

Elements use `capture` to match feature names dynamically — no hardcoded feature lists:

```javascript
{
  type: "feature",
  pattern: "src/features/*",
  mode: "folder",
  capture: ["featureName"],  // captures "auth", "products", etc.
}
```

Error messages reference captured names:

```
VSA: Use public API — import from '@/features/auth' instead of deep import.
```

## Minimal Mode (No Boundaries Plugin)

Uses built-in ESLint rules only. Good for teams that don't want `eslint-plugin-boundaries`.

### What it enforces:

| Rule | Plugin | What It Catches |
|------|--------|----------------|
| Deep feature imports | `no-restricted-imports` | `@/features/auth/hooks/use-auth` |
| Relative feature imports | `no-restricted-imports` | `../features/auth/types/**` |
| Wildcard exports | `no-restricted-syntax` | `export * from './hooks/use-auth'` |

### What it misses (vs boundaries plugin):

- No dependency direction enforcement (shared → features not blocked)
- No entry-point enforcement (any file in feature is accessible)
- No capture groups (static patterns, not dynamic)

Provide feature names via `--features` for per-feature error messages:

```bash
python scripts/generate-eslint-config.py --arch=vsa --enforcement=minimal --features=auth,products,cart
```

## Element Types

### Simple VSA (3 elements)

| Type | Pattern | Mode | Description |
|------|---------|------|-------------|
| `feature` | `src/features/*` | folder | Each feature is a slice |
| `shared` | `src/shared` | file | Shared utilities |
| `app` | `src/app` | file | Entry point |

### FSD (6 elements)

| Type | Pattern | Mode | Description |
|------|---------|------|-------------|
| `app` | `src/app` | folder | App layer |
| `page` | `src/pages/*` | folder | Page compositions |
| `widget` | `src/widgets/*` | folder | Composite UI blocks |
| `feature` | `src/features/*` | folder | User scenarios |
| `entity` | `src/entities/*` | folder | Business entities |
| `shared` | `src/shared` | folder | UI kit, utilities |

## Monorepo

For monorepo projects (detected by `packages/` or `apps/` directories):

```bash
# Generate in specific package
python scripts/generate-eslint-config.py --output=packages/web

# Handle existing root .editorconfig
python scripts/generate-eslint-config.py --existing-config=append
```

Options for `--existing-config`:
- `skip` — Don't overwrite existing configs (safest)
- `append` — Add new sections to existing files (.editorconfig only)
- `overwrite` — Replace existing files

## Import Ordering

Generated config includes import ordering via `eslint-plugin-import`:

```typescript
// 1. Built-in (fs, path)
// 2. External (react, zustand, axios)
// 3. Internal — features first, then shared
import { useAuth } from '@/features/auth';
import { Button } from '@/shared/ui/button';
// 4. Parent (../)
// 5. Sibling (./)
// 6. Index (./index)
```

## Scripts Integration

Add to `package.json`:

```json
{
  "scripts": {
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix"
  }
}
```

## Pre-commit Hook (Optional)

```bash
# .husky/pre-commit
npx eslint --max-warnings=0 src/
```

## Excluding Generated Code

Add to `eslint.config.mjs` overrides:

```javascript
{
  files: ["**/__generated__/**", "**/*.generated.ts"],
  rules: {
    "boundaries/dependencies": "off",
    "boundaries/entry-point": "off",
    "boundaries/no-private": "off",
  },
}
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Cannot find module 'eslint-plugin-boundaries'` | `npm i -D eslint-plugin-boundaries` |
| False positives on test files | Test files have relaxed rules in base config |
| Import resolver errors | `npm i -D eslint-import-resolver-typescript` |
| Feature not recognized | Check `src/features/` folder name matches pattern |
| `export *` needed for barrel file | Use explicit named exports instead |
| Config too strict for prototype | Use `--enforcement=minimal` or `--enforcement=none` |
| Monorepo: wrong config location | Use `--output=packages/web` to target specific package |

## Migration from Old Template

If upgrading from the previous `eslint.config.template.mjs`:

1. Delete old `eslint.config.mjs` (or rename as backup)
2. Run `python scripts/generate-eslint-config.py` with your preferred mode
3. The old `boundaries/element-types` rule has been replaced by `boundaries/dependencies` (newer API)
4. Feature names are now auto-detected via capture groups (no `FEATURES` array to maintain)
