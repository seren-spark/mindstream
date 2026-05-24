<script setup lang="ts">
import { IconBook } from '@arco-design/web-vue/es/icon'
import type { CitationRef } from '@/types/chat'

defineProps<{
  citations: CitationRef[]
}>()

function locationLabel(cite: CitationRef): string {
  const loc = cite.source_location
  const parts: string[] = []
  if (loc.page_start != null) {
    parts.push(
      loc.page_end != null && loc.page_end !== loc.page_start
        ? `第 ${loc.page_start}-${loc.page_end} 页`
        : `第 ${loc.page_start} 页`,
    )
  }
  if (loc.section_title) parts.push(loc.section_title)
  return parts.join(' · ')
}
</script>

<template>
  <Transition name="chat-cite">
    <div v-if="citations.length" class="citation-list">
      <a-collapse :default-active-key="[]" :bordered="false">
        <a-collapse-item key="refs" :header="`引用来源 (${citations.length})`">
          <div class="citation-list__items">
            <div
              v-for="(cite, i) in citations"
              :id="`cite-${cite.index}`"
              :key="cite.chunk_id"
              class="citation-card"
              :style="{ animationDelay: `${i * 0.06}s` }"
            >
              <div class="citation-card__head">
                <span class="citation-card__index">[{{ cite.index }}]</span>
                <IconBook class="citation-card__icon" />
                <span class="citation-card__title">
                  {{ cite.display_title || cite.source_name }}
                </span>
              </div>
              <p v-if="locationLabel(cite)" class="citation-card__meta">
                {{ locationLabel(cite) }}
              </p>
              <p class="citation-card__excerpt">
                {{ cite.highlight_text || cite.content_excerpt }}
              </p>
            </div>
          </div>
        </a-collapse-item>
      </a-collapse>
    </div>
  </Transition>
</template>

<style scoped>
.citation-list {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed var(--color-border-2);
}

.citation-list :deep(.arco-collapse-item-header) {
  padding: 0 0 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-3);
  background: transparent;
  transition: color var(--chat-duration-fast) ease;
}

.citation-list :deep(.arco-collapse-item-header:hover) {
  color: rgb(var(--primary-6));
}

.citation-list :deep(.arco-collapse-item-content) {
  padding: 0;
  background: transparent;
}

.citation-list :deep(.arco-collapse-item-content-box) {
  transition: height var(--chat-duration) var(--chat-ease) !important;
}

.citation-list__items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.citation-card {
  padding: 11px 14px;
  background: var(--color-fill-1);
  border: 1px solid var(--color-border-2);
  border-radius: 10px;
  opacity: 0;
  animation: cite-card-in var(--chat-duration) var(--chat-ease-out) forwards;
  transition:
    border-color var(--chat-duration) var(--chat-ease),
    background var(--chat-duration) var(--chat-ease),
    transform var(--chat-duration-fast) var(--chat-ease),
    box-shadow var(--chat-duration) var(--chat-ease);
}

@keyframes cite-card-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.citation-card:hover {
  border-color: rgb(var(--primary-4));
  background: var(--color-bg-2);
  transform: translateX(2px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.citation-card__head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.citation-card__index {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  color: rgb(var(--primary-6));
}

.citation-card__icon {
  flex-shrink: 0;
  font-size: 14px;
  color: var(--color-text-3);
}

.citation-card__title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.citation-card__meta {
  margin: 0 0 6px;
  font-size: 12px;
  color: var(--color-text-4);
}

.citation-card__excerpt {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--color-text-2);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
