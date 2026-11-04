# Zustand stores — complete patterns

Zustand is the app's only client-state library (shipped by the `starter` template).
It holds **client state that is shared or must outlive a screen**: UI preferences,
screen filters, multi-row selection. It never holds server data, form values or
state local to one component — see the decision tree in SKILL.md.

```
src/stores/
├── ui-store.ts          # preferences — persisted in localStorage
├── filters-store.ts     # screen filters per business scope — persisted in sessionStorage
└── selection-store.ts   # multi-row selection per scope — not persisted
src/lib/storage.ts       # namespaced storage keys
```

## 1. Namespaced, versioned persistence

The app runs in an iframe: its storage is third-party storage, partitioned by the
host and possibly unavailable (blocked by browser settings). `createJSONStorage`
returns nothing when the storage throws, and `persist` then simply doesn't persist —
the app must work identically with nothing restored. Prefix every key with the app
name so two apps (or two stores) never read each other's data.

```ts
// src/lib/storage.ts
const APP_STORAGE_PREFIX = "samples-app"; // the app's folder name under codeapps/

export function storageKey(store: string): string {
  return `${APP_STORAGE_PREFIX}:${store}`;
}
```

## 2. UI preferences — `localStorage`

```ts
// src/stores/ui-store.ts
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { storageKey } from "@/lib/storage";

export type Density = "comfortable" | "compact";

type UiState = {
  sidebarCollapsed: boolean;
  density: Density;
  toggleSidebar: () => void;
  setDensity: (density: Density) => void;
};

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      density: "comfortable",
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setDensity: (density) => set({ density }),
    }),
    {
      name: storageKey("ui"),
      storage: createJSONStorage(() => localStorage),
      version: 1,
      // Persist values only — never actions.
      partialize: (state) => ({ sidebarCollapsed: state.sidebarCollapsed, density: state.density }),
      // Bump `version` whenever the persisted shape changes; preferences can start over.
      migrate: () => ({ sidebarCollapsed: false, density: "comfortable" as Density }),
    },
  ),
);

// Derived hooks — components never write inline selectors.
export const useSidebarCollapsed = () => useUiStore((state) => state.sidebarCollapsed);
export const useToggleSidebar = () => useUiStore((state) => state.toggleSidebar);
export const useDensity = () => useUiStore((state) => state.density);
```

## 3. Screen filters per business scope — `sessionStorage`

Filters are indexed by the business context they apply to (a folder, a project, or
`"all"` for an unscoped list), so returning to folder A shows folder A's filters.
The store holds **committed** values only — the search text after debounce, trimmed;
multi-select values sorted — so a filter object can go straight into a query key.

```ts
// src/stores/filters-store.ts
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { storageKey } from "@/lib/storage";
import type { SampleFilters } from "@/services/samples.service";

export const DEFAULT_SAMPLE_FILTERS: SampleFilters = { search: "", status: null };

type FiltersState = {
  samples: Record<string, SampleFilters>;
  setSampleFilters: (scope: string, patch: Partial<SampleFilters>) => void;
  resetSampleFilters: (scope: string) => void;
};

export const useFiltersStore = create<FiltersState>()(
  persist(
    (set) => ({
      samples: {},
      setSampleFilters: (scope, patch) =>
        set((state) => ({
          samples: {
            ...state.samples,
            [scope]: { ...(state.samples[scope] ?? DEFAULT_SAMPLE_FILTERS), ...patch },
          },
        })),
      resetSampleFilters: (scope) =>
        set((state) => ({ samples: { ...state.samples, [scope]: DEFAULT_SAMPLE_FILTERS } })),
    }),
    {
      name: storageKey("filters"),
      storage: createJSONStorage(() => sessionStorage),
      version: 1,
      partialize: (state) => ({ samples: state.samples }),
      migrate: () => ({ samples: {} }),
    },
  ),
);

// Returns the stored object itself (stable reference) — no useShallow needed.
export const useSampleFiltersOf = (scope: string) =>
  useFiltersStore((state) => state.samples[scope] ?? DEFAULT_SAMPLE_FILTERS);
export const useSetSampleFilters = () => useFiltersStore((state) => state.setSampleFilters);
export const useResetSampleFilters = () => useFiltersStore((state) => state.resetSampleFilters);
```

Adding a screen's filters = one typed slice (`orders: Record<string, OrderFilters>`)
and its two actions. Keep slices explicit; no generic `Record<string, unknown>` bag.

## 4. Multi-row selection — not persisted

Selection holds **ids**, never rows (rows stay in the Query cache). Each row reads a
boolean for itself, so toggling one checkbox re-renders one row.

```ts
// src/stores/selection-store.ts
import { create } from "zustand";
import { useShallow } from "zustand/react/shallow";

const EMPTY: ReadonlySet<string> = new Set();

type SelectionState = {
  byScope: Record<string, ReadonlySet<string>>;
  toggle: (scope: string, id: string) => void;
  selectMany: (scope: string, ids: readonly string[]) => void;
  clear: (scope: string) => void;
};

export const useSelectionStore = create<SelectionState>()((set) => ({
  byScope: {},
  toggle: (scope, id) =>
    set((state) => {
      // Always a new Set: mutating the existing one would not notify subscribers.
      const next = new Set(state.byScope[scope] ?? EMPTY);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { byScope: { ...state.byScope, [scope]: next } };
    }),
  selectMany: (scope, ids) => set((state) => ({ byScope: { ...state.byScope, [scope]: new Set(ids) } })),
  clear: (scope) => set((state) => ({ byScope: { ...state.byScope, [scope]: EMPTY } })),
}));

// One primitive per selector…
export const useIsSelected = (scope: string, id: string) =>
  useSelectionStore((state) => (state.byScope[scope] ?? EMPTY).has(id));
export const useSelectedCount = (scope: string) =>
  useSelectionStore((state) => (state.byScope[scope] ?? EMPTY).size);
// …or useShallow when the selector builds an array or an object.
export const useSelectedIds = (scope: string) =>
  useSelectionStore(useShallow((state) => [...(state.byScope[scope] ?? EMPTY)]));
export const useSelectionActions = () =>
  useSelectionStore(useShallow((state) => ({ toggle: state.toggle, selectMany: state.selectMany, clear: state.clear })));
```

```tsx
// src/components/samples/select-sample-cell.tsx
import { Checkbox } from "@/components/ui/checkbox";
import { useIsSelected, useSelectionActions } from "@/stores/selection-store";

export function SelectSampleCell({ scope, id, name }: { scope: string; id: string; name: string }) {
  const selected = useIsSelected(scope, id);
  const { toggle } = useSelectionActions();
  return <Checkbox checked={selected} onCheckedChange={() => toggle(scope, id)} aria-label={`Select ${name}`} />;
}
```

## 5. Feature hook — filters + selection, one API for the screen

Changing the filters clears the scope's selection: a bulk action must never apply to
rows the user can no longer see.

```ts
// src/components/samples/use-sample-filters.ts
import { useCallback } from "react";
import type { SampleFilters } from "@/services/samples.service";
import { useResetSampleFilters, useSampleFiltersOf, useSetSampleFilters } from "@/stores/filters-store";
import { useSelectionActions } from "@/stores/selection-store";

export function useSampleFilters(scope: string) {
  const filters = useSampleFiltersOf(scope);
  const setSampleFilters = useSetSampleFilters();
  const resetSampleFilters = useResetSampleFilters();
  const { clear } = useSelectionActions();

  const setFilters = useCallback(
    (patch: Partial<SampleFilters>) => {
      setSampleFilters(scope, patch);
      clear(scope);
    },
    [scope, setSampleFilters, clear],
  );

  const clearFilters = useCallback(() => {
    resetSampleFilters(scope);
    clear(scope);
  }, [scope, resetSampleFilters, clear]);

  return {
    filters, // committed and normalised: usable as is in a query key
    hasFilters: filters.search !== "" || filters.status !== null,
    setFilters,
    clearFilters,
  };
}
```

## 6. Fast input: local draft, committed to the store after a pause

Keystrokes stay in local state; only the debounced, trimmed value reaches the store
(and therefore the query key and `sessionStorage`). When the store value changes from
elsewhere — "Clear filters", another screen — the draft follows, using React's
"adjust state when a prop changes" pattern (a conditional `setState` during render,
accepted by the react-hooks rules).

```ts
// src/hooks/use-committed-draft.ts
import { useEffect, useState } from "react";

export function useCommittedDraft(committed: string, commit: (value: string) => void, delayMs = 300) {
  const [draft, setDraft] = useState(committed);
  const [lastCommitted, setLastCommitted] = useState(committed);

  if (committed !== lastCommitted) {
    setLastCommitted(committed);
    // Only an external change overwrites what the user is typing.
    if (draft.trim() !== committed) setDraft(committed);
  }

  useEffect(() => {
    const value = draft.trim();
    if (value === committed) return;
    const timer = setTimeout(() => commit(value), delayMs);
    return () => clearTimeout(timer);
  }, [draft, committed, commit, delayMs]);

  return [draft, setDraft] as const;
}
```

```tsx
// src/components/samples/sample-filters-bar.tsx
import { useCallback } from "react";
import { FieldGroup } from "@/components/ui/field-group";
import { SearchInput } from "@/components/ui/search-input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCommittedDraft } from "@/hooks/use-committed-draft";
import { SAMPLE_STATUS_OPTIONS } from "./samples.rules";
import { useSampleFilters } from "./use-sample-filters";

const ALL = "all";

export function SampleFiltersBar({ scope }: { scope: string }) {
  const { filters, setFilters } = useSampleFilters(scope);
  const commitSearch = useCallback((search: string) => setFilters({ search }), [setFilters]);
  const [search, setSearch] = useCommittedDraft(filters.search, commitSearch);

  return (
    <div className="flex flex-wrap items-end gap-4">
      <FieldGroup label="Search" htmlFor="sample-search">
        <SearchInput id="sample-search" value={search} onValueChange={setSearch} placeholder="Sample name" />
      </FieldGroup>
      <FieldGroup label="Status" htmlFor="sample-status">
        <Select
          value={filters.status === null ? ALL : String(filters.status)}
          onValueChange={(value) => setFilters({ status: value === ALL ? null : Number(value) })}
        >
          <SelectTrigger id="sample-status" className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All statuses</SelectItem>
            {SAMPLE_STATUS_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={String(option.value)}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FieldGroup>
    </div>
  );
}
```

## 7. Outside React — loaders, handlers

```tsx
// src/router.tsx (excerpt — keep the template's basename block above it)
import type { RouteObject } from "react-router-dom";
import { queryClient } from "@/providers/query-client";
import { sampleListOptions } from "@/components/samples/samples.queries";
import { DEFAULT_SAMPLE_FILTERS, useFiltersStore } from "@/stores/filters-store";

export const samplesRoute: RouteObject = {
  path: "samples",
  // Warm the cache with the filters the user left on this screen.
  loader: () =>
    queryClient.ensureInfiniteQueryData(
      sampleListOptions(useFiltersStore.getState().samples.all ?? DEFAULT_SAMPLE_FILTERS),
    ),
  lazy: async () => ({ Component: (await import("@/pages/samples")).default }),
};
```

`getState()` / `setState()` are for code outside components (loaders, plain handlers,
tests). Components always go through the exported hooks.

## 8. Deep links — the play URL, not the store

Only the play URL (`https://apps.powerapps.com/play/e/{environmentId}/app/{appId}?…`)
can be shared. Its query parameters reach the app through
`getContext().app.queryParams`; read them once at start-up and turn them into a
navigation.

```ts
// src/hooks/use-deep-link.ts
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getContext } from "@microsoft/power-apps/app";
import { sampleDetailPath } from "@/lib/routes";

let consumed = false;

// Mounted once in pages/_layout.tsx. Link format: …/app/{appId}?sampleId={guid}
export function useDeepLink(): void {
  const navigate = useNavigate();

  useEffect(() => {
    if (consumed) return;
    let cancelled = false;
    void getContext().then(({ app }) => {
      if (cancelled || consumed) return;
      consumed = true;
      const sampleId = app.queryParams.sampleId;
      if (sampleId) navigate(sampleDetailPath(sampleId), { replace: true });
    });
    return () => {
      cancelled = true;
    };
  }, [navigate]);
}
```

## 9. Tests — every store reset before every test

```ts
// src/test/setup.ts
import "@testing-library/jest-dom/vitest";
import { beforeEach } from "vitest";
import { useFiltersStore } from "@/stores/filters-store";
import { useSelectionStore } from "@/stores/selection-store";
import { useUiStore } from "@/stores/ui-store";

beforeEach(() => {
  // getInitialState() keeps the actions; setState({}, true) would erase them.
  useUiStore.setState(useUiStore.getInitialState(), true);
  useFiltersStore.setState(useFiltersStore.getInitialState(), true);
  useSelectionStore.setState(useSelectionStore.getInitialState(), true);
  localStorage.clear();
  sessionStorage.clear();
});
```

Add every new store to this list in the same change.

```ts
// src/stores/selection-store.test.ts
import { describe, expect, it } from "vitest";
import { useSelectionStore } from "./selection-store";

describe("selection store", () => {
  it("toggles an id with a new Set", () => {
    const before = useSelectionStore.getState().byScope.all;
    useSelectionStore.getState().toggle("all", "a");
    const after = useSelectionStore.getState().byScope.all;
    expect(after?.has("a")).toBe(true);
    expect(after).not.toBe(before);
  });
});
```

## Wrong / correct

| Wrong | Correct |
|---|---|
| `const { search, setSearch } = useFiltersStore()` — subscribes to the whole store | One selector per value, through an exported hook |
| `useStore((s) => ({ a: s.a, b: s.b }))` — new object each call, re-render loop in Zustand v5 | `useStore(useShallow((s) => ({ a: s.a, b: s.b })))` or two primitive selectors |
| `useFiltersStore((s) => s.samples[scope])` written inside a component | `useSampleFiltersOf(scope)` exported by the store |
| `set({ rows: query.data })` / a store mirroring Query data | Query is the only home of server data; the store holds ids and filters |
| `setFilters({ search: event.target.value })` on each keystroke | Local draft + `useCommittedDraft` |
| `state.selected.add(id); set({ selected: state.selected })` | `new Set(...)` in the action |
| `persist` with key `"filters"`, no `version`, whole state persisted | `storageKey("filters")`, `version` + `migrate`, `partialize` |
| A `Set` or a selection in a persisted store | Selection store without `persist` |
| One `app-store.ts` holding UI, filters, selection and the current record | One store per domain; the current record id stays in the route |
| `?status=2` search params for screen filters | The filters store (the iframe URL is neither shared nor kept on reload) |
| Tests depending on a previous test's store state | Reset every store in `src/test/setup.ts` |
