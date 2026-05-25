import http from './client'
import { API_ROUTES } from './routes'
import type { PaginatedResult } from '@/types/api'
import type {
  KnowledgeItem,
  KnowledgeItemCreatePayload,
  KnowledgeItemListItem,
  KnowledgeItemListQuery,
  KnowledgeItemStatusUpdatePayload,
  KnowledgeItemUpdatePayload,
} from '@/types/knowledge-item'

export function fetchKnowledgeItems(knowledgeBaseId: number, params?: KnowledgeItemListQuery) {
  const query = {
    ...params,
    status: params?.status || undefined,
    source_type: params?.source_type || undefined,
  }
  return http.get<PaginatedResult<KnowledgeItemListItem>>(
    API_ROUTES.knowledge.items(knowledgeBaseId),
    {
      params: query,
    },
  )
}

export function fetchKnowledgeItem(itemId: number) {
  return http.get<KnowledgeItem>(API_ROUTES.knowledge.item(itemId))
}

export function createKnowledgeItem(knowledgeBaseId: number, data: KnowledgeItemCreatePayload) {
  return http.post<KnowledgeItem>(API_ROUTES.knowledge.items(knowledgeBaseId), data)
}

export function updateKnowledgeItem(itemId: number, data: KnowledgeItemUpdatePayload) {
  return http.put<KnowledgeItem>(API_ROUTES.knowledge.item(itemId), data)
}

export function updateKnowledgeItemStatus(itemId: number, data: KnowledgeItemStatusUpdatePayload) {
  return http.patch<KnowledgeItem>(API_ROUTES.knowledge.itemStatus(itemId), data)
}

export function triggerKnowledgeItemProcess(itemId: number) {
  return http.post<KnowledgeItem>(API_ROUTES.knowledge.itemProcess(itemId))
}

export function deleteKnowledgeItem(itemId: number) {
  return http.delete<void>(API_ROUTES.knowledge.item(itemId))
}
