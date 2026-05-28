// Boundary enforcement for Feature-Sliced Design (FSD) — 7-layer strict
// Requires: npm i -D eslint-plugin-boundaries
import boundaries from "eslint-plugin-boundaries";

export const fsdBoundaryConfig = {
  files: ["**/*.{ts,tsx}"],
  plugins: { boundaries },
  settings: {
    "boundaries/elements": [
      {
        type: "app",
        pattern: "src/app",
        mode: "folder",
        capture: ["sliceName"],
      },
      {
        type: "page",
        pattern: "src/pages/*",
        mode: "folder",
        capture: ["sliceName"],
      },
      {
        type: "widget",
        pattern: "src/widgets/*",
        mode: "folder",
        capture: ["sliceName"],
      },
      {
        type: "feature",
        pattern: "src/features/*",
        mode: "folder",
        capture: ["sliceName"],
      },
      {
        type: "entity",
        pattern: "src/entities/*",
        mode: "folder",
        capture: ["sliceName"],
      },
      {
        type: "shared",
        pattern: "src/shared",
        mode: "folder",
      },
    ],
    "import/resolver": {
      typescript: true,
      node: true,
    },
  },
  rules: {
    // FSD: Strict downward-only imports
    // app → pages → widgets → features → entities → shared
    "boundaries/dependencies": [
      "error",
      {
        default: "disallow",
        rules: [
          { from: ["app"], allow: ["page", "shared"] },
          { from: ["page"], allow: ["widget", "feature", "entity", "shared"] },
          { from: ["widget"], allow: ["feature", "entity", "shared"] },
          { from: ["feature"], allow: ["entity", "shared"] },
          { from: ["entity"], allow: ["shared"] },
          { from: ["shared"], allow: ["shared"] },
        ],
        message:
          "FSD: '${file.type}' cannot import '${dependency.type}'. Layers must import downward only.",
      },
    ],

    // Entry-point: each slice exposes via its segment index
    "boundaries/entry-point": [
      "error",
      {
        default: "disallow",
        rules: [
          // Higher layers can import from lower layer public APIs
          {
            from: ["page", "widget", "feature", "entity"],
            target: ["widget", "feature", "entity", "shared"],
            allow: ["**/index.ts"],
          },
          // app layer can import pages directly
          {
            from: ["app"],
            target: ["page"],
            allow: "**",
          },
        ],
        message:
          "FSD: Use public API — import from the slice index, not internal files.",
      },
    ],

    // No-private: enforce segment encapsulation
    "boundaries/no-private": [
      "error",
      {
        allowUncles: true,
        entryPoint: "index.ts",
      },
    ],
  },
};
