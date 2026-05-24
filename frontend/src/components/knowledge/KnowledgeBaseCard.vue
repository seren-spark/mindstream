<script setup lang="ts">
import { IconDelete, IconEdit, IconMore, IconRight } from '@arco-design/web-vue/es/icon'
import type { KnowledgeBase } from '@/types/knowledge-base'
import { formatRelativeTime } from '@/utils/format'

defineProps<{
  item: KnowledgeBase
}>()

const emit = defineEmits<{
  enter: [item: KnowledgeBase]
  edit: [item: KnowledgeBase]
  delete: [item: KnowledgeBase]
}>()

const statusMap = {
  active: { label: '启用', color: 'green' },
  disabled: { label: '禁用', color: 'gray' },
} as const
</script>

<template>
  <a-card class="kb-card" hoverable @click="emit('enter', item)">
    <div class="kb-card__header">
      <div class="kb-card__title-wrap">
        <h3 class="kb-card__title">{{ item.name }}</h3>
        <a-tag :color="statusMap[item.status].color" size="small">
          {{ statusMap[item.status].label }}
        </a-tag>
      </div>

      <a-dropdown trigger="click" @click.stop>
        <a-button type="text" size="small" class="kb-card__more" @click.stop>
          <icon-more />
        </a-button>
        <template #content>
          <a-doption @click.stop="emit('edit', item)"> <icon-edit /> 编辑 </a-doption>
          <a-doption class="kb-card__danger" @click.stop="emit('delete', item)">
            <icon-delete /> 删除
          </a-doption>
        </template>
      </a-dropdown>
    </div>

    <p class="kb-card__desc">
      {{ item.description || '暂无描述，可在编辑时补充知识库用途说明' }}
    </p>

    <div v-if="item.tags.length" class="kb-card__tags">
      <a-tag v-for="tag in item.tags" :key="tag" size="small" color="arcoblue">
        {{ tag }}
      </a-tag>
    </div>
    <div v-else class="kb-card__tags kb-card__tags--empty">暂无标签</div>

    <div class="kb-card__footer">
      <span>创建于 {{ formatRelativeTime(item.created_at) }}</span>
      <a-link @click.stop="emit('enter', item)">
        进入
        <icon-right />
      </a-link>
    </div>
  </a-card>
</template>

<style scoped>
.kb-card {
  height: 100%;
  cursor: pointer;
  background: var(--color-bg-1);
  border: 1px solid var(--color-border-1) !important;
  box-shadow: var(--ui-shadow-sm);
  transition:
    transform var(--ui-duration) var(--ui-ease),
    box-shadow var(--ui-duration) var(--ui-ease),
    border-color var(--ui-duration-fast) var(--ui-ease) !important;
}

.kb-card:hover {
  transform: translateY(-4px);
  border-color: rgb(var(--primary-3)) !important;
  box-shadow: var(--ui-shadow-soft);
}

.kb-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.kb-card__title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.kb-card__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-card__more {
  flex-shrink: 0;
  border-radius: 8px;
}

.kb-card__desc {
  min-height: 44px;
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--color-text-3);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kb-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 24px;
  margin-bottom: 16px;
}

.kb-card__tags--empty {
  font-size: 12px;
  color: var(--color-text-4);
}

.kb-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-1);
  font-size: 12px;
  color: var(--color-text-3);
}

.kb-card__danger {
  color: rgb(var(--danger-6));
}
</style>
