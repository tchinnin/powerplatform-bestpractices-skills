---
name: ppbp-codeapps-setup
description: >
  Additive best practices for Power Apps Code Apps scaffolding and deployment.
  Use when the user is structuring a Code App repository, choosing or upgrading
  dependencies, configuring environment-specific values, or deciding how to lay
  out multiple apps. Defers all scaffold/init/auth/deploy commands to the
  official code-apps-preview:create-code-app skill.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.1.0"
---

## Official skill

`code-apps-preview:create-code-app` — owns the authoritative procedure for
scaffolding (`npx degit` the Vite template), initialising (`pac code init`),
authenticating, and deploying (`pac code push`). **Always load and follow that
skill for every command.** If it is not active, strongly recommend the user
install it before proceeding. This skill never restates or overrides its steps —
it only adds conventions the official skill leaves open.

## Best practices (additive only)

1. **Match the template's React version — never pin a different major.** The
   official Vite template sets the React version. Before adding or upgrading any
   dependency, check the actual version in the scaffolded `package.json` and
   verify the dependency is compatible with it. Do not hard-code a React version
   from memory.
2. **One app per subfolder.** Give each Code App its own folder with its own
   `package.json` so versioning and `pac code push` stay independent. Never put
   multiple apps in a flat shared folder.
3. **Externalise environment-specific values via `import.meta.env`.** Vite
   injects them at build time; never hard-code environment IDs or URLs.
4. **Run every `pac` command exactly as the official skill shows it** —
   `pwsh -NoProfile -Command "pac ..."` — because `pac` is a Windows executable
   not on the bash PATH. Do not invent bare `pac` invocations.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Pinning React to a version that differs from the scaffolded template — breaks the app and contradicts the official template. | Use the version the template ships; verify new deps against it. |
| Importing CommonJS-only packages — Vite's ESM bundler fails on packages that only expose `require()`. | Prefer ESM packages (`"type": "module"`); use an ESM fork or a Vite plugin shim. |
| Multiple apps in one flat folder — breaks independent versioning and deployment. | One subfolder per app, each with its own `package.json`. |
| Re-deriving scaffold/init/auth/deploy commands here — risks drifting from the official procedure. | Defer to `code-apps-preview:create-code-app` for all commands. |

## Skill boundaries

This skill adds repository-layout, dependency, and configuration conventions on
top of the official Code Apps procedure. It does not cover:

- The scaffold/init/auth/deploy procedure itself → `code-apps-preview:create-code-app`
- Domain orientation and repository layout → `ppbp-codeapps-overview`
- Generated data-access code, bundle optimisation, data-fetching hygiene → `ppbp-codeapps-connectors`
- Custom / company UX/UI guidelines, theming, design assets, HTML previews → `ppbp-codeapps-uxui`
- Generative Pages inside model-driven apps → `ppbp-genpages-overview`
- Dataverse schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
- Solution lifecycle → `ppbp-alm-solutions`
