"""本地文件存储适配器"""
from pathlib import Path
from typing import BinaryIO

from app.services.storage_service import StoredObject


class LocalStorageAdapter:
    """本地文件系统存储适配器，兼容历史 /uploads 目录"""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, *, content: bytes, object_key: str, content_type: str = "") -> StoredObject:
        file_path = self.root_dir / object_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        return StoredObject(
            storage_provider="local",
            bucket_name="",
            object_key=object_key,
            stored_name=object_key,
            content_type=content_type,
            size_bytes=len(content),
        )

    def open_stream(self, *, object_key: str) -> BinaryIO:
        file_path = self.root_dir / object_key
        return open(file_path, "rb")

    def exists(self, *, object_key: str) -> bool:
        return (self.root_dir / object_key).is_file()

    def delete(self, *, object_key: str) -> None:
        file_path = self.root_dir / object_key
        if file_path.is_file():
            file_path.unlink()
