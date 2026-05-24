import http from './index'
import type {
  Conversation,
  ConversationMessageRecord,
  PaginatedConversations,
} from '@/types/conversation'

export function createConversation(
  knowledgeBaseId: number,
  title = '新对话',
  agentId?: string | null,
) {
  return http.post<Conversation>(`/knowledge-bases/${knowledgeBaseId}/conversations`, {
    title,
    agent_id: agentId ?? undefined,
  })
}

export function fetchConversations(
  knowledgeBaseId: number,
  page = 1,
  pageSize = 30,
  agentId?: string | null,
) {
  return http.get<PaginatedConversations>(`/knowledge-bases/${knowledgeBaseId}/conversations`, {
    params: { page, page_size: pageSize, agent_id: agentId ?? undefined },
  })
}

export function fetchConversationMessages(knowledgeBaseId: number, conversationId: string) {
  return http.get<ConversationMessageRecord[]>(
    `/knowledge-bases/${knowledgeBaseId}/conversations/${conversationId}/messages`,
  )
}

export function deleteConversation(knowledgeBaseId: number, conversationId: string) {
  return http.delete<void>(`/knowledge-bases/${knowledgeBaseId}/conversations/${conversationId}`)
}
