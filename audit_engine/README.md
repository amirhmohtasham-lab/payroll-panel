# Audit engine (vendored)

The original app depended on two scripts living outside the repository at
`~/.hermes/scripts/farm_payroll_audit.py` and `~/.hermes/scripts/fertilizer_audit.py`.
Those files were not present on this machine when the rebuild was performed (checked with
a full filesystem + Spotlight search), so this package is a **from-scratch, API-compatible
reimplementation** based on:

- The exact function/dataclass names and fields `app.py` imported and used
  (`audit_workbook`, `write_highlighted_workbook`, `Issue`, `AuditResult`, sheet fields like
  `foreman`, `list_no`, `workplace`, `period`, `worker_rows`, `worker_gross`, `desc_gross`).
- The Persian field labels and validation categories implied by the front-end
  (`static/index.html`, `static/operator.html`).

**Action required:** if the real audit rules differ from what's implemented here (e.g. specific
column layout, specific error codes/thresholds), replace the logic in `payroll.py` /
`fertilizer.py` with the real business rules — the rest of the application (upload flow,
highlighting, reports) is wired against this module's public API and does not need to change.

## Public API

`payroll.py`:
- `audit_workbook(path: Path) -> AuditResult`
- `write_highlighted_workbook(result: AuditResult, src: Path, dest: Path) -> None`
- `result_to_jsonable(result: AuditResult) -> dict`

`fertilizer.py`:
- `audit_workbook(path: Path) -> FertilizerResult`
- `write_highlighted_workbook(result: FertilizerResult, src: Path, dest: Path) -> None`
- `result_to_jsonable(result: FertilizerResult) -> dict`

## Google Drive backup (vendored)

The original `drive_sync.py` / `bootstrap_drive.py` shelled out to `~/.hermes` and stored the
Drive folder id in a local `config.json`. This has been replaced by
`app/services/drive_service.py`, which:

- Uses the official `google-api-python-client` + a service account file, configured via
  `GOOGLE_APPLICATION_CREDENTIALS` (see `.env.example`).
- Resolves/creates the backup folder via `DRIVE_PARENT_FOLDER_ID` / `DRIVE_FOLDER_NAME` env vars
  instead of a hardcoded path or local JSON cache.
- Exposes `ensure_folder()`, `upload_file()`, and `delete_file()` with the same behavior the
  upload flow relies on.
