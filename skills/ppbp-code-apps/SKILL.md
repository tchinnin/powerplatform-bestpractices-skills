---
name: ppbp-code-apps
description: >
  Use when the user is building or modifying a Power Apps Code App (React/Vite canvas app):
  project setup, connector integration, PCF controls, deployment to Power Platform,
  authentication (MSAL), data binding with Dataverse or other connectors.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0"
---

## Best practices

1. **Scaffold with the official PAC CLI template** (`pac code init`) — it pre-wires the Vite config, auth provider, and connector hooks correctly.
2. **Use the `useConnector` hook** for all connector calls — it handles token refresh, error boundaries, and loading states consistently.
3. **Type-generate your Dataverse tables** with `pac modelbuilder build` so TypeScript catches column name typos at build time.
4. **Keep connector calls out of render functions** — fetch in `useEffect` or React Query, never directly in JSX; prevents waterfall re-fetches.
5. **Respect the 3 MB bundle size limit** — tree-shake Fluent UI v9 imports; import individual components, never the full barrel (`@fluentui/react-components`).
6. **Use environment variables via `import.meta.env`** for any environment-specific configuration; the PAC deploy pipeline injects them at build time.
7. **Deploy with `pac code push`**, not by uploading the ZIP manually — the CLI handles solution wrapping and version bumping.
8. **Test locally with `pac auth create` + `npm run dev`** before every push; the local dev proxy avoids CORS issues with connector calls.

## Common pitfalls

**Referencing `window.location` directly** — Code Apps run inside an iframe; `window.location` is the parent frame, not the app. *Use the `usePlatformContext` hook to get the current environment URL.*

**Missing `allowedOrigins` in the app manifest** — Connector calls from a domain not listed in the manifest are blocked silently. *Add all target environment domains to `allowedOrigins` in `appsettings.json`.*

**Using React 18 features** — Code Apps currently run on React 17; hooks like `useId` or the `<Suspense>` streaming API are not available. *Pin `react` and `react-dom` to `^17.0.2` in `package.json`.*

**Importing CommonJS-only packages** — Vite's ESM bundler fails on packages that only expose `require()`. *Check `"type": "module"` compatibility; use an ESM fork or a Vite plugin shim.*

**Connector schema drift** — The connector schema cached at design time can diverge from the live API. *Regenerate the connector types (`pac connector create --generate-types`) when the underlying API changes.*
