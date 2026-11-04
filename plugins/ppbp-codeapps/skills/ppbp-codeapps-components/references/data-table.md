# Shared building blocks: async states, data table, inputs

Every list or grid in the app is a `DataTable`; every other async block is wrapped in
`AsyncState`. Both render the same four states, the same way, from one place. The
files below live in `src/components/ui/` and `src/hooks/` and contain no business
logic. They build on the template's shadcn primitives (`table`, `button`, `input`,
`label`, `skeleton`, `dialog`) and TanStack Table.

## 1. `AsyncState` — the four states, decided once

```tsx
// src/components/ui/async-state.tsx
import type { ReactNode } from "react";
import { AlertCircle, Inbox, SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { userMessageOf } from "@/lib/errors";

// Structural subset of UseQueryResult / UseInfiniteQueryResult.
export type QueryLike = {
  status: "pending" | "error" | "success";
  error: unknown;
  data: unknown;
  isFetching: boolean;
  refetch: () => unknown;
};

export type AsyncView = "loading" | "error" | "empty" | "noResults" | "content";

export function asyncView(query: QueryLike, isEmpty: boolean, hasFilters: boolean): AsyncView {
  if (query.status === "pending") return "loading";
  // With data on screen, a failed background refresh is announced by the global toast.
  if (query.status === "error" && query.data === undefined) return "error";
  if (isEmpty) return hasFilters ? "noResults" : "empty";
  return "content";
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 py-10 text-center">
      <AlertCircle aria-hidden className="size-6 text-destructive" />
      <p>{userMessageOf(error)}</p>
      <Button variant="outline" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 py-10 text-center text-muted-foreground">
      <Inbox aria-hidden className="size-6" />
      <div>{children}</div>
    </div>
  );
}

export function NoResultsState({ onClearFilters }: { onClearFilters?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 py-10 text-center text-muted-foreground">
      <SearchX aria-hidden className="size-6" />
      <p>No results match the current filters.</p>
      {onClearFilters && (
        <Button variant="outline" onClick={onClearFilters}>
          Clear filters
        </Button>
      )}
    </div>
  );
}

type AsyncStateProps = {
  query: QueryLike;
  isEmpty: boolean;
  emptyMessage: ReactNode;
  hasFilters?: boolean;
  onClearFilters?: () => void;
  loading?: ReactNode;
  children: ReactNode;
};

export function AsyncState({
  query,
  isEmpty,
  emptyMessage,
  hasFilters = false,
  onClearFilters,
  loading,
  children,
}: AsyncStateProps) {
  switch (asyncView(query, isEmpty, hasFilters)) {
    case "loading":
      return <>{loading ?? <Skeleton className="h-32 w-full" />}</>;
    case "error":
      return <ErrorState error={query.error} onRetry={() => query.refetch()} />;
    case "empty":
      return <EmptyState>{emptyMessage}</EmptyState>;
    case "noResults":
      return <NoResultsState onClearFilters={onClearFilters} />;
    case "content":
      return <div aria-busy={query.isFetching}>{children}</div>;
  }
}
```

Usage for any non-table block:

```tsx
// src/components/samples/sample-summary.tsx
import { AsyncState } from "@/components/ui/async-state";
import { useSample } from "./samples.queries";

export function SampleSummary({ id }: { id: string }) {
  const sample = useSample(id);
  return (
    <AsyncState query={sample} isEmpty={sample.data === null} emptyMessage="This sample no longer exists.">
      <h2 className="text-xl font-semibold">{sample.data?.cr123_name}</h2>
    </AsyncState>
  );
}
```

## 2. `useInfiniteScroll` — one observer for every list

```ts
// src/hooks/use-infinite-scroll.ts
import { useEffect, useRef, useState } from "react";

type Options = {
  hasNextPage: boolean;
  isFetching: boolean;
  fetchNextPage: () => unknown;
  rootMargin?: string;
};

// Returns a callback ref for a sentinel element placed after the last row.
export function useInfiniteScroll({ hasNextPage, isFetching, fetchNextPage, rootMargin = "200px" }: Options) {
  const [sentinel, setSentinel] = useState<Element | null>(null);
  const fetchNext = useRef(fetchNextPage);

  useEffect(() => {
    fetchNext.current = fetchNextPage;
  });

  useEffect(() => {
    if (!sentinel || !hasNextPage || isFetching) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) fetchNext.current();
      },
      { rootMargin },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [sentinel, hasNextPage, isFetching, rootMargin]);

  return setSentinel;
}
```

## 3. `DataTable` — states, refresh indicator, infinite scroll

```tsx
// src/components/ui/data-table.tsx
import type { ReactNode } from "react";
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  asyncView,
  EmptyState,
  ErrorState,
  NoResultsState,
  type QueryLike,
} from "@/components/ui/async-state";
import { useInfiniteScroll } from "@/hooks/use-infinite-scroll";
import { cn } from "@/lib/utils";

export type InfiniteQueryLike = QueryLike & {
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  fetchNextPage: () => unknown;
};

type DataTableProps<TRow> = {
  caption: string;
  columns: ColumnDef<TRow, unknown>[];
  rows: TRow[];
  getRowId: (row: TRow) => string;
  query: QueryLike | InfiniteQueryLike;
  emptyMessage: ReactNode;
  hasFilters?: boolean;
  onClearFilters?: () => void;
  skeletonRows?: number;
};

function isInfinite(query: QueryLike | InfiniteQueryLike): query is InfiniteQueryLike {
  return "fetchNextPage" in query;
}

export function DataTable<TRow>({
  caption,
  columns,
  rows,
  getRowId,
  query,
  emptyMessage,
  hasFilters = false,
  onClearFilters,
  skeletonRows = 8,
}: DataTableProps<TRow>) {
  const table = useReactTable({ data: rows, columns, getRowId, getCoreRowModel: getCoreRowModel() });
  const infinite = isInfinite(query) ? query : undefined;
  const sentinelRef = useInfiniteScroll({
    hasNextPage: infinite?.hasNextPage ?? false,
    isFetching: infinite?.isFetchingNextPage ?? false,
    fetchNextPage: () => infinite?.fetchNextPage(),
  });
  const view = asyncView(query, rows.length === 0, hasFilters);
  const isRefreshing = view === "content" && query.isFetching && !infinite?.isFetchingNextPage;
  const span = columns.length;

  function messageRow(content: ReactNode) {
    return (
      <TableRow className="hover:bg-transparent">
        <TableCell colSpan={span}>{content}</TableCell>
      </TableRow>
    );
  }

  return (
    <div className="relative">
      {isRefreshing && (
        <div
          role="status"
          aria-label="Refreshing"
          className="absolute inset-x-0 top-0 h-0.5 animate-pulse bg-primary"
        />
      )}
      <Table aria-busy={query.isFetching}>
        <TableCaption className="sr-only">{caption}</TableCaption>
        <TableHeader>
          {table.getHeaderGroups().map((group) => (
            <TableRow key={group.id}>
              {group.headers.map((header) => (
                <TableHead key={header.id} style={{ width: header.getSize() }}>
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody className={cn(isRefreshing && "opacity-70 transition-opacity")}>
          {view === "loading" &&
            Array.from({ length: skeletonRows }, (_, index) => (
              <TableRow key={`skeleton-${index}`}>
                {Array.from({ length: span }, (_, cell) => (
                  <TableCell key={cell}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          {view === "error" && messageRow(<ErrorState error={query.error} onRetry={() => query.refetch()} />)}
          {view === "empty" && messageRow(<EmptyState>{emptyMessage}</EmptyState>)}
          {view === "noResults" && messageRow(<NoResultsState onClearFilters={onClearFilters} />)}
          {view === "content" &&
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                ))}
              </TableRow>
            ))}
          {view === "content" && infinite?.hasNextPage && (
            <TableRow ref={sentinelRef} className="hover:bg-transparent">
              <TableCell colSpan={span} className="text-center">
                {/* Keyboard and assistive-technology users load more explicitly. */}
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={infinite.isFetchingNextPage}
                  onClick={() => infinite.fetchNextPage()}
                >
                  {infinite.isFetchingNextPage ? "Loading…" : "Load more"}
                </Button>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
```

`TableRow` must forward `ref` (it does with React 19 — `ref` is a regular prop).

## 4. Columns — activation through a real button

Opening a row is a `<Button variant="link">` in the primary cell, so it is reachable
with Tab and triggered with Enter. No clickable `<tr>` / `<div>`, no double-click-only
action.

```tsx
// src/components/samples/sample-columns.tsx
import type { ColumnDef } from "@tanstack/react-table";
import { Archive } from "lucide-react";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/format";
import { sampleStatusLabel } from "./samples.rules";

type Handlers = {
  onOpen: (id: string) => void;
  onArchive: (sample: Cr123_samples) => void;
};

export function sampleColumns({ onOpen, onArchive }: Handlers): ColumnDef<Cr123_samples, unknown>[] {
  return [
    {
      id: "name",
      header: "Name",
      cell: ({ row }) => (
        <Button variant="link" className="h-auto p-0" onClick={() => onOpen(row.original.cr123_sampleid)}>
          {row.original.cr123_name}
        </Button>
      ),
    },
    {
      id: "status",
      header: "Status",
      cell: ({ row }) => sampleStatusLabel(row.original.cr123_status),
    },
    {
      id: "modifiedon",
      header: "Modified",
      cell: ({ row }) => formatDate(row.original.modifiedon),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      size: 48,
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Archive ${row.original.cr123_name}`}
          onClick={() => onArchive(row.original)}
        >
          <Archive aria-hidden className="size-4" />
        </Button>
      ),
    },
  ];
}
```

`sampleStatusLabel` comes from `samples.rules.ts` (`ppbp-codeapps-architecture` →
`references/layers.md` §1).

## 5. Pure formatters — once, in `lib/format.ts`

```ts
// src/lib/format.ts
import { format, parseISO } from "date-fns";

export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return "";
  return format(typeof value === "string" ? parseISO(value) : value, "dd/MM/yyyy");
}

export function formatNumber(value: number | null | undefined, fractionDigits = 0): string {
  if (value == null) return "";
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

export function sameCode(a: string | null | undefined, b: string | null | undefined): boolean {
  return (a ?? "").trim().localeCompare((b ?? "").trim(), undefined, { sensitivity: "accent" }) === 0;
}
```

## 6. Inputs — `SearchInput`, `FieldGroup`

```tsx
// src/components/ui/search-input.tsx
import type { ComponentProps } from "react";
import { Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type SearchInputProps = Omit<ComponentProps<typeof Input>, "type" | "value" | "onChange"> & {
  value: string;
  onValueChange: (value: string) => void;
};

export function SearchInput({ value, onValueChange, className, ...props }: SearchInputProps) {
  return (
    <div className={cn("relative", className)}>
      <Search
        aria-hidden
        className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
      />
      <Input
        type="search"
        value={value}
        onChange={(event) => onValueChange(event.target.value)}
        className="pl-8 pr-9"
        {...props}
      />
      {value !== "" && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Clear search"
          className="absolute right-0.5 top-1/2 size-8 -translate-y-1/2"
          onClick={() => onValueChange("")}
        >
          <X aria-hidden className="size-4" />
        </Button>
      )}
    </div>
  );
}
```

```tsx
// src/components/ui/field-group.tsx — label + control (+ hint) for filters and simple fields
import type { ReactNode } from "react";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type FieldGroupProps = {
  label: string;
  htmlFor: string;
  hint?: string;
  className?: string;
  children: ReactNode;
};

export function FieldGroup({ label, htmlFor, hint, className, children }: FieldGroupProps) {
  return (
    <div className={cn("grid gap-1.5", className)}>
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  );
}
```

Forms driven by React Hook Form use the shadcn `form` primitives (`FormField`,
`FormItem`, `FormLabel`, `FormControl`, `FormMessage`), which wire `aria-invalid` and
`aria-describedby` for you.

## 7. Variants instead of repeated classes

When several dialogs repeat the same classes, the classes become a variant — in the
primitive itself (shadcn files are yours to edit) or in one wrapper in `ui/`:

```tsx
// src/components/ui/app-dialog-content.tsx
import type { ComponentProps } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { DialogContent } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

const appDialogContentVariants = cva("", {
  variants: {
    size: { sm: "sm:max-w-sm", md: "sm:max-w-lg", lg: "sm:max-w-3xl" },
    tone: { default: "", flat: "rounded-none border-foreground p-10 shadow-none" },
  },
  defaultVariants: { size: "md", tone: "default" },
});

type AppDialogContentProps = ComponentProps<typeof DialogContent> &
  VariantProps<typeof appDialogContentVariants>;

export function AppDialogContent({ size, tone, className, ...props }: AppDialogContentProps) {
  return <DialogContent className={cn(appDialogContentVariants({ size, tone }), className)} {...props} />;
}
```

## 8. Providers once, at the root

Context providers of primitives (tooltip, toaster, theme) are mounted **once** in
`providers/`. A component that renders its own `TooltipProvider` creates one provider
per instance — hundreds in a table. If the shadcn `Tooltip` you installed wraps itself
in a provider, remove that wrapper and rely on the root one.

```tsx
// src/App.tsx (excerpt)
import { RouterProvider } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryProvider } from "@/providers/query-provider";
import { router } from "@/router";

export default function App() {
  return (
    <QueryProvider>
      <TooltipProvider delayDuration={300}>
        <RouterProvider router={router} />
        <Toaster />
      </TooltipProvider>
    </QueryProvider>
  );
}
```

## Wrong / correct

| Wrong | Correct |
|---|---|
| Loading / error / empty JSX rewritten in every table | `DataTable` / `AsyncState` |
| One "No data" message for both an empty table and a filter with no match | `empty` vs `noResults` (+ "Clear filters") |
| `<p>{error.message}</p>` | `ErrorState` → `userMessageOf(error)` + Retry |
| `IntersectionObserver` copied into each table | `useInfiniteScroll` |
| `<div tabIndex={0} onClick aria-expanded>` row, double-click to edit | `<Button variant="link">` / real `<button>` in the cell, Enter works |
| `role="listbox"` on clickable divs without arrow-key support | Radix / cmdk `Combobox` from `ui/` |
| `TooltipProvider` inside `Hint` / `ClampedText` | One `TooltipProvider` at the root |
| `rounded-none border-black p-10 shadow-none w-[…]` repeated in four dialogs | A `cva` variant (`tone: "flat"`) |
| `fmtDensity`, `sameCode`, folder label rebuilt in several files | `lib/format.ts`, one hook for the label |
