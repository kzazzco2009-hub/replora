"""Taking one member out of an uploaded ZIP (P7.1, P7.2 `extract_member`).

The archive passed the P6.4 safety checks at upload, so reading one named member is safe. The
member's path joins the lineage, so every row can name the file it came from inside the ZIP.
"""

import io
import zipfile
from typing import Any

from app.core.engine.executor import OperationError


def extract_member(archive: bytes, path: str, source: dict[str, Any]) -> tuple[bytes, dict]:
    with zipfile.ZipFile(io.BytesIO(archive)) as handle:
        names = [info.filename for info in handle.infolist() if not info.is_dir()]
        if path not in names:
            raise OperationError("ZIP_MEMBER_MISSING", path=path, found=names)
        return handle.read(path), {**source, "member": path}
