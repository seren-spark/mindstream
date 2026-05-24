import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  createKnowledgeItem,
  deleteKnowledgeItem,
  fetchKnowledgeItem,
  fetchKnowledgeItems,
  triggerKnowledgeItemProcess,
  updateKnowledgeItem,
  updateKnowledgeItemStatus,
} from '@/api/knowledge-item'
import type {
  KnowledgeItem,
  KnowledgeItemFormData,
  KnowledgeItemListItem,
  KnowledgeItemListQuery,
  KnowledgeItemSourceType,
  KnowledgeItemStatus,
} from '@/types/knowledge-item'

const defaultFormData = (): KnowledgeItemFormData => ({
  title: '',
  content: '',
  summary: '',
  category: '',
  tags: [],
  source_type: 'manual',
  file_name: '',
})

export const useKnowledgeItemStore = defineStore('knowledgeItem', () => {
  const knowledgeBaseId = ref<number | null>(null)

  const list = ref<KnowledgeItemListItem[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const keyword = ref('')
  const statusFilter = ref<KnowledgeItemStatus | ''>('')
  const sourceTypeFilter = ref<KnowledgeItemSourceType | ''>('')
  const sort = ref<KnowledgeItemListQuery['sort']>('updated_at_desc')

  const listLoading = ref(false)
  const listError = ref('')

  const selectedId = ref<number | null>(null)
  const current = ref<KnowledgeItem | null>(null)
  const detailLoading = ref(false)
  const detailError = ref('')

  const isCreating = ref(false)
  const formData = ref<KnowledgeItemFormData>(defaultFormData())
  const isDirty = ref(false)

  const saveLoading = ref(false)
  const saveError = ref('')
  const processLoading = ref(false)

  const selectedListItem = computed(
    () => list.value.find((item) => item.id === selectedId.value) ?? null,
  )

  const isEditing = computed(() => isCreating.value || selectedId.value !== null)

  function resetFilters() {
    keyword.value = ''
    statusFilter.value = ''
    sourceTypeFilter.value = ''
    page.value = 1
  }

  function buildQuery(): KnowledgeItemListQuery {
    return {
      keyword: keyword.value.trim() || undefined,
      status: statusFilter.value || undefined,
      source_type: sourceTypeFilter.value || undefined,
      sort: sort.value,
      page: page.value,
      page_size: pageSize.value,
    }
  }

  function syncListItem(item: KnowledgeItem | KnowledgeItemListItem) {
    const index = list.value.findIndex((row) => row.id === item.id)
    const listItem: KnowledgeItemListItem = {
      id: item.id,
      knowledge_base_id: item.knowledge_base_id,
      title: item.title,
      source_type: item.source_type,
      status: item.status,
      summary: item.summary,
      file_name: item.file_name,
      category: item.category,
      tags: item.tags,
      chunk_count: item.chunk_count,
      processing_progress: item.processing_progress,
      error_message: item.error_message,
      created_at: item.created_at,
      updated_at: item.updated_at,
    }
    if (index >= 0) {
      list.value[index] = listItem
    }
  }

  async function loadList(kbId: number, force = false) {
    if (listLoading.value && !force) return
    knowledgeBaseId.value = kbId
    listLoading.value = true
    listError.value = ''
    try {
      const { data } = await fetchKnowledgeItems(kbId, buildQuery())
      list.value = data.items
      total.value = data.total
      page.value = data.page
      pageSize.value = data.page_size
    } catch {
      listError.value = '加载知识条目失败，请稍后重试'
    } finally {
      listLoading.value = false
    }
  }

  async function loadDetail(itemId: number) {
    detailLoading.value = true
    detailError.value = ''
    try {
      const { data } = await fetchKnowledgeItem(itemId)
      current.value = data
      selectedId.value = itemId
      syncListItem(data)
      return data
    } catch {
      detailError.value = '条目不存在或加载失败'
      current.value = null
      return null
    } finally {
      detailLoading.value = false
    }
  }

  function startCreate() {
    isCreating.value = true
    selectedId.value = null
    current.value = null
    detailError.value = ''
    formData.value = defaultFormData()
    isDirty.value = false
    saveError.value = ''
  }

  function populateFormFromCurrent() {
    if (!current.value) return
    formData.value = {
      title: current.value.title,
      content: current.value.content ?? '',
      summary: current.value.summary ?? '',
      category: current.value.category ?? '',
      tags: [...current.value.tags],
      source_type: current.value.source_type,
      file_name: current.value.file_name ?? '',
    }
    isDirty.value = false
    saveError.value = ''
  }

  async function selectItem(itemId: number) {
    if (isDirty.value) {
      return 'unsaved'
    }
    isCreating.value = false
    await loadDetail(itemId)
    populateFormFromCurrent()
    return 'ok'
  }

  function markDirty() {
    isDirty.value = true
  }

  function cancelEdit() {
    isCreating.value = false
    isDirty.value = false
    saveError.value = ''
    if (selectedId.value && current.value) {
      populateFormFromCurrent()
      return
    }
    selectedId.value = null
    current.value = null
    formData.value = defaultFormData()
  }

  async function saveForm(kbId: number) {
    saveLoading.value = true
    saveError.value = ''
    try {
      const payload = {
        title: formData.value.title.trim(),
        content: formData.value.content.trim() || undefined,
        summary: formData.value.summary.trim() || undefined,
        category: formData.value.category.trim() || undefined,
        tags: formData.value.tags,
      }

      if (isCreating.value) {
        const { data } = await createKnowledgeItem(kbId, {
          ...payload,
          source_type: formData.value.source_type,
          file_name: formData.value.file_name.trim() || undefined,
        })
        isCreating.value = false
        selectedId.value = data.id
        current.value = data
        await loadList(kbId, true)
        populateFormFromCurrent()
      } else if (selectedId.value !== null) {
        const { data } = await updateKnowledgeItem(selectedId.value, payload)
        current.value = data
        syncListItem(data)
      }

      isDirty.value = false
      return true
    } catch {
      saveError.value = '保存失败，请检查内容后重试'
      return false
    } finally {
      saveLoading.value = false
    }
  }

  async function remove(itemId: number) {
    await deleteKnowledgeItem(itemId)
    if (selectedId.value === itemId) {
      selectedId.value = null
      current.value = null
      isCreating.value = false
      formData.value = defaultFormData()
      isDirty.value = false
    }
    if (knowledgeBaseId.value !== null) {
      if (list.value.length === 1 && page.value > 1) {
        page.value -= 1
      }
      await loadList(knowledgeBaseId.value, true)
    }
  }

  async function changeStatus(itemId: number, status: KnowledgeItemStatus) {
    const { data } = await updateKnowledgeItemStatus(itemId, { status })
    if (current.value?.id === itemId) current.value = data
    syncListItem(data)
    return data
  }

  async function triggerProcess(itemId: number) {
    processLoading.value = true
    try {
      const { data } = await triggerKnowledgeItemProcess(itemId)
      if (current.value?.id === itemId) {
        current.value = data
        populateFormFromCurrent()
      }
      syncListItem(data)
      return data
    } finally {
      processLoading.value = false
    }
  }

  function setKeyword(value: string) {
    keyword.value = value
    page.value = 1
  }

  function setStatusFilter(value: KnowledgeItemStatus | '') {
    statusFilter.value = value
    page.value = 1
  }

  function setSourceTypeFilter(value: KnowledgeItemSourceType | '') {
    sourceTypeFilter.value = value
    page.value = 1
  }

  function setPage(value: number) {
    page.value = value
  }

  function reset() {
    knowledgeBaseId.value = null
    list.value = []
    total.value = 0
    selectedId.value = null
    current.value = null
    isCreating.value = false
    isDirty.value = false
    listError.value = ''
    detailError.value = ''
    saveError.value = ''
    formData.value = defaultFormData()
    resetFilters()
  }

  return {
    knowledgeBaseId,
    list,
    total,
    page,
    pageSize,
    keyword,
    statusFilter,
    sourceTypeFilter,
    sort,
    listLoading,
    listError,
    selectedId,
    current,
    detailLoading,
    detailError,
    isCreating,
    formData,
    isDirty,
    saveLoading,
    saveError,
    processLoading,
    selectedListItem,
    isEditing,
    loadList,
    loadDetail,
    startCreate,
    populateFormFromCurrent,
    selectItem,
    markDirty,
    cancelEdit,
    saveForm,
    remove,
    changeStatus,
    triggerProcess,
    setKeyword,
    setStatusFilter,
    setSourceTypeFilter,
    setPage,
    reset,
  }
})
