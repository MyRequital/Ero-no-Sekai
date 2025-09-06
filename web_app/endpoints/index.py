from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from web_app.app.config import Config
import os
from _configs.config import BASE_DIR

router = APIRouter()

TITLE = "Добро пожаловать в Ero no Sekai: Shinigami"
BACKGROUND_PICTURE = "url('/static/pictures/main_theme_stability.jpg') no-repeat center center / cover"
TEXT_COLOR = "#fff"
BUTTON_COLOR = "#ff3366"
BUTTON_HOVER_COLOR = "#cc2952"
BUTTON_TEXT_COLOR = "#fff"
BUTTON_TEXT = "Написать боту"
BOT_URL = "https://t.me/EroNoSekai_Shinigami_bot"
QR_IMAGE = "/static/pictures/group_qr_link.png"

env = Environment(loader=FileSystemLoader(Config.TEMPLATES_PATH))

@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    template = env.get_template("index.j2")
    html_content = template.render(
        title=TITLE,
        background=BACKGROUND_PICTURE,
        text_color=TEXT_COLOR,
        button_color=BUTTON_COLOR,
        button_hover_color=BUTTON_HOVER_COLOR,
        button_text_color=BUTTON_TEXT_COLOR,
        button_text=BUTTON_TEXT,
        bot_url=BOT_URL,
        qr_image=QR_IMAGE
    )
    return HTMLResponse(content=html_content)


