# 教师端学生成绩课程化导出 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让教师端“学生成绩”页面的作业卡片展示课程名称，并让学生成绩 Excel 按课程拆 Sheet、横向展示每次作业分数。

**Architecture:** 后端先扩展任务总览、学生列表和导出聚合能力，保持 Routes -> Services -> Models 分层。前端只在 `TeacherStudents.vue` 增加课程筛选和展示逻辑，复用已有课程、班级、任务和导出接口。

**Tech Stack:** FastAPI、SQLAlchemy、openpyxl、Vue 3 `<script setup lang="ts">`、Element Plus、Vite。

---

## 文件结构

- 修改：`backend/app/services/task_service.py`
  - `task_overview` 增加 `course_id` 参数。
  - 每个任务返回 `course_id`、`course_name`。
- 修改：`backend/app/api/v1/routes/announcement_routes.py`
  - `/announcements/task-overview` 接收 `course_id` 查询参数并传给服务层。
- 修改：`backend/app/services/teacher_service.py`
  - `list_students` 增加 `course_id` 参数。
  - 新增课程化导出数据聚合函数，复用任务计分口径。
- 修改：`backend/app/api/v1/routes/teacher_routes.py`
  - `/teacher/students` 与 `/teacher/students/export` 接收 `course_id`。
  - Excel 写入逻辑支持课程 Sheet 和作业分数列。
- 修改：`frontend/src/api/announcement.ts`
  - `TaskOverview.tasks` 增加 `course_id`、`course_name`。
  - `getTaskOverview` 增加可选参数。
- 修改：`frontend/src/api/teacher.ts`
  - `getStudents` 增加 `courseId` 参数。
- 修改：`frontend/src/views/teacher/TeacherStudents.vue`
  - 增加课程筛选。
  - 作业卡片展示“作业名称（课程名称）”。
  - 导出 URL 附带 `course_id`。
- 测试：`backend/tests/test_teacher_grades_course_export.py`
  - 覆盖作业总览课程字段、学生列表课程过滤、Excel 按课程 Sheet 导出和作业分数列。

---

### Task 1: 后端回归测试

**Files:**
- Create: `backend/tests/test_teacher_grades_course_export.py`

- [ ] **Step 1: 写失败测试**

新增测试文件，包含以下测试：

```python
"""教师端学生成绩课程化导出测试。"""
from io import BytesIO

from openpyxl import load_workbook

from app.core.security import get_password_hash
from app.models.entities import (
    Announcement,
    AnnouncementClass,
    Class,
    Course,
    Question,
    QuizAttempt,
    StudentClassEnrollment,
    TaskCompletion,
    User,
)
from tests.conftest import auth_header


def _seed_second_teacher_course(db_session):
    course = Course(name="第二课程", created_by="T001")
    db_session.add(course)
    db_session.flush()
    cls = Class(name="第二课程班", course_id=course.id, created_by="T001")
    student = User(
        id="2025003",
        name="第二学生",
        hashed_password=get_password_hash("abc123"),
        role="student",
        major="人工智能",
    )
    question = Question(
        type="choice",
        course_id=course.id,
        stem="2+2=?",
        options=["A. 3", "B. 4"],
        answer="B",
    )
    db_session.add_all([cls, student, question])
    db_session.flush()
    db_session.add(StudentClassEnrollment(user_id=student.id, class_id=cls.id, import_order=2))
    db_session.commit()
    return course, cls, student, question


def _seed_assignment(db_session, course, cls, title, question):
    ann = Announcement(course_id=course.id, teacher_id="T001", type="quiz", title=title, question_ids=[question.id])
    db_session.add(ann)
    db_session.flush()
    db_session.add(AnnouncementClass(announcement_id=ann.id, class_id=cls.id))
    db_session.commit()
    return ann


def test_task_overview_returns_course_fields_and_filters_by_course(client, db_session, teacher_token):
    first_course = db_session.query(Course).filter(Course.created_by == "T001", Course.name == "测试课程").one()
    first_class = db_session.query(Class).filter(Class.course_id == first_course.id).one()
    first_question = db_session.query(Question).filter(Question.course_id == first_course.id).one()
    second_course, second_class, _, second_question = _seed_second_teacher_course(db_session)
    _seed_assignment(db_session, first_course, first_class, "第一课程作业", first_question)
    _seed_assignment(db_session, second_course, second_class, "第二课程作业", second_question)

    all_data = client.get("/api/announcements/task-overview", headers=auth_header(teacher_token)).json()["data"]
    assert {task["course_name"] for task in all_data["tasks"]} >= {"测试课程", "第二课程"}

    filtered = client.get(
        f"/api/announcements/task-overview?course_id={second_course.id}",
        headers=auth_header(teacher_token),
    ).json()["data"]
    assert [task["title"] for task in filtered["tasks"]] == ["第二课程作业"]
    assert filtered["tasks"][0]["course_id"] == second_course.id
    assert filtered["tasks"][0]["course_name"] == "第二课程"


def test_teacher_students_filters_stats_by_course(client, db_session, teacher_token):
    first_course = db_session.query(Course).filter(Course.created_by == "T001", Course.name == "测试课程").one()
    first_class = db_session.query(Class).filter(Class.course_id == first_course.id).one()
    first_question = db_session.query(Question).filter(Question.course_id == first_course.id).one()
    second_course, second_class, second_student, second_question = _seed_second_teacher_course(db_session)
    first_ann = _seed_assignment(db_session, first_course, first_class, "第一课程作业", first_question)
    second_ann = _seed_assignment(db_session, second_course, second_class, "第二课程作业", second_question)
    db_session.add(TaskCompletion(announcement_id=second_ann.id, user_id=second_student.id))
    db_session.commit()

    first_resp = client.get(
        f"/api/teacher/students?course_id={first_course.id}",
        headers=auth_header(teacher_token),
    ).json()
    assert [item["id"] for item in first_resp["data"]["items"]] == ["2025001"]
    assert first_resp["data"]["items"][0]["incomplete_tasks"] == 1

    second_resp = client.get(
        f"/api/teacher/students?course_id={second_course.id}",
        headers=auth_header(teacher_token),
    ).json()
    assert [item["id"] for item in second_resp["data"]["items"]] == ["2025003"]
    assert second_resp["data"]["items"][0]["completed_tasks"] == 1


def test_students_export_splits_sheets_by_course_and_writes_task_scores(client, db_session, teacher_token):
    first_course = db_session.query(Course).filter(Course.created_by == "T001", Course.name == "测试课程").one()
    first_class = db_session.query(Class).filter(Class.course_id == first_course.id).one()
    first_question = db_session.query(Question).filter(Question.course_id == first_course.id).one()
    second_course, second_class, second_student, second_question = _seed_second_teacher_course(db_session)
    first_ann = _seed_assignment(db_session, first_course, first_class, "第一课程作业", first_question)
    second_ann = _seed_assignment(db_session, second_course, second_class, "第二课程作业", second_question)
    db_session.add_all([
        QuizAttempt(user_id="2025001", question_id=first_question.id, user_answer=first_question.answer, is_correct=True, announcement_id=first_ann.id),
        TaskCompletion(announcement_id=first_ann.id, user_id="2025001"),
        QuizAttempt(user_id=second_student.id, question_id=second_question.id, user_answer="A", is_correct=False, announcement_id=second_ann.id),
        TaskCompletion(announcement_id=second_ann.id, user_id=second_student.id),
    ])
    db_session.commit()

    resp = client.get("/api/teacher/students/export", headers=auth_header(teacher_token))
    assert resp.status_code == 200
    wb = load_workbook(BytesIO(resp.content))
    assert "总览" in wb.sheetnames
    assert "测试课程" in wb.sheetnames
    assert "第二课程" in wb.sheetnames

    first_sheet = wb["测试课程"]
    headers = [cell.value for cell in first_sheet[1]]
    assert "第一课程作业" in headers
    score_col = headers.index("第一课程作业") + 1
    assert first_sheet.cell(row=2, column=score_col).value == 100

    second_sheet = wb["第二课程"]
    second_headers = [cell.value for cell in second_sheet[1]]
    second_score_col = second_headers.index("第二课程作业") + 1
    assert second_sheet.cell(row=2, column=second_score_col).value == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```powershell
cd backend
python -m pytest tests/test_teacher_grades_course_export.py -q
```

Expected: 至少因为 `course_id` 参数未生效、任务缺 `course_name` 字段或 Excel 缺作业分数列而失败。

### Task 2: 后端服务与路由实现

**Files:**
- Modify: `backend/app/services/task_service.py`
- Modify: `backend/app/api/v1/routes/announcement_routes.py`
- Modify: `backend/app/services/teacher_service.py`
- Modify: `backend/app/api/v1/routes/teacher_routes.py`
- Test: `backend/tests/test_teacher_grades_course_export.py`

- [ ] **Step 1: 扩展 `task_overview`**

在 `task_service.py` 中：

- 函数签名改为 `task_overview(db: Session, teacher_id: str, course_id: int | None = None) -> dict`。
- 查询 `Announcement` 时如果传入 `course_id`，追加 `Announcement.course_id == course_id`。
- 任务 payload 增加 `course_id` 和 `course_name`。

- [ ] **Step 2: 扩展任务总览路由**

在 `announcement_routes.py` 的 `overview` 中增加 `course_id: int | None = None`，调用 `task_overview(db, current_user.id, course_id)`。

- [ ] **Step 3: 扩展学生列表服务**

在 `teacher_service.py` 中：

- `list_students` 增加 `course_id: int = None` 参数。
- 如果传入 `course_id`，先校验课程属于当前教师，再把 `class_ids` 缩小为该课程下班级。
- 任务统计只使用筛选后的班级与课程。

- [ ] **Step 4: 新增导出聚合函数**

在 `teacher_service.py` 中新增：

```python
def build_student_task_score_export(db: Session, teacher_id: str, course_id: int = None, class_id: int = None) -> list[dict]:
    """构建按课程分组的学生作业分数导出数据。"""
```

核心要求：

- 只读取当前教师课程。
- 每个课程返回课程名、作业列表、学生列表。
- 作业分数按任务下每题最新一次答题结果计算百分制。
- 完全未答的作业分数写为 `None`。

- [ ] **Step 5: 改造 Excel 写入**

在 `teacher_routes.py` 中：

- `/teacher/students` 增加 `course_id` 参数并传给 `list_students`。
- `/teacher/students/export` 增加 `course_id` 参数。
- 新增课程 Sheet 写入函数，表头包含基础列与作业列。
- 未筛选课程时保留 `总览` Sheet，再创建每个课程 Sheet。
- 筛选课程或班级时只导出对应课程 Sheet。

- [ ] **Step 6: 运行后端测试确认通过**

Run:

```powershell
cd backend
python -m pytest tests/test_teacher_grades_course_export.py tests/test_assignment_practice_flow.py::test_assignment_report_uses_latest_attempt_per_question_and_current_announcement_only tests/test_integration_bugfixes.py::TestTeacherRefactor::test_teacher_students_include_task_completion_stats -q
```

Expected: 全部通过。

### Task 3: 前端课程筛选和作业卡片展示

**Files:**
- Modify: `frontend/src/api/announcement.ts`
- Modify: `frontend/src/api/teacher.ts`
- Modify: `frontend/src/views/teacher/TeacherStudents.vue`

- [ ] **Step 1: 更新前端 API 类型**

在 `announcement.ts`：

- `TaskOverview.tasks` 增加 `course_id: number`、`course_name: string`。
- `getTaskOverview(courseId?: number)` 用 params 传递 `course_id`。

在 `teacher.ts`：

- `getStudents(classId?: number, page = 1, pageSize = 20, keyword?: string, courseId?: number)` 增加 `course_id` 查询参数。

- [ ] **Step 2: 更新学生成绩页状态**

在 `TeacherStudents.vue`：

- 引入 `getCourses` 和 `Course`。
- 新增 `courses`、`selectedCourseId`。
- 初始化时并行加载课程、班级、学生和作业总览。
- `loadStudents` 和 `loadTaskOverview` 均带上当前 `selectedCourseId`。
- 课程变化时清空不属于该课程的班级选择。

- [ ] **Step 3: 更新模板**

在筛选条增加课程下拉框：

```vue
<el-select v-model="selectedCourseId" placeholder="全部课程" clearable filterable style="width: 220px" @change="handleCourseChange">
  <el-option v-for="course in courses" :key="course.id" :label="course.name" :value="course.id" />
</el-select>
```

作业卡片标题改为：

```vue
<span class="task-title">{{ task.title }}（{{ task.course_name || '未命名课程' }}）</span>
```

导出 URL 附带 `course_id`：

```ts
const params = new URLSearchParams()
if (selectedClassId.value) params.set('class_id', String(selectedClassId.value))
if (selectedCourseId.value) params.set('course_id', String(selectedCourseId.value))
const url = params.toString() ? `/api/teacher/students/export?${params}` : '/api/teacher/students/export'
```

- [ ] **Step 4: 运行前端构建**

Run:

```powershell
cd frontend
npm run build
```

Expected: 构建成功。

### Task 4: 收尾验证

**Files:**
- Modify: `graphify-out/graph.json` 等图谱输出文件可能发生变化，按项目规则更新但不纳入业务提交。

- [ ] **Step 1: 运行后端相关测试**

Run:

```powershell
cd backend
python -m pytest tests/test_teacher_grades_course_export.py tests/test_assignment_practice_flow.py tests/test_integration_bugfixes.py::TestTeacherRefactor::test_teacher_students_include_task_completion_stats -q
```

Expected: 全部通过。

- [ ] **Step 2: 运行前端构建**

Run:

```powershell
cd frontend
npm run build
```

Expected: 构建成功。

- [ ] **Step 3: 更新图谱**

Run:

```powershell
graphify update .
```

Expected: 图谱更新完成。

- [ ] **Step 4: 检查变更范围**

Run:

```powershell
git status --short
git diff -- backend/app/services/task_service.py backend/app/api/v1/routes/announcement_routes.py backend/app/services/teacher_service.py backend/app/api/v1/routes/teacher_routes.py frontend/src/api/announcement.ts frontend/src/api/teacher.ts frontend/src/views/teacher/TeacherStudents.vue backend/tests/test_teacher_grades_course_export.py docs/superpowers/plans/2026-06-09-teacher-grades-course-task-export.md
```

Expected: 只包含本需求相关增量和既有工作区改动，不回滚用户已有修改。

## 自检

- 设计中的课程筛选、作业课程名、课程 Sheet、每次作业分数列、后端测试、前端构建均有对应任务。
- 不新增独立页面，不改作业详情抽屉导出，不改学生端答题流程。
- 类型字段 `course_id`、`course_name` 在后端 payload、前端类型和页面展示中保持一致。
