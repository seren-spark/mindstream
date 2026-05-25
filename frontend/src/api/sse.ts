/**
 * SSE 解析工具 — 供 chat 等流式接口复用。
 */
import type { SseEventType } from '@/types/api'

export interface ParsedSseFrame<T extends { type: SseEventType }> {
  events: T[]
  rest: string
}

export function parseSseEvents<T extends { type: SseEventType }>(
  buffer: string,
): ParsedSseFrame<T> {
  const events: T[] = []
  const parts = buffer.split('\n\n')
  const rest = parts.pop() ?? ''

  for (const part of parts) {
    for (const line of part.split('\n')) {
      if (!line.startsWith('data:')) continue
      const raw = line.slice(5).trim()
      if (!raw) continue
      try {
        events.push(JSON.parse(raw) as T)
      } catch {
        // 忽略不完整 JSON 帧
      }
    }
  }
  return { events, rest }
}
