import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  fetchKnowledgeBase,
  fetchKnowledgeBases,
  updateKnowledgeBase,
} from '@/api/knowledge-base'
import type {
  KnowledgeBase,
  KnowledgeBaseFormData,
  KnowledgeBaseListQuery,
  KnowledgeBaseStatus,
} from '@/types/knowledge-base'

const defaultFormData = (): KnowledgeBaseFormData => ({
  name: '',
  description: '',
  tags: [],
  status: 'active',
})

export const useKnowledgeBaseStore = defineStore('knowledgeBase', () => {
  const list = ref<KnowledgeBase[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(12)
  const keyword = ref('')
  const statusFilter = ref<KnowledgeBaseStatus | ''>('')
  const sort = ref<KnowledgeBaseListQuery['sort']>('created_at_desc')

  const listLoading = ref(false)
  const listError = ref('')
  const submitting = ref(false)

  const current = ref<KnowledgeBase | null>(null)
  const detailLoading = ref(false)
  const detailError = ref('')

  const drawerVisible = ref(false)
  const editingId = ref<number | null>(null)
  const formData = ref<KnowledgeBaseFormData>(defaultFormData())

  const isEditing = computed(() => editingId.value !== null)
  const drawerTitle = computed(() => (isEditing.value ? '编辑知识库' : '新建知识库'))

  function buildQuery(): KnowledgeBaseListQuery {
    return {
      keyword: keyword.value.trim() || undefined,
      status: statusFilter.value || undefined,
      sort: sort.value,
      page: page.value,
      page_size: pageSize.value,
    }
  }

  async function loadList(force = false) {
    if (listLoading.value && !force) return
    listLoading.value = true
    listError.value = ''
    try {
      const { data } = await fetchKnowledgeBases(buildQuery())
      list.value = data.items
      total.value = data.total
      page.value = data.page
      pageSize.value = data.page_size
    } catch {
      listError.value = '加载知识库列表失败，请稍后重试'
    } finally {
      listLoading.value = false
    }
  }

  async function loadDetail(id: number) {
    detailLoading.value = true
    detailError.value = ''
    try {
      const { data } = await fetchKnowledgeBase(id)
      current.value = data
      return data
    } catch {
      detailError.value = '知识库不存在或加载失败'
      current.value = null
      return null
    } finally {
      detailLoading.value = false
    }
  }

  function openCreateDrawer() {
    editingId.value = null
    formData.value = defaultFormData()
    drawerVisible.value = true
  }

  function openEditDrawer(item: KnowledgeBase) {
    editingId.value = item.id
    formData.value = {
      name: item.name,
      description: item.description ?? '',
      tags: [...item.tags],
      status: item.status,
    }
    drawerVisible.value = true
  }

  function closeDrawer() {
    drawerVisible.value = false
    editingId.value = null
    formData.value = defaultFormData()
  }

  async function submitForm() {
    submitting.value = true
    try {
      const payload = {
        name: formData.value.name.trim(),
        description: formData.value.description.trim() || undefined,
        tags: formData.value.tags,
        status: formData.value.status,
      }

      if (isEditing.value && editingId.value !== null) {
        const { data } = await updateKnowledgeBase(editingId.value, payload)
        const index = list.value.findIndex((item) => item.id === data.id)
        if (index >= 0) list.value[index] = data
        if (current.value?.id === data.id) current.value = data
      } else {
        await createKnowledgeBase(payload)
        page.value = 1
        await loadList(true)
      }
      closeDrawer()
      return true
    } catch {
      return false
    } finally {
      submitting.value = false
    }
  }

  async function remove(id: number) {
    await deleteKnowledgeBase(id)
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    if (current.value?.id === id) current.value = null
    await loadList(true)
  }

  function setKeyword(value: string) {
    keyword.value = value
    page.value = 1
  }

  function setStatusFilter(value: KnowledgeBaseStatus | '') {
    statusFilter.value = value
    page.value = 1
  }

  function setSort(value: KnowledgeBaseListQuery['sort']) {
    sort.value = value
    page.value = 1
  }

  function setPage(value: number) {
    page.value = value
  }

  return {
    list,
    total,
    page,
    pageSize,
    keyword,
    statusFilter,
    sort,
    listLoading,
    listError,
    submitting,
    current,
    detailLoading,
    detailError,
    drawerVisible,
    editingId,
    formData,
    isEditing,
    drawerTitle,
    loadList,
    loadDetail,
    openCreateDrawer,
    openEditDrawer,
    closeDrawer,
    submitForm,
    remove,
    setKeyword,
    setStatusFilter,
    setSort,
    setPage,
  }
})
