<script setup lang="ts">
import { MarkdownRender } from 'markstream-vue'
import CitationList from '@/components/chat/CitationList.vue'
import type { ChatMessage } from '@/types/chat'

defineProps<{
  message: ChatMessage
}>()
</script>

<template>
  <div class="chat-message" :class="`chat-message--${message.role}`">
    <a-tag :color="message.role === 'user' ? 'arcoblue' : 'green'" size="small">
      {{ message.role === 'user' ? '用户' : '助手' }}
    </a-tag>

    <div v-if="message.role === 'user'" class="chat-message__text">
      {{ message.content }}
    </div>

    <div v-else class="chat-message__assistant">
      <div v-if="message.status === 'streaming' && !message.content" class="chat-message__loading">
        <a-spin />
        <span>正在检索并生成回答…</span>
      </div>

      <MarkdownRender
        v-if="message.content"
        :content="message.content"
        :max-live-nodes="0"
        :batch-rendering="true"
        :typewriter="message.status === 'streaming'"
        class="chat-message__markdown markstream-vue"
      />

      <span
        v-if="message.status === 'streaming' && message.content"
        class="chat-message__cursor"
        aria-hidden="true"
      />

      <a-alert
        v-if="message.status === 'error' || message.status === 'cancelled'"
        :type="message.status === 'cancelled' ? 'warning' : 'error'"
        :title="message.errorMessage || '生成失败'"
        banner
        style="margin-top: 8px"
      />

      <CitationList
        v-if="message.citations?.length && message.status !== 'streaming'"
        :citations="message.citations"
      />
    </div>
  </div>
</template>

<style scoped>
.chat-message {
  margin-bottom: 16px;
}

.chat-message__text {
  margin-top: 8px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.chat-message__assistant {
  margin-top: 8px;
}

.chat-message__loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-3);
  font-size: 13px;
}

.chat-message__markdown {
  line-height: 1.7;
}

.chat-message__cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  margin-left: 2px;
  vertical-align: text-bottom;
  background: rgb(var(--primary-6));
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}
</style>
