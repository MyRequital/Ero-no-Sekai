from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from web_app.app.config import Config
from fastapi.responses import Response
from fastapi import APIRouter
from starlette.exceptions import HTTPException as StarletteHTTPException


templates = Jinja2Templates(directory=Config.TEMPLATES_PATH)
router = APIRouter()


async def handler_404(request: Request, exc: StarletteHTTPException) -> Response:
    context = {
        "request": request,
        "code": 404,
        "image_url": "static/pictures/custom_err_404.png",
        "error_message": "Страница не найдена",
        "error_description": str(exc),
        "suggestion_1": "Проверьте правильность введённого адреса",
        "suggestion_2": "Вернитесь на предыдущую страницу",
    }
    try:
        return templates.TemplateResponse("errors/error_404.j2", context, status_code=404)
    except Exception as e:
        from starlette.responses import PlainTextResponse
        return PlainTextResponse(content=f"Ошибка рендеринга шаблона: {e}", status_code=404)


async def handler_403(request: Request, exc: StarletteHTTPException):
    context = {
        "request": request,
        "code": 403,
        "image_url": "static/pictures/custom_err_403.png",
        "error_message": "Доступ запрещён",
        "error_description": str(exc),
        "suggestion_1": "Убедитесь, что у вас есть права доступа",
        "suggestion_2": "Вернитесь на предыдущую страницу",
    }
    try:
        return templates.TemplateResponse("errors/error_403.j2", context, status_code=403)
    except Exception as e:
        from starlette.responses import PlainTextResponse
        return PlainTextResponse(content=f"Ошибка рендеринга шаблона: {e}", status_code=403)


async def handler_401(request: Request, exc: StarletteHTTPException):
    context = {
        "request": request,
        "code": 401,
        "image_url": "static/pictures/custom_err_401.png",
        "error_message": "Требуется авторизация",
        "error_description": str(exc),
        "suggestion_1": "Войдите в систему, чтобы получить доступ",
        "suggestion_2": "Вернитесь на предыдущую страницу",
    }
    try:
        return templates.TemplateResponse("errors/error_401.j2", context, status_code=401)
    except Exception as e:
        from starlette.responses import PlainTextResponse
        return PlainTextResponse(content=f"Ошибка рендеринга шаблона: {e}", status_code=401)


async def handler_400(request: Request, exc: StarletteHTTPException):
    context = {
        "request": request,
        "code": 400,
        "image_url": "static/pictures/custom_err_400.png",
        "error_message": "Некорректный запрос",
        "error_description": str(exc),
        "suggestion_1": "Проверьте корректность переданных данных",
        "suggestion_2": "Попробуйте обновить страницу или вернуться назад",
    }
    try:
        return templates.TemplateResponse("errors/error_400.j2", context, status_code=400)
    except Exception as e:
        from starlette.responses import PlainTextResponse
        return PlainTextResponse(content=f"Ошибка рендеринга шаблона: {e}", status_code=400)


@router.get("/trigger-404")
async def trigger_404():
    raise StarletteHTTPException(status_code=404, detail="Тестовая ошибка 404")

@router.get("/trigger-403")
async def trigger_403():
    raise StarletteHTTPException(status_code=403, detail="Тестовая ошибка 403")

@router.get("/trigger-401")
async def trigger_401():
    raise StarletteHTTPException(status_code=401, detail="Тестовая ошибка 401")

@router.get("/trigger-400")
async def trigger_400():
    raise StarletteHTTPException(status_code=400, detail="Тестовая ошибка 400")
