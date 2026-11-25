"""API v1, mounted at `/api/v1`."""

from fastapi import APIRouter

from app.api.v1 import auth, drafts, files, health, operations, runs, workspaces

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(workspaces.router)
router.include_router(files.router)
router.include_router(operations.operations)
router.include_router(operations.limits)
router.include_router(drafts.templates)
router.include_router(drafts.drafts)
router.include_router(runs.router)
