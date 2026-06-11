---
name: ppbp-codeapps-uxui
description: >
  Best practices for applying your own or your company's UX/UI guidelines to a
  Power Apps Code App. Use when the user wants to brand a Code App, apply a colour
  palette / typography / spacing system, set up design tokens or a theme, work with
  design guidelines, or turn HTML/Claude design previews into a real app. Keeps
  custom design within the React + Vite stack the official skill imposes, whatever
  UI library is chosen.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.2.0"
---

## Official skill

No official Microsoft skill exists for UX/UI guidelines in Code Apps. The **stack**
is owned by `code-apps-preview:create-code-app` (React + Vite + TypeScript, plus the
Power SDK wiring). **Load it before this skill** and, if it is not active, strongly
recommend the user install it. This skill is purely additive: it tells you how to
express custom branding *within* that stack — it never restates the stack itself.

General design-helper skills (`ui-ux-pro-max`, `frontend-design`) may assist with
producing layouts and previews, but they are not Power Platform-aware — anything
they emit must still build on the imposed React + Vite stack per the rules below.

## Core principle: design freedom, stack constraint

A Code App may follow **any** UX/UI guideline — your own or your company's brand —
and use **any** UI approach (a component library such as Fluent UI, Material UI or
Mantine, or plain CSS/Tailwind), **as long as the imposed stack is respected.** The
choice of UI library is the team's; what matters is that branding is expressed
cleanly *through* the stack, not bolted on:

- **Centralise design tokens.** Capture colours, typography, spacing and radii once
  — as CSS custom properties and/or a typed tokens module — and have components read
  from them. Never scatter literal hex codes, px sizes or ad-hoc margins through JSX.
- **Theme the library you chose; don't override it per-component.** If you use a
  component library, feed your tokens into its theming mechanism (e.g. a theme
  object / provider) rather than overriding individual components' styles. Don't mix
  several component libraries to chase a look. (Which library to prefer is an
  accessibility decision — see **Accessibility** below.)
- **One source of truth.** `uxui/guidelines.md` is the human-readable spec; the
  token layer is its machine translation. Keep them in sync; when the guideline
  changes, change the tokens, not individual components.

## The `uxui/` repository layout

Design assets live in a single top-level `uxui/` folder at the repo root, kept
separate from the Code App project(s) under `codeapps/`:

```
<repo-root>/
└── uxui/
    ├── guidelines.md           # the design spec: colours, typography, spacing, layout
    ├── assets/                 # logo, icons, illustrations, fonts referenced by apps
    └── <app-name>/             # design previews for ONE app (matches codeapps/<app-name>)
        ├── <app-name>-home.html
        └── <app-name>-detail.html   # one HTML per screen, or one file for the whole app
```

- **`guidelines.md`** — the written design system: colour palette (with roles, not
  just hexes), typography scale, spacing/disposition rules, component conventions.
  This is the source the token layer is built from.
- **`assets/`** — shared brand assets (logo, icons, custom fonts) referenced by the
  apps. Import production copies into the app's own assets; do not hot-link across
  folders at build time.
- **`<app-name>/`** — HTML design previews (e.g. generated with Claude design) for a
  specific app, one file per page or one file for the whole flow. The folder name
  **mirrors** `codeapps/<app-name>` so each preview is clearly associated with its app
  (a naming convention only — preview content is not kept in sync with the code).

## Accessibility (strongly recommended)

Branding must never come at the cost of accessibility. Treat WCAG AA as the baseline
for every Code App — these apps are business apps, often under enterprise
accessibility mandates.

- **Strongly prefer an accessibility-first component library.** Libraries such as
  **Fluent UI v9** or **Radix UI** ship keyboard navigation, focus management, ARIA
  roles and screen-reader support **by design** — you get compliant primitives for
  free instead of re-implementing (and getting wrong) focus traps, roving tabindex,
  and dialog semantics by hand. This is the single biggest accessibility lever and a
  strong reason to build on such a library rather than hand-rolled components.
- **Bake accessibility into the tokens.** Verify the palette in `guidelines.md` meets
  contrast ratios (≥4.5:1 for body text, ≥3:1 for large text / UI borders) *before*
  it becomes tokens — a brand colour that fails contrast is a guideline bug to fix at
  the source, not per-component.
- **Never rely on colour alone** to convey state (error, success, required) — pair it
  with text, an icon, or a label.
- **Keep semantics and keyboard support** — real `<button>`/`<a>`/heading elements,
  visible focus states, full keyboard operability, and labelled form fields.

## HTML previews are design artifacts, not the app

The `.html` files under `uxui/<app-name>/` are **mockups** — a visual contract to
implement against. They are never shipped or imported as the running app.
Re-implement each preview as React components in the chosen UI approach, styled from
the token layer; the preview's structure and look are the target, the stack and your
library decide the building blocks.

**Previews are a point-in-time reference, not a synced artifact.** A preview captures
the intended UX/UI **at the moment it was created**. As development iterates —
enhancements, bug fixes, refinements — the real app will legitimately diverge from
it, and that is expected. **Keeping previews in lockstep with the code is neither
required nor recommended** (it just creates maintenance churn). The code is the
source of truth for what ships; the preview is the source of truth for the original
design intent.

**Diverge in the details, not in the principles.** A preview expresses an *intention*
of the expected UX/UI — its layout language, visual hierarchy, spacing rhythm,
branding and interaction patterns. Diverging from the exact markup is fine and
normal; what must stay aligned are those **core UX/UI principles** the preview
embodies. Use the preview as the design contract for *how it should feel and behave*,
and let the implementation differ in specifics as long as it honours that intent.

When a **major new page or feature** comes up, a developer *may* add a fresh preview
under `uxui/<app-name>/` to align on the look before building it — treat that as a new
design milestone, not an obligation to retrofit previews for existing screens.

## Workflow

1. Write/refresh `uxui/guidelines.md` (palette, type scale, spacing).
2. Optionally generate HTML previews per screen under `uxui/<app-name>/` to agree on
   the look before coding.
3. Translate `guidelines.md` into a design-token layer (CSS variables and/or a typed
   tokens module; or your library's theme), applied once at the app root.
4. Build screens as React components consuming those tokens — following the design
   intent of the previews (diverge in details, honour the core principles).

For a concrete `guidelines.md` skeleton and a library-agnostic token setup (with a
note on feeding tokens into a component library's theme), load
[`references/guidelines-and-theming.md`](references/guidelines-and-theming.md).

## Anti-patterns (DO NOT DO)

| Anti-pattern | Correct approach |
|---|---|
| Hard-coding hex colours / px sizes / margins in JSX — drift from the guideline and impossible to re-theme. | Read from a central token layer (CSS variables / typed tokens) built off `guidelines.md`. |
| Mixing several UI component libraries to match a brand — bloats the bundle and fragments the look. | Pick one UI approach and theme it from your tokens. |
| Overriding a component library's styles per-instance instead of theming it. | Feed tokens into the library's theme/provider once; let them propagate. |
| Hand-rolling interactive controls (menus, dialogs, tabs) instead of using accessible primitives — keyboard/ARIA support is hard to get right. | Build on an accessibility-first library (Fluent UI, Radix UI) that ships these compliant by design. |
| A brand colour that fails WCAG contrast, or conveying state by colour alone. | Fix contrast at the token source; pair colour with text/icon. |
| Shipping or importing the `uxui/<app>/*.html` previews as the actual app. | Treat HTML as a mockup; re-implement it as styled React components. |
| Retrofitting old previews to match shipped code, or treating preview/code drift as a defect. | Leave previews as point-in-time references; only add a new preview for a major new page/feature. |
| Diverging so far from a preview that its core UX/UI principles (hierarchy, layout language, branding, interaction patterns) are abandoned. | Diverge in the details; honour the design intent the preview embodies. |
| Putting design assets inside one app's `src/` only — other apps can't reuse them. | Keep shared brand assets in `uxui/assets/`; copy production-needed ones into the app. |

## Skill boundaries

This skill covers applying custom/company UX/UI guidelines, design tokens/theming,
design assets, and HTML previews for Code Apps. It does not cover:

- Domain orientation and repository layout → `ppbp-codeapps-overview`
- Repo / dependency / config conventions → `ppbp-codeapps-setup`
- Generated data-access code, bundle optimisation, data-fetching hygiene → `ppbp-codeapps-connectors`
- The scaffold / init / auth / deploy procedure and the stack itself → `code-apps-preview:create-code-app`
- Generative Pages inside model-driven apps → `ppbp-genpages-overview`, `model-apps:genpage`
