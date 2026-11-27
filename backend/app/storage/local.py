"""Local storage (P6.1): files under `.data/storage`, behind signed same-origin URLs.

Production uses Supabase Storage with its own signed URLs (Phase 18); the interface is the same.
Keys are `workspace_id/file_id`, never a user filename (S-33), and can't leave the root.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath

from app.storage.signing import sign

UPLOAD_TTL = timedelta(minutes=10)
DOWNLOAD_TTL = timedelta(minutes=5)
ROUTE = "/api/v1/storage"


@dataclass(frozen=True)
class Upload:
    url: str
    method: str
    headers: dict[str, str]
    expires_at: datetime


class LocalStorage:
    def __init__(self, root: Path, signing_key: str) -> None:
        self.root, self.signing_key = Path(root), signing_key

    def _path(self, key: str) -> Path:
        parts = PurePosixPath(key).parts
        if not parts or "\\" in key or key.startswith("/") or any(p in {"..", "."} for p in parts):
            raise ValueError(f"not a storage key: {key!r}")
        return self.root.joinpath(*parts)

    def create_upload_url(self, key: str, size: int, now: datetime) -> Upload:
        self._path(key)
        expires = now + UPLOAD_TTL
        token = sign({"op": "put", "key": key, "size": size}, self.signing_key, expires)
        headers = {"Content-Type": "application/octet-stream"}
        return Upload(url=f"{ROUTE}/{token}", method="PUT", headers=headers, expires_at=expires)

    def signed_download_url(self, key: str, filename: str, now: datetime) -> tuple[str, datetime]:
        expires = now + DOWNLOAD_TTL
        token = sign({"op": "get", "key": key, "name": filename}, self.signing_key, expires)
        return f"{ROUTE}/{token}", expires

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def open(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def size(self, key: str) -> int:
        return self._path(key).stat().st_size

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)
