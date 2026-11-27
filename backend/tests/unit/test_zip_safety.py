"""P6.4 ZIP safety (T6.4–T6.6, S-32): counters while streaming, never full extraction first."""

import io
import json
import stat
import time
import zipfile

import pytest

from app.files.zip_safety import ZipLimits, inspect

MiB = 1024 * 1024


def build(members: dict[str, bytes], compression=zipfile.ZIP_DEFLATED) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buffer.getvalue()


CSV = b"order_id,amount\nA1,10\n"


def test_a_clean_archive_lists_its_members():
    data = build({"orders.csv": CSV, "data/payments.json": json.dumps([{"a": 1}]).encode(),
                  "data/": b""})  # fmt: skip
    assert inspect(data) == [
        {"path": "orders.csv", "detected_type": "csv", "size": len(CSV)},
        {"path": "data/payments.json", "detected_type": "json", "size": 10},
    ]


def test_a_zip_bomb_is_stopped_by_the_ratio_before_it_is_extracted():
    buffer = io.BytesIO()
    with (
        zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive,
        archive.open("x.csv", "w") as member,
    ):
        for _ in range(100):
            member.write(b"\0" * MiB)  # 100 MiB of zeros, about 100 KiB compressed
    start = time.perf_counter()
    assert inspect(buffer.getvalue()) == "ZIP_RATIO_EXCEEDED"
    assert time.perf_counter() - start < 2  # stopped early: reading all 100 MiB takes far longer


def test_the_total_uncompressed_size_is_counted():
    data = build({f"{k}.csv": CSV * 50 for k in range(3)}, zipfile.ZIP_STORED)
    assert inspect(data, ZipLimits(max_total=2 * len(CSV) * 50)) == "ZIP_TOO_LARGE"


@pytest.mark.parametrize("name", ["../evil.csv", "/etc/passwd.csv", "a/../../x.csv",
                                  "C:/windows/x.csv", "a\\..\\x.csv"])  # fmt: skip
def test_unsafe_paths_are_rejected(name):
    assert inspect(build({name: CSV})) == "ZIP_UNSAFE_PATH"


def test_a_symlink_member_is_rejected():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("link.csv")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, b"/etc/passwd")
    assert inspect(buffer.getvalue()) == "ZIP_SYMLINK"


def test_26_members_are_too_many_and_25_are_fine():
    assert inspect(build({f"{k}.csv": CSV for k in range(26)})) == "ZIP_TOO_MANY_MEMBERS"
    assert isinstance(inspect(build({f"{k}.csv": CSV for k in range(25)})), list)


def test_a_nested_archive_is_rejected():
    assert inspect(build({"inner.zip": build({"a.csv": CSV})})) == "ZIP_NESTED"


def test_an_encrypted_member_is_rejected_with_a_clear_code():
    data = bytearray(build({"a.csv": CSV}, zipfile.ZIP_STORED))
    for header in (b"PK\x03\x04", b"PK\x01\x02"):
        at = data.index(header)
        flag = at + (6 if header == b"PK\x03\x04" else 8)
        data[flag] |= 0x01
    assert inspect(bytes(data)) == "ZIP_ENCRYPTED"


def test_an_unsupported_member_is_rejected():
    assert inspect(build({"tool.exe": b"MZ\x90\x00" + b"\x00" * 60})) == "ZIP_MEMBER_UNSUPPORTED"


def test_a_damaged_archive_is_corrupt():
    assert inspect(b"PK\x03\x04" + b"\x00" * 40) == "FILE_CORRUPT"
