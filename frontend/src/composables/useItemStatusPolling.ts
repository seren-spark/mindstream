import { onUnmounted, watch, type Ref } from 'vue'
import { fetchKnowledgeItem } from '@/api/knowledge-item'
import type { KnowledgeItem, KnowledgeItemListItem } from '@/types/knowledge-item'

const DEFAULT_INTERVAL_MS = 2000

interface UseItemStatusPollingOptions {
  /** 当前列表中的条目（含 processing 态） */
  list: Ref<KnowledgeItemListItem[]>
  /** 当前选中的详情条目 */
  current: Ref<KnowledgeItem | null>
  /** 详情刷新后回调 */
  onDetailUpdate?: (item: KnowledgeItem) => void
  /** 列表行同步回调 */
  onListSync?: (item: KnowledgeItem | KnowledgeItemListItem) => void
  intervalMs?: number
}

/**
 * 当存在 processing 态条目时，轮询后端刷新 status / processing_progress。
 * 与 AgentGenerateWizard 的 job 轮询模式一致，保证前后端状态对齐。
 */
export function useItemStatusPolling(options: UseItemStatusPollingOptions) {
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  let timer: ReturnType<typeof setInterval> | null = null

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  function processingIds(): number[] {
    const ids = new Set<number>()
    for (const row of options.list.value) {
      if (row.status === 'processing') ids.add(row.id)
    }
    if (options.current.value?.status === 'processing') {
      ids.add(options.current.value.id)
    }
    return [...ids]
  }

  async function pollOnce() {
    const ids = processingIds()
    if (ids.length === 0) {
      stop()
      return
    }

    await Promise.all(
      ids.map(async (id) => {
        try {
          const { data } = await fetchKnowledgeItem(id)
          options.onListSync?.(data)
          if (options.current.value?.id === id) {
            options.onDetailUpdate?.(data)
          }
        } catch {
          /* 单次失败不打断轮询 */
        }
      }),
    )

    if (processingIds().length === 0) {
      stop()
    }
  }

  function startIfNeeded() {
    if (processingIds().length === 0) {
      stop()
      return
    }
    if (timer) return
    timer = setInterval(() => {
      pollOnce().catch(() => stop())
    }, intervalMs)
    pollOnce().catch(() => stop())
  }

  watch(
    () => [options.list.value, options.current.value?.status, options.current.value?.id],
    () => startIfNeeded(),
    { deep: true, immediate: true },
  )

  onUnmounted(stop)

  return { stop, pollOnce }
}
