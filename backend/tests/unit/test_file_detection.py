"""P6.3 content-based type detection (T6.1, S-30) and display-name safety (T6.3, S-33)."""

import io
import json
import zipfile

import pytest

from app.files.detect import detect, safe_display_name


def a_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("a.csv", "x\n1\n")
    return buffer.getvalue()


@pytest.mark.parametrize(("data", "kind"), [
    (b"order_id,amount\nA1,10\n", "csv"),
    ("رقم الطلب,المبلغ\nA1,10\n".encode(), "csv"),
    ("\ufeffid;name\n1;x\n".encode(), "csv"),
    ("id,name\n1,x\n".encode("cp1256"), "csv"),
    (json.dumps([{"a": 1}]).encode(), "json"),
    (b'  {"rows": []}', "json"),
    (a_zip(), "zip"),
])  # fmt: skip
def test_supported_content_is_recognized_whatever_the_name(data, kind):
    assert detect(data) == kind


@pytest.mark.parametrize(("data", "code"), [
    (b"", "FILE_EMPTY"),
    (b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 64, "FILE_TYPE_UNSUPPORTED"),
    (b"<!DOCTYPE html><html><script>alert(1)</script></html>", "FILE_TYPE_UNSUPPORTED"),
    (b"<?xml version='1.0'?><a/>", "FILE_TYPE_UNSUPPORTED"),
    (b"\x89PNG\r\n\x1a\n" + b"\x00" * 20, "FILE_TYPE_UNSUPPORTED"),
    (b"%PDF-1.7\n", "FILE_TYPE_UNSUPPORTED"),
    (b"id,name\n1,\x00x\n", "FILE_TYPE_UNSUPPORTED"),
    (b'{"broken": ', "FILE_CORRUPT"),
])  # fmt: skip
def test_unsupported_or_disguised_content_is_rejected(data, code):
    assert detect(data) == code


@pytest.mark.parametrize(("name", "shown"), [
    ("../../etc/passwd", "passwd"),
    ("C:\\Users\\x\\report.csv", "report.csv"),
    ("bad\x00name.csv", "badname.csv"),
    ("invoice\u202egpj.exe", "invoicegpj.exe"),
    ("CON.csv", "_CON.csv"),
    ("nul", "_nul"),
    ("   ", "file"),
    ("التقرير الشهري.csv", "التقرير الشهري.csv"),
])  # fmt: skip
def test_display_names_are_neutralized(name, shown):
    assert safe_display_name(name) == shown


def test_a_long_name_is_cut_to_255_keeping_the_extension():
    shown = safe_display_name("a" * 300 + ".csv")
    assert len(shown) == 255 and shown.endswith(".csv")
