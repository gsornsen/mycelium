# React Modern Patterns

## Overview

Modern React development patterns using TanStack ecosystem (Query, Table, Router, Form), Next.js App Router, and headless UI libraries. This guide covers production-ready implementations of data fetching, state management, routing, forms, and component abstractions.

**Use Cases:**
- Type-safe data fetching and caching
- Complex table implementations with sorting/filtering
- Type-safe routing with loaders and search params
- Form handling with validation
- Server components and server actions (Next.js)
- Headless UI component abstractions

## Prerequisites

### Required Tools
- **React 18+** - Concurrent features, Server Components
- **TypeScript 5+** - Type safety across the stack
- **TanStack Query** - Server state management
- **TanStack Table** - Headless table library
- **TanStack Router** or **Next.js App Router** - Type-safe routing

### Component Library Recommendations

**For New Projects (Headless-First):**
- React Aria (Adobe) - Industrial-strength accessibility
- Ark UI - Framework-agnostic, modern patterns
- Radix UI - Battle-tested primitives
- Floating UI - Positioning engine for tooltips, popovers

**For Quick Prototypes:**
- Mantine v7 - 100+ components, hooks-based
- Shadcn UI - Copy-paste components (Radix + Tailwind)

**Styling:**
- Tailwind CSS - Utility-first standard
- Panda CSS - Zero-runtime, type-safe

## Pattern 1: TanStack Query - Server State Management

**Use Case:** Fetch, cache, and synchronize server state with automatic background updates

**Why TanStack Query?** Eliminates boilerplate; handles caching, deduplication, stale-while-revalidate; optimistic updates.

**Implementation:**

### Basic Query with Auto-Refetch

```typescript
// File: hooks/useVoiceSession.ts

import { useQuery } from '@tanstack/react-query';

interface VoiceSession {
  id: string;
  status: 'idle' | 'active' | 'completed';
  transcript: string[];
  duration: number;
}

export const useVoiceSession = (sessionId: string) => {
  return useQuery({
    queryKey: ['voice-session', sessionId],
    queryFn: async () => {
      const response = await fetch(`/api/sessions/${sessionId}`);
      if (!response.ok) throw new Error('Failed to fetch session');
      return response.json() as Promise<VoiceSession>;
    },
    staleTime: 30_000,  // Consider data fresh for 30 seconds
    gcTime: 5 * 60_000,  // Keep in cache for 5 minutes
    // Auto-refetch every 5 seconds if session is active
    refetchInterval: (query) =>
      query.state.data?.status === 'active' ? 5_000 : false,
  });
};

// Usage in component
function SessionView({ sessionId }: { sessionId: string }) {
  const { data, isLoading, error } = useVoiceSession(sessionId);

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorBanner error={error} />;

  return (
    <div>
      <h1>Session {data.id}</h1>
      <StatusBadge status={data.status} />
      <Transcript lines={data.transcript} />
    </div>
  );
}
```

### Optimistic Updates with Mutations

```typescript
// File: hooks/useUpdateTranscript.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';

export const useUpdateTranscript = (sessionId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (newText: string) => {
      const response = await fetch(`/api/sessions/${sessionId}/transcript`, {
        method: 'POST',
        body: JSON.stringify({ text: newText }),
      });
      if (!response.ok) throw new Error('Failed to update');
      return response.json();
    },
    // Optimistic update: Update UI immediately before server responds
    onMutate: async (newText) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ['voice-session', sessionId],
      });

      // Snapshot previous value
      const previous = queryClient.getQueryData(['voice-session', sessionId]);

      // Optimistically update cache
      queryClient.setQueryData(['voice-session', sessionId], (old: any) => ({
        ...old,
        transcript: [...old.transcript, newText],
      }));

      return { previous };
    },
    // Rollback on error
    onError: (err, newText, context) => {
      queryClient.setQueryData(
        ['voice-session', sessionId],
        context.previous
      );
    },
    // Refetch after mutation settles
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ['voice-session', sessionId],
      });
    },
  });
};
```

### Infinite Queries for Pagination

```typescript
// File: hooks/useTranscriptHistory.ts

import { useInfiniteQuery } from '@tanstack/react-query';

export const useTranscriptHistory = (sessionId: string) => {
  return useInfiniteQuery({
    queryKey: ['transcript-history', sessionId],
    queryFn: async ({ pageParam = 0 }) => {
      const response = await fetch(
        `/api/sessions/${sessionId}/history?cursor=${pageParam}`
      );
      return response.json();
    },
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    initialPageParam: 0,
  });
};

// Usage with infinite scroll
function TranscriptHistory({ sessionId }: { sessionId: string }) {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useTranscriptHistory(sessionId);

  return (
    <div>
      {data?.pages.map((page) =>
        page.items.map((item) => <TranscriptItem key={item.id} {...item} />)
      )}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

**Considerations:**
- Set `staleTime` to reduce refetches (default: 0, always stale)
- Use `gcTime` (formerly `cacheTime`) to keep unused data in memory
- Implement `onMutate` for instant UI feedback (optimistic updates)
- Use query keys as dependencies: `['voice-session', sessionId]`

## Pattern 2: TanStack Table - Headless Tables

**Use Case:** Build complex tables with sorting, filtering, pagination without opinionated UI

**Why TanStack Table?** Headless (full styling control); type-safe; handles complex state management.

**Implementation:**

```typescript
// File: components/TranscriptTable.tsx

import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';

interface Transcript {
  id: string;
  timestamp: number;
  text: string;
  confidence: number;
  speaker: string;
}

const columnHelper = createColumnHelper<Transcript>();

const columns = [
  columnHelper.accessor('timestamp', {
    header: 'Time',
    cell: (info) => formatTimestamp(info.getValue()),
    sortingFn: 'datetime',
  }),
  columnHelper.accessor('speaker', {
    header: 'Speaker',
    cell: (info) => <SpeakerBadge name={info.getValue()} />,
  }),
  columnHelper.accessor('text', {
    header: 'Transcript',
    cell: (info) => (
      <TranscriptCell
        text={info.getValue()}
        confidence={info.row.original.confidence}
      />
    ),
    enableSorting: false,
  }),
  columnHelper.display({
    id: 'actions',
    cell: (props) => (
      <button onClick={() => handleEdit(props.row.original)}>Edit</button>
    ),
  }),
];

export function TranscriptTable({ data }: { data: Transcript[] }) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: { pageSize: 50 },
    },
  });

  return (
    <div>
      <table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {header.isPlaceholder ? null : (
                    <div
                      onClick={header.column.getToggleSortingHandler()}
                      style={{ cursor: header.column.getCanSort() ? 'pointer' : 'default' }}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                      {{ asc: ' ‘', desc: ' “' }[header.column.getIsSorted() as string] ?? null}
                    </div>
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div>
        <button
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Previous
        </button>
        <span>
          Page {table.getState().pagination.pageIndex + 1} of{' '}
          {table.getPageCount()}
        </span>
        <button
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
        </button>
      </div>
    </div>
  );
}
```

**Reusable Table Hook:**

```typescript
// File: hooks/useDataTable.ts

import { useReactTable, getCoreRowModel, ColumnDef } from '@tanstack/react-table';

interface DataTableOptions<TData> {
  data: TData[];
  columns: ColumnDef<TData>[];
  enableSorting?: boolean;
  enableFiltering?: boolean;
  enablePagination?: boolean;
}

export function useDataTable<TData>({
  data,
  columns,
  enableSorting = true,
  enableFiltering = true,
  enablePagination = true,
}: DataTableOptions<TData>) {
  return useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: enableFiltering ? getFilteredRowModel() : undefined,
    getSortedRowModel: enableSorting ? getSortedRowModel() : undefined,
    getPaginationRowModel: enablePagination
      ? getPaginationRowModel()
      : undefined,
  });
}
```

**Considerations:**
- Use `columnHelper` for type-safe column definitions
- Implement custom `sortingFn` for complex data types
- Use `flexRender` to render dynamic cell content
- Extract table logic into reusable hooks

## Pattern 3: Next.js App Router - Server Components & Actions

**Use Case:** Build full-stack React apps with server-side rendering, streaming, and mutations

**Why App Router?** Server Components reduce client bundle; Server Actions simplify mutations; type-safe end-to-end.

**Implementation:**

### Server Component with Data Fetching

```typescript
// File: app/sessions/[id]/page.tsx (Server Component)

import { notFound } from 'next/navigation';

interface Props {
  params: { id: string };
  searchParams: { tab?: string };
}

async function getSession(id: string) {
  const response = await fetch(`http://localhost:3000/api/sessions/${id}`, {
    cache: 'no-store',  // Always fetch fresh data
  });
  if (!response.ok) return null;
  return response.json();
}

export default async function SessionPage({ params, searchParams }: Props) {
  const session = await getSession(params.id);

  if (!session) notFound();

  return (
    <div>
      <h1>{session.name}</h1>
      <SessionTabs tab={searchParams.tab} />
      {/* Client component for interactive UI */}
      <TranscriptView sessionId={session.id} />
    </div>
  );
}
```

### Server Actions for Mutations

```typescript
// File: app/actions/updateSession.ts (Server Action)

'use server';

import { revalidatePath } from 'next/cache';

export async function updateSessionName(sessionId: string, newName: string) {
  // Server-side validation
  if (!newName || newName.length < 3) {
    return { error: 'Name must be at least 3 characters' };
  }

  // Update in database
  await db.session.update({
    where: { id: sessionId },
    data: { name: newName },
  });

  // Revalidate cached pages
  revalidatePath(`/sessions/${sessionId}`);

  return { success: true };
}

// Usage in Client Component
'use client';

import { updateSessionName } from '@/app/actions/updateSession';

export function SessionNameEditor({ sessionId, currentName }: Props) {
  const [name, setName] = useState(currentName);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const result = await updateSessionName(sessionId, name);
    if (result.error) {
      toast.error(result.error);
    } else {
      toast.success('Name updated!');
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <button type="submit">Save</button>
    </form>
  );
}
```

### Streaming with Suspense

```typescript
// File: app/sessions/[id]/page.tsx

import { Suspense } from 'react';

export default function SessionPage({ params }: { params: { id: string } }) {
  return (
    <div>
      <h1>Session {params.id}</h1>

      {/* Transcript loads immediately */}
      <Suspense fallback={<TranscriptSkeleton />}>
        <TranscriptSection sessionId={params.id} />
      </Suspense>

      {/* Metrics loads in background */}
      <Suspense fallback={<MetricsSkeleton />}>
        <MetricsSection sessionId={params.id} />
      </Suspense>
    </div>
  );
}

async function TranscriptSection({ sessionId }: { sessionId: string }) {
  const transcript = await fetchTranscript(sessionId);
  return <Transcript data={transcript} />;
}

async function MetricsSection({ sessionId }: { sessionId: string }) {
  // Slow query - loads in background while transcript shows
  const metrics = await fetchMetrics(sessionId);
  return <MetricsChart data={metrics} />;
}
```

**Considerations:**
- Server Components run only on server (smaller bundle)
- Use `'use client'` directive for interactive components
- Server Actions replace API routes for mutations
- `revalidatePath` / `revalidateTag` for cache invalidation
- Suspense enables streaming and progressive loading

## Pattern 4: Form Handling with TanStack Form

**Use Case:** Type-safe form validation and state management

**Implementation:**

```typescript
// File: components/VoiceSettingsForm.tsx

import { useForm } from '@tanstack/react-form';

interface VoiceSettings {
  vadSensitivity: number;
  asrModel: string;
  ttsVoice: string;
}

export function VoiceSettingsForm({ defaults }: { defaults: VoiceSettings }) {
  const form = useForm({
    defaultValues: defaults,
    onSubmit: async ({ value }) => {
      await updateSettings(value);
      toast.success('Settings saved!');
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        form.handleSubmit();
      }}
    >
      <form.Field
        name="vadSensitivity"
        validators={{
          onChange: ({ value }) =>
            value < 0 || value > 3
              ? 'VAD sensitivity must be between 0 and 3'
              : undefined,
        }}
      >
        {(field) => (
          <div>
            <label htmlFor={field.name}>VAD Sensitivity</label>
            <input
              id={field.name}
              type="number"
              value={field.state.value}
              onChange={(e) => field.handleChange(Number(e.target.value))}
            />
            {field.state.meta.errors && (
              <span className="error">{field.state.meta.errors[0]}</span>
            )}
          </div>
        )}
      </form.Field>

      <form.Field name="asrModel">
        {(field) => (
          <div>
            <label htmlFor={field.name}>ASR Model</label>
            <select
              id={field.name}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
            >
              <option value="whisper-small">Whisper Small</option>
              <option value="whisper-base">Whisper Base</option>
            </select>
          </div>
        )}
      </form.Field>

      <button type="submit">Save Settings</button>
    </form>
  );
}
```

**Considerations:**
- Use `validators.onChange` for real-time validation
- Access field state via render props
- `form.handleSubmit()` runs all validators before submission

## Pattern 5: Headless UI Abstractions with React Aria

**Use Case:** Build accessible, unstyled components with full control over styling

**Why React Aria?** Industry-standard accessibility; keyboard navigation; ARIA attributes; mobile support.

**Implementation:**

### Custom Button Component

```typescript
// File: components/ui/Button.tsx

import { useButton } from 'react-aria';
import { useRef } from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onPress?: () => void;
  variant?: 'primary' | 'secondary';
  isDisabled?: boolean;
}

export function Button({ children, onPress, variant = 'primary', isDisabled }: ButtonProps) {
  const ref = useRef(null);
  const { buttonProps } = useButton({ onPress, isDisabled }, ref);

  return (
    <button
      {...buttonProps}
      ref={ref}
      className={`btn btn-${variant}`}
      disabled={isDisabled}
    >
      {children}
    </button>
  );
}
```

### Custom Select Component

```typescript
// File: components/ui/Select.tsx

import { useSelect } from 'react-aria';
import { useSelectState } from 'react-stately';

export function Select({ label, items }: SelectProps) {
  const state = useSelectState({ label, items });
  const ref = useRef(null);
  const { labelProps, triggerProps, menuProps } = useSelect({ label }, state, ref);

  return (
    <div>
      <label {...labelProps}>{label}</label>
      <button {...triggerProps} ref={ref}>
        {state.selectedItem?.rendered || 'Select...'}
      </button>
      {state.isOpen && (
        <ul {...menuProps}>
          {[...state.collection].map((item) => (
            <li key={item.key}>{item.rendered}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

**Considerations:**
- React Aria handles ARIA attributes, keyboard nav, focus management
- Use `react-stately` for state management
- Full styling control via className or CSS-in-JS

## Best Practices

1. **Use TanStack Query for server state** - Eliminates boilerplate, handles caching automatically
2. **Implement optimistic updates** - Instant UI feedback on mutations
3. **Server Components by default (Next.js)** - Use `'use client'` only when needed
4. **Headless UI for accessibility** - React Aria, Radix, or Ark UI for a11y compliance
5. **Type-safe routing** - TanStack Router or Next.js App Router with TypeScript
6. **Streaming with Suspense** - Progressive loading for better UX
7. **Server Actions for mutations** - Simplifies data updates in Next.js
8. **Extract reusable hooks** - `useDataTable`, `useVoiceSession` for DRY code

## Related Agents

- **react-tanstack-developer** (`plugins/mycelium-core/agents/02-language-react-tanstack-developer.md`) - TanStack ecosystem specialist
- **nextjs-developer** (`plugins/mycelium-core/agents/02-language-nextjs-developer.md`) - Next.js App Router expert
- **frontend-developer** - General React patterns and component architecture
- **typescript-pro** - Type-safe patterns across the stack

## References

- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [TanStack Table Documentation](https://tanstack.com/table/latest)
- [TanStack Router Documentation](https://tanstack.com/router/latest)
- [Next.js App Router](https://nextjs.org/docs/app)
- [React Aria Documentation](https://react-spectrum.adobe.com/react-aria/)
- [Radix UI Primitives](https://www.radix-ui.com/)
