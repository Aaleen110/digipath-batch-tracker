import { BellIcon, Spinner } from '@/components/icons'
import type { Batch } from '@/types/batch'

interface NotifyButtonProps {
  batch: Batch
  pending: boolean
  onNotify: (batch: Batch) => void
}

export function NotifyButton({ batch, pending, onNotify }: NotifyButtonProps) {
  return (
    <button
      type="button"
      disabled={pending}
      onClick={() => onNotify(batch)}
      className="focus-ring inline-flex cursor-pointer items-center gap-1.5 rounded-full border border-line px-2.5 py-1 text-xs font-medium text-ink transition hover:border-teal/40 hover:bg-teal-light disabled:cursor-not-allowed disabled:opacity-50"
    >
      {pending ? <Spinner /> : <BellIcon className="h-3.5 w-3.5" />}
      Notify partner
    </button>
  )
}
