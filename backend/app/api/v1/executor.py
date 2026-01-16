from fastapi import APIRouter

from app.schemas.executor import ExecutorHandlersResponse
from app.services import executor as executor_service

router = APIRouter(prefix="/executor", tags=["executor"])


@router.get("/handlers", response_model=ExecutorHandlersResponse)
def list_executor_handlers() -> ExecutorHandlersResponse:
    handlers = executor_service.list_handlers()
    return ExecutorHandlersResponse(handlers=handlers)
