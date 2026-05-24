<script setup lang="ts">
import { IconDelete, IconPlus } from '@arco-design/web-vue/es/icon'
import type { Conversation } from '@/types/conversation'
import { formatRelativeTime } from '@/utils/format'

defineProps<{
  conversations: Conversation[]
  activeId: string | null
  loading?: boolean
}>()

const emit = defineEmits<{
  newChat: []
  select: [id: string]
  delete: [id: string]
}>()

function handleDelete(conv: Conversation, event: Event) {
  event.stopPropagation()
  emit('delete', conv.id)
}
</script>

<template>
  <aside class="chat-sidebar">
    <div class="chat-sidebar__head">
      <span class="chat-sidebar__title">对话记录</span>
      <a-button type="primary" size="small" @click="emit('newChat')">
        <template #icon><IconPlus /></template>
        新对话
      </a-button>
    </div>

    <a-spin :loading="loading" class="chat-sidebar__spin">
      <a-empty v-if="!loading && !conversations.length" description="暂无历史对话" />

      <ul v-else class="chat-sidebar__list">
        <li
          v-for="conv in conversations"
          :key="conv.id"
          class="chat-sidebar__item"
          :class="{ 'chat-sidebar__item--active': activeId === conv.id }"
          @click="emit('select', conv.id)"
        >
          <div class="chat-sidebar__item-main">
            <span class="chat-sidebar__item-title">{{ conv.title }}</span>
            <span class="chat-sidebar__item-meta">
              {{ conv.message_count }} 条 ·
              {{ conv.last_message_at ? formatRelativeTime(conv.last_message_at) : '刚刚' }}
            </span>
          </div>
          <a-button
            type="text"
            size="mini"
            status="danger"
            class="chat-sidebar__delete"
            @click="handleDelete(conv, $event)"
          >
            <template #icon><IconDelete /></template>
          </a-button>
        </li>
      </ul>
    </a-spin>
  </aside>
</template>

<style scoped>
.chat-sidebar {
  display: flex;
  flex-direction: column;
  width: 260px;
  flex-shrink: 0;
  height: 100%;
  border-right: 1px solid var(--color-border-1);
  background: color-mix(in srgb, var(--color-bg-2) 96%, transparent);
}

.chat-sidebar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 14px 12px;
  border-bottom: 1px solid var(--color-border-1);
}

.chat-sidebar__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-2);
}

.chat-sidebar__spin {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-sidebar__spin :deep(.arco-spin) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chat-sidebar__list {
  list-style: none;
  margin: 0;
  padding: 8px;
  overflow-y: auto;
  flex: 1;
}

.chat-sidebar__item {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  padding: 10px 10px 10px 12px;
  margin-bottom: 4px;
  border-radius: var(--ui-radius-sm);
  cursor: pointer;
  transition:
    background var(--ui-duration-fast) var(--ui-ease),
    box-shadow var(--ui-duration-fast) var(--ui-ease);
}

.chat-sidebar__item:hover {
  background: var(--color-fill-2);
}

.chat-sidebar__item--active {
  background: rgb(var(--primary-1));
  box-shadow: inset 3px 0 0 rgb(var(--primary-6));
}

.chat-sidebar__item-main {
  flex: 1;
  min-width: 0;
}

.chat-sidebar__item-title {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-sidebar__item-meta {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: var(--color-text-4);
}

.chat-sidebar__delete {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--ui-duration-fast) ease;
}

.chat-sidebar__item:hover .chat-sidebar__delete {
  opacity: 1;
}
</style>
