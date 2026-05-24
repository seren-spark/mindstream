<script setup lang="ts">
import { ref } from 'vue'
import PageContainer from '@/components/common/PageContainer.vue'

const input = ref('')
const messages = ref<{ role: 'user' | 'assistant'; content: string }[]>([])
</script>

<template>
  <PageContainer title="智能问答">
    <div class="chat-panel">
      <div class="chat-panel__messages">
        <a-empty v-if="!messages.length" description="基于知识库的 RAG 问答（后续模块启用）" />
        <div v-for="(msg, index) in messages" :key="index" class="chat-message" :class="msg.role">
          <a-tag :color="msg.role === 'user' ? 'arcoblue' : 'green'" size="small">
            {{ msg.role === 'user' ? '用户' : '助手' }}
          </a-tag>
          <p>{{ msg.content }}</p>
        </div>
      </div>

      <div class="chat-panel__input">
        <a-textarea
          v-model="input"
          placeholder="输入问题，基于知识库检索回答（SSE 流式输出）"
          :auto-size="{ minRows: 2, maxRows: 4 }"
          disabled
        />
        <a-button type="primary" disabled style="margin-top: 8px">发送</a-button>
      </div>
    </div>
  </PageContainer>
</template>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: 480px;
}

.chat-panel__messages {
  flex: 1;
  min-height: 320px;
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 6px;
  background: var(--color-fill-1);
}

.chat-message {
  margin-bottom: 12px;
}

.chat-message p {
  margin: 8px 0 0;
  line-height: 1.6;
}
</style>
