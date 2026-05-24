import http from './index'
import type {
  KnowledgeItem,
  KnowledgeItemCreatePayload,
  KnowledgeItemListItem,
  KnowledgeItemListQuery,
  KnowledgeItemStatusUpdatePayload,
  KnowledgeItemUpdatePayload,
  PaginatedResult,
} from '@/types/knowledge-item'

export function fetchKnowledgeItems(knowledgeBaseId: number, params?: KnowledgeItemListQuery) {
  const query = {
    ...params,
    status: params?.status || undefined,
    source_type: params?.source_type || undefined,
  }
  return http.get<PaginatedResult<KnowledgeItemListItem>>(
    `/knowledge-bases/${knowledgeBaseId}/items`,
    { params: query },
  )
}

export function fetchKnowledgeItem(itemId: number) {
  return http.get<KnowledgeItem>(`/knowledge-items/${itemId}`)
}

export function createKnowledgeItem(knowledgeBaseId: number, data: KnowledgeItemCreatePayload) {
  return http.post<KnowledgeItem>(`/knowledge-bases/${knowledgeBaseId}/items`, data)
}

export function updateKnowledgeItem(itemId: number, data: KnowledgeItemUpdatePayload) {
  return http.put<KnowledgeItem>(`/knowledge-items/${itemId}`, data)
}

export function updateKnowledgeItemStatus(itemId: number, data: KnowledgeItemStatusUpdatePayload) {
  return http.patch<KnowledgeItem>(`/knowledge-items/${itemId}/status`, data)
}

export function triggerKnowledgeItemProcess(itemId: number) {
  return http.post<KnowledgeItem>(`/knowledge-items/${itemId}/process`)
}

export function deleteKnowledgeItem(itemId: number) {
  return http.delete<void>(`/knowledge-items/${itemId}`)
}
