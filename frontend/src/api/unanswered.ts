import http from './index'
import type {
  PaginatedUnanswered,
  UnansweredQuestion,
  UnansweredResolvePayload,
  UnansweredResolveResult,
  UnansweredStatus,
} from '@/types/unanswered'

export function fetchUnansweredQuestions(
  knowledgeBaseId: number,
  params?: { status?: UnansweredStatus; page?: number; page_size?: number },
) {
  return http.get<PaginatedUnanswered>(`/knowledge-bases/${knowledgeBaseId}/unanswered-questions`, {
    params,
  })
}

export function fetchUnansweredQuestion(knowledgeBaseId: number, questionId: string) {
  return http.get<UnansweredQuestion>(
    `/knowledge-bases/${knowledgeBaseId}/unanswered-questions/${questionId}`,
  )
}

export function updateUnansweredQuestion(
  knowledgeBaseId: number,
  questionId: string,
  payload: {
    status?: UnansweredStatus
    suggested_title?: string
    suggested_summary?: string
  },
) {
  return http.patch<UnansweredQuestion>(
    `/knowledge-bases/${knowledgeBaseId}/unanswered-questions/${questionId}`,
    payload,
  )
}

export function dismissUnansweredQuestion(knowledgeBaseId: number, questionId: string) {
  return http.post<UnansweredQuestion>(
    `/knowledge-bases/${knowledgeBaseId}/unanswered-questions/${questionId}/dismiss`,
  )
}

export function resolveUnansweredQuestion(
  knowledgeBaseId: number,
  questionId: string,
  payload?: UnansweredResolvePayload,
) {
  return http.post<UnansweredResolveResult>(
    `/knowledge-bases/${knowledgeBaseId}/unanswered-questions/${questionId}/resolve`,
    payload ?? {},
  )
}
