# Layers: a complete feature, from rule to page

One feature (`samples`) shown through every layer. Each file has a single job: the
rule decides, the hook orchestrates, the component renders, the page lays out.

```
src/components/samples/
├── samples.rules.ts          # pure business rules (+ samples.rules.test.ts)
├── samples.queries.ts        # key factory, queryOptions, query & mutation hooks (ppbp-codeapps-data)
├── use-sample-filters.ts     # screen filters from the filters store (references/stores.md)
├── use-sample-actions.ts     # orchestration: mutations + rules + dialogs → stable callbacks
├── sample-columns.tsx        # column definitions for the shared DataTable
├── sample-list.tsx           # presentational: props in, events out
└── archive-sample-dialog.tsx # presentational
src/pages/samples.tsx         # layout only
```

## 1. Rules — pure, typed, tested

No React, no I/O. Everything a reviewer must be able to read as "the business rule"
lives here.

```ts
// src/components/samples/samples.rules.ts
import { Cr123_samplescr123_status } from "@/generated/models/Cr123_samplesModel";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";

export type SampleStatus = Cr123_samplescr123_status;

export const SAMPLE_STATUS = {
  draft: 100000000,
  validated: 100000001,
  archived: 100000002,
} as const satisfies Record<string, SampleStatus>;

export const SAMPLE_STATUS_VALUES = Object.keys(Cr123_samplescr123_status).map(Number) as SampleStatus[];

export const SAMPLE_STATUS_OPTIONS = SAMPLE_STATUS_VALUES.map((value) => ({
  value,
  label: Cr123_samplescr123_status[value],
}));

export function sampleStatusLabel(status: SampleStatus | null | undefined): string {
  return status == null ? "" : Cr123_samplescr123_status[status];
}

export function isSampleStatus(value: number): value is SampleStatus {
  return (SAMPLE_STATUS_VALUES as number[]).includes(value);
}

export type ArchiveDecision =
  | { allowed: true; needsConfirmation: boolean }
  | { allowed: false; reason: string };

// BR-04: a validated sample can be archived only after confirmation; an archived one never again.
export function canArchive(sample: Pick<Cr123_samples, "cr123_status">): ArchiveDecision {
  switch (sample.cr123_status) {
    case SAMPLE_STATUS.archived:
      return { allowed: false, reason: "This sample is already archived." };
    case SAMPLE_STATUS.validated:
      return { allowed: true, needsConfirmation: true };
    default:
      return { allowed: true, needsConfirmation: false };
  }
}
```

```ts
// src/components/samples/samples.rules.test.ts
import { describe, expect, it } from "vitest";
import { canArchive, SAMPLE_STATUS } from "./samples.rules";

describe("canArchive", () => {
  it("asks for confirmation on a validated sample", () => {
    expect(canArchive({ cr123_status: SAMPLE_STATUS.validated })).toEqual({ allowed: true, needsConfirmation: true });
  });

  it("refuses an archived sample", () => {
    expect(canArchive({ cr123_status: SAMPLE_STATUS.archived }).allowed).toBe(false);
  });
});
```

The rule in the client is UX (disable, confirm, explain). When it must hold for every
client, Dataverse enforces it too (plug-in or Custom API) — see `ppbp-codeapps-data`.

## 2. Screen filters — a store hook per screen

Filters, search and tabs survive leaving the screen in the filters store, indexed by
business scope. The screen reads them through `useSampleFilters(scope)` and the filter
bar edits them through a local draft. Both are in
[`stores.md`](stores.md) §5–6; the list below consumes `filters` as a query key.

## 3. Actions hook — orchestration out of the page

Mutations, rules, confirmation state and success side effects are gathered in one
hook that returns stable callbacks. The page no longer knows how an action works.

```ts
// src/components/samples/use-sample-actions.ts
import { useCallback, useState } from "react";
import { toast } from "sonner";
import type { Cr123_samples } from "@/generated/models/Cr123_samplesModel";
import { canArchive, SAMPLE_STATUS } from "./samples.rules";
import { useUpdateSampleStatus } from "./samples.queries";

export function useSampleActions() {
  const { mutate: updateStatus, isPending: isArchiving } = useUpdateSampleStatus();
  const [pendingArchive, setPendingArchive] = useState<Cr123_samples | null>(null);

  const archive = useCallback(
    (id: string) =>
      updateStatus(
        { id, status: SAMPLE_STATUS.archived },
        {
          onSuccess: () => {
            setPendingArchive(null);
            toast.success("Sample archived");
          },
        },
      ),
    [updateStatus],
  );

  const requestArchive = useCallback(
    (sample: Cr123_samples) => {
      const decision = canArchive(sample);
      if (!decision.allowed) {
        toast.info(decision.reason);
        return;
      }
      if (decision.needsConfirmation) setPendingArchive(sample);
      else archive(sample.cr123_sampleid);
    },
    [archive],
  );

  const cancelArchive = useCallback(() => setPendingArchive(null), []);
  const confirmArchive = useCallback(() => {
    if (pendingArchive) archive(pendingArchive.cr123_sampleid);
  }, [archive, pendingArchive]);

  return {
    requestArchive,
    pendingArchive,
    confirmArchive,
    cancelArchive,
    isArchiving,
  };
}
```

(`useUpdateSampleStatus` follows the mutation pattern of `ppbp-codeapps-data` →
`references/tanstack-query.md` §3: `mutationKey`, `meta.errorMessage`, one cache
strategy. TanStack's `mutate` is stable, so it is a safe dependency.)

## 4. Presentational components — props in, events out

No query, no mutation, no service, no rule: they render what they receive and report
what the user did.

```tsx
// src/components/samples/archive-sample-dialog.tsx
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

type Props = {
  sampleName: string | null;
  isPending: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ArchiveSampleDialog({ sampleName, isPending, onConfirm, onCancel }: Props) {
  return (
    <AlertDialog open={sampleName !== null} onOpenChange={(open) => !open && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Archive “{sampleName}”?</AlertDialogTitle>
          <AlertDialogDescription>A validated sample can't be edited once archived.</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction disabled={isPending} onClick={onConfirm}>
            {isPending ? "Archiving…" : "Archive"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

Small *containers* may own one hook for one need — a filter bar reads the filters
store (`SampleFiltersBar`, [`stores.md`](stores.md) §6), a list reads its query. They
still hold no business rule and call no service.

`SampleList` (the shared `DataTable` bound to `useSamples`) is shown in
`ppbp-codeapps-data` → `references/tanstack-query.md` §7; `SearchInput`,
`FieldGroup` and `DataTable` in `ppbp-codeapps-components` → `references/data-table.md`.

## 5. Page — layout only

```tsx
// src/pages/samples.tsx
import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { ErrorZone } from "@/components/ui/error-zone";
import { SampleFiltersBar } from "@/components/samples/sample-filters-bar";
import { SampleList } from "@/components/samples/sample-list";
import { ArchiveSampleDialog } from "@/components/samples/archive-sample-dialog";
import { useSampleActions } from "@/components/samples/use-sample-actions";
import { sampleDetailPath } from "@/lib/routes";

// One filter set per business scope: this list is unscoped; a folder screen passes its folderId.
const SCOPE = "all";

export default function SamplesPage() {
  const navigate = useNavigate();
  const actions = useSampleActions();
  const openSample = useCallback((id: string) => navigate(sampleDetailPath(id)), [navigate]);

  return (
    <main className="space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Samples</h1>
      <SampleFiltersBar scope={SCOPE} />
      <ErrorZone name="samples-list">
        <SampleList scope={SCOPE} onOpen={openSample} onArchive={actions.requestArchive} />
      </ErrorZone>
      <ArchiveSampleDialog
        sampleName={actions.pendingArchive?.cr123_name ?? null}
        isPending={actions.isArchiving}
        onConfirm={actions.confirmArchive}
        onCancel={actions.cancelArchive}
      />
    </main>
  );
}
```

```ts
// src/lib/routes.ts — paths as typed helpers, relative to the router basename
export const ROUTES = {
  samples: "/samples",
  sampleDetail: "/samples/:id",
} as const;

export function sampleDetailPath(id: string): string {
  return `/samples/${encodeURIComponent(id)}`;
}
```

## 6. Enforcing the boundaries with ESLint

Add to the template's flat config (`eslint.config.js`, which already uses
typescript-eslint). The rules turn the layer table of SKILL.md into build errors;
`allowTypeImports` keeps `import type` of generated row types legal in rendering code.

```js
// eslint.layers.js
const NO_SDK_INTERNALS = { group: ["**/.power/*"], message: "Never import Power Apps SDK internals." };
const NO_GENERATED_VALUES = {
  group: ["@/generated/*", "**/generated/*"],
  allowTypeImports: true,
  message: "Rendering code never calls generated code: go through a Query or actions hook.",
};
const NO_SERVICES = { group: ["@/services/*"], message: "Rendering code never calls services: use a Query or actions hook." };

export const layerRules = [
  {
    files: ["src/components/**/*.tsx", "src/pages/**/*.tsx"],
    ignores: ["src/components/ui/**"],
    rules: {
      "@typescript-eslint/no-restricted-imports": [
        "error",
        {
          patterns: [
            NO_SDK_INTERNALS,
            NO_GENERATED_VALUES,
            NO_SERVICES,
            { group: ["@radix-ui/*"], message: "Use the primitives from @/components/ui." },
          ],
        },
      ],
    },
  },
  {
    // Primitives may wrap Radix but never touch data or pages.
    files: ["src/components/ui/**/*.tsx"],
    rules: {
      "@typescript-eslint/no-restricted-imports": [
        "error",
        { patterns: [NO_SDK_INTERNALS, NO_GENERATED_VALUES, NO_SERVICES, { group: ["@/pages/*"], message: "ui/ never imports a page." }] },
      ],
    },
  },
  {
    // Stores hold client state only: no data access.
    files: ["src/stores/**/*.ts"],
    rules: {
      "@typescript-eslint/no-restricted-imports": [
        "error",
        {
          patterns: [
            NO_SDK_INTERNALS,
            NO_GENERATED_VALUES,
            { group: ["@/services/*"], allowTypeImports: true, message: "Stores never call services." },
          ],
        },
      ],
    },
  },
  {
    files: ["src/services/**/*.ts", "src/lib/**/*.ts"],
    rules: {
      "@typescript-eslint/no-restricted-imports": [
        "error",
        { paths: [{ name: "react", message: "services/ and lib/ stay framework-free." }], patterns: [NO_SDK_INTERNALS] },
      ],
    },
  },
];
```

```js
// eslint.config.js — wiring
import { layerRules } from "./eslint.layers.js";

export default [
  // …template config…
  ...layerRules,
];
```

"`ui/` never imports a feature" and "a feature never imports another feature's
internals" are checked in review (`ppbp-codeapps-review`): feature folder names are
app-specific.

## Wrong / correct

| Wrong | Correct |
|---|---|
| Page with 10 mutations, 5 `useState`, confirmation logic and toasts | `use<Feature>Actions` returns callbacks; page lays out |
| `if (rec === "Test" && !checked) setOpen(true)` inside a page | `samples.rules.ts` decision + actions hook |
| `const [search, setSearch] = useState("")` for a list filter, or `?q=` search params | `use<Screen>Filters(scope)` over the filters store |
| `fabricColorsService.listX(...)` called in a page handler | `queryClient.fetchQuery(xOptions(...))` inside an actions hook |
| Feature component importing `@radix-ui/react-dropdown-menu` | `@/components/ui/dropdown-menu` |
| `components/ui/hint.tsx` living in `components/<feature>/` while used by three features | Promoted to `components/ui/` |
