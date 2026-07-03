"""
Modal cloud replay worker.

Deploys as a serverless function on Modal. Each invocation:
  1. Downloads the .capsule file from Backblaze B2 (or local disk in dev)
  2. Runs ``capsule-trace replay`` and parses its real --json verdict
  3. Writes that result back to the `replays` table so the API's
     GET /replays/{id} can report it (see _write_result below) — the API
     spawns this function fire-and-forget and has no other way to learn
     the outcome.

Deploy with:
    modal deploy src/capsule_cloud/replay_worker.py

The FastAPI server calls run_replay.spawn(...) to fire-and-forget.
Check the Modal dashboard (https://modal.com) for execution logs.
"""

from __future__ import annotations

import modal

# The image must have the capsule SDK + async S3 client + a Postgres driver
# for writing the result back to the replays table.
# NOTE: the PyPI package is "capsule-trace" (see packages/sdk/pyproject.toml);
# "capsule-sdk" is not a real package and would fail to install.
_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "capsule-sdk>=0.1.0",
        "aiobotocore[boto3]>=2.13.0",
        "zstandard>=0.22.0",
        "sqlalchemy>=2.0.0",
        "asyncpg>=0.29.0",
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


async def _write_result(
    replay_id: str,
    database_url: str,
    status: str,
    result: dict | None,
    error: str | None,
) -> None:
    """Write the real replay result back to the replays table.

    Best-effort: a failure here must not raise past run_replay — there's
    nothing more this fire-and-forget job can do. The row simply stays
    "queued" rather than a fabricated verdict, which is the honest failure
    mode.
    """
    import json as _json

    try:
        import sqlalchemy as sa
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(database_url)
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    sa.text(
                        "UPDATE replays SET status = :status, "
                        "result_json = :result_json, error_message = :error_message, "
                        "updated_at = now() WHERE id = :id"
                    ),
                    {
                        "status": status,
                        "result_json": _json.dumps(result) if result is not None else None,
                        "error_message": error,
                        "id": replay_id,
                    },
                )
        finally:
            await engine.dispose()
    except Exception:
        pass


@app.function(timeout=300, memory=512)
async def run_replay(
    replay_id: str,
    storage_path: str,
    mode: str = "cassette",
    branch_from_step: int | None = None,
    storage_endpoint: str = "",
    storage_access_key: str = "",
    storage_secret_key: str = "",
    storage_bucket: str = "capsule-sessions",
    database_url: str = "",
) -> dict:
    """Execute a deterministic replay of a .capsule session.

    Args:
        replay_id: Row in the `replays` table to update with the real result.
        storage_path: The object key, e.g. ``workspace_id/session_id.capsule``
        mode: ``"cassette"`` (replay recorded responses) or ``"live"`` (re-run live)
        branch_from_step: Fork replay from this step index (None = full replay)
        storage_*: B2/R2 credentials forwarded from the API server
        database_url: Connection string for writing the result back

    Returns:
        dict with keys: status, returncode, stdout (last 4 KB), stderr (last 2 KB)
    """
    import json
    import os
    import subprocess
    import tempfile

    async def _finish(status: str, result: dict | None, error: str | None) -> dict:
        if database_url:
            await _write_result(replay_id, database_url, status, result, error)
        return {"status": status, "result": result, "error": error}

    # Download the .capsule archive
    try:
        raw = await _download(
            storage_path,
            storage_endpoint,
            storage_access_key,
            storage_secret_key,
            storage_bucket,
        )
    except Exception as exc:
        return await _finish("error", None, f"Failed to download session data: {exc}")

    with tempfile.NamedTemporaryFile(suffix=".capsule", delete=False) as f:
        f.write(raw)
        tmp_path = f.name

    try:
        cmd = ["capsule", "replay", tmp_path, f"--mode={mode}"]
        if branch_from_step is not None:
            cmd += [f"--branch-from={branch_from_step}"]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=240,
        )

        if proc.returncode != 0:
            return await _finish(
                "error", None, proc.stderr[-2000:] or f"capsule replay exited with code {proc.returncode}"
            )

        try:
            parsed = json.loads(proc.stdout)
        except (json.JSONDecodeError, ValueError) as exc:
            return await _finish("error", None, f"Could not parse replay output as JSON: {exc}")

        result = {
            "is_deterministic": parsed.get("is_deterministic"),
            "integrity_ok": parsed.get("integrity_ok"),
            "replayed_steps": parsed.get("replayed_steps"),
            "original_steps": parsed.get("original_steps"),
        }
        return await _finish("completed", result, None)
    except subprocess.TimeoutExpired:
        return await _finish("error", None, "Replay timed out after 240 seconds")
    except Exception as exc:
        return await _finish("error", None, str(exc))
    finally:
        os.unlink(tmp_path)
