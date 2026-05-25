"""SeaweedFS / S3 兼容存储适配器"""
import io
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.storage_service import StoredObject


class S3StorageAdapter:
    """基于 boto3 的 S3 存储适配器"""

    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self._bucket_public = settings.s3_bucket_public
        self._bucket_private = settings.s3_bucket_private

    def _resolve_bucket(self, bucket_name: str = "") -> str:
        return bucket_name or self._bucket_public

    def save_bytes(self, *, content: bytes, object_key: str, content_type: str = "",
                   bucket_name: str = "") -> StoredObject:
        bucket = self._resolve_bucket(bucket_name)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        self._client.put_object(Bucket=bucket, Key=object_key, Body=content, **extra_args)
        return StoredObject(
            storage_provider="s3",
            bucket_name=bucket,
            object_key=object_key,
            stored_name=object_key,
            content_type=content_type,
            size_bytes=len(content),
        )

    def open_stream(self, *, object_key: str, bucket_name: str = "") -> BinaryIO:
        bucket = self._resolve_bucket(bucket_name)
        resp = self._client.get_object(Bucket=bucket, Key=object_key)
        return resp["Body"]

    def exists(self, *, object_key: str, bucket_name: str = "") -> bool:
        bucket = self._resolve_bucket(bucket_name)
        try:
            self._client.head_object(Bucket=bucket, Key=object_key)
            return True
        except ClientError:
            return False

    def delete(self, *, object_key: str, bucket_name: str = "") -> None:
        bucket = self._resolve_bucket(bucket_name)
        self._client.delete_object(Bucket=bucket, Key=object_key)
