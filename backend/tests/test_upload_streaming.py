import hashlib
import io

from app.models.entities import StoredFile
from app.services.storage_service import StoredObject
from tests.conftest import auth_header


def test_local_upload_streams_to_disk_without_save_bytes(client, db_session, teacher_token, monkeypatch):
    """本地上传应分块写入磁盘，不再把完整文件交给 save_bytes。"""
    import app.services.file_service as file_service

    def fail_save_bytes(**kwargs):
        raise AssertionError("不应通过 save_bytes 整文件写入本地存储")

    monkeypatch.setattr(file_service._local_adapter, "save_bytes", fail_save_bytes)

    content = b"%PDF-1.4 streamed upload\n" + (b"x" * 128 * 1024)
    response = client.post(
        "/api/upload",
        files={"file": ("streamed.pdf", io.BytesIO(content), "application/pdf")},
        headers=auth_header(teacher_token),
    )
    data = response.json()

    assert data["code"] == 0
    assert data["data"]["size"] == len(content)
    assert data["data"]["content_type"] == "application/pdf"

    stored = db_session.query(StoredFile).filter(StoredFile.id == data["data"]["file_id"]).one()
    assert stored.size_bytes == len(content)
    assert stored.sha256 == hashlib.sha256(content).hexdigest()

    saved_path = file_service._local_adapter.root_dir / stored.object_key
    assert saved_path.read_bytes() == content


def test_s3_upload_streams_file_object_without_save_bytes(client, db_session, teacher_token, monkeypatch):
    """S3 上传应传递文件对象给适配器，不再把完整文件读成 bytes 后调用 save_bytes。"""
    import app.services.file_service as file_service

    class FakeS3Adapter:
        def __init__(self):
            self.saved_content = b""

        def save_bytes(self, **kwargs):
            raise AssertionError("不应通过 save_bytes 整文件上传到 S3")

        def save_fileobj(self, *, fileobj, object_key: str, content_type: str = "", bucket_name: str = "", size_bytes: int = 0):
            self.saved_content = fileobj.read()
            return StoredObject(
                storage_provider="s3",
                bucket_name=bucket_name or "test-public",
                object_key=object_key,
                stored_name=object_key,
                content_type=content_type,
                size_bytes=len(self.saved_content),
            )

        def delete(self, *, object_key: str, bucket_name: str = "") -> None:
            pass

    fake_adapter = FakeS3Adapter()
    monkeypatch.setattr("app.core.config.settings.storage_backend", "s3")
    monkeypatch.setattr(file_service, "_s3_adapter", fake_adapter)

    content = b"%PDF-1.4 streamed s3 upload\n" + (b"s" * 128 * 1024)
    response = client.post(
        "/api/upload",
        files={"file": ("streamed-s3.pdf", io.BytesIO(content), "application/pdf")},
        headers=auth_header(teacher_token),
    )
    data = response.json()

    assert data["code"] == 0
    assert data["data"]["storage_provider"] == "s3"
    assert data["data"]["size"] == len(content)
    assert data["data"]["content_type"] == "application/pdf"
    assert fake_adapter.saved_content == content

    stored = db_session.query(StoredFile).filter(StoredFile.id == data["data"]["file_id"]).one()
    assert stored.storage_provider == "s3"
    assert stored.size_bytes == len(content)
    assert stored.sha256 == hashlib.sha256(content).hexdigest()


def test_s3_adapter_save_fileobj_uses_boto3_streaming_upload():
    """S3 适配器应使用 upload_fileobj 上传文件对象，避免 put_object Body 接收完整 bytes。"""
    from app.services.storage_s3 import S3StorageAdapter

    class FakeS3Client:
        def __init__(self):
            self.uploaded_content = b""
            self.upload_kwargs = {}

        def put_object(self, **kwargs):
            raise AssertionError("不应通过 put_object Body 上传完整 bytes")

        def upload_fileobj(self, Fileobj, Bucket, Key, **kwargs):
            self.uploaded_content = Fileobj.read()
            self.upload_kwargs = {"Bucket": Bucket, "Key": Key, **kwargs}

    fake_client = FakeS3Client()
    adapter = S3StorageAdapter.__new__(S3StorageAdapter)
    adapter._client = fake_client
    adapter._bucket_public = "test-public"
    adapter._bucket_private = "test-private"
    adapter._transfer_config = object()

    content = b"%PDF-1.4 streaming adapter"
    stored = adapter.save_fileobj(
        fileobj=io.BytesIO(content),
        object_key="streaming/test.pdf",
        content_type="application/pdf",
        size_bytes=len(content),
    )

    assert fake_client.uploaded_content == content
    assert fake_client.upload_kwargs["Bucket"] == "test-public"
    assert fake_client.upload_kwargs["Key"] == "streaming/test.pdf"
    assert fake_client.upload_kwargs["ExtraArgs"] == {"ContentType": "application/pdf"}
    assert fake_client.upload_kwargs["Config"] is adapter._transfer_config
    assert stored.storage_provider == "s3"
    assert stored.size_bytes == len(content)
