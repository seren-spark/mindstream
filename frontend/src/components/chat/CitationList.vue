<script setup lang="ts">
import type { CitationRef } from '@/types/chat'

defineProps<{
  citations: CitationRef[]
}>()
</script>

<template>
  <div v-if="citations.length" class="citation-list">
    <div class="citation-list__title">引用来源</div>
    <a-card
      v-for="cite in citations"
      :key="cite.chunk_id"
      size="small"
      class="citation-card"
      :bordered="true"
    >
      <template #title>
        <span class="citation-card__index">[{{ cite.index }}]</span>
        {{ cite.display_title || cite.source_name }}
      </template>
      <p class="citation-card__excerpt">{{ cite.highlight_text || cite.content_excerpt }}</p>
    </a-card>
  </div>
</template>

<style scoped>
.citation-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.citation-list__title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-3);
}

.citation-card__index {
  color: rgb(var(--primary-6));
  margin-right: 4px;
}

.citation-card__excerpt {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-2);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
