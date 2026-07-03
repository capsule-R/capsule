"""Capsule CLI — entry point for all `capsule` commands."""

from __future__ import annotations

import json
import sys
from datetime import UTC
from pathlib import Path
from typing import Any, cast

import click
from rich.console import Console
from rich.table import Table

console = Console()


# ── config helpers ────────────────────────────────────────────


def load_config() -> dict[str, Any] | None:
    config_path = Path.home() / ".capsule" / "config.json"
    if not config_path.exists():
        return None
    with open(config_path) as f:
        return cast("dict[str, Any]", json.load(f))


def save_config(data: dict[str, Any]) -> None:
    config_dir = Path.home() / ".capsule"
    config_dir.mkdir(exist_ok=True)
    with open(config_dir / "config.json", "w") as f:
        json.dump(data, f, indent=2)


@click.group()
@click.version_option(package_name="capsule-trace")
def main() -> None:
    """Capsule — deterministic replay & time-travel debugger for AI agents."""


# ── capsule list ──────────────────────────────────────────────


@main.command("list")
@click.option("--agent", default=None, help="Filter by agent name")
@click.option("--status", default=None, help="Filter by status (success|failed)")
@click.option("--limit", default=20, show_default=True, help="Max results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_sessions(agent: str | None, status: str | None, limit: int, as_json: bool) -> None:
    """List captured sessions."""
    from capsule_trace.storage.sqlite import SQLiteBackend

    backend = SQLiteBackend.default()
    sessions = backend.list_sessions(limit=limit)

    if agent:
        sessions = [s for s in sessions if agent.lower() in s.agent_name.lower()]
    if status:
        sessions = [s for s in sessions if s.status.value == status]

    if as_json:
        click.echo(json.dumps([s.model_dump(mode="json") for s in sessions], indent=2, default=str))
        return

    if not sessions:
        console.print("[dim]No sessions found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Agent")
    table.add_column("Status")
    table.add_column("Steps", justify="right")
    table.add_column("Duration")
    table.add_column("Started At")

    for s in sessions:
        status_style = "green" if s.status.value == "success" else "red"
        duration = f"{s.duration_ms:.0f}ms" if s.duration_ms else "-"
        table.add_row(
            s.session_id[:26],
            s.agent_name,
            f"[{status_style}]{s.status.value}[/{status_style}]",
            str(s.step_count),
            duration,
            str(s.started_at)[:19],
        )

    console.print(table)


# ── capsule show ──────────────────────────────────────────────


@main.command("show")
@click.argument("session_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_session(session_id: str, as_json: bool) -> None:
    """Show details of a session."""
    from capsule_trace.storage.sqlite import SQLiteBackend

    backend = SQLiteBackend.default()
    try:
        meta = backend.read_session_metadata(session_id)
        events = backend.read_events(session_id)
    except KeyError:
        console.print(f"[red]Session not found:[/red] {session_id}")
        sys.exit(1)

    if as_json:
        out = {
            "session": meta.model_dump(mode="json"),
            "events": [e.model_dump_json_safe() for e in events],
        }
        click.echo(json.dumps(out, indent=2, default=str))
        return

    console.print(f"\n[bold]Session[/bold] [cyan]{meta.session_id}[/cyan]")
    console.print(f"  Agent:    {meta.agent_name}")
    console.print(f"  Status:   {meta.status.value}")
    console.print(f"  Steps:    {meta.step_count}")
    console.print(f"  Duration: {meta.duration_ms:.0f}ms" if meta.duration_ms else "  Duration: -")
    console.print(f"  Started:  {meta.started_at}")

    if meta.error:
        console.print(f"\n[red]Error:[/red] {meta.error.type}: {meta.error.message}")

    console.print(f"\n[bold]Events[/bold] ({len(events)})")
    for event in events:
        console.print(
            f"  [{event.step_index:03d}] {event.event_type.value} — {event.duration_ms:.1f}ms"
        )


# ── capsule export ────────────────────────────────────────────


@main.command("export")
@click.argument("session_id")
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Output .capsule file path (default: <session_id>.capsule)",
)
def export_session(session_id: str, output: str | None) -> None:
    """Export a session to a .capsule file."""
    from capsule_trace.core.exporter import export_capsule
    from capsule_trace.storage.sqlite import SQLiteBackend

    backend = SQLiteBackend.default()
    out_path = Path(output) if output else Path(f"{session_id}.capsule")

    try:
        result = export_capsule(session_id, backend, out_path)
        size_kb = result.stat().st_size / 1024
        console.print(f"[green]Exported[/green] → {result} ({size_kb:.1f} KB)")
    except KeyError:
        console.print(f"[red]Session not found:[/red] {session_id}")
        sys.exit(1)


# ── capsule import ────────────────────────────────────────────


@main.command("import")
@click.argument("capsule_file", type=click.Path(exists=True))
def import_capsule(capsule_file: str) -> None:
    """Import a .capsule file into the local store."""
    from capsule_trace.core.importer import import_capsule_file

    path = Path(capsule_file)
    try:
        session_id = import_capsule_file(path)
        console.print(f"[green]Imported[/green] session {session_id}")
    except Exception as exc:
        console.print(f"[red]Import failed:[/red] {exc}")
        sys.exit(1)


# ── capsule replay ────────────────────────────────────────────


@main.command("replay")
@click.argument("session_id_or_file")
@click.option("--mode", default="cassette", type=click.Choice(["cassette", "live"]))
@click.option("--json", "as_json", is_flag=True, help="Output result as JSON")
def replay_session(session_id_or_file: str, mode: str, as_json: bool) -> None:
    """Replay a captured session deterministically from cassettes."""
    from pathlib import Path

    from capsule_trace.replay.engine import Replayer

    try:
        p = Path(session_id_or_file)
        if p.exists() and p.suffix == ".capsule":
            replayer = Replayer.from_file(p)
        else:
            replayer = Replayer.from_session_id(session_id_or_file)
    except Exception as exc:
        console.print(f"[red]Failed to load session:[/red] {exc}")
        sys.exit(1)

    console.print(
        f"Replaying [cyan]{replayer.session_id}[/cyan] "
        f"({replayer.step_count} steps) in [bold]{mode}[/bold] mode..."
    )

    result = replayer.replay(mode=mode)

    if as_json:
        click.echo(
            json.dumps(
                {
                    "session_id": result.session_id,
                    "replayed_steps": result.replayed_step_count,
                    "original_steps": result.original_step_count,
                    "is_deterministic": result.is_deterministic,
                    "integrity_ok": result.integrity_ok,
                },
                indent=2,
            )
        )
        return

    status = (
        "[green]deterministic[/green]" if result.is_deterministic else "[yellow]mismatch[/yellow]"
    )
    console.print(f"\nResult: {status}")
    console.print(f"  Steps replayed:  {result.replayed_step_count}/{result.original_step_count}")
    console.print(f"  Integrity check: {'✓' if result.integrity_ok else '✗'}")

    for e in result.events:
        has_cassette = (
            "[dim](cassette)[/dim]" if e.event_type.value in ("llm_call", "tool_call") else ""
        )
        console.print(f"  [{e.step_index:03d}] {e.event_type.value} {has_cassette}")


# ── capsule branch ────────────────────────────────────────────


@main.command("branch")
@click.argument("session_id")
@click.option("--from-step", "-s", required=True, type=int, help="Step index to branch from")
@click.option(
    "--modify", "-m", multiple=True, help="key=value modifications (e.g. temperature=0.0)"
)
def branch_session(session_id: str, from_step: int, modify: tuple[str, ...]) -> None:
    """Branch a session from a specific step with optional modifications."""
    modifications: dict[str, str] = {}
    for item in modify:
        if "=" not in item:
            console.print(f"[red]Invalid modification (expected key=value):[/red] {item}")
            sys.exit(1)
        k, v = item.split("=", 1)
        modifications[k.strip()] = v.strip()

    from capsule_trace.replay.engine import Replayer

    try:
        replayer = Replayer.from_session_id(session_id)
    except Exception as exc:
        console.print(f"[red]Failed to load session:[/red] {exc}")
        sys.exit(1)

    try:
        branch = replayer.branch_from_step(from_step, modifications)
    except IndexError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    console.print(f"Branch context ready: [cyan]{session_id}[/cyan] @ step {from_step}")
    console.print(f"  Pre-branch events: {len(branch.pre_branch_events)}")
    console.print(f"  Modifications:     {branch.modifications or '(none)'}")
    console.print(
        "\n[dim]Re-run your agent code under this branch context to continue "
        "from step {from_step} with live LLM calls.[/dim]"
    )


# ── capsule diff ──────────────────────────────────────────────


@main.command("diff")
@click.argument("session_id_1")
@click.argument("session_id_2")
def diff_sessions(session_id_1: str, session_id_2: str) -> None:
    """Show differences between two sessions."""
    from capsule_trace.storage.sqlite import SQLiteBackend

    backend = SQLiteBackend.default()
    try:
        m1 = backend.read_session_metadata(session_id_1)
        m2 = backend.read_session_metadata(session_id_2)
        e1 = backend.read_events(session_id_1)
        e2 = backend.read_events(session_id_2)
    except KeyError as exc:
        console.print(f"[red]Session not found:[/red] {exc}")
        sys.exit(1)

    console.print(
        f"\n[bold]Session A[/bold] [cyan]{session_id_1}[/cyan]: {m1.status.value}, {len(e1)} steps"
    )
    console.print(
        f"[bold]Session B[/bold] [cyan]{session_id_2}[/cyan]: {m2.status.value}, {len(e2)} steps"
    )
    console.print(f"\nStep count diff: {len(e1)} vs {len(e2)} ({len(e2) - len(e1):+d})")

    min_len = min(len(e1), len(e2))
    diffs = 0
    for i in range(min_len):
        if e1[i].event_type != e2[i].event_type:
            console.print(
                f"  Step {i:03d}: [yellow]event type changed[/yellow] "
                f"{e1[i].event_type.value} → {e2[i].event_type.value}"
            )
            diffs += 1

    if diffs == 0 and len(e1) == len(e2):
        console.print("\n[green]Sessions have identical event structure.[/green]")


# ── capsule delete ────────────────────────────────────────────


@main.command("delete")
@click.argument("session_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def delete_session(session_id: str, yes: bool) -> None:
    """Delete a session from the local store."""
    from capsule_trace.storage.sqlite import SQLiteBackend

    if not yes:
        click.confirm(f"Delete session {session_id}?", abort=True)

    backend = SQLiteBackend.default()
    try:
        backend.delete_session(session_id)
        console.print(f"[green]Deleted[/green] session {session_id}")
    except Exception as exc:
        console.print(f"[red]Delete failed:[/red] {exc}")
        sys.exit(1)


# ── capsule serve ─────────────────────────────────────────────


@main.command("serve")
@click.option("--port", default=7842, show_default=True)
def serve(port: int) -> None:
    """Start the local web UI."""
    console.print("[yellow]Local web UI coming in Sprint 6 (cloud platform).[/yellow]")
    console.print(f"Would start on http://localhost:{port}")


# ── capsule upload ────────────────────────────────────────────


@main.command("upload")
@click.argument("session_id")
@click.option("--tags", default="", help="Comma-separated tags e.g. production,refund")
def upload_session_cmd(session_id: str, tags: str) -> None:
    """Upload a session to Capsule Cloud."""
    import httpx

    config = load_config()
    if config is None:
        console.print("Not logged in. Run: capsule-trace login")
        sys.exit(1)

    api_key = config["api_key"]
    api_url = config["api_url"]

    # Find the .capsule file
    candidates = [
        Path.home() / ".capsule" / f"{session_id}.capsule",
        Path.cwd() / f"{session_id}.capsule",
    ]
    capsule_path: Path | None = None
    for p in candidates:
        if p.exists():
            capsule_path = p
            break

    if capsule_path is None:
        console.print(
            f"Session {session_id} not found locally. "
            "Run capsule-trace list to see available sessions."
        )
        sys.exit(1)

    # Resolve workspace ID
    auth_headers = {"Authorization": f"Bearer {api_key}"}
    try:
        ws_resp = httpx.get(f"{api_url}/api/v1/workspaces", headers=auth_headers, timeout=10)
    except httpx.ConnectError:
        console.print(f"Could not reach {api_url}. Check your internet connection.")
        sys.exit(1)

    if ws_resp.status_code == 401:
        console.print("Session expired. Run: capsule-trace login")
        sys.exit(1)

    # The API returns a bare array of workspaces, not {"workspaces": [...]}.
    workspaces = ws_resp.json()
    if not workspaces:
        console.print("No workspaces found for this account.")
        sys.exit(1)
    workspace_id = workspaces[0]["id"]

    # Build and send multipart upload
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    metadata = json.dumps({"session_id": session_id, "tags": tag_list})
    capsule_bytes = capsule_path.read_bytes()

    try:
        up_resp = httpx.post(
            f"{api_url}/api/v1/workspaces/{workspace_id}/sessions",
            headers=auth_headers,
            files=[
                ("metadata", (None, metadata, "application/json")),
                ("file", (f"{session_id}.capsule", capsule_bytes, "application/octet-stream")),
            ],
            timeout=60,
        )
    except httpx.ConnectError:
        console.print(f"Could not reach {api_url}. Check your internet connection.")
        sys.exit(1)

    if up_resp.status_code == 413:
        console.print("File too large for your current plan.")
        sys.exit(1)
    if up_resp.status_code == 401:
        console.print("Authentication failed. Run: capsule-trace login")
        sys.exit(1)
    if up_resp.status_code != 201:
        console.print(f"Upload failed: {up_resp.status_code} {up_resp.text}")
        sys.exit(1)

    result = up_resp.json()
    console.print("[green]Uploaded successfully.[/green]")
    if result.get("view_url"):
        console.print(f"View at: {result['view_url']}")


# ── capsule cloud ─────────────────────────────────────────────


@main.group("cloud")
def cloud_group() -> None:
    """Manage Capsule Cloud connection."""


@cloud_group.command("login")
@click.option(
    "--url", default="https://api.capsule.dev", show_default=True, help="Cloud API base URL"
)
@click.option(
    "--api-key", prompt="API key", hide_input=True, help="Your Capsule Cloud API key (csk_…)"
)
@click.option("--workspace", prompt="Workspace ID", help="Your workspace ID")
def cloud_login(url: str, api_key: str, workspace: str) -> None:
    """Save Capsule Cloud credentials to ~/.capsule/cloud.json."""
    import json as _json

    config_dir = Path.home() / ".capsule"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "cloud.json"

    config_data = {
        "base_url": url,
        "api_key": api_key,
        "workspace_id": workspace,
    }
    config_file.write_text(_json.dumps(config_data, indent=2))
    config_file.chmod(0o600)  # restrict to owner

    console.print(f"[green]Saved cloud config[/green] → {config_file}")
    console.print(f"  Workspace: [cyan]{workspace}[/cyan]")
    console.print(f"  URL:       {url}")


@cloud_group.command("status")
def cloud_status() -> None:
    """Show current Capsule Cloud connection status."""
    from capsule_trace.cloud.uploader import _get_cloud_config

    config = _get_cloud_config()
    if config["api_key"]:
        masked = config["api_key"][:8] + "…" if len(config["api_key"]) > 8 else "***"
        console.print(f"[green]Connected[/green] to {config['base_url']}")
        console.print(f"  API key:     {masked}")
        console.print(f"  Workspace:   {config['workspace_id'] or '[dim](not set)[/dim]'}")
    else:
        console.print("[yellow]Not connected.[/yellow] Run `capsule cloud login` to configure.")


# ── capsule login ─────────────────────────────────────────────


@main.command("login")
@click.option(
    "--api-key",
    prompt="API Key",
    hide_input=True,
    help="Your Capsule API key from Settings > API Keys",
)
@click.option(
    "--api-url",
    default="https://YOUR_RAILWAY_URL",
    help="Capsule API base URL",
)
def login(api_key: str, api_url: str) -> None:
    """Authenticate with the Capsule API."""
    from datetime import datetime

    import httpx

    if not api_key.startswith("csk_"):
        console.print(
            "Invalid API key format. Get your key from the dashboard under Settings → API Keys."
        )
        sys.exit(1)

    try:
        resp = httpx.get(
            f"{api_url}/api/v1/workspaces",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
    except httpx.ConnectError:
        console.print(f"Could not reach {api_url}. Check your internet connection or the API URL.")
        sys.exit(1)

    if resp.status_code == 401:
        console.print("Invalid API key. Please check and try again.")
        sys.exit(1)

    if resp.status_code != 200:
        console.print(f"Unexpected response {resp.status_code}. Please try again.")
        sys.exit(1)

    save_config(
        {
            "api_key": api_key,
            "api_url": api_url,
            "logged_in_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    console.print("[green]Logged in successfully.[/green]")


# ── capsule logout ────────────────────────────────────────────


@main.command("logout")
def logout() -> None:
    """Remove saved Capsule credentials."""
    config_path = Path.home() / ".capsule" / "config.json"
    if not config_path.exists():
        console.print("You are not logged in.")
        sys.exit(0)
    config_path.unlink()
    console.print("Logged out.")
