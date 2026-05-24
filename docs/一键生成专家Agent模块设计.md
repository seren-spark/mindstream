# 一键生成专家 Agent 模块设计（生产级）

> 对齐：`RAG-Prompt组装模块设计.md`、`会话与消息历史模块设计.md`  
> 原则：**可配置、可版本化、可审计**；生成是入口，不是一次性脚本

---

## 1. 模块职责

### 专家 Agent 是什么

绑定单个知识库的**持久化问答配置实体**，包含：

- 面向用户的 **Profile**（名称、描述、人设、欢迎语、示例问题、形象）
- 面向模型的 **Prompt 配置**（分层组装，而非一整段不可维护的自由文本）
- 独立 **对话入口**与**隔离的会话空间**（`conversation.agent_id`）

### 与普通知识库聊天

| 维度 | 普通 `/chat` | 专家 Agent |
|------|-------------|------------|
| System | 平台默认 `SYSTEM_INSTRUCTION` | **Agent 人设层** + 平台 **RAG 基座层**（不可被生成覆盖） |
| 配置 | 无持久化 | DB 实体 + 版本历史 |
| 会话 | `agent_id IS NULL` | `agent_id` 必填，列表隔离 |
| 生成 | — | 异步任务 + 可编辑 + 可重新生成新版本 |
| 产品 | 通用检索问答 | **领域专家服务**（同一 RAG，不同服务角色） |

### 差异化价值（非 Demo 话术）

- **配置即产品**：Agent 是一等公民资源，可列表、编辑、归档、版本对比  
- **Prompt 工程化**：生成只产出 Profile；运行时 Prompt 由**分层模板**组装，保证引用/拒答规则不被 LLM 生成破坏  
- **可追溯**：`generation_jobs` 记录采样来源、模型、原始 JSON，便于审计与重放  

---

## 2. 数据模型（生产级）

### 2.1 `expert_agents` — 当前生效配置

```sql
CREATE TABLE expert_agents (
  id                  VARCHAR(36) PRIMARY KEY,
  knowledge_base_id   INTEGER NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  slug                VARCHAR(64) NOT NULL,
  name                VARCHAR(100) NOT NULL,
  description         VARCHAR(500) NOT NULL,
  persona             TEXT NOT NULL,
  tone                VARCHAR(50) NOT NULL DEFAULT 'professional',  -- professional | concise | detailed
  custom_instructions TEXT,           -- 用户可编辑的补充指令（可选，有长度上限）
  welcome_message     VARCHAR(800) NOT NULL,
  suggested_questions JSON NOT NULL,  -- 3~5 条
  avatar_type         VARCHAR(20) NOT NULL DEFAULT 'emoji',        -- emoji | preset | upload
  avatar_value        VARCHAR(500) NOT NULL DEFAULT '🤖',        -- emoji 或 URL
  status              VARCHAR(20) NOT NULL DEFAULT 'draft',      -- draft | published | archived
  current_version_id  VARCHAR(36),    -- 指向 agent_versions
  published_at        TIMESTAMP,
  created_at          TIMESTAMP NOT NULL,
  updated_at          TIMESTAMP NOT NULL,
  UNIQUE (knowledge_base_id, slug)
);
CREATE INDEX idx_agents_kb_status ON expert_agents(knowledge_base_id, status);
```

**不再存储单一 `system_prompt` 长文本为唯一真相**——运行时由 `AgentPromptComposer` 从基座 + agent 字段组装；`agent_versions.snapshot` 存组装结果用于回放。

### 2.2 `agent_versions` — 版本历史

```sql
CREATE TABLE agent_versions (
  id              VARCHAR(36) PRIMARY KEY,
  agent_id        VARCHAR(36) NOT NULL REFERENCES expert_agents(id) ON DELETE CASCADE,
  version_number  INTEGER NOT NULL,
  source          VARCHAR(20) NOT NULL,  -- generated | manual_edit | regenerate
  profile_snapshot JSON NOT NULL,        -- 生成或编辑时的完整 profile
  prompt_snapshot  TEXT NOT NULL,        -- 组装后的完整 system prompt（只读存档）
  generation_job_id VARCHAR(36),
  created_at      TIMESTAMP NOT NULL,
  UNIQUE (agent_id, version_number)
);
```

### 2.3 `agent_generation_jobs` — 异步生成任务

```sql
CREATE TABLE agent_generation_jobs (
  id                  VARCHAR(36) PRIMARY KEY,
  knowledge_base_id   INTEGER NOT NULL,
  agent_id            VARCHAR(36),       -- 生成完成后关联
  status              VARCHAR(20) NOT NULL,  -- pending | running | succeeded | failed
  stage               VARCHAR(50),       -- sampling | profiling | composing | saving
  progress_message    VARCHAR(200),
  input_snapshot      JSON NOT NULL,     -- KB 元数据 + 采样条目 id 列表
  result_profile      JSON,              -- LLM 原始 JSON
  error_message       TEXT,
  model_name          VARCHAR(100),
  started_at          TIMESTAMP,
  finished_at         TIMESTAMP,
  created_at          TIMESTAMP NOT NULL
);
```

大库生成可能 10~30s，**必须异步**：POST 返回 `job_id`，前端轮询或 SSE 任务状态。

### 2.4 `conversations` 扩展

```sql
ALTER TABLE conversations ADD COLUMN agent_id VARCHAR(36) NULL REFERENCES expert_agents(id);
CREATE INDEX idx_conv_agent ON conversations(agent_id, updated_at DESC);
```

- 普通聊天：`agent_id IS NULL`  
- Agent 页：`agent_id` 必填，API 校验 agent 属于同一 `knowledge_base_id`  

---

## 3. 生成流程（生产级）

```
POST /agents/generate  → 创建 job (pending)
    ↓
[异步 Worker / 同请求 async 任务]
  Stage 1 sampling
    - 校验 KB：status=active，ready 条目数 ≥ 阈值（否则 400）
    - 分层采样：按 category/tag 分组，每组取 1~2 条 summary
    - 补充 chunk 级 excerpt（高 token 条目取首 chunk highlight）
    - 写入 input_snapshot（条目 id、标题、摘要 hash）
  Stage 2 profiling
    - LLM structured output（JSON schema / function calling）
    - Pydantic 校验 + 敏感词/长度校验
    - 失败可重试 1 次（temperature 降低）
  Stage 3 composing
    - AgentPromptComposer.compose(agent_fields, kb_name)
    - 写入 prompt_snapshot，**不**把 RAG 规则交给 LLM 自由撰写
  Stage 4 saving
    - INSERT expert_agents (status=draft) + agent_versions v1
    - job → succeeded
    ↓
前端：job 完成 → 跳转 Agent 详情/编辑页 → 用户确认 → PATCH publish
```

| 与 Demo 方案差异 | 生产级 |
|------------------|--------|
| 同步 3~8s 返回 | **异步 job** + 阶段进度 |
| 仅 8 条 summary | **分层采样** + chunk excerpt + 条目数校验 |
| 直接 published | 默认 **draft**，人工确认后 publish |
| 覆盖旧 Agent | **多 Agent 并存** + 版本历史 |
| 单一 system_prompt 字段 | **分层组装** + version snapshot |

---

## 4. Prompt 架构（核心）

### 4.1 三层组装（不可省略）

```
┌─────────────────────────────────────┐
│ Layer 0: RAG_BASE（平台常量，不可编辑） │  拒答、引用 [n]、仅参考知识、禁止泄露
├─────────────────────────────────────┤
│ Layer 1: AGENT_PERSONA（生成+可编辑）  │  name、persona、tone、custom_instructions
├─────────────────────────────────────┤
│ Layer 2: RUNTIME_CONTEXT（动态）      │  知识库名、参考知识块（现有 build_context_block）
└─────────────────────────────────────┘
```

```python
class AgentPromptComposer:
    @staticmethod
    def compose(*, kb_name: str, agent: ExpertAgent, context_block: str) -> str:
        persona = f"你是{agent.name}。{agent.persona}\n语气风格：{agent.tone}。"
        if agent.custom_instructions:
            persona += f"\n\n补充说明：{agent.custom_instructions}"
        return (
            f"{persona}\n\n{RAG_BASE_RULES}\n\n"
            f"当前知识库：{kb_name}\n\n## 参考知识\n\n{context_block or '（暂无）'}"
        )
```

`PromptBuilderService.build` 增加：

- `agent: ExpertAgent | None`
- 有 agent 时：**Layer 0+1 由 Composer 处理**，替换默认 `SYSTEM_INSTRUCTION` 的人设部分，**RAG_BASE 与现网一致**

### 4.2 生成 Profile 的 Meta-Prompt

- 输出 **严格 JSON Schema**（Pydantic `AgentProfileGenerated`）  
- **禁止** LLM 输出 system_prompt 全文——只产 profile 字段  
- 增加 `tone` enum、`expertise_tags`（与 KB tags 对齐校验）  
- 失败重试 + 结构化解析错误写入 job.error_message  

### 4.3 用户编辑后的 Prompt 安全

- `custom_instructions` max 1000 字，过滤「忽略以上规则」类注入模式（简单 denylist）  
- 编辑后重新 `compose` + 存新版本 `agent_versions`  

---

## 5. API 设计（完整）

前缀：`/api/knowledge-bases/{kb_id}/agents`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/generate` | 创建 generation_job，返回 `{ job_id }` |
| GET | `/generate/{job_id}` | 轮询任务状态 / 结果 |
| GET | `/` | 列表，filter `status`，分页 |
| POST | `/` | 手动创建空 Agent（draft） |
| GET | `/{agent_id}` | 详情（含 current_version 摘要） |
| PATCH | `/{agent_id}` | 编辑 profile / custom_instructions |
| POST | `/{agent_id}/publish` | draft → published |
| POST | `/{agent_id}/archive` | 归档 |
| POST | `/{agent_id}/regenerate` | 新建 job，完成后 increment version |
| GET | `/{agent_id}/versions` | 版本列表 |
| GET | `/{agent_id}/versions/{vid}` | 版本详情（prompt_snapshot 只读） |
| DELETE | `/{agent_id}` | 仅 draft 可物理删；published 走 archive |

**对话**（复用 stream，扩展校验）：

```
POST /knowledge-bases/{kb_id}/chat/stream
{
  "query": "...",
  "conversation_id": "...",
  "agent_id": "uuid",   // Agent 页必填
  "history": [...],
  "top_k": 5
}
```

服务端：

1. 校验 `agent.status == published`  
2. 校验 `agent.knowledge_base_id == kb_id`  
3. `ConversationService` 创建会话时写入 `agent_id`  

---

## 6. 前端（产品级，非单按钮）

### 6.1 信息架构

```
知识库详情
  └─ Tab「专家助手」
       ├─ Agent 卡片列表（published / draft）
       ├─ 「一键生成专家」→ 生成向导 Modal
       └─ 「手动创建」

/agents/:agentId
  └─ Agent 详情（编辑 persona、welcome、示例问题、发布）

/agents/:agentId/chat
  └─ 独立对话（侧栏会话 filter agent_id，顶栏 Agent 身份）
```

### 6.2 生成向导（非 Loading 了事）

1. 前置检查：条目数不足 → 引导去上传  
2. 提交 → 显示 **阶段进度**（采样 / 人设 / 组装 / 保存）  
3. 成功 → **预览页**：展示 name、persona、welcome、示例问题、**试答一条**（可选）  
4. 用户 **编辑** → **发布** → 进入对话  

### 6.3 与普通聊天复用

- 组件：`ChatMessageItem`、`ChatInput`、`ChatSidebar`、`useChatStream`  
- Store：`useChatSessionStore` 增加 `agentId`，API 带 `agent_id`  
- 路由：`/agents/:agentId/chat?conversationId=`  

---

## 7. 服务与代码结构

```
backend/app/
  models/agent.py              # ExpertAgent, AgentVersion, AgentGenerationJob
  schemas/agent.py
  services/
    agent_service.py           # CRUD, publish, archive
    agent_generator_service.py # 采样 + LLM profile + job 状态机
    agent_prompt_composer.py   # 三层 prompt 组装
  api/agent.py
  api/chat.py                  # 扩展 agent_id 校验与 compose

frontend/src/
  api/agent.ts
  stores/agent.ts
  views/agent/Detail.vue       # 编辑 / 发布
  views/agent/Chat.vue         # 独立对话
  views/knowledge/AgentPanel.vue  # KB 详情 Tab
  components/agent/
    AgentCard.vue
    AgentGenerateWizard.vue
    AgentProfileForm.vue
```

---

## 8. 面试表达（生产级）

> Agent 不是一段临时 prompt，而是**带版本的知识库服务配置**。生成走异步任务，采样有分层策略和 audit snapshot；运行时 Prompt 分三层——平台 RAG 基座不可被生成覆盖，中间是人设层，最后是动态检索 context。发布前默认 draft，支持编辑和版本回滚。对话与会话通过 agent_id 隔离，和普通聊天共用 SSE 与引用 UI，但配置层是完整产品能力。

---

## 9. 实施路线图

| 阶段 | 交付 | 说明 |
|------|------|------|
| **P0** | 表 + Composer + CRUD + generate job + publish | 无简化单 Agent 限制 |
| **P1** | Agent 详情/编辑 + 版本列表 + conversation.agent_id | 会话隔离 |
| **P2** | 独立 Chat 页 + KB Tab + 生成向导 + 试答预览 | 完整 UX |
| **P3** | regenerate 新版本 + prompt 对比 + 条目数策略可配置 | 运维增强 |

**明确不做 Demo 妥协**：不限每 KB 一个 Agent；不跳过 draft/publish；不用 emoji 替代完整 avatar 模型；不把 system_prompt 完全交给 LLM 生成。

---

## 10. 验证清单

1. KB 无 ready 条目时生成被拒绝并提示  
2. 生成 job 可轮询阶段，失败有 error_message  
3. draft 可编辑，publish 后才可对话  
4. Agent 对话与普通聊天会话列表隔离  
5. 编辑后新版本 prompt_snapshot 可追溯  
6. 运行时引用 [n]、拒答行为与平台基座一致  
7. archived Agent 不可发起新对话  
