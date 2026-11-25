"""API v1, mounted at `/api/v1`."""

from fastapi import APIRouter

from app.api.v1 import auth, health, workspaces

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(workspaces.router)
