import { ref } from 'vue'
import { streamChat } from '@/api/chat'
import type { ChatMessage, CitationRef, ChatStreamRequest } from '@/types/chat'

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function useChatStream() {
  const streaming = ref(false)
  const abortController = ref<AbortController | null>(null)

  function cancel() {
    abortController.value?.abort()
    abortController.value = null
    streaming.value = false
  }

  async function send(
    knowledgeBaseId: number,
    query: string,
    messages: ChatMessage[],
    onUpdate: (messages: ChatMessage[]) => void,
  ) {
    if (!knowledgeBaseId || !query.trim()) return

    const userMsg: ChatMessage = {
      id: createId(),
      role: 'user',
      content: query.trim(),
      status: 'done',
    }
    const assistantMsg: ChatMessage = {
      id: createId(),
      role: 'assistant',
      content: '',
      status: 'streaming',
      citations: [],
    }

    const next = [...messages, userMsg, assistantMsg]
    onUpdate(next)

    const history = messages
      .filter((m) => m.status === 'done' && m.content)
      .slice(-6)
      .map((m) => ({ role: m.role, content: m.content }))

    const payload: ChatStreamRequest = {
      query: query.trim(),
      history: history as ChatStreamRequest['history'],
      top_k: 5,
    }

    abortController.value = new AbortController()
    streaming.value = true

    const assistantIndex = next.length - 1

    try {
      await streamChat(
        knowledgeBaseId,
        payload,
        {
          onToken(delta) {
            const updated = [...next]
            const current = updated[assistantIndex]
            if (!current) return
            updated[assistantIndex] = {
              ...current,
              content: current.content + delta,
              status: 'streaming',
            }
            onUpdate(updated)
            next[assistantIndex] = updated[assistantIndex]
          },
          onReferences(event) {
            const updated = [...next]
            const current = updated[assistantIndex]
            if (!current) return
            updated[assistantIndex] = {
              ...current,
              citations: event.citations as CitationRef[],
            }
            onUpdate(updated)
            next[assistantIndex] = updated[assistantIndex]
          },
          onDone() {
            const updated = [...next]
            const current = updated[assistantIndex]
            if (!current) return
            updated[assistantIndex] = { ...current, status: 'done' }
            onUpdate(updated)
          },
          onError(message) {
            const updated = [...next]
            const current = updated[assistantIndex]
            if (!current) return
            updated[assistantIndex] = {
              ...current,
              status: 'error',
              errorMessage: message,
            }
            onUpdate(updated)
          },
        },
        abortController.value.signal,
      )

      const current = next[assistantIndex]
      if (current?.status === 'streaming') {
        const updated = [...next]
        updated[assistantIndex] = { ...current, status: 'done' }
        onUpdate(updated)
      }
    } catch (err) {
      const isAbort = err instanceof DOMException && err.name === 'AbortError'
      const updated = [...next]
      const current = updated[assistantIndex]
      if (current) {
        updated[assistantIndex] = {
          ...current,
          status: isAbort ? 'cancelled' : 'error',
          errorMessage: isAbort ? '已停止生成' : err instanceof Error ? err.message : '请求失败',
        }
        onUpdate(updated)
      }
    } finally {
      streaming.value = false
      abortController.value = null
    }
  }

  return { streaming, send, cancel }
}
