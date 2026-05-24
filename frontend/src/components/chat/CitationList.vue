<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { IconInfoCircle } from '@arco-design/web-vue/es/icon'
import CitationRefRow from '@/components/chat/CitationRefRow.vue'
import type { CitationRef } from '@/types/chat'
import { ROUTE_NAMES } from '@/utils/constants'

const props = defineProps<{
  citations: CitationRef[]
  knowledgeBaseId: number
}>()

const emit = defineEmits<{
  highlight: [index: number | null]
}>()

const router = useRouter()
const activeIndex = ref<number | null>(null)
const expanded = ref(true)

function setHighlight(index: number | null) {
  activeIndex.value = index
  emit('highlight', index)
}

function scrollToCitation(index: number) {
  setHighlight(index)
  const el = document.getElementById(`cite-${index}`)
  el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  el?.classList.add('cite-row--flash')
  window.setTimeout(() => el?.classList.remove('cite-row--flash'), 1200)
}

function openCitation(cite: CitationRef) {
  activeIndex.value = cite.index
  router.push({
    name: ROUTE_NAMES.KNOWLEDGE_ITEMS,
    params: {
      id: String(props.knowledgeBaseId),
      itemId: String(cite.knowledge_item_id),
    },
    query: {
      chunk: cite.chunk_id,
      page: cite.source_location.page_start ?? undefined,
    },
  })
}

defineExpose({ scrollToCitation, activeIndex })
</script>

<template>
  <Transition name="chat-cite">
    <section v-if="citations.length" class="citation-panel">
      <header class="citation-panel__header" @click="expanded = !expanded">
        <span class="citation-panel__title"> 为你找到 {{ citations.length }} 篇参考资料 </span>
        <IconInfoCircle class="citation-panel__info" />
        <span class="citation-panel__toggle">{{ expanded ? '收起' : '展开' }}</span>
      </header>

      <Transition name="ui-fade">
        <div v-show="expanded" class="citation-panel__list">
          <CitationRefRow
            v-for="cite in citations"
            :key="cite.chunk_id"
            :cite="cite"
            :active="activeIndex === cite.index"
            @click="openCitation"
            @hover="setHighlight"
          />
        </div>
      </Transition>
    </section>
  </Transition>
</template>

<style scoped>
.citation-panel {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-2);
}

.citation-panel__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  user-select: none;
}

.citation-panel__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
}

.citation-panel__info {
  font-size: 14px;
  color: var(--color-text-4);
}

.citation-panel__toggle {
  margin-left: auto;
  font-size: 12px;
  color: var(--color-text-3);
}

.citation-panel__list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

:deep(.cite-row--flash) {
  animation: cite-flash 1.2s var(--ui-ease);
}

@keyframes cite-flash {
  0%,
  100% {
    background: var(--color-fill-2);
  }
  30% {
    background: rgb(var(--primary-1));
  }
}
</style>
