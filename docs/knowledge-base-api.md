# 知识库管理模块 API

Base URL: `/api/knowledge-bases`

## 列表

`GET /api/knowledge-bases`

Query:

| 参数 | 类型 | 说明 |
|------|------|------|
| keyword | string | 搜索名称/描述 |
| status | active \| disabled | 状态筛选 |
| sort | created_at_desc \| created_at_asc \| name_asc | 排序 |
| page | int | 页码，默认 1 |
| page_size | int | 每页数量，默认 12 |

Response:

```json
{
  "items": [KnowledgeBase],
  "total": 0,
  "page": 1,
  "page_size": 12
}
```

## 创建

`POST /api/knowledge-bases`

Body:

```json
{
  "name": "产品文档库",
  "description": "可选",
  "tags": ["产品", "API"],
  "status": "active"
}
```

## 详情

`GET /api/knowledge-bases/{id}`

## 更新

`PUT /api/knowledge-bases/{id}`

Body 字段均可选，只更新传入字段。

## 删除

`DELETE /api/knowledge-bases/{id}` → 204

## 错误响应

```json
{
  "detail": "Knowledge base 1 not found",
  "code": null
}
```
