# Code App review report — format

One table per priority, findings numbered continuously across the tables, then a
suggested order of work. Each finding names a file and line range, states the
observable consequence, and gives one concrete fix tied to a rule.

## Template

````markdown
# Code App review — <app-name>

Scope: codeapps/<app-name>/src — <N> features, <M> services, <K> query modules.
Call map: docs/<app-name>/dataverse-calls.md — <present / missing / out of date>.

## 🔴 P1 — fix first

| # | Category | Finding | Recommendation |
|---|---|---|---|
| 1 | Errors | `samplesService.get` (`services/samples.service.ts` l.40-48) catches every error and returns `null`: a network or privilege failure shows "sample not found". | Use `runOrNull` — `null` only for `notFound`; let every other error propagate. (`ppbp-codeapps-errors`) |
| 2 | Dataverse data | `ordersService.listAll` loops on `skipToken` (up to 30 × 500 rows) to compute the dashboard totals in the browser. | FetchXML `aggregate` with `groupby` (one call), or an unbound Custom API if the logic exceeds FetchXML. (`ppbp-codeapps-data`) |

## 🟠 P2 — important improvements

| # | Category | Finding | Recommendation |
|---|---|---|---|
| 3 | TanStack Query | `pickSample` (`sample-dialog.tsx` l.120-130) rewrites the `queryKey` / `queryFn` of `sampleDetailOptions`. | `queryClient.fetchQuery(sampleDetailOptions(id))`. (`ppbp-codeapps-data`) |

## 🟡 P3 — quality and tooling

| # | Category | Finding | Recommendation |
|---|---|---|---|
| 4 | Tooling | ESLint uses `eslint-plugin-react-hooks` v5, no `jsx-a11y`, no Query plugin; no Prettier. | Apply the tooling baseline. (`ppbp-codeapps-setup`) |

## Suggested order

1. Findings 1, … — unify the error and data layers first: later fixes build on them.
2. …
3. Tooling last.

Summary: 2 P1, 1 P2, 1 P3.
````

## Categories

Use these labels so reports can be compared across apps:

`Errors` · `Dataverse data` · `TanStack Query` · `State` · `Architecture` ·
`Components` · `Forms` · `Accessibility` · `Performance` · `Bundle` · `Typing` ·
`Tooling` · `Documentation`

## Writing rules

- **Observable consequence first** ("a privilege failure shows 'not found'"), not
  just the rule broken.
- **Location precise** — file and line range; several locations in one finding when
  it is the same defect (e.g. "copied in 6 services: …").
- **One fix per finding**, concrete (names the helper, hook or component to create),
  with the owning skill in parentheses.
- **No false positives**: a respected convention is not a finding. A justified
  exception (documented in a comment or in the call map) is not a finding.
- **Group duplicates**: one finding for a pattern repeated in N places, listing them.
- **Order of work**: errors and data-layer foundations first (other fixes reuse
  them), then Query conventions, state, component splits, UI factorisation, tooling.
