import type { ChatMessage as PromptChatMessage } from './prompt'

export type ChatMessageStatus = 'pending' | 'streaming' | 'done' | 'error' | 'cancelled'

export interface CitationRef {
  index: number
  chunk_id: string
  knowledge_item_id: number
  source_name: string
  display_title: string
  source_type?: string
  file_name?: string | null
  category?: string | null
  updated_at?: string | null
  highlight_text: string
  content_excerpt: string
  score: number
  source_location: {
    page_start?: number | null
    page_end?: number | null
    section_title?: string | null
    heading_path?: string[]
    char_start?: number | null
    char_end?: number | null
  }
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  status: ChatMessageStatus
  citations?: CitationRef[]
  errorMessage?: string
}

export interface ChatStreamRequest {
  query: string
  history?: PromptChatMessage[]
  conversation_id?: string
  agent_id?: string
  top_k?: number
}

export type StreamEventType = 'start' | 'token' | 'references' | 'done' | 'error'

export interface StreamEventBase {
  type: StreamEventType
}

export interface StreamEventStart extends StreamEventBase {
  type: 'start'
  message_id: string
}

export interface StreamEventToken extends StreamEventBase {
  type: 'token'
  delta: string
}

export interface StreamEventReferences extends StreamEventBase {
  type: 'references'
  citations: CitationRef[]
}

export interface StreamEventDone extends StreamEventBase {
  type: 'done'
}

export interface StreamEventError extends StreamEventBase {
  type: 'error'
  message: string
}

export type StreamEvent =
  | StreamEventStart
  | StreamEventToken
  | StreamEventReferences
  | StreamEventDone
  | StreamEventError
