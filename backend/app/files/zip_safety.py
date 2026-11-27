"""ZIP safety (P6.4, S-32). An archive is read member by member, counting real bytes as they come.

Header sizes can lie, so they are never trusted: the counters stop a bomb (ratio or total) while
it streams, long before it is extracted. Paths are only checked, never joined to anything.
"""

import io
import re
import stat
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import PurePosixPath

from app.files.detect import detect

CHUNK = 64 * 1024


@dataclass(frozen=True)
class ZipLimits:
    max_members: int = 25
    max_total: int = 200 * 1024 * 1024
    max_ratio: int = 100


def _unsafe(name: str) -> bool:
    parts = PurePosixPath(name).parts
    return (name.startswith("/") or "\\" in name or re.match(r"^[A-Za-z]:", name) is not None
            or ".." in parts)  # fmt: skip


def _symlink(info: zipfile.ZipInfo) -> bool:
    return stat.S_ISLNK(info.external_attr >> 16)


def inspect(data: bytes, limits: ZipLimits = ZipLimits()) -> list[dict] | str:
    """The members `[{path, detected_type, size}]`, or the rejection code."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            return _members(archive, limits)
    except zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError:
        return "FILE_CORRUPT"


def _members(archive: zipfile.ZipFile, limits: ZipLimits) -> list[dict] | str:
    infos = archive.infolist()
    for info in infos:
        if _unsafe(info.filename):
            return "ZIP_UNSAFE_PATH"
        if _symlink(info):
            return "ZIP_SYMLINK"
        if info.flag_bits & 0x1:
            return "ZIP_ENCRYPTED"
    files = [info for info in infos if not info.is_dir()]
    if len(files) > limits.max_members:
        return "ZIP_TOO_MANY_MEMBERS"
    members, total = [], 0
    for info in files:
        content, budget = bytearray(), max(info.compress_size, 1) * limits.max_ratio
        with archive.open(info) as stream:
            while chunk := stream.read(CHUNK):
                content += chunk
                total += len(chunk)
                if len(content) > budget:
                    return "ZIP_RATIO_EXCEEDED"
                if total > limits.max_total:
                    return "ZIP_TOO_LARGE"
        kind = detect(bytes(content))
        if kind == "zip":
            return "ZIP_NESTED"
        if kind not in {"csv", "json"}:
            return "ZIP_MEMBER_UNSUPPORTED"
        members.append({"path": info.filename, "detected_type": kind, "size": len(content)})
    return members
