interface PaginationBarProps {
  page: number
  pageSize: number
  total: number
  onPage: (page: number) => void
}

export function PaginationBar({
  page,
  pageSize,
  total,
  onPage,
}: PaginationBarProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(total, page * pageSize)

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-slate2">
        Showing{' '}
        <span className="font-medium text-ink">
          {start}–{end}
        </span>{' '}
        of <span className="font-medium text-ink">{total}</span>
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          className="focus-ring rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-ink transition hover:bg-paper disabled:cursor-not-allowed disabled:opacity-40"
        >
          Previous
        </button>
        <span className="text-sm text-slate2">
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() => onPage(page + 1)}
          className="focus-ring rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-ink transition hover:bg-paper disabled:cursor-not-allowed disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  )
}
