# `guidelines.md` template & design-token setup

This reference shows (1) a `uxui/guidelines.md` skeleton to capture a design system,
and (2) how to turn it into a centralised design-token layer so a Code App stays
branded without leaving the imposed React + Vite stack. The token approach is
**library-agnostic** — it works with plain CSS, Tailwind, or any component library.
A final section shows how to feed the same tokens into a component library's theme
if you use one (Fluent UI is shown as one example among many).

---

## 1. `uxui/guidelines.md` skeleton

Capture the design system in roles, scales and rules — never as one-off values.

```markdown
# <Company / App> UX-UI Guidelines

## Colours
| Role        | Hex       | Usage                                  |
|-------------|-----------|----------------------------------------|
| Brand       | #0F6CBD   | Primary actions, active state, links   |
| Brand-dark  | #0A4A82   | Hover / pressed on brand               |
| Surface     | #FFFFFF   | Card / panel background                |
| Background  | #F5F5F5   | App canvas                             |
| Text        | #242424   | Primary text                          |
| Text-muted  | #616161   | Secondary text, captions              |
| Success     | #107C10   | Positive feedback                     |
| Danger      | #C50F1F   | Errors, destructive actions           |

## Typography
- Font family: "Segoe UI", system-ui, sans-serif   (or a custom font in uxui/assets/)
- Scale: 12 / 14 / 16 / 20 / 28 / 40  (caption → body → subtitle → title → large)
- Weights: 400 regular, 600 semibold, 700 bold

## Spacing & disposition
- Base unit: 4px. Spacing scale: 4 / 8 / 12 / 16 / 24 / 32.
- Layout: 12-column responsive grid, max content width 1200px.
- Corner radius: 4px (controls), 8px (cards).

## Component conventions
- Primary button = brand colour; one primary action per view.
- Forms: label above field; inline validation under the field.
```

---

## 2. A central token layer (library-agnostic)

Express the guideline once as CSS custom properties, applied at the app root. Every
component — however it is built — reads from these variables, so a guideline change
propagates everywhere.

```css
/* src/theme/tokens.css */
:root {
  /* colours */
  --color-brand: #0F6CBD;
  --color-brand-dark: #0A4A82;
  --color-surface: #FFFFFF;
  --color-background: #F5F5F5;
  --color-text: #242424;
  --color-text-muted: #616161;
  --color-danger: #C50F1F;

  /* typography */
  --font-family-base: "Segoe UI", system-ui, sans-serif;
  --font-size-body: 14px;
  --font-size-title: 20px;
  --font-weight-semibold: 600;

  /* spacing & shape */
  --space-s: 8px;
  --space-m: 16px;
  --space-l: 24px;
  --radius-control: 4px;
  --radius-card: 8px;
}
```

Optionally mirror them in a typed module so component code gets autocompletion and
type-safety instead of stringly-typed variable names:

```ts
// src/theme/tokens.ts
export const tokens = {
  colorBrand: "var(--color-brand)",
  colorSurface: "var(--color-surface)",
  colorText: "var(--color-text)",
  spaceM: "var(--space-m)",
  radiusCard: "var(--radius-card)",
  fontSizeTitle: "var(--font-size-title)",
  fontWeightSemibold: "var(--font-weight-semibold)",
} as const;
```

Import the CSS once at the entry point so the variables exist app-wide:

```ts
// src/main.tsx
import "./theme/tokens.css";
```

---

## 3. Consume tokens — never literals

Components read from the tokens, so a guideline change in one place propagates
everywhere automatically. This works the same whether you use CSS modules, inline
styles, styled-components, or Tailwind (map the variables in `tailwind.config`).

```tsx
import { tokens } from "../theme/tokens";

export function SummaryCard() {
  return (
    <div
      style={{
        backgroundColor: tokens.colorSurface,
        padding: tokens.spaceM,
        borderRadius: tokens.radiusCard,
      }}
    >
      <h2 style={{ color: tokens.colorText, fontSize: tokens.fontSizeTitle }}>
        Sales summary
      </h2>
      <button
        style={{
          backgroundColor: tokens.colorBrand,
          color: "#fff",
          border: "none",
          borderRadius: "var(--radius-control)",
          padding: "var(--space-s) var(--space-m)",
        }}
      >
        New order
      </button>
    </div>
  );
}
```

### Wrong / Correct

| Wrong | Correct |
|---|---|
| `style={{ color: "#0F6CBD" }}` | `tokens.colorBrand` / `var(--color-brand)` |
| `style={{ padding: 16 }}` | `tokens.spaceM` / `var(--space-m)` |
| Different hexes copied into several components | One value in `tokens.css` |
| Mixing two component libraries to get a look | One UI approach themed from the tokens |

---

## 4. If you use a component library, theme it from the same tokens

Don't override components case by case — feed your tokens into the library's theming
mechanism once. The pattern is the same for any library; below are two examples.

**Tailwind** — map the CSS variables in the config so utilities stay branded:

```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: { brand: "var(--color-brand)", surface: "var(--color-surface)" },
      spacing: { s: "var(--space-s)", m: "var(--space-m)", l: "var(--space-l)" },
      borderRadius: { card: "var(--radius-card)", control: "var(--radius-control)" },
    },
  },
};
```

**Fluent UI v9** (one option, not a requirement) — build a theme from a brand ramp
generated from your Brand colour, then provide it once at the root:

```tsx
import { FluentProvider, createLightTheme, BrandVariants } from "@fluentui/react-components";

const brand: BrandVariants = { /* 16-step ramp generated from #0F6CBD */ } as BrandVariants;
const theme = createLightTheme(brand);

export default function App() {
  return <FluentProvider theme={theme}>{/* screens */}</FluentProvider>;
}
```

Either way, components consume the theme/tokens — never raw literals — so the brand
lives in exactly one place.

---

## 5. Custom fonts from `uxui/assets/`

If `guidelines.md` mandates a non-system font, copy the font files into the app's own
assets and declare them in global CSS, then point the token at it:

```css
@font-face {
  font-family: "Inter";
  src: url("./assets/Inter.woff2") format("woff2");
}
:root { --font-family-base: "Inter", "Segoe UI", system-ui, sans-serif; }
```

Import the file from the app's `src/assets` (not hot-linked across `uxui/`) so the
build bundles it correctly.
