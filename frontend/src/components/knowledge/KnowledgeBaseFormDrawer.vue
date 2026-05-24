<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Message } from '@arco-design/web-vue'
import { useKnowledgeBaseStore } from '@/stores/knowledge-base'

const store = useKnowledgeBaseStore()

const formRef = ref()

const rules = {
  name: [{ required: true, message: '请输入知识库名称' }],
}

const statusOptions = [
  { label: '启用', value: 'active' },
  { label: '禁用', value: 'disabled' },
]

const tagInput = ref('')

const visible = computed({
  get: () => store.drawerVisible,
  set: (value: boolean) => {
    if (!value) store.closeDrawer()
  },
})

watch(
  () => store.drawerVisible,
  (open) => {
    if (open) tagInput.value = ''
  },
)

function handleAddTag() {
  const value = tagInput.value.trim()
  if (!value) return
  if (store.formData.tags.includes(value)) {
    Message.warning('标签已存在')
    return
  }
  if (store.formData.tags.length >= 10) {
    Message.warning('最多添加 10 个标签')
    return
  }
  store.formData.tags.push(value)
  tagInput.value = ''
}

function handleRemoveTag(tag: string) {
  store.formData.tags = store.formData.tags.filter((item) => item !== tag)
}

async function handleSubmit() {
  const errors = await formRef.value?.validate()
  if (errors) return

  const ok = await store.submitForm()
  if (ok) {
    Message.success(store.isEditing ? '知识库已更新' : '知识库创建成功')
  } else {
    Message.error('保存失败，请检查输入后重试')
  }
}
</script>

<template>
  <a-drawer
    v-model:visible="visible"
    :title="store.drawerTitle"
    :width="480"
    unmount-on-close
    @cancel="store.closeDrawer()"
  >
    <a-form ref="formRef" :model="store.formData" :rules="rules" layout="vertical">
      <a-form-item label="名称" field="name" required>
        <a-input
          v-model="store.formData.name"
          placeholder="例如：产品文档库、面试资料库"
          :max-length="100"
          show-word-limit
        />
      </a-form-item>

      <a-form-item label="描述" field="description">
        <a-textarea
          v-model="store.formData.description"
          placeholder="说明该知识库的用途、覆盖范围"
          :max-length="2000"
          :auto-size="{ minRows: 3, maxRows: 6 }"
          show-word-limit
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
          <a-input
            v-model="tagInput"
            placeholder="输入标签后回车添加"
            @press-enter="handleAddTag"
          />
          <a-button type="outline" @click="handleAddTag">添加</a-button>
        </a-space>
      </a-form-item>

      <a-form-item label="状态" field="status">
        <a-radio-group v-model="store.formData.status">
          <a-radio v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </a-radio>
        </a-radio-group>
      </a-form-item>
    </a-form>

    <template #footer>
      <a-space>
        <a-button @click="store.closeDrawer()">取消</a-button>
        <a-button type="primary" :loading="store.submitting" @click="handleSubmit"> 保存 </a-button>
      </a-space>
    </template>
  </a-drawer>
</template>
