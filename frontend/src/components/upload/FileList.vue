<script setup lang="ts">
import FileItem from '@/components/upload/FileItem.vue'
import type { LocalUploadFile } from '@/types/upload'

defineProps<{
  files: LocalUploadFile[]
  uploading?: boolean
}>()

const emit = defineEmits<{
  remove: [uid: string]
  retry: [uid: string]
}>()
</script>

<template>
  <div class="file-list">
    <a-empty v-if="!files.length" description="尚未选择文件">
      <template #image>
        <div class="file-list__empty-icon">📄</div>
      </template>
    </a-empty>

    <div v-else class="file-list__items">
      <FileItem
        v-for="item in files"
        :key="item.uid"
        :item="item"
        :disabled="uploading"
        @remove="emit('remove', item.uid)"
        @retry="emit('retry', item.uid)"
      />
    </div>
  </div>
</template>

<style scoped>
.file-list__items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-list__empty-icon {
  font-size: 40px;
  line-height: 1;
}
</style>
