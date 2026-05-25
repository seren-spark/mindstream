import type { KnowledgeItemStatus } from '@/types/knowledge-item'

/** 与后端 `domain/knowledge_item_fsm.py` 保持一致的转移表 */
export const ALLOWED_TRANSITIONS: Record<KnowledgeItemStatus, KnowledgeItemStatus[]> = {
  pending: ['processing', 'ready', 'failed', 'disabled'],
  processing: ['ready', 'failed', 'disabled'],
  ready: ['disabled', 'processing'],
  failed: ['pending', 'processing', 'disabled'],
  disabled: ['pending', 'ready'],
}

export const RETRIEVABLE_STATUSES: KnowledgeItemStatus[] = ['ready']
export const RETRYABLE_STATUSES: KnowledgeItemStatus[] = ['pending', 'failed']

/** 流水线进度锚点，与后端 PIPELINE_PROGRESS 对齐 */
export const PIPELINE_PROGRESS = {
  queued: 0,
  parsing: 30,
  chunking: 50,
  embeddingStart: 60,
  embeddingMid: 70,
  embeddingWrite: 85,
  done: 100,
} as const

export function canTransition(current: KnowledgeItemStatus, target: KnowledgeItemStatus): boolean {
  if (current === target) return true
  return ALLOWED_TRANSITIONS[current]?.includes(target) ?? false
}

export function isRetrievable(status: KnowledgeItemStatus): boolean {
  return RETRIEVABLE_STATUSES.includes(status)
}

export function isRetryable(status: KnowledgeItemStatus): boolean {
  return RETRYABLE_STATUSES.includes(status)
}

export function isTerminal(status: KnowledgeItemStatus): boolean {
  return status !== 'processing'
}
