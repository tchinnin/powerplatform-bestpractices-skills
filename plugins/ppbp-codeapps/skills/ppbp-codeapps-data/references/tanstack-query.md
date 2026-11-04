# TanStack Query over the generated services

Full pattern for server state in a Code App:
generated service → `src/services/` wrapper → feature `.queries.ts` → hooks → component.

The example uses a hypothetical Dataverse table `cr123_sample` whose generated files
are `src/generated/services/Cr123_samplesService.ts` and
`src/generated/models/Cr123_samplesModel.ts`. Replace the names with your own
generated ones. The generated method signatures are owned by the official `add-*`
skills; check them with `grep` before writing the wrapper. Field-level rules
(choice integers, virtual fields, lookups, files) are owned by
`code-apps-preview:add-dataverse` → `dataverse-reference.md`.

The result helpers (`run`, `runPage`, `runOrNull`, `Page`) and the `QueryClient`
(global error channels, `meta` typing) come from `ppbp-codeapps-errors` →
`references/error-handling.md`.

---

## 1. Service wrapper — no React, bounded, filtered on the server

```ts
// src/services/samples.service.ts
import { Cr123_samplesService } from "@/generated/services/Cr123_samplesService";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";
import { and, eq, odataString } from "@/lib/odata";
import { run, runOrNull, runPage, type Page } from "./dataverse-result";

export type SampleFilters = { search: string; status: number | null };
export type SampleInput = { name: string; code: string };

export const SAMPLES_PAGE_SIZE = 50;
const LIST_COLUMNS = ["cr123_sampleid", "cr123_name", "cr123_code", "cr123_status", "modifiedon"];

function toFilter({ search, status }: SampleFilters): string {
  return and(
    "statecode eq 0",
    status === null ? undefined : eq("cr123_status", status),
    search ? `contains(cr123_name,${odataString(search)})` : undefined,
  );
}

export const samplesService = {
  // Paged list: maxPageSize sets the page; the SDK returns the next skipToken.
  // count is requested on the first page only (Dataverse caps it at 5,000).
  listPage(filters: SampleFilters, skipToken?: string): Promise<Page<Cr123_samples>> {
    return runPage(() =>
      Cr123_samplesService.getAll({
        select: LIST_COLUMNS,
        filter: toFilter(filters),
        orderBy: ["modifiedon desc", "cr123_sampleid asc"],
        maxPageSize: SAMPLES_PAGE_SIZE,
        count: skipToken === undefined,
        skipToken,
      }),
    );
  },

  // Bounded list (dropdown, "recent items"): top, never a loop over pages.
  searchOptions(search: string): Promise<Cr123_samples[]> {
    return run(() =>
      Cr123_samplesService.getAll({
        select: ["cr123_sampleid", "cr123_name"],
        filter: toFilter({ search, status: null }),
        orderBy: ["cr123_name asc"],
        top: 20,
      }),
    );
  },

  get(id: string): Promise<Cr123_samples | null> {
    return runOrNull(() => Cr123_samplesService.get(id, { select: LIST_COLUMNS }));
  },

  create(input: SampleInput): Promise<Cr123_samples> {
    return run(() => Cr123_samplesService.create({ cr123_name: input.name, cr123_code: input.code }));
  },

  // The SDK returns the written row: use it instead of reading it again.
  update(id: string, changes: Partial<SampleInput>): Promise<Cr123_samples> {
    return run(() =>
      Cr123_samplesService.update(id, {
        ...(changes.name !== undefined && { cr123_name: changes.name }),
        ...(changes.code !== undefined && { cr123_code: changes.code }),
      }),
    );
  },

  remove(id: string): Promise<void> {
    return run(() => Cr123_samplesService.delete(id));
  },
};
```

The payloads are typed against the generated model: no `as never`, no
`as Parameters<…>`. If the compiler rejects a payload, the payload is wrong.

## 2. Query-string helpers — one module, escaping included

```ts
// src/lib/odata.ts
type Primitive = string | number | boolean;

export function odataString(value: string): string {
  return `'${value.replace(/'/g, "''")}'`;
}

function literal(value: Primitive): string {
  return typeof value === "string" ? odataString(value) : String(value);
}

export function eq(column: string, value: Primitive): string {
  return `${column} eq ${literal(value)}`;
}

// Microsoft.Dynamics.CRM.In — the right operator for "id in (…)" filters.
export function inFilter(column: string, values: readonly Primitive[]): string | undefined {
  if (values.length === 0) return undefined;
  const list = values.map((v) => literal(String(v))).join(",");
  return `Microsoft.Dynamics.CRM.In(PropertyName=${odataString(column)},PropertyValues=[${list}])`;
}

export function and(...parts: (string | undefined)[]): string {
  return parts.filter((p): p is string => Boolean(p)).map((p) => `(${p})`).join(" and ");
}
```

## 3. Feature queries — key factory, `queryOptions`, hooks

```ts
// src/components/samples/samples.queries.ts
import {
  infiniteQueryOptions,
  keepPreviousData,
  queryOptions,
  skipToken,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  type InfiniteData,
} from "@tanstack/react-query";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";
import type { Page } from "@/services/dataverse-result";
import { samplesService, type SampleFilters, type SampleInput } from "@/services/samples.service";

export const sampleKeys = {
  all: ["samples"] as const,
  lists: () => [...sampleKeys.all, "list"] as const,
  list: (filters: SampleFilters) => [...sampleKeys.lists(), filters] as const,
  options: (search: string) => [...sampleKeys.all, "options", search] as const,
  details: () => [...sampleKeys.all, "detail"] as const,
  detail: (id: string | undefined) => [...sampleKeys.details(), id] as const,
  mutations: {
    create: () => [...sampleKeys.all, "create"] as const,
    update: () => [...sampleKeys.all, "update"] as const,
    delete: () => [...sampleKeys.all, "delete"] as const,
  },
};

export const sampleListOptions = (filters: SampleFilters) =>
  infiniteQueryOptions({
    queryKey: sampleKeys.list(filters),
    queryFn: ({ pageParam }) => samplesService.listPage(filters, pageParam),
    initialPageParam: undefined as string | undefined,
    // SDK pagination skipToken — NOT TanStack's skipToken
    getNextPageParam: (last) => last.skipToken,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
    meta: { firstPageOnly: true },
  });

// TanStack's skipToken disables the query while the input is missing: no "idle" key, no `!`.
export const sampleDetailOptions = (id: string | undefined) =>
  queryOptions({
    queryKey: sampleKeys.detail(id),
    queryFn: id ? () => samplesService.get(id) : skipToken,
  });

export const sampleOptionsOptions = (search: string) =>
  queryOptions({
    queryKey: sampleKeys.options(search),
    queryFn: () => samplesService.searchOptions(search),
    staleTime: 30_000,
  });

export function useSamples(filters: SampleFilters) {
  return useInfiniteQuery(sampleListOptions(filters));
}

export function useSample(id: string | undefined) {
  return useQuery(sampleDetailOptions(id));
}

export function useSampleOptions(debouncedSearch: string) {
  return useQuery(sampleOptionsOptions(debouncedSearch));
}

type SampleListData = InfiniteData<Page<Cr123_samples>, string | undefined>;

function replaceInLists(queryClient: ReturnType<typeof useQueryClient>, row: Cr123_samples) {
  queryClient.setQueriesData<SampleListData>({ queryKey: sampleKeys.lists() }, (old) =>
    old
      ? {
          ...old,
          pages: old.pages.map((page) => ({
            ...page,
            items: page.items.map((item) => (item.cr123_sampleid === row.cr123_sampleid ? row : item)),
          })),
        }
      : old,
  );
}

export function useCreateSample(options: { silent?: boolean } = {}) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: sampleKeys.mutations.create(),
    mutationFn: (input: SampleInput) => samplesService.create(input),
    meta: { errorMessage: "The sample could not be created.", silent: options.silent },
    // A new row changes membership and order: invalidate the lists (returning the promise).
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sampleKeys.lists() }),
  });
}

export function useUpdateSample() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: sampleKeys.mutations.update(),
    mutationFn: ({ id, changes }: { id: string; changes: Partial<SampleInput> }) =>
      samplesService.update(id, changes),
    meta: { errorMessage: "The sample could not be saved." },
    // One strategy: patch the cache with the row the server returned. No invalidate on top.
    onSuccess: (row) => {
      queryClient.setQueryData(sampleKeys.detail(row.cr123_sampleid), row);
      replaceInLists(queryClient, row);
    },
  });
}
```

Rules embodied above:

- **Every query is defined once** with `queryOptions` / `infiniteQueryOptions`, and
  reused by `useQuery`, `useSuspenseQuery`, `prefetchQuery`, `ensureQueryData`,
  `fetchQuery` and `getQueryData`. Never rewrite a `queryKey` / `queryFn` pair inline.
- **Every key comes from the factory**, polling and mutation keys included. Every
  variable the `queryFn` uses is in the key.
- **`skipToken` for conditional queries.** It replaces `enabled: !!id` plus a non-null
  assertion, and replaces throwing inside `queryFn` when an input is missing.
- **One cache strategy per mutation**: patch with the returned row *or* invalidate.
  Patching and then invalidating doubles the traffic.
- **Every write has a `mutationKey`**, so `useMutationState` and the global error
  channel see it.

## 4. Imperative reads and polling

```ts
// Reading inside a handler — through the same queryOptions, so cache and dedup apply.
import { useQueryClient } from "@tanstack/react-query";

export function useSampleExists() {
  const queryClient = useQueryClient();
  return (id: string) => queryClient.fetchQuery(sampleDetailOptions(id)).then((row) => row !== null);
}
```

```ts
// src/components/jobs/jobs.queries.ts
// Polling a long-running job: the key comes from the factory, the interval stops itself.
import { queryOptions, skipToken } from "@tanstack/react-query";
import { jobsService } from "@/services/jobs.service"; // getStatus(jobId): Promise<{ done: boolean }>

export const jobKeys = {
  all: ["jobs"] as const,
  status: (jobId: string | undefined) => [...jobKeys.all, "status", jobId] as const,
};

export const jobStatusOptions = (jobId: string | undefined) =>
  queryOptions({
    queryKey: jobKeys.status(jobId),
    queryFn: jobId ? () => jobsService.getStatus(jobId) : skipToken,
    refetchInterval: (query) => (query.state.data?.done ? false : 5_000),
    staleTime: 0,
  });
```

## 5. Cache policy — choose `staleTime` per query

| Data | `staleTime` | Why |
|---|---|---|
| Reference data (countries, choice labels, current user) | `Infinity` | Changes with a deployment, not during a session |
| Lists the user filters and edits | 30 s | Short enough to see colleagues' changes on return |
| Detail of a record being edited | 30 s – 5 min | Writes patch it directly |
| Status of a running job (polling) | `0` + `refetchInterval` | Must be fresh by design |
| Default (from `providers/query-client.ts`) | 5 min | Anything not listed above |

Never set `Infinity` on data other users change. Never leave a polled or
frequently changing query on the default.

## 6. Infinite lists — keep only page 1 when nobody watches

An infinite query that is refetched reloads **every page in its cache**, one after
the other. Once a list is no longer displayed (route left, filter changed), trim it
to its first page:

```ts
// src/lib/first-page-only.ts
import type { InfiniteData, Query, QueryClient } from "@tanstack/react-query";

function trim(query: Query) {
  if (!query.meta?.firstPageOnly || query.getObserversCount() > 0) return;
  const data = query.state.data as InfiniteData<unknown> | undefined;
  if (!data || !Array.isArray(data.pages) || data.pages.length <= 1) return;
  // setState keeps dataUpdatedAt and isInvalidated: a stale list stays stale.
  query.setState({ data: { pages: data.pages.slice(0, 1), pageParams: data.pageParams.slice(0, 1) } });
}

export function keepFirstPageOnlyWhenInactive(queryClient: QueryClient): () => void {
  return queryClient.getQueryCache().subscribe((event) => {
    if (event.type === "observerRemoved" || event.type === "updated") trim(event.query);
  });
}
```

```tsx
// src/providers/query-provider.tsx
import { lazy, Suspense, useEffect, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { keepFirstPageOnlyWhenInactive } from "@/lib/first-page-only";
import { queryClient } from "./query-client";

const ReactQueryDevtools = import.meta.env.DEV
  ? lazy(() => import("@tanstack/react-query-devtools").then((m) => ({ default: m.ReactQueryDevtools })))
  : () => null;

export function QueryProvider({ children }: { children: ReactNode }) {
  useEffect(() => keepFirstPageOnlyWhenInactive(queryClient), []);
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Suspense fallback={null}>
        <ReactQueryDevtools initialIsOpen={false} />
      </Suspense>
    </QueryClientProvider>
  );
}
```

Writes on a displayed infinite list patch the cache (§3) rather than invalidating
it, for the same reason. When a write must mark a list stale without reloading it
now, use `invalidateQueries({ queryKey, refetchType: "none" })`.

## 7. Component usage

```tsx
// src/components/samples/sample-list.tsx
import { useMemo } from "react";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";
import { DataTable } from "@/components/ui/data-table";
import { useSampleFilters } from "./use-sample-filters";
import { useSamples } from "./samples.queries";
import { sampleColumns } from "./sample-columns";

type Props = {
  scope: string;
  onOpen: (id: string) => void;
  onArchive: (sample: Cr123_samples) => void;
};

export function SampleList({ scope, onOpen, onArchive }: Props) {
  // Committed, normalised filters from the filters store: used as is in the query key.
  const { filters, hasFilters, clearFilters } = useSampleFilters(scope);
  const samples = useSamples(filters);
  const rows = useMemo(() => samples.data?.pages.flatMap((page) => page.items) ?? [], [samples.data]);
  const columns = useMemo(() => sampleColumns({ onOpen, onArchive }), [onOpen, onArchive]);

  return (
    <DataTable
      caption="Samples"
      columns={columns}
      rows={rows}
      getRowId={(row) => row.cr123_sampleid}
      query={samples}
      hasFilters={hasFilters}
      onClearFilters={clearFilters}
      emptyMessage="No samples yet."
    />
  );
}
```

`DataTable` and `useInfiniteScroll` are in `ppbp-codeapps-components` →
`references/data-table.md`; `useSampleFilters` in `ppbp-codeapps-architecture` →
`references/stores.md`.

## 8. Mutation side effects in the caller

```tsx
// src/components/samples/rename-sample-dialog.tsx (excerpt)
const updateSample = useUpdateSample();

function handleSubmit(name: string) {
  updateSample.mutate(
    { id: sampleId, changes: { name } },
    { onSuccess: () => onOpenChange(false) },
  );
}

return (
  <Button type="submit" disabled={updateSample.isPending}>
    {updateSample.isPending ? "Saving…" : "Save"}
  </Button>
);
```

- `mutate` with callbacks, never `mutateAsync` + `try/catch`.
- `isPending` from the mutation, never a `submitting` state that duplicates it.
- To disable a control while *any* write on a row is running, read
  `useMutationState({ filters: { mutationKey: sampleKeys.mutations.update(), status: "pending" } })`.
- **On-demand downloads** may use `useMutation` (an imperative, uncached read). Add
  a comment saying so, so nobody "fixes" it into a query.

## 9. Preloading from the router

```tsx
// src/router.tsx (excerpt — keep the template's basename block above it)
import type { RouteObject } from "react-router-dom";
import { queryClient } from "@/providers/query-client";
import { sampleDetailOptions } from "@/components/samples/samples.queries";

export const sampleRoutes: RouteObject[] = [
  {
    path: "samples/:id",
    loader: ({ params }) => queryClient.ensureQueryData(sampleDetailOptions(params.id)),
    lazy: async () => ({ Component: (await import("@/pages/sample-detail")).default }),
  },
];
```

The page reads with `useSample(id)`; the loader only warms the cache.

## 10. Testing Query hooks

Fresh `QueryClient` per test, `retry: false`, the `src/services/` layer mocked — the
SDK cannot run outside the Power Apps host.

```tsx
// src/components/samples/samples.queries.test.tsx
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useSample } from "./samples.queries";
import { samplesService } from "@/services/samples.service";

vi.mock("@/services/samples.service", () => ({
  samplesService: { get: vi.fn() },
}));

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useSample", () => {
  it("does not fetch without an id", () => {
    const { result } = renderHook(() => useSample(undefined), { wrapper });
    expect(result.current.fetchStatus).toBe("idle");
    expect(samplesService.get).not.toHaveBeenCalled();
  });

  it("returns the row", async () => {
    vi.mocked(samplesService.get).mockResolvedValue({ cr123_sampleid: "1", cr123_name: "A" } as never);
    const { result } = renderHook(() => useSample("1"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.cr123_name).toBe("A");
  });
});
```

(`as never` is acceptable in test fixtures only.)

## Wrong / correct

| Wrong | Correct |
|---|---|
| `useEffect(() => { Service.getAll().then(setRows) }, [])` | `useSamples(filters)` over `sampleListOptions` |
| `do { r = await getAll({ skipToken }) } while (r.skipToken)` in one `queryFn` | `useInfiniteQuery`, one page per `queryFn` call |
| `getAll({ top: 50, skipToken })` to page | `getAll({ maxPageSize: 50, skipToken })`; `top` only for bounded lists |
| `queryKey: ['samples-' + id]` / `[...all, "idle"]` | `sampleKeys.detail(id)` + `skipToken` |
| `{ queryKey, queryFn }` rewritten inline for a `fetchQuery` | `queryClient.fetchQuery(sampleDetailOptions(id))` |
| `onSuccess: () => { setQueryData(...); invalidateQueries(...) }` | One of the two |
| `onSuccess: () => refetch()` | `invalidateQueries` on the factory key (promise returned) |
| `mutateAsync` + `try/catch` + `useState(submitting)` | `mutate(vars, { onSuccess })` + `isPending` |
| Writes queued by hand with refs, outside `useMutation` | `useMutation` with a `mutationKey`; drafts may stay local |
| `isLoading` to show a skeleton | `isPending` (no data yet) |
| `new QueryClient()` inside a component | Module-level client in `providers/query-client.ts` |
| `const [rows, setRows] = useState(query.data)` | Use `query.data` directly, or `select` |
| `getNextPageParam: () => skipToken` (TanStack import) | `getNextPageParam: (last) => last.skipToken` (SDK value) |
