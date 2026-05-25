# AI 知识库管理平台

> 本地可运行的 RAG 知识库应用，覆盖文档入库、向量检索、流式问答与知识运营全流程。

## 功能特性

- **知识库与条目管理** — 多知识库隔离，支持手动录入与文件导入
- **文档处理流水线** — 上传 → 解析 → 切片 → 向量化，状态可追踪、失败可重试
- **混合检索** — 向量检索与关键词检索 RRF 融合
- **流式 RAG 问答** — SSE 实时输出，支持引用溯源与会话历史
- **专家 Agent** — 基于知识库一键生成对话人设
- **运营 Dashboard** — 问答热度、条目统计与趋势分析
- **知识缺口沉淀** — 未命中问题自动记录，辅助补录

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3、TypeScript、Vite、Pinia、Arco Design Vue |
| 后端 | Python 3.11、FastAPI、SQLAlchemy 2、Pydantic v2 |
| 存储 | SQLite、ChromaDB |
| 工程化 | ESLint、Prettier、Ruff、Husky、Commitlint |

## 环境要求

- **Node.js** ≥ 18
- **Python** 3.11
- **npm** ≥ 9

## 安装

```powershell
# 克隆仓库
git clone <repository-url>
cd smart_space

# 后端
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

# 前端
cd ../frontend
npm install

# 根目录（可选，Git 钩子）
cd ..
npm install
```

默认配置无需外部 API Key 即可运行（Mock LLM + Hash Embedding）。

## 使用

### 启动开发服务

**方式一 — 分终端启动**

```powershell
# 终端 1 — 后端
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端 2 — 前端
cd frontend
npm run dev
```

**方式二 — 根目录 npm 脚本**

```powershell
npm run dev:backend   # 终端 1
npm run dev:frontend  # 终端 2
```

**方式三 — 一键脚本（Windows）**

```powershell
.\scripts\dev.ps1
```

### 访问地址

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端页面 |
| http://127.0.0.1:8000/docs | API 文档（Swagger） |
| http://127.0.0.1:8000/api/ping | 健康检查 |

### 验证

1. 打开前端页面，顶栏应显示 **后端已连接**。
2. 或请求健康检查接口：

```bash
curl http://127.0.0.1:8000/api/ping
# {"status":"ok","message":"pong","version":"0.1.0"}
```

### 快速体验

1. 打开 **Dashboard** 查看运营概览。
2. 新建 **知识库**，上传文档（PDF / DOCX / MD / TXT）。
3. 观察条目状态流转：`pending` → `processing` → `ready`。
4. 进入 **流式问答**，提问并查看引用溯源。
5. 在 **知识缺口** 中查看未命中问题。

## 配置

将 `backend/.env.example` 复制为 `backend/.env`。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_MODE` | `mock` 或 `openai` | `mock` |
| `EMBEDDING_MODE` | `hash` 或 `chromadb_default` | `hash` |
| `DATABASE_URL` | SQLite 连接串 | `sqlite:///./data/app.db` |
| `CHROMA_PATH` | 向量库目录 | `./data/chroma` |
| `CORS_ORIGINS` | 允许的前端源 | `http://localhost:5173` |

接入真实大模型时，设置 `LLM_MODE=openai` 并配置 `OPENAI_API_KEY`。

## 项目结构

```
smart_space/
├── frontend/          # Vue 3 前端
│   └── src/
│       ├── api/       # HTTP 客户端与路由常量
│       ├── stores/    # Pinia 状态管理
│       ├── views/     # 页面组件
│       └── components/
├── backend/           # FastAPI 后端
│   └── app/
│       ├── api/       # 路由层
│       ├── services/  # 业务逻辑
│       ├── models/    # 数据库模型
│       ├── schemas/   # 请求 / 响应模型
│       └── parsers/   # 文档解析器
└── scripts/           # 开发脚本
```

## 开发

```powershell
# 代码检查
npm run lint:frontend
npm run lint:backend

# 生产构建
cd frontend && npm run build

# 从 OpenAPI 生成 TypeScript 类型
npm run openapi:types
```

### API 约定

- **成功响应** — HTTP 2xx，body 直接返回业务数据（无 `{ success, data }` 包装）。
- **分页列表** — `{ items, total, page, page_size }`。
- **错误响应** — `{ detail, code?, errors? }`。
- **流式接口** — `POST /api/knowledge-bases/{id}/chat/stream`，`Content-Type: text/event-stream`。

完整接口说明见：http://127.0.0.1:8000/docs

## License

Private — 仅供本地演示与作品集展示使用。
