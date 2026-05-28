// Minimal VSA enforcement without eslint-plugin-boundaries
// Uses built-in no-restricted-imports + no-restricted-syntax only
//
// FEATURE_NAMES placeholder is replaced by the harness with actual feature names.
// Example after replacement:
//   { group: ["@/features/auth/**"], message: "..." },
//   { group: ["@/features/products/**"], message: "..." },

export const minimalBoundaryConfig = {
  files: ["**/*.{ts,tsx}"],
  rules: {
    // Block deep feature imports — force public API usage
    "no-restricted-imports": [
      "error",
      {
        patterns: [
          // FEATURE_NAMES_START — harness replaces this block
          // Example generated pattern:
          // { group: ["@/features/auth/**"], message: "VSA: Use '@/features/auth' (public API only)." },
          // FEATURE_NAMES_END
          { group: ["@/features/*/**"], message: "VSA: Use feature public API — import from '@/features/{name}' not deep paths." },
          { group: ["../features/*/**"], message: "VSA: Use feature public API — use absolute '@/features/{name}' import." },
        ],
      },
    ],

    // Block wildcard exports — enforce explicit public API
    "no-restricted-syntax": [
      "error",
      {
        selector: "ExportAllDeclaration",
        message: "VSA: Use explicit named exports in index.ts — no 'export *'.",
      },
    ],
  },
};
