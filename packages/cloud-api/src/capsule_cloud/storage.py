"""
Object storage abstraction — Backblaze B2 / Cloudflare R2 / any S3-compatible
service in production; local filesystem fallback when credentials are not set.

Usage:
    from capsule_cloud import storage
    await storage.upload("workspace_id/session_id.capsule", raw_bytes)
    raw_bytes = await storage.download("workspace_id/session_id.capsule")
"""

from __future__ import annotations

import os


def _local_path(key: str) -> str:
    base = os.path.realpath(os.path.join(os.getcwd(), "data", "storage"))
    path = os.path.realpath(os.path.join(base, key))
    # Guard against path traversal — e.g. key = "../../etc/passwd"
    if not (path == base or path.startswith(base + os.sep)):
        raise ValueError(f"Unsafe storage key rejected: {key!r}")
    return path


def _local_write(key: str, data: bytes) -> None:
    path = _local_path(key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _local_read(key: str) -> bytes:
    path = _local_path(key)
    with open(path, "rb") as f:
        return f.read()


def _local_exists(key: str) -> bool:
    return os.path.exists(_local_path(key))


def _make_client(settings):  # pragma: no cover
    """Return a context-manager for an aiobotocore S3 client."""
    import aiobotocore.session  # type: ignore[import-untyped]

    session = aiobotocore.session.get_session()
    return session.create_client(
        "s3",
        endpoint_url=settings.storage_endpoint,
        aws_access_key_id=settings.storage_access_key,
        aws_secret_access_key=settings.storage_secret_key,
        region_name="auto",
    )


async def upload(key: str, data: bytes) -> None:
    """Upload raw bytes to object storage at *key*.

    Falls back to local disk when ``STORAGE_ENDPOINT`` is not configured
    (useful for local development).
    """
    from capsule_cloud.config import get_settings

    settings = get_settings()

    if not settings.storage_endpoint:
        _local_write(key, data)
        return

    async with _make_client(settings) as client:  # pragma: no cover
        await client.put_object(
            Bucket=settings.storage_bucket,
            Key=key,
            Body=data,
            ContentType="application/octet-stream",
        )


async def download(key: str) -> bytes:
    """Download raw bytes from object storage by *key*.

    Falls back to local disk when ``STORAGE_ENDPOINT`` is not configured.
    Raises ``FileNotFoundError`` (local) or a botocore ``NoSuchKey`` error
    (remote) if the key does not exist.
    """
    from capsule_cloud.config import get_settings

    settings = get_settings()

    if not settings.storage_endpoint:
        if not _local_exists(key):
            raise FileNotFoundError(
                f"Session file not found locally: {key}"
            )  # pragma: no cover
        return _local_read(key)

    async with _make_client(settings) as client:  # pragma: no cover
        response = await client.get_object(
            Bucket=settings.storage_bucket,
            Key=key,
        )
        return await response["Body"].read()


async def delete(key: str) -> None:  # pragma: no cover
    """Delete an object from storage (best-effort; does not raise on missing key)."""
    from capsule_cloud.config import get_settings

    settings = get_settings()

    if not settings.storage_endpoint:
        path = _local_path(key)
        if os.path.exists(path):
            os.remove(path)
        return

    async with _make_client(settings) as client:
        await client.delete_object(
            Bucket=settings.storage_bucket,
            Key=key,
        )
