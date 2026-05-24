<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { IconSend, IconPause } from '@arco-design/web-vue/es/icon'

const props = defineProps<{
  modelValue: string
  disabled?: boolean
  streaming?: boolean
  canSend?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
  stop: []
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)

const innerValue = computed({
  get: () => props.modelValue,
  set: (v: string) => emit('update:modelValue', v),
})

function resizeTextarea() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 128)}px`
}

watch(
  () => props.modelValue,
  async () => {
    await nextTick()
    resizeTextarea()
  },
)

onMounted(resizeTextarea)

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    if (props.canSend) emit('send')
  }
}

function onInput() {
  resizeTextarea()
}
</script>

<template>
  <div class="chat-input">
    <div
      class="chat-input__box"
      :class="{
        'chat-input__box--disabled': disabled,
        'chat-input__box--focusable': !disabled,
      }"
    >
      <textarea
        ref="textareaRef"
        v-model="innerValue"
        class="chat-input__textarea"
        placeholder="输入问题，Enter 发送，Shift + Enter 换行"
        rows="1"
        :disabled="disabled"
        @keydown="onKeydown"
        @input="onInput"
      />
      <div class="chat-input__actions">
        <Transition name="ui-fade" mode="out-in">
          <a-button
            v-if="streaming"
            key="stop"
            type="outline"
            shape="circle"
            size="small"
            class="chat-input__btn"
            @click="emit('stop')"
          >
            <template #icon><IconPause /></template>
          </a-button>
          <a-button
            v-else
            key="send"
            type="primary"
            shape="circle"
            size="small"
            class="chat-input__btn chat-input__btn--send"
            :disabled="!canSend"
            @click="emit('send')"
          >
            <template #icon><IconSend /></template>
          </a-button>
        </Transition>
      </div>
    </div>
    <p class="chat-input__hint">回答由 AI 基于所选知识库生成，重要信息请以引用来源为准</p>
  </div>
</template>

<style scoped>
.chat-input {
  width: 100%;
  max-width: 768px;
  margin: 0 auto;
}

.chat-input__box {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 12px 14px 12px 18px;
  background: var(--color-bg-2);
  border: 1px solid var(--color-border-2);
  border-radius: 22px;
  box-shadow: var(--ui-shadow-sm);
  transition:
    border-color var(--ui-duration) var(--ui-ease),
    box-shadow var(--ui-duration) var(--ui-ease),
    opacity var(--ui-duration) var(--ui-ease),
    transform var(--ui-duration) var(--ui-ease);
}

.chat-input__box--focusable:focus-within {
  border-color: rgb(var(--primary-5));
  box-shadow:
    0 0 0 4px rgba(var(--primary-6), 0.07),
    var(--ui-shadow-soft);
  transform: translateY(-2px);
}

.chat-input__box--disabled {
  opacity: 0.65;
  transform: none;
}

.chat-input__textarea {
  flex: 1;
  min-height: 24px;
  max-height: 128px;
  padding: 2px 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-1);
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  transition: color var(--chat-duration-fast) ease;
}

.chat-input__textarea::placeholder {
  color: var(--color-text-4);
}

.chat-input__textarea:disabled {
  cursor: not-allowed;
}

.chat-input__actions {
  flex-shrink: 0;
  padding-bottom: 1px;
  min-width: 32px;
  min-height: 32px;
}

.chat-input__btn {
  transition: transform var(--chat-duration-fast) var(--chat-ease);
}

.chat-input__btn--send:not(:disabled):hover {
  transform: scale(1.06);
}

.chat-input__btn:active {
  transform: scale(0.94);
}

.chat-input__hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--color-text-4);
  text-align: center;
  opacity: 0.85;
}
</style>
