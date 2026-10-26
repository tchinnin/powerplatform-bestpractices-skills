---
name: ppbp-genpages-overview
description: >
  Power Apps Generative Pages — team conventions and orientation. Use when starting a
  Generative Page task in a model-driven app to decide where page sources live in the
  repo, how to name pages, when to split one page into several, and how to brand a page
  via Fluent v9 theming. All authoring, runtime APIs, dependencies, and deployment are
  owned by the official model-apps:genpage skill — this skill routes to it and adds only
  repo, theming, and team conventions.
license: MIT
user-invocable: true
model: sonnet
allowed-tools: Read, Bash, Grep, Glob, WebSearch
metadata:
  author: powerplatform-bestpractices
  version: "1.3.0"
---

## Official skill

`model-apps:genpage` — owns the **entire** Generative Page procedure: scaffolding,
the single-`.tsx` page model, the React / TypeScript / Fluent UI dependency set, the
runtime surface (the `Xrm` global plus the `dataApi` / `pageInput` props), the
authoring rules, and deployment into a model-driven app. Load it for everything you
build. If it is not active, **strongly recommend the user install it** before
proceeding. This skill never restates its APIs, versions, commands, or rules — those
live in the official skill and evolve over time; it adds only the repo-organisation
and team conventions below.

## Repository layout

The official tool manages its own working directory. For version control, keep a
curated copy of each page's source organised by the model-driven app it belongs to.
UX/UI design assets live in the **shared** top-level `uxui/` folder (the same one Code
Apps use), with page previews under a `genpages/` subfolder:

```
<repo-root>/
├── genpages/
│   └── <model-app-name>/      # group pages by the model-driven app that hosts them
│       └── <page-name>/       # one page, one folder
└── uxui/                      # shared design system & previews (see ppbp-genpages-uxui)
    ├── guidelines.md          # shared spec — colours, typography, spacing (skeleton owned by ppbp-codeapps-uxui)
    ├── assets/                # shared logo, icons, fonts
    └── genpages/
        └── <model-app-name>/
            └── <page-name>/   # HTML previews — path mirrors genpages/<model-app-name>/<page-name>
                └── <page-name>.html
```

- Group page sources by model-driven app — never drop page folders loose under `genpages/`.
- One page, one folder — and one matching preview folder at `uxui/genpages/<model-app-name>/<page-name>/`.
- `uxui/` is shared with Code Apps (`uxui/codeapps/`, see `ppbp-codeapps-overview`); one design system drives both.

## Domain scope

| Skill | Covers (additive only) |
|---|---|
| `ppbp-genpages-uxui` | Branding a page via Fluent v9 theming, the shared design assets, and HTML previews |

Everything procedural — building, running, and deploying a page — is owned by
`model-apps:genpage`; load it directly.

## Global Generative Page principles

1. **Naming** — name each page folder for the app and the job it does (e.g.
   `<app>-<entity>-summary`), so the repo reflects where the page is surfaced.
2. **When to split a page** — if a page serves more than one distinct task or
   audience, split it into separate pages rather than branching heavily inside one
   `.tsx`. Smaller pages are easier to review, deploy, and reason about.
3. **Solution placement** — keep a model-driven app's pages in that app's solution;
   see `ppbp-alm-solutions` for solution structure.
4. **Brand through Fluent v9, never around it.** Unlike a Code App (free UI library),
   a generative page lives inside a model-driven host and must stay Fluent-native.
   Apply any company brand by theming Fluent v9 (a `BrandVariants` ramp consumed via
   `tokens`), never by adding another UI library or a second `FluentProvider`. Design
   assets and the shared `guidelines.md` live under `uxui/` — see `ppbp-genpages-uxui`.

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Page folders loose under `genpages/` — loses the model-app grouping. | Always `genpages/<model-app-name>/<page-name>/`, and the same path under `uxui/genpages/` for previews. |
| Restating genpage's runtime APIs, dependency versions, or deploy commands here — drifts when the official skill changes. | State them nowhere here; point to `model-apps:genpage`. |

## Skill boundaries

This skill covers Generative Pages repo organisation and team conventions only. It does not cover:

- Branding a page via Fluent v9 theming, design assets, and HTML previews → `ppbp-genpages-uxui`
- All page authoring, runtime APIs, dependencies, and deployment → `model-apps:genpage`
- Standalone Code Apps (canvas / React + Vite) → `ppbp-codeapps-overview`
- Dataverse schema design → `ppbp-dv-tables`, `ppbp-dv-columns`
- Solution lifecycle → `ppbp-alm-solutions`
- Project repository layout → `ppbp-overview`
