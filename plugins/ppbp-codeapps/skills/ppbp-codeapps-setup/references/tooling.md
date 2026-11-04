# Tooling baseline for a Code App

Apply right after scaffolding from the `starter` template, before the first feature.
Every block is a complete file or a complete addition to a template file. Check the
installed versions against the template's React and ESLint versions before
installing (`npm view <package> peerDependencies`).

## 1. Dependencies

```bash
npm install react-error-boundary react-hook-form @hookform/resolvers zod
npm install -D eslint-plugin-react-hooks@latest eslint-plugin-jsx-a11y @tanstack/eslint-plugin-query \
  @tanstack/react-query-devtools prettier prettier-plugin-tailwindcss eslint-config-prettier \
  rollup-plugin-visualizer vitest @testing-library/react @testing-library/jest-dom jsdom
```

`zustand` comes with the template — keep it.

## 2. TypeScript — stricter than the template

Add to `compilerOptions` in `tsconfig.app.json`:

```json
{
  "compilerOptions": {
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true
  }
}
```

`noUncheckedIndexedAccess` turns `array[i]` and `record[key]` into `T | undefined`:
the compiler then demands guards instead of `!`.

## 3. ESLint — hooks v7, a11y, Query, layers, Prettier last

```js
// eslint.config.js
import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import jsxA11y from "eslint-plugin-jsx-a11y";
import pluginQuery from "@tanstack/eslint-plugin-query";
import tseslint from "typescript-eslint";
import prettier from "eslint-config-prettier";
import { defineConfig, globalIgnores } from "eslint/config";
import { layerRules } from "./eslint.layers.js";

export default defineConfig([
  globalIgnores(["dist", "src/generated", ".power"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.strict,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
      jsxA11y.flatConfigs.recommended,
      pluginQuery.configs["flat/recommended"],
    ],
    languageOptions: {
      ecmaVersion: "latest",
      globals: globals.browser,
    },
    rules: {
      "@typescript-eslint/no-non-null-assertion": "error",
      "no-console": "error",
    },
  },
  {
    // The single logging sink (ppbp-codeapps-errors) is the only console user.
    files: ["src/lib/report-error.ts"],
    rules: { "no-console": "off" },
  },
  ...layerRules,
  prettier,
]);
```

`eslint.layers.js` (import boundaries per layer) is in `ppbp-codeapps-architecture`
→ `references/layers.md` §6.

## 4. Prettier

`.prettierrc.json`:

```json
{
  "semi": false,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 120,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

`.prettierignore`:

```text
dist
src/generated
.power
```

Choose `semi` once per repository (match the template) and let Prettier enforce it —
style is never discussed in review.

## 5. Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "lint": "eslint .",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "tsc -b",
    "test": "vitest run",
    "analyze": "ANALYZE=1 vite build"
  }
}
```

`npm run lint`, `npm run format:check`, `npm run test` and `npm run build` are green
before every commit.

## 6. Bundle — budget, analysis, splitting

The bundle loads inside the Power Apps host on every launch. Budget: **no chunk over
Vite's 500 kB warning**, treated as a failure, not a hint.

```ts
// vite.config.ts — the template's config with the additions (keep its plugins and imports)
import { defineConfig } from "vite";
import { visualizer } from "rollup-plugin-visualizer";

const analyze = process.env.ANALYZE === "1";

export default defineConfig({
  plugins: [
    // …template plugins…
    analyze && visualizer({ open: true, gzipSize: true, filename: "dist/stats.html" }),
  ],
  build: {
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks: {
          charts: ["recharts"],
          tables: ["@tanstack/react-table"],
        },
      },
    },
  },
});
```

Order of levers:

1. **Lazy routes** (`lazy` on every route) — each page in its own chunk.
2. **Lazy heavy widgets** (charts, editors, spreadsheet export) with `React.lazy`
   inside the page that needs them.
3. **`manualChunks`** for large libraries shared by several lazy chunks.
4. **Tree-shake UI libraries**: import components individually. With Fluent UI v9,
   import from `@fluentui/react-components` by name — never a whole barrel.

Run `npm run analyze` whenever a dependency is added; the treemap shows what to split.

## 7. Devtools

React Query Devtools are loaded lazily and only in development — the provider in
`ppbp-codeapps-data` → `references/tanstack-query.md` §6 does exactly that.

## 8. Vitest

```ts
// vitest.config.ts
import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
    },
  }),
);
```

```ts
// src/test/setup.ts
import "@testing-library/jest-dom/vitest";
```

Once the app has stores, this file also resets every store before each test
(`ppbp-codeapps-architecture` → `references/stores.md` §9).
