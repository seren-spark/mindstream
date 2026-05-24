<script setup lang="ts">
const suggestions = [
  '这份文档的核心流程是什么？',
  '有哪些注意事项或限制条件？',
  '和上一版相比有什么变化？',
]

const emit = defineEmits<{
  pick: [text: string]
}>()
</script>

<template>
  <div class="chat-empty">
    <div class="chat-empty__icon" aria-hidden="true">
      <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="8" y="12" width="32" height="26" rx="4" stroke="currentColor" stroke-width="2" />
        <path
          d="M16 22h16M16 28h10"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        />
        <circle cx="38" cy="10" r="6" fill="rgb(var(--primary-6))" opacity="0.15" />
        <circle cx="38" cy="10" r="3" fill="rgb(var(--primary-6))" />
      </svg>
    </div>
    <h3 class="chat-empty__title">向知识库提问</h3>
    <p class="chat-empty__desc">基于检索增强生成，支持流式回答与引用来源核对</p>
    <div class="chat-empty__chips">
      <button
        v-for="(item, i) in suggestions"
        :key="item"
        type="button"
        class="chat-empty__chip"
        :style="{ animationDelay: `${0.12 * i + 0.2}s` }"
        @click="emit('pick', item)"
      >
        {{ item }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 56px 16px;
  text-align: center;
  animation: empty-in var(--chat-duration) var(--chat-ease-out) both;
}

@keyframes empty-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-empty__icon {
  width: 60px;
  height: 60px;
  margin-bottom: 20px;
  color: var(--color-text-4);
  animation: icon-float 4s var(--chat-ease) infinite;
}

@keyframes icon-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}

.chat-empty__icon svg {
  width: 100%;
  height: 100%;
}

.chat-empty__title {
  margin: 0 0 10px;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-1);
  letter-spacing: -0.02em;
}

.chat-empty__desc {
  margin: 0 0 28px;
  font-size: 14px;
  color: var(--color-text-3);
  max-width: 380px;
  line-height: 1.65;
}

.chat-empty__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  max-width: 520px;
}

.chat-empty__chip {
  padding: 10px 16px;
  font-size: 13px;
  line-height: 1.4;
  color: var(--color-text-2);
  background: var(--color-bg-2);
  border: 1px solid var(--color-border-2);
  border-radius: 22px;
  cursor: pointer;
  opacity: 0;
  animation: chip-in var(--chat-duration) var(--chat-ease-out) forwards;
  transition:
    border-color var(--chat-duration) var(--chat-ease),
    background var(--chat-duration) var(--chat-ease),
    color var(--chat-duration) var(--chat-ease),
    transform var(--chat-duration-fast) var(--chat-ease),
    box-shadow var(--chat-duration) var(--chat-ease);
}

@keyframes chip-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-empty__chip:hover {
  border-color: rgb(var(--primary-5));
  background: rgb(var(--primary-1));
  color: rgb(var(--primary-6));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--primary-6), 0.12);
}

.chat-empty__chip:active {
  transform: translateY(0);
}
</style>
