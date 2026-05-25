export type KnowledgeItemSourceType = 'manual' | 'file' | 'ai_generated'

export type KnowledgeItemStatus = 'pending' | 'processing' | 'ready' | 'failed' | 'disabled'

export interface KnowledgeItem {
  id: number
  knowledge_base_id: number
  title: string
  source_type: KnowledgeItemSourceType
  status: KnowledgeItemStatus
  content: string | null
  summary: string | null
  file_name: string | null
  file_type: string | null
  category: string | null
  tags: string[]
  chunk_count: number
  processing_progress: number
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface KnowledgeItemListItem {
  id: number
  knowledge_base_id: number
  title: string
  source_type: KnowledgeItemSourceType
  status: KnowledgeItemStatus
  summary: string | null
  file_name: string | null
  category: string | null
  tags: string[]
  chunk_count: number
  processing_progress: number
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface KnowledgeItemFormData {
  title: string
  content: string
  summary: string
  category: string
  tags: string[]
  source_type: KnowledgeItemSourceType
  file_name: string
}

export interface KnowledgeItemListQuery {
  keyword?: string
  status?: KnowledgeItemStatus | ''
  source_type?: KnowledgeItemSourceType | ''
  category?: string
  tag?: string
  sort?: 'updated_at_desc' | 'created_at_asc' | 'title_asc'
  page?: number
  page_size?: number
}

export interface KnowledgeItemCreatePayload {
  title: string
  source_type?: KnowledgeItemSourceType
  content?: string
  summary?: string
  file_name?: string
  file_type?: string
  category?: string
  tags?: string[]
}

export interface KnowledgeItemUpdatePayload {
  title?: string
  content?: string
  summary?: string
  category?: string
  tags?: string[]
  status?: KnowledgeItemStatus
}

export interface KnowledgeItemStatusUpdatePayload {
  status: KnowledgeItemStatus
  error_message?: string
}

export type { PaginatedResult } from '@/types/api'

export interface ItemStatusMeta {
  label: string
  color: string
  description: string
  /** 是否可被混合检索引用 */
  retrievable: boolean
  /** 是否展示「触发处理 / 重试」 */
  retryable: boolean
  /** 处理中是否展示进度条 */
  showProgress: boolean
}

export const ITEM_STATUS_MAP: Record<KnowledgeItemStatus, ItemStatusMeta> = {
  pending: {
    label: '待处理',
    color: 'orangered',
    description: '已创建，等待解析或入库',
    retrievable: false,
    retryable: true,
    showProgress: false,
  },
  processing: {
    label: '处理中',
    color: 'arcoblue',
    description: '正在解析、切片或向量化',
    retrievable: false,
    retryable: false,
    showProgress: true,
  },
  ready: {
    label: '可用',
    color: 'green',
    description: '可被 RAG 检索引用',
    retrievable: true,
    retryable: false,
    showProgress: false,
  },
  failed: {
    label: '失败',
    color: 'red',
    description: '处理失败，可查看错误并重试',
    retrievable: false,
    retryable: true,
    showProgress: false,
  },
  disabled: {
    label: '已禁用',
    color: 'gray',
    description: '不参与检索，向量已从索引中移除',
    retrievable: false,
    retryable: false,
    showProgress: false,
  },
}

export const ITEM_SOURCE_MAP: Record<KnowledgeItemSourceType, string> = {
  manual: '手动录入',
  file: '文件导入',
  ai_generated: 'AI 生成',
}
