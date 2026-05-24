<script setup lang="ts">
import { useRouter } from 'vue-router'
import { IconUpload } from '@arco-design/web-vue/es/icon'
import PageContainer from '@/components/common/PageContainer.vue'
import { ROUTE_NAMES } from '@/utils/constants'

const router = useRouter()
</script>

<template>
  <PageContainer title="上传知识">
    <a-upload draggable :auto-upload="false" disabled>
      <template #upload-button>
        <div class="upload-placeholder">
          <icon-upload :style="{ fontSize: '32px' }" />
          <p>拖拽文件到此处，或点击选择</p>
          <p class="upload-placeholder__hint">支持 PDF / Markdown / TXT（后续模块启用）</p>
        </div>
      </template>
    </a-upload>

    <a-space style="margin-top: 16px">
      <a-button type="primary" disabled>开始上传</a-button>
      <a-button @click="router.push({ name: ROUTE_NAMES.KNOWLEDGE_LIST })">返回列表</a-button>
    </a-space>
  </PageContainer>
</template>

<style scoped>
.upload-placeholder {
  padding: 40px 0;
  text-align: center;
  color: var(--color-text-3);
}

.upload-placeholder__hint {
  font-size: 12px;
  margin-top: 8px;
}
</style>
