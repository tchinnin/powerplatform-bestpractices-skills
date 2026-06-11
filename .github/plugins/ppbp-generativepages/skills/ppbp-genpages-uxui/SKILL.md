---
name: ppbp-genpages-uxui
description: >
  Best practices for applying your own or your company's UX/UI guidelines to a Power
  Apps Generative Page. Use when the user wants to brand a generative page, apply a
  colour palette / typography / spacing system, set up a theme, work with design
  guidelines, or turn HTML/Claude design previews into a real page. Because a
  generative page lives inside a model-driven app, branding MUST be expressed by
  theming Fluent UI v9 — the opposite of Code Apps, where the UI library is free.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0.0"
---

## Official skill

`model-apps:genpage` owns the **stack** — React, TypeScript, and **Fluent UI v9** —
plus the single-`.tsx` page model, the runtime surface, the authoring rules, and
deployment. **Load it before this skill** and, if it is not active, strongly
recommend the user install it. This skill is purely additive: it tells you how to
express custom branding *within* that Fluent-v9 stack — it never restates the stack,
the Fluent APIs, or the page wiring.

General design-helper skills (`ui-ux-pro-max`, `frontend-design`) may help produce
layouts and previews, but they are not Power Platform-aware — anything they emit must
be re-expressed as Fluent UI v9 components per the rules below.

## Core principle: brand *through* the Fluent v9 theme — not a second library

This is the **opposite** of a Code App. A Code App may pick any UI library and feed
tokens into it; a generative page may not. It runs **inside a model-driven app** whose
chrome, navigation, and controls are Fluent UI v9, and the page must look native to
that host. So custom branding is applied by **theming Fluent v9**, never by bolting
another library on top or hard-coding values:

- **Generate a Fluent brand theme from `guidelines.md`.** Turn your brand colour into
  a Fluent `BrandVariants` ramp and build light/dark themes from it. The written
  guideline is the source; the theme is its machine translation.
- **Consume Fluent design tokens, never literals.** Read colours, spacing, radii and
  type from Fluent's `tokens` (e.g. `tokens.colorBrandBackground`,
  `tokens.spacingHorizontalM`) inside `makeStyles`. A token automatically tracks the
  active light/dark theme; a hard-coded hex does not.
- **Do not introduce a second UI library** (Material, Mantine, Tailwind component
  kits, Bootstrap) to chase a look. It fragments the page from its host and bloats it.
- **One source of truth.** `uxui/guidelines.md` is the human-readable spec; the Fluent
  brand theme is its translation. When the guideline changes, change the theme, not
  individual components.

## Consistency with the model-driven host (non-negotiable)

A generative page is a guest in the model-driven app. Branding must **harmonise** with
that host, not fight it:

- **Honour the host's light/dark mode** — provide both `createLightTheme` and
  `createDarkTheme` from the same brand ramp so the page follows the user's theme.
- **Keep Fluent's structure** — its control sizing, focus states, and spacing rhythm —
  so the page feels like part of the app, not an embedded micro-site. Tune the brand
  ramp and accent, not the fundamentals of how Fluent looks and behaves.
- **Restrained accent.** Apply your brand mainly to primary actions and accents; let
  neutrals and surfaces stay close to Fluent defaults so the page blends with the host.

Concrete `BrandVariants` ramp generation, light/dark theme building, and token
consumption examples live in
[`references/fluent-theming.md`](references/fluent-theming.md) — load it before
writing any theming code.

## The shared `uxui/` layout

Generative pages reuse the **same** top-level `uxui/` folder and the **same**
`guidelines.md` as Code Apps — one design system for the repo. Page previews live in a
dedicated `genpages/` subfolder, one folder per page:

```
<repo-root>/
└── uxui/
    ├── guidelines.md           # shared design spec — colours, typography, spacing
    ├── assets/                 # shared logo, icons, fonts
    ├── <app-name>/             # Code App previews (see ppbp-codeapps-uxui)
    └── genpages/               # generative-page previews
        └── <page-name>/        # one folder per page — name mirrors genpages/<…>/<page-name>
            └── <page-name>.html
```

- **`guidelines.md`** is shared and identical in format to the Code App one — the
  skeleton is owned by `ppbp-codeapps-uxui`; do not duplicate it here. The same palette,
  type scale and spacing rules drive both Code Apps and generative pages.
- **`genpages/<page-name>/`** holds the HTML design preview(s) for one page. The folder
  name **mirrors** the page's source folder under `genpages/<model-app-name>/<page-name>/`
  (see `ppbp-genpages-overview`) so design and code stay paired.

## HTML previews are design artifacts, not the page

The `.html` files under `uxui/genpages/<page-name>/` are **mockups** — a visual
contract to implement against, never shipped. Re-implement each as a Fluent UI v9
`.tsx` page styled from the brand theme. Make previews **look Fluent-native** (Fluent
spacing, control shapes, type scale) so they read as a realistic model-driven page,
not a generic web design that can't be built within the stack.

**Previews are point-in-time references, not synced artifacts.** A preview captures the
intended UX/UI *at the moment it was created*. As the page iterates, the real `.tsx`
will legitimately diverge — that is expected. Keeping previews in lockstep with the
code is neither required nor recommended.

**Diverge in the details, not in the principles.** Diverging from the exact markup is
fine; what must stay aligned are the core UX/UI principles the preview embodies —
visual hierarchy, layout language, spacing rhythm, branding, and host-consistent
interaction patterns. For a **major new page**, a developer *may* add a fresh preview
to agree on the look before building — a new design milestone, not an obligation to
retrofit previews for existing pages.

## Workflow

1. Write/refresh the shared `uxui/guidelines.md` (palette, type scale, spacing).
2. Optionally generate a Fluent-native HTML preview under `uxui/genpages/<page-name>/`
   to agree on the look before coding.
3. Translate `guidelines.md` into a Fluent **brand theme** — a `BrandVariants` ramp
   plus light/dark themes — applied at the page root.
4. Build the page as Fluent UI v9 components consuming Fluent `tokens` — following the
   design intent of the preview (diverge in details, honour the core principles).

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Adding a second UI library (Material, Mantine, Tailwind kit) to match a brand. | Theme Fluent UI v9 from a `BrandVariants` ramp; it is the only UI layer. |
| Hard-coding hex colours / px sizes in `makeStyles` or JSX — drift from the guideline and breaks light/dark. | Read Fluent `tokens` (`tokens.colorBrandBackground`, `tokens.spacingHorizontalM`). |
| Building only a light theme, so the page clashes when the host is in dark mode. | Build light *and* dark themes from the same ramp; follow the host mode. |
| Branding so heavily the page no longer looks like part of the model-driven app. | Apply brand to accents/primary actions; keep Fluent neutrals, sizing and structure. |
| Restating genpage's Fluent APIs, theme-provider wiring, or page model here. | Point to `model-apps:genpage`; keep only branding conventions here. |
| Duplicating the `uxui/guidelines.md` skeleton in this plugin. | Reuse the shared one — its skeleton is owned by `ppbp-codeapps-uxui`. |
| Shipping or importing the `uxui/genpages/<page>/*.html` previews as the page. | Treat HTML as a mockup; re-implement as a themed Fluent `.tsx` page. |
| Retrofitting old previews to match shipped code, or treating preview/code drift as a defect. | Leave previews as point-in-time references; add a new preview only for a major new page. |

## Skill boundaries

This skill covers applying custom / company UX/UI guidelines to a generative page via
Fluent v9 theming, the shared design assets, and HTML previews. It does not cover:

- Domain orientation and repository layout → `ppbp-genpages-overview`
- All page authoring, runtime APIs, the Fluent v9 stack, and deployment → `model-apps:genpage`
- The shared `uxui/guidelines.md` skeleton and Code App UX/UI → `ppbp-codeapps-uxui`
- Dataverse schema behind the page → `ppbp-dv-tables`, `ppbp-dv-columns`
- Solution placement of the page → `ppbp-alm-solutions`
