import { useCallback, useEffect, useRef, useState } from 'react'

import {
  createBatch,
  listBatches,
  normalizeList,
  notifyBatch,
  updateBatchStatus,
} from '@/api/client'
import { BatchCard } from '@/components/BatchCard'
import { CreateBatchModal } from '@/components/CreateBatchModal'
import { EmptyState } from '@/components/EmptyState'
import { ErrorBanner } from '@/components/ErrorBanner'
import { FiltersBar } from '@/components/FiltersBar'
import { Header } from '@/components/Header'
import { PaginationBar } from '@/components/PaginationBar'
import { SkeletonList } from '@/components/SkeletonList'
import { ToastStack } from '@/components/ToastStack'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useToasts } from '@/hooks/useToasts'
import { STATUS_META } from '@/lib/status'
import { ApiError, type Batch, type BatchStatus, type CreateBatchRequest } from '@/types/batch'

export default function App() {
  const firstConnectDone = useRef(false)

  const [statusFilter, setStatusFilter] = useState('')
  const [typeInput, setTypeInput] = useState('')
  const debouncedType = useDebouncedValue(typeInput, 350)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [reloadTick, setReloadTick] = useState(0)

  const [batches, setBatches] = useState<Batch[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const [pendingIds, setPendingIds] = useState(() => new Set<number>())
  const [notifyingIds, setNotifyingIds] = useState(() => new Set<number>())
  const [createOpen, setCreateOpen] = useState(false)

  const { toasts, push: pushToast, dismiss: dismissToast } = useToasts()

  useEffect(() => {
    setPage(1)
  }, [statusFilter, debouncedType, pageSize])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

      ; (async () => {
        try {
          const json = await listBatches({
            status: statusFilter,
            type: debouncedType,
            page,
            page_size: pageSize,
          })
          if (cancelled) return
          const { items, total: nextTotal } = normalizeList(json)
          setBatches(items)
          setTotal(nextTotal)
          firstConnectDone.current = true
        } catch (err) {
          if (cancelled) return
          setError(err instanceof ApiError ? err : new ApiError(String(err), 'api'))
          setBatches([])
          setTotal(0)
        } finally {
          if (!cancelled) setLoading(false)
        }
      })()

    return () => {
      cancelled = true
    }
  }, [statusFilter, debouncedType, page, pageSize, reloadTick])

  const handleStatusChange = useCallback(
    async (batch: Batch, newStatus: BatchStatus) => {
      setPendingIds((prev) => new Set(prev).add(batch.id))
      const prevStatus = batch.status
      setBatches((list) =>
        list.map((b) => (b.id === batch.id ? { ...b, status: newStatus } : b)),
      )

      try {
        const updated = await updateBatchStatus(batch.id, newStatus)
        setBatches((list) =>
          list.map((b) => {
            if (b.id !== batch.id) return b
            return {
              ...b,
              ...(updated ?? {}),
              status: updated?.status || newStatus,
            }
          }),
        )
        pushToast(
          'success',
          `${batch.sample_id || `Batch ${batch.id}`} moved to ${STATUS_META[newStatus].label}.`,
        )
      } catch (err) {
        setBatches((list) =>
          list.map((b) =>
            b.id === batch.id ? { ...b, status: prevStatus } : b,
          ),
        )
        pushToast(
          'error',
          err instanceof Error
            ? err.message
            : `Could not update ${batch.sample_id || `batch ${batch.id}`}.`,
        )
      } finally {
        setPendingIds((prev) => {
          const next = new Set(prev)
          next.delete(batch.id)
          return next
        })
      }
    },
    [pushToast],
  )

  const handleNotify = useCallback(
    async (batch: Batch) => {
      setNotifyingIds((prev) => new Set(prev).add(batch.id))
      try {
        await notifyBatch(batch.id)
        pushToast(
          'success',
          `Partner notified for ${batch.sample_id || `batch ${batch.id}`}.`,
        )
      } catch (err) {
        pushToast(
          'error',
          err instanceof Error
            ? err.message
            : `Notify failed for ${batch.sample_id || `batch ${batch.id}`}.`,
        )
      } finally {
        setNotifyingIds((prev) => {
          const next = new Set(prev)
          next.delete(batch.id)
          return next
        })
      }
    },
    [pushToast],
  )

  const handleCreateBatch = useCallback(
    async (payload: CreateBatchRequest, idempotencyKey: string) => {
      try {
        const created = await createBatch(payload, idempotencyKey)
        pushToast(
          'success',
          `Created ${created.sample_id || `batch ${created.id}`}.`,
        )
        setPage(1)
        setReloadTick((tick) => tick + 1)
      } catch (err) {
        pushToast(
          'error',
          err instanceof Error ? err.message : 'Could not create batch.',
        )
        throw err
      }
    },
    [pushToast],
  )

  const hasActiveFilters = !!statusFilter || !!typeInput.trim()
  const clearFilters = () => {
    setStatusFilter('')
    setTypeInput('')
  }

  const connTone: 'ok' | 'warn' | 'bad' | 'idle' =
    error?.kind === 'network'
      ? 'bad'
      : error?.kind === 'auth' || error?.kind === 'config'
        ? 'warn'
        : firstConnectDone.current && !error
          ? 'ok'
          : 'idle'

  const connLabel =
    error?.kind === 'network'
      ? 'Offline'
      : error?.kind === 'auth' || error?.kind === 'config'
        ? 'Auth error'
        : firstConnectDone.current && !error
          ? 'Connected'
          : 'Connecting…'

  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <Header
        status={{ tone: connTone, label: connLabel }}
        onRefresh={() => setReloadTick((tick) => tick + 1)}
        onCreateClick={() => setCreateOpen(true)}
      />

      <CreateBatchModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSubmit={handleCreateBatch}
      />

      <main className="mx-auto w-full max-w-6xl flex-1 space-y-5 px-4 py-6 sm:px-6 sm:py-8">
        <FiltersBar
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          typeInput={typeInput}
          setTypeInput={setTypeInput}
          pageSize={pageSize}
          setPageSize={setPageSize}
          onClear={clearFilters}
          hasActiveFilters={hasActiveFilters}
        />

        {error && (
          <ErrorBanner
            error={error}
            onRetry={() => setReloadTick((tick) => tick + 1)}
          />
        )}

        {loading && !error && <SkeletonList />}

        {!loading && !error && batches.length === 0 && (
          <EmptyState
            hasActiveFilters={hasActiveFilters}
            onClear={clearFilters}
          />
        )}

        {!loading && !error && batches.length > 0 && (
          <>
            <div className="grid grid-cols-1 gap-3">
              {batches.map((batch) => (
                <BatchCard
                  key={batch.id}
                  batch={batch}
                  pending={pendingIds.has(batch.id)}
                  notifying={notifyingIds.has(batch.id)}
                  onStatusChange={handleStatusChange}
                  onNotify={handleNotify}
                />
              ))}
            </div>
            <PaginationBar
              page={page}
              pageSize={pageSize}
              total={total}
              onPage={setPage}
            />
          </>
        )}
      </main>

      <ToastStack toasts={toasts} onDismiss={dismissToast} />
      <footer className="py-6 text-center text-xs text-slate2">
        Batch Tracker · Diagnostic sample pipeline console
      </footer>
    </div>
  )
}
