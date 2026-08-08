import { AlertIcon, CheckIcon, CloseIcon } from '@/components/icons'
import type { Toast } from '@/hooks/useToasts'

interface ToastStackProps {
  toasts: Toast[]
  onDismiss: (id: string) => void
}

export function ToastStack({ toasts, onDismiss }: ToastStackProps) {
  return (
    <div
      className="fixed top-4 right-4 z-50 flex w-[calc(100%-2rem)] flex-col gap-2 sm:w-80"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`toast-anim flex items-start gap-2.5 rounded-lg border bg-white p-3 shadow-liftedcard ${
            toast.type === 'error' ? 'border-brick/30' : 'border-leaf/30'
          }`}
        >
          {toast.type === 'error' ? (
            <AlertIcon className="mt-0.5 h-4 w-4 shrink-0 text-brick" />
          ) : (
            <CheckIcon className="mt-0.5 h-4 w-4 shrink-0 text-leaf" />
          )}
          <p className="flex-1 text-sm text-ink">{toast.message}</p>
          <button
            type="button"
            onClick={() => onDismiss(toast.id)}
            aria-label="Dismiss"
            className="text-slate2 hover:text-ink"
          >
            <CloseIcon className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}
