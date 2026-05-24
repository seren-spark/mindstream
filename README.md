# AI 知识库管理平台

本地可运行的 AI 知识库 Demo，用于演示「知识生产 → 知识管理 → 知识消费」闭环。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3、TypeScript、Vite、Pinia、Vue Router、Arco Design Vue |
| 后端 | Python 3.11、FastAPI、SQLAlchemy 2.x、SQLite、ChromaDB |

## 快速启动

### 方式一：分别启动（推荐）

**后端**

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**前端**

```powershell
cd frontend
npm install
npm run dev
```

### 方式二：根目录脚本

```powershell
# 根目录已安装 husky，首次需 npm install
npm run dev:backend   # 终端 1
npm run dev:frontend  # 终端 2
```

或一键脚本（Windows）：

```powershell
.\scripts\dev.ps1
```

访问：http://localhost:5173  
API 文档：http://127.0.0.1:8000/docs

## 代码规范

```powershell
npm run lint:frontend   # ESLint + Prettier
npm run lint:backend    # Ruff
```

## 目录结构

```
smart_space/
├── frontend/     # Vue 3 前端
├── backend/      # FastAPI 后端
├── docs/         # 设计文档
└── scripts/      # 开发脚本
```

## 联调验证

1. 启动前后端
2. 浏览器打开首页，顶栏应显示「后端已连接」
3. 或访问 http://127.0.0.1:8000/api/ping 应返回 `{"status":"ok","message":"pong"}`
