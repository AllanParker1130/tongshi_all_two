"""管理员公共课程服务。"""
from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.entities import Course, Material, Question, QuizAttempt
from app.services.public_course_sync_service import (
    delete_synced_materials,
    delete_synced_questions,
    sync_course_name_to_copies,
    sync_material_to_course_copies,
    sync_question_to_course_copies,
)


def _get_public_course(db: Session, course_id: int) -> Course | None:
    return db.query(Course).filter(Course.id == course_id, Course.is_public.is_(True)).first()


def list_public_courses(db: Session) -> list[Course]:
    return db.query(Course).filter(Course.is_public.is_(True)).order_by(Course.id.desc()).all()


def get_course_sync_status(db: Session, course: Course) -> dict:
    """计算公共课程的同步状态摘要。"""
    copies = db.query(Course).filter(Course.source_course_id == course.id).all()
    sync_copy_count = len(copies)
    synced_material_count = db.query(Material).filter(
        Material.source_material_id.in_([m.id for m in course.materials])
    ).count() if course.materials else 0
    synced_question_count = db.query(Question).filter(
        Question.source_question_id.in_([q.id for q in course.questions])
    ).count() if course.questions else 0

    total_items = len(course.materials) + len(course.questions)
    synced_items = synced_material_count + synced_question_count
    if total_items == 0 or sync_copy_count == 0:
        sync_status = "not_synced"
    elif synced_items >= total_items * sync_copy_count:
        sync_status = "synced"
    else:
        sync_status = "partial"

    return {
        "sync_copy_count": sync_copy_count,
        "synced_material_count": synced_material_count,
        "synced_question_count": synced_question_count,
        "sync_status": sync_status,
    }


def create_public_course(db: Session, name: str, admin_id: str) -> Course:
    if db.query(Course).filter(Course.name == name, Course.created_by == admin_id).first():
        raise BusinessException(400, "公共课程已存在")
    course = Course(name=name, created_by=admin_id, is_public=True)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_public_course(db: Session, course_id: int, name: str) -> Course | None:
    course = _get_public_course(db, course_id)
    if not course:
        return None
    course.name = name
    sync_course_name_to_copies(db, course)
    db.commit()
    db.refresh(course)
    return course


def delete_public_course(db: Session, course_id: int) -> bool:
    course = _get_public_course(db, course_id)
    if not course:
        return False
    copies = db.query(Course).filter(Course.source_course_id == course.id).all()
    source_material_ids = [material.id for material in course.materials]
    source_question_ids = [question.id for question in course.questions]
    for copy in copies:
        copy.source_course_id = None
    if source_material_ids:
        db.query(Material).filter(
            Material.source_material_id.in_(source_material_ids),
        ).update({Material.source_material_id: None}, synchronize_session=False)
    if source_question_ids:
        # 先清理引用这些题目的 QuizAttempt，防止外键约束阻止题目删除
        # （即使模型已声明 ondelete=CASCADE，旧数据库可能尚未执行迁移）
        db.query(QuizAttempt).filter(
            QuizAttempt.question_id.in_(source_question_ids),
        ).delete(synchronize_session=False)
        db.query(Question).filter(
            Question.source_question_id.in_(source_question_ids),
        ).update({Question.source_question_id: None}, synchronize_session=False)
    db.delete(course)
    db.commit()
    return True


def get_public_material(db: Session, material_id: int) -> Material | None:
    """查询公共课程资料（仅查存在性，不触发同步）。"""
    return db.query(Material).join(Course).filter(
        Material.id == material_id,
        Course.is_public.is_(True),
    ).first()


def get_public_question(db: Session, question_id: int) -> Question | None:
    """查询公共课程题目（仅查存在性，不触发同步）。"""
    return db.query(Question).join(Course).filter(
        Question.id == question_id,
        Course.is_public.is_(True),
    ).first()


def list_public_materials(db: Session, course_id: int) -> list[Material]:
    course = _get_public_course(db, course_id)
    if not course:
        raise BusinessException(404, "公共课程不存在")
    return db.query(Material).filter(Material.course_id == course_id).order_by(Material.id).all()


def create_public_material(db: Session, course_id: int, data: dict) -> Material:
    course = _get_public_course(db, course_id)
    if not course:
        raise BusinessException(404, "公共课程不存在")
    material = Material(
        course_id=course.id,
        date=datetime.now().strftime("%Y-%m-%d"),
        **data,
    )
    db.add(material)
    db.flush()
    sync_material_to_course_copies(db, material)
    db.commit()
    db.refresh(material)
    return material


def update_public_material(db: Session, material_id: int, data: dict) -> Material | None:
    material = db.query(Material).join(Course).filter(
        Material.id == material_id,
        Course.is_public.is_(True),
    ).first()
    if not material:
        return None
    for key, value in data.items():
        if value is not None and hasattr(material, key):
            setattr(material, key, value)
    sync_material_to_course_copies(db, material)
    db.commit()
    db.refresh(material)
    return material


def delete_public_material(db: Session, material_id: int) -> bool:
    material = db.query(Material).join(Course).filter(
        Material.id == material_id,
        Course.is_public.is_(True),
    ).first()
    if not material:
        return False
    delete_synced_materials(db, material.id)
    db.delete(material)
    db.commit()
    return True


def list_public_questions(db: Session, course_id: int) -> list[Question]:
    course = _get_public_course(db, course_id)
    if not course:
        raise BusinessException(404, "公共课程不存在")
    return db.query(Question).filter(Question.course_id == course_id).order_by(Question.id).all()


def create_public_question(db: Session, course_id: int, data: dict) -> Question:
    course = _get_public_course(db, course_id)
    if not course:
        raise BusinessException(404, "公共课程不存在")
    data["tags"] = _normalize_tags(data.get("tags"))
    question = Question(course_id=course.id, **data)
    db.add(question)
    db.flush()
    sync_question_to_course_copies(db, question)
    db.commit()
    db.refresh(question)
    return question


def update_public_question(db: Session, question_id: int, data: dict) -> Question | None:
    question = db.query(Question).join(Course).filter(
        Question.id == question_id,
        Course.is_public.is_(True),
    ).first()
    if not question:
        return None
    for key, value in data.items():
        if value is not None and hasattr(question, key):
            setattr(question, key, _normalize_tags(value) if key == "tags" else value)
    sync_question_to_course_copies(db, question)
    db.commit()
    db.refresh(question)
    return question


def delete_public_question(db: Session, question_id: int) -> bool:
    question = db.query(Question).join(Course).filter(
        Question.id == question_id,
        Course.is_public.is_(True),
    ).first()
    if not question:
        return False
    delete_synced_questions(db, question.id)
    db.delete(question)
    db.commit()
    return True


def get_course_by_id(db: Session, course_id: int) -> Course | None:
    """按 ID 查询课程（不限公共标记）。"""
    return db.query(Course).filter(Course.id == course_id).first()


def _row_value(row: dict, *keys: str):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return value
    return ""


def _normalize_tags(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = re.split(r"[,，、|/；;]+", str(value))
    seen = set()
    tags = []
    for item in raw_items:
        tag = str(item).strip()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def import_questions_to_public_course(db: Session, course_id: int, rows: list[dict]) -> dict:
    """批量导入题目到公共课程，并同步到教师副本。"""
    course = _get_public_course(db, course_id)
    if not course:
        raise BusinessException(404, "公共课程不存在")
    success_count = 0
    fail_count = 0
    errors = []
    for idx, row in enumerate(rows, start=2):
        try:
            q_type = str(_row_value(row, "题型", "type")).strip()
            stem = str(_row_value(row, "题干", "stem")).strip()
            if not stem:
                raise BusinessException(400, "题干为空")
            options = str(_row_value(row, "选项（选择题用 | 分隔）", "选项", "options")).strip()
            option_list = [x.strip() for x in options.split("|") if x.strip()] if options else []
            answer = str(_row_value(row, "答案", "answer")).strip()
            explanation = str(_row_value(row, "解析", "explanation")).strip()
            tags = _normalize_tags(_row_value(row, "标签", "课程标签", "tags", "course_tags"))
            if q_type not in {"choice", "fill", "multi_choice"}:
                raise BusinessException(400, "题型必须为 choice、fill 或 multi_choice")
            if q_type in {"choice", "multi_choice"} and not option_list:
                raise BusinessException(400, "选择题必须填写选项")
            question = Question(
                type=q_type, course_id=course.id, stem=stem,
                options=option_list, answer=answer, explanation=explanation, tags=tags,
            )
            db.add(question)
            db.flush()
            sync_question_to_course_copies(db, question)
            success_count += 1
        except Exception as exc:
            fail_count += 1
            errors.append({"row": idx, "reason": str(exc)})
    db.commit()
    return {"success_count": success_count, "fail_count": fail_count, "errors": errors}
