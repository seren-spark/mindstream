/**
 * SSE 流式请求封装（后续 chat 模块使用）
 */
export async function fetchSSE(
  url: string,
  options: RequestInit,
  onMessage: (chunk: string) => void,
): Promise<void> {
  const response = await fetch(url, options)

  if (!response.ok) {
    throw new Error(`SSE request failed: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('ReadableStream not supported')
  }

  const decoder = new TextDecoder()

  let finished = false
  while (!finished) {
    const { done, value } = await reader.read()
    finished = done
    if (value) onMessage(decoder.decode(value, { stream: true }))
  }
}
