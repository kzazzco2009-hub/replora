"""What a file really is, from its bytes (P6.3, S-30), and a safe name to show (S-33).

The extension and the client's content type are never trusted. Today's allow-list is ZIP, JSON
and CSV text (UTF-8, with or without BOM, or Windows-1256 for Arabic Excel exports); later
phases add formats. Binary files, markup and scripts are refused, even when renamed.
"""

import json
import re
import unicodedata

ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06")
REFUSED_MAGIC = (
    b"MZ",
    b"\x7fELF",
    b"%PDF",
    b"\x89PNG",
    b"GIF8",
    b"\xff\xd8\xff",
    b"\xd0\xcf\x11\xe0",
)
"""Executables, PDF, images and old Office files: known not to be supported (yet)."""

WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"{port}{n}" for port in ("com", "lpt")
                                                  for n in range(1, 10))}  # fmt: skip
MAX_NAME = 255


def _text(data: bytes) -> str | None:
    for encoding in ("utf-8-sig", "cp1256"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def detect(data: bytes) -> str:
    """`csv`, `json` or `zip`; otherwise the rejection code."""
    if not data:
        return "FILE_EMPTY"
    if data.startswith(ZIP_MAGIC):
        return "zip"
    text = None if data.startswith(REFUSED_MAGIC) else _text(data)
    if text is None or any(ch < " " and ch not in "\t\n\r" or ch == "\x7f" for ch in text):
        return "FILE_TYPE_UNSUPPORTED"
    start = text.lstrip()[:1]
    if start == "<":
        return "FILE_TYPE_UNSUPPORTED"
    if start in {"{", "["}:
        try:
            json.loads(text)
        except ValueError:
            return "FILE_CORRUPT"
        return "json"
    return "csv"


def safe_display_name(name: str) -> str:
    """For display only: no path, no control or bidi characters, no reserved names, ≤ 255."""
    name = unicodedata.normalize("NFC", re.split(r"[\\/]", name)[-1])
    name = "".join(ch for ch in name if unicodedata.category(ch) not in {"Cc", "Cf"})
    name = " ".join(name.split())
    if name in {"", ".", ".."}:
        return "file"
    if name.split(".")[0].lower() in WINDOWS_RESERVED:
        name = f"_{name}"
    if len(name) > MAX_NAME:
        base, dot, ext = name.rpartition(".")
        keep = dot and len(ext) <= 16
        name = f"{base[: MAX_NAME - len(ext) - 1]}.{ext}" if keep else name[:MAX_NAME]
    return name
