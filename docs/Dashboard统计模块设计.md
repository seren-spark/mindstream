# Dashboard 统计模块设计

> 对齐：`会话与消息历史模块设计.md`、`引用源展示模块设计.md`、`流式问答模块设计.md`  
> 现状：**P0+P1 实现中** — overview / trend / heat / unanswered 四类统计 API + Dashboard 可视化

---

## 1. 模块职责

Dashboard 是 **知识运营驾驶舱**，不是聊天附属页。

| 角色 | 价值 |
|------|------|
| 知识运营 | 热度榜 → 优先维护高引用文档 |
| 平台管理 | 提问趋势、命中率 → 证明 RAG 被使用且有效 |
| 内容治理 | 未命中队列 → 待补知识 backlog |

闭环：**提问 → 统计 → 补库 → 命中率提升**。

---

## 2. 指标设计

| 指标 | MVP | 数据来源 |
|------|-----|----------|
| 知识库总数 | ✅ | `knowledge_bases` |
| 知识条目数 / 就绪数 | ✅ | `knowledge_items` |
| 今日提问数 | ✅ | `conversation_messages` role=user |
| RAG 命中率 | ✅ | assistant 且 `references_json` 非空 |
| 每日提问趋势 | ✅ | user 消息按日聚合 |
| 知识热度榜 | ✅ | `references_json[].knowledge_item_id` 聚合 |
| 未命中问题 | ✅ | assistant 无引用或拒答文案 |
| 平均引用数 / Agent 占比 | 增强 | 后续 query_events 表 |

**命中率定义**：assistant 完成且 `len(references_json) > 0`，与 RAG 可追溯一致，非模型自评。

---

## 3. 图表与布局

```
[ 筛选：知识库 | 近 N 天 ]
[ 4 概览卡片：KB数 | 条目数 | 今日提问 | 命中率 ]
[ 提问趋势折线 8/12 ] [ 热度横向条形 4/12 ]
[ 未命中问题表格 全宽 ]
```

- 趋势：折线 + 渐变面积（活跃度）
- 热度：横向条形（长标题可读、可排序）
- 未命中：表格（可跳转补文档）

---

## 4. API

前缀：`/api/stats`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/overview` | 概览卡片 |
| GET | `/trend` | 每日提问趋势 |
| GET | `/heat` | 知识热度榜 |
| GET | `/unanswered` | 未命中问题 |

公共 Query：`knowledge_base_id?`、`days=7`（默认 7，最大 90）

---

## 5. 前端结构

```
types/stats.ts
api/stats.ts
composables/useDashboardStats.ts
components/dashboard/
  DashboardFilterBar.vue
  StatOverviewCards.vue
  QuestionTrendChart.vue
  KnowledgeHeatRank.vue
  UnansweredTable.vue
views/dashboard/Index.vue
```

ECharts 按需引入 + `Promise.allSettled` 模块级容错。

---

## 6. 实施阶段

| 阶段 | 内容 |
|------|------|
| P0 | overview + trend + 概览卡片 |
| P1 | heat + unanswered + 筛选栏 |
| P2 | sparkline、query_events 埋点、下钻 |
