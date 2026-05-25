"""统一存储抽象层"""
from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass
class StoredObject:
    """存储适配器返回的存储结果"""
    storage_provider: str
    bucket_name: str
    object_key: str
    stored_name: str
    content_type: str
    size_bytes: int


class StorageAdapter(Protocol):
    """存储适配器协议，所有适配器需实现以下方法"""

    def save_bytes(self, *, content: bytes, object_key: str, content_type: str) -> StoredObject:
        """保存字节内容，返回 StoredObject"""
        ...

    def open_stream(self, *, object_key: str) -> BinaryIO:
        """打开文件流，调用方负责关闭"""
        ...

    def exists(self, *, object_key: str) -> bool:
        """检查文件是否存在"""
        ...

    def delete(self, *, object_key: str) -> None:
        """删除文件"""
        ...
