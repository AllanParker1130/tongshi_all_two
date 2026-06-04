"""Teacher service"""
from sqlalchemy.orm import Session
from app.models.entities import (
    Announcement,
    AnnouncementClass,
    Class,
    Course,
    Project,
    QuizAttempt,
    StudentProgress,
    StudentClassEnrollment,
    TaskCompletion,
    User,
)


def _teacher_class_ids(db: Session, teacher_id: str) -> list[int]:
    return [
        row.id for row in db.query(Class.id)
        .filter(Class.created_by == teacher_id)
        .all()
    ]


def _teacher_student_ids(db: Session, teacher_id: str) -> list[str]:
    class_ids = _teacher_class_ids(db, teacher_id)
    if not class_ids:
        return []
    return [
        row.user_id for row in db.query(StudentClassEnrollment.user_id)
        .filter(StudentClassEnrollment.class_id.in_(class_ids))
        .distinct()
        .all()
    ]


def get_teacher_stats(db: Session, teacher_id: str):
    student_ids = _teacher_student_ids(db, teacher_id)
    total_students = len(student_ids)
    my_courses = db.query(Course).filter(Course.created_by == teacher_id).count()
    public_courses = db.query(Course).filter(Course.is_public.is_(True)).count()
    pending_reviews_query = db.query(Project).filter(Project.status == "pending")
    if student_ids:
        pending_reviews_query = pending_reviews_query.filter(Project.author_id.in_(student_ids))
    else:
        pending_reviews_query = pending_reviews_query.filter(False)
    pending_reviews = pending_reviews_query.count()
    weekly_exercises_query = db.query(QuizAttempt)
    if student_ids:
        weekly_exercises_query = weekly_exercises_query.filter(QuizAttempt.user_id.in_(student_ids))
    else:
        weekly_exercises_query = weekly_exercises_query.filter(False)
    weekly_exercises = weekly_exercises_query.count()  # simplified: total instead of weekly
    return {
        "total_students": total_students,
        "my_courses": my_courses,
        "public_courses": public_courses,
        "pending_reviews": pending_reviews,
        "weekly_exercises": weekly_exercises,
    }


def list_students(db: Session, teacher_id: str, class_id: int = None, page: int = None, page_size: int = None, keyword: str = None):
    class_ids = _teacher_class_ids(db, teacher_id)
    if class_id:
        if class_id not in class_ids:
            return [], 0
        class_ids = [class_id]
    if not class_ids:
        return [], 0
    query = (
        db.query(User, StudentClassEnrollment, Class)
        .join(StudentClassEnrollment, StudentClassEnrollment.user_id == User.id)
        .join(Class, Class.id == StudentClassEnrollment.class_id)
        .filter(User.role == "student", StudentClassEnrollment.class_id.in_(class_ids))
    )
    if keyword:
        query = query.filter(
            (User.id.like(f"%{keyword}%")) | (User.name.like(f"%{keyword}%"))
        )
    query = query.order_by(Class.id.asc(), StudentClassEnrollment.import_order.asc(), User.id.asc())
    rows = query.all()

    # 按学生 ID 去重：同一学生在多个班级时合并班级信息
    student_class_ids: dict[str, set[int]] = {}
    student_class_names: dict[str, list[str]] = {}
    student_first_enrollment: dict[str, StudentClassEnrollment] = {}
    student_user: dict[str, User] = {}
    for s, enrollment, class_ in rows:
        student_class_ids.setdefault(s.id, set()).add(class_.id)
        student_class_names.setdefault(s.id, []).append(class_.name)
        if s.id not in student_first_enrollment:
            student_first_enrollment[s.id] = enrollment
        student_user[s.id] = s

    unique_student_ids = list(student_user.keys())
    total = len(unique_student_ids)

    # 按当前排序规则排序：class_id asc, import_order asc
    unique_student_ids.sort(key=lambda sid: (
        min(student_class_ids[sid]) if student_class_ids[sid] else 0,
        student_first_enrollment[sid].import_order or 0,
        sid,
    ))

    # 分页
    if page and page_size:
        paged_ids = unique_student_ids[(page - 1) * page_size: page * page_size]
    else:
        paged_ids = unique_student_ids

    # 任务与完成数据
    class_task_ids: dict[int, set[int]] = {}
    completed_task_ids: dict[str, set[int]] = {sid: set() for sid in paged_ids}

    if paged_ids:
        task_rows = (
            db.query(Announcement.id, AnnouncementClass.class_id)
            .join(AnnouncementClass, AnnouncementClass.announcement_id == Announcement.id)
            .filter(
                Announcement.teacher_id == teacher_id,
                Announcement.type == "quiz",
                AnnouncementClass.class_id.in_(class_ids),
            )
            .all()
        )
        all_task_ids: set[int] = set()
        for task_id, owned_class_id in task_rows:
            class_task_ids.setdefault(owned_class_id, set()).add(task_id)
            all_task_ids.add(task_id)

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

    result = []
    for sid in paged_ids:
        s = student_user[sid]
        enrollment = student_first_enrollment[sid]
        class_id_list = list(student_class_ids[sid])
        class_name_str = "、".join(student_class_names[sid])

        progresses = (
            db.query(StudentProgress)
            .join(Course, Course.id == StudentProgress.course_id)
            .filter(
                StudentProgress.user_id == sid,
                StudentProgress.course_id.in_(
                    db.query(Class.course_id).filter(Class.id.in_(class_ids))
                ),
            )
            .all()
        )
        total_progress = sum(p.learn_progress for p in progresses)
        avg_progress = int(total_progress / len(progresses)) if progresses else 0

        total_done = sum(p.questions_done for p in progresses)
        total_accuracy = sum(p.accuracy for p in progresses)
        avg_accuracy = int(total_accuracy / len(progresses)) if progresses else 0

        assigned_task_ids: set[int] = set()
        for cid in class_id_list:
            assigned_task_ids.update(class_task_ids.get(cid, set()))
        completed_count = len(assigned_task_ids & completed_task_ids.get(sid, set()))
        total_task_count = len(assigned_task_ids)
        incomplete_count = max(total_task_count - completed_count, 0)
        task_completion_rate = int(round(completed_count / total_task_count * 100)) if total_task_count else 0

        result.append({
            "serial_no": enrollment.import_order or 0,
            "id": sid,
            "name": s.name,
            "major": s.major or "",
            "class_id": class_id_list[0] if class_id_list else None,
            "class_name": class_name_str,
            "progress": avg_progress,
            "exercises": total_done,
            "accuracy": avg_accuracy,
            "completed_tasks": completed_count,
            "incomplete_tasks": incomplete_count,
            "task_completion_rate": task_completion_rate,
        })
    return result, total


def list_all_projects(
    db: Session,
    status: str = None,
    page: int = None,
    page_size: int = None,
    teacher_id: str | None = None,
    keyword: str | None = None,
):
    query = db.query(Project)
    if teacher_id:
        student_ids = _teacher_student_ids(db, teacher_id)
        if student_ids:
            query = query.filter(Project.author_id.in_(student_ids))
        else:
            query = query.filter(False)
    if status:
        query = query.filter(Project.status == status)
    if keyword:
        query = query.filter(Project.title.like(f"%{keyword}%"))
    query = query.order_by(Project.date.desc())
    total = query.count()
    if page and page_size:
        projects = query.offset((page - 1) * page_size).limit(page_size).all()
    else:
        projects = query.all()
    return projects, total
