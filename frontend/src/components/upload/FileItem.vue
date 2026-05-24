<script setup lang="ts">
import { IconDelete, IconFile, IconRefresh } from '@arco-design/web-vue/es/icon'
import ItemStatusTag from '@/components/knowledge-item/ItemStatusTag.vue'
import { UPLOAD_STATUS_LABEL, formatFileSize, getFileExtension } from '@/constants/upload'
import type { LocalUploadFile } from '@/types/upload'

defineProps<{
  item: LocalUploadFile
  disabled?: boolean
}>()

const emit = defineEmits<{
  remove: []
  retry: []
}>()
</script>

<template>
  <div class="file-item" :class="`file-item--${item.status}`">
    <div class="file-item__icon">
      <icon-file />
    </div>

    <div class="file-item__body">
      <div class="file-item__head">
        <span class="file-item__name">{{ item.file.name }}</span>
        <a-tag size="small" :color="item.status === 'error' ? 'red' : 'arcoblue'">
          {{ UPLOAD_STATUS_LABEL[item.status] || item.status }}
        </a-tag>
      </div>

      <div class="file-item__meta">
        <span>{{ formatFileSize(item.file.size) }}</span>
        <span>{{ getFileExtension(item.file.name).toUpperCase() || 'FILE' }}</span>
      </div>

      <a-progress
        v-if="item.status === 'uploading'"
        :percent="item.progress / 100"
        size="small"
        style="margin-top: 8px"
      />

      <div v-if="item.result?.knowledge_item_id" class="file-item__result">
        <ItemStatusTag :status="item.result.item_status" />
        <span>条目 ID: {{ item.result.knowledge_item_id }}</span>
      </div>

      <a-alert
        v-if="item.errorMessage"
        type="error"
        :title="item.errorMessage"
        banner
        style="margin-top: 8px"
      />
    </div>

    <a-space direction="vertical" size="mini">
      <a-button
        v-if="item.status === 'error'"
        type="text"
        size="mini"
        :disabled="disabled"
        @click="emit('retry')"
      >
        <icon-refresh />
      </a-button>
      <a-button
        v-if="item.status !== 'uploading'"
        type="text"
        size="mini"
        status="danger"
        :disabled="disabled"
        @click="emit('remove')"
      >
        <icon-delete />
      </a-button>
    </a-space>
  </div>
</template>

<style scoped>
.file-item {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--color-border-2);
  border-radius: 8px;
  background: var(--color-bg-1);
}

.file-item--success {
  border-color: rgb(var(--green-3));
  background: rgb(var(--green-1));
}

.file-item--error {
  border-color: rgb(var(--red-3));
  background: rgb(var(--red-1));
}

.file-item__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--color-fill-2);
  color: rgb(var(--primary-6));
  flex-shrink: 0;
}

.file-item__body {
  flex: 1;
  min-width: 0;
}

.file-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.file-item__name {
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-item__meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--color-text-3);
}

.file-item__result {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-2);
}
</style>
