export interface PingResponse {
  status: string
  message: string
  version: string
}

export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}
