"""P5.5 and P5.6: the permission table covers every route, and T5.9 / T5.10 hold for all of them.

The expected status of each (route, caller) pair comes from the table itself: anonymous → 401,
not a member → 404 (no existence leak, S-22), a role without the permission → 403, otherwise the
route's own answer (a stub's 501, a validation 422, …) but never 401, 403 or 404.
"""

import re

import pytest
from conftest import with_csrf
from fastapi.testclient import TestClient

from app.auth.access import PUBLIC, SIGNED_IN, TABLE, check_table
from app.auth.permissions import MATRIX, Permission, Role, allowed
from app.config import Settings
from app.db import models as m
from app.db.base import Base
from app.db.engine import make_engine, make_sessions
from app.main import create_app

PASSWORD = "a long and unusual passphrase"
ID = "01937a5e-7f00-7000-8000-000000000001"
CALLERS = [*Role, "non-member", "anonymous"]


def test_the_matrix_is_the_documented_one():
    viewer = {p for p in Permission if allowed(Role.VIEWER, p)}
    assert viewer == {Permission.WORKSPACE_READ, Permission.FILES_READ, Permission.DRAFTS_READ,
                      Permission.WORKFLOWS_READ, Permission.RUNS_READ}  # fmt: skip
    assert MATRIX[Permission.WORKSPACE_DELETE] == {Role.OWNER}
    assert MATRIX[Permission.MEMBERS_MANAGE] == {Role.OWNER, Role.ADMIN}
    assert MATRIX[Permission.AUDIT_READ] == {Role.OWNER, Role.ADMIN}
    assert all(Role.OWNER in roles for roles in MATRIX.values())


def test_every_route_is_in_the_table_and_the_table_has_no_extra_route(openapi):
    routes = {(method.upper(), path) for path, ops in openapi["paths"].items() for method in ops}
    assert set(TABLE) == routes
    check_table(routes)


def test_the_startup_check_refuses_an_undeclared_route():
    with pytest.raises(RuntimeError, match="no permission"):
        check_table({*TABLE, ("GET", "/api/v1/secret")})


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    url = f"sqlite:///{(tmp_path_factory.mktemp('perm') / 'p.db').as_posix()}"
    Base.metadata.create_all(make_engine(url))
    app = create_app(Settings(_env_file=None, database_url=url))
    clients = {"anonymous": with_csrf(TestClient(app))}
    for name in CALLERS[:-1]:
        client = with_csrf(TestClient(app))
        body = {"email": f"{name}@example.com", "password": PASSWORD, "display_name": name,
                "locale": "en"}  # fmt: skip
        client.post("/api/v1/auth/register", json=body)
        client.post("/api/v1/auth/login", json={"email": body["email"], "password": PASSWORD})
        clients[name] = client
    sessions = make_sessions(make_engine(url))
    with sessions.begin() as session:
        users = {u.display_name: u for u in session.query(m.User)}
        space = session.query(m.Workspace).filter_by(owner_id=users["owner"].id).one()
        for role in (Role.ADMIN, Role.MEMBER, Role.VIEWER):
            session.add(m.Membership(workspace_id=space.id, user_id=users[role].id, role=role))
    return clients, str(space.id)


def expected(declared, caller: str) -> set[int] | None:
    """The statuses this caller may get, or None for "the route's own answer"."""
    if declared is PUBLIC:
        return None
    if caller == "anonymous":
        return {401}
    if declared is SIGNED_IN:
        return None
    if caller == "non-member":
        return {404}
    return None if allowed(Role(caller), declared) else {403}


def concrete(path: str, ws: str) -> str:
    return re.sub(r"\{[^}]+\}", ID, path.replace("{ws_id}", ws))


@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize(("method", "path"), sorted(TABLE), ids=" ".join)
def test_every_route_answers_every_caller_as_the_table_says(world, method, path, caller):
    clients, ws = world
    if (method, path) in {("POST", "/api/v1/auth/logout"), ("DELETE", "/api/v1/auth/me")}:
        pytest.skip("would sign this shared caller out")
    response = clients[caller].request(method, concrete(path, ws), json={})
    if TABLE[method, path] is PUBLIC:
        return  # its own tests cover it (a refresh with no cookie is a fair 401)
    want = expected(TABLE[method, path], caller)
    if want is None:
        assert response.status_code not in {401, 403}, response.text
        if response.status_code == 404:  # only a resource that doesn't exist
            assert "{" in path.replace("{ws_id}", ""), response.text
    else:
        assert response.status_code in want, response.text
        code = {401: "UNAUTHENTICATED", 403: "PERMISSION_DENIED", 404: "NOT_FOUND"}
        assert response.json()["code"] == code[response.status_code]


def test_a_malformed_workspace_id_is_not_found(world):
    clients, _ = world
    response = clients["owner"].get("/api/v1/workspaces/not-a-uuid/members")
    assert (response.status_code, response.json()["code"]) == (404, "NOT_FOUND")
