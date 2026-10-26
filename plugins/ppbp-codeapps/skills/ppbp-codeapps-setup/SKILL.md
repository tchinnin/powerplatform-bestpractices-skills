---
name: ppbp-codeapps-setup
description: >
  Additive best practices for Power Apps Code Apps scaffolding and deployment.
  Use when the user is scaffolding a new Code App (template choice), structuring
  a Code App repository, choosing or upgrading dependencies, configuring
  environment-specific values, or deciding how to lay out multiple apps. Defers all scaffold/init/auth/deploy commands to the
  official code-apps-preview:create-code-app skill.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.2.0"
---

## Official skill

`code-apps-preview:create-code-app` — owns the authoritative procedure for
scaffolding, initialising, authenticating, adding data sources and deploying, and
the CLI to use for each step. **Always load and follow that skill for every
command.** If it is not active, strongly recommend the user
install it before proceeding. This skill never restates or overrides its steps —
it only adds conventions the official skill leaves open.

## Best practices (additive only)

1. **Scaffold from the `starter` template, not `vite`.** Team convention: in the
   official scaffold step, use Microsoft's `templates/starter` (same
   `microsoft/PowerAppsCodeApps` repo, same `degit` procedure) in place of
   `templates/vite`. It ships the team's standard stack — shadcn/ui (Radix),
   Tailwind, React Router, TanStack Query/Table, sonner — and a router already
   wired for the Power Apps host. Every other step follows the official skill
   unchanged.
2. **Remove Zustand right after scaffolding.** `starter` lists `zustand` in its
   dependencies but does not use it. Uninstall it (`npm uninstall zustand`) and do
   not reintroduce any global store library — state rules are in
   `ppbp-codeapps-react`.
3. **Match the template's React version — never pin a different major.** The
   scaffolded template sets the React version. Before adding or upgrading any
   dependency, check the actual version in the scaffolded `package.json` and
   verify the dependency is compatible with it. Do not hard-code a React version
   from memory.
4. **One app per subfolder.** Give each Code App its own folder with its own
   `package.json` so versioning and deployment stay independent. Never put
   multiple apps in a flat shared folder.
5. **Externalise environment-specific values via `import.meta.env`.** Vite
   injects them at build time; never hard-code environment IDs or URLs.
6. **Run every CLI command exactly as the official skill shows it** — including
   how it resolves the CLI binary. Do not invent bare invocations or flags.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Scaffolding from `templates/vite` or `npm create vite` — loses the standard stack and the host-aware router. | Official scaffold procedure with `templates/starter`. |
| Keeping or adding Zustand (or Redux, Jotai…) — duplicates the server cache and URL state. | Uninstall it; server state in TanStack Query, view state in the URL. |
| Pinning React to a version that differs from the scaffolded template — breaks the app and contradicts the official template. | Use the version the template ships; verify new deps against it. |
| Importing CommonJS-only packages — Vite's ESM bundler fails on packages that only expose `require()`. | Prefer ESM packages (`"type": "module"`); use an ESM fork or a Vite plugin shim. |
| Multiple apps in one flat folder — breaks independent versioning and deployment. | One subfolder per app, each with its own `package.json`. |
| Re-deriving scaffold/init/auth/deploy commands here — risks drifting from the official procedure. | Defer to `code-apps-preview:create-code-app` for all commands. |

## Skill boundaries

This skill adds repository-layout, dependency, and configuration conventions on
top of the official Code Apps procedure. It does not cover:

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- The scaffold/init/auth/deploy procedure itself → `code-apps-preview:create-code-app`
- React code organisation, state, TanStack Query, tests → `ppbp-codeapps-react`
- Generated data-access code, bundle optimisation, data-fetching hygiene → `ppbp-codeapps-connectors`
- Custom / company UX/UI guidelines, theming, design assets, HTML previews → `ppbp-codeapps-uxui`
- Generative Pages inside model-driven apps → `ppbp-genpages-overview`
- Dataverse schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
- Solution lifecycle → `ppbp-alm-solutions`
