import http from './index'
import type { BatchUploadResponse, UploadFileResult, UploadOptions } from '@/types/upload'

export function uploadDocument(
  knowledgeBaseId: number,
  file: File,
  options?: UploadOptions,
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData()
  formData.append('file', file)
  if (options?.category) formData.append('category', options.category)
  if (options?.tags?.length) formData.append('tags', options.tags.join(','))
  formData.append('auto_parse', String(options?.autoParse ?? true))

  return http.post<UploadFileResult>(`/knowledge-bases/${knowledgeBaseId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
    onUploadProgress: (event) => {
      if (!event.total) return
      onProgress?.(Math.round((event.loaded / event.total) * 100))
    },
  })
}

export function uploadDocumentsBatch(
  knowledgeBaseId: number,
  files: File[],
  options?: UploadOptions,
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  if (options?.category) formData.append('category', options.category)
  if (options?.tags?.length) formData.append('tags', options.tags.join(','))
  formData.append('auto_parse', String(options?.autoParse ?? true))

  return http.post<BatchUploadResponse>(
    `/knowledge-bases/${knowledgeBaseId}/upload/batch`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000,
      onUploadProgress: (event) => {
        if (!event.total) return
        onProgress?.(Math.round((event.loaded / event.total) * 100))
      },
    },
  )
}
