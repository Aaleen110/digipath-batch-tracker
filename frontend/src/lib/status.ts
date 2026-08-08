import type { BatchStatus } from '@/types/batch'

export const STATUS_ORDER: BatchStatus[] = [
  'queued',
  'processing',
  'completed',
  'failed',
]

export const STATUS_META: Record<
  BatchStatus,
  { label: string; dot: string; text: string; bg: string; pulse?: boolean }
> = {
  queued: {
    label: 'Queued',
    dot: 'bg-slate2',
    text: 'text-slate2',
    bg: 'bg-slate2-light',
  },
  processing: {
    label: 'Processing',
    dot: 'bg-amber',
    text: 'text-amber',
    bg: 'bg-amber-light',
    pulse: true,
  },
  completed: {
    label: 'Completed',
    dot: 'bg-leaf',
    text: 'text-leaf',
    bg: 'bg-leaf-light',
  },
  failed: {
    label: 'Failed',
    dot: 'bg-brick',
    text: 'text-brick',
    bg: 'bg-brick-light',
  },
}

export const NEXT_VALID: Record<BatchStatus, BatchStatus[]> = {
  queued: ['processing'],
  processing: ['completed', 'failed'],
  completed: [],
  failed: [],
}

export const NEXT_LABEL: Partial<Record<BatchStatus, string>> = {
  processing: 'Start processing',
  completed: 'Mark completed',
  failed: 'Mark failed',
}

export function formatDate(value?: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
