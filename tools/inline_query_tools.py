import re, json

from tools.common_utils import get_player_url, get_kodik_response
from _configs.log_config import logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BASE_URL = "https://ero-no-sekai.up.railway.app/watch/?sid="

def clean_description(text: str) -> str:
    if not text:
        return "Описание отсутствует."
    return re.sub(r'\[/?character[^\]]*\]', '', text)


def safe_join(items):
    return ', '.join([item if isinstance(item, str) else item.get('russian', 'Не указано') for item in items]) or 'Не указаны'

def build_anime_caption(anime: dict):
    description = clean_description(anime.get("description", "Описание отсутствует."))
    if len(description) > 300:
        description = description[:300] + "..."

    logger.debug(json.dumps(anime, indent=4, ensure_ascii=False))

    anime_id = anime.get('id')
    genres = anime.get("genres", [])
    studios = anime.get("studios", [])

    caption = (
        f"🎬 <b>{anime.get('name', 'Без названия')}</b> (<i>{anime.get('russian', '...')}</i>)\n"
        f"⭐️ <b>Оценка:</b> {anime.get('score', '?')}/10\n"
        f"🔖 <b>Жанры:</b> {safe_join(genres)}\n"
        f"🏢 <b>Студия:</b> {safe_join(studios)}\n"
        f"📺 <b>Эпизоды:</b> {anime.get('episodes', '?')}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"🔗 <a href='{anime.get('url', '')}'>Страница на Shikimori</a>"
    )


    result = get_kodik_response(anime_id)
    if result.status_code == 200:
        try:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Смотреть", url=BASE_URL+anime_id)
                ]
            ])

            return caption, markup
        except Exception as e:
            logger.error(f"[build_anime_caption] - Ошибка проверки kodik response {e}")
            return caption, None
    else:
        return caption, None




