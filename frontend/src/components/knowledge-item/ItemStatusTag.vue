<script setup lang="ts">
import type { KnowledgeItemStatus } from '@/types/knowledge-item'
import { ITEM_STATUS_MAP } from '@/types/knowledge-item'

defineProps<{
  status: KnowledgeItemStatus
  showDot?: boolean
}>()
</script>

<template>
  <a-tooltip :content="ITEM_STATUS_MAP[status].description">
    <a-tag :color="ITEM_STATUS_MAP[status].color" size="small">
      <span v-if="showDot" class="status-dot" />
      {{ ITEM_STATUS_MAP[status].label }}
    </a-tag>
  </a-tooltip>
</template>

<style scoped>
.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 4px;
  border-radius: 50%;
  background: currentColor;
}
</style>
