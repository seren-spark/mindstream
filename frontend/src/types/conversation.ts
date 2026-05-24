import type { ChatMessageStatus, CitationRef } from './chat'

export interface Conversation {
  id: string
  knowledge_base_id: number
  title: string
  message_count: number
  last_message_at: string | null
  created_at: string
  updated_at: string
}

export interface ConversationMessageRecord {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  status: ChatMessageStatus
  error_message?: string | null
  citations: CitationRef[]
  created_at: string
  updated_at: string
}

export interface PaginatedConversations {
  items: Conversation[]
  total: number
  page: number
  page_size: number
}
