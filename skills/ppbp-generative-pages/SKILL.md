---
name: ppbp-generative-pages
description: >
  Use when the user is building or modifying a Power Apps Generative Page
  inside a model-driven app: React + TypeScript + Fluent UI v9, PAC CLI deployment,
  accessing Dataverse data via the platform context, form/view embedding.
license: MIT
metadata:
  author: powerplatform-bestpractices
  version: "1.0"
---

## Best practices

1. **Use `@microsoft/powerplatform-mda-page-sdk`** for all platform interactions — it provides typed access to the form context, navigation, and Dataverse Web API.
2. **Stick to Fluent UI v9 components** (`@fluentui/react-components`) — they are the only component library guaranteed to match the shell's theming tokens.
3. **Access the current record via `context.parameters.entityId`**, not from the URL — the URL format is an implementation detail that may change.
4. **Declare all required form columns in the page manifest** (`customPage.yml`) under `dataColumns`; the platform pre-fetches them before mounting the page.
5. **Avoid full-page navigation inside the page** — use `context.navigation.openForm()` / `openEntityList()` to stay inside the model-driven shell.
6. **Deploy with `pac pages push`** after every change; the page is compiled and embedded in the solution automatically.
7. **Use `FluentProvider` with `webLightTheme` at the root** only as a local dev fallback — in production the shell injects its own theme tokens.

## Common pitfalls

**Calling `Xrm.Page` directly** — `Xrm.Page` is deprecated and unavailable in Generative Pages. *Use the SDK context object passed to the page entry point.*

**Fetching data outside `dataColumns`** — Columns not declared in the manifest are not pre-loaded and require a separate Web API call, adding latency. *Declare all needed columns upfront.*

**Using `useState` for platform context** — The platform context reference is stable; storing it in state causes stale closure bugs. *Store it in a `useRef` or access it directly from the entry point closure.*

**Forgetting `"type": "CustomPage"` in the sitemap** — Adding the page to the app without the correct sitemap entry type causes the page to render in a plain iframe without SDK access.

**Bundle size creep** — Generative Pages have a tighter bundle budget than standalone apps. *Monitor with `pac pages analyze`; lazy-load heavy sub-sections with `React.lazy`.*
