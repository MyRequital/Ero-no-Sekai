from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from web_app.app.config import Config

router = APIRouter()
templates = Jinja2Templates(directory=Config.TEMPLATES_PATH)

@router.get("/policy", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("tg_webapp/policy.j2", {"request": request})
