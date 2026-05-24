<script setup lang="ts">
import FileList from '@/components/upload/FileList.vue'
import UploadTrigger from '@/components/upload/UploadTrigger.vue'
import type { LocalUploadFile } from '@/types/upload'

defineProps<{
  files: LocalUploadFile[]
  uploading: boolean
  globalError?: string
  successCount: number
  errorCount: number
  canUpload: boolean
}>()

const emit = defineEmits<{
  select: [files: File[]]
  remove: [uid: string]
  retry: [uid: string]
  upload: []
  clearCompleted: []
}>()
</script>

<template>
  <div class="upload-panel">
    <UploadTrigger @select="emit('select', $event)" />

    <a-alert
      v-if="globalError"
      type="error"
      :title="globalError"
      banner
      closable
      style="margin-top: 16px"
    />

    <div v-if="files.length" class="upload-panel__summary">
      <span>已选 {{ files.length }} 个文件</span>
      <span v-if="successCount">成功 {{ successCount }}</span>
      <span v-if="errorCount" class="upload-panel__error">失败 {{ errorCount }}</span>
    </div>

    <FileList
      :files="files"
      :uploading="uploading"
      style="margin-top: 16px"
      @remove="emit('remove', $event)"
      @retry="emit('retry', $event)"
    />

    <a-space style="margin-top: 16px">
      <a-button type="primary" :loading="uploading" :disabled="!canUpload" @click="emit('upload')">
        开始上传并解析
      </a-button>
      <a-button v-if="successCount" @click="emit('clearCompleted')">清除已完成</a-button>
    </a-space>
  </div>
</template>

<style scoped>
.upload-panel__summary {
  display: flex;
  gap: 16px;
  margin-top: 16px;
  font-size: 13px;
  color: var(--color-text-2);
}

.upload-panel__error {
  color: rgb(var(--red-6));
}
</style>
