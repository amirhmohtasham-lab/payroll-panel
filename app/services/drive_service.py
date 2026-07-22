"""Google Drive backup service — config-driven, no hardcoded ~/.hermes paths.

Uses the official google-api-python-client with a service account, replacing the
original subprocess-based wrapper around a Hermes-specific script.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import get_settings

_SCOPES = ["https://www.googleapis.com/auth/drive"]


class DriveNotConfiguredError(RuntimeError):
    pass


def _get_service():
    settings = get_settings()
    if not settings.google_application_credentials:
        raise DriveNotConfiguredError(
            "GOOGLE_APPLICATION_CREDENTIALS تنظیم نشده. آپلود در Drive غیرفعال است."
        )
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        settings.google_application_credentials, scopes=_SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def ensure_folder() -> str:
    """Return the configured Drive parent folder id, creating it under the parent hint if missing."""
    settings = get_settings()
    if settings.drive_parent_folder_id:
        return settings.drive_parent_folder_id

    service = _get_service()
    query = (
        f"name = '{settings.drive_folder_name}' and "
        "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    resp = service.files().list(q=query, fields="files(id, name)", pageSize=5).execute()
    files = resp.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {"name": settings.drive_folder_name, "mimeType": "application/vnd.google-apps.folder"}
    created = service.files().create(body=metadata, fields="id").execute()
    return created["id"]


def upload_file(local_path: Path, *, parent: str, name: str | None = None) -> dict[str, Any]:
    from googleapiclient.http import MediaFileUpload

    service = _get_service()
    metadata = {"name": name or local_path.name, "parents": [parent]}
    media = MediaFileUpload(str(local_path), resumable=True)
    return service.files().create(body=metadata, media_body=media, fields="id, name").execute()


def delete_file(file_id: str, *, permanent: bool = False) -> None:
    service = _get_service()
    if permanent:
        service.files().delete(fileId=file_id).execute()
    else:
        service.files().update(fileId=file_id, body={"trashed": True}).execute()
