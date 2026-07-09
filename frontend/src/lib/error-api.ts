/**
 * Error API client — fetch and aggregate frontend errors from the backend.
 */

export interface ErrorRecord {
  id: string
  type: string
  severity: string
  message: string
  stack: string | null
  fingerprint: string
  context: Record<string, unknown>
  ip_address: string | null
  user_agent: string | null
  created_at: string | null
}

export interface ErrorAggregation {
  fingerprint: string
  count: number
  type: string
  severity: string
  message: string
}

export interface ErrorListResponse {
  errors: ErrorRecord[]
  total: number
  page: number
  limit: number
}

export interface ErrorAggregationResponse {
  aggregations: ErrorAggregation[]
}

export interface FetchErrorsParams {
  page?: number
  limit?: number
  type?: string
  severity?: string
  since?: string
  aggregate?: boolean
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

/**
 * Fetch errors from the backend with optional pagination, filtering, and aggregation.
 */
export async function fetchErrors(
  params: FetchErrorsParams = {}
): Promise<ErrorListResponse | ErrorAggregationResponse> {
  const searchParams = new URLSearchParams()

  if (params.page) searchParams.set("page", String(params.page))
  if (params.limit) searchParams.set("limit", String(params.limit))
  if (params.type) searchParams.set("type", params.type)
  if (params.severity) searchParams.set("severity", params.severity)
  if (params.since) searchParams.set("since", params.since)
  if (params.aggregate) searchParams.set("aggregate", "true")

  const query = searchParams.toString()
  const url = `${API_BASE}/errors${query ? `?${query}` : ""}`

  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`)
  }

  return res.json()
}

/**
 * Fetch error aggregation (grouped by fingerprint).
 */
export async function fetchErrorAggregation(): Promise<ErrorAggregation[]> {
  const result = await fetchErrors({ aggregate: true, limit: 100 })
  return (result as ErrorAggregationResponse).aggregations
}