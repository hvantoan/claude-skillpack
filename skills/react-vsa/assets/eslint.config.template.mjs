// @ts-check
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import importPlugin from "eslint-plugin-import";
import boundaries from "eslint-plugin-boundaries";

/**
 * ESLint Flat Config for React + VSA (Vertical Slice Architecture)
 *
 * Usage: Copy this file to your project root as `eslint.config.mjs`
 * Requires: npm i -D eslint typescript-eslint eslint-plugin-react-hooks
 *                     eslint-plugin-react-refresh eslint-plugin-import
 *                     eslint-plugin-boundaries
 *
 * Customize the `features` list below to match your project's feature names.
 */

// ── Project Config ─────────────────────────────────────
// List your feature names here. The boundary rules use these to enforce VSA.
const FEATURES = [
  "auth",
  "products",
  "cart",
  "dashboard",
  "settings",
  // Add your feature names here
];

// ── Helper ─────────────────────────────────────────────
const featureNames = FEATURES.join("|");
const featurePattern = `src/features/(${featureNames})`;
const sharedPattern = "src/shared";
const appPattern = "src/app";

// ── Config ─────────────────────────────────────────────
export default tseslint.config(
  // ── Global Ignores ────────────────────────────────────
  {
    ignores: [
      "**/dist/**",
      "**/build/**",
      "**/node_modules/**",
      "**/*.config.*",
      "**/coverage/**",
    ],
  },

  // ── Base: JS + TS ─────────────────────────────────────
  js.configs.recommended,
  ...tseslint.configs.recommended,

  // ── React ─────────────────────────────────────────────
  {
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": ["warn", {
        allowConstantExport: true,
      }],
    },
  },

  // ── Import Ordering ───────────────────────────────────
  {
    plugins: { import: importPlugin },
    settings: {
      "import/resolver": {
        typescript: true,
        node: true,
      },
    },
    rules: {
      "import/order": ["warn", {
        groups: [
          "builtin",   // Node built-ins
          "external",  // npm packages (react, zustand, etc.)
          "internal",  // alias imports (@/features/*, @/shared/*)
          "parent",    // ../  imports
          "sibling",   // ./   imports
          "index",     // ./index imports
          "type",
        ],
        pathGroups: [
          { pattern: "@/features/**", group: "internal", position: "before" },
          { pattern: "@/shared/**", group: "internal", position: "after" },
          { pattern: "@/app/**", group: "internal", position: "after" },
        ],
        "newlines-between": "never",
        alphabetize: { order: "asc", caseInsensitive: true },
      }],
      "import/no-duplicates": "error",
      "import/no-cycle": "warn",
      "import/no-self-import": "error",
      "import/no-useless-path-segments": "warn",
    },
  },

  // ── VSA Boundary Rules ────────────────────────────────
  {
    plugins: { boundaries },
    settings: {
      "boundaries/elements": [
        // Feature slices — each is an independent module
        {
          type: "feature",
          pattern: `${featurePattern}/**/*`,
          capture: ["featureName"],
        },
        // Shared layer — generic, reusable code
        {
          type: "shared",
          pattern: `${sharedPattern}/**/*`,
        },
        // App layer — entry point, can import anything
        {
          type: "app",
          pattern: `${appPattern}/**/*`,
        },
      ],
    },
    rules: {
      // ── Rule 1: No deep imports into features ──────────
      // Features MUST be imported via their public API (index.ts)
      "no-restricted-imports": ["error", {
        patterns: [
          {
            group: [`@/features/(${featureNames})/**`],
            message: "VSA: Import from feature public API only. Use `@/features/{{featureName}}` instead of deep imports.",
          },
          {
            group: [`../features/(${featureNames})/**`],
            message: "VSA: Import from feature public API only. Use `@/features/{{featureName}}` instead of deep imports.",
          },
        ],
      }],

      // ── Rule 2: Shared cannot import features ──────────
      "boundaries/element-types": ["error", {
        default: "disallow",
        rules: [
          // App can import everything
          { from: ["app"], allow: ["feature", "shared", "app"] },
          // Features can import other features (via public API) and shared
          { from: ["feature"], allow: ["feature", "shared"] },
          // Shared can only import shared — never features
          { from: ["shared"], allow: ["shared"] },
        ],
      }],

      // ── Rule 3: No wildcard exports from features ──────
      // Feature index.ts must use explicit named exports
      "no-restricted-syntax": ["error", {
        selector: "ExportAllDeclaration",
        message: "VSA: No wildcard exports (`export *`). Use explicit named exports in feature index.ts.",
      }],
    },
  },

  // ── TypeScript-specific ───────────────────────────────
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
      }],
      "@typescript-eslint/consistent-type-imports": ["warn", {
        prefer: "type-imports",
        fixStyle: "inline-type-imports",
      }],
      "@typescript-eslint/no-empty-object-type": "off",
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },

  // ── Test files — relaxed rules ────────────────────────
  {
    files: [
      "**/*.test.{ts,tsx}",
      "**/*.spec.{ts,tsx}",
      "**/test/**",
      "**/__tests__/**",
      "**/setupTests.ts",
    ],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "no-restricted-imports": "off",
      "boundaries/element-types": "off",
      "react-refresh/only-export-components": "off",
    },
  },

  // ── Feature index.ts — enforce barrel exports ─────────
  {
    files: [`src/features/*/index.ts`, `src/features/*/index.tsx`],
    rules: {
      // Barrel files should only re-export
      "@typescript-eslint/no-unused-vars": "off",
    },
  },

  // ── Storybook stories — relaxed ───────────────────────
  {
    files: ["**/*.stories.{ts,tsx}"],
    rules: {
      "no-restricted-imports": "off",
      "boundaries/element-types": "off",
      "react-refresh/only-export-components": "off",
    },
  }
);
