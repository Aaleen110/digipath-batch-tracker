import { STATUS_META, STATUS_ORDER } from '@/lib/status'

interface FiltersBarProps {
  statusFilter: string
  setStatusFilter: (value: string) => void
  typeInput: string
  setTypeInput: (value: string) => void
  pageSize: number
  setPageSize: (value: number) => void
  onClear: () => void
  hasActiveFilters: boolean
}

export function FiltersBar({
  statusFilter,
  setStatusFilter,
  typeInput,
  setTypeInput,
  pageSize,
  setPageSize,
  onClear,
  hasActiveFilters,
}: FiltersBarProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-line bg-white p-4 sm:flex-row sm:items-end sm:gap-4">
      <div className="min-w-[140px] flex-1">
        <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate2">
          Status
        </label>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="focus-ring w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink"
        >
          <option value="">All statuses</option>
          {STATUS_ORDER.map((status) => (
            <option key={status} value={status}>
              {STATUS_META[status].label}
            </option>
          ))}
        </select>
      </div>
      <div className="min-w-[160px] flex-1">
        <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate2">
          Batch type
        </label>
        <input
          value={typeInput}
          onChange={(e) => setTypeInput(e.target.value)}
          placeholder="e.g. Blood Panel"
          className="focus-ring w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink placeholder:text-slate2/70"
        />
      </div>
      <div className="w-full sm:w-32">
        <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate2">
          Per page
        </label>
        <select
          value={pageSize}
          onChange={(e) => setPageSize(Number(e.target.value))}
          className="focus-ring w-full rounded-lg border border-line bg-paper px-3 py-2 text-sm text-ink"
        >
          {[10, 20, 50].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>
      {hasActiveFilters && (
        <button
          type="button"
          onClick={onClear}
          className="focus-ring self-start text-sm font-medium text-teal hover:text-teal-dark sm:mb-2.5 sm:self-auto"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}
