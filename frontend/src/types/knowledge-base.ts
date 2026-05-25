export type KnowledgeBaseStatus = 'active' | 'disabled'

export interface KnowledgeBase {
  id: number
  name: string
  description: string | null
  tags: string[]
  status: KnowledgeBaseStatus
  created_at: string
  updated_at: string
}

export interface KnowledgeBaseFormData {
  name: string
  description: string
  tags: string[]
  status: KnowledgeBaseStatus
}

export interface KnowledgeBaseListQuery {
  keyword?: string
  status?: KnowledgeBaseStatus | ''
  sort?: 'created_at_desc' | 'created_at_asc' | 'name_asc'
  page?: number
  page_size?: number
}

export type { PaginatedResult } from '@/types/api'

export interface KnowledgeBaseCreatePayload {
  name: string
  description?: string
  tags?: string[]
  status?: KnowledgeBaseStatus
}

export interface KnowledgeBaseUpdatePayload {
  name?: string
  description?: string
  tags?: string[]
  status?: KnowledgeBaseStatus
}
