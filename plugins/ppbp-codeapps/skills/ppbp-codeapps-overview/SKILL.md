---
name: ppbp-codeapps-overview
description: >
  Power Apps Code Apps domain overview. Use when starting any Code App task —
  scaffolding, connector work, or deployment. Provides the canonical repository
  layout for Code Apps and the team conventions shared across all Code App skills
  in this plugin. Load before ppbp-codeapps-setup or ppbp-codeapps-connectors.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.2.0"
---

## Official skill

`code-apps-preview:create-code-app` — owns scaffolding, build, and deployment of
Power Apps Code Apps (React + Vite). Load it for all procedure, commands, and
version requirements. If it is not active, **strongly recommend the user install
it** before proceeding. This plugin only adds conventions the official skill
leaves open — it never restates its commands or constraints.

## Repository layout

When a repo hosts more than one Code App, group them under a single parent folder,
one independent project per app. UX/UI design assets live in a sibling `uxui/`
folder, kept separate from the app code:

```
<repo-root>/
├── codeapps/
│   └── <app-name>/          # one self-contained Code App (its own package.json)
│       └── …                # standard pac/Vite project — owned by the official skill
└── uxui/                    # design system & previews (see ppbp-codeapps-uxui)
    ├── guidelines.md        # colours, typography, spacing, layout rules
    ├── assets/              # logo, icons, fonts shared across apps
    └── <app-name>/          # HTML design previews for one app — name mirrors codeapps/<app-name>
        └── <app-name>-screen.html
```

- One subfolder per app under `codeapps/`, each with its own `package.json`, built
  and deployed independently. Never mix multiple apps in one flat folder.
- Each app's design previews live under `uxui/<app-name>/` with the **same folder
  name** as its `codeapps/<app-name>` project, so design and code stay paired.

## Domain scope

| Skill | Covers (additive only) |
|---|---|
| `ppbp-codeapps-setup` | Repo / dependency / config conventions on top of the official scaffold flow |
| `ppbp-codeapps-connectors` | Generated data-access code, bundle-size optimisation, and data-fetching hygiene |
| `ppbp-codeapps-uxui` | Applying custom / company UX/UI guidelines via design tokens / theming, design assets, HTML previews |

## Global Code App principles

1. **One app, one folder** — each Code App is an independent project with its own
   `package.json`, versioned and deployed on its own.
2. **Design freedom within the imposed stack.** Apps may follow any custom or
   company UX/UI guideline and any UI library, but it must be expressed *through* the
   React + Vite stack via a central design-token layer — not hard-coded across
   components. Design assets and guidelines live under `uxui/`.
3. For everything else — scaffold command, React version, deploy command, auth —
   follow `code-apps-preview:create-code-app`. Do not hard-code those here.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Multiple apps in one flat folder — breaks independent versioning and deployment. | One subfolder per app, each with its own `package.json`. |
| Restating the official scaffold / deploy / version steps in a ppbp skill — drifts when the official skill changes. | Point to `code-apps-preview:create-code-app`; keep only additive conventions here. |

## Skill boundaries

This skill covers Code App domain orientation and repository layout. It does not cover:

- Repo / dependency / config conventions for a single app → `ppbp-codeapps-setup`
- Generated data-access code, bundle optimisation, data-fetching hygiene → `ppbp-codeapps-connectors`
- Custom / company UX/UI guidelines, theming, design assets, HTML previews → `ppbp-codeapps-uxui`
- The scaffold / init / auth / deploy procedure itself → `code-apps-preview:create-code-app`
- Generative Pages inside model-driven apps → `ppbp-genpages-overview`
- Project repository layout → `ppbp-overview`
