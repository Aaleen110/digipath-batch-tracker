import { InboxIcon } from '@/components/icons'

interface EmptyStateProps {
  hasActiveFilters: boolean
  onClear: () => void
}

export function EmptyState({ hasActiveFilters, onClear }: EmptyStateProps) {
  return (
    <div className="rounded-xl border border-dashed border-line bg-white/60 py-14 text-center">
      <InboxIcon className="mx-auto h-8 w-8 text-slate2/60" />
      <p className="mt-3 text-sm font-medium text-ink">
        {hasActiveFilters
          ? 'No batches match these filters.'
          : 'No batches yet.'}
      </p>
      <p className="mt-1 text-sm text-slate2">
        {hasActiveFilters
          ? 'Try a different status or batch type.'
          : 'Batches created through the API will show up here.'}
      </p>
      {hasActiveFilters && (
        <button
          type="button"
          onClick={onClear}
          className="focus-ring mt-4 text-sm font-medium text-teal hover:text-teal-dark"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}
