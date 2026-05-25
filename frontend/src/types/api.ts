/**
 * API 契约类型 — 与 backend/app/schemas/common.py 对齐。
 *
 * 约定：
 * - 成功：HTTP 2xx，response.data 即业务体（无 success/code 外壳）
 * - 失败：HTTP 4xx/5xx，body 为 ApiErrorResponse
 * - 分页：PaginatedResult<T>
 * - 流式：Content-Type text/event-stream，见 StreamEvent
 */

export interface PingResponse {
  status: string
  message: string
  version: string
}

/** 机器可读错误码，与后端 ApiErrorCode 一致 */
export type ApiErrorCode =
  | 'VALIDATION_ERROR'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'INVALID_STATUS'
  | 'UNSUPPORTED_FORMAT'
  | 'PIPELINE_ERROR'
  | 'STREAM_ERROR'
  | 'INTERNAL_ERROR'

export interface ValidationErrorItem {
  loc: (string | number)[]
  msg: string
  type: string
}

/** 统一错误响应体 */
export interface ApiErrorResponse {
  detail: string
  code?: ApiErrorCode | string
  errors?: ValidationErrorItem[]
}

/** 统一分页列表（成功时直接作为 response body） */
export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PaginationQuery {
  page?: number
  page_size?: number
}

export interface MessageResponse {
  message: string
}

/** 流式接口标识 */
export const STREAM_CONTENT_TYPE = 'text/event-stream'
export const STREAM_ACCEPT = 'text/event-stream'

export type SseEventType = 'start' | 'token' | 'references' | 'done' | 'error'

/** 判断响应是否为 SSE 流 */
export function isStreamResponse(contentType: string | null): boolean {
  return (contentType ?? '').includes(STREAM_CONTENT_TYPE)
}

/** 从 axios/fetch 错误中解析 ApiErrorResponse */
export function parseApiError(error: unknown): ApiErrorResponse {
  if (error && typeof error === 'object' && 'response' in error) {
    const resp = (error as { response?: { data?: ApiErrorResponse } }).response
    if (resp?.data?.detail) return resp.data
  }
  if (error instanceof Error) {
    return { detail: error.message }
  }
  return { detail: '请求失败，请稍后重试' }
}

/** 取用户可读错误文案 */
export function getErrorMessage(error: unknown): string {
  return parseApiError(error).detail
}
