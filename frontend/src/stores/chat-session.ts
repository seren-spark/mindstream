import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  createConversation,
  deleteConversation,
  fetchConversationMessages,
  fetchConversations,
} from '@/api/conversation'
import type { ChatMessage } from '@/types/chat'
import type { Conversation } from '@/types/conversation'
import type { ConversationMessageRecord } from '@/types/conversation'

function mapRecordToUiMessage(record: ConversationMessageRecord): ChatMessage {
  return {
    id: record.id,
    role: record.role,
    content: record.content,
    status: record.status,
    citations: record.citations?.length ? record.citations : undefined,
    errorMessage: record.error_message ?? undefined,
  }
}

export const useChatSessionStore = defineStore('chatSession', () => {
  const conversationId = ref<string | null>(null)
  const conversations = ref<Conversation[]>([])
  const messages = ref<ChatMessage[]>([])
  const listLoading = ref(false)
  const messagesLoading = ref(false)

  async function loadConversationList(knowledgeBaseId: number) {
    listLoading.value = true
    try {
      const { data } = await fetchConversations(knowledgeBaseId)
      conversations.value = data.items
    } finally {
      listLoading.value = false
    }
  }

  async function ensureConversation(knowledgeBaseId: number): Promise<string> {
    if (conversationId.value) return conversationId.value
    const { data } = await createConversation(knowledgeBaseId)
    conversationId.value = data.id
    conversations.value = [data, ...conversations.value]
    return data.id
  }

  async function loadConversation(knowledgeBaseId: number, id: string) {
    messagesLoading.value = true
    try {
      const { data } = await fetchConversationMessages(knowledgeBaseId, id)
      conversationId.value = id
      messages.value = data.map(mapRecordToUiMessage)
    } finally {
      messagesLoading.value = false
    }
  }

  async function reloadMessages(knowledgeBaseId: number) {
    if (!conversationId.value) return
    await loadConversation(knowledgeBaseId, conversationId.value)
  }

  function startNewConversation() {
    conversationId.value = null
    messages.value = []
  }

  async function removeConversation(knowledgeBaseId: number, id: string) {
    await deleteConversation(knowledgeBaseId, id)
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (conversationId.value === id) {
      startNewConversation()
    }
  }

  return {
    conversationId,
    conversations,
    messages,
    listLoading,
    messagesLoading,
    loadConversationList,
    ensureConversation,
    loadConversation,
    reloadMessages,
    startNewConversation,
    removeConversation,
  }
})
