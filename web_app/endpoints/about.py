from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from web_app.app.config import Config
import os
from _configs.config import BASE_DIR

router = APIRouter()

BACKGROUND_PICTURE = "url('/static/pictures/main_theme_stability.jpg') no-repeat center center / cover"
TEXT_COLOR = "#fff"
ABOUT_TEXT = (
    "<p><strong>Ero no Sekai: Yami no Yokubo - Shinigami</strong> — это некоммерческий чат-бот, созданный для развлечения аниме-сообществ.</p>"
    "<p>Он подбирает аниме-подборки с полноценными ссылками на плеер, а также модерирует чат, следя за нарушениями участников.</p>"
    "<p>Shinigami поддерживает множество ручных команд — как для модерации, так и для генерации аниме-каруселей.</p>"
    "<p><em>Попробуй — тебе обязательно понравится!</em></p>"
)
BOT_URL = "https://t.me/EroNoSekai_Shinigami_bot"
QR_IMAGE = "/static/pictures/group_qr_link.png"



env = Environment(loader=FileSystemLoader(Config.TEMPLATES_PATH))


@router.get("/about")
async def about_project():
    template = env.get_template("about.j2")
    html_content = template.render(
        background=BACKGROUND_PICTURE,
        text_color=TEXT_COLOR,
        about_text=ABOUT_TEXT,
        bot_url=BOT_URL,
        qr_image=QR_IMAGE
    )
    return HTMLResponse(content=html_content)

