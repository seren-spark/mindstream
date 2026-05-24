<script setup lang="ts">
import { ref } from 'vue'
import { IconUpload } from '@arco-design/web-vue/es/icon'
import { ALLOWED_UPLOAD_ACCEPT, MAX_UPLOAD_COUNT, MAX_UPLOAD_SIZE_MB } from '@/constants/upload'

const emit = defineEmits<{
  select: [files: File[]]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const dragOver = ref(false)

function openPicker() {
  inputRef.value?.click()
}

function extractFiles(fileList: FileList | null) {
  if (!fileList?.length) return
  emit('select', Array.from(fileList))
}

function handleInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  extractFiles(target.files)
  target.value = ''
}

function handleDrop(event: DragEvent) {
  dragOver.value = false
  extractFiles(event.dataTransfer?.files ?? null)
}
</script>

<template>
  <div
    class="upload-trigger"
    :class="{ 'upload-trigger--active': dragOver }"
    @click="openPicker"
    @dragover.prevent="dragOver = true"
    @dragleave.prevent="dragOver = false"
    @drop.prevent="handleDrop"
  >
    <input
      ref="inputRef"
      type="file"
      class="upload-trigger__input"
      multiple
      :accept="ALLOWED_UPLOAD_ACCEPT"
      @change="handleInputChange"
    />
    <icon-upload class="upload-trigger__icon" />
    <p class="upload-trigger__title">拖拽文件到此处，或点击选择</p>
    <p class="upload-trigger__hint">
      支持 PDF / Word / Markdown / TXT，单文件最大 {{ MAX_UPLOAD_SIZE_MB }} MB，最多
      {{ MAX_UPLOAD_COUNT }} 个
    </p>
  </div>
</template>

<style scoped>
.upload-trigger {
  padding: 52px 28px;
  border: 2px dashed var(--color-border-2);
  border-radius: var(--ui-radius-lg);
  text-align: center;
  cursor: pointer;
  background: var(--color-fill-1);
  transition:
    border-color var(--ui-duration) var(--ui-ease),
    background var(--ui-duration) var(--ui-ease),
    transform var(--ui-duration) var(--ui-ease),
    box-shadow var(--ui-duration) var(--ui-ease);
}

.upload-trigger:hover,
.upload-trigger--active {
  border-color: rgb(var(--primary-5));
  background: rgb(var(--primary-1));
  transform: translateY(-2px);
  box-shadow: var(--ui-shadow-soft);
}

.upload-trigger__input {
  display: none;
}

.upload-trigger__icon {
  font-size: 36px;
  color: rgb(var(--primary-6));
  margin-bottom: 12px;
}

.upload-trigger__title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-1);
}

.upload-trigger__hint {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-3);
}
</style>
