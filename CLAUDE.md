# CLAUDE.md — C 组（作品与文件存储）

This file provides guidance to Claude Code when working on C 组 tasks in this repository.

## 角色身份

- **负责人**：俞（yu1gg），C 组
- **协作/审核**：邱
- **组长分工来源**：`D:\8\2\job.md`

## C 组使命与范围

### 使命

完成作品上传、审核、批量下载和存储改造。

### 范围（必须做）

| 功能域 | 说明 |
|--------|------|
| 作品上传 | 学生端提交 AI 项目作品（图片、报告），含文件安全校验 |
| 教师审核 | 教师端审批学生作品（通过/驳回），含审核意见 |
| 批量下载 | 教师按条件批量打包下载全班作品（ZIP），内存可控 |
| 对象存储接入 | 新增文件写入 S3 兼容存储（SeaweedFS），本地降级兜底 |
| 历史文件兼容 | 旧 `/uploads/` URL 继续可用，不强制一次性搬迁 |
| 上传安全校验 | 扩展名 + 魔数双重校验，防伪造文件和恶意上传 |

**前端页面**：`ProjectUploadView.vue`、`TeacherReviews.vue`

**后端模块**：`project_routes.py`、`upload_routes.py`、`teacher_routes.py`（仅审核/批量下载部分）、存储抽象层（`storage_service.py`、`storage_local.py`、`storage_s3.py`）、`file_routes.py`、`file_service.py`

### 不做

- 班级管理、班级导入（A 组）
- 课程 CRUD、章节管理、资料上传、题库导入（B 组）
- 公告/任务、工作台统计（D 组）
- 学生成长档案、学习进度（全局）

### 交付物

1. 作品上传链路（前端 → 上传校验 → 存储分发 → 元数据入库）
2. 教师审核链路（列表 → 审核意见 → 状态变更）
3. 批量下载链路（多文件打包 → StreamingResponse → 不爆内存）
4. 存储改造（统一抽象层 → local/s3 适配器 → 配置切换）
5. 测试（上传安全、审核流程、存储切换、批量下载、兼容性）
6. 设计/计划文档

### 验收标准

- 新上传文件走对象存储（STORAGE_BACKEND=s3 时）
- 历史上传文件通过 `/uploads/...` 仍可访问
- 批量下载 ZIP 使用流式输出，不将全部文件读入内存
- 文件上传有魔数校验，拒绝伪造扩展名
- 审核通过/驳回后作品状态正确更新，错误提示清晰
- 接口返回统一格式 `{"code": 0, "data": ..., "message": "ok"}`

---

## 项目环境

### 后端（Python / FastAPI）

```bash
cd backend
pip install -r requirements.txt
py database_setup.py          # 初始化/重置 MySQL 数据库 + 建表 + 种子数据
py main.py                    # 启动 FastAPI 服务，端口 8050
```

API 文档：http://127.0.0.1:8050/docs

### 前端（Vue 3 / Vite）

```bash
cd frontend
npm install
npm run dev                   # Vite 开发服务器（默认端口 5173）
npm run build                 # 类型检查 + 生产构建
```

Vite 代理 `/api` 和 `/uploads` → `http://127.0.0.1:8050`

### API 文档
FastAPI 自动生成的 Swagger UI：http://127.0.0.1:8050/docs

### 运行测试

```bash
cd backend
py -m pytest tests/ -v
```

测试使用 SQLite 内存数据库（无需 MySQL），覆盖认证、结构兼容、存储、业务修复回归（共 39 个测试）。

---

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

### 数据库表（17 张）

`users`、`classes`、`student_class_enrollment`、`courses`、`chapters`、`materials`、`questions`、`quiz_attempts`、`student_progress`、`projects`、`project_images`、`project_likes`、`announcements`、`announcement_reads`、`task_completions`、`activity_events`、`stored_files`

---

## 后端架构（分层：Routes → Services → Models）

```
Client → Routes（鉴权 + 校验 + 调 Service）
       → Services（业务逻辑 + 调 Model）
         → Models（SQLAlchemy ORM → MySQL）
           → Response: {"code": 0, "data": {...}, "message": "ok"}
```

### C 组核心文件

```
backend/app/api/v1/routes/
├── project_routes.py      # 作品广场、提交、点赞
├── upload_routes.py       # 通用文件上传（含魔数校验）
├── teacher_routes.py      # 作品审核、批量下载（仅 C 组部分）
└── file_routes.py         # 统一文件访问 GET /api/files/{file_id}

backend/app/services/
├── project_service.py     # 作品 CRUD + 点赞 + 审核
├── storage_service.py     # 存储抽象协议 + StoredObject
├── storage_local.py       # 本地文件适配器
├── storage_s3.py          # SeaweedFS S3 适配器
└── file_service.py        # 文件元数据写入、URL 构建

backend/app/core/
└── upload_validation.py   # 扩展名 + 魔数双重校验
```

### 统一响应格式

```json
// 成功
{ "code": 0, "data": {...}, "message": "ok" }
// 失败
{ "code": 400, "data": null, "message": "错误描述" }
```

HTTP 状态码始终为 200，通过 `code` 区分成功/失败。

### 数据库表（C 组直接相关）

| 表名 | 用途 |
|------|------|
| `projects` | 学生 AI 项目作品（标题、描述、标签、状态、报告 URL） |
| `project_images` | 作品图片 |
| `project_likes` | 作品点赞关系 |
| `stored_files` | 文件元数据（存储后端、桶、路径、原始名称） |

### 存储架构

- **配置开关**：`.env` 中 `STORAGE_BACKEND=local|s3`
- **统一入口**：`GET /api/files/{file_id}` 自动分发到对应存储
- **历史兼容**：`/uploads/...` 静态挂载保留，旧 URL 继续可用
- **设计文档**：`docs/superpowers/specs/2026-05-24-multi-storage-collaboration-design.md`

---

## 开发约定

- 所有对话使用中文，代码注释使用中文
- 用户 `id` 即学号或工号，同时作为主键
- 新增 Pydantic Schema → `backend/app/schemas/common.py`
- 新增 ORM 模型 → `backend/app/models/entities.py`
- 新增路由 → `backend/app/api/v1/routes/` + `__init__.py` 注册
- 新增服务 → `backend/app/services/`
- 错误返回 → 抛出 `BusinessException(code, message)`
- 前端统一使用 `<script setup>` + TypeScript

---

## 工作流程

> **硬性规则：每次修改项目代码前，必须先读取本 CLAUDE.md 文件，确认 C 组范围与约束后再动手。**

写代码前必须先明确：

1. 要解决的问题是什么
2. 涉及哪些页面、接口或模块
3. 哪些内容在 C 组范围内、哪些不是（不碰班级/课程/题库/公告）
4. 如何验收

### 较大改动先写计划文档

满足以下任一条件，先在 `docs/superpowers/` 写设计或计划文档：

- 同时涉及前后端两个以上模块
- 涉及数据库结构、权限边界、存储策略调整
- 涉及教师端多个页面联动
- 涉及接口新增或接口语义变化

```
docs/superpowers/specs/   # 设计文档（目标、范围、方案取舍）
docs/superpowers/plans/   # 实施计划（分步任务、涉及文件、验证方式）
```

### 协作边界

- D 组（邱）负责整体接口拍板、联调推进和最终验收收口
- 修改跨组共享文件（如 `teacher_routes.py`、`entities.py`、`common.py`）时，只动 C 组相关部分
- 接口变更需与 D 组同步确认

### 验收清单

C 组每次修改完成后自检：

1. 新上传文件是否走对象存储（s3 模式）
2. 旧文件通过 `/uploads/...` 是否仍可访问
3. 批量下载是否使用 StreamingResponse 流式输出
4. 上传是否有魔数校验
5. 审核状态变更是否正确
6. 接口错误提示是否清晰
7. 相关测试是否通过：`python -m pytest tests/ -v`
