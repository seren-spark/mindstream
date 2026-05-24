<script setup lang="ts">
import { computed, ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import ItemStatusTag from '@/components/knowledge-item/ItemStatusTag.vue'
import { useKnowledgeItemStore } from '@/stores/knowledge-item'
import { ITEM_SOURCE_MAP, ITEM_STATUS_MAP } from '@/types/knowledge-item'
import { formatDateTime } from '@/utils/format'

const props = defineProps<{
  knowledgeBaseId: number
}>()

const emit = defineEmits<{
  delete: []
  saved: [itemId: number]
}>()

const store = useKnowledgeItemStore()
const editorMode = ref<'edit' | 'preview'>('edit')
const tagInput = ref('')

const hasSelection = computed(() => store.isCreating || !!store.current)
const panelTitle = computed(() => {
  if (store.isCreating) return '新建知识条目'
  if (store.current) return store.current.title
  return '条目详情'
})

function handleAddTag() {
  const value = tagInput.value.trim()
  if (!value) return
  if (store.formData.tags.includes(value)) {
    Message.warning('标签已存在')
    return
  }
  if (store.formData.tags.length >= 10) {
    Message.warning('最多 10 个标签')
    return
  }
  store.formData.tags.push(value)
  store.markDirty()
  tagInput.value = ''
}

function handleRemoveTag(tag: string) {
  store.formData.tags = store.formData.tags.filter((item) => item !== tag)
  store.markDirty()
}

function handleFieldChange() {
  store.markDirty()
}

async function handleSave() {
  if (!store.formData.title.trim()) {
    Message.warning('请输入标题')
    return
  }
  const wasCreating = store.isCreating
  const ok = await store.saveForm(props.knowledgeBaseId)
  if (ok && store.current) {
    Message.success(wasCreating ? '条目已创建' : '保存成功')
    emit('saved', store.current.id)
  } else {
    Message.error(store.saveError || '保存失败')
  }
}

async function handleRetry() {
  if (!store.current) return
  await store.changeStatus(store.current.id, 'pending')
  await store.triggerProcess(store.current.id)
  Message.success('已重新触发处理')
}
</script>

<template>
  <div class="item-editor-panel">
    <a-empty v-if="!hasSelection" description="选择左侧条目，或新建一条知识" />

    <template v-else>
      <div class="item-editor-panel__header">
        <div>
          <h3 class="item-editor-panel__title">{{ panelTitle }}</h3>
          <div v-if="store.current" class="item-editor-panel__meta">
            <ItemStatusTag :status="store.current.status" show-dot />
            <span>{{ ITEM_SOURCE_MAP[store.current.source_type] }}</span>
            <span v-if="store.current.chunk_count">分块 {{ store.current.chunk_count }}</span>
            <span>更新于 {{ formatDateTime(store.current.updated_at) }}</span>
          </div>
        </div>
        <a-space>
          <a-button
            v-if="store.current && ['pending', 'failed'].includes(store.current.status)"
            size="small"
            :loading="store.processLoading"
            @click="store.current && store.triggerProcess(store.current.id)"
          >
            触发处理
          </a-button>
          <a-button v-if="store.current?.status === 'failed'" size="small" @click="handleRetry">
            重新处理
          </a-button>
          <a-button v-if="store.current" size="small" status="danger" @click="emit('delete')">
            删除
          </a-button>
          <a-button type="primary" size="small" :loading="store.saveLoading" @click="handleSave">
            保存
          </a-button>
        </a-space>
      </div>

      <a-progress
        v-if="store.current?.status === 'processing'"
        :percent="store.current.processing_progress / 100"
        style="margin-bottom: 12px"
      />

      <a-alert
        v-if="store.current?.status === 'failed' && store.current.error_message"
        type="error"
        :title="`处理失败：${store.current.error_message}`"
        style="margin-bottom: 12px"
      />

      <a-alert
        v-if="store.current?.status === 'processing'"
        type="info"
        :title="ITEM_STATUS_MAP.processing.description"
        style="margin-bottom: 12px"
      />

      <a-form :model="store.formData" layout="vertical" class="item-editor-panel__form">
        <a-form-item label="标题" required>
          <a-input
            v-model="store.formData.title"
            placeholder="条目标题"
            :max-length="200"
            show-word-limit
            @input="handleFieldChange"
          />
        </a-form-item>

        <a-form-item label="分类">
          <a-input
            v-model="store.formData.category"
            placeholder="例如：API / 产品 / FAQ"
            @input="handleFieldChange"
          />
        </a-form-item>

        <a-form-item label="摘要">
          <a-textarea
            v-model="store.formData.summary"
            placeholder="可选，用于列表展示与 RAG 引用摘要"
            :auto-size="{ minRows: 2, maxRows: 4 }"
            @input="handleFieldChange"
          />
        </a-form-item>

        <a-form-item label="标签">
          <a-space wrap>
            <a-tag
              v-for="tag in store.formData.tags"
              :key="tag"
              closable
              @close="handleRemoveTag(tag)"
            >
              {{ tag }}
            </a-tag>
          </a-space>
          <a-space style="margin-top: 8px">
            <a-input v-model="tagInput" placeholder="添加标签" @press-enter="handleAddTag" />
            <a-button size="small" @click="handleAddTag">添加</a-button>
          </a-space>
        </a-form-item>

        <a-form-item label="正文内容">
          <a-radio-group v-model="editorMode" type="button" size="small" style="margin-bottom: 8px">
            <a-radio value="edit">编辑</a-radio>
            <a-radio value="preview">预览</a-radio>
          </a-radio-group>

          <a-textarea
            v-if="editorMode === 'edit'"
            v-model="store.formData.content"
            placeholder="支持 Markdown 语法，后续可替换为富文本/Markdown 编辑器"
            :auto-size="{ minRows: 12, maxRows: 24 }"
            @input="handleFieldChange"
          />

          <div v-else class="item-editor-panel__preview">
            <pre v-if="!store.formData.content.trim()">暂无内容</pre>
            <pre v-else>{{ store.formData.content }}</pre>
          </div>
        </a-form-item>
      </a-form>

      <div v-if="store.isDirty" class="item-editor-panel__dirty">有未保存的更改</div>
    </template>
  </div>
</template>

<style scoped>
.item-editor-panel {
  height: 100%;
  padding: 16px 20px;
  overflow: auto;
}

.item-editor-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.item-editor-panel__title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
}

.item-editor-panel__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--color-text-3);
}

.item-editor-panel__preview {
  min-height: 280px;
  padding: 12px;
  border: 1px solid var(--color-border-2);
  border-radius: 6px;
  background: var(--color-fill-1);
}

.item-editor-panel__preview pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  line-height: 1.7;
}

.item-editor-panel__dirty {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgb(var(--warning-1));
  color: rgb(var(--warning-6));
  font-size: 12px;
}
</style>
