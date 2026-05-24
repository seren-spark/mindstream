import type { KnowledgeItemStatus } from '@/types/knowledge-item'

export type LocalUploadStatus = 'idle' | 'queued' | 'uploading' | 'parsing' | 'success' | 'error'

export type ParseStatus = 'completed' | 'failed' | 'pending'

export interface UploadFileResult {
  upload_id: string
  knowledge_item_id: number
  knowledge_base_id: number
  original_filename: string
  stored_filename: string
  mime_type: string
  file_type: string
  size: number
  item_status: KnowledgeItemStatus
  parse_status: ParseStatus
  error_message: string | null
}

export interface BatchUploadResponse {
  total: number
  succeeded: number
  failed: number
  results: UploadFileResult[]
}

export interface LocalUploadFile {
  uid: string
  file: File
  status: LocalUploadStatus
  progress: number
  errorMessage?: string
  result?: UploadFileResult
}

export interface UploadOptions {
  category?: string
  tags?: string[]
  autoParse?: boolean
}
