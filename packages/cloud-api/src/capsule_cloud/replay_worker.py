"""
Modal cloud replay worker.

Deploys as a serverless function on Modal. Each invocation:
  1. Downloads the .capsule file from Backblaze B2 (or local disk in dev)
  2. Runs ``capsule replay`` in cassette mode (deterministic, mocked LLM calls)
  3. Returns a result dict with status, stdout tail, and any error

Deploy with:
    modal deploy src/capsule_cloud/replay_worker.py

The FastAPI server calls run_replay.spawn(...) to fire-and-forget.
Check the Modal dashboard (https://modal.com) for execution logs.
"""

from __future__ import annotations

import modal

# The image must have the capsule SDK + async S3 client
_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "capsule-sdk>=0.1.0",
        "aiobotocore[boto3]>=2.13.0",
        "zstandard>=0.22.0",
    )
)

app = modal.App("capsule-replay", image=_image)


async def _download(
    key: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket: str,
) -> bytes:
    """Download a .capsule file from B2/R2 or local disk."""
    if not endpoint:
        import os
        path = os.path.join(os.getcwd(), "data", "storage", key)
        with open(path, "rb") as f:
            return f.read()
    import aiobotocore.session  # type: ignore[import-untyped]
    session = aiobotocore.session.get_session()
    async with session.create_client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    ) as client:
        resp = await client.get_object(Bucket=bucket, Key=key)
        return await resp["Body"].read()


@app.function(timeout=300, memory=512)
async def run_replay(
    storage_path: str,
    mode: str = "cassette",
    branch_from_step: int | None = None,
    storage_endpoint: str = "",
    storage_access_key: str = "",
    storage_secret_key: str = "",
    storage_bucket: str = "capsule-sessions",
) -> dict:
    """Execute a deterministic replay of a .capsule session.

    Args:
        storage_path: The object key, e.g. ``workspace_id/session_id.capsule``
        mode: ``"cassette"`` (replay recorded responses) or ``"live"`` (re-run live)
        branch_from_step: Fork replay from this step index (None = full replay)
        storage_*: B2/R2 credentials forwarded from the API server

    Returns:
        dict with keys: status, returncode, stdout (last 4 KB), stderr (last 2 KB)
    """
    import os
    import subprocess
    import tempfile

    # Download the .capsule archive
    raw = await _download(
        storage_path,
        storage_endpoint,
        storage_access_key,
        storage_secret_key,
        storage_bucket,
    )

    with tempfile.NamedTemporaryFile(suffix=".capsule", delete=False) as f:
        f.write(raw)
        tmp_path = f.name

    try:
        cmd = ["capsule", "replay", tmp_path, f"--mode={mode}"]
        if branch_from_step is not None:
            cmd += [f"--branch-from={branch_from_step}"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=240,
        )

        return {
            "status": "completed" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "returncode": -1,
            "stdout": "",
            "stderr": "Replay timed out after 240 seconds",
        }
    except Exception as exc:
        return {
            "status": "error",
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
        }
    finally:
        os.unlink(tmp_path)
