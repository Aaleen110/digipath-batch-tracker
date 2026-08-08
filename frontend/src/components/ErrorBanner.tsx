import { AlertIcon } from '@/components/icons'
import type { ApiError } from '@/types/batch'

interface ErrorBannerProps {
  error: ApiError
  onRetry: () => void
}

export function ErrorBanner({ error, onRetry }: ErrorBannerProps) {
  const kind = error.kind || 'api'
  const title =
    kind === 'auth'
      ? "Your API key isn't working"
      : kind === 'network'
        ? "Can't reach the API"
        : kind === 'config'
          ? 'Missing API configuration'
          : 'Something went wrong'

  return (
    <div
      className="flex flex-col gap-3 rounded-xl border border-brick/30 bg-brick-light p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5"
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertIcon className="mt-0.5 h-5 w-5 shrink-0 text-brick" />
        <div>
          <p className="text-sm font-semibold text-ink">{title}</p>
          <p className="mt-0.5 text-sm text-ink/80">
            {error.message || 'An unexpected error occurred.'}
          </p>
        </div>
      </div>
      {kind !== 'config' && (
        <button
          type="button"
          onClick={onRetry}
          className="focus-ring shrink-0 rounded-lg border border-line bg-white px-3 py-1.5 text-sm font-medium text-ink transition hover:bg-paper"
        >
          Retry
        </button>
      )}
    </div>
  )
}
