import { Spinner } from '@/components/icons'
import { NEXT_LABEL, NEXT_VALID } from '@/lib/status'
import type { Batch, BatchStatus } from '@/types/batch'

interface StatusActionsProps {
  batch: Batch
  pending: boolean
  onChange: (batch: Batch, status: BatchStatus) => void
}

const ACTION_STYLE: Record<BatchStatus, string> = {
  queued: 'bg-amber-500 text-white hover:bg-amber-600',
  processing: 'bg-amber-500 text-white hover:bg-amber-600',
  completed: 'bg-emerald-600 text-white hover:bg-emerald-700',
  failed: 'border border-rose-200 bg-white text-rose-600 hover:bg-rose-50', // see note below
}

export function StatusActions({ batch, pending, onChange }: StatusActionsProps) {
  const next = NEXT_VALID[batch.status] || []
  if (next.length === 0) return null

  return (
    <div className="flex flex-wrap items-center justify-end gap-1.5">
      {next.map((status) => (
        <button
          key={status}
          type="button"
          disabled={pending}
          onClick={() => onChange(batch, status)}
          className={`focus-ring inline-flex cursor-pointer items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold shadow-sm transition disabled:cursor-not-allowed disabled:opacity-50 ${ACTION_STYLE[status]}`}
        >
          {pending && <Spinner className="h-3 w-3" />}
          {NEXT_LABEL[status]}
        </button>
      ))}
    </div>
  )
}