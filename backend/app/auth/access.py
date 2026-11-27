"""Who may call each route (P5.6, S-21, S-22).

`TABLE` declares every `/api/v1` route as public, signed-in, or needing a workspace permission.
`authorize` is a v1 router dependency that enforces it:
- no valid session: 401 `UNAUTHENTICATED`;
- not a member of the workspace (or a malformed id): 404 `NOT_FOUND`, so nothing leaks;
- a member whose role lacks the permission: 403 `PERMISSION_DENIED`.
`check_table` runs at startup and refuses an app with a route the table doesn't declare.
"""

from collections.abc import Iterable
from uuid import UUID

from fastapi import Request
from sqlalchemy import select

from app.api.problem import ProblemError
from app.api.session import caller, database
from app.auth.permissions import Permission, Role, allowed
from app.db import models as m

PUBLIC = "public"
SIGNED_IN = "signed-in"

P = Permission
V1, WS = "/api/v1", "/api/v1/workspaces/{ws_id}"
_auth = f"{V1}/auth"
_runs, _out = f"{WS}/runs/{{run_id}}", f"{WS}/runs/{{run_id}}/outputs/{{artifact_id}}"
_flow = f"{WS}/workflows/{{workflow_id}}"

TABLE: dict[tuple[str, str], str | Permission] = {
    ("GET", f"{V1}/health"): PUBLIC,
    ("GET", f"{V1}/operations"): PUBLIC,
    ("GET", f"{V1}/limits"): PUBLIC,
    ("GET", f"{V1}/templates"): PUBLIC,
    ("GET", f"{_auth}/csrf"): PUBLIC,
    ("POST", f"{_auth}/register"): PUBLIC,
    ("POST", f"{_auth}/login"): PUBLIC,
    ("POST", f"{_auth}/logout"): PUBLIC,
    ("POST", f"{_auth}/refresh"): PUBLIC,
    ("POST", f"{_auth}/verify-email"): PUBLIC,
    ("POST", f"{_auth}/password/forgot"): PUBLIC,
    ("POST", f"{_auth}/password/reset"): PUBLIC,
    ("POST", f"{_auth}/mfa/challenge"): PUBLIC,
    ("GET", f"{_auth}/me"): SIGNED_IN,
    ("PATCH", f"{_auth}/me"): SIGNED_IN,
    ("DELETE", f"{_auth}/me"): SIGNED_IN,
    ("POST", f"{_auth}/me/export"): SIGNED_IN,
    ("GET", f"{_auth}/me/export/{{export_id}}"): SIGNED_IN,
    ("POST", f"{_auth}/mfa/enroll"): SIGNED_IN,
    ("POST", f"{_auth}/mfa/enroll/confirm"): SIGNED_IN,
    ("DELETE", f"{_auth}/mfa"): SIGNED_IN,
    ("GET", f"{_auth}/sessions"): SIGNED_IN,
    ("DELETE", f"{_auth}/sessions/{{session_id}}"): SIGNED_IN,
    ("GET", f"{V1}/workspaces"): SIGNED_IN,
    ("POST", f"{V1}/workspaces"): SIGNED_IN,
    ("POST", f"{V1}/invitations/accept"): SIGNED_IN,
    ("DELETE", WS): P.WORKSPACE_DELETE,
    ("GET", f"{WS}/members"): P.WORKSPACE_READ,
    ("PATCH", f"{WS}/members/{{user_id}}"): P.MEMBERS_MANAGE,
    ("DELETE", f"{WS}/members/{{user_id}}"): P.MEMBERS_MANAGE,
    ("GET", f"{WS}/invitations"): P.MEMBERS_MANAGE,
    ("POST", f"{WS}/invitations"): P.MEMBERS_MANAGE,
    ("DELETE", f"{WS}/invitations/{{invitation_id}}"): P.MEMBERS_MANAGE,
    ("GET", f"{WS}/audit"): P.AUDIT_READ,
    ("GET", f"{WS}/files"): P.FILES_READ,
    ("GET", f"{WS}/files/{{file_id}}"): P.FILES_READ,
    ("GET", f"{WS}/files/{{file_id}}/download"): P.FILES_READ,
    ("POST", f"{WS}/files/samples"): P.FILES_READ,
    ("POST", f"{WS}/files/upload-intent"): P.FILES_UPLOAD,
    ("POST", f"{WS}/files/{{file_id}}/complete"): P.FILES_UPLOAD,
    ("DELETE", f"{WS}/files/{{file_id}}"): P.FILES_DELETE,
    ("POST", f"{WS}/drafts"): P.DRAFTS_CREATE,
    ("GET", f"{WS}/drafts/{{draft_id}}"): P.DRAFTS_READ,
    ("PATCH", f"{WS}/drafts/{{draft_id}}"): P.DRAFTS_CREATE,
    ("GET", f"{WS}/workflows"): P.WORKFLOWS_READ,
    ("POST", f"{WS}/workflows"): P.WORKFLOWS_SAVE,
    ("GET", _flow): P.WORKFLOWS_READ,
    ("DELETE", _flow): P.WORKFLOWS_SAVE,
    ("POST", f"{_flow}/versions"): P.WORKFLOWS_SAVE,
    ("GET", f"{_flow}/versions/{{version}}"): P.WORKFLOWS_READ,
    ("POST", f"{_flow}/replay-check"): P.WORKFLOWS_READ,
    ("GET", f"{WS}/runs"): P.RUNS_READ,
    ("POST", f"{WS}/runs"): P.RUNS_CREATE,
    ("GET", _runs): P.RUNS_READ,
    ("GET", f"{_runs}/events"): P.RUNS_READ,
    ("POST", f"{_runs}/approve"): P.RUNS_APPROVE,
    ("POST", f"{_runs}/resolve"): P.RUNS_APPROVE,
    ("POST", f"{_runs}/cancel"): P.RUNS_CANCEL,
    ("GET", f"{_runs}/outputs"): P.RUNS_READ,
    ("GET", f"{_out}/download"): P.RUNS_READ,
    ("GET", f"{_out}/preview"): P.RUNS_READ,
    ("GET", f"{_out}/rows/{{row}}/lineage"): P.RUNS_READ,
}


def check_table(routes: Iterable[tuple[str, str]]) -> None:
    """Refuse to start when a route has no declaration, or the table names a missing route."""
    routes = set(routes)
    if missing := routes - set(TABLE):
        raise RuntimeError(f"routes with no permission declaration: {sorted(missing)}")
    if extra := set(TABLE) - routes:
        raise RuntimeError(f"permission declarations for no route: {sorted(extra)}")


def not_found() -> ProblemError:
    return ProblemError(404, "NOT_FOUND", "Not found")


def authorize(request: Request) -> None:
    declared = TABLE[request.method, V1 + request.scope["route"].path]
    if declared == PUBLIC:
        return
    signed_in = caller(request)
    request.state.caller = signed_in
    if declared == SIGNED_IN:
        return
    try:
        workspace_id = UUID(request.path_params["ws_id"])
    except ValueError:
        raise not_found() from None
    with database(request)() as session:
        role = session.scalars(
            select(m.Membership.role).where(
                m.Membership.workspace_id == workspace_id,
                m.Membership.user_id == signed_in.user.id,
            )
        ).one_or_none()
    if role is None:
        raise not_found()
    if not allowed(Role(role), declared):
        raise ProblemError(403, "PERMISSION_DENIED", "Not allowed in this workspace")
    request.state.workspace_id, request.state.role = workspace_id, Role(role)
