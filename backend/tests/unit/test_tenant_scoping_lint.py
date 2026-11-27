"""S-14 and S-15 as a lint over `app/`.

S-14: a query on a tenant table (`select`, `update`, `delete`, `session.get`) is built only by
`app.db.repos.scoped`, which always adds the workspace filter.
S-15: `text()` never gets an f-string, `%` formatting or `.format()`, so SQL is never built from
strings.
"""

import ast
from pathlib import Path

import pytest

from app.db.repos import CHILD, TENANT

APP = Path(__file__).resolve().parents[2] / "app"
TENANT_NAMES = {model.__name__ for model in (*TENANT, *CHILD)}
QUERY_BUILDERS = {"select", "update", "delete"}
SYSTEM_JOBS = {"purge_expired", "expire_stale_runs"}
"""Jobs that work across every workspace on purpose (P6.6 retention, P8.2 approval expiry).
Each is listed by name."""


def _functions(tree: ast.AST):
    """Each call with the name of the function it is in."""
    for function in ast.walk(tree):
        if isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
            for node in ast.walk(function):
                if isinstance(node, ast.Call):
                    yield function.name, node


def _first_arg(call: ast.Call) -> str | None:
    if not call.args:
        return None
    arg = call.args[0]
    if isinstance(arg, ast.Name):
        return arg.id
    return arg.attr if isinstance(arg, ast.Attribute) else None


def _name(call: ast.Call) -> str | None:
    func = call.func
    return func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)


def unscoped_queries(source: str) -> list[str]:
    found = []
    for function, call in _functions(ast.parse(source)):
        name, target = _name(call), _first_arg(call)
        builds = name in QUERY_BUILDERS or (name == "get" and isinstance(call.func, ast.Attribute))
        if builds and target in TENANT_NAMES and function not in {"scoped", *SYSTEM_JOBS}:
            found.append(f"{name}({target}) in {function}")
    return found


def string_sql(source: str) -> list[str]:
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and _name(node) == "text" and node.args:
            arg = node.args[0]
            formatted = isinstance(arg, ast.JoinedStr | ast.BinOp) or (
                isinstance(arg, ast.Call) and _name(arg) == "format"
            )
            if formatted:
                found.append(ast.unparse(node))
    return found


@pytest.mark.parametrize("path", sorted(APP.rglob("*.py")), ids=lambda p: str(p.relative_to(APP)))
def test_app_queries_tenant_tables_only_through_scoped(path):
    assert unscoped_queries(path.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("path", sorted(APP.rglob("*.py")), ids=lambda p: str(p.relative_to(APP)))
def test_app_never_builds_sql_from_strings(path):
    assert string_sql(path.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("def f(s, i):\n    return select(Run).where(Run.id == i)", ["select(Run) in f"]),
        ("def f(s, i):\n    return s.get(m.File, i)", ["get(File) in f"]),
        ("def f(i):\n    return update(Draft).values(x=1)", ["update(Draft) in f"]),
        ("def f(i):\n    return delete(RunNode)", ["delete(RunNode) in f"]),
        ("def scoped(model, ws):\n    return select(Run)", []),
        ("def f(e):\n    return select(User).where(User.email == e)", []),
        ("def f(d):\n    return d.get('key')", []),
    ],
)
def test_the_scoping_lint_catches_unscoped_queries(source, expected):
    assert unscoped_queries(source) == expected


@pytest.mark.parametrize(
    ("source", "flagged"),
    [
        ('text(f"SELECT * FROM runs WHERE id = {i}")', True),
        ('text("SELECT * FROM runs WHERE id = %s" % i)', True),
        ('text("SELECT * FROM runs WHERE id = {}".format(i))', True),
        ('text("SELECT * FROM runs WHERE id = :id")', False),
    ],
)
def test_the_sql_lint_catches_string_built_sql(source, flagged):
    assert bool(string_sql(source)) is flagged
