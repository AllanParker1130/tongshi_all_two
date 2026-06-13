# 教师端学生成绩作业分数展示 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在教师端“学生成绩”表格中展示每名学生每次作业的成绩，超过 3 次作业时通过“详细”按钮查看完整作业成绩，并确认 Excel 导出包含每次作业成绩。

**Architecture:** 后端在现有 `/api/teacher/students` 列表响应中补充每名学生的 `task_scores` 数组，复用现有任务分配、完成统计和 `_latest_task_scores()` 计分逻辑。前端只消费该字段，不新增接口；表格展示前三个作业成绩，超过 3 个作业时用详情弹窗展示完整列表。Excel 导出后端已经通过 `build_student_task_score_export()` 横向写入每次作业成绩，本计划只补足回归测试并保持现有导出路径。

**Tech Stack:** FastAPI + SQLAlchemy + Pydantic，Vue 3 `<script setup lang="ts">`，Element Plus，openpyxl，pytest。

---

## 范围

本次只做教师端学生成绩页和对应教师端学生成绩接口：

- 修改 `/api/teacher/students` 返回结构，新增每名学生的作业成绩明细。
- 修改 `frontend/src/api/teacher.ts` 的 `Student` 类型。
- 修改 `frontend/src/views/teacher/TeacherStudents.vue` 的表格展示和详情弹窗。
- 补充后端测试，覆盖列表接口返回每次作业成绩。
- 补充前端静态测试，覆盖“前三个作业成绩 + 详细按钮”结构。
- 保持 `students/export` 现有 Excel 导出接口和文件下载方式不变，只确认导出仍包含每次作业成绩。

不做：

- 不新增数据库表或字段。
- 不修改学生端。
- 不改变作业完成页。
- 不改变 Excel Sheet 的现有拆分方式。
- 不新增前端状态管理。

## 文件地图

- Modify: `backend/app/schemas/common.py`
  - `StudentOut` 增加 `task_scores: list[StudentTaskScoreOut]`。
  - 新增 `StudentTaskScoreOut` Pydantic Schema。
- Modify: `backend/app/services/teacher_service.py`
  - `list_students()` 查询当前筛选范围内的作业、作业班级、最新答题分数。
  - 每名学生返回 `task_scores`。
  - 复用 `_latest_task_scores()` 和 `_ordered_task_header_titles()`。
- Modify: `backend/tests/test_teacher_grades_course_export.py`
  - 增加接口响应测试：学生成绩列表返回作业标题、完成状态、分数。
  - 保留现有 Excel 导出测试。
- Modify: `frontend/src/api/teacher.ts`
  - `Student` 类型增加 `task_scores`。
- Modify: `frontend/src/views/teacher/TeacherStudents.vue`
  - 增加“作业成绩”列。
  - 展示最多前三次作业成绩。
  - 超过 3 个作业显示“详细”按钮，点击后弹窗查看完整作业成绩。
  - 空成绩显示 `未作答` 或 `未完成`，已完成但无可计算分数显示 `0分`。
- Modify: `frontend/tests/teacher-task-report-migration-static.test.mjs`
  - 增加静态断言，防止作业成绩列、详情按钮和 `task_scores` 类型被移除。

---

### Task 1: 后端列表接口补充作业成绩明细

**Files:**
- Modify: `backend/app/schemas/common.py`
- Modify: `backend/app/services/teacher_service.py`
- Test: `backend/tests/test_teacher_grades_course_export.py`

- [ ] **Step 1: 写失败测试，覆盖 `/api/teacher/students` 返回每次作业成绩**

在 `backend/tests/test_teacher_grades_course_export.py` 追加测试：

```python
def test_teacher_students_returns_each_task_scores(client, db_session, teacher_token):
    first_course = db_session.query(Course).filter(Course.created_by == "T001", Course.name == "测试课程").one()
    first_class = db_session.query(Class).filter(Class.course_id == first_course.id).one()
    first_question = db_session.query(Question).filter(Question.course_id == first_course.id).one()
    first_ann = _seed_assignment(db_session, first_course, first_class, "第一次作业", first_question)
    second_ann = _seed_assignment(db_session, first_course, first_class, "第二次作业", first_question)
    db_session.add_all([
        QuizAttempt(
            user_id="2025001",
            question_id=first_question.id,
            user_answer=first_question.answer,
            is_correct=True,
            announcement_id=first_ann.id,
        ),
        TaskCompletion(announcement_id=first_ann.id, user_id="2025001"),
    ])
    db_session.commit()

    resp = client.get(
        f"/api/teacher/students?course_id={first_course.id}",
        headers=auth_header(teacher_token),
    )
    assert resp.status_code == 200
    student = resp.json()["data"]["items"][0]
    assert [item["title"] for item in student["task_scores"]] == ["第一次作业", "第二次作业"]
    assert student["task_scores"][0] == {
        "announcement_id": first_ann.id,
        "title": "第一次作业",
        "score": 100,
        "is_completed": True,
    }
    assert student["task_scores"][1] == {
        "announcement_id": second_ann.id,
        "title": "第二次作业",
        "score": None,
        "is_completed": False,
    }
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```powershell
pytest backend/tests/test_teacher_grades_course_export.py::test_teacher_students_returns_each_task_scores -q
```

Expected: FAIL，失败原因是响应中没有 `task_scores` 字段。

- [ ] **Step 3: 增加响应 Schema**

在 `backend/app/schemas/common.py` 的 `StudentOut` 前新增：

```python
class StudentTaskScoreOut(BaseModel):
    announcement_id: int
    title: str
    score: Optional[int] = None
    is_completed: bool = False
```

在 `StudentOut` 末尾增加：

```python
    task_scores: List[StudentTaskScoreOut] = []
```

- [ ] **Step 4: 修改 `list_students()` 组装作业成绩**

在 `backend/app/services/teacher_service.py` 的 `list_students()` 中，当前已有 `class_task_ids` 和 `completed_task_ids`。将任务查询从只取 `Announcement.id, AnnouncementClass.class_id` 扩展为同时保留任务对象、任务标题和题目数。

在 `# 任务与完成数据` 区域使用以下结构替换原有任务与完成数据准备逻辑：

```python
    class_task_ids: dict[int, set[int]] = {}
    completed_task_ids: dict[str, set[int]] = {sid: set() for sid in paged_ids}
    task_by_id: dict[int, Announcement] = {}
    task_class_ids: dict[int, set[int]] = {}
    task_scores: dict[tuple[str, int], int] = {}
    task_titles: dict[int, str] = {}

    if paged_ids:
        task_rows = (
            db.query(Announcement, AnnouncementClass.class_id)
            .join(AnnouncementClass, AnnouncementClass.announcement_id == Announcement.id)
            .filter(
                Announcement.teacher_id == teacher_id,
                Announcement.type == "quiz",
                AnnouncementClass.class_id.in_(class_ids),
            )
            .order_by(Announcement.created_at.asc(), Announcement.id.asc())
            .all()
        )
        all_task_ids: set[int] = set()
        for task, owned_class_id in task_rows:
            class_task_ids.setdefault(owned_class_id, set()).add(task.id)
            task_class_ids.setdefault(task.id, set()).add(owned_class_id)
            task_by_id[task.id] = task
            all_task_ids.add(task.id)

        if all_task_ids:
            completion_rows = (
                db.query(TaskCompletion.user_id, TaskCompletion.announcement_id)
                .filter(
                    TaskCompletion.user_id.in_(paged_ids),
                    TaskCompletion.announcement_id.in_(all_task_ids),
                )
                .all()
            )
            for user_id, task_id in completion_rows:
                completed_task_ids.setdefault(user_id, set()).add(task_id)

            ordered_tasks = sorted(task_by_id.values(), key=lambda item: (item.created_at, item.id))
            task_titles = _ordered_task_header_titles(ordered_tasks)
            task_question_counts = {
                task.id: len(task.question_ids if isinstance(task.question_ids, list) else [])
                for task in ordered_tasks
            }
            task_scores = _latest_task_scores(db, list(all_task_ids), task_question_counts)
```

在每个学生 `result.append({...})` 前增加：

```python
        score_items = []
        ordered_assigned_tasks = [
            task for task in sorted(task_by_id.values(), key=lambda item: (item.created_at, item.id))
            if task.id in assigned_task_ids
        ]
        for task in ordered_assigned_tasks:
            score_items.append({
                "announcement_id": task.id,
                "title": task_titles.get(task.id, task.title),
                "score": task_scores.get((sid, task.id)),
                "is_completed": task.id in completed_task_ids.get(sid, set()),
            })
```

并在返回字典里增加：

```python
            "task_scores": score_items,
```

- [ ] **Step 5: 运行后端目标测试**

Run:

```powershell
pytest backend/tests/test_teacher_grades_course_export.py -q
```

Expected: PASS。

---

### Task 2: 前端类型和表格展示作业成绩

**Files:**
- Modify: `frontend/src/api/teacher.ts`
- Modify: `frontend/src/views/teacher/TeacherStudents.vue`
- Modify: `frontend/tests/teacher-task-report-migration-static.test.mjs`

- [ ] **Step 1: 写失败静态测试**

在 `frontend/tests/teacher-task-report-migration-static.test.mjs` 追加：

```js
const teacherApi = readFileSync(resolve(root, 'src/api/teacher.ts'), 'utf8')

assert.match(teacherApi, /task_scores/, '教师端学生类型应包含每次作业成绩')
assert.match(studentGrades, /作业成绩/, '学生成绩页应展示作业成绩列')
assert.match(studentGrades, /visibleTaskScores/, '学生成绩页应只内联展示前三次作业成绩')
assert.match(studentGrades, /scoreDialogVisible/, '学生成绩页应提供完整作业成绩详情弹窗')
```

- [ ] **Step 2: 运行静态测试确认失败**

Run:

```powershell
cd frontend
node .\tests\teacher-task-report-migration-static.test.mjs
```

Expected: FAIL，失败原因是 `teacher.ts` 和页面还没有作业成绩字段与详情弹窗。

- [ ] **Step 3: 修改前端 API 类型**

在 `frontend/src/api/teacher.ts` 的 `Student` 前新增：

```ts
export interface StudentTaskScore {
  announcement_id: number
  title: string
  score: number | null
  is_completed: boolean
}
```

在 `Student` 中增加：

```ts
  task_scores: StudentTaskScore[]
```

- [ ] **Step 4: 修改学生成绩页脚本**

在 `frontend/src/views/teacher/TeacherStudents.vue` 中增加状态和工具函数：

```ts
const scoreDialogVisible = ref(false)
const selectedScoreStudent = ref<Student | null>(null)

function visibleTaskScores(row: Student) {
  return (row.task_scores || []).slice(0, 3)
}

function hasMoreTaskScores(row: Student) {
  return (row.task_scores || []).length > 3
}

function formatTaskScore(score: number | null, isCompleted: boolean) {
  if (score !== null && score !== undefined) return `${score}分`
  return isCompleted ? '0分' : '未完成'
}

function openScoreDetail(row: Student) {
  selectedScoreStudent.value = row
  scoreDialogVisible.value = true
}
```

- [ ] **Step 5: 修改学生成绩页表格列**

在 `完成率` 列后新增：

```vue
        <el-table-column label="作业成绩" min-width="260">
          <template #default="{ row }">
            <div v-if="row.task_scores?.length" class="task-score-list">
              <el-tag
                v-for="task in visibleTaskScores(row)"
                :key="task.announcement_id"
                size="small"
                :type="task.is_completed ? 'success' : 'info'"
              >
                {{ task.title }}：{{ formatTaskScore(task.score, task.is_completed) }}
              </el-tag>
              <el-button
                v-if="hasMoreTaskScores(row)"
                text
                size="small"
                @click="openScoreDetail(row)"
              >
                详细
              </el-button>
            </div>
            <span v-else class="muted-text">暂无作业</span>
          </template>
        </el-table-column>
```

- [ ] **Step 6: 增加详情弹窗**

在 `</template>` 结束前、根节点内部追加：

```vue
    <el-dialog
      v-model="scoreDialogVisible"
      :title="selectedScoreStudent ? `${selectedScoreStudent.name}的作业成绩` : '作业成绩'"
      width="560px"
    >
      <el-table
        v-if="selectedScoreStudent"
        :data="selectedScoreStudent.task_scores || []"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="title" label="作业名称" min-width="180" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_completed ? 'success' : 'info'" size="small">
              {{ row.is_completed ? '已完成' : '未完成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="成绩" width="100" align="center">
          <template #default="{ row }">
            {{ formatTaskScore(row.score, row.is_completed) }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
```

- [ ] **Step 7: 增加样式**

在 `TeacherStudents.vue` 的 `<style scoped>` 中追加：

```css
.task-score-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.muted-text {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}
```

- [ ] **Step 8: 运行前端静态测试和类型检查**

Run:

```powershell
cd frontend
node .\tests\teacher-task-report-migration-static.test.mjs
npm run type-check
```

Expected: 两个命令都 PASS。

---

### Task 3: 验证 Excel 导出仍包含每次作业成绩

**Files:**
- Modify: `backend/tests/test_teacher_grades_course_export.py`

- [ ] **Step 1: 强化现有导出测试**

现有 `test_students_export_splits_sheets_by_course_and_writes_task_scores` 已验证导出 Sheet 包含作业列和分数。补充一个筛选课程导出的断言，确保前端传 `course_id` 时仍导出该课程每次作业成绩。

在该测试末尾追加：

```python
    filtered_resp = client.get(
        f"/api/teacher/students/export?course_id={first_course.id}",
        headers=auth_header(teacher_token),
    )
    assert filtered_resp.status_code == 200
    filtered_wb = load_workbook(BytesIO(filtered_resp.content))
    filtered_sheet = filtered_wb[filtered_wb.sheetnames[0]]
    filtered_headers = [cell.value for cell in filtered_sheet[1]]
    assert "第一课程作业" in filtered_headers
    assert "第二课程作业" not in filtered_headers
```

- [ ] **Step 2: 运行后端导出测试**

Run:

```powershell
pytest backend/tests/test_teacher_grades_course_export.py::test_students_export_splits_sheets_by_course_and_writes_task_scores -q
```

Expected: PASS。

---

### Task 4: 全量验证和图谱更新

**Files:**
- No code changes expected beyond previous tasks.

- [ ] **Step 1: 后端相关测试**

Run:

```powershell
pytest backend/tests/test_teacher_grades_course_export.py -q
```

Expected: PASS。

- [ ] **Step 2: 前端构建**

Run:

```powershell
cd frontend
npm run build
```

Expected: PASS。若只出现 Vite 大 chunk 警告，可记录为既有构建警告。

- [ ] **Step 3: 浏览器检查**

启动前端服务，登录教师账号后检查：

- `/teacher/grades` 表格出现“作业成绩”列。
- 作业不超过 3 次时直接显示成绩标签。
- 作业超过 3 次时显示“详细”按钮。
- 点击“详细”后弹窗展示完整作业列表、状态和成绩。
- 课程下拉仍只显示教师自己的课程。
- 导出 Excel 后对应 Sheet 中包含每次作业成绩列。

- [ ] **Step 4: 更新 graphify**

Run:

```powershell
graphify update .
```

Expected: graphify 更新完成。

---

## 风险点

- `QuizAttempt` 只有作业上下文的记录才有 `announcement_id`，自由练习不应进入作业分数。
- 未完成作业但有部分作答草稿时，当前 `_latest_task_scores()` 会算出分数；展示时以 `is_completed` 区分状态，列表仍可显示分数。若产品希望未完成一律显示“未完成”，实现时应在 `formatTaskScore()` 中以 `is_completed` 优先。
- 同名作业会通过 `_ordered_task_header_titles()` 加 `#id` 区分，前端和导出保持一致。
- 学生跨多个班级时，作业成绩应按该学生所在班级的作业并集展示，沿用现有完成率统计口径。

## 自检

- 覆盖用户要求：学生成绩页新增每次作业成绩；超过 3 次作业使用详细按钮；Excel 导出每次作业成绩。
- 没有数据库迁移。
- 没有新增接口。
- 后端导出逻辑复用现有实现，避免重复改动。
- 前端文案均为正常中文。
