export type AgentStatus = 'draft' | 'published' | 'archived'
export type AgentTone = 'professional' | 'concise' | 'detailed'
export type AgentJobStatus = 'pending' | 'running' | 'succeeded' | 'failed'

export interface ExpertAgent {
  id: string
  knowledge_base_id: number
  slug: string
  name: string
  description: string
  persona: string
  tone: AgentTone | string
  custom_instructions: string | null
  welcome_message: string
  suggested_questions: string[]
  avatar_type: string
  avatar_value: string
  status: AgentStatus
  current_version_id: string | null
  published_at: string | null
  created_at: string
  updated_at: string
}

export interface AgentVersion {
  id: string
  agent_id: string
  version_number: number
  source: string
  profile_snapshot: Record<string, unknown>
  prompt_snapshot: string
  generation_job_id: string | null
  created_at: string
}

export interface AgentGenerationJob {
  id: string
  knowledge_base_id: number
  agent_id: string | null
  status: AgentJobStatus
  stage: string | null
  progress_message: string | null
  error_message: string | null
  model_name: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  agent: ExpertAgent | null
}

export interface ExpertAgentCreatePayload {
  name: string
  description?: string
  persona?: string
  tone?: AgentTone
  custom_instructions?: string | null
  welcome_message?: string
  suggested_questions?: string[]
}

export interface ExpertAgentUpdatePayload {
  name?: string
  description?: string
  persona?: string
  tone?: AgentTone
  custom_instructions?: string | null
  welcome_message?: string
  suggested_questions?: string[]
}

export interface PaginatedAgents {
  items: ExpertAgent[]
  total: number
  page: number
  page_size: number
}
