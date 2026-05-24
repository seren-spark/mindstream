# 知识条目 API

## 列表（按知识库）

`GET /api/knowledge-bases/{knowledge_base_id}/items`

Query: `keyword`, `status`, `source_type`, `category`, `tag`, `sort`, `page`, `page_size`

## 创建

`POST /api/knowledge-bases/{knowledge_base_id}/items`

手动录入有内容时默认 `ready`；文件导入默认 `pending`。

## 详情 / 更新 / 删除

- `GET /api/knowledge-items/{item_id}`
- `PUT /api/knowledge-items/{item_id}`
- `DELETE /api/knowledge-items/{item_id}`

## 状态流转

`PATCH /api/knowledge-items/{item_id}/status`

状态：`pending` → `processing` → `ready` / `failed`；支持 `disabled`。

## 触发处理（Demo）

`POST /api/knowledge-items/{item_id}/process`

模拟解析/向量化流程，后续可替换为异步任务队列。
