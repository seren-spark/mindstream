import http from './client'
import { API_ROUTES } from './routes'
import type { PaginatedResult } from '@/types/api'
import type {
  KnowledgeBase,
  KnowledgeBaseCreatePayload,
  KnowledgeBaseListQuery,
  KnowledgeBaseUpdatePayload,
} from '@/types/knowledge-base'

export function fetchKnowledgeBases(params?: KnowledgeBaseListQuery) {
  const query = {
    ...params,
    status: params?.status || undefined,
  }
  return http.get<PaginatedResult<KnowledgeBase>>(API_ROUTES.kb.list, { params: query })
}

export function fetchKnowledgeBase(id: number) {
  return http.get<KnowledgeBase>(API_ROUTES.kb.detail(id))
}

export function createKnowledgeBase(data: KnowledgeBaseCreatePayload) {
  return http.post<KnowledgeBase>(API_ROUTES.kb.list, data)
}

export function updateKnowledgeBase(id: number, data: KnowledgeBaseUpdatePayload) {
  return http.put<KnowledgeBase>(API_ROUTES.kb.detail(id), data)
}

export function deleteKnowledgeBase(id: number) {
  return http.delete<void>(API_ROUTES.kb.detail(id))
}
