export type { ChatMessage, CitationRef, ChatStreamRequest, StreamEvent } from './chat'

export interface ChatMessageHistory {
  role: 'user' | 'assistant'
  content: string
}
