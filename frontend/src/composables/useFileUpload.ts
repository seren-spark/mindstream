import { computed, ref } from 'vue'
import { uploadDocument } from '@/api/upload'
import { MAX_UPLOAD_COUNT, validateLocalFile } from '@/constants/upload'
import type { LocalUploadFile, UploadOptions } from '@/types/upload'

function createUid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function useFileUpload(knowledgeBaseId: () => number) {
  const files = ref<LocalUploadFile[]>([])
  const uploading = ref(false)
  const globalError = ref('')

  const hasFiles = computed(() => files.value.length > 0)
  const canUpload = computed(
    () =>
      hasFiles.value &&
      files.value.some((item) => item.status === 'queued' || item.status === 'error'),
  )
  const successCount = computed(
    () => files.value.filter((item) => item.status === 'success').length,
  )
  const errorCount = computed(() => files.value.filter((item) => item.status === 'error').length)

  function addFiles(rawFiles: File[]) {
    globalError.value = ''
    const remaining = MAX_UPLOAD_COUNT - files.value.length
    if (remaining <= 0) {
      globalError.value = `最多同时添加 ${MAX_UPLOAD_COUNT} 个文件`
      return
    }

    const incoming = rawFiles.slice(0, remaining)
    for (const file of incoming) {
      const validationError = validateLocalFile(file)
      files.value.push({
        uid: createUid(),
        file,
        status: validationError ? 'error' : 'queued',
        progress: 0,
        errorMessage: validationError ?? undefined,
      })
    }
  }

  function removeFile(uid: string) {
    files.value = files.value.filter((item) => item.uid !== uid)
  }

  function retryFile(uid: string) {
    const target = files.value.find((item) => item.uid === uid)
    if (!target) return
    const validationError = validateLocalFile(target.file)
    target.status = validationError ? 'error' : 'queued'
    target.progress = 0
    target.errorMessage = validationError ?? undefined
    target.result = undefined
  }

  function clearCompleted() {
    files.value = files.value.filter((item) => item.status !== 'success')
  }

  function reset() {
    files.value = []
    uploading.value = false
    globalError.value = ''
  }

  async function uploadAll(options?: UploadOptions) {
    uploading.value = true
    globalError.value = ''

    const queue = files.value.filter((item) => item.status === 'queued' || item.status === 'error')
    for (const item of queue) {
      const validationError = validateLocalFile(item.file)
      if (validationError) {
        item.status = 'error'
        item.errorMessage = validationError
        continue
      }

      item.status = 'uploading'
      item.progress = 0
      item.errorMessage = undefined

      try {
        const { data } = await uploadDocument(knowledgeBaseId(), item.file, options, (percent) => {
          item.progress = percent
        })

        item.result = data
        if (data.knowledge_item_id <= 0) {
          item.status = 'error'
          item.errorMessage = data.error_message || '上传失败'
          continue
        }

        item.status = data.parse_status === 'completed' ? 'success' : 'parsing'
        item.progress = 100

        if (data.parse_status === 'failed') {
          item.status = 'error'
          item.errorMessage = data.error_message || '解析失败'
        } else if (data.parse_status === 'completed') {
          item.status = 'success'
        } else {
          item.status = 'success'
          item.errorMessage = data.error_message || undefined
        }
      } catch {
        item.status = 'error'
        item.errorMessage = '上传失败，请检查网络或稍后重试'
      }
    }

    uploading.value = false
  }

  return {
    files,
    uploading,
    globalError,
    hasFiles,
    canUpload,
    successCount,
    errorCount,
    addFiles,
    removeFile,
    retryFile,
    clearCompleted,
    reset,
    uploadAll,
  }
}
