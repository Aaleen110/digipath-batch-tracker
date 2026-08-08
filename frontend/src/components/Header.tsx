import { RefreshIcon, SampleVialIcon } from '@/components/icons'

interface HeaderProps {
  status: { tone: 'ok' | 'warn' | 'bad' | 'idle'; label: string }
  onRefresh: () => void
  onCreateClick: () => void
}

const toneClasses = {
  ok: 'bg-leaf-light text-leaf',
  warn: 'bg-amber-light text-amber',
  bad: 'bg-brick-light text-brick',
  idle: 'bg-slate2-light text-slate2',
}

const dotClasses = {
  ok: 'bg-leaf',
  warn: 'bg-amber',
  bad: 'bg-brick',
  idle: 'bg-slate2',
}

export function Header({ status, onRefresh, onCreateClick }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal text-white">
            <SampleVialIcon className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate font-display font-semibold leading-tight text-ink">
              Batch Tracker
            </h1>
            <p className="truncate text-xs leading-tight text-slate2">
              Diagnostic sample pipeline console
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span
            className={`hidden items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium sm:inline-flex ${toneClasses[status.tone]}`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${dotClasses[status.tone]}`}
            />
            {status.label}
          </span>
          <button
            type="button"
            onClick={onCreateClick}
            className="focus-ring rounded-lg bg-teal px-3 py-2 text-sm font-medium text-white transition hover:bg-teal-dark"
          >
            Create batch
          </button>
          <button
            type="button"
            onClick={onRefresh}
            title="Refresh"
            aria-label="Refresh batches"
            className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line text-slate2 transition hover:bg-paper hover:text-ink"
          >
            <RefreshIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
