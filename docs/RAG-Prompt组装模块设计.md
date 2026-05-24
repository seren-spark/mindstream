# RAG Prompt 组装模块设计

> 对齐：`混合检索模块设计.md`、`文本切片模块设计.md`  
> 当前实现：`backend/app/services/prompt_builder_service.py`

---

## 1. 模块职责定义

### 在 RAG 链路中的位置

```
用户 query → 混合检索 → 【Prompt 组装】 → LLM 调用 → 解析引用 → 前端展示
                            ↑ 本模块
```

Prompt 组装模块负责：把 **System 约束 + 参考知识 + 历史对话 + 当前问题** 组织成 LLM 可消费的消息结构，并输出 **引用索引 ↔ chunk_id** 映射供前端卡片使用。

### 为什么不能写死在聊天接口里

| 写死接口内 | 独立 PromptBuilder |
|-----------|-------------------|
| 改模板要动 API 代码 | 模板集中维护、可 A/B |
| 无法单测 prompt 输出 | 给定 hits/history 即可断言 |
| 裁剪逻辑与 HTTP 耦合 | 上下文/token 预算可配置 |
| 引用映射散落 | `citations[]` 与 `[1][2]` 一一对应 |

---

## 2. Prompt 结构设计

### 四层区块

| 区块 | 角色 | 内容 |
|------|------|------|
| **System** | 全局约束 | 仅基于参考知识、拒答规则、引用格式、中文结构化 |
| **Context** | 检索知识 | `[1] 来源：…\n正文` 编号块 |
| **History** | 多轮对话 | 最近 N 轮 user/assistant |
| **User Query** | 当前问题 | 用户本轮输入 |

### OpenAI 风格消息数组

```json
[
  { "role": "system", "content": "<系统指令 + 参考知识>" },
  { "role": "user", "content": "..." },
  { "role": "assistant", "content": "..." },
  { "role": "user", "content": "<当前问题>" }
]
```

Demo 将 **参考知识嵌入 System**（约束更强）；History 以标准多轮消息插入。

---

## 3. 模板细化

### 必须基于上下文

> 你只能根据下方「参考知识」回答问题。不得使用参考知识以外的常识或臆测补全。

### 知识不足时拒答

> 若参考知识中没有足够依据，请明确回答：「根据现有知识库资料，无法找到相关信息」，并简要说明缺失什么，不要编造。

### 引用编号

> 关键事实后标注引用编号，格式为 [1]、[2]，编号必须与「参考知识」中的序号一致。每条引用至少对应一处具体依据。

### 中文结构化

> 使用简体中文。优先用分点或短段落组织答案，先结论后依据。

---

## 4. 历史对话策略

| 参数 | Demo 默认 | 说明 |
|------|-----------|------|
| `rag_max_history_turns` | **3** | 3 轮 = 最多 6 条消息 |
| 滑动窗口 | 保留最近 N 轮 | 丢弃更早的 |
| 压缩 | Demo 不做 | 后续可用摘要压缩 |

**不能无限堆历史：** 占用 context 窗口、引入无关话题、增加幻觉与成本。

---

## 5. 上下文裁剪策略

| 参数 | Demo 默认 | 说明 |
|------|-----------|------|
| `rag_max_context_chars` | **6000** | 参考知识总字符上限 |
| `rag_chunk_max_chars` | **800** | 单 chunk 截断长度 |
| 裁剪顺序 | 低分 chunk 先截/丢 | 按 RRF score 降序保留 |

**流程：**

1. hits 已按 score 排序（检索模块保证）
2. 单 chunk 超 `chunk_max_chars` → 截断 + `…`
3. 总长超 `max_context_chars` → 从尾部低分项开始丢弃
4. 至少保留 1 条（若有），否则 Context 为空 → 触发拒答指引

---

## 6. 与前端引用卡片协同

```
Prompt 中 [1]  ←→  citations[0].index == 1  ←→  chunk_id  ←→  引用卡片
```

`PromptBuildResult.citations` 与 Context 编号严格对齐，前端解析回答中的 `[n]` 即可高亮对应卡片。

---

## 7. API

```
POST /api/knowledge-bases/{id}/prompt/build
```

预览 Prompt（不调用 LLM），用于调试与答辩演示。

---

## 8. 面试表达

> Prompt 不是随便写的 system 字符串，而是带约束的模板：只允许基于检索 context 回答，不足则拒答，事实用 [1][2] 标注。PromptBuilder 独立出来，输出 messages 和 citations 映射，和前端引用卡片一一对应——这样 hallucination 可控，引用可解释，模板改起来也不动聊天 API。

---

## 9. 验证清单

1. `prompt/build` 返回 system + messages + citations
2. citations[i].index 与 context 中 [i+1] 一致
3. 超长 chunk / 超长 context 被裁剪
4. 历史超过 3 轮时只保留最近 3 轮
5. 无检索结果时 prompt 含拒答指引
