# 文档导入与上传模块设计

## 1. 模块职责

### 在知识生产链路中的位置

```
选择文件 → 上传落盘 → 创建 knowledge_item → 解析(parse) → 切片 → 向量化 → 可检索
         ↑ 本模块
```

上传模块是 **RAG 生产链路的入口**：负责把外部文档变成系统内的结构化知识条目，并触发后续解析状态流转。

### 为什么不能只是 `<input type="file">`

- 需要 **校验**（格式、大小、空文件）
- 需要 **进度与状态反馈**（上传中 / 解析中 / 成功 / 失败）
- 需要 **与 knowledge_item 绑定**（每条上传对应一条可追踪的条目）
- 需要 **结构化返回**（`knowledge_item_id`、`parse_status`），供前端展示和后续轮询
- 需要 **批量、重试、移除** 等交互，支撑 Demo 与后续扩展

---

## 2. 上传流程设计

### 前端流程

1. 用户拖拽 / 选择文件 → 本地队列校验
2. 展示 FileList（queued）
3. 点击「开始上传并解析」→ 逐文件 POST multipart
4. 每个文件：`uploading`（进度条）→ 根据响应进入 `success` / `error`
5. 展示 `knowledge_item_id` 与条目状态 Tag

### 后端流程

1. 校验 KB 存在、文件格式与大小
2. 写入 `./data/uploads/{kb_id}/{uuid}_{filename}`
3. 创建 `knowledge_item`（`source_type=file`, `status=pending`）
4. 若 `auto_parse=true`：调用 `ParserService`
   - TXT/MD：读文本 → `ready`
   - PDF/DOCX：保留文件 → `pending` + 提示信息
5. 返回 `UploadFileResult` 结构化结果

### 成功 / 失败 / 部分成功

- **单文件接口**：始终返回 `UploadFileResult`；校验失败时 `knowledge_item_id=0` + `error_message`
- **批量接口**：返回 `BatchUploadResponse { total, succeeded, failed, results[] }`
- 前端逐文件上传时，天然支持 **部分成功**

---

## 3. 文件模型设计

### 上传返回字段（`UploadFileResult`）

| 字段 | 说明 |
|------|------|
| upload_id | 本次上传 UUID |
| knowledge_item_id | 绑定的知识条目 ID |
| knowledge_base_id | 所属知识库 |
| original_filename | 原始文件名 |
| stored_filename | 磁盘存储名（uuid 前缀防冲突） |
| mime_type / file_type / size | 文件元数据 |
| item_status | 条目当前状态 |
| parse_status | completed / pending / failed |
| error_message | 错误或提示 |

### 落库字段（`knowledge_items` 扩展）

- `file_name`, `file_path`, `file_type`, `mime_type`, `file_size`
- 不单独建 `files` 表（MVP）；后续大文件/版本管理可拆 `uploaded_files`

---

## 4. 前端 UI 设计

| 区域 | 设计 |
|------|------|
| UploadTrigger | 虚线拖拽区 + hidden input，支持多选 |
| FileList / FileItem | 文件名、大小、类型、进度、状态 Tag、条目 ID |
| 错误 | 行内 `a-alert` + 重试按钮 |
| 操作 | 移除、重试、清除已完成 |

---

## 5. 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge-bases/{id}/upload` | 单文件 multipart |
| POST | `/api/knowledge-bases/{id}/upload/batch` | 多文件（最多 10 个） |

Form 字段：`file`/`files`, `category`, `tags`, `auto_parse`

---

## 6. 组件设计

- `UploadPanel` — 页面主面板
- `UploadTrigger` — 拖拽/选择
- `FileList` / `FileItem` — 队列展示
- `useFileUpload` — 队列状态与上传逻辑

---

## 7. 边界情况

| 场景 | 处理 |
|------|------|
| 格式不支持 | 前后端双重校验，明确提示支持列表 |
| 文件过大 | 默认 20MB，可配置 |
| 上传中断 | axios 超时 + 前端 error 态 + 重试 |
| 后端异常 | 统一 error 文案 |
| 同名文件 | 存储名 uuid 前缀，不冲突 |
| 重复上传 | 允许；每条上传新建独立 item |

---

## 8. Demo 取舍

| 能力 | MVP |
|------|-----|
| 多文件 | ✅ 前端队列逐文件上传 |
| 分片上传 | ❌ 后续 |
| PDF/Word 解析 | ❌ 先落盘 + pending 提示 |
| TXT/MD 解析 | ✅ 同步解析 |
| 状态轮询 | ❌ 同步返回；后续 SSE/轮询 |

---

## 9. 面试表达

**不仅是上传组件**：上传 = 文件落盘 + 元数据入库 + 条目创建 + 解析触发，是知识生产链路第一步。

**异步链路**：上传态（HTTP 进度）与条目态（pending/processing/ready）分离；响应用 `parse_status` 桥接，后续可改为任务队列 + 轮询而不改前端模型。

---

## 验证

1. 进入知识库详情 → 知识条目 →「导入文档」
2. 上传 `.md` / `.txt` → 应显示条目 ID + **可用**
3. 上传 `.pdf` → 文件已保存，条目 **待处理**，提示解析后续接入
