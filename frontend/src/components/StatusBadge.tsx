import { STATUS_META } from '@/lib/status'
import type { BatchStatus } from '@/types/batch'

interface StatusBadgeProps {
  status: BatchStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const meta = STATUS_META[status] || STATUS_META.queued

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${meta.bg} ${meta.text}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${meta.dot} ${meta.pulse ? 'animate-pulse' : ''}`}
      />
      {meta.label}
    </span>
  )
}
