# React Code App review checklist

Use when reviewing a pull request or a generated change in a Code App.

## Code App / SDK

- [ ] Nothing edited under `src/generated/`; types imported from generated models (`import type`)?
- [ ] Components never call generated services; access goes through `src/services/` with `unwrap`?
- [ ] Every `getAll` has a minimal `select`; filter / sort / `top` done server-side?
- [ ] Dataverse field rules from `dataverse-reference.md` respected (choices, virtual fields, lookups)?
- [ ] Router basename block untouched; no `window.location` / absolute `/…` URLs?

## TanStack Query

- [ ] Reads through a per-resource hook over `queryOptions`; keys from the feature factory and containing every variable?
- [ ] Mutations invalidate (promise returned) or `setQueryData`; no manual `refetch`, no effect?
- [ ] `isPending` / `isFetching` / error / empty all handled; `data` never copied into state?
- [ ] SDK pagination `skipToken` not confused with TanStack's `skipToken`?

## Organisation and routing

- [ ] File in the right place (`components/ui/`, `components/<feature>/`, `pages/`), kebab-case, dependency direction respected?
- [ ] Route declared in `router.tsx`, lazy, layout via `<Outlet />`, view state in the URL?
- [ ] No global store library added (Zustand, Redux…)?

## React

- [ ] Single-responsibility components; none defined inside another?
- [ ] `components/ui/` primitive reused or extended rather than forked?
- [ ] Hooks at top level, exhaustive deps, lint green?
- [ ] Minimal state, no copied props / server data, reset via `key`?
- [ ] `useEffect` only for external sync, with cleanup?
- [ ] Stable `key` (GUID) on lists; no `{n && …}`?
- [ ] No unmeasured memoisation?
- [ ] Typed props, no `any` / abusive `as`, `import type`?
- [ ] Forms labelled, validated, no double submission?
- [ ] Semantic HTML, keyboard/focus OK, a11y lint green?
- [ ] No secret, no unsanitised `dangerouslySetInnerHTML`?
- [ ] Tests on behaviour, `src/services/` mocked?
- [ ] `npm run lint` and `npm run build` green?
