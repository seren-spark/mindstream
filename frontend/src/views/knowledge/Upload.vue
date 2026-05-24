<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconLeft } from '@arco-design/web-vue/es/icon'
import PageContainer from '@/components/common/PageContainer.vue'
import UploadPanel from '@/components/upload/UploadPanel.vue'
import { useFileUpload } from '@/composables/useFileUpload'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'
import { ROUTE_NAMES } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const baseStore = useKnowledgeBaseStore()

const knowledgeBaseId = computed(() => Number(route.params.id))
const category = ref('')
const tagInput = ref('')

const {
  files,
  uploading,
  globalError,
  canUpload,
  successCount,
  errorCount,
  addFiles,
  removeFile,
  retryFile,
  clearCompleted,
  uploadAll,
  reset,
} = useFileUpload(() => knowledgeBaseId.value)

onMounted(async () => {
  if (Number.isNaN(knowledgeBaseId.value)) return
  await baseStore.loadDetail(knowledgeBaseId.value)
})

function handleBack() {
  reset()
  router.push({ name: ROUTE_NAMES.KNOWLEDGE_DETAIL, params: { id: knowledgeBaseId.value } })
}

function handleViewItems() {
  router.push({ name: ROUTE_NAMES.KNOWLEDGE_ITEMS, params: { id: knowledgeBaseId.value } })
}

async function handleUpload() {
  const tags = tagInput.value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)

  await uploadAll({
    category: category.value.trim() || undefined,
    tags,
    autoParse: true,
  })

  if (successCount.value > 0) {
    Message.success(`已成功导入 ${successCount.value} 个文件`)
  }
  if (errorCount.value > 0 && successCount.value === 0) {
    Message.error('全部文件上传失败，请检查格式与大小')
  }
}
</script>

<template>
  <PageContainer
    :title="baseStore.current?.name ? `${baseStore.current.name} / 导入文档` : '导入文档'"
  >
    <template #extra>
      <a-space>
        <a-button @click="handleBack">
          <template #icon><icon-left /></template>
          返回知识库
        </a-button>
        <a-button v-if="successCount" type="outline" @click="handleViewItems">
          查看知识条目
        </a-button>
      </a-space>
    </template>

    <a-result v-if="Number.isNaN(knowledgeBaseId)" status="error" title="无效的知识库 ID" />

    <template v-else>
      <a-alert
        type="info"
        title="上传完成后将自动创建知识条目并进入解析流程。TXT / Markdown 会立即解析，PDF / Word 先保存文件并等待后续解析模块。"
        style="margin-bottom: 16px"
      />

      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="12">
          <a-form-item label="分类（可选）">
            <a-input v-model="category" placeholder="如：产品文档 / API 手册" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="标签（可选，逗号分隔）">
            <a-input v-model="tagInput" placeholder="faq, 产品, 内部" />
          </a-form-item>
        </a-col>
      </a-row>

      <UploadPanel
        :files="files"
        :uploading="uploading"
        :global-error="globalError"
        :success-count="successCount"
        :error-count="errorCount"
        :can-upload="canUpload"
        @select="addFiles"
        @remove="removeFile"
        @retry="retryFile"
        @upload="handleUpload"
        @clear-completed="clearCompleted"
      />
    </template>
  </PageContainer>
</template>
