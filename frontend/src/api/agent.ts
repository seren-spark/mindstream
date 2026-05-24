import http from './index'
import type {
  AgentGenerationJob,
  AgentVersion,
  ExpertAgent,
  ExpertAgentCreatePayload,
  ExpertAgentUpdatePayload,
  PaginatedAgents,
} from '@/types/agent'

export function startAgentGenerate(knowledgeBaseId: number) {
  return http.post<AgentGenerationJob>(`/knowledge-bases/${knowledgeBaseId}/agents/generate`, {})
}

export function fetchAgentGenerateJob(knowledgeBaseId: number, jobId: string) {
  return http.get<AgentGenerationJob>(
    `/knowledge-bases/${knowledgeBaseId}/agents/generate/${jobId}`,
  )
}

export function fetchAgents(knowledgeBaseId: number, status?: string, page = 1, pageSize = 20) {
  return http.get<PaginatedAgents>(`/knowledge-bases/${knowledgeBaseId}/agents`, {
    params: { status, page, page_size: pageSize },
  })
}

export function createAgent(knowledgeBaseId: number, payload: ExpertAgentCreatePayload) {
  return http.post<ExpertAgent>(`/knowledge-bases/${knowledgeBaseId}/agents`, payload)
}

export function fetchAgent(knowledgeBaseId: number, agentId: string) {
  return http.get<ExpertAgent>(`/knowledge-bases/${knowledgeBaseId}/agents/${agentId}`)
}

export function updateAgent(
  knowledgeBaseId: number,
  agentId: string,
  payload: ExpertAgentUpdatePayload,
) {
  return http.patch<ExpertAgent>(`/knowledge-bases/${knowledgeBaseId}/agents/${agentId}`, payload)
}

export function publishAgent(knowledgeBaseId: number, agentId: string) {
  return http.post<ExpertAgent>(`/knowledge-bases/${knowledgeBaseId}/agents/${agentId}/publish`)
}

export function archiveAgent(knowledgeBaseId: number, agentId: string) {
  return http.post<ExpertAgent>(`/knowledge-bases/${knowledgeBaseId}/agents/${agentId}/archive`)
}

export function regenerateAgent(knowledgeBaseId: number, agentId: string) {
  return http.post<ExpertAgent>(`/knowledge-bases/${knowledgeBaseId}/agents/${agentId}/regenerate`)
}

export function deleteAgent(knowledgeBaseId: number, agentId: string) {
  return http.delete<void>(`/knowledge-bases/${knowledgeBaseId}/agents/${agentId}`)
}

export function fetchAgentVersions(knowledgeBaseId: number, agentId: string) {
  return http.get<AgentVersion[]>(`/knowledge-bases/${knowledgeBaseId}/agents/${agentId}/versions`)
}

export function fetchAgentVersion(knowledgeBaseId: number, agentId: string, versionId: string) {
  return http.get<AgentVersion>(
    `/knowledge-bases/${knowledgeBaseId}/agents/${agentId}/versions/${versionId}`,
  )
}
