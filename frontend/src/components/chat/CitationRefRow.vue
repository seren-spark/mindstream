<script setup lang="ts">
import { IconBook, IconFile, IconFolder, IconRobot } from '@arco-design/web-vue/es/icon'
import type { CitationRef } from '@/types/chat'
import { formatCitationDate, getCitationLabel, getCitationSnippet } from '@/utils/citation'

const props = defineProps<{
  cite: CitationRef
  active?: boolean
}>()

const emit = defineEmits<{
  click: [cite: CitationRef]
  hover: [index: number | null]
}>()

const iconMap = {
  file: IconFile,
  manual: IconBook,
  ai_generated: IconRobot,
} as const

function resolveIcon() {
  const key = (props.cite.source_type || 'manual') as keyof typeof iconMap
  return iconMap[key] ?? IconFolder
}
</script>

<template>
  <div
    :id="`cite-${cite.index}`"
    class="cite-row"
    :class="{ 'cite-row--active': active }"
    role="button"
    tabindex="0"
    @click="emit('click', cite)"
    @mouseenter="emit('hover', cite.index)"
    @mouseleave="emit('hover', null)"
    @keydown.enter="emit('click', cite)"
  >
    <span class="cite-row__index">{{ cite.index }}</span>
    <component :is="resolveIcon()" class="cite-row__type-icon" />
    <div class="cite-row__main">
      <a class="cite-row__title" @click.prevent="emit('click', cite)">
        {{ getCitationLabel(cite) }}
      </a>
      <p v-if="getCitationSnippet(cite)" class="cite-row__snippet">
        {{ getCitationSnippet(cite) }}
      </p>
    </div>
    <div class="cite-row__meta">
      <a-tag v-if="cite.category" size="small" class="cite-row__tag">{{ cite.category }}</a-tag>
      <span v-if="formatCitationDate(cite.updated_at)" class="cite-row__date">
        {{ formatCitationDate(cite.updated_at) }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.cite-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  margin: 0 -4px;
  border-radius: var(--ui-radius-sm);
  cursor: pointer;
  transition:
    background var(--ui-duration-fast) var(--ui-ease),
    box-shadow var(--ui-duration-fast) var(--ui-ease);
}

.cite-row:hover,
.cite-row--active {
  background: var(--color-fill-2);
}

.cite-row--active {
  box-shadow: inset 3px 0 0 rgb(var(--primary-6));
}

.cite-row__index {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-2);
  background: var(--color-fill-3);
  border-radius: 50%;
  transition:
    background var(--ui-duration-fast) var(--ui-ease),
    color var(--ui-duration-fast) var(--ui-ease);
}

.cite-row--active .cite-row__index,
.cite-row:hover .cite-row__index {
  color: rgb(var(--primary-6));
  background: rgb(var(--primary-1));
}

.cite-row__type-icon {
  flex-shrink: 0;
  margin-top: 3px;
  font-size: 16px;
  color: var(--color-text-3);
}

.cite-row__main {
  flex: 1;
  min-width: 0;
}

.cite-row__title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.45;
  color: rgb(var(--primary-6));
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cite-row__title:hover {
  text-decoration: underline;
}

.cite-row__snippet {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-3);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cite-row__meta {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  margin-top: 2px;
}

.cite-row__tag {
  margin: 0;
}

.cite-row__date {
  font-size: 12px;
  color: var(--color-text-4);
  white-space: nowrap;
}
</style>
