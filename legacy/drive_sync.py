#!/usr/bin/env python3
"""Google Drive helpers for payroll panel (wraps Hermes google_api.py)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PY = sys.executable
GAPI = Path("/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py")


def _run(args: list[str]) -> Any:
    r = subprocess.run([PY, str(GAPI), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "drive error").strip())
    out = r.stdout.strip()
    if not out:
        return {}
    return json.loads(out)


def upload_file(local_path: Path, *, parent: str, name: str | None = None) -> dict[str, Any]:
    args = ["drive", "upload", str(local_path), "--parent", parent]
    if name:
        args.extend(["--name", name])
    return _run(args)


def delete_file(file_id: str, *, permanent: bool = False) -> None:
    args = ["drive", "delete", file_id]
    if permanent:
        args.append("--permanent")
    _run(args)


def get_file_meta(file_id: str) -> dict[str, Any]:
    return _run(["drive", "get", file_id])