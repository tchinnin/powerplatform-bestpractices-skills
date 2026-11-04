---
name: ppbp-codeapps-setup
description: >
  Additive best practices for Power Apps Code Apps scaffolding, dependencies and
  tooling. Use when the user is scaffolding a new Code App (template choice), choosing
  or upgrading dependencies, configuring environment-specific values, or setting up
  the tooling baseline — strict TypeScript, ESLint (react-hooks, jsx-a11y, TanStack
  Query, layer boundaries), Prettier, tests, React Query Devtools — or analysing and
  splitting an oversized bundle. Defers all scaffold/init/auth/deploy commands to the
  official code-apps-preview:create-code-app skill.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.3.0"
---

## Official skill

`code-apps-preview:create-code-app` — owns the authoritative procedure for
scaffolding, initialising, authenticating, adding data sources and deploying, and
the CLI to use for each step. **Always load and follow that skill for every
command.** If it is not active, strongly recommend the user install it before
proceeding. This skill never restates or overrides its steps — it only adds
conventions the official skill leaves open.

## Scaffolding and dependencies

1. **Scaffold from the `starter` template, not `vite`.** Team convention: in the
   official scaffold step, use Microsoft's `templates/starter` (same
   `microsoft/PowerAppsCodeApps` repo, same procedure) in place of `templates/vite`.
   It ships the team's standard stack — shadcn/ui (Radix), Tailwind, React Router,
   TanStack Query/Table, sonner — and a router already wired for the Power Apps host.
   Every other step follows the official skill unchanged.
2. **Keep Zustand as the only client-state library.** `starter` ships `zustand`; it
   is the home of shared and cross-screen client state (when and how:
   `ppbp-codeapps-architecture`). Never add Redux, Jotai, Valtio, MobX or a second
   state library.
3. **Match the template's React version — never pin a different major.** Before
   adding or upgrading a dependency, read the version in the scaffolded
   `package.json` and check the dependency's peer requirements against it.
4. **Prefer ESM packages.** Vite's bundler fails on CommonJS-only packages; use an
   ESM alternative.
5. **Externalise environment-specific values via `import.meta.env`.** Never
   hard-code environment IDs or URLs. Everything in the bundle — including every
   `VITE_*` variable — is public: no secret, key or token in a Code App.
6. **Run every CLI command exactly as the official skill shows it**, including how it
   resolves the CLI binary. Do not invent bare invocations or flags.

## Tooling baseline — set it up before the first feature

The `starter` template's tooling is a starting point, not the standard. Apply this
baseline right after scaffolding; the complete files are in
[`references/tooling.md`](references/tooling.md).

| Area | Baseline | Why |
|---|---|---|
| TypeScript | `strict` + `noUncheckedIndexedAccess` | Forces guards instead of `!` on indexed access |
| ESLint — hooks | `eslint-plugin-react-hooks` **v7+**, flat `recommended` (the template ships v5) | Compiler-era rules (`refs`, `set-state-in-effect`, `purity`…) |
| ESLint — a11y | `eslint-plugin-jsx-a11y` (`flatConfigs.recommended`) | Catches clickable divs, missing labels and roles |
| ESLint — Query | `@tanstack/eslint-plugin-query` (`flat/recommended`) | Exhaustive keys, stable client, no rest destructuring |
| ESLint — layers | `@typescript-eslint/no-restricted-imports` per folder | Enforces UI ⇄ logic isolation (`ppbp-codeapps-architecture`) |
| ESLint — misc | `ecmaVersion: "latest"`, `no-non-null-assertion`, `no-console` (except the logging sink) | Modern syntax; no `!`; one logging path |
| Formatting | Prettier + `prettier-plugin-tailwindcss` + `eslint-config-prettier` | Consistent style and class order; never discussed in review |
| Tests | Vitest + React Testing Library + jsdom | Behaviour tests with `src/services/` mocked |
| Devtools | `@tanstack/react-query-devtools`, lazy, development only | Inspect cache and keys without shipping it |
| Libraries | `react-error-boundary`, `react-hook-form` + `zod` | Zone boundaries and forms (`ppbp-codeapps-errors`, `-components`) |

`src/generated/` and `.power/` are excluded from lint and formatting — never edited.

## Bundle budget

The bundle loads inside the Power Apps host at every launch. **No chunk may exceed
Vite's 500 kB warning** — treat it as a failure. Analyse with
`rollup-plugin-visualizer` (`npm run analyze`) whenever a dependency is added, then
split in this order: lazy routes, lazy heavy widgets (charts, editors, exports),
`manualChunks` for large shared libraries, per-component imports for UI libraries
(with Fluent UI v9, import components by name, never a whole barrel). Configuration
in [`references/tooling.md`](references/tooling.md) §6.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Scaffolding from `templates/vite` or `npm create vite` — loses the standard stack and the host-aware router. | Official scaffold procedure with `templates/starter`. |
| Adding a second state library (Redux, Jotai, Valtio, MobX…) next to Zustand. | Zustand for client state, TanStack Query for server state. |
| Pinning React to a version that differs from the scaffolded template. | Use the version the template ships; verify new deps against it. |
| Importing CommonJS-only packages. | Prefer ESM packages or an ESM fork. |
| Keeping the template's lint setup (react-hooks v5, `ecmaVersion: 2020`, no a11y, no Query plugin) and no Prettier. | Apply the tooling baseline before the first feature. |
| Leaving `noUncheckedIndexedAccess` off and silencing the compiler with `!`. | Enable it; guard instead. |
| Shipping a 500 kB+ main chunk. | Analyse, then lazy-load and split. |
| Importing a UI library's full barrel. | Import components individually. |
| Re-deriving scaffold/init/auth/deploy commands here. | Defer to `code-apps-preview:create-code-app`. |

## Skill boundaries

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- The scaffold/init/auth/deploy procedure itself → `code-apps-preview:create-code-app`
- Layers, folders, state placement and the layer lint rules → `ppbp-codeapps-architecture`
- Data access and TanStack Query → `ppbp-codeapps-data`
- Components, tables, forms → `ppbp-codeapps-components`
- Error handling → `ppbp-codeapps-errors`
- Generic React and TypeScript rules → `ppbp-codeapps-react`
- Custom / company UX/UI guidelines, theming → `ppbp-codeapps-uxui`
- Generative Pages inside model-driven apps → `ppbp-genpages-overview`
- Solution lifecycle → `ppbp-alm-solutions`
