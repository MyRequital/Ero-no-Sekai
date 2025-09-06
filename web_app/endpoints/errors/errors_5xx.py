from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path
from fastapi import APIRouter

from fastapi.templating import Jinja2Templates
from web_app.app.config import Config


router = APIRouter()
templates = Jinja2Templates(directory=Config.TEMPLATES_PATH)


@router.get("/trigger-500")
async def trigger_500():
    raise Exception("Тест")


async def handler_500(request: Request, exc: StarletteHTTPException):
    context = {
        "request": request,
        "code": 500,
        "image_url": "static/pictures/custom_err_500.png",
        "error_message": "Внутренняя ошибка сервера",
        "error_description": str(exc),
        "suggestion_1": "Попробуйте обновить страницу",
        "suggestion_2": "Вернуться назад",
        "suggestion_3": "Связаться с поддержкой",
    }
    try:
        return templates.TemplateResponse("errors/error_500.j2", context, status_code=500)
    except Exception as e:
        from starlette.responses import PlainTextResponse
        return PlainTextResponse(
            content=f"Ошибка рендеринга шаблона: {e}",
            status_code=500
        )


async def handler_default_5xx(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse(
        "errors/default.j2",
        {
            "request": request,
            "code": exc.status_code,
            "message": getattr(exc, "detail", "Произошла внутренняя ошибка сервера.")
        },
        status_code=exc.status_code
    )
