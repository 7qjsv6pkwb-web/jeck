from fastapi import APIRouter

from app.api.v1.actions import router as actions_router
from app.api.v1.messages import router as messages_router
from app.api.v1.projects import router as projects_router
from app.api.v1.threads import router as threads_router

router = APIRouter()
router.include_router(projects_router)
router.include_router(threads_router)
router.include_router(messages_router)
router.include_router(actions_router)
