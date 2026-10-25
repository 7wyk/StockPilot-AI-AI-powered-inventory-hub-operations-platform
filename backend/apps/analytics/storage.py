"""
Supabase Storage adapter for StockPilot AI report files.

Uses private storage with organization-scoped paths:
  organizations/{org_id}/reports/{filename}

Uses signed URLs for secure downloads.

If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not configured,
the adapter raises explicit errors rather than silently failing.
Local development can use the LocalStorageAdapter fallback.
"""

import os
from pathlib import Path

from django.conf import settings
from django.utils import timezone


class StorageError(Exception):
    """Raised when storage operations fail."""


class SupabaseStorageAdapter:
    """
    Server-side Supabase Storage adapter.
    Never exposes the service role key to the client.
    """

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "reports")
        if not self.url or not self.key:
            raise StorageError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set "
                "for Supabase storage. Use LocalStorageAdapter for development."
            )

    def _get_client(self):
        try:
            from supabase import create_client
            return create_client(self.url, self.key)
        except Exception as exc:
            raise StorageError(f"Failed to create Supabase client: {exc}") from exc

    def upload(self, *, organization_id, filename, content, content_type="application/octet-stream"):
        """
        Upload a file to organization-scoped private storage.
        Returns the storage path.
        """
        path = f"organizations/{organization_id}/reports/{filename}"
        client = self._get_client()
        try:
            client.storage.from_(self.bucket).upload(
                path=path,
                file=content,
                file_options={"content-type": content_type},
            )
        except Exception as exc:
            raise StorageError(f"Failed to upload {path}: {exc}") from exc
        return path

    def get_signed_url(self, path, expires_in=3600):
        """
        Generate a signed URL for private file download.
        Default expiry: 1 hour.
        """
        client = self._get_client()
        try:
            result = client.storage.from_(self.bucket).create_signed_url(
                path=path,
                expires_in=expires_in,
            )
            return result.get("signedURL") or result.get("signedUrl", "")
        except Exception as exc:
            raise StorageError(f"Failed to create signed URL for {path}: {exc}") from exc

    def delete(self, path):
        """Delete a file from storage."""
        client = self._get_client()
        try:
            client.storage.from_(self.bucket).remove([path])
        except Exception as exc:
            raise StorageError(f"Failed to delete {path}: {exc}") from exc


class LocalStorageAdapter:
    """
    Local filesystem storage adapter for development.
    Stores files in MEDIA_ROOT or a configurable directory.
    Does not require any external credentials.
    """

    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or getattr(settings, "MEDIA_ROOT", None) or settings.BASE_DIR / "media")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def upload(self, *, organization_id, filename, content, content_type="application/octet-stream"):
        path = f"organizations/{organization_id}/reports/{filename}"
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content if isinstance(content, bytes) else content.encode())
        return path

    def get_signed_url(self, path, expires_in=3600):
        """For local dev, return the file path. In production, use Supabase."""
        full_path = self.base_dir / path
        if full_path.exists():
            return f"/media/{path}"
        return ""

    def delete(self, path):
        full_path = self.base_dir / path
        if full_path.exists():
            full_path.unlink()


def get_storage_adapter():
    """
    Factory: return Supabase adapter if credentials are configured,
    otherwise fall back to local storage for development.
    """
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        return SupabaseStorageAdapter()
    return LocalStorageAdapter()
