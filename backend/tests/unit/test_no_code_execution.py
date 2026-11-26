"""S-10: nothing in `app/` can run code from data. No eval/exec/compile, no pickle-style
deserializers, and no dynamic imports. Only registered operations run.

This scans the source tree, so it runs in CI with the rest of the tests. Ruff's `S` rules catch
some of these calls too, but not `compile` or `__import__`.
"""

import ast

import pytest

from app.config import REPO_ROOT

APP_DIR = REPO_ROOT / "backend" / "app"
BANNED_CALLS = {"eval", "exec", "compile", "__import__", "breakpoint"}
BANNED_MODULES = {"pickle", "cPickle", "dill", "marshal", "shelve", "importlib", "runpy", "code"}
BANNED_ATTRIBUTES = {"import_module", "__import__", "load_module", "exec_module"}
ALLOWED_MODULES = {"importlib.metadata"}
"""Reads installed package metadata only (the version in `/health`)."""


def _banned(module: str) -> bool:
    return module.split(".")[0] in BANNED_MODULES and module not in ALLOWED_MODULES


def violations(source: str) -> list[str]:
    """Every banned call or import in `source`, as `line: what`."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BANNED_CALLS:
                found.append(f"{node.lineno}: {node.func.id}()")
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_ATTRIBUTES:
            found.append(f"{node.lineno}: .{node.attr}")
        elif isinstance(node, ast.Import):
            found += [
                f"{node.lineno}: import {alias.name}" for alias in node.names if _banned(alias.name)
            ]
        elif isinstance(node, ast.ImportFrom) and node.module and _banned(node.module):
            found.append(f"{node.lineno}: from {node.module} import")
    return found


SOURCES = sorted(APP_DIR.rglob("*.py"))


def test_the_scan_covers_the_app():
    assert len(SOURCES) > 20
    assert APP_DIR / "core" / "run_state.py" in SOURCES


@pytest.mark.parametrize("path", SOURCES, ids=lambda path: str(path.relative_to(APP_DIR)))
def test_no_code_execution_in_app(path):
    assert violations(path.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "source",
    [
        "eval(text)",
        "exec(text)",
        "compile(text, 'x', 'exec')",
        "__import__(name)",
        "import pickle",
        "import marshal as m",
        "from shelve import open",
        "import importlib",
        "from importlib import import_module",
        "from importlib.util import spec_from_file_location",
        "import runpy",
        "loader.exec_module(module)",
        "spec.loader.load_module()",
        "builtins.__import__(name)",
    ],
)
def test_the_scan_catches_each_banned_form(source):
    assert violations(source)


def test_ordinary_code_passes_the_scan():
    assert violations("import json\nfrom pathlib import Path\nvalue = json.loads(text)") == []
