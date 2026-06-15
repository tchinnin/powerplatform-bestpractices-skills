# Branding a generative page through Fluent UI v9

This reference covers the **one additive thing** this skill owns: turning a company
`guidelines.md` into a Fluent **brand theme** for a generative page. Everything about
*how the page is authored* — the `makeStyles` + `tokens` rules, the single-`.tsx`
model, and the `themeToVars` two-div mechanism used to apply a theme override — is
owned by `model-apps:genpage` (`references/rules.md`). Load that skill for the
mechanics; this file only shows how to produce the brand theme object you feed into it.

> **Hard constraints from the official skill — do not violate:**
> - **No second `FluentProvider`.** The host supplies one at the root; adding another
>   causes a double-render flicker in React 17.
> - **Forbidden functions:** `createTheme`, `mergeThemes`, `useTheme` (they don't
>   exist in Fluent v9 the way v8 code expects).
> - Style with `makeStyles` + `tokens`; inline styles only for dynamic values.
>
> `createLightTheme` / `createDarkTheme` / `BrandVariants` are **allowed** — they are
> the supported v9 way to build a theme object, and are not in the forbidden list.

---

## 1. The shared `guidelines.md` drives the ramp

`uxui/guidelines.md` is the **same** spec Code Apps use — its skeleton is owned by
`ppbp-codeapps-uxui`; do not duplicate it here. For theming a page you only need the
**Brand** colour and confirmation that it meets WCAG AA contrast. Everything else
(spacing, type scale) is expressed by consuming Fluent `tokens`, which already encode a
consistent scale.

---

## 2. Generate a `BrandVariants` ramp from the brand colour

Fluent themes are built from a 16-step brand ramp (`BrandVariants`, keys `10`–`160`).
Generate it once from your Brand hex — the easiest reliable source is the **Fluent UI
Theme Designer** (export the ramp), or any brand-ramp generator — then paste the result
as a typed constant. Do not hand-pick 16 shades by eye.

```ts
import {
  BrandVariants,
  createLightTheme,
  createDarkTheme,
  Theme,
} from "@fluentui/react-components";

// Generated from the guidelines.md Brand colour (#0F6CBD in this example).
const brand: BrandVariants = {
  10: "#020305",
  20: "#111723",
  30: "#16263D",
  40: "#193253",
  50: "#1B3F6A",
  60: "#1B4C82",
  70: "#18599B",
  80: "#1267B4",
  90: "#3174C2",
  100: "#4F82C8",
  110: "#6790CF",
  120: "#7D9ED5",
  130: "#92ACDC",
  140: "#A8BAE3",
  150: "#BDC8E9",
  160: "#D2D7F0",
};

export const brandLightTheme: Theme = createLightTheme(brand);
export const brandDarkTheme: Theme = createDarkTheme(brand);
```

`createLightTheme` / `createDarkTheme` produce full theme objects whose **neutrals,
spacing, radii and type still come from Fluent's defaults** — only the brand ramp is
yours. That is exactly what keeps the page consistent with the model-driven host.

---

## 3. Apply the brand theme — via the official `themeToVars` pattern only

You do **not** wrap the page in a `FluentProvider`. Instead, feed the theme object into
the `themeToVars` two-div pattern that `model-apps:genpage` documents for theme
overrides (its "Dark Mode Toggle" / theme-override rule). The only change versus that
pattern is **which theme object you pass**: substitute `brandLightTheme` /
`brandDarkTheme` for the stock `webLightTheme` / `webDarkTheme`.

```ts
// Schematic — the actual two-div wrapper and the themeToVars helper are owned by
// model-apps:genpage's rules.md. Reuse THAT code; only swap the theme source:
const theme = isDarkMode ? brandDarkTheme : brandLightTheme;
// → apply `theme` through the official themeToVars two-div wrapper.
```

Because the wrapper writes the theme as CSS custom properties, every Fluent descendant
and every `makeStyles` rule that reads `tokens` automatically picks up your brand — no
per-component overrides, no provider.

---

## 4. Consume tokens — never literals

Inside the page, style with `makeStyles` and read `tokens`. The brand now flows through
those tokens, so components need no awareness of the brand at all.

```tsx
import { makeStyles, tokens, Button } from "@fluentui/react-components";

const useStyles = makeStyles({
  card: {
    backgroundColor: tokens.colorNeutralBackground1,
    padding: tokens.spacingHorizontalL,
    borderRadius: tokens.borderRadiusMedium,
    color: tokens.colorNeutralForeground1,
  },
});

export function SummaryCard() {
  const styles = useStyles();
  return (
    <div className={styles.card}>
      <Button appearance="primary">New record</Button>
    </div>
  );
}
```

`appearance="primary"` and `tokens.colorBrand*` automatically reflect the brand ramp —
no hex anywhere in the component.

### Wrong / Correct

| Wrong | Correct |
|---|---|
| `<FluentProvider theme={brandTheme}>…` at the page root | Apply the ramp via the official `themeToVars` two-div pattern (host owns the provider) |
| `createTheme(...)` / `mergeThemes(...)` / `useTheme()` | `createLightTheme(brand)` / `createDarkTheme(brand)` + `tokens` |
| `style={{ color: "#0F6CBD" }}` | `tokens.colorBrandForeground1` inside `makeStyles` |
| Light theme only | Build light *and* dark from one ramp; follow the host mode |
| Adding a second UI library for a component | Use the Fluent v9 component, themed by the ramp |
