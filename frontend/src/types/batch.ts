export type BatchStatus = 'queued' | 'processing' | 'completed' | 'failed'

export interface Batch {
  id: number
  sample_id: string
  batch_type: string
  submitted_by: string
  status: BatchStatus
  result: string | null
  partner_webhook?: string | null
  webhook_url?: string | null
  created_at: string
  updated_at: string
}

export interface BatchListResponse {
  items: Batch[]
  page: number
  page_size: number
  total: number
}

export interface CreateBatchRequest {
  sample_id: string
  batch_type: string
  submitted_by: string
  partner_webhook?: string | null
}

export type ApiErrorKind = 'config' | 'network' | 'auth' | 'api'

export class ApiError extends Error {
  kind: ApiErrorKind
  status?: number

  constructor(message: string, kind: ApiErrorKind, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
  }
}
