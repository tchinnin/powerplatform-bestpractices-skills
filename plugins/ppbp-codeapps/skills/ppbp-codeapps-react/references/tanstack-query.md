# TanStack Query over the generated services

Full pattern for server state in a Code App: generated service → `src/services/`
wrapper → feature `.queries.ts` → component. The example uses a hypothetical
Dataverse table `cr123_sample` whose generated files are
`src/generated/services/Cr123_samplesService.ts` and
`src/generated/models/Cr123_samplesModel.ts`. Replace names with your own
generated ones — the generated method signatures are owned by the official
`add-*` skills; check them with `grep` before writing the wrapper.

Field-level Dataverse rules (choice integers, virtual fields, lookups,
file/image columns) are owned by `code-apps-preview:add-dataverse` →
`dataverse-reference.md` and are not repeated here.

---

## 1. `unwrap` — one place to check `IOperationResult`

```ts
// src/services/operation-result.ts
import type { IOperationResult } from "@microsoft/power-apps/data";

export function unwrap<T>(result: IOperationResult<T>): T {
  if (!result.success || result.error) {
    throw new Error(result.error?.message ?? "Data operation failed");
  }
  return result.data as T;
}

export type Page<T> = { items: T[]; skipToken?: string };

export function unwrapPage<T>(result: IOperationResult<T[]>): Page<T> {
  return { items: unwrap(result), skipToken: result.skipToken ?? undefined };
}
```

Throwing is what lets Query populate `error`, retry, and reach error boundaries.

## 2. Service wrapper — no React, minimal `select`, server-side filtering

```ts
// src/services/samples.service.ts
import { Cr123_samplesService } from "@/generated/services/Cr123_samplesService";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";
import { unwrap, unwrapPage, type Page } from "./operation-result";

export type SampleFilters = { search?: string; status?: number };

const LIST_COLUMNS = ["cr123_sampleid", "cr123_name", "cr123_status", "modifiedon"];
const PAGE_SIZE = 50;

function toFilter(f: SampleFilters): string | undefined {
  const parts: string[] = ["statecode eq 0"];
  if (f.status !== undefined) parts.push(`cr123_status eq ${f.status}`);
  if (f.search) parts.push(`contains(cr123_name,'${f.search.replace(/'/g, "''")}')`);
  return parts.join(" and ");
}

export const samplesService = {
  async list(filters: SampleFilters, skipToken?: string): Promise<Page<Cr123_samples>> {
    const result = await Cr123_samplesService.getAll({
      select: LIST_COLUMNS,
      filter: toFilter(filters),
      orderBy: ["modifiedon desc"],
      top: PAGE_SIZE,
      skipToken,
    });
    return unwrapPage(result);
  },

  async get(id: string): Promise<Cr123_samples> {
    return unwrap(await Cr123_samplesService.get(id));
  },

  async create(input: Partial<Cr123_samples>): Promise<Cr123_samples> {
    return unwrap(await Cr123_samplesService.create(input as Cr123_samples));
  },

  async update(id: string, changes: Partial<Cr123_samples>): Promise<void> {
    unwrap(await Cr123_samplesService.update(id, changes));
  },
};
```

## 3. QueryClient setup

Start from the template's `providers/query-provider.tsx` `defaultOptions`. Export
the client so router loaders can use it, and add global error handling:

```tsx
// src/providers/query-provider.tsx
import type { ReactNode } from "react";
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { toast } from "sonner";

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => toast.error("Unable to load data", { description: error.message }),
  }),
  mutationCache: new MutationCache({
    onError: (error) => toast.error("Unable to save", { description: error.message }),
  }),
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

export function QueryProvider({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
```

Avoid `staleTime: 0` (the TanStack default): it refetches on every mount.

## 4. Feature queries — key factory, `queryOptions`, hooks

```ts
// src/components/samples/samples.queries.ts
import {
  infiniteQueryOptions,
  keepPreviousData,
  queryOptions,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";
import { samplesService, type SampleFilters } from "@/services/samples.service";

export const sampleKeys = {
  all: ["samples"] as const,
  lists: () => [...sampleKeys.all, "list"] as const,
  list: (filters: SampleFilters) => [...sampleKeys.lists(), filters] as const,
  infinite: (filters: SampleFilters) => [...sampleKeys.lists(), "infinite", filters] as const,
  details: () => [...sampleKeys.all, "detail"] as const,
  detail: (id: string) => [...sampleKeys.details(), id] as const,
};

export const sampleListOptions = (filters: SampleFilters) =>
  queryOptions({
    queryKey: sampleKeys.list(filters),
    queryFn: () => samplesService.list(filters),
    placeholderData: keepPreviousData,
  });

export const sampleDetailOptions = (id: string) =>
  queryOptions({
    queryKey: sampleKeys.detail(id),
    queryFn: () => samplesService.get(id),
  });

export const sampleInfiniteOptions = (filters: SampleFilters) =>
  infiniteQueryOptions({
    queryKey: sampleKeys.infinite(filters),
    queryFn: ({ pageParam }) => samplesService.list(filters, pageParam),
    initialPageParam: undefined as string | undefined,
    // SDK pagination skipToken — NOT TanStack's skipToken
    getNextPageParam: (last) => last.skipToken,
  });

export function useSamples(filters: SampleFilters) {
  return useQuery(sampleListOptions(filters));
}

export function useSample(id: string | undefined) {
  return useQuery({ ...sampleDetailOptions(id ?? ""), enabled: !!id });
}

export function useInfiniteSamples(filters: SampleFilters) {
  return useInfiniteQuery(sampleInfiniteOptions(filters));
}

export function useCreateSample() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: Partial<Cr123_samples>) => samplesService.create(input),
    // returning the promise keeps the mutation pending until lists are refetched
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sampleKeys.lists() }),
  });
}

export function useUpdateSample() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, changes }: { id: string; changes: Partial<Cr123_samples> }) =>
      samplesService.update(id, changes),
    onSuccess: (_data, { id }) =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: sampleKeys.detail(id) }),
        queryClient.invalidateQueries({ queryKey: sampleKeys.lists() }),
      ]),
  });
}
```

Rules embodied above:

- Every variable used by `queryFn` appears in the key.
- `queryOptions` / `infiniteQueryOptions` share typing between `useQuery`,
  `useSuspenseQuery`, `prefetchQuery`, `ensureQueryData` and `getQueryData`.
- Dependent queries use `enabled`. TanStack's `skipToken` (a typed way to
  disable a query) is a different thing from the SDK's pagination `skipToken`.
- `select` functions must be stable — defined at module scope or memoised.
- No rest destructuring of the result (`const { data, ...rest } = useQuery(...)`):
  it defeats tracked properties and causes extra renders.

## 5. Component usage — states and mutation side effects

```tsx
// src/components/samples/sample-list.tsx
import { useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSamples } from "./samples.queries";

export function SampleList() {
  const [params] = useSearchParams();
  const search = params.get("q") ?? undefined;
  const samples = useSamples({ search });

  if (samples.isPending) return <Skeleton className="h-40 w-full" />;
  if (samples.isError)
    return (
      <div role="alert" className="space-y-2">
        <p>The samples could not be loaded.</p>
        <Button variant="outline" onClick={() => samples.refetch()}>Retry</Button>
      </div>
    );
  if (samples.data.items.length === 0) return <p>No samples yet.</p>;

  return (
    <ul aria-busy={samples.isFetching}>
      {samples.data.items.map((s) => (
        <li key={s.cr123_sampleid}>{s.cr123_name}</li>
      ))}
    </ul>
  );
}
```

```tsx
// src/components/samples/create-sample-button.tsx
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useCreateSample } from "./samples.queries";

export function CreateSampleButton() {
  const navigate = useNavigate();
  const createSample = useCreateSample();

  function handleClick() {
    createSample.mutate(
      { cr123_name: "New sample" },
      {
        onSuccess: (created) => {
          toast.success("Sample created");
          navigate(`/samples/${created.cr123_sampleid}`);
        },
      },
    );
  }

  return (
    <Button onClick={handleClick} disabled={createSample.isPending}>
      {createSample.isPending ? "Creating…" : "New sample"}
    </Button>
  );
}
```

UI side effects (toast, close dialog, navigate) go in the `mutate(..., { onSuccess })`
callbacks — never in a `useEffect` watching mutation state.

## 6. Preloading from the router

```tsx
// src/router.tsx (excerpt — keep the template's basename block above it)
import type { RouteObject } from "react-router-dom";
import { queryClient } from "@/providers/query-provider";
import { sampleDetailOptions } from "@/components/samples/samples.queries";

export const sampleRoutes: RouteObject[] = [
  {
    path: "samples/:id",
    loader: ({ params }) => queryClient.ensureQueryData(sampleDetailOptions(params.id!)),
    lazy: async () => ({ Component: (await import("@/pages/sample-detail")).default }),
  },
];
```

The page then reads with `useSample(id)` — the loader only warms the cache.

## 7. Optimistic updates (only when UX justifies it)

```ts
export function useRenameSample() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      samplesService.update(id, { cr123_name: name }),
    onMutate: async ({ id, name }) => {
      await queryClient.cancelQueries({ queryKey: sampleKeys.detail(id) });
      const previous = queryClient.getQueryData(sampleKeys.detail(id));
      queryClient.setQueryData(sampleKeys.detail(id), (old) =>
        old ? { ...old, cr123_name: name } : old,
      );
      return { previous };
    },
    onError: (_err, { id }, context) => {
      queryClient.setQueryData(sampleKeys.detail(id), context?.previous);
    },
    onSettled: (_data, _err, { id }) =>
      queryClient.invalidateQueries({ queryKey: sampleKeys.detail(id) }),
  });
}
```

Simpler alternative: render `mutation.variables` while `mutation.isPending`.

## 8. Suspense mode

Use `useSuspenseQuery(sampleDetailOptions(id))` inside `<Suspense>` and an error
boundary wired to `QueryErrorResetBoundary` when you want per-zone loading states.
Do not mix Suspense and `isPending`-style handling in the same screen.

```tsx
import { Suspense } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SampleDetail } from "./sample-detail";

export function SampleDetailZone({ id }: { id: string }) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          fallbackRender={({ resetErrorBoundary }) => (
            <Button variant="outline" onClick={resetErrorBoundary}>Retry</Button>
          )}
        >
          <Suspense fallback={<Skeleton className="h-24 w-full" />}>
            <SampleDetail id={id} />
          </Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
```

## 9. Testing Query hooks

Fresh `QueryClient` per test, `retry: false`, and the `src/services/` layer mocked
— the SDK cannot run outside the Power Apps host.

```tsx
// src/components/samples/samples.queries.test.tsx
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useSamples } from "./samples.queries";
import { samplesService } from "@/services/samples.service";

vi.mock("@/services/samples.service", () => ({
  samplesService: { list: vi.fn() },
}));

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useSamples", () => {
  it("returns the service items", async () => {
    vi.mocked(samplesService.list).mockResolvedValue({
      items: [{ cr123_sampleid: "1", cr123_name: "A" }] as never,
    });
    const { result } = renderHook(() => useSamples({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toHaveLength(1);
  });
});
```

## Wrong / correct

| Wrong | Correct |
|---|---|
| `useEffect(() => { Service.getAll().then(setRows) }, [])` | `useSamples(filters)` over `sampleListOptions` |
| `queryKey: ['samples-' + id]` | `sampleKeys.detail(id)` |
| `onSuccess: () => { refetch() }` | `onSuccess: () => queryClient.invalidateQueries({ queryKey: sampleKeys.lists() })` |
| `new QueryClient()` inside a component | Module-level client in `providers/query-provider.tsx` |
| `const [rows, setRows] = useState(query.data)` | Use `query.data` directly, or `select` |
| `getNextPageParam: () => skipToken` (TanStack import) | `getNextPageParam: (last) => last.skipToken` (SDK value) |
| Query used for dialog open/close or input text | `useState` |
| `mutateAsync` without `try/catch` | `mutate` with callbacks |
