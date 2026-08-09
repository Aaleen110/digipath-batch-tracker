import { ApiError, type Batch, type CreateBatchRequest } from '@/types/batch'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
  /\/+$/,
  '',
) ?? ''
const API_KEY = (import.meta.env.VITE_API_KEY as string | undefined) ?? ''

// Single fetch wrapper — every API call goes through here with X-API-Key attached
async function safeMessage(res: Response): Promise<string> {
  try {
    const json = (await res.json()) as {
      message?: string
      detail?: string | { msg?: string }[]
      error?: string
    }
    if (typeof json.detail === 'string') return json.detail
    if (Array.isArray(json.detail)) {
      return json.detail.map((d) => d.msg).filter(Boolean).join(', ')
    }
    return json.message || json.error || ''
  } catch {
    return ''
  }
}

export async function apiRequest<T>(
  path: string,
  options: {
    method?: string
    body?: unknown
    headers?: Record<string, string>
  } = {},
): Promise<T> {
  if (!API_KEY.trim()) {
    // Fail early with a clear message — matches Task 3 invalid-token UX
    throw new ApiError(
      'Missing VITE_API_KEY in frontend/.env. Set it to match the backend API_KEY.',
      'config',
    )
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    ...options.headers,
  }

  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    })
  } catch {
    // fetch throws on network failure (backend down, CORS, etc.)
    throw new ApiError(
      'Could not reach the API. Is the backend running on port 8000?',
      'network',
    )
  }

  if (res.status === 401 || res.status === 403) {
    const detail = await safeMessage(res)
    throw new ApiError(
      detail ||
        'API key rejected. Check VITE_API_KEY in frontend/.env matches backend API_KEY.',
      'auth',
      res.status,
    )
  }

  if (!res.ok) {
    const detail = await safeMessage(res)
    throw new ApiError(
      detail || `Request failed with status ${res.status}.`,
      'api',
      res.status,
    )
  }

  if (res.status === 204) return null as T

  try {
    return (await res.json()) as T
  } catch {
    return null as T
  }
}

export function normalizeList(json: unknown): { items: Batch[]; total: number } {
  if (Array.isArray(json)) {
    return { items: json as Batch[], total: json.length }
  }

  const data = (json ?? {}) as Record<string, unknown>
  const items = (data.items ||
    data.results ||
    data.data ||
    data.batches ||
    []) as Batch[]
  const total = Number(data.total ?? data.count ?? items.length)
  return { items, total }
}

export function listBatches(params: {
  status?: string
  type?: string
  page: number
  page_size: number
}) {
  const qs = new URLSearchParams()
  if (params.status) qs.set('status', params.status)
  if (params.type?.trim()) qs.set('type', params.type.trim())
  qs.set('page', String(params.page))
  qs.set('page_size', String(params.page_size))
  return apiRequest<unknown>(`/batches?${qs.toString()}`)
}

export function createBatch(payload: CreateBatchRequest, idempotencyKey: string) {
  // Idempotency-Key header — backend uses it to prevent duplicate batches on retry
  return apiRequest<Batch>('/batches', {
    method: 'POST',
    body: payload,
    headers: { 'Idempotency-Key': idempotencyKey },
  })
}

export function getBatch(id: number) {
  return apiRequest<Batch>(`/batches/${id}`)
}

export function updateBatchStatus(id: number, status: string) {
  return apiRequest<Batch>(`/batches/${id}/status`, {
    method: 'PATCH',
    body: { status },
  })
}

export function notifyBatch(id: number) {
  return apiRequest<unknown>(`/batches/${id}/notify`, {
    method: 'POST',
  })
}
