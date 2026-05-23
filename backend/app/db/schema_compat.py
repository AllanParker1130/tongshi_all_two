"""数据库结构兼容修复。"""
from sqlalchemy import inspect, text


def ensure_schema_compatibility(engine) -> None:
    """补齐旧数据库缺失的业务字段和关联表。"""
    with engine.begin() as conn:
        inspector = inspect(conn)
        table_names = set(inspector.get_table_names())

        if "chapters" in table_names:
            columns = {column["name"] for column in inspector.get_columns("chapters")}
            required_columns = [
                ("day_of_week", "VARCHAR(16)", "''"),
                ("class_periods", "VARCHAR(32)", "''"),
                ("schedule_note", "VARCHAR(128)", "''"),
            ]

            for name, column_type, default_value in required_columns:
                if name not in columns:
                    conn.execute(text(
                        f"ALTER TABLE chapters ADD COLUMN {name} {column_type} DEFAULT {default_value}"
                    ))

        if "projects" in table_names and "project_images" not in table_names:
            dialect_name = conn.dialect.name
            if dialect_name == "sqlite":
                conn.execute(text("""
                    CREATE TABLE project_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        image_url VARCHAR(512) NOT NULL DEFAULT '',
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                    )
                """))
            else:
                conn.execute(text("""
                    CREATE TABLE project_images (
                        id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        project_id INTEGER NOT NULL,
                        image_url VARCHAR(512) NOT NULL DEFAULT '',
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        CONSTRAINT fk_project_images_project_id
                            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                    )
                """))

            conn.execute(text(
                "CREATE INDEX ix_project_images_project_id ON project_images (project_id)"
            ))
