import { useEffect, useState, type FormEvent } from 'react'

import { CloseIcon, Spinner } from '@/components/icons'
import type { CreateBatchRequest } from '@/types/batch'

interface CreateBatchModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (payload: CreateBatchRequest, idempotencyKey: string) => Promise<void>
}

const emptyForm: CreateBatchRequest = {
  sample_id: '',
  batch_type: '',
  submitted_by: '',
  partner_webhook: '',
}

export function CreateBatchModal({ open, onClose, onSubmit }: CreateBatchModalProps) {
  const [form, setForm] = useState<CreateBatchRequest>(emptyForm)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open) setForm(emptyForm)
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  if (!open) return null

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const payload: CreateBatchRequest = {
        sample_id: form.sample_id.trim(),
        batch_type: form.batch_type.trim(),
        submitted_by: form.submitted_by.trim(),
        partner_webhook: form.partner_webhook?.trim() || null,
      }
      // New UUID each submit — fine for normal use; would keep same key until success for retries
      await onSubmit(payload, crypto.randomUUID())
      onClose()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close modal"
        className="absolute inset-0 bg-ink/40 backdrop-blur-[1px]"
        onClick={onClose}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-batch-title"
        className="relative w-full max-w-lg rounded-2xl border border-line bg-white shadow-liftedcard"
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 id="create-batch-title" className="font-display text-lg font-semibold text-ink">
            Create batch
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-slate2 transition hover:text-ink"
          >
            <CloseIcon className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 px-5 py-5 sm:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm sm:col-span-2">
            <span className="text-[11px] font-medium uppercase tracking-wide text-slate2">
              Sample ID
            </span>
            <input
              required
              autoFocus
              value={form.sample_id}
              onChange={(e) => setForm({ ...form, sample_id: e.target.value })}
              placeholder="Sample #123"
              className="focus-ring rounded-lg border border-line bg-paper px-3 py-2 text-ink"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-[11px] font-medium uppercase tracking-wide text-slate2">
              Batch type
            </span>
            <input
              required
              value={form.batch_type}
              onChange={(e) => setForm({ ...form, batch_type: e.target.value })}
              placeholder="Blood Panel"
              className="focus-ring rounded-lg border border-line bg-paper px-3 py-2 text-ink"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-[11px] font-medium uppercase tracking-wide text-slate2">
              Submitted by
            </span>
            <input
              required
              value={form.submitted_by}
              onChange={(e) => setForm({ ...form, submitted_by: e.target.value })}
              placeholder="lab-user-01"
              className="focus-ring rounded-lg border border-line bg-paper px-3 py-2 text-ink"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm sm:col-span-2">
            <span className="text-[11px] font-medium uppercase tracking-wide text-slate2">
              Partner webhook (optional)
            </span>
            <input
              value={form.partner_webhook ?? ''}
              onChange={(e) =>
                setForm({ ...form, partner_webhook: e.target.value })
              }
              placeholder="https://webhook.site/..."
              className="focus-ring rounded-lg border border-line bg-paper px-3 py-2 font-mono text-[13px] text-ink"
            />
          </label>

          <div className="flex justify-end gap-2 sm:col-span-2">
            <button
              type="button"
              onClick={onClose}
              className="focus-ring rounded-lg border border-line px-4 py-2 text-sm font-medium text-ink transition hover:bg-paper"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="focus-ring inline-flex items-center gap-2 rounded-lg bg-teal px-4 py-2 text-sm font-medium text-white transition hover:bg-teal-dark disabled:opacity-50"
            >
              {submitting && <Spinner className="h-3.5 w-3.5" />}
              Create batch
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
