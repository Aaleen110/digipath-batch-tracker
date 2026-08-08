import { useEffect, useState } from 'react'

import { Field } from '@/components/Field'
import { CloseIcon, Spinner } from '@/components/icons'
import { StatusBadge } from '@/components/StatusBadge'
import { getBatch } from '@/api/client'
import { formatDate } from '@/lib/status'
import type { Batch } from '@/types/batch'
import { ApiError } from '@/types/batch'

interface BatchDetailModalProps {
  batchId: number | null
  onClose: () => void
}

export function BatchDetailModal({ batchId, onClose }: BatchDetailModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [batch, setBatch] = useState<Batch | null>(null)

  useEffect(() => {
    if (batchId === null) return

    let cancelled = false
    setLoading(true)
    setError(null)
    setBatch(null)

    getBatch(batchId)
      .then((data) => {
        if (!cancelled) {
          setBatch(data)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError ? err.message : 'Could not load batch details.',
          )
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [batchId])

  useEffect(() => {
    if (batchId === null) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [batchId, onClose])

  if (batchId === null) return null

  const webhook = batch?.partner_webhook || batch?.webhook_url

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
        aria-labelledby="batch-detail-title"
        className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-line bg-white shadow-liftedcard"
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-line bg-white px-5 py-4">
          <h2 id="batch-detail-title" className="font-display text-lg font-semibold text-ink">
            Batch details
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

        <div className="px-5 py-5">
          {loading && (
            <p className="flex items-center gap-2 text-sm text-slate2">
              <Spinner className="h-4 w-4" /> Loading batch…
            </p>
          )}

          {error && <p className="text-sm text-brick">{error}</p>}

          {batch && !loading && !error && (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center gap-2.5">
                <p className="font-display text-base font-semibold text-ink">
                  {batch.sample_id}
                </p>
                <StatusBadge status={batch.status} />
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Batch #" value={batch.id} mono />
                <Field label="Batch type" value={batch.batch_type} />
                <Field label="Submitted by" value={batch.submitted_by} />
                <Field
                  label="Result"
                  value={
                    batch.result != null && batch.result !== ''
                      ? String(batch.result)
                      : 'Not available yet'
                  }
                />
                <Field label="Created" value={formatDate(batch.created_at)} />
                <Field label="Updated" value={formatDate(batch.updated_at)} />
              </div>

              <div className="min-w-0">
                <p className="text-[11px] font-medium uppercase tracking-wide text-slate2">
                  Partner webhook
                </p>
                {webhook ? (
                  <a
                    href={webhook}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-0.5 block break-all font-mono text-[13px] text-teal hover:underline"
                  >
                    {webhook}
                  </a>
                ) : (
                  <p className="mt-0.5 text-sm text-ink">—</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
