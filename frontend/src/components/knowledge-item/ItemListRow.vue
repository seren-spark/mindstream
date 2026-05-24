<script setup lang="ts">
import ItemStatusTag from '@/components/knowledge-item/ItemStatusTag.vue'
import type { KnowledgeItemListItem } from '@/types/knowledge-item'
import { ITEM_SOURCE_MAP } from '@/types/knowledge-item'
import { formatRelativeTime } from '@/utils/format'

defineProps<{
  item: KnowledgeItemListItem
  active?: boolean
}>()

const emit = defineEmits<{
  select: [item: KnowledgeItemListItem]
}>()
</script>

<template>
  <div class="item-row" :class="{ 'item-row--active': active }" @click="emit('select', item)">
    <div class="item-row__head">
      <h4 class="item-row__title">{{ item.title }}</h4>
      <ItemStatusTag :status="item.status" />
    </div>

    <p class="item-row__summary">
      {{ item.summary || item.file_name || '暂无摘要' }}
    </p>

    <div class="item-row__meta">
      <span>{{ ITEM_SOURCE_MAP[item.source_type] }}</span>
      <span>{{ formatRelativeTime(item.updated_at) }}</span>
    </div>

    <a-progress
      v-if="item.status === 'processing'"
      :percent="item.processing_progress / 100"
      size="small"
      style="margin-top: 8px"
    />

    <div v-if="item.tags.length" class="item-row__tags">
      <a-tag v-for="tag in item.tags.slice(0, 3)" :key="tag" size="small">{{ tag }}</a-tag>
      <span v-if="item.tags.length > 3" class="item-row__more">+{{ item.tags.length - 3 }}</span>
    </div>
  </div>
</template>

<style scoped>
.item-row {
  padding: 12px 14px;
  margin: 4px 8px;
  border: 1px solid transparent;
  border-radius: var(--ui-radius-sm);
  cursor: pointer;
  transition:
    background var(--ui-duration-fast) var(--ui-ease),
    border-color var(--ui-duration-fast) var(--ui-ease),
    transform var(--ui-duration-fast) var(--ui-ease),
    box-shadow var(--ui-duration-fast) var(--ui-ease);
}

.item-row:hover {
  background: var(--color-fill-2);
  transform: translateX(2px);
}

.item-row--active {
  background: rgb(var(--primary-1));
  border-color: rgb(var(--primary-3));
  box-shadow: 0 2px 10px rgba(var(--primary-6), 0.08);
}

.item-row__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.item-row__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-row__summary {
  margin: 0 0 8px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-3);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-row__meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--color-text-4);
}

.item-row__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}

.item-row__more {
  font-size: 11px;
  color: var(--color-text-4);
}
</style>
