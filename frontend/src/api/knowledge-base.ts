import http from './index'
import type {
  KnowledgeBase,
  KnowledgeBaseCreatePayload,
  KnowledgeBaseListQuery,
  KnowledgeBaseUpdatePayload,
  PaginatedResult,
} from '@/types/knowledge-base'

export function fetchKnowledgeBases(params?: KnowledgeBaseListQuery) {
  const query = {
    ...params,
    status: params?.status || undefined,
  }
  return http.get<PaginatedResult<KnowledgeBase>>('/knowledge-bases', { params: query })
}

export function fetchKnowledgeBase(id: number) {
  return http.get<KnowledgeBase>(`/knowledge-bases/${id}`)
}

export function createKnowledgeBase(data: KnowledgeBaseCreatePayload) {
  return http.post<KnowledgeBase>('/knowledge-bases', data)
}

export function updateKnowledgeBase(id: number, data: KnowledgeBaseUpdatePayload) {
  return http.put<KnowledgeBase>(`/knowledge-bases/${id}`, data)
}

export function deleteKnowledgeBase(id: number) {
  return http.delete<void>(`/knowledge-bases/${id}`)
}
