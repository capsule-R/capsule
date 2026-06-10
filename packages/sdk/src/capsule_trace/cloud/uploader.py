"""Upload a local session to the Capsule Cloud API."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("capsule.cloud")


def _get_cloud_config() -> dict[str, str]:
    """Read cloud config from env vars or ~/.capsule/cloud.json."""
    base_url = os.environ.get("CAPSULE_CLOUD_URL", "https://api.capsule.dev")
    api_key = os.environ.get("CAPSULE_API_KEY", "")
    workspace_id = os.environ.get("CAPSULE_WORKSPACE_ID", "")

    # Fall back to config file
    config_file = Path.home() / ".capsule" / "cloud.json"
    if config_file.exists() and (not api_key or not workspace_id):
        try:
            data = json.loads(config_file.read_text())
            base_url = base_url or data.get("base_url", base_url)
            api_key = api_key or data.get("api_key", "")
            workspace_id = workspace_id or data.get("workspace_id", "")
        except Exception:
            pass

    return {"base_url": base_url, "api_key": api_key, "workspace_id": workspace_id}


def upload_session(
    session_id: str,
    *,
    agent_name: str | None = None,
    agent_version: str | None = None,
    tags: list[str] | None = None,
    user_metadata: dict[str, Any] | None = None,
    auto_redact: bool = False,
) -> dict[str, Any]:
    """Export the session to a .capsule file and upload it to Capsule Cloud.

    Returns the API response dict.

    Raises:
        RuntimeError: if CAPSULE_API_KEY or CAPSULE_WORKSPACE_ID are not configured.
        httpx.HTTPStatusError: if the upload fails.
    """
    try:
        import httpx
    except ImportError as exc:
        raise ImportError("httpx is required for cloud uploads: pip install httpx") from exc

    from capsule_trace.core.exporter import export_capsule
    from capsule_trace.storage.sqlite import SQLiteBackend

    config = _get_cloud_config()
    if not config["api_key"]:
        raise RuntimeError(
            "CAPSULE_API_KEY is not set. "
            "Run `capsule cloud login` or set the env var."
        )
    if not config["workspace_id"]:
        raise RuntimeError(
            "CAPSULE_WORKSPACE_ID is not set. "
            "Set it via env var or `capsule cloud login`."
        )

    # Export to a temp .capsule file
    import tempfile

    backend = SQLiteBackend.default()
    meta = backend.read_session_metadata(session_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        capsule_path = export_capsule(session_id, backend, Path(tmpdir) / f"{session_id}.capsule")

        upload_metadata = {
            "session_id": session_id,
            "agent_name": agent_name or meta.agent_name,
            "agent_version": agent_version or meta.agent_version,
            "tags": tags if tags is not None else meta.tags,
            "user_metadata": user_metadata if user_metadata is not None else meta.user_metadata,
            "auto_redact": auto_redact,
        }

        url = f"{config['base_url']}/api/v1/workspaces/{config['workspace_id']}/sessions"
        headers = {"Authorization": f"Bearer {config['api_key']}"}

        with open(capsule_path, "rb") as f:
            resp = httpx.post(
                url,
                headers=headers,
                files={"file": (capsule_path.name, f, "application/octet-stream")},
                data={"metadata": json.dumps(upload_metadata)},
                timeout=120.0,
            )

        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        logger.info(
            "capsule.cloud.uploaded",
            session_id=session_id,
            response_id=result.get("id"),
        )
        return result
