from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from web_app.app.config import Config
from fastapi.templating import Jinja2Templates


router = APIRouter()


templates = Jinja2Templates(directory=Config.TEMPLATES_PATH)


@router.get("/free_rules", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("tg_webapp/free_rules.j2", {"request": request})

