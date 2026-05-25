"""统一文件访问路由"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.core.security import get_current_user
from app.db.session import get_db
from app.services.file_service import resolve_file_stream

router = APIRouter()


@router.get("/files/{file_id}")
def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """通过 file_id 统一访问文件，自动分发到本地或 S3 存储"""
    record, stream = resolve_file_stream(db, file_id)

    if record is None:
        raise BusinessException(404, "文件不存在")

    if stream is None:
        raise BusinessException(404, "文件内容已丢失")

    content_type = record.content_type or "application/octet-stream"
    filename = record.original_name or record.stored_name or "download"

    return StreamingResponse(
        stream,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
