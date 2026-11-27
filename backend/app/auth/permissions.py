"""Roles and the permission matrix (P5.5, S-21): one table in code, mirrored in security.md.

A member may approve or cancel only their own runs; that rule lives with the runs endpoints.
"""

from enum import IntEnum, StrEnum
from types import MappingProxyType


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Rank(IntEnum):
    """For invitations: nobody grants a role above their own (S-29)."""

    VIEWER = 1
    MEMBER = 2
    ADMIN = 3
    OWNER = 4


class Permission(StrEnum):
    WORKSPACE_READ = "workspace.read"
    WORKSPACE_DELETE = "workspace.delete"
    MEMBERS_MANAGE = "members.manage"
    FILES_READ = "files.read"
    FILES_UPLOAD = "files.upload"
    FILES_DELETE = "files.delete"
    DRAFTS_READ = "drafts.read"
    DRAFTS_CREATE = "drafts.create"
    WORKFLOWS_READ = "workflows.read"
    WORKFLOWS_SAVE = "workflows.save"
    RUNS_READ = "runs.read"
    RUNS_CREATE = "runs.create"
    RUNS_APPROVE = "runs.approve"
    RUNS_CANCEL = "runs.cancel"
    AUDIT_READ = "audit.read"


EVERYONE = frozenset(Role)
EDITORS = frozenset({Role.OWNER, Role.ADMIN, Role.MEMBER})
MANAGERS = frozenset({Role.OWNER, Role.ADMIN})
P = Permission

MATRIX = MappingProxyType({
    P.WORKSPACE_READ: EVERYONE,
    P.WORKSPACE_DELETE: frozenset({Role.OWNER}),
    P.MEMBERS_MANAGE: MANAGERS,
    P.FILES_READ: EVERYONE,
    P.FILES_UPLOAD: EDITORS,
    P.FILES_DELETE: EDITORS,
    P.DRAFTS_READ: EVERYONE,
    P.DRAFTS_CREATE: EDITORS,
    P.WORKFLOWS_READ: EVERYONE,
    P.WORKFLOWS_SAVE: EDITORS,
    P.RUNS_READ: EVERYONE,
    P.RUNS_CREATE: EDITORS,
    P.RUNS_APPROVE: EDITORS,
    P.RUNS_CANCEL: EDITORS,
    P.AUDIT_READ: MANAGERS,
})  # fmt: skip


def allowed(role: Role, permission: Permission) -> bool:
    return role in MATRIX[permission]
