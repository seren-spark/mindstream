# 知识条目管理模块设计

## 1. 模块定位

### 条目与知识库的关系

- **知识库（Knowledge Base）**：逻辑容器，定义检索范围、标签体系与启用状态。
- **知识条目（Knowledge Item）**：容器内的最小内容单元，承载实际文本/文件元数据，并驱动后续解析、切片、向量化。

关系：`1 个知识库 : N 个知识条目`，条目通过 `knowledge_base_id` 外键归属知识库，删除知识库时级联删除条目。

### 条目在 RAG 链路中的作用

```
录入/导入 → 元数据入库(pending) → 解析/切片/向量化(processing) → 可用(ready) → 检索引用
```

条目是 RAG 链路的**源头对象**：聊天检索时返回的 references 应能回溯到 `knowledge_item.id`（及 chunk 子表，后续扩展）。

---

## 2. 数据模型设计

### knowledge_items 表字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | 主键 |
| knowledge_base_id | int FK | 所属知识库 |
| title | varchar(200) | 标题 |
| source_type | varchar(20) | 来源：manual / file / ai_generated |
| status | varchar(20) | 处理状态 |
| content | text | 正文（手动录入 / 解析结果） |
| summary | text | 摘要（可自动生成） |
| file_name | varchar(255) | 导入文件名 |
| file_path | varchar(500) | 文件存储路径（预留） |
| file_type | varchar(50) | 文件类型（预留） |
| category | varchar(100) | 分类 |
| tags | json | 标签数组 |
| chunk_count | int | 切片数量（演示用） |
| processing_progress | int | 处理进度 0-100 |
| error_message | text | 失败原因 |
| created_at / updated_at | datetime | 时间戳 |

### source_type 是否需要

**需要。** 统一抽象三种来源，前端用同一列表/详情展示，仅通过 `source_type` 区分展示与默认状态：

| 值 | 含义 | 典型初始状态 |
|----|------|--------------|
| manual | 手动录入 | 有内容 → ready；无内容 → pending |
| file | 文档导入 | pending |
| ai_generated | AI 生成（预留） | pending |

### status 状态机

```
pending ──→ processing ──→ ready
   │              │
   │              └──→ failed
   ├──→ ready (手动有内容时跳过流水线)
   └──→ disabled

ready ──→ disabled
failed ──→ pending (重试)
disabled ──→ pending (重新启用)
```

后端 `ALLOWED_STATUS_TRANSITIONS` 约束非法跳转；`POST /knowledge-items/{id}/process` 提供演示用 mock 处理。

### 字段必要性

- **content**：手动录入与解析结果共用，必需。
- **summary**：列表摘要展示，可自动生成，建议保留。
- **file_name**：文件导入场景展示，手动录入可为空。
- **error_message**：失败态演示与排障，必需。

### tags 挂载方式

MVP：**JSON 数组内嵌于条目表**，与知识库 tags 一致，不单独拆表。后续若需全局标签云可再抽 `tags` + `item_tags` 关联表。

---

## 3. 页面结构设计

### 布局：左列表 + 右详情/编辑

在知识库详情页「知识条目」Tab 内采用 **Master-Detail**：

- 左 8 列：搜索、状态/来源筛选、条目列表、分页
- 右 16 列：详情元信息 + 编辑器

适合面试讲解：列表管**浏览与筛选**，右侧管**编辑与状态操作**，状态互不干扰。

### 列表项展示字段

- 标题、状态 Tag（处理中带进度）
- 摘要或文件名
- 来源、分类、相对更新时间

### 搜索 / 筛选

- 关键词：title / summary / content
- 状态过滤、来源过滤
- 分页（默认 20 条/页）

### 状态可视化

| 状态 | 颜色 | 交互 |
|------|------|------|
| pending | gray | 可「触发处理」 |
| processing | blue + spin + 进度条 | 只读 |
| ready | green | 可编辑、可禁用 |
| failed | red + error alert | 可重试 |
| disabled | orange | 可重新启用 |

---

## 4. 编辑体验设计

### 录入形式

MVP：**textarea + 编辑/预览切换**（预留 Markdown 编辑器接口）。  
原因：实现快、可演示、后续可替换为 `@vueup/vue-quill` 或 `md-editor-v3` 而不改数据模型。

### 预览

Radio 切换「编辑 / 预览」，预览区 `pre-wrap` 展示正文（后续接 markdown-it 渲染）。

### 自动保存草稿

MVP **不做**服务端草稿；用 `isDirty` 标记未保存。  
扩展：localStorage 键 `kb_item_draft_{kbId}` 或 `draft_content` 字段。

### 未保存离开提醒

- 切换列表条目：`Modal` 确认
- 路由离开：`onBeforeRouteLeave`
- 组件卸载：`store.reset()`

---

## 5. API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge-bases/{kb_id}/items` | 分页列表 |
| POST | `/api/knowledge-bases/{kb_id}/items` | 创建 |
| GET | `/api/knowledge-items/{id}` | 详情 |
| PUT | `/api/knowledge-items/{id}` | 更新 |
| PATCH | `/api/knowledge-items/{id}/status` | 状态变更 |
| POST | `/api/knowledge-items/{id}/process` | 触发处理（mock） |
| DELETE | `/api/knowledge-items/{id}` | 删除 |

标签：随条目 CRUD 的 `tags` 字段提交，**MVP 不拆独立标签 API**。

---

## 6. 前端组件拆分

| 组件 | 职责 |
|------|------|
| `KnowledgeItemManager` | 页面编排、左右布局 |
| `KnowledgeItemListPanel` | 列表、筛选、分页 |
| `KnowledgeItemDetailPanel` | 详情头、操作栏、状态区 |
| `KnowledgeItemEditor` | 表单与预览 |
| `KnowledgeItemStatusTag` | 状态 Tag + 进度 |
| `KnowledgeItemTags` | 标签输入/展示 |

Store：`useKnowledgeItemStore`  
Composable：`useKnowledgeItemEditor`（脏检查、离开确认）

---

## 7. 状态流设计

| 维度 | 状态变量 | 说明 |
|------|----------|------|
| 页面加载 | listLoading / detailLoading | 列表与详情分离 |
| 编辑 | isCreating / isDirty / formData | 创建与编辑共用表单 |
| 保存 | saveLoading / saveError | 提交反馈 |
| 条目处理 | current.status / processLoading | 与编辑态解耦 |
| 错误 | listError / detailError / error_message | 分层展示 |

**避免混乱的原则**：

1. 条目 `status`（业务）≠ UI `loading`（交互）
2. 列表用 `KnowledgeItemListItem`，详情用完整 `KnowledgeItem`
3. 选中条目以 `selectedId` 为准，不直接用列表行做编辑源

---

## 8. 实现建议

### MVP 已完成

- 条目 CRUD、列表筛选、状态展示
- 手动录入 + 编辑预览切换
- mock 处理接口（文件导入会提示解析未接入）
- 左列表右详情嵌入知识库详情 Tab

### 预留、未实现

- 真实文件上传与 `parser_service`
- ChromaDB 向量写入与 chunk 表
- Markdown 富渲染、自动草稿、SSE 处理进度

### 演示路径

1. 新建手动条目（有正文）→ 直接 **可用**
2. 新建 file 类型条目（仅文件名）→ **待处理** → 点「触发处理」→ 失败提示 / 或补内容后成功
3. 筛选「失败」→ 查看 error_message → 重试

---

## 9. 面试表达

### 状态机

> 条目状态描述的是**内容处理生命周期**，不是 UI loading。我用枚举 + 转移表约束后端，前端用 StatusTag 映射颜色与文案，把「待处理→处理中→可用」做成可演示闭环。

### 手动录入与文件导入的统一抽象

> 无论来源，都是一条 `knowledge_item` 记录，用 `source_type` 区分入口，用同一套 CRUD 和列表 UI。区别只在初始 `status` 和是否展示 `file_name`，这样后续加 URL 抓取、AI 生成不用改页面结构。

### 前端交互

> Master-Detail + 脏检查离开确认 + 分 store 管理列表/详情/保存态，保证演示时操作路径清晰，也方便追问时画状态图。
