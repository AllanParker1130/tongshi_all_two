# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 平台功能

### 学生端
- **探·学无止境（/learn）** — 按章节浏览课程内容，在线观看视频和阅读 PDF 教材，追踪学习进度
- **练·学以致用（/practice）** — 按章节进行在线测验，支持选择题和填空题，即时批改并展示解析
- **造·智创未来（/create）** — 浏览和提交 AI 项目作品，支持标签分类、点赞、详情查看
- **行·知行合一（/act）** — 查看课程活动时间线与动态
- **成长档案（/portfolio）** — 个人学习数据可视化，包含雷达图展示各章掌握程度

### 教师端（/teacher）
- **工作台概览** — 教学数据总览仪表盘
- **资料管理** — 上传和管理课程视频/PDF 资料
- **题库管理** — 增删改查题目（选择题/填空题）
- **学生数据** — 查看学生学习进度与成绩统计
- **作品审核** — 审批学生提交的项目作品（通过/驳回）




### 后端（Python / FastAPI）
```bash
cd backend
pip install -r requirements.txt
py database_setup.py          # 初始化/重置 MySQL 数据库 + 建表 + 填充种子数据
py main.py                    # 启动 FastAPI 服务，端口 8050
# Windows 下也可使用：start_backend.bat（自动安装依赖 + 检查数据库 + 启动服务）
```

### 前端（Vue 3 / Vite）
```bash
cd frontend
npm install
npm run dev                   # Vite 开发服务器（默认端口 5173）
npm run build                 # 类型检查 + 生产构建
npm run preview               # 预览生产构建产物
```

### API 文档
FastAPI 自动生成的 Swagger UI：http://127.0.0.1:8050/docs

## 项目架构

### 后端 — 分层架构：Routes → Services → Models

- `backend/main.py` — FastAPI 应用入口，CORS、静态文件挂载、全局异常处理
- `backend/app/api/v1/routes/` — 12 个路由模块，全部挂载在 `/api` 前缀下（含 `file_routes.py` 统一文件访问）
- `backend/app/services/` — 12+ 个业务逻辑服务模块（含 `storage_service.py`、`storage_local.py`、`storage_s3.py`、`file_service.py`）
- `backend/app/models/entities.py` — 所有 17 个 SQLAlchemy ORM 模型集中在一个文件（含 `StoredFile`）
- `backend/app/schemas/common.py` — 所有 Pydantic 请求/响应 Schema 集中在一个文件
- `backend/app/core/` — 配置（读取 `.env`）、JWT/密码安全、统一响应格式、自定义异常、文件上传校验
- `backend/app/db/session.py` — SQLAlchemy 引擎 + 会话工厂
- `backend/app/db/schema_compat.py` — 旧库字段自动补齐（排课字段、教师归属字段、stored_files 表等）
- `backend/tests/` — 集成测试（conftest.py + 3 个测试文件，39 个测试覆盖认证、兼容性、存储、业务修复回归）

**统一响应格式：** 所有接口返回 `{"code": 0, "data": ..., "message": "ok"}`（成功）或 `{"code": <错误码>, "data": null, "message": "..."}`（失败）。HTTP 状态码始终为 200。

**数据库：** MySQL（数据库名 `tongshi`），通过 `backend/.env` 配置连接串 `mysql+pymysql://`。SQLite 仅用于测试内存库，不作为业务运行时数据库。数据库迁移使用 Alembic（`alembic.ini` + `migrations/`）。

**文件存储：** 支持 `local`（默认，兼容历史 `uploads/`）和 `s3`（SeaweedFS / S3 兼容网关）两种后端。统一文件访问路由 `GET /api/files/{file_id}`，由 `StoredFile` 元数据记录自动分发。上传接口自动做魔数校验（PDF/ZIP/PNG/JPEG/GIF/WebP）。

**数据库结构兼容：** `backend/app/db/schema_compat.py` 在后端启动时自动补齐旧表缺失字段（排课字段、教师归属字段等），避免旧库升级后报错。

### 前端 — Vue 3 单页应用

- `frontend/src/api/http.ts` — Axios 实例，JWT 拦截器（从 localStorage 读取 token），401 自动跳转登录
- `frontend/src/api/*.ts` — 12 个类型化 API 模块，对应后端各业务域
- `frontend/src/stores/auth.ts` — Pinia 认证状态管理（登录/注册/登出），JWT 持久化到 localStorage
- `frontend/src/router/index.ts` — 20+ 路由，`beforeEach` 鉴权守卫 + 教师角色校验
- `frontend/src/views/` — 页面组件（Composition API + Element Plus）
- `frontend/src/views/teacher/` — 教师端子页面（布局 + 7 个视图）
- `frontend/src/views/content/` — VideoPlayer 和 PdfViewer 组件

Vite 开发服务器将 `/api` 和 `/uploads` 代理到 `http://127.0.0.1:8050`。

### 数据库表（17 张）

`users`、`classes`、`student_class_enrollment`、`courses`、`chapters`、`materials`、`questions`、`quiz_attempts`、`student_progress`、`projects`、`project_images`、`project_likes`、`announcements`、`announcement_reads`、`task_completions`、`activity_events`、`stored_files`

### 约定

- 用户 `id` 即学号或工号，同时作为主键
- 前端统一使用 `<script setup>` + TypeScript
- 新增 Pydantic Schema 往 `common.py` 中追加
- 新增 ORM 模型往 `entities.py` 中追加
- 在实施计划之前要先做好规划在工作

## 语言要求

- 所有对话必须使用中文。
- 所有文档必须使用中文。
- 所有代码注释必须使用中文。

## 执行要求

- 在生成说明、总结、计划、提交说明时，统一使用中文。
- 在新增或修改 Markdown 文档时，统一使用中文。
- 在新增或修改代码注释时，统一使用中文。

### 设计文档

规格说明和实施计划位于 `docs/superpowers/`：
- `specs/` — 功能设计规格（教师数据隔离、课程体系管理等）
- `plans/` — 实施任务清单（TDD 步骤、涉及文件、验收方式）

### 运行测试

```bash
cd backend
py -m pytest tests/ -v
```

测试使用 SQLite 内存数据库（无需 MySQL），覆盖认证、结构兼容、存储、业务修复回归（共 39 个测试）。

## 工作流程

正式写代码前必须先明确以下内容：

1. 要解决的问题是什么。
2. 涉及哪些页面、接口或模块。
3. 哪些内容在范围内，哪些内容不做。
4. 如何验收。
- 如果有先进行 /brainstorming 明确任务目标
对于较大的改动，必须先写设计或计划文档，放在：

```text
docs/superpowers/specs/
docs/superpowers/plans/
```

用户确认后再进入实现。

### 何时视为较大改动

满足以下任一条件，应先写设计或计划文档：

- 同时涉及前后端两个以上模块。
- 涉及数据库结构、权限边界、核心业务流程调整。
- 涉及教师端多个页面联动修改。
- 涉及接口新增、接口语义变化或批量数据导入导出。

### 计划文档要求

- 设计文档聚焦目标、范围、现状问题、方案取舍、接口或数据影响。
- 其次写文档是优先按照任务所需的分成前端和后端文档，方便后续团队合作
- 实施计划聚焦分步任务、涉及文件、验证方式、风险点。
- 文档命名优先使用日期和主题，保持与现有 `docs/superpowers/` 风格一致。

### 最后流程
- 如果一次任务结束可以运行/neat-freak 总结一下