import http from './index'
import type { PingResponse } from '@/types/api'

export function fetchPing() {
  return http.get<PingResponse>('/ping')
}
