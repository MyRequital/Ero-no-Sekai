from aiogram.utils.chat_action import logger
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tools.common_utils import get_kodik_data_for_site
from web_app.app.config import Config

router = APIRouter()
templates = Jinja2Templates(directory=Config.TEMPLATES_PATH)


@router.get("/watch", response_class=HTMLResponse)
async def show_iframe(request: Request):
    shiki_id = request.query_params.get("sid")
    kp_id = request.query_params.get("kpid")

    if not shiki_id and not kp_id:
        raise HTTPException(
            status_code=400,
            detail="Не указан ни sid, ни kpid. Проверьте правильность ссылки."
        )

    title_name = ""
    iFrame_url = ""
    title_type = ""

    if shiki_id:
        kodik_anime_data = get_kodik_data_for_site(shikimori_id=shiki_id)
        title_type = "аниме"
    elif kp_id:
        kodik_anime_data = get_kodik_data_for_site(kinopoisk_id=kp_id)
        title_type = "фильм"

    if not kodik_anime_data:
        context = {
            "request": request,
            "image_url": "/static/pictures/custom_err_404.png",
            "error_code": "404",
            "error_message": "Видео не найдено",
            "error_description": "Возможно, видео отсутствует на сервере, было удалено или перемещено.",
            "suggestion_1": "Попробуйте открыть другое видео или вернуться позднее.",
            "suggestion_2": "Убедитесь, что ссылка была скопирована полностью и без ошибок."
        }
        return templates.TemplateResponse("errors/error_404.j2", context, status_code=404)

    title_name = kodik_anime_data.get("title")
    iFrame_url = kodik_anime_data.get("link")
    screenshot_poster = "/static/pictures/player_poster.jpg"

    try:
        screenshot_poster = kodik_anime_data.get("screenshots")[0]
        logger.info(f"[/watch][show_iFrame] Постер превью: {screenshot_poster}")
    except IndexError:
        logger.info(f"[/watch][show_iFrame] Постер превью: {screenshot_poster}")


    if not iFrame_url:
        context = {
            "request": request,
            "image_url": "/static/pictures/custom_err_500.png",
            "error_code": "500",
            "error_message": "Видео не найдено",
            "error_description": "Возможно, видео отсутствует на сервере, было удалено или перемещено.",
            "suggestion_1": "Попробуйте открыть другое видео или вернуться позднее.",
            "suggestion_2": "Убедитесь, что ссылка была скопирована полностью и без ошибок."
        }
        return templates.TemplateResponse("errors/error_500.j2", context, status_code=500)

    iFrame_url = f"https:{iFrame_url}"

    context = {
        "request": request,
        "title_type": title_type,
        "title_name": title_name,
        "iFrame_url": iFrame_url,
        "full_page_url": str(request.url),
        "preview_poster_image": screenshot_poster
    }

    return templates.TemplateResponse("iFrame.j2", context, status_code=200)
