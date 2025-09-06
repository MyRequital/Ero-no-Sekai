from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from web_app.app.config import Config

import html
import re

router = APIRouter()
templates = Jinja2Templates(directory=Config.TEMPLATES_PATH)

def sanitize_name(name: str | None) -> str | None:
    if not name:
        return None

    name = re.sub(r'[^\w\s\-.,!?@А-Яа-яЁё]', '', name)

    name = name[:50]

    name = html.escape(name)

    return name


@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request, name: str | None = None):
    safe_name = sanitize_name(name)
    return templates.TemplateResponse(
        "tg_webapp/index.j2",
        {
            "request": request,
            "name": safe_name
        }
    )

