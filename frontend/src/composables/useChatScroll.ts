import { ref, type Ref } from 'vue'

const BOTTOM_THRESHOLD = 80

export function useChatScroll(containerRef: Ref<HTMLElement | null | undefined>) {
  const pinned = ref(true)
  let rafId = 0

  function onScroll() {
    const el = containerRef.value
    if (!el) return
    pinned.value = el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_THRESHOLD
  }

  function scrollToBottom(behavior: ScrollBehavior = 'auto') {
    const el = containerRef.value
    if (!el || !pinned.value) return

    cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(() => {
      el.scrollTo({ top: el.scrollHeight, behavior })
    })
  }

  return { pinned, onScroll, scrollToBottom }
}
