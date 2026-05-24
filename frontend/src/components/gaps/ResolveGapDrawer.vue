<script setup lang="ts">
import { ref, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { resolveUnansweredQuestion } from '@/api/unanswered'
import type { UnansweredQuestion } from '@/types/unanswered'

const visible = defineModel<boolean>('visible', { default: false })

const props = defineProps<{
  record: UnansweredQuestion | null
}>()

const emit = defineEmits<{
  resolved: [itemId: number]
}>()

const title = ref('')
const summary = ref('')
const content = ref('')
const submitting = ref(false)

watch(
  () => props.record,
  (r) => {
    if (!r) return
    title.value = r.suggested_title || r.query_text
    summary.value = r.suggested_summary || ''
    content.value = r.suggested_summary || ''
  },
)

async function handleSubmit() {
  if (!props.record) return
  submitting.value = true
  try {
    const { data } = await resolveUnansweredQuestion(
      props.record.knowledge_base_id,
      props.record.id,
      {
        title: title.value,
        summary: summary.value,
        content: content.value,
      },
    )
    Message.success('已沉淀为知识条目')
    visible.value = false
    emit('resolved', data.knowledge_item_id)
  } catch {
    Message.error('沉淀失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <a-drawer
    v-model:visible="visible"
    title="沉淀为知识条目"
    :width="480"
    unmount-on-close
    @cancel="visible = false"
  >
    <a-form :model="{ title, summary, content }" layout="vertical">
      <a-form-item label="标题">
        <a-input v-model="title" />
      </a-form-item>
      <a-form-item label="摘要">
        <a-textarea v-model="summary" :auto-size="{ minRows: 2, maxRows: 4 }" />
      </a-form-item>
      <a-form-item label="正文">
        <a-textarea v-model="content" :auto-size="{ minRows: 6, maxRows: 12 }" />
      </a-form-item>
    </a-form>
    <template #footer>
      <a-space>
        <a-button @click="visible = false">取消</a-button>
        <a-button type="primary" :loading="submitting" @click="handleSubmit">确认沉淀</a-button>
      </a-space>
    </template>
  </a-drawer>
</template>
