"""数据库结构兼容修复测试"""
import os

from sqlalchemy import create_engine, inspect, text

from app.core.config import Settings
from app.db.schema_compat import ensure_schema_compatibility


def test_ensure_schema_compatibility_adds_chapter_schedule_columns():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE chapters (
                id INTEGER PRIMARY KEY,
                num VARCHAR(8) NOT NULL,
                title VARCHAR(64) NOT NULL
            )
        """))

    ensure_schema_compatibility(engine)

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("chapters")}

    assert {"day_of_week", "class_periods", "schedule_note"}.issubset(columns)


def test_ensure_schema_compatibility_creates_project_images_table():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                title VARCHAR(128) NOT NULL
            )
        """))

    ensure_schema_compatibility(engine)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    columns = {column["name"] for column in inspector.get_columns("project_images")}

    assert "project_images" in table_names
    assert {"id", "project_id", "image_url", "sort_order"}.issubset(columns)


def test_settings_defaults_keep_mysql_and_local_storage(monkeypatch):
    """未设置 S3 环境变量时，storage_backend 默认 local，DATABASE_URL 不受影响"""
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://root:123456@127.0.0.1:3306/tongshi?charset=utf8mb4")
    settings = Settings()
    assert settings.database_url.startswith("mysql+pymysql://")
    assert settings.storage_backend in {"local", "s3"}


def test_ensure_schema_compatibility_creates_stored_files_table():
    """兼容脚本应自动创建 stored_files 表"""
    engine = create_engine("sqlite:///:memory:")

    ensure_schema_compatibility(engine)

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    assert "stored_files" in table_names
    columns = {column["name"] for column in inspector.get_columns("stored_files")}
    assert {"id", "biz_type", "biz_id", "storage_provider", "bucket_name",
            "object_key", "original_name", "stored_name", "content_type",
            "extension", "size_bytes", "sha256", "status", "created_by",
            "created_at"}.issubset(columns)


def test_ensure_schema_compatibility_adds_file_columns_to_business_tables():
    """兼容脚本应为 materials、projects、project_images 补齐 file_id 列"""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id VARCHAR(32) PRIMARY KEY,
                name VARCHAR(64) NOT NULL,
                hashed_password VARCHAR(128) NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE chapters (
                id INTEGER PRIMARY KEY,
                num VARCHAR(8) NOT NULL,
                title VARCHAR(64) NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE materials (
                id INTEGER PRIMARY KEY,
                chapter_id INTEGER NOT NULL,
                type VARCHAR(16) NOT NULL,
                title VARCHAR(128) NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                title VARCHAR(128) NOT NULL,
                author_id VARCHAR(32) NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE project_images (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                image_url VARCHAR(512) NOT NULL DEFAULT ''
            )
        """))

    ensure_schema_compatibility(engine)

    inspector = inspect(engine)
    mat_cols = {c["name"] for c in inspector.get_columns("materials")}
    proj_cols = {c["name"] for c in inspector.get_columns("projects")}
    img_cols = {c["name"] for c in inspector.get_columns("project_images")}

    assert "file_id" in mat_cols
    assert "report_file_id" in proj_cols
    assert "cover_file_id" in proj_cols
    assert "file_id" in img_cols
