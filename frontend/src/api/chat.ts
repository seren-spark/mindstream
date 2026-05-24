import type { ChatStreamRequest, StreamEvent } from '@/types/chat'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export interface StreamChatHandlers {
  onStart?: (messageId: string) => void
  onToken?: (delta: string) => void
  onReferences?: (citations: StreamEvent & { type: 'references' }) => void
  onDone?: () => void
  onError?: (message: string) => void
}

function parseSseEvents(buffer: string): { events: StreamEvent[]; rest: string } {
  const events: StreamEvent[] = []
  const parts = buffer.split('\n\n')
  const rest = parts.pop() ?? ''

  for (const part of parts) {
    const lines = part.split('\n')
    for (const line of lines) {
      if (!line.startsWith('data:')) continue
      const raw = line.slice(5).trim()
      if (!raw) continue
      try {
        events.push(JSON.parse(raw) as StreamEvent)
      } catch {
        // 忽略不完整 JSON
      }
    }
  }
  return { events, rest }
}

export async function streamChat(
  knowledgeBaseId: number,
  payload: ChatStreamRequest,
  handlers: StreamChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/knowledge-bases/${knowledgeBaseId}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(payload),
    signal,
  })

  if (!response.ok) {
    const text = await response.text().catch(() => '')
    throw new Error(text || `请求失败 (${response.status})`)
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
      const { events, rest } = parseSseEvents(buffer)
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
      const { events } = parseSseEvents(`${buffer}\n\n`)
      for (const event of events) {
        if (event.type === 'done') handlers.onDone?.()
        if (event.type === 'error') handlers.onError?.(event.message)
      }
    }
  } finally {
    reader.releaseLock()
  }
}
