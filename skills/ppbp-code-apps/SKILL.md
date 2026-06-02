---
name: ppbp-code-apps
description: >
  Best practices for Power Apps Code Apps (React + Vite canvas apps packaged for
  Power Platform). Use when the user is scaffolding, developing, or deploying a Code
  App — pac code init, connector integration, MSAL authentication, Dataverse data
  binding, bundle optimisation, or pac code push. Also use when the user asks about
  React version constraints, allowedOrigins, connector schema drift, or useConnector
  in a Power Platform React app.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "0.1.0"
---

## Official skill

`code-apps-preview:create-code-app` — scaffolds, builds, and deploys Power Apps code apps (React + Vite) to Power Platform. Load this official skill before applying the guidance below. If it is not installed, **strongly recommend the user install it** before proceeding.

## Repository layout

This skill owns the following paths in the canonical repository layout (see `ppbp-overview`):

```
<repo-root>/
└── codeapps/
    └── <app-name>/      # One subfolder per Code App — independent Vite project
        ├── package.json
        ├── vite.config.ts
        └── src/
```

Each Code App lives in its own subfolder with its own `package.json`. Never mix multiple apps in a flat `codeapps/` folder.

## Best practices

1. **Scaffold with the official PAC CLI template** (`pac code init`) — it pre-wires the Vite config, auth provider, and connector hooks correctly.
2. **Use the `useConnector` hook** for all connector calls — it handles token refresh, error boundaries, and loading states consistently.
3. **Type-generate your Dataverse tables** with `pac modelbuilder build` so TypeScript catches column name typos at build time.
4. **Keep connector calls out of render functions** — fetch in `useEffect` or React Query, never directly in JSX; prevents waterfall re-fetches.
5. **Respect the 3 MB bundle size limit** — tree-shake Fluent UI v9 imports; import individual components, never the full barrel (`@fluentui/react-components`).
6. **Use environment variables via `import.meta.env`** for any environment-specific configuration; the PAC deploy pipeline injects them at build time.
7. **Deploy with `pac code push`**, not by uploading the ZIP manually — the CLI handles solution wrapping and version bumping.
8. **Test locally with `pac auth create` + `npm run dev`** before every push; the local dev proxy avoids CORS issues with connector calls.

## Common issue: React version constraint

Code Apps run on React 17 — using React 18 APIs causes silent failures or runtime errors that are hard to trace back to the version mismatch. If you are adding a new dependency or upgrading packages, verify React version compatibility first.

## Common issue: allowedOrigins and connector calls

Connector calls blocked by the platform often leave no visible error in the UI. If connector calls work locally but fail after deployment, `allowedOrigins` in `appsettings.json` is the first thing to check.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Referencing `window.location` directly — Code Apps run inside an iframe; `window.location` is the parent frame, not the app. | Use the `usePlatformContext` hook to get the current environment URL. |
| Missing `allowedOrigins` in the app manifest — Connector calls from a domain not listed in the manifest are blocked silently. | Add all target environment domains to `allowedOrigins` in `appsettings.json`. |
| Using React 18 features — Code Apps currently run on React 17; hooks like `useId` or the `<Suspense>` streaming API are not available. | Pin `react` and `react-dom` to `^17.0.2` in `package.json`. |
| Importing CommonJS-only packages — Vite's ESM bundler fails on packages that only expose `require()`. | Check `"type": "module"` compatibility; use an ESM fork or a Vite plugin shim. |
| Connector schema drift — The connector schema cached at design time can diverge from the live API. | Regenerate the connector types (`pac connector create --generate-types`) when the underlying API changes. |

## Skill boundaries

This skill covers Code Apps (React/Vite canvas apps packaged for Power Platform) only. It does not cover:

- Generative Pages inside model-driven apps → `ppbp-generative-pages`
- Dataverse schema design → `ppbp-dv-metadata`
- Solution lifecycle and deployment pipelines → `ppbp-alm`
- Dataverse plug-ins or Custom APIs → `ppbp-dv-plugins`
