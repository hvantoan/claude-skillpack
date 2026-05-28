// Boundary enforcement for Simple VSA using eslint-plugin-boundaries
// Requires: npm i -D eslint-plugin-boundaries
import boundaries from "eslint-plugin-boundaries";

export const boundaryConfig = {
  files: ["**/*.{ts,tsx}"],
  plugins: { boundaries },
  settings: {
    "boundaries/elements": [
      {
        type: "feature",
        pattern: "src/features/*",
        mode: "folder",
        capture: ["featureName"],
      },
      {
        type: "shared",
        pattern: "src/shared",
        mode: "file",
      },
      {
        type: "app",
        pattern: "src/app",
        mode: "file",
      },
    ],
    "import/resolver": {
      typescript: true,
      node: true,
    },
  },
  rules: {
    // Rule 1: Dependency direction — who can import whom
    "boundaries/dependencies": [
      "error",
      {
        default: "disallow",
        rules: [
          { from: ["app"], allow: ["feature", "shared"] },
          { from: ["feature"], allow: ["feature", "shared"] },
          { from: ["shared"], allow: ["shared"] },
        ],
        message:
          "VSA: '${file.type}' cannot import '${dependency.type}'. ${file.type} → ${dependency.type} is not allowed.",
      },
    ],

    // Rule 2: Entry-point enforcement — features must go through index.ts
    "boundaries/entry-point": [
      "error",
      {
        default: "disallow",
        rules: [
          {
            from: ["feature", "app"],
            target: ["feature"],
            allow: ["**/index.ts"],
          },
          {
            from: ["feature", "app"],
            target: ["shared"],
            allow: "**",
          },
        ],
        message:
          "VSA: Use public API — import from '@/features/${target.elementCaptured.featureName}' instead of deep import.",
      },
    ],

    // Rule 3: No private — block access to internal feature files
    "boundaries/no-private": [
      "error",
      {
        allowUncles: true,
        entryPoint: "index.ts",
      },
    ],
  },
};
