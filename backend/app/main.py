from fastapi import FastAPI

from app.core import env  # noqa: F401

from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Jack API")
    app.include_router(api_router)
    return app


app = create_app()
