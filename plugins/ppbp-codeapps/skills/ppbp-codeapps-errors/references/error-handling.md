# Error handling: the complete pattern

One error model, one normaliser, one result module, one logging sink, and global
channels in the `QueryClient`. Every file below is complete. The names
(`lib/errors.ts`, `services/dataverse-result.ts`, `providers/query-client.ts`) are
the team convention; keep them so every app reads the same.

Flow:

```
generated service / connector ──► services/dataverse-result.ts (run, unwrap…)
                                     │ throws AppError (classified once)
                                     ▼
            TanStack Query ── QueryCache / MutationCache onError (toast + report, once)
                                     │
                                     ▼
     component ── AsyncState (first load, inline) · form setError (field) · boundary (render bug)
```

---

## 1. `lib/errors.ts`: the error model and the normaliser

Pure module, no SDK import, so components may import it.

```ts
// src/lib/errors.ts
export type AppErrorKind =
  | "network"
  | "throttled"
  | "forbidden"
  | "notFound"
  | "duplicate"
  | "conflict"
  | "business"
  | "unknown";

const USER_MESSAGES: Record<AppErrorKind, string> = {
  network: "The server could not be reached. Check your connection and try again.",
  throttled: "The server is busy. Try again in a moment.",
  forbidden: "You don't have permission to do this.",
  notFound: "This item no longer exists.",
  duplicate: "An item with the same values already exists.",
  conflict: "Someone else changed this item. Reload it and try again.",
  business: "The operation was rejected.",
  unknown: "Something went wrong. Try again, or contact support if it persists.",
};

// Dataverse error codes (learn.microsoft.com → "Web service error codes").
const CODE_KINDS: Record<string, AppErrorKind> = {
  "0x80040237": "duplicate", // DuplicateRecord
  "0x80060892": "duplicate", // DuplicateRecordEntityKey (alternate key)
  "0x80040333": "duplicate", // DuplicateRecordsFound (duplicate detection rule)
  "0x80040217": "notFound", // ObjectDoesNotExist
  "0x80040220": "forbidden", // PrivilegeDenied
  "0x80060882": "conflict", // ConcurrencyVersionMismatch
  "0x80040265": "business", // IsvAborted: InvalidPluginExecutionException from a plug-in / Custom API
};

const STATUS_KINDS: Record<number, AppErrorKind> = {
  401: "forbidden",
  403: "forbidden",
  404: "notFound",
  409: "conflict",
  412: "conflict",
  429: "throttled",
};

type AppErrorOptions = {
  message: string;
  code?: string;
  status?: number;
  serverMessage?: string;
  cause?: unknown;
};

export class AppError extends Error {
  readonly kind: AppErrorKind;
  readonly code?: string;
  readonly status?: number;
  readonly userMessage: string;

  constructor(kind: AppErrorKind, options: AppErrorOptions) {
    super(options.message, { cause: options.cause });
    this.name = "AppError";
    this.kind = kind;
    this.code = options.code;
    this.status = options.status;
    // A plug-in / Custom API message is written for users; every other server text is technical.
    this.userMessage =
      kind === "business" && options.serverMessage ? options.serverMessage : USER_MESSAGES[kind];
  }

  get retryable(): boolean {
    return this.kind === "network" || this.kind === "throttled";
  }
}

function textOf(error: unknown): string {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (typeof error === "object" && error !== null && "message" in error) {
    return String((error as { message: unknown }).message);
  }
  try {
    return JSON.stringify(error) ?? "Unknown error";
  } catch {
    return "Unknown error";
  }
}

function statusOf(error: unknown): number | undefined {
  if (typeof error === "object" && error !== null && "status" in error) {
    const status = Number((error as { status: unknown }).status);
    return Number.isFinite(status) ? status : undefined;
  }
  return undefined;
}

// The SDK and the connector surface the Dataverse code inside the message text, in hex
// ("0x80040237") or decimal ("-2147220937"). Extract the code — never match words.
function dataverseCode(text: string): string | undefined {
  const hex = /0x[0-9a-f]{8}/i.exec(text);
  if (hex) return hex[0].toLowerCase();
  const decimal = /-21\d{8}/.exec(text);
  if (decimal) return `0x${(Number(decimal[0]) >>> 0).toString(16).padStart(8, "0")}`;
  return undefined;
}

// Connector errors carry a JSON body inside the message: {"error":{"message"}} or {"Message"}.
function serverMessageOf(text: string): string | undefined {
  const start = text.indexOf("{");
  if (start < 0) return undefined;
  try {
    const body = JSON.parse(text.slice(start)) as {
      error?: { message?: string };
      Message?: string;
      message?: string;
    };
    return body.error?.message ?? body.Message ?? body.message;
  } catch {
    return undefined;
  }
}

export function toAppError(error: unknown): AppError {
  if (error instanceof AppError) return error;
  const text = textOf(error);
  const status = statusOf(error);
  const code = dataverseCode(text);
  const serverMessage = serverMessageOf(text);
  const kind: AppErrorKind =
    (code ? CODE_KINDS[code] : undefined) ??
    (status !== undefined ? STATUS_KINDS[status] : undefined) ??
    (error instanceof TypeError && status === undefined ? "network" : "unknown");
  return new AppError(kind, { message: serverMessage ?? text, code, status, serverMessage, cause: error });
}

export function userMessageOf(error: unknown): string {
  return toAppError(error).userMessage;
}
```

## 2. `lib/report-error.ts`: the only place that logs

```ts
// src/lib/report-error.ts
import type { AppError } from "./errors";

export type ErrorContext = Record<string, unknown>;
export type ErrorSink = (error: AppError, context: ErrorContext) => void;

const consoleSink: ErrorSink = (error, context) => {
  console.error(`[${error.kind}] ${error.message}`, {
    ...context,
    code: error.code,
    status: error.status,
    cause: error.cause,
  });
};

let sink: ErrorSink = consoleSink;

// Wire the app's telemetry once at start-up (e.g. in main.tsx); every report goes through here.
export function setErrorSink(next: ErrorSink): void {
  sink = next;
}

export function reportError(error: AppError, context: ErrorContext = {}): void {
  sink(error, context);
}
```

No other file calls `console.error`.

## 3. `services/dataverse-result.ts`: the only place that reads an `IOperationResult`

```ts
// src/services/dataverse-result.ts
import type { IOperationResult } from "@microsoft/power-apps/data";
import { toAppError } from "@/lib/errors";

export type Page<T> = { items: T[]; skipToken?: string; count?: number };

export function unwrap<T>(result: IOperationResult<T>): T {
  if (!result.success) throw toAppError(result.error ?? "Dataverse operation failed");
  return result.data;
}

export function unwrapPage<T>(result: IOperationResult<T[]>): Page<T> {
  return {
    items: unwrap(result) ?? [],
    skipToken: result.skipToken ?? undefined,
    count: result.count ?? undefined,
  };
}

// Runs one SDK or connector call. Covers both failure styles: a returned
// { success: false } and a thrown error. Some generated methods return void.
export async function run<T>(operation: () => Promise<IOperationResult<T>>): Promise<T>;
export async function run(operation: () => Promise<void>): Promise<void>;
export async function run<T>(operation: () => Promise<IOperationResult<T> | void>): Promise<T | void> {
  let result: IOperationResult<T> | void;
  try {
    result = await operation();
  } catch (error) {
    throw toAppError(error);
  }
  return result ? unwrap(result) : undefined;
}

export async function runPage<T>(operation: () => Promise<IOperationResult<T[]>>): Promise<Page<T>> {
  let result: IOperationResult<T[]>;
  try {
    result = await operation();
  } catch (error) {
    throw toAppError(error);
  }
  return unwrapPage(result);
}

// null means "does not exist" — and nothing else. Every other failure propagates.
export async function runOrNull<T>(operation: () => Promise<IOperationResult<T>>): Promise<T | null> {
  try {
    return await run(operation);
  } catch (error) {
    if (toAppError(error).kind === "notFound") return null;
    throw error;
  }
}
```

Services use it like this:

```ts
// src/services/samples.service.ts (excerpt)
import { Cr123_samplesService } from "@/generated/services/Cr123_samplesService";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";
import { run, runOrNull } from "./dataverse-result";

const DETAIL_COLUMNS = ["cr123_sampleid", "cr123_name", "cr123_status", "modifiedon"];

export const samplesService = {
  get: (id: string): Promise<Cr123_samples | null> =>
    runOrNull(() => Cr123_samplesService.get(id, { select: DETAIL_COLUMNS })),
  remove: (id: string): Promise<void> => run(() => Cr123_samplesService.delete(id)),
};
```

## 4. `providers/query-client.ts`: the global channels

```ts
// src/providers/query-client.ts
import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { toAppError } from "@/lib/errors";
import { reportError } from "@/lib/report-error";

declare module "@tanstack/react-query" {
  interface Register {
    queryMeta: {
      /** User-facing text for a failed background refresh of this query. */
      errorMessage?: string;
      /** Infinite list: keep only page 1 once nobody observes it (see ppbp-codeapps-data). */
      firstPageOnly?: boolean;
    };
    mutationMeta: {
      /** User-facing text replacing the default message for this mutation's kind. */
      errorMessage?: string;
      /** The caller renders the error itself (form field, dialog): no toast. Still reported. */
      silent?: boolean;
    };
  }
}

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      const appError = toAppError(error);
      reportError(appError, { queryKey: query.queryKey });
      // First load: the component shows the error inline (AsyncState). Toast only when
      // data is already on screen and a background refresh failed.
      if (query.state.data !== undefined) {
        toast.error(query.meta?.errorMessage ?? appError.userMessage);
      }
    },
  }),
  mutationCache: new MutationCache({
    onError: (error, _variables, _context, mutation) => {
      const appError = toAppError(error);
      reportError(appError, { mutationKey: mutation.options.mutationKey });
      if (mutation.meta?.silent) return;
      toast.error(mutation.meta?.errorMessage ?? appError.userMessage);
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => toAppError(error).retryable && failureCount < 2,
    },
    mutations: {
      retry: false,
    },
  },
});
```

Mutation hooks then contain no error code at all:

```ts
export function useDeleteSample() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: sampleKeys.mutations.delete(),
    mutationFn: (id: string) => samplesService.remove(id),
    meta: { errorMessage: "The sample could not be deleted." },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sampleKeys.lists() }),
  });
}
```

## 5. Route and zone boundaries

```tsx
// src/components/ui/route-error.tsx — errorElement of every route / layout
import { useEffect } from "react";
import { useRouteError } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { toAppError } from "@/lib/errors";
import { reportError } from "@/lib/report-error";

export function RouteError() {
  const error = useRouteError();
  const appError = toAppError(error);

  useEffect(() => {
    reportError(toAppError(error), { boundary: "route" });
  }, [error]);

  return (
    <div role="alert" className="mx-auto max-w-md space-y-4 p-8 text-center">
      <p>{appError.userMessage}</p>
      <Button onClick={() => window.location.reload()}>Reload</Button>
    </div>
  );
}
```

```tsx
// src/components/ui/error-zone.tsx — wraps an independent area (widget, panel, Suspense zone)
import type { ReactNode } from "react";
import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { ErrorBoundary } from "react-error-boundary";
import { Button } from "@/components/ui/button";
import { toAppError } from "@/lib/errors";
import { reportError } from "@/lib/report-error";

export function ErrorZone({ children, name }: { children: ReactNode; name: string }) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary
          onReset={reset}
          onError={(error) => reportError(toAppError(error), { boundary: name })}
          fallbackRender={({ error, resetErrorBoundary }) => (
            <div role="alert" className="space-y-2 p-4">
              <p>{toAppError(error).userMessage}</p>
              <Button variant="outline" onClick={resetErrorBoundary}>
                Retry
              </Button>
            </div>
          )}
        >
          {children}
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}
```

Register the route boundary on every route that renders a layout or a page:

```tsx
// src/router.tsx (excerpt — the template's basename block stays above)
import { createBrowserRouter } from "react-router-dom";
import { RouteError } from "@/components/ui/route-error";

export const router = createBrowserRouter(
  [
    {
      path: "/",
      lazy: async () => ({ Component: (await import("@/pages/_layout")).default }),
      errorElement: <RouteError />,
      children: [
        { index: true, lazy: async () => ({ Component: (await import("@/pages/home")).default }) },
      ],
    },
  ],
  { basename: BASENAME },
);
```

## 6. Server errors mapped to form fields

A mutation whose error belongs to a field is `silent`, and the form maps the kind:

```tsx
// src/components/samples/use-sample-form.ts
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toAppError } from "@/lib/errors";
import { useCreateSample } from "./samples.queries";

export const sampleFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(100),
  code: z.string().trim().min(1, "Code is required"),
});
export type SampleFormValues = z.infer<typeof sampleFormSchema>;

export function useSampleForm(onCreated: (id: string) => void) {
  const form = useForm<SampleFormValues>({
    resolver: zodResolver(sampleFormSchema),
    defaultValues: { name: "", code: "" },
  });
  const createSample = useCreateSample({ silent: true });

  const submit = form.handleSubmit((values) =>
    createSample.mutate(values, {
      onSuccess: (created) => onCreated(created.cr123_sampleid),
      onError: (error) => {
        const appError = toAppError(error);
        if (appError.kind === "duplicate") {
          form.setError("code", { message: "This code is already used." });
        } else {
          form.setError("root.server", { message: appError.userMessage });
        }
      },
    }),
  );

  return { form, submit, isSubmitting: createSample.isPending };
}
```

```ts
// in samples.queries.ts
export function useCreateSample(options: { silent?: boolean } = {}) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationKey: sampleKeys.mutations.create(),
    mutationFn: (input: SampleInput) => samplesService.create(input),
    meta: { silent: options.silent },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sampleKeys.lists() }),
  });
}
```

## 7. Tests for the normaliser

```ts
// src/lib/errors.test.ts
import { describe, expect, it } from "vitest";
import { AppError, toAppError } from "./errors";

describe("toAppError", () => {
  it("classifies an alternate-key violation by code", () => {
    const error = toAppError(new Error('Failed to create: {"error":{"code":"0x80060892","message":"Entity Key violated"}}'));
    expect(error.kind).toBe("duplicate");
    expect(error.code).toBe("0x80060892");
  });

  it("converts decimal codes", () => {
    expect(toAppError("Error -2147220969 occurred").kind).toBe("notFound");
  });

  it("keeps the plug-in message for business errors", () => {
    const error = toAppError({ message: '{"error":{"code":"0x80040265","message":"Quantity must be positive"}}', status: 400 });
    expect(error.kind).toBe("business");
    expect(error.userMessage).toBe("Quantity must be positive");
  });

  it("never shows technical text for other kinds", () => {
    const error = toAppError({ message: "SQL timeout on table cr123_sample", status: 500 });
    expect(error.kind).toBe("unknown");
    expect(error.userMessage).not.toContain("SQL");
  });

  it("is idempotent", () => {
    const first = toAppError({ message: "x", status: 429 });
    expect(toAppError(first)).toBe(first);
    expect(first).toBeInstanceOf(AppError);
    expect(first.retryable).toBe(true);
  });
});
```

## Wrong / correct

| Wrong | Correct |
|---|---|
| `catch { return null }` in a service | `runOrNull(...)` — `null` only for `notFound` |
| `toError` / `unwrap` copied in every service | `services/dataverse-result.ts`, imported everywhere |
| `/already\|in progress\|duplicate/i.test(message)` | `toAppError(error).kind === "duplicate"` (code-based) |
| `onError: (e) => toast.error(errorMessage(e))` in each mutation | `MutationCache.onError` + `meta.errorMessage` / `meta.silent` |
| `<p>{error.message}</p>` in a table | `AsyncState` → `userMessageOf(error)` |
| A generic text replacing the cause everywhere | Generic **user** text, real cause sent to `reportError` |
| `console.error` in components | `reportError` (one sink, swappable) |
| Only route `errorElement`s | Route `errorElement` + `ErrorZone` around independent areas |
