from typing import Callable

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from web_app.app.config import Config
from web_app.endpoints import routers
from web_app.endpoints.errors.errors_4xx import handler_400, handler_401, handler_403, handler_404
from web_app.endpoints.errors.errors_5xx import handler_500


def cors_middleware_factory() -> Callable:
    return CORSMiddleware


async def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        cors_middleware_factory(),
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Статические файлы
    app.mount("/static", StaticFiles(directory="web_app/static"), name="static")

    # Registering 4xx
    app.add_exception_handler(400, handler_400)
    app.add_exception_handler(401, handler_401)
    app.add_exception_handler(403, handler_403)
    app.add_exception_handler(404, handler_404)

    # Registering 5xx
    app.add_exception_handler(500, handler_500)

    # Централизованная регистрация роутеров
    for router, prefix in routers:
        app.include_router(router, prefix=prefix or "")

    return app


