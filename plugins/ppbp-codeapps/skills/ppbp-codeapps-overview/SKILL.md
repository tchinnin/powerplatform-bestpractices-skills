---
name: ppbp-codeapps-overview
description: >
  Power Apps Code Apps domain overview. Use when starting any Code App task —
  scaffolding, architecture, components, Dataverse data access, error handling,
  review or deployment. Provides the repository layout for Code Apps (including the
  mandatory docs/<app-name>/ call map), the five team principles shared by every Code
  App skill (UI/logic isolation, reuse first, server-side data work, four async
  states, centralised errors) and routes to the right task skill in this plugin.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "2.0.0"
---

## Official skill

`code-apps-preview:create-code-app` — owns scaffolding, build, and deployment of
Power Apps Code Apps (React + Vite), and the `add-*` skills own data sources. Load it
for all procedure, commands, and version requirements. If it is not active,
**strongly recommend the user install it** before proceeding. This plugin only adds
conventions the official skills leave open — it never restates their commands or
constraints.

## Repository layout

When a repo hosts Code Apps, each app is an independent project under `codeapps/`,
its documentation under `docs/<app-name>/`, and its design assets under `uxui/`:

```
<repo-root>/
├── codeapps/
│   └── <app-name>/          # one self-contained Code App (its own package.json)
│       └── …                # standard project — src/ organisation in ppbp-codeapps-architecture
├── docs/
│   └── <app-name>/          # app documentation — path mirrors codeapps/<app-name>
│       └── dataverse-calls.md   # MANDATORY call map: every Dataverse call, per screen and action
└── uxui/                    # design system & previews — shared with Generative Pages
    ├── guidelines.md        # colours, typography, spacing, layout rules (skeleton owned by ppbp-codeapps-uxui)
    ├── assets/              # logo, icons, fonts shared across apps
    └── codeapps/
        └── <app-name>/      # HTML design previews for one app — path mirrors codeapps/<app-name>
            └── <app-name>-<screen>.html
```

- One subfolder per app under `codeapps/`, each with its own `package.json`, built
  and deployed independently. Never mix multiple apps in one flat folder.
- `docs/<app-name>/dataverse-calls.md` is created with the first Dataverse call and
  updated in the same change as every new or modified call (template in
  `ppbp-codeapps-data`). Other documentation of the app sits next to it.
- `uxui/` is shared with Generative Pages (`uxui/genpages/`, see
  `ppbp-genpages-overview`); one `guidelines.md` drives both.

## Domain scope

| Skill | Covers (additive only) |
|---|---|
| `ppbp-codeapps-setup` | `starter` template, dependencies, tooling baseline (TypeScript, ESLint, Prettier, tests, Devtools), bundle budget |
| `ppbp-codeapps-architecture` | UI ⇄ logic isolation: layers, `src/` by feature, where state lives (Query / route / form / local / Zustand stores / Context), split thresholds, lint boundaries, routing under the host |
| `ppbp-codeapps-components` | Reuse first (search → extend → promote), shared `DataTable` / `AsyncState` with the four states, forms, accessibility in code |
| `ppbp-codeapps-data` | 🚨 Server-side delegation (OData → FetchXML via connector → Custom API), TanStack Query conventions, paging, counts, writes, cache policy, call map |
| `ppbp-codeapps-errors` | One error model and normaliser, `dataverse-result` module, global error channels, boundaries, logging sink |
| `ppbp-codeapps-react` | Generic React 19 / TypeScript rules: effects, derived state, hooks, keys, performance, tests |
| `ppbp-codeapps-review` | Read-only audit of a Code App against all the above, report ranked P1 / P2 / P3 |
| `ppbp-codeapps-uxui` | Custom / company UX/UI guidelines via design tokens / theming, design assets, HTML previews |

## Global Code App principles

1. **UI renders, logic decides, services fetch.** Components and pages hold no
   business rule and call no service; rules are pure functions, orchestration lives in
   hooks → `ppbp-codeapps-architecture`.
2. **Reuse before you create.** Search `components/ui/`, `hooks/`, `lib/` and the
   features first; extend with a variant; promote anything a second feature needs →
   `ppbp-codeapps-components`.
3. **🚨 The server does the work.** Every Dataverse call goes through TanStack Query,
   returns one bounded page, and pushes filtering, counting and aggregation to
   Dataverse — OData first, FetchXML through the Dataverse connector next, a bound or
   unbound Custom API for business processing and multi-row writes. Looping over
   pages in the browser is forbidden → `ppbp-codeapps-data`.
4. **Every async view renders four states** — loading, error, empty, no results —
   through the shared `DataTable` / `AsyncState` → `ppbp-codeapps-components`.
5. **Errors are classified, shown and logged once, centrally** — never swallowed,
   never shown raw → `ppbp-codeapps-errors`.
6. **Design freedom within the imposed stack.** Any custom or company UX/UI guideline,
   expressed through a central design-token layer, with assets under `uxui/` →
   `ppbp-codeapps-uxui`.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Multiple apps in one flat folder — breaks independent versioning and deployment. | One subfolder per app, each with its own `package.json`. |
| App documentation inside `codeapps/<app-name>/` or scattered at the repo root. | `docs/<app-name>/`, mirroring the app path. |
| An app without `docs/<app-name>/dataverse-calls.md`, or a call map out of date. | Create it with the first call; update it with every call. |
| Restating the official scaffold / deploy / version steps in a ppbp skill — drifts when the official skill changes. | Point to `code-apps-preview:create-code-app`; keep only additive conventions here. |

## Skill boundaries

This skill covers Code App domain orientation and repository layout. It does not cover:

- Template, dependencies, tooling, bundle → `ppbp-codeapps-setup`
- Layers, `src/` organisation, state placement, routing → `ppbp-codeapps-architecture`
- Reusable components, tables, async states, forms, accessibility in code → `ppbp-codeapps-components`
- Dataverse and connector data access, FetchXML, Custom API calls, call map → `ppbp-codeapps-data`
- Error handling → `ppbp-codeapps-errors`
- Generic React / TypeScript rules → `ppbp-codeapps-react`
- Auditing an existing app → `ppbp-codeapps-review`
- Custom / company UX/UI guidelines, theming, design assets, HTML previews → `ppbp-codeapps-uxui`
- The scaffold / init / auth / deploy procedure itself → `code-apps-preview:create-code-app`
- Custom API design and plug-ins → `ppbp-dv-plugins-overview`
- Generative Pages inside model-driven apps → `ppbp-genpages-overview`
- Project repository layout → `ppbp-overview`
