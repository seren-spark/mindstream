# 知识条目 API

Base URL: `http://127.0.0.1:8000/api`

## 列表

`GET /knowledge-bases/{knowledge_base_id}/items`

Query:

| 参数 | 说明 |
|------|------|
| keyword | 搜索标题/摘要/正文 |
| status | pending / processing / ready / failed / disabled |
| source_type | manual / file / ai_generated |
| category | 分类精确匹配 |
| tag | 标签包含 |
| sort | updated_at_desc（默认）/ created_at_asc / title_asc |
| page, page_size | 分页 |

## 创建

`POST /knowledge-bases/{knowledge_base_id}/items`

```json
{
  "title": "产品 FAQ",
  "source_type": "manual",
  "content": "# 常见问题\n...",
  "category": "产品文档",
  "tags": ["faq", "产品"]
}
```

## 详情

`GET /knowledge-items/{item_id}`

## 更新

`PUT /knowledge-items/{item_id}`

## 状态更新

`PATCH /knowledge-items/{item_id}/status`

```json
{ "status": "disabled" }
```

## 触发处理（Demo）

`POST /knowledge-items/{item_id}/process`

Mock：pending/failed → processing → ready（有内容）或 failed（纯文件且无解析模块）。

## 删除

`DELETE /knowledge-items/{item_id}` → 204
