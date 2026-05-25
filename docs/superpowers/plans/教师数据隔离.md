# 教师数据隔离权限 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为教师端核心业务数据补齐教师归属和权限过滤，确保不同教师之间的资料管理、班级管理、题库和学生数据互不串扰。

**Architecture:** 后端以 `teacher_id` 作为教师数据隔离边界，继续遵循 Routes -> Services -> Models 分层；路由层传入当前教师 ID，服务层负责过滤和归属校验。旧库通过 `schema_compat.py` 自动补字段并默认归属 `T001`，前端尽量不改结构，只消费已隔离的接口结果。

**Tech Stack:** FastAPI、SQLAlchemy、Pytest、Vue 3、TypeScript、Vite、Element Plus。

---

## 文件结构

- Modify: `backend/app/models/entities.py`
  - 给 `Class`、`Course`、`Chapter`、`Material`、`Question` 增加 `teacher_id` 字段和必要索引。
- Modify: `backend/app/db/schema_compat.py`
  - 给旧库自动补 `teacher_id` 字段，并把空值归属到 `T001`。
- Modify: `backend/app/services/class_service.py`
  - 班级列表、创建、删除、学生维护和导入按教师隔离。
- Modify: `backend/app/api/v1/routes/class_routes.py`
  - 把当前教师 ID 传入服务层。
- Modify: `backend/app/services/teacher_service.py`
  - 教师统计和学生数据只统计当前教师班级范围。
- Modify: `backend/app/api/v1/routes/teacher_routes.py`
  - 把当前教师 ID 传入统计和学生数据服务。
- Modify: `backend/app/services/question_service.py`
  - 课程和题目按教师隔离，课程下章节必须属于同一教师。
- Modify: `backend/app/api/v1/routes/question_routes.py`
  - 传入当前教师 ID，限制课程和题目管理范围。
- Modify: `backend/app/services/chapter_service.py`
  - 章节按教师隔离，创建/编辑时校验课程归属。
- Modify: `backend/app/api/v1/routes/chapter_routes.py`
  - 教师端章节管理传入当前教师 ID。
- Modify: `backend/app/services/material_service.py`
  - 资料按教师隔离，创建资料时校验章节归属。
- Modify: `backend/app/api/v1/routes/material_routes.py`
  - 教师端资料管理传入当前教师 ID。
- Modify: `backend/app/services/announcement_service.py`
  - 创建公告和完成报告校验班级或公告属于当前教师。
- Modify: `backend/tests/conftest.py`
  - 测试种子数据补充第二个教师、第二套班级/课程/章节/资料/题目。
- Modify: `backend/tests/test_integration_bugfixes.py`
  - 增加教师隔离回归测试。
- Modify: `frontend/src/views/teacher/TeacherClasses.vue`
  - 如果接口错误文案需要调整，只做中文提示优化。
- Modify: `frontend/src/views/teacher/TeacherMaterials.vue`
  - 前端不主动过滤跨教师数据，依赖后端隔离；只保留错误提示。
- Modify: `frontend/src/views/teacher/TeacherStudents.vue`
  - 前端不主动过滤跨教师数据，依赖后端隔离；班级下拉使用当前教师班级。

---

## Task 1: 数据模型和旧库兼容

**Files:**
- Modify: `backend/app/models/entities.py`
- Modify: `backend/app/db/schema_compat.py`
- Test: `backend/tests/test_schema_compat.py`

- [ ] **Step 1: 写失败测试，旧库补齐教师归属字段**

在 `backend/tests/test_schema_compat.py` 增加测试，创建缺少 `teacher_id` 的 `classes`、`courses`、`chapters`、`materials`、`questions` 表，执行 `ensure_schema_compatibility(engine)` 后断言这些表均有 `teacher_id` 字段。

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
py -m pytest backend\tests\test_schema_compat.py -q
```

Expected: FAIL，原因是兼容脚本尚未补齐这些表的 `teacher_id`。

- [ ] **Step 3: 增加 ORM 字段**

在 `backend/app/models/entities.py` 中添加：

```python
teacher_id = Column(String(32), ForeignKey("users.id"), nullable=False, default="T001", index=True)
```

添加位置：

- `Class`
- `Course`
- `Chapter`
- `Material`
- `Question`

- [ ] **Step 4: 扩展旧库兼容脚本**

在 `backend/app/db/schema_compat.py` 中对 `classes`、`courses`、`chapters`、`materials`、`questions` 逐表补 `teacher_id VARCHAR(32) DEFAULT 'T001'`，并更新空值为 `T001`。

- [ ] **Step 5: 运行兼容测试**

Run:

```bash
py -m pytest backend\tests\test_schema_compat.py -q
```

Expected: PASS。

---

## Task 2: 班级和学生数据隔离

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_integration_bugfixes.py`
- Modify: `backend/app/services/class_service.py`
- Modify: `backend/app/api/v1/routes/class_routes.py`
- Modify: `backend/app/services/teacher_service.py`
- Modify: `backend/app/api/v1/routes/teacher_routes.py`

- [ ] **Step 1: 写失败测试，教师只能看到自己的班级**

在 `backend/tests/test_integration_bugfixes.py` 增加测试：用 `T001` 和新教师 `T002` 登录，各自请求 `/api/classes`，断言看不到对方班级。

- [ ] **Step 2: 写失败测试，教师学生数据只来自自己班级**

增加测试：同一个库中存在两个教师的班级和学生，`GET /api/teacher/students` 只返回当前教师班级学生。

- [ ] **Step 3: 写失败测试，教师不能操作其它教师班级**

增加测试：教师 `T002` 删除、查看、添加学生到 `T001` 班级时返回 404。

- [ ] **Step 4: 运行测试确认失败**

Run:

```bash
py -m pytest backend\tests\test_integration_bugfixes.py -q
```

Expected: FAIL，原因是班级接口仍全局可见。

- [ ] **Step 5: 修改班级服务签名**

让以下函数接收 `teacher_id` 并过滤：

```python
list_classes(db, teacher_id)
create_class(db, name, major, teacher_id)
delete_class(db, class_id, teacher_id)
list_class_students(db, class_id, teacher_id)
enroll_student(db, class_id, student_id, teacher_id)
remove_student(db, class_id, student_id, teacher_id)
import_students_from_excel(db, file_bytes, teacher_id)
```

- [ ] **Step 6: 修改班级路由**

在 `backend/app/api/v1/routes/class_routes.py` 使用 `current_user: AuthUser = Depends(require_role("teacher"))`，并把 `current_user.id` 传入服务层。

- [ ] **Step 7: 修改教师统计和学生数据**

`get_teacher_stats(db, teacher_id)` 只统计当前教师班级学生、当前教师章节、当前教师待审核作品关联学生。`list_students(db, teacher_id, class_id=None)` 只返回当前教师班级学生。

- [ ] **Step 8: 运行测试**

Run:

```bash
py -m pytest backend\tests\test_integration_bugfixes.py -q
```

Expected: PASS。

---

## Task 3: 课程、章节、资料、题目隔离

**Files:**
- Modify: `backend/tests/test_integration_bugfixes.py`
- Modify: `backend/app/services/question_service.py`
- Modify: `backend/app/api/v1/routes/question_routes.py`
- Modify: `backend/app/services/chapter_service.py`
- Modify: `backend/app/api/v1/routes/chapter_routes.py`
- Modify: `backend/app/services/material_service.py`
- Modify: `backend/app/api/v1/routes/material_routes.py`

- [ ] **Step 1: 写失败测试，课程按教师隔离**

增加测试：`T001` 和 `T002` 各有课程，`GET /api/questions/courses` 只返回当前教师课程；教师不能编辑或删除对方课程。

- [ ] **Step 2: 写失败测试，章节和资料按教师隔离**

增加测试：`GET /api/chapters`、`GET /api/materials` 只返回当前教师数据；教师不能给对方章节上传资料。

- [ ] **Step 3: 写失败测试，题目按教师隔离**

增加测试：`GET /api/questions` 只返回当前教师题目；教师不能新增题目到对方章节。

- [ ] **Step 4: 运行测试确认失败**

Run:

```bash
py -m pytest backend\tests\test_integration_bugfixes.py -q
```

Expected: FAIL，原因是课程、章节、资料、题目接口仍全局可见。

- [ ] **Step 5: 修改课程和题目服务**

让 `list_courses`、`create_course`、`update_course`、`delete_course`、`get_course_detail`、`list_questions`、`create_question`、`update_question`、`delete_question` 接收 `teacher_id` 并过滤归属。

- [ ] **Step 6: 修改章节服务**

让 `list_chapters`、`get_chapter`、`create_chapter`、`update_chapter`、`delete_chapter` 接收 `teacher_id`。教师创建章节时写入 `teacher_id`，章节所属课程必须属于同一教师。

- [ ] **Step 7: 修改资料服务**

让教师端资料接口接收 `teacher_id`。创建资料时写入 `teacher_id`，并校验章节属于当前教师。

- [ ] **Step 8: 修改相关路由**

把 `question_routes.py`、`chapter_routes.py`、`material_routes.py` 中教师端接口的 `_` 改为 `current_user`，传入 `current_user.id`。

- [ ] **Step 9: 运行测试**

Run:

```bash
py -m pytest backend\tests\test_integration_bugfixes.py -q
```

Expected: PASS。

---

## Task 4: 公告任务权限补强

**Files:**
- Modify: `backend/tests/test_integration_bugfixes.py`
- Modify: `backend/app/services/announcement_service.py`
- Modify: `backend/app/services/task_service.py`
- Modify: `backend/app/api/v1/routes/announcement_routes.py`

- [ ] **Step 1: 写失败测试，教师不能向其它教师班级发布公告**

增加测试：`T002` 调用公告创建接口，传入 `T001` 的班级，返回 404 或 403。

- [ ] **Step 2: 写失败测试，教师不能查看其它教师公告完成报告**

增加测试：`T002` 查看 `T001` 公告的完成报告，返回 404 或 403。

- [ ] **Step 3: 修改公告服务校验班级归属**

`create_announcement(db, teacher_id, data)` 查询班级时加 `Class.teacher_id == teacher_id`。

- [ ] **Step 4: 修改完成报告校验公告归属**

`completion_report(db, announcement_id, teacher_id)` 只允许读取 `Announcement.teacher_id == teacher_id` 的公告。

- [ ] **Step 5: 运行测试**

Run:

```bash
py -m pytest backend\tests\test_integration_bugfixes.py -q
```

Expected: PASS。

---

## Task 5: 前端验证与错误提示

**Files:**
- Modify only if build or手工验证发现当前页面文案不清楚。

- [ ] **Step 1: 运行后端全量测试**

Run:

```bash
py -m pytest backend\tests -q
```

Expected: PASS。

- [ ] **Step 2: 运行前端构建**

Run:

```bash
cd frontend
npm run build
```

Expected: PASS，允许 Vite chunk 体积提示。

- [ ] **Step 3: 手工验证教师隔离**

启动后端和前端，用 `T001` 和 `T002` 分别登录：

```text
/teacher/classes
/teacher/materials
/teacher/questions
/teacher/students
```

检查：

- `T001` 看不到 `T002` 班级。
- `T001` 看不到 `T002` 课程、章节、资料、题目。
- `T001` 学生数据页只显示 `T001` 班级学生。
- `T002` 不能操作 `T001` 的资源。

---

## 自检结果

- 覆盖了教师端资料管理、班级管理、学生数据、题库管理和公告任务的隔离需求。
- 保留了旧库兼容策略，默认归属 `T001`。
- 没有新增管理员、多租户组织或新 UI 框架。
- 没有改变统一响应格式。
- 学生端课程公开可见策略已明确为本阶段非目标。
