#!/usr/bin/env python3
"""Bootstrap Drive folder for payroll panel."""
import json
import subprocess
import sys
from pathlib import Path

PY = sys.executable
GAPI = Path("/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py")
CONFIG = Path("/root/.hermes/payroll_panel/config.json")
FOLDER_NAME = "صورت-کارگری-پنل-بهزادیان"
REFERENCE_FILE = "10VL8PMVLNmRYqx4UOaV3MNg4ujEKADKC"


def run(args):
    r = subprocess.run([PY, str(GAPI), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout)
    return json.loads(r.stdout) if r.stdout.strip() else {}


def main():
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG.exists():
        cfg = json.loads(CONFIG.read_text())
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
        return

    parent = ""
    try:
        meta = run(["drive", "get", REFERENCE_FILE])
        parents = meta.get("parents") or []
        if parents:
            parent = parents[0]
    except Exception as e:
        print("warn: no parent from reference file:", e, file=sys.stderr)

    # search existing folder
    q = f"name = '{FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent:
        q += f" and '{parent}' in parents"
    found = run(["drive", "search", q, "--raw-query", "--max", "5"])
    if isinstance(found, list) and found:
        folder_id = found[0]["id"]
    else:
        args = ["drive", "create-folder", FOLDER_NAME]
        if parent:
            args.extend(["--parent", parent])
        created = run(args)
        folder_id = created["id"]

    cfg = {
        "drive_folder_id": folder_id,
        "drive_folder_name": FOLDER_NAME,
        "parent_hint": parent or None,
    }
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(cfg, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()