import type { ChatStreamRequest, StreamEvent } from '@/types/chat'
import { STREAM_ACCEPT, parseApiError } from '@/types/api'
import { API_ROUTES } from '@/api/routes'
import { parseSseEvents } from '@/api/sse'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export interface StreamChatHandlers {
  onStart?: (messageId: string) => void
  onToken?: (delta: string) => void
  onReferences?: (citations: StreamEvent & { type: 'references' }) => void
  onDone?: () => void
  onError?: (message: string) => void
}

function parseSseEventsLocal(buffer: string): { events: StreamEvent[]; rest: string } {
  return parseSseEvents<StreamEvent>(buffer)
}

export async function streamChat(
  knowledgeBaseId: number,
  payload: ChatStreamRequest,
  handlers: StreamChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}${API_ROUTES.chat.stream(knowledgeBaseId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: STREAM_ACCEPT },
    body: JSON.stringify(payload),
    signal,
  })

  if (!response.ok) {
    let message = `请求失败 (${response.status})`
    try {
      const body = await response.json()
      message = parseApiError({ response: { data: body } }).detail
    } catch {
      const text = await response.text().catch(() => '')
      if (text) message = text
    }
    throw new Error(message)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('浏览器不支持流式响应')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    let readResult = await reader.read()
    while (!readResult.done) {
      buffer += decoder.decode(readResult.value, { stream: true })
      const { events, rest } = parseSseEventsLocal(buffer)
      buffer = rest

      for (const event of events) {
        switch (event.type) {
          case 'start':
            handlers.onStart?.(event.message_id)
            break
          case 'token':
            handlers.onToken?.(event.delta)
            break
          case 'references':
            handlers.onReferences?.(event)
            break
          case 'done':
            handlers.onDone?.()
            break
          case 'error':
            handlers.onError?.(event.message)
            break
        }
      }
      readResult = await reader.read()
    }

    if (buffer.trim()) {
      const { events } = parseSseEventsLocal(`${buffer}\n\n`)
      for (const event of events) {
        if (event.type === 'done') handlers.onDone?.()
        if (event.type === 'error') handlers.onError?.(event.message)
      }
    }
  } finally {
    reader.releaseLock()
  }
}
