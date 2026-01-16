from fastapi import FastAPI

from app.api.router import api_router
from app.core import env  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(title="Jack API")
    app.include_router(api_router)
    return app


app = create_app()
