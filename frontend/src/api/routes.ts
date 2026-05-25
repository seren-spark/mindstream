/**
 * API 路由常量 — 逻辑分组与路径模板。
 * 实际 baseURL 为 /api，此处为相对路径。
 */
export const API_ROUTES = {
  health: {
    ping: '/ping',
  },
  kb: {
    list: '/knowledge-bases',
    detail: (id: number) => `/knowledge-bases/${id}`,
  },
  knowledge: {
    items: (kbId: number) => `/knowledge-bases/${kbId}/items`,
    item: (id: number) => `/knowledge-items/${id}`,
    itemStatus: (id: number) => `/knowledge-items/${id}/status`,
    itemProcess: (id: number) => `/knowledge-items/${id}/process`,
    itemChunks: (id: number) => `/knowledge-items/${id}/chunks`,
    search: (kbId: number) => `/knowledge-bases/${kbId}/search`,
    promptBuild: (kbId: number) => `/knowledge-bases/${kbId}/prompt/build`,
    vectorsStats: (kbId: number) => `/knowledge-bases/${kbId}/vectors/stats`,
    vectorsRebuild: (kbId: number) => `/knowledge-bases/${kbId}/vectors/rebuild`,
    vectorsSearch: (kbId: number) => `/knowledge-bases/${kbId}/vectors/search`,
  },
  upload: {
    single: (kbId: number) => `/knowledge-bases/${kbId}/upload`,
    batch: (kbId: number) => `/knowledge-bases/${kbId}/upload/batch`,
  },
  chat: {
    stream: (kbId: number) => `/knowledge-bases/${kbId}/chat/stream`,
    conversations: (kbId: number) => `/knowledge-bases/${kbId}/conversations`,
    conversation: (kbId: number, convId: string) =>
      `/knowledge-bases/${kbId}/conversations/${convId}`,
    messages: (kbId: number, convId: string) =>
      `/knowledge-bases/${kbId}/conversations/${convId}/messages`,
  },
  agent: {
    list: (kbId: number) => `/knowledge-bases/${kbId}/agents`,
    detail: (kbId: number, agentId: string) => `/knowledge-bases/${kbId}/agents/${agentId}`,
    generate: (kbId: number) => `/knowledge-bases/${kbId}/agents/generate`,
    job: (kbId: number, jobId: string) => `/knowledge-bases/${kbId}/agents/generate/${jobId}`,
  },
  stats: {
    overview: '/stats/overview',
    heat: '/stats/heat',
    unanswered: '/stats/unanswered',
  },
  unanswered: {
    list: (kbId: number) => `/knowledge-bases/${kbId}/unanswered-questions`,
    detail: (kbId: number, id: number) => `/knowledge-bases/${kbId}/unanswered-questions/${id}`,
  },
} as const

export type ApiRouteGroup = keyof typeof API_ROUTES
