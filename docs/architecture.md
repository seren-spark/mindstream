# AI 知识库管理平台 - 架构说明

## 分层设计

### 前端

- `api/` — HTTP 请求封装，按资源拆分
- `stores/` — Pinia 状态管理
- `views/` — 路由级页面
- `components/` — 可复用 UI 组件
- `layouts/` — 页面布局骨架

### 后端

- `api/` — FastAPI 路由（薄层）
- `services/` — 业务逻辑
- `models/` — SQLAlchemy ORM
- `schemas/` — Pydantic 请求/响应模型
- `core/` — 配置、数据库、第三方客户端

## 联调

前端 Vite dev server 将 `/api` 代理到 `http://127.0.0.1:8000`，Axios 统一使用 `/api` 前缀。

健康检查：`GET /api/ping` → `{ "status": "ok", "message": "pong", "version": "0.1.0" }`
