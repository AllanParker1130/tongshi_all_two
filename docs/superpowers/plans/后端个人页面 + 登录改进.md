# 后端实施计划 — 个人页面 + 登录改进 + 班级管理

> **For agentic workers:** Use superpowers:subagent-driven-development 或 superpowers:executing-plans 按任务逐步实施。步骤使用 `- [ ]` 追踪。

**Goal:** 围绕学生个人页面（修改密码/错题本/收藏作品）、登录流程改进（忘记密码/首次改密）、班级管理改进（手动添加学生自动建号）三组需求，补齐后端 API 和业务逻辑。

**Architecture:** 继续 Routes → Services → Models 分层。新增 `profile_routes.py` 处理个人页面请求，修改 `auth_routes.py` 和 `class_routes.py` 扩展现有认证和班级功能。旧库通过 `schema_compat.py` 自动补齐 `is_first_login` 字段。

**Tech Stack:** FastAPI、SQLAlchemy、Pytest、MySQL（开发用 SQLite）。

---

## 文件结构

- Modify: `backend/app/models/entities.py`
  - User 模型增加 `is_first_login` 字段
- Modify: `backend/app/db/schema_compat.py`
  - 旧库自动补 `is_first_login` 字段
- Modify: `backend/app/schemas/common.py`
  - 新增 `ChangePasswordRequest`、`ForgotPasswordRequest` Schema；`AuthUser` 增加 `is_first_login`；`ClassEnrollRequest` 增加 `name` 字段
- Modify: `backend/app/services/auth_service.py`
  - 新增 `change_password()`、`forgot_password()`；修改 `login_user()` 返回 `is_first_login`
- Modify: `backend/app/api/v1/routes/auth_routes.py`
  - 新增 `POST /password/change`、`POST /password/forgot` 路由
- Modify: `backend/app/services/quiz_service.py`
  - 新增 `get_wrong_questions()` 错题本查询
- Modify: `backend/app/services/project_service.py`
  - 提取 `format_project()` 共享函数
- Modify: `backend/app/api/v1/routes/project_routes.py`
  - 复用 `project_service.format_project`
- Modify: `backend/app/services/class_service.py`
  - `enroll_student()` 支持自动创建用户
- Modify: `backend/app/api/v1/routes/class_routes.py`
  - `enroll` 路由传入 `name` 字段
- Create: `backend/app/api/v1/routes/profile_routes.py`
  - 个人页面路由（错题本 + 收藏作品）
- Modify: `backend/app/api/v1/__init__.py`
  - 注册 profile_router

---

## Task 1: 数据模型和旧库兼容

**Files:**
- Modify: `backend/app/models/entities.py`
- Modify: `backend/app/db/schema_compat.py`

- [ ] **Step 1: User 模型增加 is_first_login 字段**

在 `backend/app/models/entities.py` 的 `User` 类中，`created_at` 字段之后添加：

```python
is_first_login = Column(Boolean, default=True)  # 首次登录标记，强制改密码
```

- [ ] **Step 2: 旧库兼容补字段**

在 `backend/app/db/schema_compat.py` 的 `ensure_schema_compatibility` 函数中，已有的 `project_images` 补表逻辑之后添加：

```python
# 补 users.is_first_login 字段
if "users" in table_names:
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "is_first_login" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN is_first_login BOOLEAN DEFAULT 1"))
        # 已有老用户不需要强制改密码
        conn.execute(text("UPDATE users SET is_first_login = 0 WHERE is_first_login IS NULL OR is_first_login = 1"))
```

注意：已有老用户设为 `False`（0），新注册/导入的用户在 service 层设为 `True`。

- [ ] **Step 3: 运行测试确认兼容**

```bash
cd backend
python -m pytest tests/ -v
```

---

## Task 2: 认证 API（修改密码 + 忘记密码）

**Files:**
- Modify: `backend/app/schemas/common.py`
- Modify: `backend/app/services/auth_service.py`
- Modify: `backend/app/api/v1/routes/auth_routes.py`

- [ ] **Step 1: 新增 Pydantic Schema**

在 `backend/app/schemas/common.py` 中添加：

```python
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个字母和一个数字")
        return v


class ForgotPasswordRequest(BaseModel):
    id: str
    new_password: str = Field(min_length=6)

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个字母和一个数字")
        return v
```

同时在 `AuthUser` schema 中增加字段：

```python
is_first_login: bool = False
```

- [ ] **Step 2: 修改 auth_service.py**

修改 `login_user()` 返回值，增加 `is_first_login`：

```python
return {
    "access_token": access_token,
    "token_type": "bearer",
    "user": {
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "major": user.major or "",
        "is_first_login": user.is_first_login,  # 新增
    },
}
```

新增 `change_password()` 函数：

```python
def change_password(db: Session, user_id: str, old_password: str, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(404, "用户不存在")
    if not verify_password(old_password, user.hashed_password):
        raise BusinessException(400, "原密码错误")
    if old_password == new_password:
        raise BusinessException(400, "新密码不能与原密码相同")
    user.hashed_password = get_password_hash(new_password)
    user.is_first_login = False
    db.commit()
    return {"message": "密码修改成功"}
```

新增 `forgot_password()` 函数：

```python
def forgot_password(db: Session, user_id: str, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(404, "学号不存在")
    user.hashed_password = get_password_hash(new_password)
    user.is_first_login = False
    db.commit()
    return {"message": "密码重置成功"}
```

- [ ] **Step 3: 新增路由**

在 `backend/app/api/v1/routes/auth_routes.py` 中添加：

```python
@router.post("/password/change", summary="修改密码")
def change_password(data: ChangePasswordRequest, db: Session = Depends(get_db),
                    current_user: AuthUser = Depends(get_current_user)):
    return success(change_password_svc(db, current_user.id, data.old_password, data.new_password))


@router.post("/password/forgot", summary="忘记密码")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return success(forgot_password_svc(db, data.id, data.new_password))
```

注意：避免函数名与 service 函数名冲突，使用别名导入或调整命名。

- [ ] **Step 4: 运行测试**

```bash
cd backend
python -m pytest tests/ -v
```

---

## Task 3: 错题本 + 收藏作品 API

**Files:**
- Modify: `backend/app/services/quiz_service.py`
- Modify: `backend/app/services/project_service.py`（提取 format_project）
- Modify: `backend/app/api/v1/routes/project_routes.py`（复用 format_project）
- Create: `backend/app/api/v1/routes/profile_routes.py`
- Modify: `backend/app/api/v1/__init__.py`

- [ ] **Step 1: quiz_service 增加错题本查询**

在 `backend/app/services/quiz_service.py` 中新增：

```python
def get_wrong_questions(db: Session, user_id: str):
    """获取错题本：该用户最近一次答错且之后未答对的题目"""
    from sqlalchemy import func as sa_func

    # 子查询：每道题的最新 attempt id
    latest_sub = (
        db.query(sa_func.max(QuizAttempt.id).label("max_id"))
        .filter(QuizAttempt.user_id == user_id)
        .group_by(QuizAttempt.question_id)
        .subquery()
    )

    attempts = (
        db.query(QuizAttempt)
        .join(latest_sub, QuizAttempt.id == latest_sub.c.max_id)
        .filter(QuizAttempt.is_correct == False)
        .options(joinedload(QuizAttempt.question))
        .all()
    )

    result = []
    for a in attempts:
        q = a.question
        if not q:
            continue
        result.append({
            "question_id": q.id,
            "chapter_id": q.chapter_id,
            "stem": q.stem,
            "options": q.options,
            "answer": q.answer,
            "explanation": q.explanation,
            "user_answer": a.user_answer,
            "answered_at": a.answered_at.isoformat() if a.answered_at else "",
        })
    return result
```

- [ ] **Step 2: 提取 format_project 到 project_service**

在 `backend/app/services/project_service.py` 中新增函数（从 `project_routes._format_project` 迁移）：

```python
def format_project(db: Session, p):
    from app.models.entities import User, ProjectImage
    author = db.query(User).filter(User.id == p.author_id).first()
    images = [
        {"id": image.id, "image_url": image.image_url, "sort_order": image.sort_order}
        for image in sorted(p.images, key=lambda item: (item.sort_order, item.id))
    ]
    if not images and p.image_url:
        images = [{"image_url": p.image_url, "sort_order": 0}]
    return {
        "id": p.id, "title": p.title, "author_id": p.author_id,
        "author_name": author.name if author else "",
        "major": p.major, "description": p.description,
        "tags": p.tags, "likes": p.likes, "featured": p.featured,
        "video_url": p.video_url, "report_url": p.report_url,
        "image_url": p.image_url, "images": images,
        "link_url": getattr(p, "link_url", ""),
        "status": p.status, "reject_reason": p.reject_reason, "date": p.date,
    }
```

同时修改 `project_routes.py`，将 `_format_project` 替换为从 `project_service` 导入的 `format_project`。

- [ ] **Step 3: 新建 profile_routes.py**

创建 `backend/app/api/v1/routes/profile_routes.py`：

```python
"""个人页面路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.response import success
from app.schemas.common import AuthUser
from app.services.quiz_service import get_wrong_questions
from app.services.project_service import list_liked_projects

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/wrong-questions", summary="错题本")
def wrong_questions(db: Session = Depends(get_db),
                    current_user: AuthUser = Depends(get_current_user)):
    return success(get_wrong_questions(db, current_user.id))


@router.get("/liked-projects", summary="收藏作品")
def liked_projects(db: Session = Depends(get_db),
                   current_user: AuthUser = Depends(get_current_user)):
    return success(list_liked_projects(db, current_user.id))
```

- [ ] **Step 4: project_service 增加 list_liked_projects**

在 `backend/app/services/project_service.py` 中新增：

```python
def list_liked_projects(db: Session, user_id: str):
    from app.models.entities import Project, ProjectLike, User
    likes = db.query(ProjectLike).filter(ProjectLike.user_id == user_id).all()
    project_ids = [l.project_id for l in likes]
    if not project_ids:
        return []
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    return [format_project(db, p) for p in projects]
```

- [ ] **Step 5: 注册路由**

在 `backend/app/api/v1/__init__.py` 中添加：

```python
from app.api.v1.routes.profile_routes import router as profile_router
# ...
api_router.include_router(profile_router)
```

- [ ] **Step 6: 运行测试**

```bash
cd backend
python -m pytest tests/ -v
```

---

## Task 4: 班级管理改进（手动添加学生自动建号）

**Files:**
- Modify: `backend/app/schemas/common.py`
- Modify: `backend/app/services/class_service.py`
- Modify: `backend/app/api/v1/routes/class_routes.py`

- [ ] **Step 1: 修改 ClassEnrollRequest Schema**

在 `backend/app/schemas/common.py` 中，给 `ClassEnrollRequest` 增加 `name` 字段：

```python
class ClassEnrollRequest(BaseModel):
    student_id: str = Field(min_length=1)
    name: str = ""  # 新增：姓名，为空时兼容旧逻辑
```

- [ ] **Step 2: 修改 enroll_student 支持自动创建用户**

在 `backend/app/services/class_service.py` 中修改 `enroll_student` 函数：

```python
def enroll_student(db: Session, class_id: int, student_id: str, name: str = ""):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        return None, "班级不存在"

    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        if not name:
            return None, "学生不存在，请提供姓名以自动创建账号"
        # 自动创建学生账号
        student = User(
            id=student_id,
            name=name,
            hashed_password=get_password_hash(DEFAULT_STUDENT_PASSWORD),
            role="student",
            major=cls.major or "",
            is_first_login=True,
        )
        db.add(student)
        db.flush()

    if student.role != "student":
        raise BusinessException(400, "仅可添加学生账号")

    existing = db.query(StudentClassEnrollment).filter(
        StudentClassEnrollment.class_id == class_id,
        StudentClassEnrollment.user_id == student_id,
    ).first()
    if existing:
        return existing, "已存在"

    enrollment = StudentClassEnrollment(user_id=student_id, class_id=class_id)
    try:
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
    except SQLAlchemyError:
        db.rollback()
        raise BusinessException(500, "添加学生失败")
    return enrollment, "created"
```

- [ ] **Step 3: 修改路由传入 name**

在 `backend/app/api/v1/routes/class_routes.py` 的 enroll 路由中，传入 `data.name`：

```python
enrollment, status = enroll_student(db, class_id, data.student_id, data.name)
```

- [ ] **Step 4: 注册逻辑一致 — 新注册用户设 is_first_login**

在 `backend/app/services/auth_service.py` 的 `register_user()` 中，确认 `User` 创建时包含 `is_first_login=False`（注册即算已改过密码）。

- [ ] **Step 5: 运行测试**

```bash
cd backend
python -m pytest tests/ -v
```

---

## 验收标准

1. `POST /api/password/change`：提供旧密码+新密码，成功修改并返回 `is_first_login=False`。
2. `POST /api/password/forgot`：提供学号+新密码，成功重置密码。
3. `GET /api/profile/wrong-questions`：返回该用户错题列表（按 question_id 去重，仅最近一次答错）。
4. `GET /api/profile/liked-projects`：返回该用户点赞过的作品列表。
5. `POST /api/classes/{class_id}/enroll`：传入学号+姓名，若学生不存在自动创建账号。
6. 登录返回值包含 `is_first_login` 字段。
7. 现有后端测试全部通过。

---

## 自检结果

- 覆盖了个人页面、登录改进、班级管理三组后端需求。
- 复用了现有密码校验逻辑（`RegisterRequest.password_complexity`），保持一致性。
- 错题去重逻辑确保"最近一次答对"的题不出现。
- 班级管理自动建号兼容旧逻辑（name 为空时要求用户已存在）。
- 没有新增角色或多租户模型。
- 没有改变统一响应格式。
