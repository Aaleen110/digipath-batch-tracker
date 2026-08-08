import { useState } from 'react'

import { BatchDetailModal } from '@/components/BatchDetailModal'
import { NotifyButton } from '@/components/NotifyButton'
import { StatusActions } from '@/components/StatusActions'
import { StatusBadge } from '@/components/StatusBadge'
import { formatDate, STATUS_META } from '@/lib/status'
import type { Batch, BatchStatus } from '@/types/batch'

interface BatchCardProps {
  batch: Batch
  pending: boolean
  notifying: boolean
  onStatusChange: (batch: Batch, status: BatchStatus) => void
  onNotify: (batch: Batch) => void
}

export function BatchCard({
  batch,
  pending,
  notifying,
  onStatusChange,
  onNotify,
}: BatchCardProps) {
  const [detailOpen, setDetailOpen] = useState(false)
  const meta = STATUS_META[batch.status] || STATUS_META.queued

  return (
    <>
      <article className="relative overflow-hidden rounded-2xl border border-line bg-white shadow-card transition-shadow duration-200 hover:shadow-liftedcard">
        <div className={`absolute inset-y-0 left-0 w-1 ${meta.dot}`} />

        <div className="p-5 pl-6 sm:p-6 sm:pl-7">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2.5">
                <h3 className="font-display text-lg font-semibold tracking-tight text-ink">
                  {batch.sample_id || `Batch ${batch.id}`}
                </h3>
                <StatusBadge status={batch.status} />
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-slate2">
                <span className="rounded-md bg-teal-light px-2 py-0.5 text-xs font-medium text-teal">
                  {batch.batch_type}
                </span>
                <span aria-hidden="true">·</span>
                <span>{batch.submitted_by}</span>
                <span aria-hidden="true">·</span>
                <span>Updated {formatDate(batch.updated_at || batch.created_at)}</span>
              </div>
            </div>

            <div className="flex shrink-0 flex-wrap items-center gap-2 sm:justify-end">
              <StatusActions
                batch={batch}
                pending={pending}
                onChange={onStatusChange}
              />
              <NotifyButton
                batch={batch}
                pending={notifying}
                onNotify={onNotify}
              />
              <button
                type="button"
                onClick={() => setDetailOpen(true)}
                className="focus-ring inline-flex cursor-pointer items-center rounded-full border border-line px-2.5 py-1 text-xs font-medium text-ink transition hover:border-teal/40 hover:bg-teal-light"
              >
                View details
              </button>
            </div>
          </div>
        </div>
      </article>

      <BatchDetailModal
        batchId={detailOpen ? batch.id : null}
        onClose={() => setDetailOpen(false)}
      />
    </>
  )
}
