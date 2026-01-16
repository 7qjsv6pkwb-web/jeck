from pydantic import BaseModel


class ExecutorHandlersResponse(BaseModel):
    handlers: list[str]
