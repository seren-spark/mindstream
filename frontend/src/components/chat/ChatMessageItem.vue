<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { MarkdownRender } from 'markstream-vue'
import { IconRobot, IconUser } from '@arco-design/web-vue/es/icon'
import CitationList from '@/components/chat/CitationList.vue'
import type { ChatMessage } from '@/types/chat'
import { linkifyCitationMarkers } from '@/utils/citation'

const props = defineProps<{
  message: ChatMessage
  knowledgeBaseId?: number
}>()

const citationListRef = ref<InstanceType<typeof CitationList> | null>(null)
const contentRef = ref<HTMLElement | null>(null)
const activeCitationIndex = ref<number | null>(null)

const renderedContent = computed(() => {
  if (props.message.role !== 'assistant' || !props.message.content) return ''
  const linked =
    props.message.status !== 'streaming' && props.message.citations?.length
      ? linkifyCitationMarkers(props.message.content, props.message.citations)
      : props.message.content
  return linked
})

const showCitations = computed(
  () =>
    !!props.message.citations?.length &&
    props.message.status !== 'streaming' &&
    !!props.knowledgeBaseId,
)

watch(activeCitationIndex, async () => {
  await nextTick()
  const root = contentRef.value
  if (!root) return
  root.querySelectorAll('a[href^="#cite-"]').forEach((el) => el.classList.remove('cite-ref-active'))
  if (activeCitationIndex.value == null) return
  root
    .querySelector(`a[href="#cite-${activeCitationIndex.value}"]`)
    ?.classList.add('cite-ref-active')
})

function onMarkdownClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  const anchor = target.closest('a[href^="#cite-"]') as HTMLAnchorElement | null
  if (!anchor) return
  event.preventDefault()
  const index = Number(anchor.getAttribute('href')?.replace('#cite-', ''))
  if (Number.isNaN(index)) return
  activeCitationIndex.value = index
  citationListRef.value?.scrollToCitation(index)
}

function onCitationHighlight(index: number | null) {
  activeCitationIndex.value = index
}
</script>

<template>
  <div class="msg-row" :class="`msg-row--${message.role}`">
    <div v-if="message.role === 'assistant'" class="msg-row__avatar msg-row__avatar--bot">
      <IconRobot />
    </div>

    <div class="msg-row__body">
      <div v-if="message.role === 'user'" class="msg-bubble msg-bubble--user">
        {{ message.content }}
      </div>

      <div v-else class="msg-bubble msg-bubble--assistant">
        <Transition name="ui-fade" mode="out-in">
          <div
            v-if="message.status === 'streaming' && !message.content"
            key="loading"
            class="msg-bubble__loading"
          >
            <span class="msg-bubble__dots" aria-hidden="true"> <span /><span /><span /> </span>
            <span>正在检索并生成…</span>
          </div>

          <div
            v-else-if="message.content"
            ref="contentRef"
            key="content"
            class="msg-bubble__content"
            @click="onMarkdownClick"
          >
            <MarkdownRender
              :content="renderedContent"
              :max-live-nodes="0"
              :batch-rendering="true"
              :typewriter="message.status === 'streaming'"
              class="msg-bubble__markdown markstream-vue"
              :class="{ 'msg-bubble__markdown--linked': showCitations }"
            />
            <span
              v-if="message.status === 'streaming'"
              class="msg-bubble__cursor"
              aria-hidden="true"
            />
          </div>
        </Transition>

        <Transition name="ui-fade">
          <a-alert
            v-if="message.status === 'error' || message.status === 'cancelled'"
            :type="message.status === 'cancelled' ? 'warning' : 'error'"
            :title="message.errorMessage || '生成失败'"
            banner
            class="msg-bubble__alert"
          />
        </Transition>

        <CitationList
          v-if="showCitations"
          ref="citationListRef"
          :citations="message.citations!"
          :knowledge-base-id="knowledgeBaseId!"
          @highlight="onCitationHighlight"
        />
      </div>
    </div>

    <div v-if="message.role === 'user'" class="msg-row__avatar msg-row__avatar--user">
      <IconUser />
    </div>
  </div>
</template>

<style scoped>
.msg-row {
  display: flex;
  gap: 12px;
  margin-bottom: 28px;
  align-items: flex-start;
}

.msg-row--user {
  flex-direction: row-reverse;
}

.msg-row__avatar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  font-size: 16px;
  transition: transform var(--ui-duration) var(--ui-ease);
}

.msg-row:hover .msg-row__avatar {
  transform: scale(1.02);
}

.msg-row__avatar--bot {
  color: rgb(var(--primary-6));
  background: linear-gradient(145deg, rgb(var(--primary-1)), rgb(var(--primary-2)));
  box-shadow: 0 2px 8px rgba(var(--primary-6), 0.12);
}

.msg-row__avatar--user {
  color: var(--color-text-2);
  background: var(--color-fill-3);
}

.msg-row__body {
  flex: 1;
  min-width: 0;
  max-width: calc(100% - 46px);
}

.msg-row--user .msg-row__body {
  display: flex;
  justify-content: flex-end;
}

.msg-bubble--user {
  display: inline-block;
  max-width: 100%;
  padding: 11px 16px;
  font-size: 14px;
  line-height: 1.65;
  color: #fff;
  white-space: pre-wrap;
  word-break: break-word;
  background: linear-gradient(
    145deg,
    color-mix(in srgb, rgb(var(--primary-6)) 90%, white),
    rgb(var(--primary-6))
  );
  border-radius: 20px 20px 6px 20px;
  box-shadow: 0 3px 16px rgba(var(--primary-6), 0.16);
  transition: box-shadow var(--ui-duration) var(--ui-ease);
}

.msg-row--user:hover .msg-bubble--user {
  box-shadow: 0 5px 20px rgba(var(--primary-6), 0.22);
}

.msg-bubble--assistant {
  padding: 4px 0;
}

.msg-bubble__loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  font-size: 13px;
  color: var(--color-text-3);
}

.msg-bubble__dots {
  display: inline-flex;
  gap: 5px;
}

.msg-bubble__dots span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgb(var(--primary-6));
  opacity: 0.45;
  animation: dot-wave 1.4s var(--ui-ease) infinite;
}

.msg-bubble__dots span:nth-child(2) {
  animation-delay: 0.18s;
}

.msg-bubble__dots span:nth-child(3) {
  animation-delay: 0.36s;
}

@keyframes dot-wave {
  0%,
  70%,
  100% {
    opacity: 0.35;
    transform: translateY(0) scale(0.9);
  }
  35% {
    opacity: 1;
    transform: translateY(-5px) scale(1);
  }
}

.msg-bubble__content {
  font-size: 14px;
  line-height: 1.75;
  color: var(--color-text-1);
}

.msg-bubble__markdown :deep(p) {
  margin: 0 0 0.75em;
}

.msg-bubble__markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.msg-bubble__markdown :deep(pre) {
  border-radius: 10px;
  font-size: 13px;
}

/* 正文引用上标：灰色圆角数字，类似飞书/豆包 */
.msg-bubble__markdown--linked :deep(a[href^='#cite-']) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  margin: 0 2px;
  padding: 0 5px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  vertical-align: super;
  color: var(--color-text-2) !important;
  text-decoration: none !important;
  background: var(--color-fill-3);
  border-radius: 10px;
  transition:
    background var(--ui-duration-fast) var(--ui-ease),
    color var(--ui-duration-fast) var(--ui-ease),
    transform var(--ui-duration-fast) var(--ui-ease);
}

.msg-bubble__markdown--linked :deep(a[href^='#cite-']:hover),
.msg-bubble__markdown--linked :deep(a.cite-ref-active) {
  color: rgb(var(--primary-6)) !important;
  background: rgb(var(--primary-1));
  transform: translateY(-1px);
}

.msg-bubble__cursor {
  display: inline-block;
  width: 2px;
  height: 1.05em;
  margin-left: 2px;
  vertical-align: text-bottom;
  background: rgb(var(--primary-6));
  border-radius: 1px;
  animation: cursor-blink 1.1s ease-in-out infinite;
}

@keyframes cursor-blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.2;
  }
}

.msg-bubble__alert {
  margin-top: 10px;
}
</style>
